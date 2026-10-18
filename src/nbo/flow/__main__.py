"""python -m nbo.flow --db nbo.db --out-dir web/twin/data"""
import argparse
import json
import sqlite3
from pathlib import Path

from nbo.flow import write_flow
from nbo.twin import generate_layout

p = argparse.ArgumentParser()
p.add_argument("--db", default="nbo.db")
p.add_argument("--out-dir", default="web/twin/data")
p.add_argument("--customers", type=int, default=400)
a = p.parse_args()

conn = sqlite3.connect(a.db)
stores = conn.execute("SELECT id, name, size_sqm, fresh_ratio FROM stores").fetchall()
conn.close()

out_dir = Path(a.out_dir)
for sid, name, size, fresh in stores:
    slug = str(int(size))
    plano = generate_layout({"id": sid, "name": name, "size_sqm": size, "fresh_ratio": fresh})
    data = write_flow(out_dir / f"flow-{slug}.json", plano, n_customers=a.customers)
    total = sum(data["grid"]["counts"])
    print(f"flow-{slug}.json: {len(data['waypoints'])} waypoints, {total} visits")
