import json
from pathlib import Path

from nbo.beverage import build_beverage, price_index

ROOT = Path(__file__).resolve().parent.parent


def test_beverage_dataset_and_math():
    d = build_beverage()
    assert len(d["brands"]) >= 10
    assert len(d["points"]) == len(d["brands"]) * len(d["cities"])
    assert d["brands"][0]["id"] == "mixue"
    assert d["brands"][1]["id"] == "momoyo"
    for p in d["points"]:
        assert p["location_precision"] in {"city_model", "osm_named_place"}
        if p["location_precision"] == "osm_named_place":
            assert p["location_source"] and p["location_name"]
        assert p["price_idr"] > 0 and p["jakarta_price_idr"] > 0
        assert p["price_index"] == price_index(p["price_idr"], p["jakarta_price_idr"])
        assert isinstance(p["lat"], float) and isinstance(p["lon"], float)
        if p["city"] == "雅加达":
            assert p["price_index"] == 100
        if p["price_basis"] == "公开菜单参考":
            assert p["price_source"]


def test_beverage_output_file_current():
    d = json.loads((ROOT / "web/map/data/beverage_index.json").read_text(encoding="utf-8"))
    assert len(d["brands"]) >= 10
    assert d["location_note"]
    assert "非全量真实门店" in d["data_mode"]
