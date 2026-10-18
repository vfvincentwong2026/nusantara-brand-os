"""需求预测引擎 v1：周几基线 × 节庆因子（品类×节庆分层因子的第一步）。

口径：
- 基线 = 近 28 天内同一星期几的均值；不足 3 个样本退化为全期均值；无数据为 0
- 节庆因子 = 事件基础因子 × 品类系数（v1 均给 1.0 默认值，结构已分层，后续用回测校准填实数）
- Mudik 效应：开斋节前 7 天城市店上冲、开斋节当周回落（mudik_offset 可正可负）
- backtest 输出 MAPE，作为因子校准的闭环指标
"""
from datetime import date, timedelta

from nbo.calendar import IndonesiaCalendar

# 事件基础因子：ramadan 按周爬坡（4 周），eid 前 7 天冲刺、eid 周回落
RAMADAN_WEEKLY = [1.10, 1.20, 1.35, 1.50]
PRE_EID_DAILY = [1.10, 1.15, 1.20, 1.30, 1.45, 1.60, 1.90]  # eid 前第 7..1 天
EVENT_FACTORS = {
    "eid_week": 0.60,        # 开斋节当周（城市店返乡回落）
    "harbolnas": 1.50,
    "independence_day": 1.20,
}
CATEGORY_FACTOR = {"default": 1.0}  # 品类系数占位：回测校准后填实（如 零食.ramadan=1.2）


def _d(s) -> date:
    return date.fromisoformat(s) if isinstance(s, str) else s


class ForecastEngine:
    def __init__(self, calendar: IndonesiaCalendar | None = None,
                 category: str | None = None, mudik_offset: float = 0.0):
        self.cal = calendar or IndonesiaCalendar()
        self.cat_factor = CATEGORY_FACTOR.get(category, CATEGORY_FACTOR["default"])
        self.mudik_offset = mudik_offset  # 负值=城市店返乡净流出，正值=目的地店流入

    def _event_factor(self, d: date) -> float:
        ev = self.cal.events
        ram_start, ram_end = _d(ev["ramadan"]["start"]), _d(ev["ramadan"]["end"])
        eid_start = _d(ev["eid"]["start"])
        # 优先级：开斋前冲刺 > 斋月爬坡（斋月末尾与冲刺期重叠，冲刺因子更接近真实峰值）
        if eid_start - timedelta(days=7) <= d < eid_start:
            i = 7 - (eid_start - d).days  # EID-7 -> 0 (1.10) ... EID-1 -> 6 (1.90)
            return PRE_EID_DAILY[i] * self.cat_factor
        if ram_start <= d <= ram_end:
            week = min((d - ram_start).days // 7, 3)
            return RAMADAN_WEEKLY[week] * self.cat_factor
        if eid_start <= d <= eid_start + timedelta(days=6):
            return EVENT_FACTORS["eid_week"] + self.mudik_offset
        for name, key in (("harbolnas", "harbolnas"), ("independence_day", "independence_day")):
            s, e = _d(ev[key]["start"]), _d(ev[key]["end"])
            if s <= d <= e:
                return EVENT_FACTORS[name] * self.cat_factor
        return 1.0

    def baseline(self, daily: dict[date, int], d: date) -> float:
        """近 28 天同星期几均值；样本不足退化为全期均值。"""
        window = [q for day, q in daily.items() if timedelta(days=28) >= d - day > timedelta(0)]
        dow = [q for day, q in daily.items() if day.isoweekday() == d.isoweekday()
               and timedelta(days=28) >= d - day > timedelta(0)]
        if len(dow) >= 3:
            return sum(dow) / len(dow)
        if window:
            return sum(window) / len(window)
        return 0.0

    def forecast(self, daily: dict, horizon_days: int, start: date | None = None) -> list[dict]:
        """daily: {date: qty}；返回 [{date, baseline, factor, predicted}]。"""
        daily = {_d(k): v for k, v in daily.items()}
        start = start or date.today()
        out = []
        for i in range(horizon_days):
            d = start + timedelta(days=i)
            b = self.baseline(daily, d)
            f = self._event_factor(d)
            out.append({"date": d.isoformat(), "baseline": round(b, 2),
                        "factor": round(f, 3), "predicted": round(b * f, 1)})
        return out

    def backtest(self, daily: dict, horizon_days: int = 7,
                 asof: date | None = None) -> dict:
        """用 asof 之前的数据预测 asof 之后 horizon 天，与实际比算 MAPE。"""
        daily = {_d(k): v for k, v in daily.items()}
        asof = asof or date.today()
        train = {d: q for d, q in daily.items() if d < asof}
        actual = {d: q for d, q in daily.items() if asof <= d < asof + timedelta(days=horizon_days)}
        if not actual:
            return {"mape": None, "n": 0}
        preds = self.forecast(train, horizon_days, start=asof)
        errors = [abs(p["predicted"] - actual.get(date.fromisoformat(p["date"]), 0))
                  / max(actual.get(date.fromisoformat(p["date"]), 1), 1)
                  for p in preds if date.fromisoformat(p["date"]) in actual]
        return {"mape": round(sum(errors) / len(errors), 3) if errors else None, "n": len(errors)}
