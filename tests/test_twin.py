import json

import pytest

from nbo.twin import generate_layout

STORE_2000 = {"id": "s2", "name": "T", "size_sqm": 2000, "fresh_ratio": 0.28}
STORE_500 = {"id": "s5", "name": "T", "size_sqm": 500, "fresh_ratio": 0.18}
STORE_5000 = {"id": "s50", "name": "T", "size_sqm": 5000, "fresh_ratio": 0.33}


def test_footprint_area_close_to_size():
    d = generate_layout(STORE_2000)
    fp = d["footprint"]
    assert abs(fp["w"] * fp["h"] - 2000) < 50


def test_aisle_width_by_scale():
    assert generate_layout(STORE_500)["aisle_width_m"] == 2.0
    assert generate_layout(STORE_2000)["aisle_width_m"] == 3.0
    assert generate_layout(STORE_5000)["aisle_width_m"] == 3.5


def test_layers_within_benchmark():
    d = generate_layout(STORE_2000)
    layers = {s["layer_count"] for s in d["shelves"]}
    assert layers <= {5, 6}


def test_all_shelves_inside_footprint():
    for store in (STORE_500, STORE_2000, STORE_5000):
        d = generate_layout(store)
        fp = d["footprint"]
        for s in d["shelves"]:
            assert 0 <= s["x"] and s["x"] + s["w"] <= fp["w"] + 0.01
            assert 0 <= s["y"] - s["h"] / 2 and s["y"] + s["h"] / 2 <= fp["h"] + 0.01


def test_500sqm_no_apparel_zone():
    d = generate_layout(STORE_500)
    assert "apparel" not in d["zones"]
    assert {"food", "non-food"} <= set(d["zones"])


def test_5000sqm_has_apparel():
    d = generate_layout(STORE_5000)
    assert "apparel" in d["zones"]


def test_heat_value_range_and_fresh_highest():
    d = generate_layout(STORE_2000)
    heats = [s["heat_value"] for s in d["shelves"]]
    assert all(0 < v <= 0.95 for v in heats)
    zone_avg = {}
    for s in d["shelves"]:
        zone_avg.setdefault(s["zone"], []).append(s["heat_value"])
    assert (sum(zone_avg["fresh"]) / len(zone_avg["fresh"])
            > sum(zone_avg["non-food"]) / len(zone_avg["non-food"]))


def test_shelf_capacity_scales_with_store():
    n500 = len(generate_layout(STORE_500)["shelves"])
    n5000 = len(generate_layout(STORE_5000)["shelves"])
    assert n5000 > n500 > 0
