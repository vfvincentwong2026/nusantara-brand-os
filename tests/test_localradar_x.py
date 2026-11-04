"""本地品牌雷达 × X 公开数据快照测试：不编造数字、逐字段标注来源。"""
import json
from pathlib import Path

import pytest

from nbo.localradar import BRANDS, build_localradar
from nbo.localradar import xsnapshot as xs

SNAP = Path(__file__).resolve().parents[1] / "data/radar/x_snapshot_2026-11-04.json"


def test_snapshot_file_shape():
    snap = xs.load_snapshot(SNAP)
    assert snap["platform"] == "x" and snap["fetched_at"]
    assert set(snap["brands"]) == {b["id"] for b in BRANDS}
    for bid, e in snap["brands"].items():
        assert e["handle_status"] in xs.STATUS_CN
        assert isinstance(e["mentions_7d"]["total"], int)
        assert e["mentions_7d"]["total"] == sum(d["count"] for d in e["mentions_7d"]["daily"])
        if e["handle_status"] in xs.ACCOUNT_OK:
            assert e["resolved_handle"] and e["account"]["followers_count"] >= 0
        else:
            assert "account" not in e and e["resolved_handle"] is None


def test_build_with_snapshot_uses_real_values(tmp_path):
    d = build_localradar(tmp_path / "t.db", x_snapshot=SNAP)
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    assert d["demo"] is False and d["x_snapshot"]["brands_with_x"] == 10
    assert "实抓" in d["source_note"] and "演示估算" in d["source_note"]
    for b in d["brands"]:
        e = snap["brands"][b["id"]]
        assert b["source_type"] == "mixed"
        assert b["x_mentions_7d"] == e["mentions_7d"]["total"]
        assert b["heat"] == xs.heat_from_mentions(e["mentions_7d"]["total"])
        assert b["provenance"]["heat"] == "x_public"
        assert b["provenance"]["followers_wan"] == "demo_estimate"
        if e["handle_status"] in xs.ACCOUNT_OK:
            assert b["x_followers"] == e["account"]["followers_count"]
            assert b["x"] == e["resolved_handle"]
        else:  # 未核实账号：不采用其指标，并在展示 handle 上标注
            assert b["x_followers"] is None and b["provenance"]["x_followers"] == "missing"
            assert xs.STATUS_CN[e["handle_status"]] in b["x"]
        assert b["heat_signals"][0].startswith("【X 实抓")
        assert all(s.startswith(("【X 实抓", "【演示】")) for s in b["heat_signals"])
    heats = [b["heat"] for b in d["brands"]]
    assert heats == sorted(heats, reverse=True)


def test_build_without_snapshot_stays_demo(tmp_path):
    d = build_localradar(tmp_path / "t.db", x_snapshot=None)
    assert d["demo"] is True and d["x_snapshot"] is None
    assert all("x_followers" not in b for b in d["brands"])


def test_brand_missing_from_snapshot_is_demo():
    b = dict(BRANDS[0], heat_signals=["s"])
    out = xs.apply_snapshot(b, {"platform": "x", "brands": {}})
    assert out["source_type"] == "demo_seed" and out["heat"] == BRANDS[0]["heat"]


def test_heat_formula():
    assert xs.heat_from_mentions(0) == 0.0
    assert xs.heat_from_mentions(xs.HEAT_REF_MENTIONS_7D) == 100.0
    assert xs.heat_from_mentions(10 ** 6) == 100.0
    with pytest.raises(ValueError):
        xs.heat_from_mentions(-1)
