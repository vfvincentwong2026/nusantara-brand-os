"""印尼本地网红品牌雷达：发现本地正在爆的品牌，评估合作价值。

商业模式定位：不做复制者，做本地网红品牌的放大器——
供应链网络加持 / 社交媒体系统加持 / 策略打法输出。
数据源：X 公开数据实抓快照（data/radar/x_snapshot_*.json，见 xsnapshot.py）叠加演示种子；
未被实抓覆盖的字段（IG/TikTok、播放、互动率、增速、缺口分等）仍为演示估算，逐字段标注于 provenance。
IG 采集在 igsnapshot.py：只读品牌清单里已经记下的 handle，凭证只来自环境变量。
build_localradar 不读取 IG 快照；没有快照时，上述演示标注保持不变。
"""
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from nbo.webpaths import asset

WIB = timezone(timedelta(hours=7))

DDL = """
CREATE TABLE IF NOT EXISTS local_brand (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  name_cn TEXT NOT NULL,
  city TEXT NOT NULL,
  category TEXT NOT NULL,
  stage TEXT NOT NULL,                -- 起步期 / 上升期 / 爆发期
  ig TEXT, tiktok TEXT, x TEXT,
  followers_wan REAL, views_wan REAL, likes_wan REAL, shares_wan REAL,
  er REAL,                            -- 互动率 %
  growth_30d REAL,                    -- 近30天热度增速 %
  heat REAL,                          -- 综合热度 0-100
  why_hot TEXT, viral_format TEXT, heat_signals TEXT,
  need_supply INTEGER, need_social INTEGER, need_strategy INTEGER,  -- 缺口分 0-100（越高越需要我们加持）
  boost TEXT,                         -- 我们能给的（JSON 数组）
  coop_model TEXT, coop_note TEXT,
  contact TEXT,
  source_type TEXT DEFAULT 'demo_seed'
);
"""

