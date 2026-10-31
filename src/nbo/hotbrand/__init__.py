"""热点品牌引擎：像喜茶这样的热点品牌档案——产品×热度×加盟状态×印尼引入路径。

面向客户回答："现在能引入什么品牌、加盟还是复制、它哪些产品正热"。
当前为演示种子（source_type=演示）；photo 字段为 AI 概念参考图，真实抓取照片 URL 预留。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BRAND_DDL = """
CREATE TABLE IF NOT EXISTS hot_brand (
    id TEXT PRIMARY KEY, name TEXT, name_local TEXT, country TEXT, category TEXT,
    franchise_status TEXT, hot_products TEXT, ido_fit REAL, ido_path TEXT, ido_note TEXT,
    social_views_wan REAL, social_likes_wan REAL, social_shares_wan REAL,
    platforms TEXT, ugc_score REAL, remix_note TEXT, photo TEXT, source_type TEXT
);
"""

BRANDS = [
    dict(id="HB-01", name="喜茶", name_local="HEYTEA", country="中国", category="新茶饮",
         status="事业合伙（区域开放）",
         products=["芝芝莓莓", "多肉葡萄", "烤黑糖波波牛乳"],
         fit=68, path="区域代理谈判 + 本地供应链共建",
         note="直营基因强、加盟门槛高；更现实路径是学其'鲜果+芝士奶盖'结构做本土品牌，或与区域代理谈雅加达试点。",
         views=52000, likes=2100, shares=340, platforms=["抖音", "小红书", "IG"],
         ugc=92, remix="奶盖分层特写 + 季节限定开箱；二创门槛低，模板化滤镜官方提供",
         photo="/assets/brand-heytea.jpg", source_type="演示"),
    dict(id="HB-02", name="霸王茶姬", name_local="CHAGEE", country="中国", category="新茶饮",
         status="开放加盟（海外已布局马来西亚）",
         products=["伯牙绝弦", "花田乌龙", "万里木兰"],
         fit=82, path="加盟优先——已有东南亚运营样板",
         note="东南亚已有 100+ 店，加盟体系成熟；印尼市场相对空白，是窗口期品牌。产品标准化程度高，适合直接加盟。",
         views=46000, likes=1800, shares=290, platforms=["抖音", "TikTok", "IG"],
         ugc=88, remix="国风杯身 + 撕杯有礼机制；包装本身即传播单元",
         photo="/assets/brand-chagee.jpg", source_type="演示"),
    dict(id="HB-03", name="蜜雪冰城", name_local="MIXUE", country="中国", category="冰淇淋茶饮",
         status="开放加盟（东南亚 2000+ 店）",
         products=["冰鲜柠檬水", "摩天脆脆", "雪王大圣代"],
         fit=90, path="直接加盟——印尼已验证",
         note="印尼已有大量门店且盈利模型跑通；主题曲营销是教科书案例。加盟费低、供应链本地化最深，复制风险最低。",
         views=88000, likes=3600, shares=510, platforms=["TikTok", "抖音", "YouTube"],
         ugc=95, remix="雪王 IP 二创自由度极高，官方鼓励鬼畜改编——UGC 引擎全开",
         photo="/assets/brand-mixue.jpg", source_type="演示"),
    dict(id="HB-04", name="Knotted", name_local="노티드", country="韩国", category="甜甜圈",
         status="直营不加盟（可学模式）",
         products=["经典奶油甜甜圈", "Ube 香芋限定", "季节联名款"],
         fit=62, path="模式复制——学排队经济学",
         note="不开放加盟；复制其'厚奶油+掰开爆浆'产品结构与饥饿营销打法，用本地烘焙代工落地。",
         views=21000, likes=950, shares=180, platforms=["TikTok", "X"],
         ugc=90, remix="掰开爆浆慢镜头是固定爆款格式；二创无需授权顾虑（学结构不抄 IP）",
         photo="/assets/brand-knotted.jpg", source_type="演示"),
    dict(id="HB-11", name="% Arabica", name_local="アラビカ", country="日本", category="精品咖啡",
         status="区域代理（高门槛）",
         products=["西班牙拿铁", "抹茶拿铁", "单品手冲"],
         fit=60, path="高端商圈代理或学极简空间",
         note="适合雅加达高端商场单点；更普适的是学其'极简白+吧台风'空间语言做中端咖啡档。",
         views=8900, likes=380, shares=55, platforms=["IG", "小红书"],
         ugc=72, remix="% 符号打卡构图；空间摄影是主要内容形式",
         photo="/assets/brand-arabica.jpg", source_type="演示"),
    dict(id="HB-12", name="奈雪", name_local="Nayuki", country="中国", category="茶饮+烘焙",
         status="直营为主（亏损收缩，谨慎）",
         products=["霸气橙子", "草莓魔法棒", "奥利奥脆弱蛋挞"],
         fit=58, path="仅学习——大店模型当前不可复制",
         note="茶饮+烘焙大店模型正在收缩，作为'反面教材库'收录：重资产大店在印尼风险高。",
         views=14000, likes=560, shares=70, platforms=["小红书", "抖音"],
         ugc=68, remix="烘焙茶饮组合拍摄；大店空间 vlog",
         photo="/assets/brand-naixue.jpg", source_type="演示"),
]


def migrate_hotbrand(conn: sqlite3.Connection) -> None:
    conn.executescript(BRAND_DDL)


def seed_hotbrand(conn: sqlite3.Connection) -> None:
    migrate_hotbrand(conn)
    for b in BRANDS:
        conn.execute("INSERT OR REPLACE INTO hot_brand VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (b["id"], b["name"], b["name_local"], b["country"], b["category"], b["status"],
                      json.dumps(b["products"], ensure_ascii=False), b["fit"], b["path"], b["note"],
                      b["views"], b["likes"], b["shares"],
                      json.dumps(b["platforms"], ensure_ascii=False), b["ugc"], b["remix"],
                      b["photo"], b["source_type"]))


# 引入分级（AI 甄别）：按加盟路径自动判定——给招商决策看的硬标签
INTRO_RULES = [
    ("直接加盟", "S", "可加盟 · 直接引入"),
    ("加盟优先", "A", "可加盟 · 优先引入"),
    ("仅学习",   "C", "仅学习 · 不引入"),
    ("代理",     "B", "可代理 · 谈判引入"),
    ("复制",     "B", "模式复制 · 学结构"),
]
INTRO_CLS = {"S": "#34d17b", "A": "#4da3ff", "B": "#e8b246", "C": "#8b98a8"}


def _intro_of(b: dict) -> dict:
    text = " ".join(str(b.get(k) or "") for k in ("path", "status", "ido_path", "franchise_status"))
    for kw, grade, label in INTRO_RULES:
        if kw in text:
            return {"grade": grade, "label": label, "color": INTRO_CLS[grade]}
    return {"grade": "B", "label": "待评估 · 需商务谈判", "color": INTRO_CLS["B"]}


def build_hotbrand(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_hotbrand(conn)
        rows = [dict(r) for r in conn.execute("SELECT * FROM hot_brand")]
    finally:
        conn.close()
    if not rows:
        return {"demo": True, "error": "hot_brand 为空，请先 seed"}
    brands = []
    for b in rows:
        b["hot_products"] = json.loads(b["hot_products"])
        b["platforms"] = json.loads(b["platforms"])
        b["social"] = {"views_wan": b.pop("social_views_wan"), "likes_wan": b.pop("social_likes_wan"),
                       "shares_wan": b.pop("social_shares_wan")}
        b["ugc"] = b.pop("ugc_score")
        b["intro"] = _intro_of(b)
        brands.append(b)
    brands.sort(key=lambda x: -(x["social"]["views_wan"] * 0.5 + x["ido_fit"] * 100))
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "demo": True,
            "window": "近 3 个月", "brands": brands,
            "source_note": "社媒数据为演示口径；photo 为 AI 概念参考图，真实照片抓取后替换 URL 即可。"}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
