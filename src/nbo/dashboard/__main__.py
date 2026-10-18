"""python -m nbo.dashboard --db nbo.db --store store-jkt-2000 --out web/dashboard/data/dashboard.json"""
import argparse
import json

from nbo.dashboard import write_dashboard

p = argparse.ArgumentParser()
p.add_argument("--db", default="nbo.db")
p.add_argument("--store", default="store-jkt-2000")
p.add_argument("--out", required=True)
p.add_argument("--lt-mean", type=float, default=7)
p.add_argument("--lt-std", type=float, default=2)
a = p.parse_args()

data = write_dashboard(a.out, db_path=a.db, store_id=a.store,
                       lt_mean=a.lt_mean, lt_std=a.lt_std)
print(json.dumps(data["kpis"], ensure_ascii=False))
print(f"written: {a.out} ({len(data['skus'])} skus)")
