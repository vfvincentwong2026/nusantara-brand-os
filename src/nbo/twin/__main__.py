"""python -m nbo.twin --store store-jkt-2000 --out web/twin/data/planogram-2000.json"""
import argparse
import json
import sqlite3
from pathlib import Path

from nbo.twin import write_layout

p = argparse.ArgumentParser()
p.add_argument("--db", default="nbo.db")
p.add_argument("--out-dir", default="web/twin/data")
a = p.parse_args()

conn = sqlite3.connect(a.db)
stores = conn.execute("SELECT id, name, size_sqm, fresh_ratio FROM stores").fetchall()
conn.close()

out_dir = Path(a.out_dir)
for sid, name, size, fresh in stores:
    slug = str(int(size))
    data = write_layout(out_dir / f"planogram-{slug}.json",
                        {"id": sid, "name": name, "size_sqm": size, "fresh_ratio": fresh})
    print(f"planogram-{slug}.json: {len(data['shelves'])} shelves, {data['footprint']['w']}x{data['footprint']['h']}m")
