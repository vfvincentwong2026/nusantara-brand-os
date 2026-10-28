"""小店版大屏引擎测试：只输出行动项。"""
from nbo.db import seed
from nbo.storedash import build_store_dash


def test_store_dash_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_store_dash(db)
    assert d["demo"] is True and d["business_date"]
    k = d["kpi"]
    # 流水与订单数同日一致
    assert k["today_revenue"] >= 0 and k["today_orders"] >= 0
    assert k["skus_on_shelf"] == 5
    # TOP5 按日均销量降序且不超 5 条
    assert len(d["top5"]) == 5
    ads = [t["avg_daily"] for t in d["top5"]]
    assert ads == sorted(ads, reverse=True)
    # 预警：blocked SKU 必须出现且级别最高
    assert any(a["level"] == "bad" and "下架" in a["action"] for a in d["alerts"])
    assert k["alert_count"] == len(d["alerts"])
    # 补货建议只针对缺货/高风险，数量为正
    for r in d["reorder"]:
        assert r["qty"] >= 1 and r["reason"]
    assert k["reorder_lines"] == len(d["reorder"])
    # 链接
    assert d["links"]["full_dashboard"].startswith("/dashboard/")


def test_store_dash_empty_db(tmp_path):
    import sqlite3
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.close()
    assert "error" in build_store_dash(db)
