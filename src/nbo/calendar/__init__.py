class IndonesiaCalendar:
    def __init__(self):
        self.events = {
            "ramadan": {"start": "2026-02-18", "end": "2026-03-19", "weight": "极高"},
            "eid": {"start": "2026-03-20", "end": "2026-03-21", "weight": "极高"},
            "harbolnas": {"start": "2026-12-12", "end": "2026-12-12", "weight": "高"},
            "independence_day": {"start": "2026-08-17", "end": "2026-08-17", "weight": "中"},
        }

    def get_events(self):
        return self.events

    def is_ramadan(self, date_str: str) -> bool:
        return self.events["ramadan"]["start"] <= date_str <= self.events["ramadan"]["end"]