# 演示种子：印尼本地真实知名品牌的演示口径数据
BRANDS = [
    dict(id="ID-01", name="Kopi Kenangan", name_cn="肯南洋咖啡", city="雅加达", category="现制咖啡", stage="爆发期",
         ig="@kopikenangan.id", tiktok="@kopikenangan", x="@KopiKenangan",
         followers_wan=58.2, views_wan=720, likes_wan=96, shares_wan=14.8, er=7.9, growth_30d=41, heat=94,
         why_hot="便利店价格带精品咖啡：2 万盾一杯拿铁击穿雅加达通勤场景，App 会员体系把复购锁成习惯。",
         viral_format="上班族晨队实拍 + '比星巴克便宜一半' 对比梗，天然 UGC 模板",
         heat_signals=["TikTok #kopikenangan 标签播放 4.1 亿", "IG Reels 单条最高 680 万播放", "X 雅加达通勤话题周均 2 次热搜"],
         need_supply=72, need_social=55, need_strategy=48,
         boost=["供应链网络加持", "区域加密选址体系"],
         coop_model="供应链共建 + 区域联营", coop_note="门店已规模化，机会在二三线城市供应链下沉与冷库共配。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-02", name="Janji Jiwa", name_cn="珍吉瓦", city="雅加达", category="现制咖啡", stage="爆发期",
         ig="@kopijanjijiwa", tiktok="@janjijiwa", x="@janjijiwa",
         followers_wan=44.6, views_wan=510, likes_wan=71, shares_wan=9.2, er=7.2, growth_30d=35, heat=89,
         why_hot=" kiosk 小店模型极致坪效：3㎡ 档口 + 外卖占比 70%，'咖啡不用坐下来喝' 心智强。",
         viral_format="档口出品 15 秒倒计时挑战 + 骑手取餐大军航拍",
         heat_signals=["TikTok #janjijiwa 播放 2.8 亿", "外卖平台月销 300 万杯", "加盟咨询量月环比 +58%"],
         need_supply=80, need_social=60, need_strategy=52,
         boost=["供应链网络加持", "加盟体系输出", "选址引擎"],
         coop_model="加盟体系输出 + 供应链托管", coop_note="加盟扩张快但品控与供应不稳，正是体系化加持窗口。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-03", name="Fore Coffee", name_cn="福咖啡", city="雅加达", category="现制咖啡", stage="上升期",
         ig="@fore.coffee", tiktok="@forecoffee", x="@forecoffee",
         followers_wan=31.4, views_wan=340, likes_wan=45, shares_wan=6.1, er=6.8, growth_30d=52, heat=84,
         why_hot="科技感第三空间：App 点单 + 轻食矩阵，抓住 Z 世代'办公第三地'。",
         viral_format="门店空间打卡 + 限定杯套收集机制",
         heat_signals=["IG 打卡笔记月增 2.4 万条", "TikTok 新品首发视频均播 120 万", "增速近 30 天 +52%"],
         need_supply=65, need_social=42, need_strategy=58,
         boost=["轻食供应链引入", "会员策略输出"],
         coop_model="品类供应链合作", coop_note="咖啡已稳，轻食 SKU 供应与冷链是短板。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-04", name="Haus!", name_cn="豪斯饮品", city="雅加达", category="综合现制饮品", stage="爆发期",
         ig="@haus.indonesia", tiktok="@hausindonesia", x="@hausindonesia",
         followers_wan=49.8, views_wan=560, likes_wan=78, shares_wan=11.3, er=8.1, growth_30d=38, heat=88,
         why_hot="全价位饮品矩阵：咖啡/奶茶/果茶一个档口全卖，'排队一次买全家的水'。",
         viral_format="一家人饮品分工梗 + 隐藏菜单 DIY 搭配",
         heat_signals=["TikTok #hausindonesia 播放 3.3 亿", "X 家庭消费话题讨论量周 +44%", "校园店型坪效第一"],
         need_supply=76, need_social=50, need_strategy=55,
         boost=["供应链网络加持", "爆品机制设计"],
         coop_model="供应链 + 爆品共创", coop_note="SKU 过宽导致备货浪费，需要精选供应链与爆品聚焦策略。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-05", name="Richeese Factory", name_cn="丽芝士工厂", city="万隆", category="芝士熟食快餐", stage="上升期",
         ig="@richeesefactory", tiktok="@richeesefactory", x="@richeese_factory",
         followers_wan=27.9, views_wan=290, likes_wan=38, shares_wan=5.4, er=6.1, growth_30d=29, heat=78,
         why_hot="芝士酱瀑布 + 炸鸡双王牌，'热量炸弹'视觉冲击是天然短视频素材。",
         viral_format="芝士拉丝慢镜头 + 瀑布酱 ASMR",
         heat_signals=["TikTok 拉丝挑战参与 12 万条", "IG 瀑布酱视频均播 90 万", "二级市场（马来/菲律宾）询问加盟"],
         need_supply=70, need_social=62, need_strategy=66,
         boost=["海外扩张策略", "社媒矩阵代运营", "供应链标准化"],
         coop_model="出海联营 + 体系输出", coop_note="国内稳态、寻求海外复制——与我们的跨国供应链网络互补。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-06", name="Es Teh Indonesia", name_cn="印尼冰茶", city="日惹", category="现制茶饮", stage="爆发期",
         ig="@esteh.indonesia", tiktok="@esteh.indonesia", x="@estehindonesia",
         followers_wan=38.5, views_wan=610, likes_wan=83, shares_wan=15.6, er=8.8, growth_30d=67, heat=92,
         why_hot="8 千盾一杯柠檬茶的绝对价格锚 + 校园店模型，日惹起家三个月席卷爪哇。",
         viral_format="'大学生第一杯品牌茶' 开学季刷屏 + 杯身方言梗包装",
         heat_signals=["TikTok #estehindonesia 播放 5.2 亿（30天+67%）", "加盟商排队视频播放破千万", "X 校园话题连续 5 次热搜"],
         need_supply=88, need_social=58, need_strategy=61,
         boost=["供应链网络加持", "加盟体系输出", "区域仓配共建"],
         coop_model="加盟体系输出 + 供应链共建", coop_note="扩张最猛但供应链最薄：茶叶/糖浆依赖分散采购，是最佳加持窗口。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-07", name="Kopi Tuku", name_cn="都库咖啡", city="雅加达", category="现制咖啡", stage="上升期",
         ig="@tokokopituku", tiktok="@kopituku", x="@kopituku",
         followers_wan=18.2, views_wan=150, likes_wan=21, shares_wan=2.8, er=7.4, growth_30d=33, heat=72,
         why_hot="'社区咖啡窗口店'鼻祖：只卖 4 个 SKU，把单品做到极致性价比。",
         viral_format="4 SKU 菜单墙打卡 + 老社区情怀叙事",
         heat_signals=["IG 社区探店笔记月增 8000 条", "TikTok 窗口店模型模仿视频 2 万条"],
         need_supply=74, need_social=68, need_strategy=63,
         boost=["社媒矩阵代运营", "多店复制手册", "供应链集采"],
         coop_model="品牌联营 + 系统加持", coop_note="模型优秀但品牌声量未匹配产品力，社媒系统加持空间最大。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-08", name="Sour Sally", name_cn="酸莎莉", city="雅加达", category="冻酸奶甜品", stage="起步期",
         ig="@soursally", tiktok="@soursally.id", x="@soursally",
         followers_wan=9.6, views_wan=64, likes_wan=9.4, shares_wan=1.2, er=6.6, growth_30d=47, heat=63,
         why_hot="健康甜品定位：冻酸奶 + 新鲜水果塔，抓住中产女性下午茶场景。",
         viral_format="水果塔组装过程延时拍摄 + 低卡标签",
         heat_signals=["IG Reels 女性向内容互动率 9.2%", "TikTok #soursally 30 天播放 +47%"],
         need_supply=69, need_social=71, need_strategy=72,
         boost=["冷链供应链", "社媒内容系统", "场景营销策略"],
         coop_model="深度孵化（供应链+社媒+策略全包）", coop_note="起步阶段、三缺口都高——最适合全托管式深度孵化样板。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-09", name="Roti'O", name_cn="罗蒂欧", city="泗水", category="现烤烘焙", stage="爆发期",
         ig="@rotiocomalang", tiktok="@rotiocomalang", x="@rotiocomalang",
         followers_wan=41.3, views_wan=480, likes_wan=66, shares_wan=10.9, er=7.6, growth_30d=36, heat=86,
         why_hot="'omo 咖啡包'单品打天下：刚出炉面包 + 咖啡酱的组合拳，商场档口模型坪效极高。",
         viral_format="出炉时刻 ASMR + 咖啡酱撕开瞬间",
         heat_signals=["TikTok #rotio 播放 3.8 亿", "商场档口加盟咨询月环比 +71%", "X '泗水之光' 话题讨论"],
         need_supply=78, need_social=46, need_strategy=49,
         boost=["中央厨房供应链", "加盟体系输出"],
         coop_model="供应链共建 + 加盟输出", coop_note="现烤模式对中央厨房与配送时效要求极高，供应链共建是最硬切入点。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="ID-10", name="Gulu Gulu", name_cn="咕噜咕噜", city="雅加达", category="台式奶茶", stage="起步期",
         ig="@guluguluid", tiktok="@gulugulu.id", x="@gulugulu_id",
         followers_wan=5.8, views_wan=32, likes_wan=4.6, shares_wan=0.6, er=5.9, growth_30d=58, heat=55,
         why_hot="黑糖珍珠鲜奶现做表演：档口现场熬糖，'看得见的制作'是核心传播点。",
         viral_format="熬糖过程直播感实拍 + 珍珠挂壁镜头",
         heat_signals=["TikTok 熬糖视频单条最高 210 万播放", "30 天热度增速 +58%（低基数高斜率）"],
         need_supply=66, need_social=75, need_strategy=70,
         boost=["社媒内容系统", "选址引擎", "爆品机制设计"],
         coop_model="深度孵化（供应链+社媒+策略全包）", coop_note="高增速低基数，早介入成本最低——典型的'投早投小'候选。",
         contact="ptxdirectionpublicrelations@gmail.com"),
    # ID-11 / ID-12：已列入追踪，但 X 粉丝与提及量尚未进入每日快照。不填估算数字。
    # 本土来源只是标签，不决定是否追踪；这两家按任务标为未核实。
    dict(id="ID-11", name="Tomoro Coffee", name_cn="Tomoro Coffee", city="未核实", category="咖啡", stage="未核实",
         ig="@tomorocoffee.id", tiktok="", x="@TomoroCoffee_ID",
         website="https://www.tomoro-coffee.id/",
         origin_label="未核实", metrics_pending=True,
         followers_wan=None, views_wan=None, likes_wan=None, shares_wan=None,
         er=None, growth_30d=None, heat=None,
         why_hot="官方 X 与 IG、官网已按公开品牌清单列入。粉丝、提及和热度等待每日 X 刷新，这里不填估算数字。",
         viral_format="未核实",
         heat_signals=["【待刷新】官方号 @TomoroCoffee_ID 已列入追踪；粉丝、发帖与近 7 天提及尚未抓取"],
         need_supply=None, need_social=None, need_strategy=None,
         boost=[],
         coop_model="待评估", coop_note="已列入雷达追踪。本土来源未核实，该标签不决定是否追踪。",
         contact=""),
    dict(id="ID-12", name="Calais Tea", name_cn="Calais Tea", city="未核实", category="奶茶", stage="未核实",
         ig="@calaistea", tiktok="", x="@CalaisTea",
         website="http://www.calaistea.com",
         origin_label="未核实", metrics_pending=True,
         followers_wan=None, views_wan=None, likes_wan=None, shares_wan=None,
         er=None, growth_30d=None, heat=None,
         why_hot="官方 X 与 IG、官网已按公开品牌清单列入。粉丝、提及和热度等待每日 X 刷新，这里不填估算数字。",
         viral_format="未核实",
         heat_signals=["【待刷新】官方号 @CalaisTea 已列入追踪；粉丝、发帖与近 7 天提及尚未抓取"],
         need_supply=None, need_social=None, need_strategy=None,
         boost=[],
         coop_model="待评估", coop_note="已列入雷达追踪。本土来源未核实，该标签不决定是否追踪。",
         contact=""),
]

