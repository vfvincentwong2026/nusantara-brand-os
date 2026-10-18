import pytest

from nbo.space import dominant_map, solve_allocation
from nbo.twin import generate_layout

PLANO = generate_layout({"id": "s", "name": "T", "size_sqm": 2000, "fresh_ratio": 0.28})
SHELVES = PLANO["shelves"][::8]  # 跨 zone 抽样，小规模加速测试

SKUS = [
    {"id": "A", "name": "A", "category": "零食", "cost_idr": 5000, "sell_price_idr": 10000, "forecast_daily": 30},
    {"id": "B", "name": "B", "category": "零食", "cost_idr": 3000, "sell_price_idr": 5000, "forecast_daily": 60},
    {"id": "C", "name": "C", "category": "零食", "cost_idr": 15000, "sell_price_idr": 28000, "forecast_daily": 5},
]


def test_solves_and_respects_capacity():
    r = solve_allocation(SHELVES, SKUS)
    assert r["status"] in ("optimal", "feasible")
    slots = {s["id"]: int(s["w"] / 0.4) * s["layer_count"] for s in SHELVES}
    used = {row["shelf_id"]: sum(e["facings"] for e in row["skus"]) for row in r["alloc"]}
    for sid, u in used.items():
        assert u <= slots[sid]


def test_demand_cap_bounds_facings():
    r = solve_allocation(SHELVES, SKUS)
    for sku in SKUS:
        cap = max(4, int(-(-sku["forecast_daily"] // 8.0)))
        total = sum(e["facings"] for row in r["alloc"] for e in row["skus"] if e["sku_id"] == sku["id"])
        assert total <= cap


def test_beat_naive_baseline():
    r = solve_allocation(SHELVES, SKUS)
    assert r["profit_after_idr"] >= r["profit_before_idr"] > 0


def test_low_demand_sku_may_be_dropped():
    r = solve_allocation(SHELVES, SKUS)
    # C 需求 5/天 < 4 面位×8=32 的供给效率，可能被最小门槛拒之门外或仅保底
    total_c = sum(e["facings"] for row in r["alloc"] for e in row["skus"] if e["sku_id"] == "C")
    assert total_c in (0, 4)


def test_deterministic():
    a = solve_allocation(SHELVES, SKUS)
    b = solve_allocation(SHELVES, SKUS)
    assert a["profit_after_idr"] == b["profit_after_idr"]
    assert dominant_map(a["alloc"]) == dominant_map(b["alloc"])


def test_dominant_map_shape():
    r = solve_allocation(SHELVES, SKUS)
    dm = dominant_map(r["alloc"])
    assert all(v in {"A", "B", "C"} for v in dm.values())
