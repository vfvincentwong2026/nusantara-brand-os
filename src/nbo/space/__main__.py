"""python -m nbo.space --db nbo.db --store store-jkt-2000 --out web/twin/data/optimize-2000.json"""
import argparse
import json
import sqlite3
from pathlib import Path

from nbo.space import solve_allocation
from nbo.twin import generate_layout

p = argparse.ArgumentParser()
p.add_argument("--db", default="nbo.db")
p.add_argument("--store", default="store-jkt-2000")
p.add_argument("--out-dir", default="web/twin/data")
a = p.parse_args()

conn = sqlite3.connect(a.db)
conn.row_factory = sqlite3.Row
store = conn.execute("SELECT * FROM stores WHERE id=?", (a.store,)).fetchone()
skus = [dict(r) for r in conn.execute("SELECT * FROM skus")]
conn.close()
assert store, f"门店不存在: {a.store}"

plano = generate_layout({"id": store["id"], "name": store["name"],
                         "size_sqm": store["size_sqm"], "fresh_ratio": store["fresh_ratio"]})
# 需求：skus 表无销量字段，从 sales 表算近 14 天日均（与 dashboard 同口径）
conn_sales = sqlite3.connect(a.db)
for s in skus:
    r = conn_sales.execute(
        "SELECT AVG(qty) FROM sales WHERE sku_id=? AND date>=date('now','-14 days')", (s["id"],)).fetchone()
    s["forecast_daily"] = round(r[0] or 0, 1)
conn_sales.close()

# 稀缺性：演示仅 8 个 SKU，自动把需求放大到 Σ需求上限 ≈ 1.1×总面位，
# 让"给谁面位、给多少、放哪个货架"成为真实权衡（接入全量 SKU 目录后移除）
TOTAL_SLOTS = sum(int(s["w"] / 0.4) * s["layer_count"] for s in plano["shelves"])
raw_caps = sum(max(4, int(-(-(s["forecast_daily"] or 0) // 8.0))) for s in skus)
scale = (1.1 * TOTAL_SLOTS / max(raw_caps, 1)) or 1
for s in skus:
    s["forecast_daily"] = round((s["forecast_daily"] or 0) * scale, 1)

result = solve_allocation(plano["shelves"], skus)
out = {
    "store_id": store["id"],
    "status": result["status"],
    "profit_before_idr": result["profit_before_idr"],
    "profit_after_idr": result["profit_after_idr"],
    "uplift": result["uplift"],
    "skus": [{"id": s["id"], "name": s["name"]} for s in skus],
    "alloc": result["alloc"],
}
slug = str(int(store["size_sqm"]))
path = Path(a.out_dir) / f"optimize-{slug}.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(f"optimize-{slug}.json: {out['status']} uplift {out['uplift']:+.1%} "
      f"({out['profit_before_idr']:,} -> {out['profit_after_idr']:,} IDR/天)")
