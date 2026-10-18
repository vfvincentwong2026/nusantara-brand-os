"""python -m nbo.channel --db nbo.db --out web/map/data/channel_map.json"""
import argparse
import json

from nbo.channel import write_map

p = argparse.ArgumentParser()
p.add_argument("--db", default="nbo.db")
p.add_argument("--out", required=True)
p.add_argument("--radius", type=float, default=500)
a = p.parse_args()

data = write_map(a.out, db_path=a.db, radius_m=a.radius)
print(json.dumps(data["kpis"], ensure_ascii=False))
print(f"written: {a.out} ({len(data['points'])} points, {len(data['gaps'])} gaps)")
