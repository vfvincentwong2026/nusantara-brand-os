import math

class ReplenishmentEngine:
    def __init__(self, service_level: float = 0.95):
        self.service_level = service_level
        self.z = 1.645  # 95% 服务水平

    def effective_lead_time(self, lt_mean: float, lt_std: float, island_region: str) -> float:
        k_map = {
            "java": 0.5,
            "sumatra": 1.0,
            "kalimantan": 1.0,
            "sulawesi": 1.5,
            "papua": 1.5,
        }
        k = k_map.get(island_region.lower(), 1.0)
        return lt_mean + k * lt_std

    def safety_stock(self, demand_std: float, lt_eff: float) -> float:
        return self.z * demand_std * math.sqrt(lt_eff)

    def reorder_point(self, avg_daily_demand: float, lt_eff: float, ss: float) -> float:
        return avg_daily_demand * lt_eff + ss

    def suggest(self, avg_daily_demand: float, demand_std: float, lt_mean: float, lt_std: float, island_region: str):
        lt_eff = self.effective_lead_time(lt_mean, lt_std, island_region)
        ss = self.safety_stock(demand_std, lt_eff)
        rop = self.reorder_point(avg_daily_demand, lt_eff, ss)
        return {"lt_eff": lt_eff, "safety_stock": ss, "reorder_point": rop}
