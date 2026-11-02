"""智能选址：候选点位评估 + POI 图层 + 人流热力（雅加达/万隆演示区）。

专业选址逻辑（借鉴连锁巨头方法论，按业态分模型）：
- 体验店（星巴克逻辑）：第三空间锚定高质人流，可见性与展示面是硬门槛，租金承受力强
- 快取外卖店（瑞幸逻辑）：外卖半径单量 + 办公密度 + 低租金小面积，数据驱动
- 车餐家庭店（麦当劳逻辑）：车流 + 学校社区家庭客群 + 全时段流量
- 性价比街铺（蜜雪逻辑）：人流绝对量 + 学校 + 极致低租金
- 推车档口（轻资产逻辑）：潮汐人流 + 接近零固定成本
每个候选点按各模型加权评分 + 硬条件否决 → 推荐匹配模型。
数据源：演示种子（字段对齐真实 POI 库 / 人流数据源，可无缝切换）。
"""
import json
import hashlib
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
  visibility INTEGER, car_traffic INTEGER, delivery_fit INTEGER,
  catch_pop_wan REAL, catch_communities INTEGER, catch_schools INTEGER,
  catch_malls INTEGER, catch_offices INTEGER, catch_radius_m INTEGER,
  recommended_model TEXT, reason TEXT,
  source_type TEXT DEFAULT 'demo_seed'
);
"""

# ---------- 选址模型库（借鉴星巴克/瑞幸/麦当劳/蜜雪方法论） ----------
# 因子键：ft=人流 cf=客群匹配 rp=租金压力(逆向) cp=竞品密度(逆向) vs=可见性 ct=车流 df=外卖适配
MODELS = {
    "experience": {
        "name": "体验店", "en": "EXPERIENCE", "icon": "☕",
        "borrow": "星巴克逻辑：第三空间锚定高质人流，可见性/展示面是硬门槛，租金承受力强（80-150㎡）",
        "weights": {"ft": 0.25, "cf": 0.20, "rp": 0.15, "cp": 0.15, "vs": 0.25},
        "hard": {"ft": 80, "vs": 70},          # 硬条件：低于即否决
        "hard_label": {"ft": "人流 ≥80", "vs": "可见性 ≥70"},
    },
    "pickup": {
        "name": "快取外卖店", "en": "PICKUP", "icon": "⚡",
        "borrow": "瑞幸逻辑：外卖半径单量 + 办公密度 + 低租金小面积，数据驱动加密（15-40㎡）",
        "weights": {"ft": 0.10, "cf": 0.10, "rp": 0.25, "cp": 0.10, "vs": 0.10, "df": 0.35},
        "hard": {"df": 55},
        "hard_label": {"df": "外卖适配 ≥55"},
    },
    "drive": {
        "name": "车餐家庭店", "en": "DRIVE-THRU", "icon": "🚗",
        "borrow": "麦当劳逻辑：车流 + 学校/社区家庭客群 + 早午晚夜宵全时段流量，车道与路口可见性（120㎡+）",
        "weights": {"ft": 0.15, "cf": 0.20, "rp": 0.10, "cp": 0.10, "vs": 0.10, "ct": 0.35},
        "hard": {"ct": 60},
        "hard_label": {"ct": "车流 ≥60"},
    },
    "value": {
        "name": "性价比街铺", "en": "VALUE", "icon": "🏪",
        "borrow": "蜜雪逻辑：人流绝对量 + 学校密度 + 极致低租金，单品打天下（20-50㎡）",
        "weights": {"ft": 0.35, "cf": 0.20, "rp": 0.25, "cp": 0.10, "vs": 0.10},
        "hard": {"rp_max": 60},
        "hard_label": {"rp_max": "租金压力 ≤60"},
    },
    "cart": {
        "name": "推车档口", "en": "CART", "icon": "🛒",
        "borrow": "轻资产逻辑：潮汐人流（校门口/通勤口/夜市）+ 接近零固定成本，验证后再固化为店",
        "weights": {"ft": 0.40, "cf": 0.20, "rp": 0.30, "cp": 0.10},
        "hard": {"ft": 65},
        "hard_label": {"ft": "人流 ≥65"},
    },
}

# 雅加达核心区坐标基准：-6.2, 106.8
CANDIDATES = [
    dict(id="ST-01", name="Bintaro 九号社区口", area="Bintaro", city="南唐格朗", lat=-6.2665, lon=106.7180,
         site_type="社区口", foot_traffic=78, crowd_fit=86, rent_pressure=42, competition=35, visibility=75, car_traffic=68, delivery_fit=58,
         catch_pop_wan=6.8, catch_communities=14, catch_schools=6, catch_malls=2, catch_offices=5, catch_radius_m=800,
         recommended_model="56㎡ 社区集装箱店 / 推车组合",
         reason="中高收入社区密集、学校 6 所保底午晚双峰；竞品密度低，社区口锚点稀缺——社区零售标准打法的首选点。"),
    dict(id="ST-02", name="UI 大学 Depok 校门带", area="Depok", city="德波", lat=-6.3649, lon=106.8219,
         site_type="学校旁", foot_traffic=88, crowd_fit=82, rent_pressure=30, competition=48, visibility=82, car_traffic=30, delivery_fit=72,
         catch_pop_wan=9.2, catch_communities=9, catch_schools=11, catch_malls=1, catch_offices=2, catch_radius_m=600,
         recommended_model="推车 / 15㎡ 档口",
         reason="3 万学生高频价格敏感客群，传播属性极强（开学季刷屏体质）；租金极低，适合推车+档口轻模型跑量。"),
    dict(id="ST-03", name="Grand Indonesia 食阁层", area="Sudirman", city="雅加达", lat=-6.1952, lon=106.8207,
         site_type="商场食阁", foot_traffic=95, crowd_fit=74, rent_pressure=88, competition=72, visibility=95, car_traffic=40, delivery_fit=78,
         catch_pop_wan=4.5, catch_communities=4, catch_schools=1, catch_malls=4, catch_offices=38, catch_radius_m=1000,
         recommended_model="品牌旗舰体验点",
         reason="全雅加达人流天花板、办公客群 38 栋；但租金与竞品双高压——只适合已验证品牌做形象与单测，不适合首店。"),
    dict(id="ST-04", name="SCBD 办公区街角", area="SCBD", city="雅加达", lat=-6.2255, lon=106.8086,
         site_type="办公区", foot_traffic=82, crowd_fit=80, rent_pressure=78, competition=55, visibility=85, car_traffic=55, delivery_fit=95,
         catch_pop_wan=3.1, catch_communities=2, catch_schools=0, catch_malls=3, catch_offices=52, catch_radius_m=700,
         recommended_model="咖啡/轻食档口",
         reason="52 栋办公楼早高峰刚需，外卖半径 1km 内单量全城 top；租金高但客单价可撑——咖啡档口坪效模型最佳试验场。"),
    dict(id="ST-05", name="MRT Blok M 枢纽口", area="Blok M", city="雅加达", lat=-6.2447, lon=106.7977,
         site_type="交通枢纽", foot_traffic=90, crowd_fit=77, rent_pressure=60, competition=58, visibility=85, car_traffic=62, delivery_fit=70,
         catch_pop_wan=7.4, catch_communities=10, catch_schools=4, catch_malls=5, catch_offices=12, catch_radius_m=900,
         recommended_model="30㎡ 快取店",
         reason="轨道枢纽+夜市商圈双人流叠加，通勤与夜间双峰；快取店型转化枢纽流量，夜间外摆接夜市客流。"),
    dict(id="ST-06", name="BSD 塞尔蓬新社区轴", area="BSD", city="唐格朗", lat=-6.2980, lon=106.6844,
         site_type="社区口", foot_traffic=66, crowd_fit=83, rent_pressure=38, competition=28, visibility=70, car_traffic=65, delivery_fit=52,
         catch_pop_wan=8.9, catch_communities=17, catch_schools=8, catch_malls=3, catch_offices=9, catch_radius_m=1000,
         recommended_model="56㎡ 社区集装箱店",
         reason="新城社区 17 个且每年新增，年轻家庭客群与竞品低密度并存——'先占社区口'战略价值最高的成长型点位。"),
    dict(id="ST-07", name="ITC Kuningan 批发商圈", area="Kuningan", city="雅加达", lat=-6.2333, lon=106.8245,
         site_type="办公区", foot_traffic=71, crowd_fit=64, rent_pressure=45, competition=41, visibility=60, car_traffic=48, delivery_fit=66,
         catch_pop_wan=4.2, catch_communities=5, catch_schools=2, catch_malls=2, catch_offices=22, catch_radius_m=800,
         recommended_model="推车 + 外带窗口",
         reason="批发商圈人流杂但单价低，适合极致性价比模型（Es Teh 路径）；办公+批发混合客群，下午茶场景空白。"),
    dict(id="ST-08", name="Summarecon Bekasi 社区轴", area="Bekasi", city="勿加泗", lat=-6.2479, lon=106.9916,
         site_type="社区口", foot_traffic=62, crowd_fit=79, rent_pressure=33, competition=22, visibility=66, car_traffic=70, delivery_fit=48,
         catch_pop_wan=10.6, catch_communities=21, catch_schools=9, catch_malls=4, catch_offices=6, catch_radius_m=1000,
         recommended_model="56㎡ 社区集装箱店",
         reason="卫星城最大社区群、覆盖人口 10.6 万全榜第一，竞品密度全榜最低——'人口密度换增长'的长期价值点位。"),
    dict(id="ST-09", name="Bandung Dago 学生街", area="Dago", city="万隆", lat=-6.8765, lon=107.6120,
         site_type="学校旁", foot_traffic=85, crowd_fit=84, rent_pressure=35, competition=45, visibility=78, car_traffic=35, delivery_fit=68,
         catch_pop_wan=3.2, catch_communities=8, catch_schools=8, catch_malls=2, catch_offices=3, catch_radius_m=600,
         recommended_model="推车 / 15㎡ 档口",
         reason="万隆高校最密集街区（ITB 半径内），学生客群价格敏感且 UGC 体质强；租金远低于雅加达同量级点位。"),
    dict(id="ST-10", name="Surabaya Rungkut 家庭社区轴", area="Rungkut", city="泗水", lat=-7.3333, lon=112.7667,
         site_type="社区口", foot_traffic=70, crowd_fit=82, rent_pressure=34, competition=30, visibility=68, car_traffic=66, delivery_fit=55,
         catch_pop_wan=9.5, catch_communities=18, catch_schools=9, catch_malls=3, catch_offices=5, catch_radius_m=900,
         recommended_model="56㎡ 社区集装箱店",
         reason="泗水东部最大社区群、覆盖 9.5 万人，家庭客群与低竞品并存——爪哇东翼复制社区店模型的首选点。"),
    dict(id="ST-11", name="Medan Ring Road 枢纽口", area="Ring Road", city="棉兰", lat=3.5952, lon=98.6722,
         site_type="交通枢纽", foot_traffic=82, crowd_fit=72, rent_pressure=40, competition=38, visibility=74, car_traffic=72, delivery_fit=52,
         catch_pop_wan=8.2, catch_communities=12, catch_schools=5, catch_malls=4, catch_offices=6, catch_radius_m=900,
         recommended_model="30㎡ 快取店",
         reason="苏门答腊第一城 ring road 与轻轨换乘叠加，通勤车流全榜最高之一；快取店吃透枢纽流量。"),
    dict(id="ST-12", name="Makassar 海滨旅游带", area="Panakkukang", city="望加锡", lat=-5.1477, lon=119.4227,
         site_type="商场食阁", foot_traffic=78, crowd_fit=70, rent_pressure=48, competition=42, visibility=82, car_traffic=58, delivery_fit=60,
         catch_pop_wan=4.8, catch_communities=9, catch_schools=4, catch_malls=5, catch_offices=4, catch_radius_m=800,
         recommended_model="品牌旗舰体验点",
         reason="印尼东部门户+海滨旅游客流，可见性高、租金仍温和——东部市场形象店与单测的稀缺优质点位。"),
    dict(id="ST-13", name="Denpasar 旅游枢纽带", area="Kuta-Seminyak", city="登巴萨", lat=-8.7060, lon=115.1800,
         site_type="交通枢纽", foot_traffic=80, crowd_fit=72, rent_pressure=55, competition=50, visibility=80, car_traffic=62, delivery_fit=64,
         catch_pop_wan=2.2, catch_communities=6, catch_schools=2, catch_malls=4, catch_offices=3, catch_radius_m=900,
         recommended_model="30㎡ 快取店",
         reason="巴厘岛游客+本地居民双客流，城镇集中度 62% 为离岛最高之一；快取店吃旅游潮汐，外卖接酒店半径。"),
    dict(id="ST-14", name="Balikpapan 能源社区口", area="Batu Ampar", city="巴厘巴板", lat=-1.2370, lon=116.8520,
         site_type="社区口", foot_traffic=68, crowd_fit=76, rent_pressure=36, competition=26, visibility=70, car_traffic=68, delivery_fit=50,
         catch_pop_wan=1.8, catch_communities=8, catch_schools=3, catch_malls=2, catch_offices=6, catch_radius_m=800,
         recommended_model="56㎡ 社区集装箱店",
         reason="加里曼丹能源城，人均收入高、社区成建制、竞品稀少；集中度 70% 的紧凑城市，单店覆盖效率最优。"),
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
        {"name": "Trans Studio Bandung", "lat": -6.9250, "lon": 107.6360},
        {"name": "Tunjungan Plaza Surabaya", "lat": -7.2628, "lon": 112.7384},
        {"name": "Malioboro Mall Yogyakarta", "lat": -7.7930, "lon": 110.3650},
        {"name": "Sun Plaza Medan", "lat": 3.5850, "lon": 98.6750},
        {"name": "Mall Panakkukang Makassar", "lat": -5.1580, "lon": 119.4370},
        {"name": "Paragon Semarang", "lat": -6.9890, "lon": 110.4230},
        {"name": "OPI Mall Palembang", "lat": -2.9450, "lon": 104.7560},
        {"name": "Level 21 Denpasar", "lat": -8.6700, "lon": 115.2080},
        {"name": "Pentacity Balikpapan", "lat": -1.2420, "lon": 116.8600},
        {"name": "Manado Town Square", "lat": 1.4910, "lon": 124.8430},
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
        {"name": "ITB Bandung", "lat": -6.8915, "lon": 107.6104},
        {"name": "ITS Surabaya", "lat": -7.2820, "lon": 112.7940},
        {"name": "UGM Yogyakarta", "lat": -7.7660, "lon": 110.3780},
        {"name": "USU Medan", "lat": 3.5620, "lon": 98.6560},
        {"name": "UNM Makassar", "lat": -5.1720, "lon": 119.4320},
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
        {"name": "Dago Bandung", "lat": -6.8765, "lon": 107.6120},
        {"name": "Rungkut Surabaya", "lat": -7.3333, "lon": 112.7667},
        {"name": "Seturan Yogyakarta", "lat": -7.7830, "lon": 110.4100},
        {"name": "Ring Road Medan", "lat": 3.5950, "lon": 98.6720},
        {"name": "Tanjung Bunga Makassar", "lat": -5.1370, "lon": 119.4150},
        {"name": "Batu Ampar Balikpapan", "lat": -1.2370, "lon": 116.8520},
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
    # ── 全国主要城市热力 ──
    [-6.917, 107.619, 0.66], [-6.8765, 107.612, 0.6], [-6.8915, 107.6104, 0.5],
    [-7.257, 112.752, 0.68], [-7.3333, 112.7667, 0.55], [-7.2628, 112.7384, 0.58],
    [-7.796, 110.370, 0.62], [-7.793, 110.365, 0.55], [-7.766, 110.378, 0.45],
    [3.595, 98.672, 0.64], [3.562, 98.656, 0.45],
    [-5.148, 119.423, 0.6], [-5.137, 119.415, 0.48],
    [-6.967, 110.419, 0.52], [-2.976, 104.775, 0.5], [-8.671, 115.213, 0.5],
    [-8.706, 115.18, 0.56], [-1.237, 116.852, 0.48], [1.4745, 124.842, 0.4],
]

SITE_TYPE_LABEL = {"社区口": "COMMUNITY", "学校旁": "CAMPUS", "商场食阁": "MALL F&B",
                   "办公区": "OFFICE", "交通枢纽": "TRANSIT", "夜市": "NIGHT MARKET",
                   "雷达店铺": "RADAR PICK"}

# ---------- 闭环：雷达发现 → 选址评估 → 合作模式匹配 ----------
# 城市基本面库：都市圈人口(百万) / 城镇集中度(%) / 岛屿 —— 离岛点位按人口×集中度加权估算
CITY_GEO = {
    # 爪哇核心
    "雅加达":   dict(lat=-6.218, lon=106.845, pop=5.2,  rp=55, ct=60, df=75, pop_m=31.0, urban=78),
    "德波":     dict(lat=-6.3649, lon=106.8219, pop=9.2, rp=40, ct=45, df=66, pop_m=31.0, urban=74),
    "南唐格朗": dict(lat=-6.2665, lon=106.7180, pop=6.8, rp=45, ct=62, df=60, pop_m=31.0, urban=72),
    "唐格朗":   dict(lat=-6.2980, lon=106.6844, pop=8.9, rp=40, ct=60, df=58, pop_m=31.0, urban=70),
    "勿加泗":   dict(lat=-6.2479, lon=106.9916, pop=10.6, rp=38, ct=66, df=56, pop_m=31.0, urban=71),
    "万隆":     dict(lat=-6.917, lon=107.619, pop=2.4,  rp=35, ct=45, df=58, pop_m=8.8,  urban=76),
    "日惹":     dict(lat=-7.796, lon=110.370, pop=1.9,  rp=32, ct=42, df=55, pop_m=4.3,  urban=68),
    "泗水":     dict(lat=-7.257, lon=112.752, pop=3.1,  rp=38, ct=48, df=60, pop_m=10.0, urban=72),
    "三宝垄":   dict(lat=-6.967, lon=110.419, pop=2.8,  rp=34, ct=46, df=53, pop_m=3.7,  urban=66),
    # 离岛（人口×集中度定级，集中度低 → 单点模型降权、推车/档口优先）
    "棉兰":     dict(lat=3.595, lon=98.672,  pop=4.1,   rp=36, ct=55, df=52, pop_m=5.2,  urban=58),
    "巨港":     dict(lat=-2.976, lon=104.775, pop=2.6,  rp=33, ct=48, df=50, pop_m=1.9,  urban=52),
    "望加锡":   dict(lat=-5.148, lon=119.423, pop=3.3,  rp=38, ct=52, df=54, pop_m=2.7,  urban=55),
    "登巴萨":   dict(lat=-8.671, lon=115.213, pop=1.6,  rp=42, ct=50, df=56, pop_m=1.1,  urban=62),
    "巴厘巴板": dict(lat=-1.237, lon=116.852, pop=0.9,  rp=37, ct=56, df=48, pop_m=0.71, urban=70),
    "马那多":   dict(lat=1.4745, lon=124.842, pop=0.7,  rp=32, ct=44, df=46, pop_m=0.46, urban=55),
}
CITY_GEO_DEFAULT = CITY_GEO["雅加达"]

# 城市 → 岛屿（爪哇以外自动走离岛修正）
CITY_ISLAND = {"雅加达": "爪哇", "德波": "爪哇", "南唐格朗": "爪哇", "唐格朗": "爪哇", "勿加泗": "爪哇",
               "万隆": "爪哇", "日惹": "爪哇", "泗水": "爪哇", "三宝垄": "爪哇",
               "棉兰": "苏门答腊", "巨港": "苏门答腊", "巴厘巴板": "加里曼丹",
               "望加锡": "苏拉威西", "马那多": "苏拉威西",
               "登巴萨": "巴厘"}

# 最佳匹配模型 → 建议合作模式（发现→评估→合作 闭环的最后一环）
MODEL_COOP = {
    "experience": "品牌联营 / 旗舰加盟",
    "pickup": "外卖联营 + 系统加持",
    "drive": "区域代理 + 车餐加盟",
    "value": "标准加盟 + 供应链直供",
    "cart": "供应链 + 推车租赁",
}


def _jit(seed_str: str, amp: float = 0.02) -> tuple:
    """由 id 生成确定性坐标偏移（演示用，避免随机数导致每次构建漂移）。"""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return ((h % 1000) / 1000 - 0.5) * 2 * amp, ((h // 1000 % 1000) / 1000 - 0.5) * 2 * amp


def _radar_to_candidate(s: dict) -> dict:
    g = CITY_GEO.get(s.get("city"), CITY_GEO_DEFAULT)
    dlat, dlon = _jit(s.get("id", "x"))
    stores = int(s.get("stores", 1))
    dims = s.get("dims", {})
    # 离岛修正：人流/外卖按都市圈人口规模 + 城镇集中度加权（集中度低 → 因子自动降权）
    pop_boost = min(12.0, max(0.0, (g["pop_m"] - 2.0) * 2.5))
    urban_boost = (g["urban"] - 60) * 0.25
    return dict(
        id="RD-" + s["id"], name=s["name"], area=s.get("city", ""), city=s.get("city", ""),
        lat=round(g["lat"] + dlat, 4), lon=round(g["lon"] + dlon, 4),
        site_type="雷达店铺",
        foot_traffic=int(min(93, max(52, 55 + stores * 4 + (dims.get("viral", 70) - 70) * 0.4 + pop_boost + urban_boost))),
        crowd_fit=int(min(92, max(50, dims.get("crowd", 70) + urban_boost))),
        rent_pressure=int(min(70, max(25, g["rp"] - stores * 3))),
        competition=int(min(65, max(15, 60 - (stores - 1) * 8 - max(0, 8 - g["pop_m"]) * 2))),
        visibility=int(dims.get("site", 65)),
        car_traffic=int(min(75, g["ct"] + stores * 3)),
        delivery_fit=int(min(90, g["df"] + dims.get("social", 60) * 0.1 + urban_boost)),
        catch_pop_wan=g["pop"], catch_communities=6 + stores * 2, catch_schools=3,
        catch_malls=2, catch_offices=4 if s.get("city") == "雅加达" else 1,
        catch_radius_m=600,
        recommended_model="", reason="",
        source_type="radar_shop",
        origin="radar", radar_score=s.get("potential_score"),
        photo=s.get("photo"), shop_coop=s.get("coop_model"), shop_coop_note=s.get("coop_note"),
        city_pop_m=g["pop_m"], urban_pct=g["urban"],
        island=CITY_ISLAND.get(s.get("city"), "其他"))


def load_radar_shops() -> list:
    p = Path(__file__).resolve().parents[3] / "web" / "trend" / "data" / "local_brands.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("shops", [])
    except Exception:
        return []


def migrate_siteselect(conn: sqlite3.Connection) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(site_candidate)")]
    if cols and "visibility" not in cols:
        conn.execute("DROP TABLE site_candidate")
    conn.executescript(DDL)


def seed_siteselect(conn: sqlite3.Connection) -> None:
    migrate_siteselect(conn)
    for c in CANDIDATES:
        conn.execute(
            "INSERT OR REPLACE INTO site_candidate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["id"], c["name"], c["area"], c["city"], c["lat"], c["lon"], c["site_type"],
             c["foot_traffic"], c["crowd_fit"], c["rent_pressure"], c["competition"],
             c["visibility"], c["car_traffic"], c["delivery_fit"],
             c["catch_pop_wan"], c["catch_communities"], c["catch_schools"],
             c["catch_malls"], c["catch_offices"], c["catch_radius_m"],
             c["recommended_model"], c["reason"], "demo_seed"))


def _factors(c: dict) -> dict:
    return {"ft": c["foot_traffic"], "cf": c["crowd_fit"],
            "rp": 100 - c["rent_pressure"], "cp": 100 - c["competition"],
            "vs": c["visibility"], "ct": c["car_traffic"], "df": c["delivery_fit"]}


_HARD_FIELD = {"ft": "foot_traffic", "cf": "crowd_fit", "vs": "visibility",
               "ct": "car_traffic", "df": "delivery_fit"}


def _hard_check(m: dict, c: dict) -> list:
    fails = []
    for k, thr in m["hard"].items():
        if k.endswith("_max"):
            if c["rent_pressure"] > thr:
                fails.append(m["hard_label"][k])
        elif c[_HARD_FIELD.get(k, k)] < thr:
            fails.append(m["hard_label"][k])
    return fails


def model_scores(c: dict) -> list:
    f = _factors(c)
    out = []
    for key, m in MODELS.items():
        score = round(sum(w * f[k] for k, w in m["weights"].items()), 1)
        fails = _hard_check(m, c)
        out.append({"key": key, "name": m["name"], "en": m["en"], "icon": m["icon"],
                    "borrow": m["borrow"], "score": score, "eligible": not fails,
                    "hard_fail": fails})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def site_score(c: dict) -> float:
    """综合选址分（基准模型）：人流×0.30 + 客群×0.25 + (100-租金)×0.20 + (100-竞品)×0.25"""
    return round(c["foot_traffic"] * 0.30 + c["crowd_fit"] * 0.25
                 + (100 - c["rent_pressure"]) * 0.20 + (100 - c["competition"]) * 0.25, 1)


def build_siteselect(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_siteselect(conn)
        seed_siteselect(conn)  # INSERT OR REPLACE 幂等：新增候选点随构建自动入库
        conn.commit()
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
    seen = set()
    for r in rows:
        c = dict(r)
        seen.add(c["id"])
        _enrich(c)
        cands.append(c)
    # 雷达发现的潜力店铺 → 自动进入选址评估（闭环：发现 → 评估 → 合作匹配）
    for s in load_radar_shops():
        if "RD-" + s.get("id", "") in seen:
            continue
        c = _radar_to_candidate(s)
        _enrich(c)
        cands.append(c)
    cands.sort(key=lambda c: c["score"], reverse=True)
    return {
        "generated_at": datetime.now(WIB).strftime("%Y-%m-%d %H:%M"),
        "demo": True,
        "source_note": "演示种子数据 · 字段对齐真实 POI 库（OSM/自采）与人流数据源",
        "model_note": "选址模型库：体验店(星巴克) / 快取外卖(瑞幸) / 车餐家庭(麦当劳) / 性价比街铺(蜜雪) / 推车档口(轻资产) —— 加权评分 + 硬条件否决",
        "loop_note": "闭环：雷达发现潜力店 → 五业态选址模型评估 → 匹配合作模式（RD- 前缀为雷达来源；离岛点位按都市圈人口×城镇集中度加权估算）",
        "models_legend": [{"key": k, "name": m["name"], "en": m["en"], "icon": m["icon"], "borrow": m["borrow"]}
                          for k, m in MODELS.items()],
        "candidates": cands,
        "pois": POIS,
        "heat": HEAT,
    }


def _enrich(c: dict) -> None:
    """统一后处理：基准分 + 覆盖圈 + 五模型评分 + 最佳模型 + 合作模式建议 + 城市基本面。"""
    g = CITY_GEO.get(c["city"], CITY_GEO_DEFAULT)
    c["city_pop_m"] = g["pop_m"]
    c["urban_pct"] = g["urban"]
    c["island"] = CITY_ISLAND.get(c["city"], "其他")
    c["score"] = site_score(c)
    c["catchment"] = {"pop_wan": c.pop("catch_pop_wan"), "communities": c.pop("catch_communities"),
                      "schools": c.pop("catch_schools"), "malls": c.pop("catch_malls"),
                      "offices": c.pop("catch_offices"), "radius_m": c.pop("catch_radius_m")}
    c["type_en"] = SITE_TYPE_LABEL.get(c["site_type"], c["site_type"])
    c["models"] = model_scores(c)
    best = next((m for m in c["models"] if m["eligible"]), None)
    c["best_model"] = best
    c["coop_proposal"] = ({"model": best["key"], "mode": MODEL_COOP[best["key"]]}
                          if best else None)


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
