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
         photo="/assets/brand-heytea.png", source_type="演示"),
    dict(id="HB-02", name="霸王茶姬", name_local="CHAGEE", country="中国", category="新茶饮",
         status="开放加盟（海外已布局马来西亚）",
         products=["伯牙绝弦", "花田乌龙", "万里木兰"],
         fit=82, path="加盟优先——已有东南亚运营样板",
         note="东南亚已有 100+ 店，加盟体系成熟；印尼市场相对空白，是窗口期品牌。产品标准化程度高，适合直接加盟。",
         views=46000, likes=1800, shares=290, platforms=["抖音", "TikTok", "IG"],
         ugc=88, remix="国风杯身 + 撕杯有礼机制；包装本身即传播单元",
         photo=None, source_type="演示"),
    dict(id="HB-03", name="蜜雪冰城", name_local="MIXUE", country="中国", category="冰淇淋茶饮",
         status="开放加盟（东南亚 2000+ 店）",
         products=["冰鲜柠檬水", "摩天脆脆", "雪王大圣代"],
         fit=90, path="直接加盟——印尼已验证",
         note="印尼已有大量门店且盈利模型跑通；主题曲营销是教科书案例。加盟费低、供应链本地化最深，复制风险最低。",
         views=88000, likes=3600, shares=510, platforms=["TikTok", "抖音", "YouTube"],
         ugc=95, remix="雪王 IP 二创自由度极高，官方鼓励鬼畜改编——UGC 引擎全开",
         photo=None, source_type="演示"),
    dict(id="HB-04", name="Knotted", name_local="노티드", country="韩国", category="甜甜圈",
         status="直营不加盟（可学模式）",
         products=["经典奶油甜甜圈", "Ube 香芋限定", "季节联名款"],
         fit=62, path="模式复制——学排队经济学",
         note="不开放加盟；复制其'厚奶油+掰开爆浆'产品结构与饥饿营销打法，用本地烘焙代工落地。",
         views=21000, likes=950, shares=180, platforms=["TikTok", "X"],
         ugc=90, remix="掰开爆浆慢镜头是固定爆款格式；二创无需授权顾虑（学结构不抄 IP）",
         photo="/assets/brand-knotted.png", source_type="演示"),
    dict(id="HB-05", name="小老板", name_local="Tao Kae Noi", country="泰国", category="海苔零食",
         status="经销代理（可复制产线）",
         products=["香脆海苔卷（辣味）", "冬阴功味海苔", "大卷分享装"],
         fit=85, path="双轨：代理引进 + 本地代工复制",
         note="印尼本身是海苔原料产地，复制成本全球最低；同时可谈区域经销快速上架。落地评分 S 级概念。",
         views=15000, likes=620, shares=95, platforms=["TikTok", "Shopee Live"],
         ugc=78, remix="整卷咬断脆响 ASMR；口味测评矩阵类内容长尾稳定",
         photo="/assets/brand-taokae.png", source_type="演示"),
    dict(id="HB-06", name="IRVINS", name_local="IRVINS Salted Egg", country="新加坡", category="咸蛋黄零食",
         status="区域代理",
         products=["咸蛋黄鱼皮", "咸蛋黄薯片", "松露味鱼皮"],
         fit=80, path="代理引进 + 本地鱼皮成本优势复制",
         note="品牌溢价强适合做礼品渠道；复制版可用印尼廉价鱼皮原料打 Rp 15k 大众价格带错位竞争。",
         views=9800, likes=410, shares=66, platforms=["IG", "小红书", "TikTok"],
         ugc=75, remix="流沙裹层特写 + 舔手指 reaction；礼盒开箱适配节庆",
         photo="/assets/brand-irvins.png", source_type="演示"),
    dict(id="HB-07", name="卡乐比", name_local="Calbee", country="日本", category="膨化零食",
         status="经销代理",
         products=["薯条三兄弟", "坚脆薯片", "水果麦片"],
         fit=72, path="经销引进 + 联名学习",
         note="单品生命周期管理教科书：限定口味 + 地区限定制造稀缺。可与本地品牌学其上新节奏。",
         views=12000, likes=500, shares=80, platforms=["X", "TikTok", "小红书"],
         ugc=70, remix="地区限定收集玩法；开箱测评类内容稳定产出",
         photo=None, source_type="演示"),
    dict(id="HB-08", name="卫龙", name_local="Weilong", country="中国", category="辣条豆干",
         status="经销 + 出海建厂",
         products=["大面筋", "魔芋爽", "亲嘴烧"],
         fit=65, path="经销试水温 + 魔芋品类重点学",
         note="魔芋爽是 S 级信号：低卡解痒精准。辣条本体在印尼需品类教育，先做魔芋线。",
         views=30000, likes=1300, shares=210, platforms=["抖音", "TikTok"],
         ugc=85, remix="老外首次吃辣条 reaction 是长青格式；热量对比测评",
         photo=None, source_type="演示"),
    dict(id="HB-09", name="三养", name_local="Samyang", country="韩国", category="方便食品",
         status="经销代理（已全球化）",
         products=["火鸡面", "奶油火鸡面", "辣鸡酱料"],
         fit=75, path="经销引进——辣挑战内容生态现成",
         note="印尼嗜辣基础极佳；火鸡面辣挑战内容可无缝平移，酱料单独引进做本地速食联名。",
         views=65000, likes=2700, shares=430, platforms=["TikTok", "YouTube", "IG"],
         ugc=93, remix="辣挑战阶梯是跨文化硬通货；印尼博主二创量巨大",
         photo=None, source_type="演示"),
    dict(id="HB-10", name="茶颜悦色", name_local="茶颜悦色", country="中国", category="新茶饮",
         status="直营不加盟（学文化叙事）",
         products=["幽兰拿铁", "声声乌龙", "桂花弄"],
         fit=55, path="学文化叙事——不做加盟指望",
         note="不开放加盟且区域保护强；其价值在'新中式文化叙事'方法论，供本土品牌策划库参考。",
         views=18000, likes=800, shares=120, platforms=["小红书", "抖音"],
         ugc=82, remix="国风美学 + 城市限定；二创以视觉模板为主",
         photo=None, source_type="演示"),
    dict(id="HB-11", name="% Arabica", name_local="アラビカ", country="日本", category="精品咖啡",
         status="区域代理（高门槛）",
         products=["西班牙拿铁", "抹茶拿铁", "单品手冲"],
         fit=60, path="高端商圈代理或学极简空间",
         note="适合雅加达高端商场单点；更普适的是学其'极简白+吧台风'空间语言做中端咖啡档。",
         views=8900, likes=380, shares=55, platforms=["IG", "小红书"],
         ugc=72, remix="% 符号打卡构图；空间摄影是主要内容形式",
         photo=None, source_type="演示"),
    dict(id="HB-12", name="奈雪", name_local="Nayuki", country="中国", category="茶饮+烘焙",
         status="直营为主（亏损收缩，谨慎）",
         products=["霸气橙子", "草莓魔法棒", "奥利奥脆弱蛋挞"],
         fit=58, path="仅学习——大店模型当前不可复制",
         note="茶饮+烘焙大店模型正在收缩，作为'反面教材库'收录：重资产大店在印尼风险高。",
         views=14000, likes=560, shares=70, platforms=["小红书", "抖音"],
         ugc=68, remix="烘焙茶饮组合拍摄；大店空间 vlog",
         photo=None, source_type="演示"),
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
