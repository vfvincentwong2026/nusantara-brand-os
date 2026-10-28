"""概念落地评分引擎：把热点零食代入「传播单元→寄生行为→机制→被拍性→活人感+大单品」
五步链路 + 机制型设计系统 + 集装箱整装 + 供应链本地匹配，归因出落地因子并评分，
为首选概念生成可执行落地方案。

评分为规则引擎（非 ML）：因子基值按品类标定，再用零食已有字段（热度/复制性/改造/合规）
做透明修正，全部规则可审计、可测试。当前数据为演示种子（source_type 继承 trend）。
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# ── 落地因子定义（权重合计 100）────────────────────────────
FACTORS = [
    dict(id="f1", name="传播单元强度", weight=15,
         desc="被消费时可传播的画面/话题/结果有多强", source="trend.heat + why_hot"),
    dict(id="f2", name="机制可运行性", weight=15,
         desc="挑战/收集/隐藏款/联名关卡能否重复运行、用户是否零门槛参与", source="品类基值 × 复制性"),
    dict(id="f3", name="被拍性与被理解性", weight=15,
         desc="货架三秒识别 + 开箱脚本 + 无需思考的拍摄角度（SHUDAO 硬标准）", source="品类基值 + 病毒玩法"),
    dict(id="f4", name="供应链本地匹配", weight=20,
         desc="原料/代工在印尼的可得性与成本结构（权重最高：落地的硬约束）", source="adaptation + 复制性"),
    dict(id="f5", name="合规就绪度", weight=10,
         desc="BPOM/Halal 路径长短与宣称风险", source="compliance_note 风险词"),
    dict(id="f6", name="集装箱整装适配", weight=10,
         desc="常温长保 / 小空间机制剧场 / warung 渠道兼容性", source="品类 + 渠道"),
    dict(id="f7", name="复购承接（大单品潜力）", weight=15,
         desc="话题款拉新之后有没有 100 分的大单品接住利润", source="品类基值"),
]

# 品类基值表：f2 机制 / f3 被拍性 / f7 复购 / f4 供应链起点 / f6 集装箱
CATEGORY_BASE = {
    "烘焙饼干":   dict(f2=78, f3=82, f7=72, f4=80, f6=82),
    "冷冻甜品":   dict(f2=62, f3=85, f7=70, f4=48, f6=35),
    "现制烘焙":   dict(f2=58, f3=90, f7=55, f4=60, f6=66),
    "传统油炸糕点": dict(f2=72, f3=62, f7=78, f4=85, f6=80),
    "现制甜品":   dict(f2=64, f3=92, f7=58, f4=58, f6=64),
    "膨化零食":   dict(f2=80, f3=78, f7=75, f4=82, f6=85),
    "海味零食":   dict(f2=74, f3=72, f7=82, f4=88, f6=86),
    "海味熟食":   dict(f2=70, f3=68, f7=80, f4=86, f6=78),
    "冲调饮品":   dict(f2=68, f3=70, f7=84, f4=80, f6=82),
    "方便熟食":   dict(f2=66, f3=64, f7=82, f4=60, f6=70),
    "糖果":      dict(f2=82, f3=80, f7=70, f4=78, f6=80),
    "豆制品零食": dict(f2=76, f3=84, f7=60, f4=55, f6=74),
    "素食零食":   dict(f2=74, f3=76, f7=76, f4=58, f6=82),
    "炸制零食":   dict(f2=76, f3=86, f7=74, f4=84, f6=80),
}

REP_BONUS = {"高": 8, "中": 0, "低": -10}
# 合规风险词 → 扣分（命中越长周期/越难的词扣越多）
COMPLIANCE_RISK = [("进口关税高", -18), ("需进口", -14), ("审批", -12), ("发酵工艺", -12),
                   ("限量严格", -10), ("检测支撑", -8), ("受控", -6), ("严格", -6)]
# 供应链加分词（本地匹配证据）
SUPPLY_EVIDENCE = [("本地采购", 10), ("本地代工", 10), ("本地有优势", 10), ("原料本地", 10),
                   ("本地原料", 10), ("本地", 6), ("成本可控", 6), ("产线本地成熟", 8), ("印尼是", 6)]

GRADES = [(85, "S", "立即立项"), (75, "A", "优先复制"), (65, "B", "改造后试销"), (0, "C", "仅作话题款")]


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, round(v, 1)))


def _score_snack(s: dict) -> dict:
    base = CATEGORY_BASE.get(s["category"], dict(f2=65, f3=70, f7=65, f4=65, f6=65))
    rep = REP_BONUS.get(s["replicability"], 0)
    adapt = s["adaptation"]
    comp = s["compliance_note"]

    f1 = _clamp(s["heat"] * 0.9 + (10 if "ASMR" in s["why_hot"] or "镜头" in s["why_hot"] else 4))
    f2 = _clamp(base["f2"] + rep + (5 if "联名" in s["viral_format"] or "挑战" in s["viral_format"] else 0))
    f3 = _clamp(base["f3"] + rep + (6 if "切面" in s["why_hot"] or "截面" in s["why_hot"] else 2))
    f4 = _clamp(base["f4"] + rep + sum(b for k, b in SUPPLY_EVIDENCE if k in adapt))
    f5 = _clamp(85 + sum(p for k, p in COMPLIANCE_RISK if k in comp))
    f6 = _clamp(base["f6"] + (8 if "warung" in adapt else 0) + (6 if "收银" in adapt else 0))
    f7 = _clamp(base["f7"] + (8 if "复购" in s["repl_reason"] else 0)
                - (12 if s["replicability"] == "低" and "话题" in s["repl_reason"] else 0))

    scores = {"f1": f1, "f2": f2, "f3": f3, "f4": f4, "f5": f5, "f6": f6, "f7": f7}
    total = _clamp(sum(scores[f["id"]] * f["weight"] for f in FACTORS) / 100.0)
    grade, action = next((g, a) for th, g, a in GRADES if total >= th)
    return {"id": s["id"], "name": s["name"], "region": s["region"], "category": s["category"],
            "heat": s["heat"], "scores": scores, "total": total, "grade": grade,
            "grade_action": action, "replicability": s["replicability"]}


def _build_plan(top: dict, s: dict) -> dict:
    """为首选概念生成执行方案：五步链路 × 设计交付 × 集装箱整装 × 供应链。"""
    fit = round(s["indo_fit"])
    tier = ("双40尺旗舰样板（56㎡）", "机制剧场全配置：挑战台+等级墙+打卡装置") if top["total"] >= 78 else \
           ("单40尺标准店（30㎡）", "机制发生区+收银转化区，打卡点 1 处") if top["total"] >= 68 else \
           ("20尺轻量店中店", "货架专区+机制标签系统，低成本验证")
    return {
        "concept": {"name": s["name"], "region": s["region"], "category": s["category"],
                    "total": top["total"], "grade": top["grade"], "indo_fit": fit},
        "container": {"tier": tier[0], "space_plan": tier[1],
                      "link": "/case/",
                      "note": "集装箱整装四档体系直接复用；快闪模块可拆装巡回"},
        "steps": [
            dict(no=1, name="定义传播单元",
                 action=f"锁定「{s['why_hot'].split('；')[0]}」为唯一传播画面，所有物料围绕这一个画面服务。",
                 design="包装主视觉 + 开箱背景板", supply="—"),
            dict(no=2, name="选择寄生行为",
                 action="寄生高频行为：办公摸鱼 / 追剧熬夜 / 课间偷吃，产品作为道具嵌入而非创造场景。",
                 design="场景化 UGC 模板（办公桌/宿舍/通勤）", supply="小规格独立包装适配场景"),
            dict(no=3, name="做成机制",
                 action=f"把机制写进产品结构：{s['viral_format']}；等级/收集/隐藏款三选一并系列化。",
                 design="等级徽章 + 收集编号 + 挑战卡（可延展超级符号）", supply="包装产线需支持变体印刷"),
            dict(no=4, name="前置被拍性与被理解性",
                 action="货架三秒识别测试 + 开箱脚本测试 + 拍摄测试 + 系列延展测试，作为评审硬标准。",
                 design="货架层/开箱层/社交层三层包装打样", supply="材质工艺与成本测试同步"),
            dict(no=5, name="活人感冷启动 + 大单品承接",
                 action=f"话题款负责拉新曝光；复购由大单品承接——{s['adaptation']}。",
                 design="内容模板 + 门店打卡模板", supply=s["adaptation"]),
        ],
        "supply_chain": {
            "local_match": s["fit_reasons"],
            "adaptation": s["adaptation"],
            "compliance": s["compliance_note"],
            "compliance_lead": "BPOM + Halal 认证周期约 3-6 个月，与产品开发同步启动",
        },
        "deliverables": [
            "品牌识别系统 VIS + 核心超级符号", "货架层/开箱层/社交层三层包装",
            "开箱脚本与机制道具（挑战卡/收集卡）", "平面动线图 + 机制装置详图",
            "陈列道具清单 + 施工落地成本估算", "快闪模块化拆装方案",
        ],
    }


def build_launch(db_path: str | Path) -> dict:
    from nbo.trend import build_trend
    t = build_trend(db_path)
    if "error" in t:
        return {"demo": True, "error": t["error"]}
    scored = [_score_snack(s) for s in t["snacks"]]
    scored.sort(key=lambda x: -x["total"])
    top = scored[0]
    top_snack = next(s for s in t["snacks"] if s["id"] == top["id"])
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "demo": True,
            "window": t["window"], "factors": FACTORS, "ranked": scored,
            "plan": _build_plan(top, top_snack),
            "source_note": "评分由规则引擎从 trend 字段推导（品类基值 + 透明修正），可审计可测试。"}


def write_json(data: dict, out_path: str | Path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
