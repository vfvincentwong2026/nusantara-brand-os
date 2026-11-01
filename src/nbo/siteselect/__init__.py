"""智能选址：候选点位评估 + POI 图层 + 人流热力（雅加达/万隆演示区）。

专业选址逻辑：人流 × 消费人群匹配 × 租金压力 × 竞品密度 → 综合选址分；
每个候选点给出覆盖范围（步行圈内社区/学校/商城/办公数量与人口）。
数据源：演示种子（字段对齐真实 POI 库 / 人流数据源，可无缝切换）。
"""
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

WIB = timezone(timedelta(hours=7))

DDL = """
CREATE TABLE IF NOT EXISTS site_candidate (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  area TEXT NOT NULL,
  city TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  site_type TEXT NOT NULL,           -- 社区口 / 学校旁 / 商场食阁 / 办公区 / 交通枢纽 / 夜市
  foot_traffic INTEGER, crowd_fit INTEGER, rent_pressure INTEGER, competition INTEGER,
  catch_pop_wan REAL, catch_communities INTEGER, catch_schools INTEGER,
  catch_malls INTEGER, catch_offices INTEGER, catch_radius_m INTEGER,
  recommended_model TEXT, reason TEXT,
  source_type TEXT DEFAULT 'demo_seed'
);
"""

# 雅加达核心区坐标基准：-6.2, 106.8
CANDIDATES = [
    dict(id="ST-01", name="Bintaro 九号社区口", area="Bintaro", city="南唐格朗", lat=-6.2665, lon=106.7180,
         site_type="社区口", foot_traffic=78, crowd_fit=86, rent_pressure=42, competition=35,
         catch_pop_wan=6.8, catch_communities=14, catch_schools=6, catch_malls=2, catch_offices=5, catch_radius_m=800,
         recommended_model="56㎡ 社区集装箱店 / 推车组合",
         reason="中高收入社区密集、学校 6 所保底午晚双峰；竞品密度低，社区口锚点稀缺——社区零售标准打法的首选点。"),
    dict(id="ST-02", name="UI 大学 Depok 校门带", area="Depok", city="德波", lat=-6.3649, lon=106.8219,
         site_type="学校旁", foot_traffic=88, crowd_fit=82, rent_pressure=30, competition=48,
         catch_pop_wan=9.2, catch_communities=9, catch_schools=11, catch_malls=1, catch_offices=2, catch_radius_m=600,
         recommended_model="推车 / 15㎡ 档口",
         reason="3 万学生高频价格敏感客群，传播属性极强（开学季刷屏体质）；租金极低，适合推车+档口轻模型跑量。"),
    dict(id="ST-03", name="Grand Indonesia 食阁层", area="Sudirman", city="雅加达", lat=-6.1952, lon=106.8207,
         site_type="商场食阁", foot_traffic=95, crowd_fit=74, rent_pressure=88, competition=72,
         catch_pop_wan=4.5, catch_communities=4, catch_schools=1, catch_malls=4, catch_offices=38, catch_radius_m=1000,
         recommended_model="品牌旗舰体验点",
         reason="全雅加达人流天花板、办公客群 38 栋；但租金与竞品双高压——只适合已验证品牌做形象与单测，不适合首店。"),
    dict(id="ST-04", name="SCBD 办公区街角", area="SCBD", city="雅加达", lat=-6.2255, lon=106.8086,
         site_type="办公区", foot_traffic=82, crowd_fit=80, rent_pressure=78, competition=55,
         catch_pop_wan=3.1, catch_communities=2, catch_schools=0, catch_malls=3, catch_offices=52, catch_radius_m=700,
         recommended_model="咖啡/轻食档口",
         reason="52 栋办公楼早高峰刚需，外卖半径 1km 内单量全城 top；租金高但客单价可撑——咖啡档口坪效模型最佳试验场。"),
    dict(id="ST-05", name="MRT Blok M 枢纽口", area="Blok M", city="雅加达", lat=-6.2447, lon=106.7977,
         site_type="交通枢纽", foot_traffic=90, crowd_fit=77, rent_pressure=60, competition=58,
         catch_pop_wan=7.4, catch_communities=10, catch_schools=4, catch_malls=5, catch_offices=12, catch_radius_m=900,
         recommended_model="30㎡ 快取店",
         reason="轨道枢纽+夜市商圈双人流叠加，通勤与夜间双峰；快取店型转化枢纽流量，夜间外摆接夜市客流。"),
    dict(id="ST-06", name="BSD 塞尔蓬新社区轴", area="BSD", city="唐格朗", lat=-6.2980, lon=106.6844,
         site_type="社区口", foot_traffic=66, crowd_fit=83, rent_pressure=38, competition=28,
         catch_pop_wan=8.9, catch_communities=17, catch_schools=8, catch_malls=3, catch_offices=9, catch_radius_m=1000,
         recommended_model="56㎡ 社区集装箱店",
         reason="新城社区 17 个且每年新增，年轻家庭客群与竞品低密度并存——'先占社区口'战略价值最高的成长型点位。"),
    dict(id="ST-07", name="ITC Kuningan 批发商圈", area="Kuningan", city="雅加达", lat=-6.2333, lon=106.8245,
         site_type="办公区", foot_traffic=71, crowd_fit=64, rent_pressure=45, competition=41,
         catch_pop_wan=4.2, catch_communities=5, catch_schools=2, catch_malls=2, catch_offices=22, catch_radius_m=800,
         recommended_model="推车 + 外带窗口",
         reason="批发商圈人流杂但单价低，适合极致性价比模型（Es Teh 路径）；办公+批发混合客群，下午茶场景空白。"),
    dict(id="ST-08", name="Summarecon Bekasi 社区轴", area="Bekasi", city="勿加泗", lat=-6.2479, lon=106.9916,
         site_type="社区口", foot_traffic=62, crowd_fit=79, rent_pressure=33, competition=22,
         catch_pop_wan=10.6, catch_communities=21, catch_schools=9, catch_malls=4, catch_offices=6, catch_radius_m=1000,
         recommended_model="56㎡ 社区集装箱店",
         reason="卫星城最大社区群、覆盖人口 10.6 万全榜第一，竞品密度全榜最低——'人口密度换增长'的长期价值点位。"),
]

