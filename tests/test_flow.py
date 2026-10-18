import json
import random

from nbo.flow import build_waypoints, simulate, zone_weights
from nbo.twin import generate_layout

STORE = {"id": "s", "name": "T", "size_sqm": 2000, "fresh_ratio": 0.28}
PLANO = generate_layout(STORE)


def test_waypoints_inside_footprint():
    wps = build_waypoints(PLANO)
    assert wps
    W, H = PLANO["footprint"]["w"], PLANO["footprint"]["h"]
    for w in wps:
        assert 0 <= w["x"] <= W and 0 <= w["y"] <= H
        assert w["zone"] in PLANO["zones"]


def test_waypoints_on_aisle_centers():
    wps = build_waypoints(PLANO)
    ys = sorted({w["y"] for w in wps})
    # 通道间距 = aisle + 1.2
    gaps = [round(ys[i + 1] - ys[i], 1) for i in range(len(ys) - 1)]
    assert all(abs(g - 4.2) < 0.15 for g in gaps)


def test_zone_weights_normalized():
    zw = zone_weights(PLANO)
    assert abs(sum(zw.values()) - 1.0) < 1e-6
    assert zw["food"] > zw["non-food"]


def test_simulation_deterministic():
    a = simulate(PLANO, n_customers=50, seed=7)
    b = simulate(PLANO, n_customers=50, seed=7)
    assert a["grid"]["counts"] == b["grid"]["counts"]
    c = simulate(PLANO, n_customers=50, seed=8)
    assert a["grid"]["counts"] != c["grid"]["counts"]


def test_entrance_and_interior_visited():
    d = simulate(PLANO, n_customers=100, seed=1)
    g = d["grid"]
    total = sum(g["counts"])
    assert total > 100  # 每条路径多个点
    entrance_cell = int(d["entrance"]["y"]) * g["cols"] + int(d["entrance"]["x"])
    assert g["counts"][entrance_cell] >= 100  # 每位顾客必经入口（进出各一次）


def test_all_visits_within_bounds():
    d = simulate(PLANO, n_customers=80, seed=3)
    g = d["grid"]
    W, H = PLANO["footprint"]["w"], PLANO["footprint"]["h"]
    assert g["cols"] == int(W) + 1 and g["rows"] == int(H) + 1
    for i, v in enumerate(g["counts"]):
        if v:
            assert 0 <= i < g["cols"] * g["rows"]
