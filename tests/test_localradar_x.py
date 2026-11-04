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
    # 2026-11-04 快照只覆盖当时的 10 家。ID-11 / ID-12 等下次刷新再写入，不在这份历史文件里补数字。
    assert set(snap["brands"]) == {f"ID-{i:02d}" for i in range(1, 11)}
    assert {b["id"] for b in BRANDS} == {f"ID-{i:02d}" for i in range(1, 13)}
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
    assert d["x_snapshot"]["brands_pending_x"] == 2
    assert "实抓" in d["source_note"] and "演示估算" in d["source_note"]
    for b in d["brands"]:
        if b["id"] not in snap["brands"]:
            continue
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
    heats = [b["heat"] for b in d["brands"] if b["heat"] is not None]
    assert heats == sorted(heats, reverse=True)
    assert [b["id"] for b in d["brands"] if b["heat"] is None] == ["ID-11", "ID-12"]


def test_build_without_snapshot_stays_demo(tmp_path):
    d = build_localradar(tmp_path / "t.db", x_snapshot=None)
    assert d["demo"] is True and d["x_snapshot"] is None
    assert all("x_followers" not in b for b in d["brands"])


def test_brand_missing_from_snapshot_is_demo():
    b = dict(BRANDS[0], heat_signals=["s"])
    out = xs.apply_snapshot(b, {"platform": "x", "brands": {}})
    assert out["source_type"] == "demo_seed" and out["heat"] == BRANDS[0]["heat"]


def test_newly_verified_handles_keep_recorded_mentions(tmp_path):
    """ID-01 / ID-09 只补已核实官方号与粉丝、累计帖数，不新造 mentions_7d 或近 30 天发帖。"""
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    kopi = snap["brands"]["ID-01"]
    rotio = snap["brands"]["ID-09"]
    assert kopi["seed_handle"] == "@KopiKenangan" and kopi["handle_status"] == "replaced"
    assert kopi["resolved_handle"] == "@Kopikenangan_ID"
    assert kopi["account"]["name"] == "Kopi Kenangan" and kopi["account"]["verified"] is True
    assert kopi["account"]["followers_count"] == 12895 and kopi["account"]["tweet_count"] == 3139
    assert "posts_30d" not in kopi and not kopi.get("last_post_at")
    assert kopi["mentions_7d"]["total"] == 968
    assert "12:36" in kopi["handle_note"]
    assert rotio["seed_handle"] == "@rotiocomalang" and rotio["handle_status"] == "replaced"
    assert rotio["resolved_handle"] == "@rotioindonesia"
    assert rotio["account"]["name"] == "Roti'O Indonesia"
    assert rotio["account"]["followers_count"] == 397 and rotio["account"]["tweet_count"] == 388
    assert "posts_30d" not in rotio and not rotio.get("last_post_at")
    assert rotio["mentions_7d"]["total"] == 444
    assert "rotio.id" in rotio["handle_note"] and "12:36" in rotio["handle_note"]

    d = build_localradar(tmp_path / "t.db", x_snapshot=SNAP)
    by_id = {b["id"]: b for b in d["brands"]}
    k, r, j = by_id["ID-01"], by_id["ID-09"], by_id["ID-02"]
    assert k["x"] == "@Kopikenangan_ID" and k["x_followers"] == 12895 and k["x_tweet_count"] == 3139
    assert k["x_posts_30d"] is None and k["provenance"]["x_posts_30d"] == "missing"
    assert k["provenance"]["x_followers"] == "x_public" and k["x_mentions_7d"] == 968
    assert "12,895" in k["heat_signals_x"][1] and "3,139" in k["heat_signals_x"][1]
    assert "None" not in " ".join(k["heat_signals_x"])
    assert r["x"] == "@rotioindonesia" and r["x_followers"] == 397 and r["x_mentions_7d"] == 444
    assert "None" not in " ".join(r["heat_signals_x"])
    assert any("近 30 天发帖 0 · 最近发帖 2023-07-11" in s for s in j["heat_signals_x"])


