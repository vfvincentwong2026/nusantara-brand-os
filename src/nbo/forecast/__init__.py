class ForecastEngine:
    def __init__(self):
        self.ramadan_factor = 2.5  # 斋月需求倍数

    def forecast(self, historical_sales: list, horizon_days: int = 30, include_ramadan: bool = False):
        # 简化示例：用移动平均 + 斋月因子
        if not historical_sales:
            return [0] * horizon_days
        avg = sum(historical_sales) / len(historical_sales)
        forecast = [avg] * horizon_days
        if include_ramadan:
            forecast = [x * self.ramadan_factor for x in forecast]
        return forecast
