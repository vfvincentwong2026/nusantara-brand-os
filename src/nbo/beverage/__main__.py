"""python -m nbo.beverage --out web/map/data/beverage_index.json"""
import argparse
from nbo.beverage import build_beverage, write_json

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
a = p.parse_args()
d = build_beverage()
write_json(d, a.out)
print(f"beverage: {len(d['brands'])} brands, {len(d['points'])} city points -> {a.out}")
