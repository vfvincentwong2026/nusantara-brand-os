"""加盟体系引擎：业态库（开店成本包 + 回本模型）× 特权加盟品牌库。

锚定：单店总投资 8–10 万 RMB（≈ Rp 176–220 juta，演示汇率 2,200，页面标注）。
回本模型由假设推导（日销 × 毛利率 − 月固定成本），可审计、可测试。
当前为演示种子（source_type=演示）。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

FX = 2200  # 1 RMB = 2200 IDR（演示口径）

FRANCHISE_DDL = """
CREATE TABLE IF NOT EXISTS franchise_format (
    id TEXT PRIMARY KEY, name TEXT, concept TEXT, store_sqm REAL,
    fee_rmb REAL, equip_rmb REAL, fitout_rmb REAL, goods_rmb REAL,
    deposit_rmb REAL, float_rmb REAL,
    daily_sales_idr REAL, gross_margin_pct REAL, monthly_fixed_idr REAL,
    staff INTEGER, supply_chain TEXT, key_risk TEXT, source_type TEXT
);
CREATE TABLE IF NOT EXISTS franchise_brand (
    id TEXT PRIMARY KEY, name TEXT, country TEXT, format_id TEXT,
    fee_idr REAL, invest_idr REAL, supply_req TEXT,
    training_level TEXT, stores_count INTEGER, fit_regions TEXT, source_type TEXT
);
"""

# 六业态：成本包（RMB 拆分，合计落在 8–10 万区间）+ 回本假设
FORMATS = [
    dict(id="snack", name="时尚零食集合店", concept="雷达 S 级概念直接上架：东亚爆款本地化 + 机制型包装",
         store_sqm=35, fee=2.0, equip=3.0, fitout=2.5, goods=1.2, deposit=0.5, float_=0.3,
         daily_sales=4_500_000, margin=0.32, monthly_fixed=30_000_000, staff=3,
         supply_chain=["休闲零食批发链", "进口爆品代购通道", "机制包装印刷厂"],
         key_risk="SKU 汰换快，滞销依赖雷达周更", source_type="演示"),
    dict(id="deli", name="熟食卤味档口", concept="即食档口 + 晚市加成，复购最强业态",
         store_sqm=12, fee=1.8, equip=3.2, fitout=2.0, goods=1.0, deposit=0.5, float_=0.5,
         daily_sales=3_500_000, margin=0.45, monthly_fixed=26_000_000, staff=2,
         supply_chain=["中央厨房半成品", "冷链日配", "Halal 认证肉源"],
         key_risk="食安与 Halal 合规一票否决", source_type="演示"),
    dict(id="coffee", name="精品咖啡档", concept="外带窗口 + 3 款招牌，人效最高的饮品业态",
         store_sqm=15, fee=2.5, equip=3.5, fitout=2.2, goods=0.6, deposit=0.7, float_=0.5,
         daily_sales=2_800_000, margin=0.62, monthly_fixed=30_000_000, staff=2,
         supply_chain=["咖啡豆烘焙坊", "乳制品日配", "纸杯包材厂"],
         key_risk="商圈依赖强，选址权重高于一切", source_type="演示"),
    dict(id="tea", name="手摇奶茶档", concept="加盟体系最成熟品类，培训与 SOP 现成度最高",
         store_sqm=10, fee=2.2, equip=3.0, fitout=2.0, goods=0.8, deposit=0.5, float_=0.3,
         daily_sales=2_600_000, margin=0.60, monthly_fixed=26_000_000, staff=2,
         supply_chain=["茶叶/果酱集采", "珍珠等配料周配", "封口设备维保"],
         key_risk="竞品密度高，需依赖品牌流量", source_type="演示"),
    dict(id="single", name="单品爆品店", concept="一支 S 级单品打穿：海苔卷/咸蛋黄鱼皮专柜模型",
         store_sqm=20, fee=1.5, equip=2.5, fitout=2.2, goods=1.2, deposit=0.4, float_=0.2,
         daily_sales=4_000_000, margin=0.40, monthly_fixed=26_000_000, staff=2,
         supply_chain=["单品深度代工", "变体包装快反", "快闪巡回团队"],
         key_risk="单品生命周期 6-9 个月，需机制续命", source_type="演示"),
    dict(id="popup", name="新品快闪柜", concept="最小单元验证：商场中岛柜 6㎡，测款后再放大",
         store_sqm=6, fee=1.5, equip=2.5, fitout=2.0, goods=1.0, deposit=1.0, float_=0.5,
         daily_sales=2_200_000, margin=0.50, monthly_fixed=18_000_000, staff=1,
         supply_chain=["共享供应链池", "柜体模块化租赁", "周更选品"],
         key_risk="点位租金谈判能力决定盈亏", source_type="演示"),
]

BRANDS = [
    dict(id="BR-01", name="SnackVault 零食仓", country="中国·杭州", format="snack",
         fee=45_000_000, invest=210_000_000, supply_req="总部集采 70% + 本地 30%",
         training="三级认证（店员→店长→督导）", stores=860, fit_regions="雅加达/泗水/万隆 商圈街铺", source_type="演示"),
    dict(id="BR-02", name="Mr. Ayam 卤味先生", country="印尼·本地", format="deli",
         fee=30_000_000, invest=180_000_000, supply_req="中央厨房日配 + 本地鸡源",
         training="7 天岗前 + 月度食安复训", stores=320, fit_regions="社区入口/夜市/办公区", source_type="演示"),
    dict(id="BR-03", name="Kopi Kilat 闪电咖啡", country="印尼·本地", format="coffee",
         fee=55_000_000, invest=215_000_000, supply_req="指定烘焙豆 + 设备租赁绑定",
         training="10 天咖啡师认证", stores=540, fit_regions="雅加达/日惹/棉兰 交通枢纽", source_type="演示"),
    dict(id="BR-04", name="Boba Sultan 波霸苏丹", country="台湾系", format="tea",
         fee=50_000_000, invest=195_000_000, supply_req="茶叶/配料总部直供",
         training="7 天调制认证 + 季度新品课", stores=1200, fit_regions="购物中心/大学区", source_type="演示"),
    dict(id="BR-05", name="Seawave 海苔卷专柜", country="泰国系", format="single",
         fee=33_000_000, invest=175_000_000, supply_req="海苔原料产地直采 + 本地代工",
         training="5 天 + 随柜督导", stores=95, fit_regions="旅游区/商场中岛", source_type="演示"),
    dict(id="BR-06", name="HypeBox 快闪盒", country="新加坡", format="popup",
         fee=33_000_000, invest=190_000_000, supply_req="共享供应链池按周结算",
         training="3 天快训 + 远程督导", stores=60, fit_regions="快闪点位轮换", source_type="演示"),
]


def migrate_franchise(conn: sqlite3.Connection) -> None:
    conn.executescript(FRANCHISE_DDL)


def seed_franchise(conn: sqlite3.Connection) -> None:
    migrate_franchise(conn)
    for f in FORMATS:
        conn.execute("INSERT OR REPLACE INTO franchise_format VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (f["id"], f["name"], f["concept"], f["store_sqm"], f["fee"], f["equip"],
                      f["fitout"], f["goods"], f["deposit"], f["float_"],
                      f["daily_sales"], f["margin"], f["monthly_fixed"], f["staff"],
                      json.dumps(f["supply_chain"], ensure_ascii=False), f["key_risk"], f["source_type"]))
    for b in BRANDS:
        conn.execute("INSERT OR REPLACE INTO franchise_brand VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (b["id"], b["name"], b["country"], b["format"], b["fee"], b["invest"],
                      b["supply_req"], b["training"], b["stores"], b["fit_regions"], b["source_type"]))


def _rmb(n: float) -> str:
    return f"{n:,.1f} 万"


def _idr(n: float) -> str:
    return f"Rp {n/1_000_000:,.1f} jt".replace(",", ".")


def build_franchise(db_path: str | Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migrate_franchise(conn)
        formats, brands = [], []
        for r in conn.execute("SELECT * FROM franchise_format"):
            f = dict(r)
            f["supply_chain"] = json.loads(f["supply_chain"])
            capex_rmb = f["fee_rmb"] + f["equip_rmb"] + f["fitout_rmb"] + f["goods_rmb"] + f["deposit_rmb"] + f["float_rmb"]
            capex_idr = capex_rmb * 10_000 * FX
            monthly_profit = f["daily_sales_idr"] * 30 * f["gross_margin_pct"] - f["monthly_fixed_idr"]
            payback = round(capex_idr / monthly_profit, 1) if monthly_profit > 0 else None
            formats.append({
                "id": f["id"], "name": f["name"], "concept": f["concept"], "store_sqm": f["store_sqm"],
                "capex_rmb": capex_rmb, "capex_idr": round(capex_idr),
                "capex_display": f"{_rmb(capex_rmb)} RMB ≈ {_idr(capex_idr)}",
                "package": {"加盟费": f["fee_rmb"], "设备": f["equip_rmb"], "装修装配": f["fitout_rmb"],
                            "首批货": f["goods_rmb"], "保证金": f["deposit_rmb"], "流动资金": f["float_rmb"]},
                "daily_sales_idr": f["daily_sales_idr"], "gross_margin_pct": f["gross_margin_pct"],
                "monthly_fixed_idr": f["monthly_fixed_idr"],
                "monthly_profit_idr": round(monthly_profit),
                "payback_months": payback, "staff": f["staff"],
                "supply_chain": f["supply_chain"], "key_risk": f["key_risk"],
                "source_type": f["source_type"]})
        for r in conn.execute("SELECT * FROM franchise_brand"):
            b = dict(r)
            b["fee_display"] = _idr(b["fee_idr"] / 1_000_000)
            b["invest_display"] = _idr(b["invest_idr"] / 1_000_000)
            formats_id = b["format_id"]
            b["format_name"] = next((x["name"] for x in formats if x["id"] == formats_id), formats_id)
            brands.append(b)
    finally:
        conn.close()
    if not formats:
        return {"demo": True, "error": "franchise_format 为空，请先 seed"}
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "demo": True,
            "fx": {"rmb_to_idr": FX, "note": "演示汇率，签约以实际牌价为准"},
            "budget_anchor": "单店总投资 8–10 万 RMB ≈ Rp 176–220 juta",
            "formats": formats, "brands": brands}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
