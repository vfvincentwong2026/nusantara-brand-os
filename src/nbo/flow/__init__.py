"""客流动线引擎：入口 -> 通道waypoint 随机游逛 -> 出口，输出米级热力网格。

- 通道 waypoint：每条货架行间隙的主通道中线（含前后边距通道），x 向每 4m 一点
- 游逛路径：L 型走法（先沿 y 到目标通道，再沿 x 平移），不穿货架
- 区域吸引权重 = zone 基准热力（fresh>food>apparel>non-food）
- 输出 grid 供 3D 地面热力叠加；前端用同一份 waypoint 做动画寻路（演示点从入口持续生成）
"""
import json
import random
from pathlib import Path

WAYPOINT_STEP_X = 4.0


def build_waypoints(plano: dict) -> list[dict]:
    """通道中线 waypoints：y = 各通道中心，x = zone 内按 4m 步进的点。"""
    H = plano["footprint"]["h"]
    aisle = plano["aisle_width_m"]
    # 通道中心 y 列表（与 twin 布局的行距几何一致：行距 = aisle + 2×0.6）
    row_pitch = aisle + 1.2
    rows = max(1, int((H - aisle) // row_pitch))
    margin = (H - (rows * row_pitch - aisle)) / 2
    aisle_ys = []
    y = margin + aisle / 2
    while y < H:
        aisle_ys.append(round(y, 2))
        y += row_pitch
    wps = []
    for z, zr in plano["zones"].items():
        for y in aisle_ys:
            x = zr["x"] + WAYPOINT_STEP_X / 2
            while x < zr["x"] + zr["w"] - 0.5:
                wps.append({"x": round(x, 2), "y": y, "zone": z})
                x += WAYPOINT_STEP_X
    return wps


def zone_weights(plano: dict) -> dict[str, float]:
    base = {"fresh": 0.30, "food": 0.35, "apparel": 0.15, "non-food": 0.20}
    zones = [z for z in base if z in plano["zones"]]
    total = sum(base[z] for z in zones)
    return {z: round(base[z] / total, 3) for z in zones}


def simulate(plano: dict, n_customers: int = 400, seed: int = 42) -> dict:
    """返回 {waypoints, zone_weights, grid}；grid 为米级计数（扁平数组，行优先）。"""
    rng = random.Random(seed)
    W, H = plano["footprint"]["w"], plano["footprint"]["h"]
    ex, ey = plano["entrance"]["x"], H - 0.01
    wps = build_waypoints(plano)
    zw = zone_weights(plano)
    by_zone: dict[str, list] = {}
    for w in wps:
        by_zone.setdefault(w["zone"], []).append(w)

    cols, rows = int(W) + 1, int(H) + 1
    grid = [0] * (cols * rows)

    def visit(x, y):
        cx, cy = int(x), int(y)
        if 0 <= cx < cols and 0 <= cy < rows:
            grid[cy * cols + cx] += 1

    def walk(x0, y0, x1, y1):
        """L 型路径：先竖后横，逐米打点。"""
        steps = int(max(abs(y1 - y0), abs(x1 - x0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            y = y0 + (y1 - y0) * t
            x = x0 if t <= 0.5 else x0 + (x1 - x0) * (t - 0.5) * 2
            visit(x, y)

    for _ in range(n_customers):
        zones = list(by_zone)
        k = rng.randint(3, 7)
        picks = rng.choices(zones, weights=[zw[z] for z in zones], k=k)
        cur = {"x": ex, "y": ey}
        for z in picks:
            tgt = rng.choice(by_zone[z])
            walk(cur["x"], cur["y"], tgt["x"], tgt["y"])
            cur = tgt
        walk(cur["x"], cur["y"], ex, ey)

    return {
        "entrance": {"x": ex, "y": round(H - 0.01, 2)},
        "waypoints": wps,
        "zone_weights": zw,
        "grid": {"cols": cols, "rows": rows, "cell_m": 1, "counts": grid},
    }


def write_flow(out_path: str | Path, plano: dict, **kw) -> dict:
    data = simulate(plano, **kw)
    data["store_id"] = plano["store_id"]
    data["size_sqm"] = plano["size_sqm"]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
