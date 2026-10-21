"""案例引擎 P1 测试：结构化实体 + 数据边界。"""
import json

from nbo.case import build_case_ops, seed_case
from nbo.db import seed

VALID_SRC = {"真实接入", "人工录入", "种子样本", "模拟计算", "待确认", "演示", "概念"}


def test_seed_and_build_case_ops(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    d = build_case_ops(db)
    assert d["demo"] is True
    assert d["store"]["id"] == "CS-D-001"
    assert d["store"]["net_length_m"] == 12.0 and d["store"]["net_width_m"] == 4.7
    # 每行都有来源标记
    assert d["store"]["source_type"] in VALID_SRC
    assert all(k["source_type"] in VALID_SRC for k in d["skus"])
    assert all(e["source_type"] in VALID_SRC for e in d["energy"])
    assert all(m["source_type"] in VALID_SRC for m in d["media"])
    # 订单 items 反序列化
    assert d["orders"][0]["items"][0]["sku"]
    assert d["flow_order"]["id"] == d["orders"][0]["id"]
    # 未核验合规 SKU 被禁止上架
    blocked = [k for k in d["skus"] if k["blocked"]]
    assert blocked and all("禁止" in k["compliance_note"] for k in blocked)
    # KPI 缺货数 = 可售库存 ≤0 的 SKU
    assert d["kpis"]["oos"]["v"] == "1 个"  # 仅试制酱料（stock 0）


def test_empty_db_returns_error(tmp_path):
    import sqlite3
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    from nbo.case import migrate_case
    migrate_case(conn)
    conn.close()
    d = build_case_ops(db)
    assert "error" in d


def test_write_case_ops(tmp_path):
    db = tmp_path / "t.db"
    seed(db)
    out = tmp_path / "case" / "case_ops.json"
    d = build_case_ops(db)
    from nbo.case import write_json
    write_json(d, out)
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == d


def test_build_case_map_and_dashboard(tmp_path):
    from nbo.case import build_case_dashboard, build_case_map
    db = tmp_path / "t.db"
    seed(db)
    m = build_case_map(db)
    assert m["name"] and m["lat"] and m["link"] == "/case/"
    assert "待复测" in m["net_size"]
    dd = build_case_dashboard(db)
    assert dd["store"]["demo"] is True
    assert dd["kpis"]["on_hand_total"] == sum(k["on_hand"] for k in dd["skus"])
    # 状态键与大屏前端一致；blocked SKU 归入缺货
    assert all(r["status"] in ("ok", "watch", "high", "out_of_stock") for r in dd["skus"])
    blocked = [r for r in dd["skus"] if r["blocked"]]
    assert blocked and all(r["status"] == "out_of_stock" for r in blocked)
