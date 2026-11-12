import json
from pathlib import Path

from nbo.beverage import build_beverage, price_index

ROOT = Path(__file__).resolve().parent.parent


def test_beverage_dataset_and_math():
    d = build_beverage()
    assert len(d["brands"]) == 20
    assert sum(b["category"] == "奶茶" for b in d["brands"]) == 10
    assert sum(b["category"] == "咖啡" for b in d["brands"]) == 10
    assert len(d["cities"]) == 178
    assert d["brands"][0]["id"] == "mixue"
    assert d["brands"][1]["id"] == "momoyo"
    assert "tianlala" in {b["id"] for b in d["brands"]}
    assert "kokumi" not in {b["id"] for b in d["brands"]}
    google = [p for p in d["points"] if p["location_precision"] == "google_verified"]
    assert len(google) == 1987
    assert {p["brand_id"] for p in google} == {"mixue", "momoyo", "tianlala"}
    assert sum(p["brand_id"] == "mixue" for p in google) == 571
    assert sum(p["brand_id"] == "momoyo" for p in google) == 1205
    tianlala = [p for p in google if p["brand_id"] == "tianlala"]
    assert len(tianlala) == 211 and len({p["city"] for p in tianlala}) == 31
    island_counts = {name: sum(p["island"] == name for p in google) for name in ["勿里洞岛", "龙目岛", "松巴哇岛", "松巴岛"]}
    assert island_counts == {"勿里洞岛": 12, "龙目岛": 55, "松巴哇岛": 4, "松巴岛": 4}
    assert len({p["google_place_id"] for p in google}) == len(google)
    assert len(d["points"]) == 142 + len(google)
    assert len({p["id"] for p in d["points"]}) == len(d["points"])
    others = [p for p in d["points"] if p["brand_id"] not in {"mixue", "momoyo", "tianlala"}]
    assert len(others) == 136 and all(p["location_precision"] == "city_model" for p in others)
    assert not any(p["brand_id"] == "tianlala" and p["location_precision"] == "city_model" for p in d["points"])
    assert next(p for p in google if p["id"] == "mixue-makassar")["business_status"] == "永久停业"
    for p in d["points"]:
        assert p["location_precision"] in {"city_model", "osm_candidate", "google_verified"}
        if p["location_precision"] == "google_verified":
            assert p["location_source"].startswith("https://www.google.com/maps/place/")
            assert p["google_place_id"] and p["location_name"]
            assert f"!3d{p['lat']}" in p["location_source"]
            assert f"!4d{p['lon']}" in p["location_source"]
        if p["location_precision"] == "osm_candidate":
            assert p["location_source"].startswith("https://www.openstreetmap.org/")
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
