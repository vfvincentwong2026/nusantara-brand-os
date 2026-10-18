"""SKU 去化大屏数据引擎：SQLite -> dashboard.json。

口径：
- 在库 on_hand = SUM(batches.qty)
- 近效期 near_expiry_qty = 30 天内到期批次数量合计
- 日均销量 avg_daily = 最近 N 天销售均值（无销售记录则为 0）
- 补货建议 = ROP + 提前期需求 - 在库（仅缺货/高风险时输出）
- 状态：out_of_stock / high(<=ROP) / watch(库存天数 < 1.5×LT_eff) / ok
- 合规 = 该 SKU 证书的最差状态（withdrawn > expired > expiring > valid > none）
"""
import json
import sqlite3
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path

from nbo.replenishment import ReplenishmentEngine
from nbo.forecast import ForecastEngine
from nbo.calendar import IndonesiaCalendar

NEAR_EXPIRY_DAYS = 30
CERT_SEVERITY = {"withdrawn": 4, "expired": 3, "expiring": 2, "valid": 1, "none": 0}
CERT_LABEL = {"withdrawn": "已撤证", "expired": "已过期", "expiring": "临期", "valid": "有效", "none": "无证"}


def _worst_cert(certs: list[dict], today: date, warn_days: int = 90) -> str:
    """按到期日推导每条证书状态，返回最差者。"""
    worst = "none"
    for c in certs:
        if c.get("status") == "withdrawn":
            return "withdrawn"
        status = "valid"
        exp = c.get("expiry_date")
        if exp:
            d = date.fromisoformat(exp)
            if d < today:
                status = "expired"
            elif (d - today).days <= warn_days:
                status = "expiring"
        if CERT_SEVERITY[status] > CERT_SEVERITY[worst]:
            worst = status
    return worst


def build_dashboard(db_path: str | Path, store_id: str,
                    lt_mean: float = 7, lt_std: float = 2,
                    sales_window_days: int = 14,
                    today: date | None = None) -> dict:
    today = today or date.today()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        store = conn.execute("SELECT * FROM stores WHERE id=?", (store_id,)).fetchone()
        if not store:
            raise ValueError(f"门店不存在: {store_id}")
        island = store["island_region"]
        eng = ReplenishmentEngine()
        lt_eff = eng.effective_lead_time(lt_mean, lt_std, island)

        window_start = (today - timedelta(days=sales_window_days)).isoformat()
        sales_agg = {r["sku_id"]: [r["d"], r["n"]] for r in conn.execute(
            "SELECT sku_id, AVG(qty) d, COUNT(*) n FROM sales "
            "WHERE store_id=? AND date>=? GROUP BY sku_id", (store_id, window_start))}
        daily_map = {}
        for r in conn.execute(
                "SELECT sku_id, date, SUM(qty) q FROM sales WHERE store_id=? GROUP BY sku_id, date",
                (store_id,)):
            daily_map.setdefault(r["sku_id"], {})[r["date"]] = r["q"]

        cert_agg = {}
        for r in conn.execute("SELECT * FROM certifications"):
            cert_agg.setdefault(r["sku_id"], []).append(dict(r))

        skus = []
        for r in conn.execute("SELECT * FROM skus ORDER BY id"):
            sku = dict(r)
            sid = sku["id"]
            on_hand = conn.execute(
                "SELECT COALESCE(SUM(qty),0) FROM batches WHERE sku_id=? AND store_id=?",
                (sid, store_id)).fetchone()[0]
            expiries = conn.execute(
                "SELECT qty, expiry_date FROM batches WHERE sku_id=? AND store_id=? AND qty>0 "
                "ORDER BY expiry_date", (sid, store_id)).fetchall()
            near_qty = sum(b["qty"] for b in expiries
                           if (date.fromisoformat(b["expiry_date"]) - today).days <= NEAR_EXPIRY_DAYS)
            next_expiry = expiries[0]["expiry_date"] if expiries else None

            d, n = sales_agg.get(sid, [0, 0])
            avg_daily = round(d, 1) if n >= 3 else 0  # 少于 3 天记录不估
            # 预测口径：预测引擎给出未来 7 天日均（节庆因子已乘）；无数据回退 raw 均值
            fe = ForecastEngine(calendar=IndonesiaCalendar(), category=sku["category"],
                                mudik_offset=store["mudik_offset"] or 0.0)
            daily = daily_map.get(sid, {})
            preds = fe.forecast(daily, 7, start=today) if daily else []
            forecast_daily = round(sum(p["predicted"] for p in preds) / 7, 1) if preds else 0
            demand_daily = forecast_daily or avg_daily
            bt = fe.backtest(daily, 7, today) if daily else {"mape": None, "n": 0}
            demand_std = 5.0  # v1 缺日销明细方差，用常数占位，回测校准后替换
            ss = eng.safety_stock(demand_std, lt_eff)
            rop = eng.reorder_point(demand_daily, lt_eff, ss)
            dos = round(on_hand / demand_daily, 1) if demand_daily > 0 else None

            if on_hand == 0:
                status = "out_of_stock"
            elif demand_daily > 0 and on_hand <= rop:
                status = "high"
            elif dos is not None and dos < lt_eff * 1.5:
                status = "watch"
            else:
                status = "ok"
            suggest = max(0, round(rop + demand_daily * lt_eff - on_hand)) if status in ("out_of_stock", "high") else 0

            cert_status = _worst_cert(cert_agg.get(sid, []), today)
            skus.append({
                "id": sid, "name": sku["name"], "category": sku["category"],
                "on_hand": on_hand, "avg_daily": avg_daily,
                "forecast_daily": forecast_daily, "days_of_supply": dos,
                "backtest_mape": bt["mape"],
                "next_expiry": next_expiry, "near_expiry_qty": near_qty,
                "rop": round(rop, 1), "suggest_qty": suggest, "status": status,
                "cert_status": cert_status, "cert_label": CERT_LABEL[cert_status],
            })

        kpis = {
            "on_hand_total": sum(s["on_hand"] for s in skus),
            "near_expiry_qty": sum(s["near_expiry_qty"] for s in skus),
            "out_of_stock": sum(1 for s in skus if s["status"] == "out_of_stock"),
            "risk_count": sum(1 for s in skus if s["status"] in ("high", "watch")),
            "cert_alert": sum(1 for s in skus if s["cert_status"] in ("expired", "expiring", "withdrawn")),
        }
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "store": {"id": store_id, "name": store["name"], "island_region": island},
            "params": {"lt_eff": lt_eff, "sales_window_days": sales_window_days,
                       "near_expiry_days": NEAR_EXPIRY_DAYS},
            "kpis": kpis,
            "skus": skus,
        }
    finally:
        conn.close()


def write_dashboard(out_path: str | Path, **kwargs) -> dict:
    data = build_dashboard(**kwargs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
