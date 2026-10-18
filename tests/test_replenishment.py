from nbo.replenishment import ReplenishmentEngine


def test_effective_lead_time_java():
    e = ReplenishmentEngine()
    assert e.effective_lead_time(10, 2, "java") == 11  # 10 + 0.5*2


def test_effective_lead_time_papua():
    e = ReplenishmentEngine()
    assert e.effective_lead_time(10, 2, "papua") == 13  # 10 + 1.5*2


def test_effective_lead_time_unknown_region_defaults_k1():
    e = ReplenishmentEngine()
    assert e.effective_lead_time(10, 2, "bali") == 12


def test_safety_stock_and_rop():
    e = ReplenishmentEngine()
    ss = e.safety_stock(5, 4)          # 1.645 * 5 * sqrt(4) = 16.45
    assert abs(ss - 16.45) < 1e-6
    rop = e.reorder_point(10, 4, ss)   # 10*4 + 16.45 = 56.45
    assert abs(rop - 56.45) < 1e-6


def test_suggest_bundle():
    e = ReplenishmentEngine()
    r = e.suggest(avg_daily_demand=10, demand_std=5, lt_mean=10, lt_std=2, island_region="java")
    assert r["lt_eff"] == 11
    assert abs(r["safety_stock"] - 1.645 * 5 * (11 ** 0.5)) < 1e-6
    assert r["reorder_point"] == 10 * 11 + r["safety_stock"]
