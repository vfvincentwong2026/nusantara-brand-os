from datetime import date, timedelta

from nbo.forecast import ForecastEngine

TODAY = date(2026, 10, 19)
RAMADAN = date(2026, 2, 18)
EID = date(2026, 3, 20)


def _daily(n=60, qty=10, start=None):
    start = start or (TODAY - timedelta(days=n))
    return {start + timedelta(days=i): qty + (i % 7) for i in range(n)}


def test_event_factor_ramadan_ramp():
    e = ForecastEngine()
    assert e._event_factor(RAMADAN) == 1.10
    assert e._event_factor(RAMADAN + timedelta(days=8)) == 1.20
    assert e._event_factor(RAMADAN + timedelta(days=22)) == 1.50


def test_event_factor_pre_eid_escalates():
    e = ForecastEngine()
    assert e._event_factor(EID - timedelta(days=1)) == 1.90
    assert e._event_factor(EID - timedelta(days=7)) == 1.10


def test_event_factor_eid_week_with_mudik():
    e = ForecastEngine(mudik_offset=-0.1)   # 城市店返乡净流出
    assert abs(e._event_factor(EID + timedelta(days=2)) - 0.50) < 1e-9
    e2 = ForecastEngine(mudik_offset=0.5)   # 目的地店流入
    assert abs(e2._event_factor(EID + timedelta(days=2)) - 1.10) < 1e-9


def test_event_factor_normal_day_is_1():
    e = ForecastEngine()
    assert e._event_factor(TODAY) == 1.0
    assert e._event_factor(date(2026, 12, 12)) == 1.50  # harbolnas


def test_baseline_prefers_same_dow():
    e = ForecastEngine()
    daily = {}
    d = TODAY - timedelta(days=28)
    while d < TODAY:
        daily[d] = 50 if d.isoweekday() == 1 else 5  # 周一 50，其他 5
        d += timedelta(days=1)
    nxt_monday = TODAY + timedelta(days=7)  # TODAY 本身是周一
    assert e.baseline(daily, nxt_monday) == 50


def test_baseline_fallback_to_window_when_sparse():
    e = ForecastEngine()
    daily = {TODAY - timedelta(days=1): 10, TODAY - timedelta(days=2): 20}
    assert e.baseline(daily, TODAY) == 15


def test_forecast_applies_factor():
    e = ForecastEngine()
    daily = _daily(qty=10)
    preds = e.forecast(daily, 3, start=EID - timedelta(days=1))
    assert preds[0]["factor"] == 1.90
    assert preds[0]["predicted"] == round(preds[0]["baseline"] * 1.90, 1)


def test_backtest_mape():
    e = ForecastEngine()
    daily = _daily(n=40, qty=10, start=TODAY - timedelta(days=40))
    r = e.backtest(daily, horizon_days=7, asof=TODAY - timedelta(days=7))
    assert r["n"] == 7
    assert r["mape"] is not None and 0 <= r["mape"] < 0.5  # 平稳序列上应较准


def test_backtest_no_actual_returns_none():
    e = ForecastEngine()
    assert e.backtest({}, asof=TODAY)["mape"] is None
