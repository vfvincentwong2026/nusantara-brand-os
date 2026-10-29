"""空间优化器（MILP，OR-Tools CP-SAT）：把货架面位分配给 SKU，最大化预期毛利。

模型：
- 变量 facings[shelf][sku] ∈ ℤ⁺（该货架给该 SKU 的面位数）；y[sku] ∈ {0,1} 是否经营
- 约束：
  1) 货架容量：Σ_sku facings ≤ shelf_slots（面位宽 0.4m × 层数）
  2) 需求上限：Σ_shelf facings ≤ ceil(daily_demand / DAILY_SALES_PER_FACING)（不给卖不动的 SKU 面位）
  3) 经营门槛：facings[s][i] ≤ cap_s × y_i；Σ_s facings[s][i] ≥ MIN_FACINGS × y_i
- 目标：max Σ margin_i × heat_s × affinity(zone_s, cat_i) × facings[s][i]
  affinity：品类与区域匹配=1.0，跨区=0.6（实验值，回测校准）

输出：分配表 + 优化前后预期日毛利对比（naive = 货架均分给本区域品类 SKU）。
"""
from ortools.sat.python import cp_model

FACING_WIDTH_M = 0.4
DAILY_SALES_PER_FACING = 8.0   # 单个面位日销假设（v1 常数，校准后替换）
MIN_FACINGS = 4                # 经营一个 SKU 的最小总面位
CROSS_ZONE_PENALTY = 0.6

ZONE_OF_CATEGORY = {  # 零食演示：默认全落 food 区
    "零食": "food", "生鲜": "fresh", "服装": "apparel", "非食品": "non-food",
}


def _shelf_slots(shelf: dict) -> int:
    return max(1, int(shelf["w"] / FACING_WIDTH_M) * shelf["layer_count"])


def solve_allocation(shelves: list[dict], skus: list[dict]) -> dict:
    """skus: [{id, name, category, cost_idr, sell_price_idr, avg_daily, forecast_daily}]"""
    model = cp_model.CpModel()
    f = {}
    for si, s in enumerate(shelves):
        for sku in skus:
            f[si, sku["id"]] = model.NewIntVar(0, _shelf_slots(s), f"f_{si}_{sku['id']}")
    y = {sku["id"]: model.NewBoolVar(f"y_{sku['id']}") for sku in skus}

    for si, s in enumerate(shelves):
        model.Add(sum(f[si, sku["id"]] for sku in skus) <= _shelf_slots(s))
    for sku in skus:
        sid = sku["id"]
        demand = sku.get("forecast_daily") or sku.get("avg_daily") or 0
        cap = max(MIN_FACINGS, int(-(-demand // DAILY_SALES_PER_FACING)))  # ceil
        model.Add(sum(f[si, sid] for si in range(len(shelves))) <= cap)
        model.Add(sum(f[si, sid] for si in range(len(shelves))) >= MIN_FACINGS * y[sid])
        for si in range(len(shelves)):
            model.Add(f[si, sid] <= _shelf_slots(shelves[si]) * y[sid])

    def value(si, sku):
        s = shelves[si]
        margin = max(0, (sku.get("sell_price_idr") or 0) - (sku.get("cost_idr") or 0))
        affinity = 1.0 if ZONE_OF_CATEGORY.get(sku["category"], "food") == s["zone"] else CROSS_ZONE_PENALTY
        return int(margin * s["heat_value"] * affinity)

    model.Maximize(sum(value(si, sku) * f[si, sku["id"]]
                       for si in range(len(shelves)) for sku in skus))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20
    solver.parameters.num_search_workers = 1  # 固定单线程，保证多次求解结果可复现（去大屏/对比视图依赖确定性）
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "infeasible", "shelves": shelves, "skus": skus,
                "alloc": [], "profit_before": 0, "profit_after": 0}

    alloc = []
    for si, s in enumerate(shelves):
        row = {"shelf_id": s["id"], "zone": s["zone"], "heat_value": s["heat_value"], "slots": _shelf_slots(s)}
        entries = []
        for sku in skus:
            n = solver.Value(f[si, sku["id"]])
            if n > 0:
                entries.append({"sku_id": sku["id"], "facings": n,
                                "value": value(si, sku)})
        row["skus"] = sorted(entries, key=lambda e: -e["facings"])
        row["dominant_sku"] = row["skus"][0]["sku_id"] if row["skus"] else None
        alloc.append(row)

    profit_after = solver.ObjectiveValue() / 1.0
    profit_before = _naive_profit(shelves, skus)
    return {"status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "shelves": shelves, "skus": skus, "alloc": alloc,
            "profit_before_idr": round(profit_before),
            "profit_after_idr": round(profit_after),
            "uplift": round((profit_after - profit_before) / max(profit_before, 1), 4)}


def _naive_profit(shelves: list[dict], skus: list[dict]) -> float:
    """现状口径：货架面位均分给本区域匹配品类的 SKU，但受需求自然上限约束
    （卖不动就不补货——与 MILP 同一需求口径，否则对比失真）。"""
    remaining = {}
    for sku in skus:
        demand = sku.get("forecast_daily") or sku.get("avg_daily") or 0
        remaining[sku["id"]] = max(MIN_FACINGS, int(-(-demand // DAILY_SALES_PER_FACING)))
    total = 0.0
    for s in shelves:
        cands = [sku for sku in skus
                 if ZONE_OF_CATEGORY.get(sku["category"], "food") == s["zone"] and remaining[sku["id"]] > 0]
        if not cands:
            continue
        share = _shelf_slots(s) / len(cands)
        for sku in cands:
            sid = sku["id"]
            take = min(share, remaining[sid])
            remaining[sid] -= take
            margin = max(0, (sku.get("sell_price_idr") or 0) - (sku.get("cost_idr") or 0))
            total += margin * s["heat_value"] * take
    return total


def dominant_map(alloc: list[dict]) -> dict[str, str]:
    """shelf_id -> dominant sku_id（3D 着色用）。"""
    return {r["shelf_id"]: r["dominant_sku"] for r in alloc if r["dominant_sku"]}
