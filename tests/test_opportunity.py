"""加盟机会图层引擎测试。"""
import sqlite3

from nbo.db import seed
from nbo.opportunity import build_opportunity, migrate_opportunity, seed_opportunity


def test_opportunity_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_opportunity(db)
    assert d["demo"] is True and len(d["zones"]) == 10
    # 评分降序、区间合法、带评级与品牌建议
    scores = [z["score"] for z in d["zones"]]
    assert scores == sorted(scores, reverse=True)
    for z in d["zones"]:
        assert 30 <= z["score"] <= 100
        assert z["grade"] in ("S", "A", "B", "C")
        assert z["suggested_brand"]["name"] and z["suggested_brand"]["invest_idr"] > 0
    # 保护圈：3 家加盟店 + 1 案例样板
    assert len(d["protection"]) == 4
    assert any(p["kind"] == "案例样板" for p in d["protection"])
    for p in d["protection"]:
        assert p["radius_m"] and p["lat"] and p["lon"]
    # KPI 与分区一致
    assert d["kpi"]["s_grade"] == sum(1 for z in d["zones"] if z["grade"] == "S")
    assert d["kpi"]["protected"] == 4


def test_opportunity_seed_idempotent(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    seed_opportunity(conn)
    seed_opportunity(conn)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM opportunity_zone").fetchone()[0]
    m = conn.execute("SELECT COUNT(*) FROM franchise_store").fetchone()[0]
    conn.close()
    assert (n, m) == (10, 3)


def test_opportunity_empty_db(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    migrate_opportunity(conn)
    conn.close()
    assert "error" in build_opportunity(db)
