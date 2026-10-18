"""WarungScout D1 导出导入器测试。"""
import json
import sqlite3

import pytest

from nbo.db import seed
from nbo.importer.warungscout import import_warungs

ROWS = [
    # 全字段：直写
    {"id": "WS-1", "name": "Warung A", "latitude": -6.2088, "longitude": 106.8456,
     "city": "Jakarta", "region": "DKI Jakarta", "sales_step": 3,
     "location_score": 90, "activity_score": 80, "competition_score": 100,
     "cooperation_score": 70, "digital_score": 75, "owner_score": 60, "region_score": 100,
     "final_score": 84, "grade": "gold"},
    # 缺维度分：回退 scoring（带信号）
    {"id": "WS-2", "name": "Warung B", "latitude": -6.2600, "longitude": 106.8100,
     "city": "Bandung", "sales_step": 1,
     "signals": {"gm_rating": 4.2, "gm_reviews": 60, "wa_active": True,
                 "reply_rate": 0.8, "visit_feedback": "positive", "qris": True,
                 "wa_reply": "fast", "smartphone": True,
                 "facilities": {"schools": 1, "residences": 1}, "warung_competitors_500m": 2}},
    # 无坐标：跳过
    {"id": "WS-3", "name": "Warung C", "latitude": None, "longitude": None},
]


def test_import_from_json(tmp_path):
    src = tmp_path / "ws.json"
    src.write_text(json.dumps(ROWS, ensure_ascii=False), encoding="utf-8")
    db = tmp_path / "t.db"
    seed(db)
    r = import_warungs(src, db)
    assert r == {"imported": 2, "skipped_no_coords": 1, "total_rows": 3}
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    pts = {p["id"]: dict(p) for p in conn.execute(
        "SELECT * FROM channel_points WHERE source='warungscout'")}
    assert pts["WS-1"]["final_score"] == 84 and pts["WS-1"]["grade"] == "gold"
    assert pts["WS-1"]["type"] == "warung" and pts["WS-1"]["sales_step"] == 3
    # WS-2 回退模型算分，7 维齐全且在 0-100
    b = pts["WS-2"]
    assert b["final_score"] and b["grade"] in ("gold", "silver", "potential", "normal")
    assert all(0 <= b[c] <= 100 for c in
               ("location_score", "activity_score", "competition_score", "cooperation_score",
                "digital_score", "owner_score", "region_score"))
    conn.close()


def test_import_from_sqlite_and_replace(tmp_path):
    src_db = tmp_path / "ws.sqlite"
    conn = sqlite3.connect(src_db)
    conn.execute("CREATE TABLE warungs (id TEXT, name TEXT, latitude REAL, longitude REAL,"
                 " city TEXT, region TEXT, sales_step INTEGER, final_score INTEGER, grade TEXT)")
    conn.execute("INSERT INTO warungs VALUES ('WS-9','Warung X',-6.9,107.6,'Bandung','Jabar',2,66,'silver')")
    conn.commit()
    conn.close()
    db = tmp_path / "t.db"
    seed(db)
    r = import_warungs(src_db, db)
    assert r["imported"] == 1
    # 再灌一次（无 replace）不报错；replace 先清后灌仍 1 条
    import_warungs(src_db, db, replace=True)
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM channel_points WHERE source='warungscout'").fetchone()[0]
    conn.close()
    assert n == 1


def test_bad_suffix_raises(tmp_path):
    bad = tmp_path / "ws.csv"
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        import_warungs(bad, tmp_path / "t.db")


def test_import_from_sql_dump(tmp_path):
    src = tmp_path / "ws.sql"
    src.write_text(
        "CREATE TABLE warungs (id TEXT, name TEXT, latitude REAL, longitude REAL, city TEXT,"
        " region TEXT, sales_step INTEGER, final_score INTEGER, grade TEXT);\n"
        "INSERT INTO warungs VALUES ('WS-7','Warung S',-6.1,106.9,'Jakarta','DKI',4,88,'gold');\n",
        encoding="utf-8")
    db = tmp_path / "t.db"
    seed(db)
    r = import_warungs(src, db)
    assert r["imported"] == 1
