from datetime import date

import pytest

from nbo.dashboard import _worst_cert, build_dashboard
from nbo.db import seed

STORE = "store-jkt-2000"
TODAY = date(2026, 10, 19)


@pytest.fixture()
def db(tmp_path):
    p = tmp_path / "t.db"
    seed(p)
    return p


def test_worst_cert_priority():
    certs = [{"status": "valid", "expiry_date": "2027-01-01"},
             {"status": "valid", "expiry_date": "2026-11-01"}]
    assert _worst_cert(certs, TODAY) == "expiring"
    assert _worst_cert([{"status": "withdrawn", "expiry_date": "2028-01-01"}], TODAY) == "withdrawn"
    assert _worst_cert([], TODAY) == "none"
    assert _worst_cert([{"status": "valid", "expiry_date": "2026-01-01"}], TODAY) == "expired"


def test_dashboard_kpis_and_scenarios(db):
    d = build_dashboard(db, STORE, today=TODAY)
    by_id = {s["id"]: s for s in d["skus"]}
    assert len(by_id) == 8
    # SKU005 在库为 0 → 缺货 + 有补货建议
    assert by_id["SKU005"]["status"] == "out_of_stock"
    assert by_id["SKU005"]["suggest_qty"] > 0
    # SKU002 批次 2026-10-28 到期 → 近效期数量 > 0
    assert by_id["SKU002"]["near_expiry_qty"] == 380
    # SKU003 证书已过期
    assert by_id["SKU003"]["cert_status"] == "expired"
    # SKU001 有 5 天销售记录 → 有日均销量
    assert by_id["SKU001"]["avg_daily"] == 28.2
    # KPI 汇总
    assert d["kpis"]["on_hand_total"] == sum(s["on_hand"] for s in d["skus"])
    assert d["kpis"]["out_of_stock"] == 1
    assert d["kpis"]["cert_alert"] >= 2  # SKU002 临期 + SKU003 过期


def test_dashboard_unknown_store(db):
    with pytest.raises(ValueError):
        build_dashboard(db, "no-such-store", today=TODAY)