# POI 图层（演示种子坐标，围绕雅加达核心）
POIS = {
    "malls": [
        {"name": "Grand Indonesia", "lat": -6.1952, "lon": 106.8207},
        {"name": "Plaza Indonesia", "lat": -6.1925, "lon": 106.8230},
        {"name": "Pacific Place", "lat": -6.2244, "lon": 106.8089},
        {"name": "Senayan City", "lat": -6.2278, "lon": 106.7975},
        {"name": "Gandaria City", "lat": -6.2440, "lon": 106.7837},
        {"name": "Blok M Square", "lat": -6.2445, "lon": 106.7980},
        {"name": "Summarecon Mall Serpong", "lat": -6.3000, "lon": 106.6830},
        {"name": "Summarecon Mall Bekasi", "lat": -6.2485, "lon": 106.9925},
        {"name": "Bintaro Jaya Xchange", "lat": -6.2650, "lon": 106.7190},
        {"name": "Mall Kelapa Gading", "lat": -6.1572, "lon": 106.9080},
    ],
    "schools": [
        {"name": "UI Depok", "lat": -6.3649, "lon": 106.8219},
        {"name": "UNJ Rawamangun", "lat": -6.1920, "lon": 106.8790},
        {"name": "Atma Jaya Semanggi", "lat": -6.2150, "lon": 106.8110},
        {"name": "Bina Nusantara Kemanggisan", "lat": -6.2015, "lon": 106.7805},
        {"name": "SMAN 8 Jakarta", "lat": -6.2340, "lon": 106.7990},
        {"name": "Santa Ursula", "lat": -6.1680, "lon": 106.8340},
        {"name": "UPH BSD", "lat": -6.3030, "lon": 106.6790},
        {"name": "SMAN 1 Bekasi", "lat": -6.2455, "lon": 106.9900},
    ],
    "communities": [
        {"name": "Bintaro Sektor 9", "lat": -6.2665, "lon": 106.7180},
        {"name": "BSD Nusa Loka", "lat": -6.2980, "lon": 106.6844},
        {"name": "Kelapa Gading", "lat": -6.1572, "lon": 106.9080},
        {"name": "Tebet Barat", "lat": -6.2290, "lon": 106.8500},
        {"name": "Cibubur Country", "lat": -6.3500, "lon": 106.8850},
        {"name": "Serpong Garden", "lat": -6.2950, "lon": 106.6900},
        {"name": "Bekasi Summarecon", "lat": -6.2479, "lon": 106.9916},
        {"name": "Tanjung Duren", "lat": -6.1680, "lon": 106.7870},
    ],
    "offices": [
        {"name": "SCBD District", "lat": -6.2255, "lon": 106.8086},
        {"name": "Sudirman CBD", "lat": -6.2100, "lon": 106.8200},
        {"name": "Kuningan Corridor", "lat": -6.2333, "lon": 106.8245},
        {"name": "TB Simatupang", "lat": -6.2930, "lon": 106.7970},
        {"name": "Gatot Subroto", "lat": -6.2370, "lon": 106.8010},
        {"name": "BSD Office Park", "lat": -6.3010, "lon": 106.6810},
        {"name": "Bekasi Cyber Park", "lat": -6.2490, "lon": 106.9880},
    ],
}

