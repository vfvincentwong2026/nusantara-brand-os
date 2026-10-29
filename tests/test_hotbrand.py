"""热点品牌引擎测试。"""
import sqlite3

from nbo.db import seed
from nbo.hotbrand import build_hotbrand, migrate_hotbrand, seed_hotbrand
from nbo.trend import build_trend


def test_hotbrand_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_hotbrand(db)
    assert d["demo"] is True and len(d["brands"]) == 12
    for b in d["brands"]:
        assert len(b["hot_products"]) == 3
        assert b["franchise_status"] and b["ido_path"] and b["ido_note"]
        assert 0 < b["ido_fit"] <= 100
        assert b["social"]["views_wan"] > 0 and b["social"]["likes_wan"] > 0
        assert len(b["platforms"]) >= 2 and 0 < b["ugc"] <= 100
        assert b["remix_note"] and b["source_type"] == "演示"
    # 按 热度×50% + 适配×100 排序
    keys = [b["social"]["views_wan"] * 0.5 + b["ido_fit"] * 100 for b in d["brands"]]
    assert keys == sorted(keys, reverse=True)


def test_trend_social_attached(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_trend(db)
    for s in d["snacks"]:
        soc = s["social"]
        assert soc and soc["views"] > 0 and soc["likes"] > 0 and soc["shares"] > 0
        assert len(soc["platforms"]) >= 2 and soc["remix"]


def test_hotbrand_seed_idempotent(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    seed_hotbrand(conn)
    seed_hotbrand(conn)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM hot_brand").fetchone()[0]
    conn.close()
    assert n == 12


def test_hotbrand_empty_db(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    migrate_hotbrand(conn)
    conn.close()
    assert "error" in build_hotbrand(db)
