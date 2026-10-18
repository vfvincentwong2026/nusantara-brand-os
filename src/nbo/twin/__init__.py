"""数字孪生布局引擎：门店参数 -> planogram JSON（2D/3D 共享同一份数据源）。

口径（docs/store-scale-benchmarks.md）：
-  footprints 按面积反推矩形（长宽比 1.6:1），入口在长边中点
-  主通道宽度：500㎡=2.0m / 2,000㎡=3.0m / 5,000㎡=3.5m
-  货架层数：500=4-5 / 2,000=5-6 / 5,000=6-7（zone 内统一取档）
-  货架模块：宽 1.2m、深 0.6m，沿 zone 横向排成行，行间留主通道
-  热力值 heat_value：入口近=高、zone 基准加权（fresh>food>apparel>non-food）
"""
import json
import math
from pathlib import Path

SHELF_MODULE_W = 1.2
SHELF_DEPTH = 0.6
ASPECT = 1.6

ZONE_SPLIT = {  # 面积占比（无 fresh/apparel 时归一化到 food/non-food）
    "food": 0.45, "non-food": 0.30, "fresh": 0.15, "apparel": 0.10,
}
ZONE_BASE_HEAT = {"fresh": 0.90, "food": 0.80, "apparel": 0.65, "non-food": 0.50}
AISLE_BY_SCALE = [(500, 2.0), (2000, 3.0), (5000, 3.5)]
LAYERS_BY_SCALE = [(500, (4, 5)), (2000, (5, 6)), (5000, (6, 7))]


def _tier(size_sqm, table):
    for limit, v in sorted(table):
        if size_sqm <= limit:
            return v
    return table[-1][1]


def generate_layout(store: dict) -> dict:
    size = float(store["size_sqm"])
    w = round(math.sqrt(size * ASPECT), 2)
    h = round(size / w, 2)
    aisle = _tier(size, AISLE_BY_SCALE)
    layers_lo, layers_hi = _tier(size, LAYERS_BY_SCALE)

    # zone 横向切分（按面积占比，fresh/apparel 无占比时收缩）
    zones = {}
    split = {z: p for z, p in ZONE_SPLIT.items()
             if z in ("food", "non-food") or store.get("fresh_ratio", 0) > 0 and z == "fresh"
             or z == "apparel" and size >= 5000}
    total = sum(split.values())
    x = 0.0
    order = ["fresh", "food", "apparel", "non-food"]
    for z in order:
        if z not in split:
            continue
        zw = round(w * split[z] / total, 2)
        zones[z] = {"x": x, "w": zw}
        x += zw

    entrance = {"x": round(w / 2, 2), "y": 0.0, "side": "south"}

    shelves = []
    for z, zr in zones.items():
        layers = layers_hi if z in ("fresh", "food") else layers_lo
        # zone 内货架行：行间距 = 通道 + 双排货架深
        row_pitch = aisle + 2 * SHELF_DEPTH
        rows = max(1, int((h - aisle) // row_pitch))
        margin_y = (h - (rows * row_pitch - aisle)) / 2  # 垂直居中
        for r in range(rows):
            y = margin_y + aisle / 2 + SHELF_DEPTH / 2 + r * row_pitch
            # 每行沿 zone 宽排模块，两端留 0.4m 边距
            usable = zr["w"] - 0.8
            n = max(1, int(usable // SHELF_MODULE_W))
            x0 = zr["x"] + (zr["w"] - n * SHELF_MODULE_W) / 2
            for i in range(n):
                sx = x0 + i * SHELF_MODULE_W
                dist = math.hypot(sx + SHELF_MODULE_W / 2 - entrance["x"], y)
                heat = round(min(0.95, ZONE_BASE_HEAT[z] + 0.2 * (1 - dist / math.hypot(w, h))), 2)
                shelves.append({
                    "id": f"{z[:3].upper()}-R{r+1:02d}-S{i+1:02d}",
                    "zone": z, "x": round(sx, 2), "y": round(y, 2),
                    "w": SHELF_MODULE_W, "h": SHELF_DEPTH, "rotation": 0,
                    "layer_count": layers, "facing_width_m": 0.4,
                    "heat_value": heat,
                })

    return {
        "store_id": store["id"],
        "store_name": store["name"],
        "size_sqm": size,
        "footprint": {"w": w, "h": h},
        "entrance": entrance,
        "aisle_width_m": aisle,
        "zones": {z: {"x": r["x"], "w": r["w"]} for z, r in zones.items()},
        "shelves": shelves,
    }


def write_layout(out_path: str | Path, store: dict) -> dict:
    data = generate_layout(store)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