# 已有品牌的本土标签来自 data/radar/brand_list_coffee_tea_2026-11-04.json 的 local 字段。
# 没有对应条目的品牌不填。标签只作展示，不参与是否追踪的判断。
_ORIGIN_FROM_BRAND_LIST = {
    "ID-01": "本土",
    "ID-02": "本土",
    "ID-03": "本土",
    "ID-04": "本土",
    "ID-05": "本土",
    "ID-06": "本土",
    "ID-07": "本土",
    "ID-08": "本土",
    "ID-09": "本土",
    "ID-10": "本土（Sour Sally Group 旗下，台式概念）",
}
for _b in BRANDS:
    if "origin_label" not in _b and _b["id"] in _ORIGIN_FROM_BRAND_LIST:
        _b["origin_label"] = _ORIGIN_FROM_BRAND_LIST[_b["id"]]

# ---------- 潜力新星：1~3 家店的线下小店，现象级候选 ----------
# 五维因子：选址 SITE / 客群 CROWD / 产品定位 PRODUCT / 社交属性 SOCIAL / 热点属性 VIRAL
SHOP_DDL = """
CREATE TABLE IF NOT EXISTS local_shop (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  category TEXT NOT NULL,
  stores INTEGER, age_months INTEGER,
  dim_site INTEGER, dim_crowd INTEGER, dim_product INTEGER, dim_social INTEGER, dim_viral INTEGER,
  opt_site TEXT, opt_crowd TEXT, opt_product TEXT, opt_social TEXT, opt_viral TEXT,
  need_supply INTEGER, need_social INTEGER, need_strategy INTEGER,
  boost TEXT,
  coop_model TEXT, coop_note TEXT, contact TEXT,
  source_type TEXT DEFAULT 'demo_seed'
);
"""

