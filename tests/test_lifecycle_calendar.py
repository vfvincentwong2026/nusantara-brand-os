from datetime import date

from nbo.lifecycle import FEFOManager
from nbo.model import Batch
from nbo.calendar import IndonesiaCalendar


def _batch(bid, expiry):
    return Batch(id=bid, sku_id="sku1", store_id="s1", qty=10,
                 receive_date="2026-01-01", expiry_date=expiry)


def test_fefo_sorts_earliest_expiry_first():
    m = FEFOManager()
    batches = [_batch("b2", "2026-12-01"), _batch("b1", "2026-06-01"), _batch("b3", "2027-03-01")]
    assert [b.id for b in m.sort_batches(batches)] == ["b1", "b2", "b3"]


def test_near_expiry_within_threshold():
    m = FEFOManager()
    from datetime import timedelta
    near_expiry = (date.today() + timedelta(days=10)).isoformat()
    near = _batch("b1", near_expiry)
    far = _batch("b2", "2099-01-01")
    assert m.near_expiry(near, days_threshold=30) is True
    assert m.near_expiry(far, days_threshold=30) is False


def test_calendar_ramadan_2026():
    c = IndonesiaCalendar()
    assert c.is_ramadan("2026-02-20") is True
    assert c.is_ramadan("2026-04-01") is False


def test_calendar_events_present():
    c = IndonesiaCalendar()
    events = c.get_events()
    assert {"ramadan", "eid", "harbolnas", "independence_day"} <= set(events)
