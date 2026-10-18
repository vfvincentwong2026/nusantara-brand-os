"""渠道地图引擎 v1：渠道点位 + 竞品密度 + 覆盖缺口。

点位数据模型对齐 WarungScout warungs 表（warungscout/docs/DATABASE_SCHEMA.md）；
Brand OS 不另建 Warung 库——未来直接消费 WarungScout D1 导出。

口径：
- 竞品密度 = 某 Warung 半径(默认 500m)内 alfamart/indomaret 数量
- 覆盖缺口 = 高评分 Warung（gold/silver）周边竞品密度为 0 的区域 → 铺货优先级最高
"""
import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path

COMPETITOR_TYPES = ("alfamart", "indomaret")
GRADE_LABEL = {"gold": "黄金", "silver": "白银", "potential": "潜力", "normal": "普通"}


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def competitor_density(points: list[dict], radius_m: float = 500) -> dict[str, int]:
    """每个 warung 半径内的现代渠道竞品数；返回 {warung_id: count}。"""
    warungs = [p for p in points if p["type"] == "warung"]
    comps = [p for p in points if p["type"] in COMPETITOR_TYPES]
    out = {}
    for w in warungs:
        out[w["id"]] = sum(1 for c in comps
                           if haversine_m(w["lat"], w["lon"], c["lat"], c["lon"]) <= radius_m)
    return out


def coverage_gaps(points: list[dict], density: dict[str, int], min_grade: str = "silver") -> list[dict]:
    """gold/silver Warung 且周边 0 竞品 → 缺口机会，按评分降序。"""
    rank = {"gold": 0, "silver": 1}
    if min_grade == "gold":
        keep = {"gold"}
    else:
        keep = {"gold", "silver"}
    gaps = [{"id": p["id"], "name": p["name"], "grade": p["grade"],
             "final_score": p["final_score"], "sales_step": p["sales_step"],
             "lat": p["lat"], "lon": p["lon"], "city": p["city"]}
            for p in points
            if p["type"] == "warung" and p["grade"] in keep and density.get(p["id"], 0) == 0]
    return sorted(gaps, key=lambda g: (rank.get(g["grade"], 9), -g["final_score"]))


def build_map(db_path: str | Path, radius_m: float = 500) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        points = [dict(r) for r in conn.execute("SELECT * FROM channel_points")]
    finally:
        conn.close()
    density = competitor_density(points, radius_m)
    for p in points:
        if p["type"] == "warung":
            p["competitors_within"] = density.get(p["id"], 0)
            p["grade_label"] = GRADE_LABEL.get(p["grade"], p["grade"])
    warungs = [p for p in points if p["type"] == "warung"]
    gaps = coverage_gaps(points, density)
    by_city = {}
    for p in points:
        c = p.get("city") or "未知"
        s = by_city.setdefault(c, {"warung": 0, "competitor": 0, "gold": 0, "silver": 0,
                                   "avg_score": 0.0, "score_n": 0})
        if p["type"] == "warung":
            s["warung"] += 1
            s["avg_score"] += p["final_score"]
            s["score_n"] += 1
            if p["grade"] in ("gold", "silver"):
                s[p["grade"]] += 1
        else:
            s["competitor"] += 1
    for s in by_city.values():
        s["avg_score"] = round(s["avg_score"] / s["score_n"], 1) if s["score_n"] else 0
        del s["score_n"]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "params": {"radius_m": radius_m},
        "kpis": {
            "warung_count": len(warungs),
            "competitor_count": len(points) - len(warungs),
            "gold_silver": sum(1 for w in warungs if w["grade"] in ("gold", "silver")),
            "avg_score": round(sum(w["final_score"] for w in warungs) / len(warungs), 1) if warungs else 0,
            "gap_count": len(gaps),
        },
        "by_city": by_city,
        "gaps": gaps,
        "points": points,
    }


def write_map(out_path: str | Path, **kwargs) -> dict:
    data = build_map(**kwargs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