SHOPS = [
    dict(id="SH-01", name="Sate Kambing H. Diding", city="雅加达", category="沙嗲烧烤", stores=1, age_months=36,
         dim_site=58, dim_crowd=72, dim_product=84, dim_social=55, dim_viral=61,
         opt_site="点位在老居民区深处，建议嫁接商场食阁或夜市档口做第二触点",
         opt_crowd="客群以周边中年男性为主，需补年轻客群入口（学生价套餐）",
         opt_product="沙嗲酱是记忆点，应做成零售罐装 SKU 进便利店测试",
         opt_social="无被拍动线设计，加开放式炭烤台让烟与火成为画面",
         opt_viral="本地论坛有口碑但零短视频运营，TikTok 账号尚未建立",
         need_supply=74, need_social=78, need_strategy=66,
         boost=["社媒内容系统", "零售化供应链", "选址引擎"],
         coop_model="深度孵化", coop_note="产品 84 分是全榜最高之一，只差包装与传播——典型的'产品好不会红'案例。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-02", name="Seblak Teh Ninih", city="万隆", category="西爪哇辣烫", stores=2, age_months=20,
         dim_site=66, dim_crowd=81, dim_product=77, dim_social=72, dim_viral=76,
         opt_site="两店都在大学半径内，第三店应沿轻轨站复制",
         opt_crowd="学生客群极稳，需设计毕业后的家庭场景产品线",
         opt_product="辣度分级+隐藏配料已是玩法雏形，应机制化写成收集系统",
         opt_social="学生自发性 UGC 多，缺官方话题引导与 KOC 分发",
         opt_viral="#seblak 话题天然高流量，本店视频被搬运 300+ 次但未挂定位",
         need_supply=70, need_social=58, need_strategy=62,
         boost=["社媒矩阵代运营", "加盟体系输出"],
         coop_model="品牌联营 + 系统加持", coop_note="已具备两店模型与自发流量，最适合'联营+体系输出'快速铺到 10 店。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-03", name="Ayam Gepuk Bu Yati", city="日惹", category="椰浆炸鸡", stores=3, age_months=30,
         dim_site=71, dim_crowd=75, dim_product=82, dim_social=61, dim_viral=68,
         opt_site="三店均为社区街边店，旗舰体验店缺失，品牌无'打卡锚点'",
         opt_crowd="家庭客群扎实，Z 世代触达不足",
         opt_product="椰浆腌制工艺有壁垒，应开发即食包装进 KA 渠道",
         opt_social="出餐快但无'被拍性'设计，加木槌敲鸡仪式化动作",
         opt_viral="本地美食号多次自发探店，未形成统一话题标签",
         need_supply=76, need_social=64, need_strategy=55,
         boost=["零售化供应链", "社媒内容系统", "爆品机制设计"],
         coop_model="供应链共建 + 爆品共创", coop_note="工艺壁垒型选手，把腌制工艺变成零售 SKU 是最快的第二曲线。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-04", name="Pisang Goreng Madu Bu Nanik", city="泗水", category="蜂蜜炸香蕉", stores=1, age_months=14,
         dim_site=52, dim_crowd=64, dim_product=79, dim_social=74, dim_viral=82,
         opt_site="流动档口无固定点位，急需固定锚点门店承接流量",
         opt_crowd="路人客群随机性强，需用预购群把过客变熟客",
         opt_product="蜂蜜瀑布浇汁是传播画面，应固定为仪式化出品 SOP",
         opt_social="浇汁慢镜头已被搬运 500+ 万次，官方账号仅 800 粉",
         opt_viral="单条搬运视频播放破 800 万，'泗水蜂蜜香蕉'已成搜索词",
         need_supply=68, need_social=82, need_strategy=71,
         boost=["社媒矩阵代运营", "选址引擎", "快闪店模型"],
         coop_model="深孵 + 快闪验证", coop_note="全网最火的'无主流量'：流量在别人的账号里。先把账号和锚点门店做出来，转化现成热度。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-05", name="Nasi Goreng Kambing Barito", city="雅加达", category="羊肉炒饭", stores=1, age_months=120,
         dim_site=78, dim_crowd=80, dim_product=80, dim_social=49, dim_viral=57,
         opt_site="Barito 夜市锚点极佳，但排队动线无拍照区",
         opt_crowd="夜宵客群全国闻名，游客占比高，缺游客伴手礼转化",
         opt_product="秘制羊肉炒饭料应做成家庭装酱料零售",
         opt_social="凌晨大排长龙是奇观却无人运营，加'排队认证'打卡机制",
         opt_viral="美食纪录片常客，但短视频时代声量断层",
         need_supply=72, need_social=75, need_strategy=63,
         boost=["社媒内容系统", "零售化供应链"],
         coop_model="品牌联营 + 系统加持", coop_note="老字号现象级点位，年轻化与零售化是最大的增值空间。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-06", name="Kwetiau Akang", city="雅加达", category="炒粿条", stores=3, age_months=42,
         dim_site=68, dim_crowd=77, dim_product=73, dim_social=66, dim_viral=70,
         opt_site="三店覆盖雅加达西区，东区与卫星城空白",
         opt_crowd="华人与本地客群双覆盖，可做'两代人同桌'叙事",
         opt_product="锅气是核心卖点但无法标准化，需锁定 3 个黄金 SKU",
         opt_social="明档现炒有画面，缺统一视觉锤与话题标签",
         opt_viral="#kwetiauakang 话题 6000 万播放，官方未下场",
         need_supply=66, need_social=60, need_strategy=58,
         boost=["加盟体系输出", "社媒矩阵代运营"],
         coop_model="加盟体系输出 + 供应链托管", coop_note="三店已验证，连锁化模板清晰——输出 SOP+供应链即可加速。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-07", name="Soto Lamongan Cak Har", city="泗水", category="爪哇鸡汤", stores=2, age_months=26,
         dim_site=61, dim_crowd=70, dim_product=76, dim_social=58, dim_viral=63,
         opt_site="两店均在传统市场旁，卫生视觉升级是第一步",
         opt_crowd="早餐刚需客群稳，午晚场景完全空白",
         opt_product="Koya 虾松粉是灵魂配料，应独立包装成零售 SKU",
         opt_social="汤头翻滚画面好，但店内灯光昏暗无法拍摄",
         opt_viral="本地美食博主零星推荐，未形成声量",
         need_supply=80, need_social=70, need_strategy=66,
         boost=["供应链网络加持", "门店轻改造方案", "社媒内容系统"],
         coop_model="深度孵化", coop_note="供应链分散采购痛点最典型——集采+标准化能直接降 15% 成本。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-08", name="Bubur Ayam Barito", city="雅加达", category="鸡肉粥", stores=1, age_months=96,
         dim_site=75, dim_crowd=78, dim_product=71, dim_social=52, dim_viral=59,
         opt_site="Barito 街区双锚点（与其余名店共生），可做'一条街吃透'动线",
         opt_crowd="早餐全龄段客群，缺办公场景外送订阅",
         opt_product="粥底可标准化中央厨房配送，门店只做浇头",
         opt_social="深夜收摊前的'最后一碗'是天然情绪点，未内容化",
         opt_viral="老牌网红余温尚在，近年声量下滑需再激活",
         need_supply=77, need_social=72, need_strategy=69,
         boost=["中央厨房供应链", "社媒内容系统"],
         coop_model="供应链共建 + 品牌焕新", coop_note="中央厨房化改造后单店人效可提 40%，是供应链切入的好标的。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-09", name="Pempek 61", city="雅加达", category="巨港鱼糕", stores=2, age_months=54,
         dim_site=64, dim_crowd=69, dim_product=78, dim_social=63, dim_viral=66,
         opt_site="两店在社区商业街，缺高流量展示面",
         opt_crowd="巨港移民乡愁客群+本地尝鲜客群并存",
         opt_product="cuko 酸甜辣酱是差异化武器，应做蘸酱零售",
         opt_social="切鱼糕的弹刀工有视觉点，未设计拍摄位",
         opt_viral="TikTok 上巨港美食话题升温，本店未承接",
         need_supply=73, need_social=66, need_strategy=61,
         boost=["零售化供应链", "社媒内容系统", "选址引擎"],
         coop_model="深孵 + 快闪验证", coop_note="蘸酱零售化+商场快闪是低成本验证路径，适合投早。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-10", name="Rujak Cingur Delta", city="泗水", category="东爪哇沙拉", stores=1, age_months=66,
         dim_site=59, dim_crowd=65, dim_product=74, dim_social=69, dim_viral=73,
         opt_site="Delta 大桥下地标点位，游客知道但找不到——导视缺失",
         opt_crowd="游客+本地家庭混合，缺年轻人轻食版本",
         opt_product="重口味是门槛也是记忆点，可出'轻版 cingur'双产品线",
         opt_social="'敢不敢吃 cingur'挑战天然适合短视频",
         opt_viral="外国游客试吃反应视频多次破百万，官方零运营",
         need_supply=64, need_social=77, need_strategy=68,
         boost=["社媒矩阵代运营", "游客动线策划", "双产品线设计"],
         coop_model="品牌联营 + 系统加持", coop_note="挑战型内容基因极强，做一次官方挑战赛即可激活存量话题。", contact="ptxdirectionpublicrelations@gmail.com"),
    # ── 离岛样本（人口×城镇集中度修正逻辑的真实跑批）──
    dict(id="SH-11", name="Sate Lilit Kedaton", city="登巴萨", category="巴厘鱼肉沙嗲", stores=2, age_months=22,
         dim_site=68, dim_crowd=74, dim_product=81, dim_social=70, dim_viral=77,
         opt_site="两店在 Kedaton 居民区，游客区（Kuta）零覆盖——游客找不到",
         opt_crowd="本地家庭客群稳，游客只认 babi guling 不认 lilit",
         opt_product="鱼肉沙嗲是 Bali 独有品类，应做真空即食装进游客伴手礼店",
         opt_social="芭蕉叶捆串是天然画面，未设计拍摄位",
         opt_viral="#satelilit 话题在欧美游客间升温，官方账号未承接",
         need_supply=72, need_social=66, need_strategy=70,
         boost=["游客动线策划", "零售化供应链", "社媒内容系统"],
         coop_model="品牌联营 + 系统加持", coop_note="巴厘岛游客流量全岛最高（集中度 62%），把游客区触达补上即放量。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-12", name="Babi Guling Pak Malen", city="登巴萨", category="巴厘烤乳猪", stores=1, age_months=48,
         dim_site=80, dim_crowd=76, dim_product=83, dim_social=62, dim_viral=71,
         opt_site="单店在 Denpasar 西，已排队但无取号系统，翻台受限",
         opt_crowd="游客专程打卡+本地宴席双客群，缺外带窗口",
         opt_product="脆皮工艺是壁垒，应出'迷你 guling 盒'进便利店",
         opt_social="整猪现切是震撼画面，但切台背对客流无法拍摄",
         opt_viral="游记平台长期霸榜，短视频声量被模仿者超越",
         need_supply=68, need_social=71, need_strategy=64,
         boost=["加盟体系输出", "社媒矩阵代运营", "零售化供应链"],
         coop_model="加盟体系输出 + 供应链托管", coop_note="单品心智极强，二店三店模板清晰——输出 SOP 即可在游客带复制。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-13", name="Amplang Barito Kaltim", city="巴厘巴板", category="东加里曼丹炸鱼饼", stores=1, age_months=30,
         dim_site=55, dim_crowd=66, dim_product=77, dim_social=58, dim_viral=64,
         opt_site="社区深处无名门面，能源城白领找不到",
         opt_crowd="本地家庭+油田外派客群，消费力全岛前列",
         opt_product="amplang 常温长保天然适合零售化，是'离岛伴手礼'首选品类",
         opt_social="现炸过程有画面，门店无展示动线",
         opt_viral="#amplangbalikpapan 本地话题稳定，未出圈",
         need_supply=78, need_social=62, need_strategy=68,
         boost=["零售化供应链", "选址引擎", "社媒内容系统"],
         coop_model="深孵 + 零售化首发", coop_note="集中度 70% 的紧凑城市+高消费力，零售化 SKU 进超市是最短路径。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-14", name="Nasi Kuning Bu Rina", city="巴厘巴板", category=" banjar 黄姜饭", stores=2, age_months=36,
         dim_site=62, dim_crowd=71, dim_product=75, dim_social=55, dim_viral=60,
         opt_site="两店在巴里奥老市场旁，早市客流强、午晚空白",
         opt_crowd="Banjar 族群乡愁客群+本地上班族，早餐刚需极稳",
         opt_product="黄姜饭可中央厨房标准化，配炸鸡腿锁定 3 个黄金 SKU",
         opt_social="堆头式出餐有烟火气，灯光与餐具拖累了画面",
         opt_viral="本地美食号偶尔推荐，零官方运营",
         need_supply=81, need_social=68, need_strategy=62,
         boost=["中央厨房供应链", "门店轻改造方案", "社媒内容系统"],
         coop_model="供应链共建 + 品牌焕新", coop_note="供应链集采痛点典型（集中度高低价食材外运），中央厨房化直接降本。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-15", name="Cakalang Fufu Rumah Manado", city="马那多", category="北苏烟熏鲣鱼", stores=1, age_months=54,
         dim_site=58, dim_crowd=63, dim_product=80, dim_social=52, dim_viral=66,
         opt_site="渔村深处家庭作坊，游客与年轻本地人都触达不到",
         opt_crowd="本地家庭刚需+海外 Manado 社群乡愁双客群",
         opt_product="烟熏鲣鱼是 Manado 头号伴手礼，真空装已验证但无品牌",
         opt_social="竹架烟熏的村落画面极具异域感，完全未被内容化",
         opt_viral="#manadofood 在印尼侨民圈稳定热度，官方缺席",
         need_supply=76, need_social=70, need_strategy=72,
         boost=["零售化供应链", "社媒矩阵代运营", "游客动线策划"],
         coop_model="深孵 + 零售化首发", coop_note="人口仅 46 万但集中度 55%，单品伴手礼逻辑跑通即可覆盖全岛——典型的离岛单品模型。", contact="ptxdirectionpublicrelations@gmail.com"),
    dict(id="SH-16", name="Tinutuan Pagi Siang Malam", city="马那多", category="北苏蔬菜粥", stores=2, age_months=28,
         dim_site=64, dim_crowd=69, dim_product=72, dim_social=61, dim_viral=68,
         opt_site="两店分踞早晚市口，午餐场景无人承接",
         opt_crowd="全龄段早餐客群，学生与教堂社群是隐形增量",
         opt_product="'无米蔬菜粥'是差异点，可出杯装即食进加油站",
         opt_social="五彩斑斓的粥体是自然流量画面，店内无法拍",
         opt_viral="健康轻食话题契合，本地 KOC 自发内容已起量",
         need_supply=69, need_social=59, need_strategy=65,
         boost=["门店轻改造方案", "零售化供应链", "社媒内容系统"],
         coop_model="品牌联营 + 系统加持", coop_note="健康叙事+现成 KOC 声量，改造拍摄位后即可承接话题。", contact="ptxdirectionpublicrelations@gmail.com"),
]

