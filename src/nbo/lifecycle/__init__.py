from datetime import datetime

class FEFOManager:
    def __init__(self):
        pass

    def sort_batches(self, batches: list):
        return sorted(batches, key=lambda b: b.expiry_date)

    def near_expiry(self, batch, days_threshold: int = 30):
        expiry = datetime.strptime(batch.expiry_date, "%Y-%m-%d")
        today = datetime.today()
        return (expiry - today).days <= days_threshold