# 人流热力演示点（商圈/枢纽权重高）
HEAT = [
    [-6.1952, 106.8207, 0.95], [-6.2244, 106.8089, 0.8], [-6.2447, 106.7977, 0.9],
    [-6.2255, 106.8086, 0.85], [-6.1925, 106.8230, 0.88], [-6.2278, 106.7975, 0.75],
    [-6.2440, 106.7837, 0.7], [-6.2333, 106.8245, 0.72], [-6.2370, 106.8010, 0.68],
    [-6.3649, 106.8219, 0.82], [-6.2665, 106.7180, 0.62], [-6.2980, 106.6844, 0.6],
    [-6.3000, 106.6830, 0.66], [-6.1572, 106.9080, 0.7], [-6.2479, 106.9916, 0.58],
    [-6.2485, 106.9925, 0.64], [-6.2015, 106.7805, 0.55], [-6.2150, 106.8110, 0.6],
    [-6.2290, 106.8500, 0.5], [-6.1680, 106.8340, 0.52], [-6.2340, 106.7990, 0.48],
    [-6.3500, 106.8850, 0.42], [-6.1680, 106.7870, 0.5], [-6.2930, 106.7970, 0.56],
    [-6.3030, 106.6790, 0.44], [-6.2950, 106.6900, 0.46], [-6.2490, 106.9880, 0.4],
    [-6.3010, 106.6810, 0.42], [-6.2455, 106.9900, 0.38], [-6.1920, 106.8790, 0.5],
]

SITE_TYPE_LABEL = {"社区口": "COMMUNITY", "学校旁": "CAMPUS", "商场食阁": "MALL F&B",
                   "办公区": "OFFICE", "交通枢纽": "TRANSIT", "夜市": "NIGHT MARKET"}


def migrate_siteselect(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)


def seed_siteselect(conn: sqlite3.Connection) -> None:
    migrate_siteselect(conn)
    for c in CANDIDATES:
        conn.execute(
            "INSERT OR REPLACE INTO site_candidate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["id"], c["name"], c["area"], c["city"], c["lat"], c["lon"], c["site_type"],
             c["foot_traffic"], c["crowd_fit"], c["rent_pressure"], c["competition"],
             c["catch_pop_wan"], c["catch_communities"], c["catch_schools"],
             c["catch_malls"], c["catch_offices"], c["catch_radius_m"],
             c["recommended_model"], c["reason"], "demo_seed"))


def site_score(c: dict) -> float:
    """综合选址分 = 人流×0.30 + 客群×0.25 + (100-租金压力)×0.20 + (100-竞品密度)×0.25"""
    return round(c["foot_traffic"] * 0.30 + c["crowd_fit"] * 0.25
                 + (100 - c["rent_pressure"]) * 0.20 + (100 - c["competition"]) * 0.25, 1)


def build_siteselect(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_siteselect(conn)
        rows = [dict(r) for r in conn.execute("SELECT * FROM site_candidate")]
    finally:
        conn.close()
    if not rows:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            seed_siteselect(conn)
            conn.commit()
            rows = [dict(r) for r in conn.execute("SELECT * FROM site_candidate")]
        finally:
            conn.close()
    cands = []
    for r in rows:
        c = dict(r)
        c["score"] = site_score(c)
        c["catchment"] = {"pop_wan": c.pop("catch_pop_wan"), "communities": c.pop("catch_communities"),
                          "schools": c.pop("catch_schools"), "malls": c.pop("catch_malls"),
                          "offices": c.pop("catch_offices"), "radius_m": c.pop("catch_radius_m")}
        c["type_en"] = SITE_TYPE_LABEL.get(c["site_type"], c["site_type"])
        cands.append(c)
    cands.sort(key=lambda c: c["score"], reverse=True)
    return {
        "generated_at": datetime.now(WIB).strftime("%Y-%m-%d %H:%M"),
        "demo": True,
        "source_note": "演示种子数据 · 字段对齐真实 POI 库（OSM/自采）与人流数据源",
        "candidates": cands,
        "pois": POIS,
        "heat": HEAT,
    }


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
