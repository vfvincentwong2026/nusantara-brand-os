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
"""


def migrate(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(DDL)
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
