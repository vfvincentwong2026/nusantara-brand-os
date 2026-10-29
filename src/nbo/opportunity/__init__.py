"""加盟机会图层引擎：区域评分（人口 × 商圈 − 竞品）→ 机会分区 + 保护半径 + 品牌匹配建议。

为渠道地图"加盟机会"模式供数；评分规则透明可审计，当前为演示种子。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

OPPORTUNITY_DDL = """
CREATE TABLE IF NOT EXISTS opportunity_zone (
    id TEXT PRIMARY KEY, name TEXT, city TEXT, lat REAL, lon REAL,
    population_k REAL, mall_grade INTEGER, competitor_count INTEGER, source_type TEXT
);
CREATE TABLE IF NOT EXISTS franchise_store (
    id TEXT PRIMARY KEY, brand_id TEXT, name TEXT, lat REAL, lon REAL,
    protect_radius_m INTEGER, opened_at TEXT, source_type TEXT
);
"""

# 雅加达都会圈 10 个候选分区（演示坐标与人口口径）
ZONES = [
    dict(id="Z-01", name="Kelapa Gading", city="Jakarta Utara", lat=-6.1575, lon=106.9083, pop=420, mall=5, comp=14),
    dict(id="Z-02", name="PIK 2", city="Jakarta Utara", lat=-6.1080, lon=106.7350, pop=180, mall=4, comp=4),
    dict(id="Z-03", name="Bekasi Kota", city="Bekasi", lat=-6.2383, lon=106.9756, pop=610, mall=3, comp=18),
    dict(id="Z-04", name="Margonda", city="Depok", lat=-6.3910, lon=106.8220, pop=520, mall=3, comp=11),
    dict(id="Z-05", name="BSD Serpong", city="Tangerang Selatan", lat=-6.3050, lon=106.6820, pop=380, mall=5, comp=9),
    dict(id="Z-06", name="Bogor Yasmin", city="Bogor", lat=-6.5700, lon=106.8060, pop=290, mall=2, comp=6),
    dict(id="Z-07", name="Tebet", city="Jakarta Selatan", lat=-6.2290, lon=106.8610, pop=350, mall=3, comp=12),
    dict(id="Z-08", name="Mangga Dua", city="Jakarta Barat", lat=-6.1430, lon=106.8270, pop=310, mall=4, comp=15),
    dict(id="Z-09", name="Cibubur", city="Jakarta Timur", lat=-6.3700, lon=106.9530, pop=450, mall=2, comp=7),
    dict(id="Z-10", name="Karawaci", city="Tangerang", lat=-6.2280, lon=106.6170, pop=340, mall=4, comp=8),
]

# 已开业加盟店（保护半径演示；CS-D-001 案例店从 case_store 表并入）
FRANCHISE_STORES = [
    dict(id="FS-01", brand="BR-02", name="Mr. Ayam · Kelapa Gading", lat=-6.1600, lon=106.9050,
         radius=500, opened="2026-03"),
    dict(id="FS-02", brand="BR-03", name="Kopi Kilat · Tebet", lat=-6.2310, lon=106.8580,
         radius=500, opened="2026-06"),
    dict(id="FS-03", brand="BR-04", name="Boba Sultan · BSD", lat=-6.3030, lon=106.6850,
         radius=500, opened="2026-08"),
]


def migrate_opportunity(conn: sqlite3.Connection) -> None:
    conn.executescript(OPPORTUNITY_DDL)


def seed_opportunity(conn: sqlite3.Connection) -> None:
    migrate_opportunity(conn)
    for z in ZONES:
        conn.execute("INSERT OR REPLACE INTO opportunity_zone VALUES (?,?,?,?,?,?,?,?,?)",
                     (z["id"], z["name"], z["city"], z["lat"], z["lon"],
                      z["pop"], z["mall"], z["comp"], "演示"))
    for s in FRANCHISE_STORES:
        conn.execute("INSERT OR REPLACE INTO franchise_store VALUES (?,?,?,?,?,?,?,?)",
                     (s["id"], s["brand"], s["name"], s["lat"], s["lon"],
                      s["radius"], s["opened"], "演示"))


def _norm(v: float, lo: float, hi: float) -> float:
    return 0.5 if hi == lo else (v - lo) / (hi - lo)


def _suggest_brand(mall: int, pop: float, comp: int) -> str:
    """品牌匹配规则：商场级 → 茶饮/快闪；人口大区 → 零食集合；低竞品 → 单品/熟食；其余 → 咖啡。"""
    if mall >= 4:
        return "BR-04" if comp >= 8 else "BR-06"
    if pop >= 450:
        return "BR-01"
    if comp <= 6:
        return "BR-05"
    return "BR-03"


def build_opportunity(db_path: str | Path) -> dict:
    from nbo.case import migrate_case
    from nbo.franchise import migrate_franchise
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_case(conn)
        migrate_franchise(conn)
        migrate_opportunity(conn)
        zones = [dict(r) for r in conn.execute("SELECT * FROM opportunity_zone")]
        fstores = [dict(r) for r in conn.execute("SELECT * FROM franchise_store")]
        brands = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM franchise_brand")}
        case_store = dict(conn.execute("SELECT * FROM case_store LIMIT 1").fetchone() or {})
    finally:
        conn.close()
    if not zones:
        return {"demo": True, "error": "opportunity_zone 为空，请先 seed"}

    pops = [z["population_k"] for z in zones]
    comps = [z["competitor_count"] for z in zones]
    out_zones = []
    for z in zones:
        raw = (0.50 * _norm(z["population_k"], min(pops), max(pops))
               + 0.30 * (z["mall_grade"] - 1) / 4
               + 0.20 * (1 - _norm(z["competitor_count"], min(comps), max(comps))))
        score = round(30 + 70 * raw)  # 线性拉伸到 30–100 区间，避免小样本压缩
        grade = "S" if score >= 75 else "A" if score >= 60 else "B" if score >= 45 else "C"
        bid = _suggest_brand(z["mall_grade"], z["population_k"], z["competitor_count"])
        b = brands.get(bid, {})
        out_zones.append({**z, "score": score, "grade": grade,
                          "suggested_brand": {"id": bid, "name": b.get("name"), "format": b.get("format_id"),
                                              "fee_idr": b.get("fee_idr"), "invest_idr": b.get("invest_idr")}})
    out_zones.sort(key=lambda x: -x["score"])

    protections = [{"name": s["name"], "lat": s["lat"], "lon": s["lon"],
                    "radius_m": s["protect_radius_m"], "opened_at": s["opened_at"], "kind": "加盟店"}
                   for s in fstores]
    if case_store:
        protections.append({"name": case_store.get("name"), "lat": case_store.get("lat"),
                            "lon": case_store.get("lon"),
                            "radius_m": case_store.get("service_radius_m") or 500,
                            "opened_at": "样板店", "kind": "案例样板"})

    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "demo": True,
            "model": "机会分 = 人口 50% + 商圈等级 30% + 低竞品 20%（min-max 归一）",
            "zones": out_zones, "protection": protections,
            "kpi": {"s_grade": sum(1 for z in out_zones if z["grade"] == "S"),
                    "a_grade": sum(1 for z in out_zones if z["grade"] == "A"),
                    "protected": len(protections),
                    "avg_score": round(sum(z["score"] for z in out_zones) / len(out_zones))}}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
