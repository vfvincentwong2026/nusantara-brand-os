"""移动推车特许加盟引擎（体系 A 轻资产入口）：供应链 + 小推车模式。

商业模式：租车 + 配供应链 = 加盟。车身涂装即品牌植入（品牌资产），合作门槛
降至 3–5 万 RMB 甚至更低。车型三档：手推车 / 电动车改造熟食车（前部制作轨）
/ 饮品咖啡车。回本测算为规则模型（假设可审计），金额演示口径。
"""
import json
import sqlite3
from pathlib import Path

CNY_IDR = 2200  # 与 assembly 同一汇率锚

CARTS = [
    dict(id="CART-H1", name="手推车 · 供应链零售", form="手推餐车/零售车",
         images=["/assets/cart-gallery-%02d.jpg" % i for i in (1, 2, 3, 4, 5, 8, 9)],
         deposit=(0.8, 1.2), rent_mo=(0.08, 0.12), first_stock=(1.0, 1.5), cert=(0.2, 0.4),
         daily_sales_idr=(450, 900), gross_margin=0.48, payback=(3, 6),
         supply="全 SKU 由中央供应链直配：网红零食 + 熟食半成品，双周补货，换品零成本",
         permit="低——PIRT 食品生产编号 + 地方政府摊位许可（TPS/UMK 档位），一周可办",
         brand="车身三面涂装 + 统一餐服 + 收款码即会员入口；推车走到哪，品牌广告打到哪"),
    dict(id="CART-E1", name="电动车改造熟食车", form="电动三轮改造 · 前部制作轨",
         images=["/assets/cart-gallery-%02d.jpg" % i for i in (6, 10)],
         deposit=(1.5, 2.0), rent_mo=(0.15, 0.22), first_stock=(1.2, 1.8), cert=(0.3, 0.5),
         daily_sales_idr=(800, 1600), gross_margin=0.52, payback=(4, 8),
         supply="熟食半成品冷链日配 + 饮品原料 + 咖啡豆统采；制作轨设备模块化，坏件 48h 换新",
         permit="中——车体改装需符合印尼电动车上路规范（演示口径），PIRT + 摊位许可 + 卫生检查",
         brand="车体即旗舰店缩微版：涂装/灯箱/菜单板全总部输出，摊主零设计负担"),
    dict(id="CART-D1", name="饮品咖啡车", form="手推/电动吧台车",
         images=["/assets/cart-gallery-%02d.jpg" % i for i in (7, 11)],
         deposit=(1.2, 1.6), rent_mo=(0.12, 0.18), first_stock=(1.0, 1.5), cert=(0.3, 0.5),
         daily_sales_idr=(700, 1400), gross_margin=0.55, payback=(4, 8),
         supply="咖啡豆/茶叶统采 + 糖浆小料中央仓；配方与出品 SOP 由培训体系 L1 认证",
         permit="中——PIRT + 摊位许可；现制饮品需卫生等级 B 以上（演示口径）",
         brand="杯身贴纸 + 车身涂装双媒介；出杯即曝光，单杯成本里含品牌广告费"),
]


def _money(lo: float, hi: float) -> dict:
    return {"wan_cny": [round(lo, 2), round(hi, 2)],
            "idr_m": [int(round(lo * CNY_IDR / 100)), int(round(hi * CNY_IDR / 100))]}


def build_cart(db_path: str = "nbo.db") -> dict:
    carts = []
    for c in CARTS:
        start_lo = c["deposit"][0] + c["first_stock"][0] + c["cert"][0]
        start_hi = c["deposit"][1] + c["first_stock"][1] + c["cert"][1]
        carts.append(dict(
            id=c["id"], name=c["name"], form=c["form"],
            startup=_money(start_lo, start_hi),
            deposit=_money(*c["deposit"]), rent_mo=_money(*c["rent_mo"]),
            first_stock=_money(*c["first_stock"]), cert=_money(*c["cert"]),
            daily_sales_idr=list(c["daily_sales_idr"]),
            gross_margin=c["gross_margin"],
            payback_months=list(c["payback"]),
            supply=c["supply"], permit=c["permit"], brand=c["brand"], images=c["images"],
            source_type="演示"))
    return {"meta": {"cny_idr": CNY_IDR, "model": "租车+配供应链=加盟；车身涂装即品牌资产",
                     "source_type": "演示",
                     "source_note": "回本测算为规则模型：日销×毛利率×30 天对启动投入；"
                                    "金额为演示口径，落地前需当地询价。"},
            "carts": carts}


def write_json(data: dict, out: str) -> None:
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def migrate_cart(conn: sqlite3.Connection) -> None:
    """预留：推车加盟商台账（车辆、押金、补货节奏）——接 D1 前的本地占位。"""
    conn.execute("""CREATE TABLE IF NOT EXISTS cart_operator(
        id TEXT PRIMARY KEY, cart_id TEXT, city TEXT, started TEXT,
        deposit_idr INTEGER, active INTEGER DEFAULT 1)""")