# 我们的三张牌（合作加持体系）
BOOST_SYSTEM = {
    "supply": {"name": "供应链网络加持", "en": "SUPPLY CHAIN",
               "desc": "集采 / 中央厨房 / 冷链仓配 —— 把分散采购成本打下来，把品控标准立起来。"},
    "social": {"name": "社交媒体系统加持", "en": "SOCIAL SYSTEM",
               "desc": "内容矩阵 + KOC 分发 + 投放中台 —— 把偶发爆火变成可运营的增长系统。"},
    "strategy": {"name": "策略打法输出", "en": "PLAYBOOK",
                 "desc": "选址引擎 + 爆品机制 + 加盟体系 —— 把单店模型沉淀成可复制的操作手册。"},
}


def migrate_localradar(conn: sqlite3.Connection) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(local_brand)")]
    if cols and "value_score" not in cols and "need_supply" not in cols and len(cols) != 27:
        conn.execute("DROP TABLE local_brand")
    conn.executescript(DDL)
    conn.executescript(SHOP_DDL)


def seed_localradar(conn: sqlite3.Connection) -> None:
    migrate_localradar(conn)
    for b in BRANDS:
        conn.execute(
            "INSERT OR REPLACE INTO local_brand VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (b["id"], b["name"], b["name_cn"], b["city"], b["category"], b["stage"],
             b["ig"], b["tiktok"], b["x"],
             b["followers_wan"], b["views_wan"], b["likes_wan"], b["shares_wan"],
             b["er"], b["growth_30d"], b["heat"],
             b["why_hot"], b["viral_format"], json.dumps(b["heat_signals"], ensure_ascii=False),
             b["need_supply"], b["need_social"], b["need_strategy"],
             json.dumps(b["boost"], ensure_ascii=False),
             b["coop_model"], b["coop_note"], b["contact"], "demo_seed"))
    for s in SHOPS:
        conn.execute(
            "INSERT OR REPLACE INTO local_shop VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (s["id"], s["name"], s["city"], s["category"], s["stores"], s["age_months"],
             s["dim_site"], s["dim_crowd"], s["dim_product"], s["dim_social"], s["dim_viral"],
             s["opt_site"], s["opt_crowd"], s["opt_product"], s["opt_social"], s["opt_viral"],
             s["need_supply"], s["need_social"], s["need_strategy"],
             json.dumps(s["boost"], ensure_ascii=False),
             s["coop_model"], s["coop_note"], s["contact"], "demo_seed"))


