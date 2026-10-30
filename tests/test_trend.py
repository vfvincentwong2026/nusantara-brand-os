"""趋势侦察引擎测试：六区域热点零食 + 网红视角 + 印尼适配。"""
import sqlite3

from nbo.db import seed
from nbo.trend import build_trend, migrate_trend, seed_trend


def test_trend_seed_and_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_trend(db)
    assert d["demo"] is True and d["window"] == "近 3 个月"
    assert len(d["regions"]) == 6 and len(d["snacks"]) == 9
    # 每行都有来源标记与信号
    assert all(s["source_type"] for s in d["snacks"])
    assert all(len(s["heat_signals"]) >= 2 for s in d["snacks"])
    # 总榜按热度降序
    heats = [s["heat"] for s in d["snacks"]]
    assert heats == sorted(heats, reverse=True)
    # 区域分组完整
    assert sum(len(v) for v in d["by_region"].values()) == 9
    # 反向指导：优先复制清单非空、适配分合法
    assert len(d["guidance"]["priority_copies"]) == 5
    assert all(0 <= p["indo_fit"] <= 100 for p in d["guidance"]["priority_copies"])
    assert len(d["guidance"]["directions"]) >= 3


def test_trend_empty_db(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    migrate_trend(conn)
    conn.close()
    assert "error" in build_trend(db)


def test_trend_seed_idempotent(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    seed_trend(conn)
    seed_trend(conn)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM trend_snack").fetchone()[0]
    conn.close()
    assert n == 9
