"""概念落地评分引擎测试：7 因子归因 + 五步链路方案。"""
from nbo.db import seed
from nbo.launch import build_launch


def test_launch_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_launch(db)
    assert d["demo"] is True
    # 7 因子权重合计 100
    assert len(d["factors"]) == 7
    assert sum(f["weight"] for f in d["factors"]) == 100
    # 9 款全部评分、降序、分数合法、带评级
    ranked = d["ranked"]
    assert len(ranked) == 9
    totals = [r["total"] for r in ranked]
    assert totals == sorted(totals, reverse=True)
    for r in ranked:
        assert 0 <= r["total"] <= 100
        assert len(r["scores"]) == 7
        assert all(0 <= v <= 100 for v in r["scores"].values())
        assert r["grade"] in ("S", "A", "B", "C")
    # 总分 = 因子加权和
    w = {f["id"]: f["weight"] for f in d["factors"]}
    top = ranked[0]
    assert abs(top["total"] - sum(top["scores"][k] * w[k] for k in w) / 100) < 0.2
    # 首选方案完整：五步 + 集装箱 + 供应链 + 交付物
    p = d["plan"]
    assert len(p["steps"]) == 5
    assert [s["no"] for s in p["steps"]] == [1, 2, 3, 4, 5]
    assert p["container"]["tier"] and p["container"]["link"] == "/case/"
    assert p["supply_chain"]["compliance_lead"]
    assert len(p["deliverables"]) >= 5
    # 供应链权重最高（落地的硬约束）
    assert max(d["factors"], key=lambda f: f["weight"])["id"] == "f4"


def test_launch_empty_db(tmp_path):
    import sqlite3
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.close()
    d = build_launch(db)
    assert "error" in d