def value_score(b: dict) -> float | None:
    """合作价值 = 热度×0.4 + 缺口均值×0.4 + 增速折算×0.2（0-100）。缺任一输入则不估算。"""
    if any(b.get(k) is None for k in ("heat", "need_supply", "need_social", "need_strategy", "growth_30d")):
        return None
    need_avg = (b["need_supply"] + b["need_social"] + b["need_strategy"]) / 3
    growth = min(max(b["growth_30d"], 0), 100)
    return round(b["heat"] * 0.4 + need_avg * 0.4 + growth * 0.2, 1)


def potential_score(s: dict) -> float:
    """现象级潜力 = 热点属性×0.30 + 社交×0.20 + 产品×0.20 + 选址×0.15 + 客群×0.15（0-100）"""
    return round(s["dim_viral"] * 0.30 + s["dim_social"] * 0.20 + s["dim_product"] * 0.20
                 + s["dim_site"] * 0.15 + s["dim_crowd"] * 0.15, 1)


def _shop_from_row(r: dict) -> dict:
    s = dict(r)
    s["boost"] = json.loads(s["boost"] or "[]")
    s["dims"] = {"site": s.pop("dim_site"), "crowd": s.pop("dim_crowd"),
                 "product": s.pop("dim_product"), "social": s.pop("dim_social"),
                 "viral": s.pop("dim_viral")}
    s["opt"] = {"site": s.pop("opt_site"), "crowd": s.pop("opt_crowd"),
                "product": s.pop("opt_product"), "social": s.pop("opt_social"),
                "viral": s.pop("opt_viral")}
    d = s["dims"]
    s["potential_score"] = round(d["viral"] * 0.30 + d["social"] * 0.20 + d["product"] * 0.20
                                 + d["site"] * 0.15 + d["crowd"] * 0.15, 1)
    s["photo"] = _photo_of(s["id"])
    return s


