"""加盟体系引擎测试：成本包锚定 + 回本模型可审计。"""
from nbo.db import seed
from nbo.franchise import FX, build_franchise


def test_franchise_build(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_franchise(db)
    assert d["demo"] is True and d["fx"]["rmb_to_idr"] == FX
    # 六业态，总投资全部锚定 8–10 万 RMB
    assert len(d["formats"]) == 6
    for f in d["formats"]:
        assert 8.0 <= f["capex_rmb"] <= 10.0, f["name"]
        expect = f["capex_rmb"] * 10_000 * FX
        assert abs(f["capex_idr"] - expect) < 1
        # 成本包拆分合计 = 总投资
        assert abs(sum(f["package"].values()) - f["capex_rmb"]) < 1e-9
        # 回本模型：月净利 = 日销×30×毛利 − 固定，回本 = 总投资/月净利
        profit = f["daily_sales_idr"] * 30 * f["gross_margin_pct"] - f["monthly_fixed_idr"]
        assert abs(f["monthly_profit_idr"] - round(profit)) < 1
        assert abs(f["payback_months"] - round(f["capex_idr"] / profit, 1)) < 0.15
        assert 6 <= f["payback_months"] <= 24  # 合理加盟回本区间
        assert f["source_type"] == "演示"
        assert len(f["supply_chain"]) == 3
    # 品牌库六条，费用/投资为正且带培训与区域
    assert len(d["brands"]) == 6
    for b in d["brands"]:
        assert b["fee_idr"] > 0 and b["invest_idr"] > 0
        assert b["training_level"] and b["fit_regions"]
        assert b["format_name"]  # 业态名 join 成功
        assert any(x["id"] == b["format_id"] for x in d["formats"])


def test_franchise_empty_db(tmp_path):
    import sqlite3
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    from nbo.franchise import migrate_franchise
    migrate_franchise(conn)
    conn.close()
    assert "error" in build_franchise(db)
