"""趋势侦察引擎：六区域热点（近 3 个月）→ 网红视角分析 → 印尼适配与复制性评估。

收录原则（AI 甄别硬门槛）：只收录**适合加盟单店的现制店面食品**（现烤烘焙 /
现调茶饮咖啡 / 现做熟食甜品）。工业级预包装零食不进入雷达——它们撑不起一家
店，不符合品牌加盟孵化定位。

数据边界：当前为带来源标记的种子样本（source_type=演示），表结构与信号字段按
可接入 X/TikTok 热点 API / 人工录入升级设计，替换 seed 即可切换真实接入。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

REGIONS = ["日本", "韩国", "台湾", "泰国", "马来西亚", "中国"]

# 社媒热度口径（演示数据）：播放量/点赞/转发（万）+ 平台分布 + 二创自由度
SOCIAL = {
    "JP-01": dict(views=42000, likes=1300, shares=210, platforms=["TikTok", "X", "IG"], ugc=85,
                  remix="切面 ASMR + 排队 vlog；礼盒开箱模板官方可复用"),
    "JP-02": dict(views=18000, likes=620, shares=95, platforms=["TikTok", "X"], ugc=80,
                  remix="解冻切开流心镜头；便利店寻宝类"),
    "JP-03": dict(views=9000, likes=350, shares=48, platforms=["TikTok", "IG"], ugc=88,
                  remix="切面 reveal + 奶油挤花过程；DIY 复刻教程 UGC 占大头"),
    "KR-01": dict(views=24000, likes=980, shares=170, platforms=["TikTok", "X", "YouTube"], ugc=75,
                  remix="蘸咖啡吃法 + 复古市场探店；低糖对比测评"),
    "KR-02": dict(views=21000, likes=950, shares=180, platforms=["TikTok", "X"], ugc=90,
                  remix="掰开爆浆慢镜头 + 排队测评；学结构不抄 IP"),
    "KR-03": dict(views=6000, likes=240, shares=38, platforms=["TikTok", "YouTube"], ugc=78,
                  remix="开袋香气 reaction + 酱料蘸食测评"),
    "TW-01": dict(views=50000, likes=1900, shares=330, platforms=["TikTok", "IG", "小红书"], ugc=92,
                  remix="咬开珍珠颗粒特写 + 奶茶对比；跨品类二创空间最大"),
    "TW-02": dict(views=8000, likes=300, shares=45, platforms=["小红书", "Threads"], ugc=65,
                  remix="酥皮分层慢镜 + 伴手礼攻略清单"),
    "TW-03": dict(views=3000, likes=130, shares=25, platforms=["TikTok", "IG"], ugc=82,
                  remix="辣度阶梯挑战 + 闻香盲测；挑战类硬通货"),
    "TH-01": dict(views=12000, likes=480, shares=70, platforms=["TikTok", "Shopee Live"], ugc=76,
                  remix="整卷咬断脆响 ASMR；口味全测评矩阵"),
    "TH-02": dict(views=50000, likes=2100, shares=380, platforms=["TikTok", "IG", "YouTube"], ugc=90,
                  remix="拉茶过程 + 泰奶色视觉标签；甜品化二创（泰奶冰/吐司）"),
    "TH-03": dict(views=7000, likes=260, shares=40, platforms=["TikTok", "YouTube"], ugc=72,
                  remix="夜市现烤 + 蘸酱吃法；硬度挑战类"),
    "MY-01": dict(views=12000, likes=520, shares=88, platforms=["TikTok", "IG", "小红书"], ugc=84,
                  remix="流沙裹层特写 + 舔手指 reaction；真假咸蛋黄对比"),
    "MY-02": dict(views=5000, likes=200, shares=30, platforms=["TikTok", "X"], ugc=62,
                  remix="kopitiam 探店 + 三合一盲测"),
    "MY-03": dict(views=6000, likes=230, shares=32, platforms=["YouTube", "TikTok"], ugc=68,
                  remix="冲泡过程 + 料包全加镜头；泡面排行榜测评"),
    "CN-01": dict(views=46000, likes=1900, shares=300, platforms=["抖音", "TikTok"], ugc=89,
                  remix="咀嚼 ASMR + 热量对比测评；办公室囤货 vlog"),
    "CN-02": dict(views=30000, likes=1250, shares=220, platforms=["抖音", "TikTok", "YouTube"], ugc=91,
                  remix="老外首次吃辣条 reaction + 撕咬慢镜；长青格式"),
    "CN-03": dict(views=4000, likes=180, shares=28, platforms=["抖音", "小红书"], ugc=74,
                  remix="开袋气泡声 + 表情 reaction 合集；生命周期短快进快出"),
}

TREND_DDL = """
CREATE TABLE IF NOT EXISTS trend_snack (
    id TEXT PRIMARY KEY, region TEXT, name TEXT, name_local TEXT,
    category TEXT, heat REAL, heat_signals TEXT,
    why_hot TEXT, viral_format TEXT,
    indo_fit REAL, fit_reasons TEXT, adaptation TEXT,
    compliance_note TEXT, replicability TEXT, repl_reason TEXT, source_type TEXT,
    store_mode TEXT
);
"""

SEED_SNACKS = [
    # ── 日本 ──────────────────────────────────────────────
    dict(id="JP-01", region="日本", name="黄油树夹心饼干", name_local="バターの木",
         category="现烤烘焙", heat=94,
         heat_signals=["X 话题 3 个月 42 万帖", "便利店限购+代购溢价 2.5 倍", "TikTok #buttertree 播放 1.8 亿"],
         why_hot="切面卡嚓 ASMR + 黄油横截面特写极具镜头感；'北海道黄油'产地叙事强化送礼属性，网红开箱即内容。",
         viral_format="切面慢镜头 + 排队 vlog；礼盒开箱测评类视频完播率最高。",
         indo_fit=72, fit_reasons="黄油+砂糖口味与印尼 palmiers/蝴蝶酥接受度重叠；礼盒化契合开斋送礼季。",
         adaptation="单店模型 = 现烤柜台（玻璃后厨看切面）+ 伴手礼礼盒墙；8 枚小规格 Rp 25k 价格带；开发榴莲/香蕉本地夹心。",
         compliance_note="现制门店需 PIRT/卫生许可 + Halal；若兼售预包装伴手礼需 BPOM 注册，黄油含量宣称需符合标签法。",
         replicability="中", repl_reason="现烤工艺门槛中等（夹心+烘烤曲线），品牌溢价靠'现烤香气+切面仪式感'，不依赖产地故事。",
         store_mode="现烤专门店 + 伴手礼双轨", source_type="演示"),
    dict(id="JP-02", region="日本", name="现烤巴斯克芝士蛋糕", name_local="バスクチーズケーキ",
         category="现烤甜品", heat=88,
         heat_signals=["TikTok 日本美食榜 TOP3 连续 8 周", "便利店 CV SNS 引流单品"],
         why_hot="'整只现烤、当场切开流心'的仪式感是天然短视频素材；焦香外皮+半熟芯的反差口感评测类内容稳定产出。",
         viral_format="出炉摇铃 + 当场切开流心镜头；整只外带 vs 切片堂食对比。",
         indo_fit=65, fit_reasons="芝士蛋糕在雅加达咖啡馆渠道已验证；现烤模式不依赖冷冻链，爪哇岛城市均可落地。",
         adaptation="配 sago/椰糖淋酱做本地化款；小门店模型：1 台风炉+明档切台，商场档口/街边店均可。",
         compliance_note="现制门店需 PIRT/卫生许可；乳源需 Halal 认证，本地乳脂供应链成熟。",
         replicability="中", repl_reason="配方可复制，明档切台是记忆点；客单价 Rp 60-120k，适合作为加盟旗舰店品类。",
         store_mode="现烤甜品专门店", source_type="演示"),
    dict(id="JP-03", region="日本", name="鲜奶油水果三明治", name_local="フルーツサンド",
         category="现制烘焙", heat=81,
         heat_signals=["TikTok #fruitsandwich 播放 9000 万", "首尔/曼谷门店相继复刻"],
         why_hot="厚切水果截面色彩爆炸，是'INS 风'摆拍标配；制作简单可复制引发 DIY 二创。",
         viral_format="切面 reveal + 奶油挤花过程；复刻教程类 UGC 占大头。",
         indo_fit=58, fit_reasons="视觉引流强，但冷链短保（当日）对印尼末端配送挑战大。",
         adaptation="限定网红店现制现售（不做零售化）；用本地芒果/红毛丹替代高价进口果。",
         compliance_note="现制餐饮需当地 PIRT/卫生许可；奶油需冷链记录。",
         replicability="高", repl_reason="设备与工艺简单，适合作为网红店引流品而非零售 SKU。",
         store_mode="现制烘焙专门店", source_type="演示"),
    # ── 韩国 ──────────────────────────────────────────────
    dict(id="KR-01", region="韩国", name="药果（蜂蜜油果子）", name_local="약과",
         category="现制传统糕点", heat=91,
         heat_signals=[" Olive Young 零食榜连续 12 周 TOP5", "TikTok 复古韩食话题播放 2.4 亿"],
         why_hot="'传统点心年轻化'叙事 + 咖啡搭配场景；低糖/无麸质改良版制造第二话题。",
         viral_format="蘸咖啡吃法 + 传统市场探店；低糖对比测评类。",
         indo_fit=70, fit_reasons="蜂蜜油炸甜味与印尼 kue 传统高度兼容；常温长保适合 warung 渠道。",
         adaptation="单店模型 = 现炸明档 + 咖啡档口组合（韩国药果 café 模式）；减糖 30% 适配本地甜度；外带礼盒做伴手礼。",
         compliance_note="现制需 PIRT/卫生许可；蜂蜜需 Halal 来源证明；油炸用油管理需留记录。",
         replicability="高", repl_reason="kue 油炸工艺与印尼本地高度相通，设备门槛低；差异化在口味微调与空间叙事。",
         store_mode="现制糕点 café（明档+外带）", source_type="演示"),
    dict(id="KR-02", region="韩国", name="Knotted 奶油甜甜圈", name_local="노티드 도넛",
         category="现制甜品", heat=86,
         heat_signals=["门店排队 2 小时+ 打卡内容", "首尔甜甜圈地图类笔记 3 个月 15 万篇"],
         why_hot="'甜甜圈中的香奈儿'定位；厚奶油填充+可爱造型是顶流打卡单品。",
         viral_format="掰开爆浆镜头 + 排队测评；联名限定款饥饿营销。",
         indo_fit=62, fit_reasons="甜食+奶油在雅加达商场客群中验证过；高客单适合网红店模式。",
         adaptation="减甜+增咸（奶酪/焦糖盐味）；门店即制即售，不做预包装。",
         compliance_note="现制同 JP-03；若做预包装需 BPOM。",
         replicability="中", repl_reason="工艺可复制，但'排队经济学'依赖商圈选址与营销预算。",
         store_mode="现制甜品专门店", source_type="演示"),
    # ── 台湾 ──────────────────────────────────────────────
    dict(id="TW-02", region="台湾", name="现烤太阳饼/老婆饼", name_local="太陽餅",
         category="现烤糕饼", heat=76,
         heat_signals=["机场伴手礼销量回升 40%", "小红书/Threads 礼盒开箱热"],
         why_hot="'现烤出炉 + 酥皮层次切面'仪式感；老字号翻新包装适礼场景，质感类内容友好。",
         viral_format="出炉整盘特写 + 酥皮分层慢镜；现烤店探店 + 伴手礼攻略清单。",
         indo_fit=60, fit_reasons="酥饼工艺与印尼 kue 千层酥（kue lapis）相通；现烤香气型门店在商场客群中已验证。",
         adaptation="开斋节/春节限定礼盒；麦芽糖内馅改椰糖（gula aren）版本；档口店+礼盒墙单店模型。",
         compliance_note="现制需 PIRT/卫生许可；椰糖为本地原料可降成本；兼售预包装礼盒需 BPOM 流通许可。",
         replicability="高", repl_reason="烘焙工艺本地完全可复制，竞争点在出炉仪式感、包装设计与节庆营销。",
         store_mode="现烤糕饼专门店 + 伴手礼", source_type="演示"),
    # ── 泰国 ──────────────────────────────────────────────
    dict(id="TH-02", region="泰国", name="泰式手打奶茶", name_local="ชาไทย",
         category="现调茶饮", heat=85,
         heat_signals=["TikTok #thaitea 播放 5 亿+", "泰国手标茶代购长盛不衰"],
         why_hot="橙红色泽辨识度极高，'泰奶色'成为视觉标签；手标拉茶过程自带表演性，是门店活广告。",
         viral_format="拉茶高空倒茶过程 + 橙色调色对比；泰奶甜品化（泰奶冰/泰奶吐司）二创。",
         indo_fit=77, fit_reasons="茶饮在印尼高速增长；泰奶与印尼 teh manis 味型接近，教育成本低；手标式 franchise 模型全球可考。",
         adaptation="减糖版 + 印尼红茶底拼配；档口店模型（3-5㎡ 即可起店）；袋装茶底做外卖零售延伸。",
         compliance_note="色素（日落黄等）BPOM 限量严格，需天然色素替代方案；现制饮品需卫生许可。",
         replicability="高", repl_reason="操作标准化程度高，培训一周可上岗；差异化在茶底拼配与减糖技术。",
         store_mode="现调茶饮档口店", source_type="演示"),
    dict(id="TH-03", region="泰国", name="烤鱿鱼丝/酸辣鱿鱼", name_local="ปลาหมึกย่าง",
         category="现烤海味熟食", heat=71,
         heat_signals=["泰国夜市内容常年热门", "711 鱿鱼干月销稳定前三"],
         why_hot="夜市烟火气内容的核心道具；撕扯质感适合咀嚼类 ASMR。",
         viral_format="夜市现烤 + 蘸酱吃法；硬度挑战类内容。",
         indo_fit=69, fit_reasons="鱿鱼制品在印尼沿海市场基础好；蘸酱吃法与 sambal 体系兼容。",
         adaptation="单店/档口模型 = 现烤明档 + sambal roa 蘸酱台（夜市烟火气直接复刻）；独立小包可做外卖延伸。",
         compliance_note="现烤水产需卫生许可 + 冷链记录；若兼售预包装干货需 BPOM 水产类注册。",
         replicability="高", repl_reason="原料与烤工艺本地成熟，设备仅需烤炉+排烟；差异化在蘸酱体系与调味升级。",
         store_mode="现烤熟食档（夜市模型）", source_type="演示"),
    # ── 马来西亚 ──────────────────────────────────────────
    dict(id="MY-02", region="马来西亚", name="南洋白咖啡（现调）", name_local="White Coffee",
         category="现调咖啡", heat=73,
         heat_signals=["东马特产伴手礼长销", "TikTok 南洋咖啡文化内容回温"],
         why_hot="'南洋慢生活'文化叙事；现拉白咖啡+炼乳的浓醇口感，评测类内容稳定产出。",
         viral_format="传统 kopitiam 探店 + 拉茶式拉咖啡过程；早餐搭挡测评。",
         indo_fit=70, fit_reasons="印尼本身是咖啡大国，kopi 店密度极高；现调白咖啡差异化在口感顺滑与文化叙事。",
         adaptation="与 toraja/aceh 豆拼配做'印尼白咖啡'；kopitiam 档口模型（咖啡+吐司+半熟蛋组合）。",
         compliance_note="现制饮品需卫生许可；植脂末改用鲜奶/淡奶规避反式脂肪争议。",
         replicability="中", repl_reason="操作流程标准化易培训；竞争点在豆种故事与 kopitiam 空间氛围。",
         store_mode="现调咖啡 kopitiam 档口", source_type="演示"),
    # ── 中国 ──────────────────────────────────────────────
]


def migrate_trend(conn: sqlite3.Connection) -> None:
    conn.executescript(TREND_DDL)
    # 存量库补列（store_mode 加盟适配甄别）
    cols = {r[1] for r in conn.execute("PRAGMA table_info(trend_snack)")}
    if "store_mode" not in cols:
        conn.execute("ALTER TABLE trend_snack ADD COLUMN store_mode TEXT")


def seed_trend(conn: sqlite3.Connection, snacks: list[dict] | None = None) -> None:
    migrate_trend(conn)
    for s in snacks or SEED_SNACKS:
        conn.execute("INSERT OR REPLACE INTO trend_snack VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (s["id"], s["region"], s["name"], s["name_local"], s["category"],
                      s["heat"], json.dumps(s["heat_signals"], ensure_ascii=False),
                      s["why_hot"], s["viral_format"], s["indo_fit"], s["fit_reasons"],
                      s["adaptation"], s["compliance_note"], s["replicability"],
                      s["repl_reason"], s["source_type"],
                      s.get("store_mode", "现制专门店")))


def _row_to_snack(r: sqlite3.Row) -> dict:
    s = dict(r)
    s["heat_signals"] = json.loads(s["heat_signals"])
    return s


def build_trend(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_trend(conn)
        snacks = [_row_to_snack(r) for r in conn.execute("SELECT * FROM trend_snack")]
    finally:
        conn.close()
    if not snacks:
        return {"demo": True, "error": "trend_snack 为空，请先 seed"}
    snacks.sort(key=lambda s: -s["heat"])
    for s in snacks:
        s["social"] = SOCIAL.get(s["id"], {})
    by_region = {reg: sorted([s for s in snacks if s["region"] == reg],
                             key=lambda s: -s["heat"]) for reg in REGIONS}
    # 反向指导：按印尼适配分 × 复制性排序，提炼可操作方向
    W_RANK = {"高": 1.0, "中": 0.6, "低": 0.3}
    ranked = sorted(snacks, key=lambda s: -(s["indo_fit"] * W_RANK.get(s["replicability"], 0.5)))
    top = ranked[:5]
    guidance = {
        "priority_copies": [{"id": s["id"], "name": s["name"], "region": s["region"],
                             "indo_fit": s["indo_fit"], "replicability": s["replicability"],
                             "action": s["adaptation"]} for s in top],
        "screening": "AI 收录硬门槛：适合加盟单店的现制店面食品（现烤/现调/现做）；工业级预包装零食不进入雷达。",
        "directions": [
            "单店模型优先：每款信号都必须回答'这家店长什么样、多少平米、几个人'——档口 3-5㎡ 到专门店 30-60㎡ 均已标注门店形态。",
            "现制是壁垒：现烤香气、明档表演（拉茶/切巴斯克/现炸药果）是包装零食无法复制的护城河，也是短视频天然素材。",
            "调味嫁接公式：东亚爆款味型 × sambal/椰糖本地底味，是低成本差异化主线（韩甜、泰奶、南洋咖啡已验证）。",
            "合规前置：现制门店需 PIRT/卫生许可 + Halal；兼售预包装伴手礼再叠加 BPOM，立项时同步启动。",
        ],
    }
    return {"generated_at": datetime.now().isoformat(timespec="seconds"),
            "demo": True, "window": "近 3 个月", "regions": REGIONS,
            "snacks": snacks, "by_region": by_region, "guidance": guidance,
            "source_note": "当前为演示种子数据；信号字段结构与真实接入（X/TikTok 热点 API）对齐，替换即切换。"}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