def test_new_brands_wait_for_x_refresh_without_invented_metrics(tmp_path):
    """ID-11 / ID-12 用品牌清单里的官方号、IG 和官网；X 数字留空，等下次刷新。"""
    listed = {b["brand"]: b for b in json.loads(
        (SNAP.parent / "brand_list_coffee_tea_2026-11-04.json").read_text(encoding="utf-8"))["brands"]}
    tomoro_src, calais_src = listed["Tomoro Coffee"], listed["Calais Tea"]
    by_seed = {b["id"]: b for b in BRANDS}
    assert by_seed["ID-11"]["x"] == "@TomoroCoffee_ID" == tomoro_src["x_handle"]
    assert by_seed["ID-11"]["ig"] == tomoro_src["ig_handle"] == "@tomorocoffee.id"
    assert by_seed["ID-11"]["website"] == tomoro_src["website"]
    assert by_seed["ID-12"]["x"] == "@CalaisTea" == calais_src["x_handle"]
    assert by_seed["ID-12"]["ig"] == calais_src["ig_handle"] == "@calaistea"
    assert by_seed["ID-12"]["website"] == calais_src["website"]
    for bid in ("ID-11", "ID-12"):
        assert by_seed[bid]["origin_label"] == "未核实"
        assert by_seed[bid]["metrics_pending"] is True
    assert by_seed["ID-01"]["origin_label"] == "本土"
    assert by_seed["ID-10"]["origin_label"] == "本土（Sour Sally Group 旗下，台式概念）"

    d = build_localradar(tmp_path / "t.db", x_snapshot=SNAP)
    by_id = {b["id"]: b for b in d["brands"]}
    forbidden = ("1694", "656", "10256", "20517")
    for bid, src in (("ID-11", tomoro_src), ("ID-12", calais_src)):
        b = by_id[bid]
        assert b["source_type"] == "pending_x"
        assert b["x"] == src["x_handle"]
        assert b["ig"] == src["ig_handle"] and b["provenance"]["ig"] == "demo_estimate"
        assert b["website"] == src["website"] and b["origin_label"] == "未核实"
        assert b["x_followers"] is None and b["x_mentions_7d"] is None and b["x_tweet_count"] is None
        assert b["heat"] is None and b["value_score"] is None
        assert b["provenance"]["x"] == "pending"
        assert b["provenance"]["x_followers"] == "missing"
        assert b["provenance"]["x_mentions_7d"] == "missing"
        assert b["provenance"]["heat"] == "missing"
        blob = json.dumps(b, ensure_ascii=False)
        assert all(n not in blob for n in forbidden)
        assert "待刷新" in b["heat_signals"][0]

    plan = xs.refresh_plan(BRANDS, json.loads(SNAP.read_text(encoding="utf-8")))
    pending = [p for p in plan if not p["in_snapshot"]]
    assert [(p["id"], p["x_handle"]) for p in pending] == [
        ("ID-11", "@TomoroCoffee_ID"),
        ("ID-12", "@CalaisTea"),
    ]
    assert all(p["include_in_user_lookup"] and p["mentions_query"] is None for p in pending)
    assert all("followers" not in p and "account" not in p for p in plan)
    kopi = next(p for p in plan if p["id"] == "ID-01")
    assert kopi["in_snapshot"] and kopi["x_handle"] == "@Kopikenangan_ID"
    assert kopi["mentions_query"]

    published = json.loads((SNAP.parents[2] / "web/trend/data/local_brands.json").read_text(encoding="utf-8"))
    pub = {b["id"]: b for b in published["brands"]}
    assert set(pub) == {b["id"] for b in BRANDS}
    for bid in ("ID-11", "ID-12"):
        assert pub[bid]["source_type"] == "pending_x"
        assert pub[bid]["x_followers"] is None and pub[bid]["x_mentions_7d"] is None
        assert pub[bid]["provenance"]["ig"] == "demo_estimate"
        assert pub[bid]["origin_label"] == "未核实"


def test_heat_formula():
    assert xs.heat_from_mentions(0) == 0.0
    assert xs.heat_from_mentions(xs.HEAT_REF_MENTIONS_7D) == 100.0
    assert xs.heat_from_mentions(10 ** 6) == 100.0
    with pytest.raises(ValueError):
        xs.heat_from_mentions(-1)
