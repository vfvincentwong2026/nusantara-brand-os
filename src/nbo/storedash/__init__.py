"""小店版去化大屏引擎：加盟商一屏 5 卡极简运营视图。

与体系一复杂大屏（dashboard.json）同数据源不同口径：只输出"需要行动"的信息。
复用 case 门店演示数据（56㎡ 集装箱店），真实接入时切换 db 即可。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

LT_EFF = 8  # 补货提前期（天）


def build_store_dash(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        from nbo.case import migrate_case
        migrate_case(conn)
        store = dict(conn.execute("SELECT * FROM case_store LIMIT 1").fetchone() or {})
        if not store:
            return {"demo": True, "error": "case_store 为空，请先 seed"}
        skus = [dict(r) for r in conn.execute("SELECT * FROM case_sku ORDER BY avg_daily_sales DESC")]
        orders = [dict(r) for r in conn.execute(
            "SELECT created_at, amount_idr, status FROM case_order ORDER BY created_at DESC")]
    finally:
        conn.close()

    # 今日流水：取最新一个有订单的自然日（演示数据非当日时标注日期）
    day_map = {}
    for o in orders:
        d = (o["created_at"] or "")[:10]
        day_map.setdefault(d, {"orders": 0, "revenue": 0.0})
        day_map[d]["orders"] += 1
        day_map[d]["revenue"] += o["amount_idr"] or 0
    today = datetime.now().date().isoformat()
    best_day = max(day_map) if day_map else None
    use_day = today if today in day_map else best_day
    flow = day_map.get(use_day, {"orders": 0, "revenue": 0})

    # 畅销 TOP5
    top5 = [{"name": k["name"], "avg_daily": k["avg_daily_sales"],
             "stock": k["stock"]} for k in skus[:5]]

    # 行动预警：只列需要动作的 SKU
    alerts, reorder = [], []
    for k in skus:
        avail = max(0, k["stock"] - k["reserved"])
        ads = k["avg_daily_sales"] or 0
        dos = round(avail / ads, 1) if ads > 0 else 0
        if k["blocked"]:
            alerts.append({"name": k["name"], "level": "bad", "action": "合规 blocked，立即下架"})
        elif avail <= 0:
            alerts.append({"name": k["name"], "level": "bad", "action": "已缺货，今日必补"})
            reorder.append({"name": k["name"], "qty": max(1, round(ads * LT_EFF)), "reason": "缺货补满"})
        elif dos <= LT_EFF:
            level = "warn" if dos > LT_EFF / 2 else "high"
            alerts.append({"name": k["name"], "level": level,
                           "action": f"仅剩 {dos} 天库存" + ("，尽快补货" if level == "high" else "，列入下次订货")})
            if level == "high":
                reorder.append({"name": k["name"], "qty": max(1, round(ads * LT_EFF) - avail),
                                "reason": f"补至 {LT_EFF} 天安全库存"})
    level_rank = {"bad": 0, "high": 1, "warn": 2}
    alerts.sort(key=lambda a: level_rank[a["level"]])

    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "demo": True,
            "store": {"name": store.get("name"), "concept": "56㎡ 案例集装箱店 · 小店模式演示"},
            "business_date": use_day, "is_today": use_day == today,
            "kpi": {"today_revenue": round(flow["revenue"]), "today_orders": flow["orders"],
                    "alert_count": len(alerts), "reorder_lines": len(reorder),
                    "skus_on_shelf": len(skus)},
            "top5": top5, "alerts": alerts[:5], "reorder": reorder[:3],
            "links": {"full_dashboard": "/dashboard/?store=case", "franchise": "/franchise/"}}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
