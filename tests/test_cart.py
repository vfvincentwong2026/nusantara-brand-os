"""移动推车加盟引擎测试。"""
from nbo.cart import CNY_IDR, build_cart


def test_three_cart_models():
    d = build_cart()
    assert len(d["carts"]) == 3
    names = [c["name"] for c in d["carts"]]
    assert any("手推" in n for n in names)
    assert any("电动车" in n or "电动" in n for n in names)
    assert any("咖啡" in n for n in names)


def test_startup_is_sum_of_parts():
    for c in build_cart()["carts"]:
        lo = c["deposit"]["wan_cny"][0] + c["first_stock"]["wan_cny"][0] + c["cert"]["wan_cny"][0]
        hi = c["deposit"]["wan_cny"][1] + c["first_stock"]["wan_cny"][1] + c["cert"]["wan_cny"][1]
        assert abs(lo - c["startup"]["wan_cny"][0]) < 0.05
        assert abs(hi - c["startup"]["wan_cny"][1]) < 0.05


def test_entry_barrier_below_store():
    """推车业态启动门槛须低于开店方案最低档（8–10 万包的下探）。"""
    carts = build_cart()["carts"]
    assert all(c["startup"]["wan_cny"][1] <= 5.5 for c in carts)
    assert min(c["startup"]["wan_cny"][0] for c in carts) <= 3.0


def test_payback_model_consistency():
    """回本月数须能被 日销×毛利率×30 的月毛利覆盖（±1 月容差）。"""
    for c in build_cart()["carts"]:
        inv_mid = sum(c["startup"]["wan_cny"]) / 2 * 10000  # CNY
        daily_mid = sum(c["daily_sales_idr"]) / 2 * 1000 / CNY_IDR  # 千IDR/日 → CNY/日
        monthly_profit = daily_mid * c["gross_margin"] * 30
        pb_calc = inv_mid / monthly_profit
        lo, hi = c["payback_months"]
        assert lo - 1 <= pb_calc <= hi + 1, f"{c['id']} 测算 {pb_calc:.1f} 月超区间 {lo}-{hi}"


def test_idr_conversion():
    for c in build_cart()["carts"]:
        for part in ["startup", "deposit", "rent_mo", "first_stock", "cert"]:
            lo, hi = c[part]["wan_cny"]
            assert c[part]["idr_m"] == [int(round(lo * CNY_IDR / 100)),
                                        int(round(hi * CNY_IDR / 100))]


def test_deterministic():
    assert build_cart() == build_cart()
