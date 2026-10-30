"""装配方案对比引擎：集装箱 / 轻钢快装 / 店中店三种整装形态的成本、工期、
证照与供应链要求对照，并按「8–10 万 RMB 单店成本包」预算线做适配判定。

当前为演示种子（source_type=演示）：金额为雅加达 2026 年行情区间估算，
汇率锚定 1 CNY ≈ 2200 IDR（演示口径，标注于 meta）。
"""
import json
from pathlib import Path

CNY_IDR = 2200  # 演示汇率锚

DIMS = ["主体与硬装", "设备", "首批货", "证照合规", "流动资金"]

# 成本单位：万 RMB（区间）
SCHEMES = [
    dict(id="ASM-C1", form="集装箱店 · 单箱体", area_sqm=18,
         cost={"主体与硬装": (4.5, 5.5), "设备": (1.5, 2.0), "首批货": (1.0, 1.5),
               "证照合规": (0.4, 0.6), "流动资金": (0.8, 1.2)},
         weeks=(2, 3), permit="中——PBG 需结构计算书（箱体有标准图纸可复用）",
         supply="低——设备模块化出厂，现场只接水电；供应链集中配送一次到位",
         pros=["总价落在 8–10 万包内，预算风险最低", "工期最短，两周可开业",
               "整店可搬迁，选址试错成本接近零", "视觉反差强，天然网红打卡属性"],
         cons=["18㎡ 只容 1 个机制剧场 + 窄 SKU 深货", "极端高温期箱体空调负荷高",
               "部分 mall 不接受箱体进场内"],
         fit="快速验证单店模型 / 社区节点 / 快闪先行",
         fit_budget=True),
    dict(id="ASM-C2", form="集装箱店 · 双箱体组合", area_sqm=36,
         cost={"主体与硬装": (6.5, 8.0), "设备": (2.2, 2.8), "首批货": (1.8, 2.4),
               "证照合规": (0.5, 0.7), "流动资金": (1.2, 1.6)},
         weeks=(3, 4), permit="中——同单箱体，组合节点多一套结构说明",
         supply="中——双箱体可分先后到货，供应链需排两次安装窗口",
         pros=["前店后仓：前场机制剧场 + 后场履约", "SKU 容量翻倍，可跑双品类",
               "保留搬迁属性"],
         cons=["总造价 12–15 万，超出 8–10 万包，适合验证后二期", "需更大场地租约"],
         fit="验证成功后的二期放大 / 双品类合营",
         fit_budget=False),
    dict(id="ASM-L1", form="轻钢快装平房", area_sqm=50,
         cost={"主体与硬装": (9.0, 11.0), "设备": (2.5, 3.2), "首批货": (2.2, 3.0),
               "证照合规": (0.6, 0.9), "流动资金": (1.5, 2.0)},
         weeks=(3, 5), permit="低——常规建筑 PBG/SLF 路径，施工队遍地都是",
         supply="中——现场湿作业多，供应链要配合工期分 3 批进场",
         pros=["空间利用率高，后仓 + 体验区一步到位", "不挑场地，社区/街边/mall 铺位通吃",
               "翻新改造成本低"],
         cons=["不可搬迁，选址错误即沉没成本", "总价 15–20 万，重资产，不符合快速验证原则"],
         fit="复购稳定后的标准社区店 / 区域样板",
         fit_budget=False),
    dict(id="ASM-S1", form="店中店 / 档口", area_sqm=20,
         cost={"主体与硬装": (2.8, 3.5), "设备": (1.8, 2.4), "首批货": (0.9, 1.4),
               "证照合规": (0.4, 0.6), "流动资金": (0.7, 1.1)},
         weeks=(1, 2), permit="低——借商场主体证照，只需经营范围增项",
         supply="低——设备即插即用，补货跟随商场物流窗口",
         pros=["造价 6–9 万，预算内且现金流启动最快", "自带商场客流，冷启动成本最低",
               "证照路径最短"],
         cons=["无独立门头，网红打卡属性弱", "租金扣点吃掉毛利，长期利润薄",
               "不可搬迁，且受商场排他条款约束"],
         fit="借成熟商圈测品 / 品牌进商场的第一块滩头阵地",
         fit_budget=True),
]


def _wan(x: float) -> dict:
    return {"wan_cny": round(x, 1), "idr_m": int(round(x * CNY_IDR / 100))}  # idr_m = 百万印尼盾


def build_assembly() -> dict:
    schemes = []
    for s in SCHEMES:
        lo = sum(v[0] for v in s["cost"].values())
        hi = sum(v[1] for v in s["cost"].values())
        breakdown = [{"dim": d, "lo": _wan(s["cost"][d][0]), "hi": _wan(s["cost"][d][1])}
                     for d in DIMS]
        mid = sum((v[0] + v[1]) / 2 for v in s["cost"].values())
        schemes.append(dict(
            id=s["id"], form=s["form"], area_sqm=s["area_sqm"],
            total_lo=_wan(lo), total_hi=_wan(hi), total_mid=_wan(mid),
            breakdown=breakdown, weeks=s["weeks"], permit=s["permit"],
            supply=s["supply"], pros=s["pros"], cons=s["cons"], fit=s["fit"],
            fit_budget=s["fit_budget"],
            images=[f"/assets/asm-{s['id'].lower().replace('asm-', '')}.jpg"]))
    rec = [s["id"] for s in schemes if s["fit_budget"] and s["area_sqm"] >= 15]
    return {
        "meta": {"cny_idr": CNY_IDR, "budget_wan": (8, 10),
                 "source_type": "演示",
                 "source_note": "金额为雅加达 2026 年行情区间估算（演示口径）；"
                                "落地前需当地承包商询价复核。"},
        "budget_fit_ids": rec,
        "schemes": schemes,
    }


def write_json(data: dict, out: str) -> None:
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
