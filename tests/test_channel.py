from nbo.channel import competitor_density, coverage_gaps, haversine_m
from nbo.db import seed

PTS = [
    {"id": "W1", "type": "warung", "lat": -6.2088, "lon": 106.8456, "grade": "gold", "final_score": 85, "name": "W1", "sales_step": 1, "city": "Jakarta"},
    {"id": "W2", "type": "warung", "lat": -6.2089, "lon": 106.8457, "grade": "silver", "final_score": 70, "name": "W2", "sales_step": 0, "city": "Jakarta"},
    {"id": "W3", "type": "warung", "lat": -6.2600, "lon": 106.8100, "grade": "silver", "final_score": 65, "name": "W3", "sales_step": 0, "city": "Jakarta"},
    {"id": "C1", "type": "alfamart", "lat": -6.20885, "lon": 106.84565, "grade": "normal", "final_score": 0, "name": "C1", "sales_step": 0, "city": "Jakarta"},
]


def test_haversine_known_distance():
    # 同点 0；赤道 1 经度 ≈ 111195 m
    assert haversine_m(0, 0, 0, 0) == 0
    assert abs(haversine_m(0, 0, 0, 1) - 111195) < 100


def test_competitor_density_radius():
    d = competitor_density(PTS, radius_m=500)
    assert d["W1"] == 1   # C1 紧贴 W1
    assert d["W2"] == 1   # C1 也在 W2 的 500m 内
    assert d["W3"] == 0   # 远在 Kemang


def test_coverage_gaps_sorted_gold_first():
    d = competitor_density(PTS, radius_m=500)
    gaps = coverage_gaps(PTS, d)
    ids = [g["id"] for g in gaps]
    assert "W3" in ids and "W1" not in ids and "W2" not in ids
    # gold 缺口排在 silver 前
    mixed = PTS + [{"id": "W4", "type": "warung", "lat": -6.30, "lon": 106.80,
                    "grade": "gold", "final_score": 95, "name": "W4", "sales_step": 0, "city": "Jakarta"}]
    gaps2 = coverage_gaps(mixed, competitor_density(mixed, 500))
    assert gaps2[0]["id"] == "W4"


def test_build_map_from_seeded_db(tmp_path):
    from nbo.channel import build_map
    db = tmp_path / "t.db"
    seed(db)
    m = build_map(db, radius_m=500)
    assert m["kpis"]["warung_count"] == 14
    assert m["kpis"]["competitor_count"] == 6
    assert m["kpis"]["gap_count"] >= 1
    assert "Jakarta" in m["by_city"] and "Bandung" in m["by_city"]
    warung_pts = [p for p in m["points"] if p["type"] == "warung"]
    assert all("competitors_within" in p for p in warung_pts)
