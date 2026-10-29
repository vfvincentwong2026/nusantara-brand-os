"""装配方案对比引擎测试。"""
from nbo.assembly import CNY_IDR, DIMS, build_assembly


def test_scheme_count_and_fields():
    d = build_assembly()
    assert len(d["schemes"]) == 4
    for s in d["schemes"]:
        for k in ["id", "form", "area_sqm", "total_lo", "total_hi", "weeks",
                  "permit", "supply", "pros", "cons", "fit", "fit_budget"]:
            assert k in s, f"{s['id']} 缺少 {k}"
        assert len(s["breakdown"]) == len(DIMS)


def test_total_is_sum_of_breakdown():
    for s in build_assembly()["schemes"]:
        lo = sum(b["lo"]["wan_cny"] for b in s["breakdown"])
        hi = sum(b["hi"]["wan_cny"] for b in s["breakdown"])
        assert abs(lo - s["total_lo"]["wan_cny"]) < 0.05
        assert abs(hi - s["total_hi"]["wan_cny"]) < 0.05


def test_idr_conversion_consistency():
    for s in build_assembly()["schemes"]:
        for b in s["breakdown"]:
            expect = round(b["lo"]["wan_cny"] * CNY_IDR / 100)
            assert b["lo"]["idr_m"] == expect


def test_budget_fit_flag_matches_range():
    d = build_assembly()
    by_id = {s["id"]: s for s in d["schemes"]}
    for sid in d["budget_fit_ids"]:
        s = by_id[sid]
        assert s["fit_budget"] is True
        assert s["total_lo"]["wan_cny"] <= 10 and s["total_mid"]["wan_cny"] <= 12


def test_deterministic():
    a = build_assembly()
    b = build_assembly()
    assert a == b