def _photo_of(eid: str) -> str | None:
    p = Path(__file__).resolve().parents[3] / "web/assets/radar" / f"{eid}.jpg"
    return asset(f"assets/radar/{eid}.jpg") if p.exists() else None


def build_localradar(db_path: str | Path, x_snapshot: str | Path | None = "auto") -> dict:
    """x_snapshot: "auto"=取 data/radar 下最新快照；None=纯演示；或指定路径。"""
    from nbo.localradar import xsnapshot as xs
    snap_path = xs.latest_snapshot_path() if x_snapshot == "auto" else x_snapshot
    snap = xs.load_snapshot(snap_path) if snap_path else None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_localradar(conn)
        rows = [dict(r) for r in conn.execute("SELECT * FROM local_brand")]
        shop_rows = [dict(r) for r in conn.execute("SELECT * FROM local_shop")]
        expected = {b["id"] for b in BRANDS}
        if not rows or not shop_rows or {r["id"] for r in rows} != expected:
            seed_localradar(conn)
            conn.commit()
            rows = [dict(r) for r in conn.execute("SELECT * FROM local_brand")]
            shop_rows = [dict(r) for r in conn.execute("SELECT * FROM local_shop")]
    finally:
        conn.close()
    seed_by_id = {b["id"]: b for b in BRANDS}
    brands = []
    for r in rows:
        b = dict(r)
        seed = seed_by_id.get(b["id"], {})
        for key in ("origin_label", "website", "metrics_pending"):
            if key in seed:
                b[key] = seed[key]
        b["heat_signals"] = json.loads(b["heat_signals"] or "[]")
        b["boost"] = json.loads(b["boost"] or "[]")
        if snap:
            b = xs.apply_snapshot(b, snap)
        b["value_score"] = value_score(b)
        b["photo"] = _photo_of(b["id"])
        brands.append(b)
    brands.sort(key=lambda b: (b.get("heat") is not None, b.get("heat") if b.get("heat") is not None else -1), reverse=True)
    shops = [_shop_from_row(r) for r in shop_rows]
    shops.sort(key=lambda s: s["potential_score"], reverse=True)
    cities = sorted({b["city"] for b in brands} | {s["city"] for s in shops})
    n_real = sum(1 for b in brands if b.get("source_type") == "mixed")
    n_pending = sum(1 for b in brands if b.get("source_type") == "pending_x")
    if snap:
        source_note = (f"X 公开数据实抓（{snap.get('fetched_at')}，{n_real}/{len(brands)} 个品牌）："
                       "热度=近7天X提及量对数分、X 官方号粉丝/发帖为实抓；"
                       "IG/TikTok、粉丝(万)/播放/赞/转发/互动率/30天增速/缺口分及潜力小店均为演示估算")
        if n_pending:
            source_note += (f"。另有 {n_pending} 个品牌已列入追踪，X 粉丝与近 7 天提及待下次刷新"
                            "（不估算这些数字）")
    else:
        source_note = "演示种子数据 · 字段对齐真实 IG/TikTok/X 公开数据抓取口径（粉丝/播放/互动/增速）"
    return {
        "generated_at": datetime.now(WIB).strftime("%Y-%m-%d %H:%M"),
        "demo": not snap,
        "data_mode": "x_public+demo_estimate" if snap else "demo_seed",
        "x_snapshot": ({"file": str(Path(snap_path).name), "fetched_at": snap.get("fetched_at"),
                        "x_calls_used": snap.get("x_calls_used"), "brands_with_x": n_real,
                        "brands_pending_x": n_pending,
                        "heat_formula": "heat = 100*log10(1+近7天X提及数)/log10(1+%d)，上限100" % xs.HEAT_REF_MENTIONS_7D}
                       if snap else None),
        "window": "近3个月",
        "source_note": source_note,
        "cities": cities,
        "brands": brands,
        "shops": shops,
        "boost_system": BOOST_SYSTEM,
    }


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
