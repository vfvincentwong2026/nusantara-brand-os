import sqlite3

from nbo.db import migrate, seed
from nbo.importer import import_csv, load_schema, validate_row

DDL_SALES = """
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sku_id TEXT, store_id TEXT,
    date TEXT, qty INTEGER, revenue_idr REAL
);
"""


def test_seed_loads_all_three_stores(tmp_path):
    db = tmp_path / "t.db"
    assert seed(db) == 3
    conn = sqlite3.connect(db)
    sizes = dict(conn.execute("SELECT id, size_sqm FROM stores").fetchall())
    conn.close()
    assert sizes["store-jkt-500"] == 500
    assert sizes["store-jkt-2000"] == 2000
    assert sizes["store-jkt-5000"] == 5000


def test_validate_row_missing_required():
    schema = load_schema("sales")
    errs = validate_row({"sku_id": "a", "qty": "3"}, schema)  # 缺 store_id/date
    assert any("store_id" in e for e in errs)
    assert any("date" in e for e in errs)


def test_import_csv_good_and_bad_rows(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.executescript(DDL_SALES)
    conn.close()
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "sku_id,store_id,date,qty,revenue_idr\n"
        "sku1,store-jkt-500,2026-10-01,5,150000\n"
        "sku2,store-jkt-500,,3,\n"              # 缺 date -> 跳过
        "sku3,store-jkt-500,2026-10-03,abc,\n"   # qty 类型转换时 int('abc') 抛错? 见下
        , encoding="utf-8")
    # 第三行 qty='abc'：coerce 失败 -> 该行跳过并进入 errors，不抛异常不静默
    result = import_csv(csv_path, "sales", db, "sales")
    assert result["imported"] == 1
    assert len(result["errors"]) == 2  # 缺 date + qty 非数字
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()
    assert n == 1


def test_import_csv_happy_path(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.executescript(DDL_SALES)
    conn.close()
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "sku_id,store_id,date,qty,revenue_idr\n"
        "sku1,store-jkt-500,2026-10-01,5,150000\n"
        "sku2,store-jkt-500,2026-10-02,3,\n"
        , encoding="utf-8")
    result = import_csv(csv_path, "sales", db, "sales")
    assert result["imported"] == 2
    assert result["errors"] == []
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT sku_id, qty, revenue_idr FROM sales ORDER BY sku_id").fetchall()
    conn.close()
    assert rows == [("sku1", 5, 150000.0), ("sku2", 3, None)]
