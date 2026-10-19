"""案例引擎 P1：门店 / SKU / 订单 / 能源 / 内容排期 结构化实体 → case_ops.json。

数据边界（任务书 §13）：每行带来源标记 source_type ∈ 真实接入/人工录入/种子样本/模拟计算/待确认。
案例页运营面板全部读取本引擎输出，不在前端硬编码业务数据。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

ORDER_STEPS = ["新订单", "待拣货", "拣货中", "待复核", "待自提/配送", "配送中", "已完成"]

CASE_DDL = """
CREATE TABLE IF NOT EXISTS case_store (
    id TEXT PRIMARY KEY, name TEXT, brand TEXT, city TEXT, neighborhood TEXT,
    lat REAL, lon REAL, tier TEXT, net_length_m REAL, net_width_m REAL,
    power_mode TEXT, service_radius_m INTEGER, status TEXT, source_type TEXT
);
CREATE TABLE IF NOT EXISTS case_sku (
    id TEXT PRIMARY KEY, store_id TEXT, name TEXT, stock INTEGER, reserved INTEGER,
    avg_daily_sales REAL, shelf_location TEXT, compliance_status TEXT,
    compliance_note TEXT, blocked INTEGER DEFAULT 0, source_type TEXT
);
CREATE TABLE IF NOT EXISTS case_order (
    id TEXT PRIMARY KEY, store_id TEXT, channel TEXT, fulfillment_type TEXT,
    status TEXT, amount_idr REAL, items TEXT, created_at TEXT, source_type TEXT
);
CREATE TABLE IF NOT EXISTS case_energy_log (
    store_id TEXT, source TEXT, generator_status TEXT, runtime_hours REAL,
    fuel_record TEXT, energy_cost_idr REAL, outage_count_30d INTEGER, source_type TEXT
);
CREATE TABLE IF NOT EXISTS case_media_schedule (
    store_id TEXT, asset_title TEXT, device TEXT, slot TEXT, linked TEXT,
    status TEXT, source_type TEXT
);
"""


def migrate_case(conn: sqlite3.Connection) -> None:
    conn.executescript(CASE_DDL)


def seed_case(conn: sqlite3.Connection, seed: dict) -> None:
    migrate_case(conn)
    s = seed["store"]
    conn.execute("INSERT OR REPLACE INTO case_store VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (s["id"], s["name"], s["brand"], s["city"], s["neighborhood"],
                  s["lat"], s["lon"], s["tier"], s["net_length_m"], s["net_width_m"],
                  s["power_mode"], s["service_radius_m"], s["status"], s["source_type"]))
    for k in seed["skus"]:
        conn.execute("INSERT OR REPLACE INTO case_sku VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (k["id"], s["id"], k["name"], k["stock"], k["reserved"],
                      k["avg_daily_sales"], k["shelf_location"], k["compliance_status"],
                      k.get("compliance_note"), int(k.get("blocked", 0)), k["source_type"]))
    for o in seed["orders"]:
        conn.execute("INSERT OR REPLACE INTO case_order VALUES (?,?,?,?,?,?,?,?,?)",
                     (o["id"], s["id"], o["channel"], o["fulfillment_type"], o["status"],
                      o["amount_idr"], json.dumps(o["items"], ensure_ascii=False),
                      o["created_at"], o["source_type"]))
    for e in seed["energy"]:
        conn.execute("INSERT OR REPLACE INTO case_energy_log VALUES (?,?,?,?,?,?,?,?)",
                     (s["id"], e["source"], e["generator_status"], e["runtime_hours"],
                      e["fuel_record"], e["energy_cost_idr"], e["outage_count_30d"], e["source_type"]))
    for m in seed["media"]:
        conn.execute("INSERT OR REPLACE INTO case_media_schedule VALUES (?,?,?,?,?,?,?)",
                     (s["id"], m["asset_title"], m["device"], m["slot"], m["linked"],
                      m["status"], m["source_type"]))


def build_case_ops(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_case(conn)
        store = dict(conn.execute("SELECT * FROM case_store LIMIT 1").fetchone() or {})
        if not store:
            return {"demo": True, "error": "case_store 为空，请先 seed"}
        skus = [dict(r) for r in conn.execute("SELECT * FROM case_sku ORDER BY id")]
        orders = [dict(r) for r in conn.execute("SELECT * FROM case_order ORDER BY created_at DESC")]
        for o in orders:
            o["items"] = json.loads(o["items"])
        energy = [dict(r) for r in conn.execute("SELECT * FROM case_energy_log")]
        media = [dict(r) for r in conn.execute("SELECT * FROM case_media_schedule")]
    finally:
        conn.close()
    kpis = {
        "daily_orders": {"v": "86 单", "l": "日交易数", "source_type": "种子样本"},
        "daily_revenue": {"v": "Rp 4.21 jt", "l": "日销售额", "source_type": "种子样本"},
        "gross_margin": {"v": "31.2%", "l": "毛利率", "source_type": "模拟计算"},
        "basket": {"v": "Rp 48,900", "l": "客单价", "source_type": "模拟计算"},
        "oos": {"v": f"{sum(1 for k in skus if k['stock'] - k['reserved'] <= 0)} 个", "l": "缺货 SKU", "source_type": "模拟计算"},
        "expiring": {"v": "5 件", "l": "临期库存（30 天内）", "source_type": "种子样本"},
        "ontime": {"v": "96%", "l": "配送准时率", "source_type": "种子样本"},
        "repurchase": {"v": "34%", "l": "30 天复购率", "source_type": "种子样本"},
    }
    flow_order = orders[0] if orders else None
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "demo": True,
        "store": store,
        "kpis": kpis,
        "order_steps": ORDER_STEPS,
        "flow_order": flow_order,
        "orders": orders,
        "skus": skus,
        "energy": energy,
        "media": media,
    }


def write_case_ops(out_path: str | Path, **kwargs) -> dict:
    data = build_case_ops(**kwargs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
