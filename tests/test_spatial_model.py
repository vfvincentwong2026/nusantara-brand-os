import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "web/map/data/spatial_model.json").read_text(encoding="utf-8"))


def test_spatial_funnel_counts_and_real_transit():
    assert len(DATA["cities"]) == 13
    assert len(DATA["candidates"]) == 30
    assert len(DATA["grids"]) == 1470
    assert len(DATA["transit_lines"]) == 27
    assert sum(s["mode"] == "MRT" for s in DATA["stations"]) == 13
    assert all(line["source"] == "Citylines" for line in DATA["transit_lines"])
    assert all("dream" not in line["id"].lower() for line in DATA["transit_lines"])


def test_grid_geometry_and_scores():
    assert DATA["grid_size_m"] == 100
    assert len({g["id"] for g in DATA["grids"]}) == len(DATA["grids"])
    for grid in DATA["grids"]:
        assert len(grid["polygon"]) == 5 and grid["polygon"][0] == grid["polygon"][-1]
        lon, lat = grid["center"]
        width = abs(grid["polygon"][1][0] - grid["polygon"][0][0]) * 111320 * math.cos(math.radians(lat))
        height = abs(grid["polygon"][2][1] - grid["polygon"][1][1]) * 110540
        # Coordinates are rounded to 6 decimals (~0.11 m), so allow rounding error.
        assert math.isclose(width, 100, abs_tol=.12)
        assert math.isclose(height, 100, abs_tol=.12)
        for key in ("demand", "competition", "saturation", "access", "rider_proxy", "cost", "suitability"):
            assert 0 <= grid[key] <= 100
    for candidate in DATA["candidates"]:
        assert set(candidate["mcda"]) == {"demand", "competition", "access", "fulfillment", "cost"}
        assert all(0 <= value <= 100 for value in candidate["mcda"].values())
        assert len(candidate["grid_ids"]) == 49


def test_sources_and_proxy_boundaries_are_explicit():
    assert {"beverage", "poi", "transit", "rail", "roads_water"} <= set(DATA["sources"])
    assert {"purchase", "rent", "rider", "saturation", "compliance"} <= set(DATA["proxy_notes"])
    assert "非官方收入统计" in DATA["proxy_notes"]["purchase"]
    assert "非挂牌租金" in DATA["proxy_notes"]["rent"]
    assert "非平台实测" in DATA["proxy_notes"]["rider"]
    assert "不绘制虚构" in DATA["proxy_notes"]["compliance"]


def test_map_uses_spatial_stack_and_deploys_all_assets():
    html = (ROOT / "web/map/index.html").read_text(encoding="utf-8")
    script = (ROOT / "web/map/spatial.js").read_text(encoding="utf-8")
    deploy = (ROOT / "scripts/deploy.py").read_text(encoding="utf-8")
    for asset in ("maplibre-gl.js", "deck.gl.min.js", "pmtiles.js", "spatial.js"):
        assert asset in html
        assert (ROOT / "web/map/vendor" / asset).exists() if asset != "spatial.js" else True
    for capability in ("MapboxOverlay", "PolygonLayer", "HeatmapLayer", "routing.openstreetmap.de", "querySourceFeatures", "compliance-rings"):
        assert capability in script
    assert "spatial_model.json" in deploy and "web/map/vendor" in deploy
