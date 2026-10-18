"""WarungScout 评分模型测试（融合自 warungscout/docs/SCORING_MODEL.md）。"""
from nbo.scoring import WEIGHTS, score_warung


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
    assert set(WEIGHTS) == {"location", "activity", "competition", "cooperation",
                            "digital", "owner", "region"}


def _strong_signals(city="Jakarta"):
    return {
        "facilities": {"schools": 1, "factories": 1, "offices": 1, "residences": 1, "transits": 1},
        "gm_rating": 4.5, "gm_reviews": 120, "wa_active": True, "participated_promo": True,
        "asked_new_product": True, "warung_competitors_500m": 1,
        "reply_rate": 0.9, "visit_feedback": "positive", "referral_given": True,
        "qris": True, "wa_reply": "fast", "smartphone": True, "photos": True, "video": True,
        "interested_inventory": True, "app_ordering": True,
        "owner_profile": {"age_20_35": True, "expansion_plan": True, "main_income": True,
                          "female": True, "high_school_plus": True, "local": True},
        "city": city,
    }


def test_strong_warung_is_gold():
    r = score_warung(_strong_signals())
    assert r["final_score"] >= 80
    assert r["grade"] == "gold"
    assert all(0 <= v <= 100 for v in r["dims"].values())


def test_no_history_neutral_50():
    r = score_warung({"no_history": True, "city": "Jakarta"})
    assert r["dims"]["cooperation"] == 50
    assert r["dims"]["digital"] == 50
    assert r["dims"]["owner"] == 50


def test_region_tier_lookup():
    assert score_warung({"no_history": True, "city": "Jakarta"})["dims"]["region"] == 100
    assert score_warung({"no_history": True, "city": "Bandung"})["dims"]["region"] == 80
    assert score_warung({"no_history": True, "city": "Semarang"})["dims"]["region"] == 60
    assert score_warung({"no_history": True, "city": "Sorong"})["dims"]["region"] == 40


def test_grade_thresholds():
    base = _strong_signals()
    # 把各维度压到 60-79 区间：信号全面降档
    weak = dict(base, facilities={"schools": 1, "factories": 0, "offices": 1, "residences": 1, "transits": 0},
                gm_rating=3.6, gm_reviews=25, wa_active=True, participated_promo=False,
                asked_new_product=False, warung_competitors_500m=1, reply_rate=0.5,
                visit_feedback="neutral", referral_given=False, qris=False, wa_reply="fast",
                photos=False, video=False, interested_inventory=False, app_ordering=False,
                owner_profile={"age_20_35": False, "expansion_plan": False, "main_income": False,
                               "female": False, "high_school_plus": False, "local": True})
    r = score_warung(weak)
    assert 60 <= r["final_score"] < 80
    assert r["grade"] == "silver"


def test_seed_and_build_map_use_real_scoring(tmp_path):
    from nbo.channel import build_map
    from nbo.db import seed
    db = tmp_path / "t.db"
    seed(db)
    m = build_map(db, radius_m=500)
    warung_pts = [p for p in m["points"] if p["type"] == "warung"]
    # 种子带信号 → 模型算分；gold 店分数应≥80
    golds = [p for p in warung_pts if p["grade"] == "gold"]
    assert golds and all(p["final_score"] >= 80 for p in golds)
    # dims 与库中存储列一致（非合成回退）
    for p in warung_pts:
        assert p["dims"] == {n: p[f"{n}_score"] for n in p["dims"]}
