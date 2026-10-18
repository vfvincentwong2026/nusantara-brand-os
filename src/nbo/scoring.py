"""WarungScout 7 维评分模型（融合自 warungscout/docs/SCORING_MODEL.md v1.0.0）。

权重：位置 25% / 活跃度 20% / 竞争 15% / 配合度 15% / 数字化 15% / 店主画像 5% / 区域 5%
分级：≥80 黄金 / ≥60 白银 / ≥40 潜力 / <40 普通

输入为原始信号 dict（Google Maps 数据 + 销售反馈），输出 7 维 0-100 + 加权总分 + 等级。
schema 对齐 WarungScout warungs 表 → 未来直接消费 WarungScout D1 导出。
"""
from typing import Any

WEIGHTS = {"location": 0.25, "activity": 0.20, "competition": 0.15, "cooperation": 0.15,
           "digital": 0.15, "owner": 0.05, "region": 0.05}

GRADE_LABEL = {"gold": "黄金", "silver": "白银", "potential": "潜力", "normal": "普通"}

CITY_TIER = {  # 区域潜力查表（SCORING_MODEL.md 维度7）
    "Jakarta": 10, "Surabaya": 8, "Medan": 8, "Bandung": 8,
    "Yogyakarta": 6, "Semarang": 6, "Makassar": 6,
}


def _location(s: dict) -> int:
    f = s.get("facilities", {})
    raw = (10 * f.get("schools", 0) + 10 * f.get("factories", 0) + 8 * f.get("offices", 0)
           + 5 * f.get("residences", 0) + 7 * f.get("transits", 0))
    return round(min(25, raw) / 25 * 100)


def _activity(s: dict) -> int:
    raw = 0
    rating, reviews = s.get("gm_rating", 0), s.get("gm_reviews", 0)
    if rating >= 4.0 and reviews >= 50:
        raw += 10
    elif rating >= 3.5 and reviews >= 20:
        raw += 5
    if s.get("wa_active"):
        raw += 10
    if s.get("participated_promo"):
        raw += 8
    if s.get("asked_new_product"):
        raw += 7
    return round(min(20, raw) / 20 * 100)


def _competition(s: dict) -> int:
    n = s.get("warung_competitors_500m", 0)
    table = 15 if n <= 2 else 12 if n <= 5 else 8 if n <= 10 else 5
    return round(table / 15 * 100)


def _cooperation(s: dict) -> int:
    if s.get("no_history", False):  # 新抓取 Warung 无历史 → 中性 50
        return 50
    score = 0
    rate = s.get("reply_rate", 0)
    if rate > 0.7:
        score += 40
    elif rate > 0.3:
        score += 20
    elif rate > 0:
        score += 5
    score += {"positive": 35, "neutral": 15, "negative": -25}.get(s.get("visit_feedback"), 0)
    if s.get("participated_promo"):
        score += 15
    if s.get("referral_given"):
        score += 10
    return max(0, min(100, score))


def _digital(s: dict) -> int:
    if s.get("no_history", False):
        return 50
    raw = 0
    if s.get("qris"):
        raw += 8
    raw += {"fast": 7, "day": 3}.get(s.get("wa_reply"), 0)
    raw += min(10, (5 if s.get("smartphone") else 0) + (3 if s.get("photos") else 0)
               + (2 if s.get("video") else 0))
    bonus = (5 if s.get("interested_inventory") else 0) + (5 if s.get("app_ordering") else 0)
    return min(100, round(min(20, raw) / 20 * 100) + bonus)


def _owner(s: dict) -> int:
    if s.get("no_history", False):
        return 50
    p = s.get("owner_profile", {})
    raw = ((3 if p.get("age_20_35") else 0) + (2 if p.get("expansion_plan") else 0)
           + (2 if p.get("main_income") else 0) + (2 if p.get("female") else 0)
           + (2 if p.get("high_school_plus") else 0) + (2 if p.get("local") else 0))
    return round(min(10, raw) / 10 * 100)


def _region(city: str | None) -> int:
    return CITY_TIER.get(city or "", 4) * 10


def score_warung(signals: dict) -> dict[str, Any]:
    dims = {"location": _location(signals), "activity": _activity(signals),
            "competition": _competition(signals), "cooperation": _cooperation(signals),
            "digital": _digital(signals), "owner": _owner(signals),
            "region": _region(signals.get("city"))}
    final = round(sum(dims[k] * w for k, w in WEIGHTS.items()))
    grade = "gold" if final >= 80 else "silver" if final >= 60 else "potential" if final >= 40 else "normal"
    return {"final_score": final, "grade": grade, "grade_label": GRADE_LABEL[grade], "dims": dims}
