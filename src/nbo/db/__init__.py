"""SQLite 本地开发库：migrate 建表 / seed 灌种子数据。生产环境切 D1 时表结构同源。"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("nbo.db")
SEED_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "seeds"

DDL = """
CREATE TABLE IF NOT EXISTS stores (
    id TEXT PRIMARY KEY, name TEXT, size_sqm REAL, island_region TEXT,
    mudik_offset REAL DEFAULT 0, qris_enabled INTEGER DEFAULT 0,
    fresh_ratio REAL DEFAULT 0, data TEXT
);
CREATE TABLE IF NOT EXISTS shelves (
    id TEXT PRIMARY KEY, store_id TEXT, zone TEXT,
    layer_count INTEGER, facing_width_m REAL, heat_value REAL
);
CREATE TABLE IF NOT EXISTS skus (
    id TEXT PRIMARY KEY, name TEXT, category TEXT, barcode TEXT, internal_code TEXT,
    halal_certified INTEGER DEFAULT 0, bpom_no TEXT, shelf_life_days INTEGER DEFAULT 365,
    fresh_ratio REAL DEFAULT 0, cost_idr REAL, sell_price_idr REAL
);
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY, sku_id TEXT, store_id TEXT, qty INTEGER,
    receive_date TEXT, expiry_date TEXT, location TEXT
);
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sku_id TEXT, store_id TEXT,
    date TEXT, qty INTEGER, revenue_idr REAL
);
CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sku_id TEXT, cert_type TEXT,
    cert_no TEXT, holder TEXT, issue_date TEXT, expiry_date TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS channel_points (
    id TEXT PRIMARY KEY, name TEXT, type TEXT, lat REAL, lon REAL,
    city TEXT, region TEXT, final_score INTEGER, grade TEXT,
    sales_step INTEGER DEFAULT 0, source TEXT DEFAULT 'manual',
    location_score INTEGER DEFAULT 50, activity_score INTEGER DEFAULT 50,
    competition_score INTEGER DEFAULT 50, cooperation_score INTEGER DEFAULT 50,
    digital_score INTEGER DEFAULT 50, owner_score INTEGER DEFAULT 50,
    region_score INTEGER DEFAULT 50, signals TEXT
);
"""

# 既有库增量补列（ WarungScout warungs 表同源，未来直接灌 D1 导出 ）
_CHANNEL_NEW_COLS = ["location_score INTEGER DEFAULT 50", "activity_score INTEGER DEFAULT 50",
                     "competition_score INTEGER DEFAULT 50", "cooperation_score INTEGER DEFAULT 50",
                     "digital_score INTEGER DEFAULT 50", "owner_score INTEGER DEFAULT 50",
                     "region_score INTEGER DEFAULT 50", "signals TEXT"]


def migrate(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(DDL)
        existing = {r[1] for r in conn.execute("PRAGMA table_info(channel_points)")}
        for col in _CHANNEL_NEW_COLS:
            name = col.split()[0]
            if name not in existing:
                conn.execute(f"ALTER TABLE channel_points ADD COLUMN {col}")
        conn.commit()
    finally:
        conn.close()


def seed(db_path: Path = DB_PATH) -> int:
    """灌入 data/seeds/ 下所有门店 JSON，返回灌入门店数。"""
    migrate(db_path)
    conn = sqlite3.connect(db_path)
    n = 0
    try:
        for f in sorted(SEED_DIR.glob("store_*.json")):
            store = json.loads(f.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR REPLACE INTO stores VALUES (?,?,?,?,?,?,?,?)",
                (store["id"], store["name"], store["size_sqm"], store["island_region"],
                 store.get("mudik_offset", 0), int(store.get("qris_enabled", False)),
                 store.get("fresh_ratio", 0), json.dumps(store, ensure_ascii=False)))
            for s in store.get("shelves", []):
                conn.execute(
                    "INSERT OR REPLACE INTO shelves VALUES (?,?,?,?,?,?)",
                    (s["id"], store["id"], s["zone"], s["layer_count"],
                     s["facing_width_m"], s["heat_value"]))
            n += 1
        # 零食演示数据（P1 SKU 去化大屏开发用）
        demo_file = SEED_DIR / "snack_demo.json"
        if demo_file.exists():
            demo = json.loads(demo_file.read_text(encoding="utf-8"))
            for s in demo.get("skus", []):
                conn.execute(
                    "INSERT OR REPLACE INTO skus VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (s["id"], s["name"], s["category"], s["barcode"], s["internal_code"],
                     int(s.get("halal_certified", False)), s.get("bpom_no"),
                     s.get("shelf_life_days", 365), s.get("fresh_ratio", 0),
                     s.get("cost_idr"), s.get("sell_price_idr")))
            for b in demo.get("batches", []):
                conn.execute(
                    "INSERT OR REPLACE INTO batches VALUES (?,?,?,?,?,?,?)",
                    (b["id"], b["sku_id"], b["store_id"], b["qty"],
                     b["receive_date"], b["expiry_date"], b.get("location")))
            for c in demo.get("certifications", []):
                conn.execute(
                    "INSERT INTO certifications (sku_id, cert_type, cert_no, holder, issue_date, expiry_date, status) VALUES (?,?,?,?,?,?,?)",
                    (c["sku_id"], c["cert_type"], c["cert_no"], c["holder"],
                     c.get("issue_date"), c.get("expiry_date"), c.get("status", "valid")))
            for s in demo.get("sales", []):
                conn.execute(
                    "INSERT INTO sales (sku_id, store_id, date, qty, revenue_idr) VALUES (?,?,?,?,?)",
                    (s["sku_id"], s["store_id"], s["date"], s["qty"], s.get("revenue_idr")))
            n += 1
        # 渠道点位演示数据（字段对齐 WarungScout warungs 表，见 warungscout docs/DATABASE_SCHEMA.md）
        # warung 带原始信号时走 WarungScout 评分模型（nbo.scoring）计算 7 维+总分+等级
        from nbo.scoring import score_warung
        ch_file = SEED_DIR / "channel_demo.json"
        if ch_file.exists():
            for p in json.loads(ch_file.read_text(encoding="utf-8")).get("channel_points", []):
                dims = {k: None for k in
                        ("location", "activity", "competition", "cooperation", "digital", "owner", "region")}
                signals = p.get("signals")
                if p["type"] == "warung" and signals is not None:
                    r = score_warung({**signals, "city": p.get("city")})
                    p["final_score"], p["grade"] = r["final_score"], r["grade"]
                    dims = r["dims"]
                elif p["type"] == "warung" and "final_score" not in p:
                    r = score_warung({"no_history": True, "city": p.get("city")})
                    p["final_score"], p["grade"] = r["final_score"], r["grade"]
                    dims = r["dims"]
                conn.execute(
                    "INSERT OR REPLACE INTO channel_points VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (p["id"], p["name"], p["type"], p["lat"], p["lon"], p.get("city"),
                     p.get("region"), p.get("final_score", 0), p.get("grade", "normal"),
                     p.get("sales_step", 0), p.get("source", "manual"),
                     dims["location"], dims["activity"], dims["competition"], dims["cooperation"],
                     dims["digital"], dims["owner"], dims["region"],
                     json.dumps(signals, ensure_ascii=False) if signals else None))
            n += 1
        # 案例演示数据（社区集装箱店，P1 结构化实体）
        case_file = SEED_DIR / "case_demo.json"
        if case_file.exists():
            from nbo.case import seed_case
            seed_case(conn, json.loads(case_file.read_text(encoding="utf-8")))
            n += 1
        # 热点零食雷达演示数据
        from nbo.trend import seed_trend
        seed_trend(conn)
        n += 1
        # 加盟体系演示数据
        from nbo.franchise import seed_franchise
        seed_franchise(conn)
        n += 1
        # 加盟机会图层演示数据
        from nbo.opportunity import seed_opportunity
        seed_opportunity(conn)
        n += 1
        # 热点品牌演示数据
        from nbo.hotbrand import seed_hotbrand
        seed_hotbrand(conn)
        n += 1
        conn.commit()
        return n
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "migrate"
    if cmd == "migrate":
        migrate()
        print("migrate ok")
    elif cmd == "seed":
        print(f"seed ok: {seed()} stores")
