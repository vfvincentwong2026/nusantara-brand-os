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
    # 2026-11-04 快照只覆盖当时的 10 家。后来列入的品牌等下次刷新再写入，不在这份历史文件里补数字。
    assert set(snap["brands"]) == {f"ID-{i:02d}" for i in range(1, 11)}
    assert {b["id"] for b in BRANDS} == {f"ID-{i:02d}" for i in range(1, 18)}
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
    assert d["x_snapshot"]["brands_pending_x"] == 7
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
    assert [b["id"] for b in d["brands"] if b["heat"] is None] == [f"ID-{i:02d}" for i in range(11, 18)]
    for row in d["brands"] + d["shops"]:
        photo = row.get("photo")
        if photo:
            assert photo.startswith("assets/radar/") and not photo.startswith("/")


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


def _assert_pending_x_has_no_metrics(b):
    """pending_x 只表示还没抓到，热度、粉丝、提及必须留空。"""
    assert b["source_type"] == "pending_x"
    assert b["heat"] is None and b["x_followers"] is None and b["x_mentions_7d"] is None
    assert b["provenance"]["x"] == "pending"
    assert b["provenance"]["heat"] == "missing"
    assert b["provenance"]["x_followers"] == "missing"
    assert b["provenance"]["x_mentions_7d"] == "missing"


def _assert_metrics_match_snapshot(b, entry):
    """已进入快照的品牌，热度、粉丝、提及只能抄快照，不能另填数字。"""
    assert b["source_type"] == "mixed"
    assert b["x_mentions_7d"] == entry["mentions_7d"]["total"]
    assert b["heat"] == xs.heat_from_mentions(entry["mentions_7d"]["total"])
    assert b["provenance"]["heat"] == "x_public"
    assert b["provenance"]["x_mentions_7d"] == "x_public"
    if entry["handle_status"] in xs.ACCOUNT_OK:
        assert b["x_followers"] == entry["account"]["followers_count"]
        assert b["x_tweet_count"] == entry["account"]["tweet_count"]
        assert b["x"] == entry["resolved_handle"]
        assert b["provenance"]["x_followers"] == "x_public"
        posts = entry.get("posts_30d")
        assert b["x_posts_30d"] == (posts["count"] if posts else None)
    else:
        assert b["x_followers"] is None and b["x_tweet_count"] is None
        assert b["provenance"]["x_followers"] == "missing"


def test_new_brands_wait_for_x_refresh_without_invented_metrics(tmp_path):
    """ID-11 / ID-12 用品牌清单里的官方号、IG 和官网。

    只用 2026-11-04 快照重建时，这两家仍是 pending_x，不填估算数字。
    已发布的 local_brands.json 不要求它们继续 pending：缺快照时热度/粉丝/提及为空，
    快照里已有的数字必须与该快照一致。
    """
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
    # 这些是后来实抓到的账号数字。只用 11-04 快照时还不能出现。
    forbidden = ("1694", "656", "10256", "10257", "20517")
    for bid, src in (("ID-11", tomoro_src), ("ID-12", calais_src)):
        b = by_id[bid]
        _assert_pending_x_has_no_metrics(b)
        assert b["x"] == src["x_handle"]
        assert b["ig"] == src["ig_handle"] and b["provenance"]["ig"] == "demo_estimate"
        assert b["website"] == src["website"] and b["origin_label"] == "未核实"
        assert b["x_tweet_count"] is None and b["value_score"] is None
        blob = json.dumps(b, ensure_ascii=False)
        assert all(n not in blob for n in forbidden)
        assert "待刷新" in b["heat_signals"][0]

    plan = xs.refresh_plan(BRANDS, json.loads(SNAP.read_text(encoding="utf-8")))
    pending = [p for p in plan if not p["in_snapshot"]]
    assert [(p["id"], p["x_handle"]) for p in pending] == [
        ("ID-11", "@TomoroCoffee_ID"),
        ("ID-12", "@CalaisTea"),
        ("ID-13", "@pointcoffeeid"),
        ("ID-14", "@ExcelsoCoffee"),
        ("ID-15", "@anomalicoffee"),
        ("ID-16", "@DJOURNALcoffee"),
        ("ID-17", "@maxxcoffeeID"),
    ]
    assert all(p["include_in_user_lookup"] and p["mentions_query"] is None for p in pending)
    assert all("followers" not in p and "account" not in p for p in plan)
    kopi = next(p for p in plan if p["id"] == "ID-01")
    assert kopi["in_snapshot"] and kopi["x_handle"] == "@Kopikenangan_ID"
    assert kopi["mentions_query"]

    published = json.loads((SNAP.parents[2] / "web/trend/data/local_brands.json").read_text(encoding="utf-8"))
    pub = {b["id"]: b for b in published["brands"]}
    assert set(pub) == {b["id"] for b in BRANDS}
    cited = json.loads((SNAP.parent / published["x_snapshot"]["file"]).read_text(encoding="utf-8"))
    pending_ids = []
    for b in published["brands"]:
        entry = cited["brands"].get(b["id"])
        if b["source_type"] == "pending_x":
            assert entry is None
            _assert_pending_x_has_no_metrics(b)
            pending_ids.append(b["id"])
            continue
        if entry is not None:
            _assert_metrics_match_snapshot(b, entry)
    assert published["x_snapshot"]["brands_pending_x"] == len(pending_ids)
    for bid, src in (("ID-11", tomoro_src), ("ID-12", calais_src)):
        b = pub[bid]
        assert b["ig"] == src["ig_handle"] and b["provenance"]["ig"] == "demo_estimate"
        assert b["website"] == src["website"] and b["origin_label"] == "未核实"
        entry = cited["brands"].get(bid)
        if entry is None:
            _assert_pending_x_has_no_metrics(b)
        else:
            _assert_metrics_match_snapshot(b, entry)


_NEW_COFFEE = {
    "ID-13": {"x": "@pointcoffeeid", "ig": "@pointcoffeeid", "tiktok": "@pointcoffeeid",
              "website": "https://pointcoffee.id"},
    "ID-14": {"x": "@ExcelsoCoffee", "ig": "@excelsocoffee", "tiktok": "",
              "website": "http://linktr.ee/ExcelsoCoffee"},
    "ID-15": {"x": "@anomalicoffee", "ig": "@anomalicoffee", "tiktok": "",
              "website": "https://anomalicoffee.com"},
    "ID-16": {"x": "@DJOURNALcoffee", "ig": "@djournalcoffee", "tiktok": "",
              "website": "http://thedjournalguidetocoffee.com"},
    "ID-17": {"x": "@maxxcoffeeID", "ig": "@maxxcoffeeid", "tiktok": "",
              "website": "https://linktr.ee/MaxxCoffee"},
}
_METRIC_KEYS = ("followers_wan", "views_wan", "likes_wan", "shares_wan", "er", "growth_30d",
                "heat", "need_supply", "need_social", "need_strategy")
# 2026-11-10 10:10 复核读到的粉丝数。种子和尚未进快照的 pending 输出里都不能出现。
_REVIEWED_FOLLOWERS = ("7975", "13947", "8548", "1727", "1812")
# 这 5 家第一次进入每日快照的日期。更早的 x_snapshot_*.json 不得补写它们。
_FIRST_X_CAPTURE = "2026-11-11"


def test_added_local_coffee_brands_appear_from_2026_11_11_snapshot(tmp_path):
    """ID-13..ID-17 的 X / IG / 官网与 2026-11-10 品牌清单一致，种子指标留空。

    2026-11-11 之前的快照里没有这 5 家；最新快照已经写入。
    用最新快照重建后，已发布的 local_brands.json 不再是 pending_x，数字只来自该快照。
    只用 2026-11-04 快照重建时，它们仍是 pending_x，不填估算数字。
    """
    old = json.loads((SNAP.parent / "brand_list_coffee_tea_2026-11-04.json").read_text(encoding="utf-8"))
    listed = json.loads((SNAP.parent / "brand_list_coffee_tea_2026-11-10.json").read_text(encoding="utf-8"))
    assert listed["schema"] == "nbo.radar.brand_list/v1"
    assert "2026-11-10" in listed["generated_at"] and "2026-11-10" in listed["x_source"]
    assert [b["brand"] for b in listed["brands"]] == [b["brand"] for b in old["brands"]]
    by_seed = {b["id"]: b for b in BRANDS}
    by_repo = {b.get("repo_id"): b for b in listed["brands"]}
    old_by_name = {b["brand"]: b for b in old["brands"]}
    for bid, expect in _NEW_COFFEE.items():
        seed = by_seed[bid]
        src = by_repo[bid]
        assert old_by_name[src["brand"]]["repo_id"] is None
        assert seed["x"] == expect["x"] == src["x_handle"]
        assert seed["ig"] == expect["ig"] == src["ig_handle"]
        assert seed["website"] == expect["website"] == src["website"]
        assert seed["tiktok"] == expect["tiktok"]
        assert seed["metrics_pending"] is True
        assert seed["origin_label"] == "本土" == src["local"]
        assert seed["city"] == "未核实" and seed["stage"] == "未核实"
        assert seed["boost"] == [] and seed["contact"] == ""
        assert seed["coop_model"] == "待评估" and seed["viral_format"] == "未核实"
        assert seed["heat_signals"][0].startswith("【待刷新】")
        assert "不填估算数字" in seed["why_hot"]
        for key in _METRIC_KEYS:
            assert seed[key] is None
        if bid == "ID-13":
            assert src["tiktok_handle"] == "@pointcoffeeid"
            assert src["tiktok_status"]
            assert "tiktok.com/@pointcoffeeid" in src["tiktok_source_url"]
        else:
            assert "tiktok_handle" not in src and "tiktok_status" not in src
        if bid == "ID-15":
            assert "是否算连锁" in src["origin_note"]

    for snap_path in sorted(SNAP.parent.glob("x_snapshot_*.json")):
        historical = json.loads(snap_path.read_text(encoding="utf-8"))
        stamp = snap_path.stem.removeprefix("x_snapshot_")
        if stamp < _FIRST_X_CAPTURE:
            assert set(_NEW_COFFEE).isdisjoint(historical["brands"])

    latest_path = xs.latest_snapshot_path()
    latest = xs.load_snapshot(latest_path)
    assert latest_path.stem.removeprefix("x_snapshot_") >= _FIRST_X_CAPTURE
    assert set(_NEW_COFFEE) <= set(latest["brands"])
    plan = xs.refresh_plan(BRANDS, latest)
    for bid, expect in _NEW_COFFEE.items():
        row = next(p for p in plan if p["id"] == bid)
        assert row["in_snapshot"] is True and row["x_handle"] == expect["x"]
    for bid in ("ID-11", "ID-12"):
        row = next(p for p in plan if p["id"] == bid)
        assert row["in_snapshot"] is True and row["x_handle"]

    for label, snap in (("old", SNAP), ("latest", latest_path)):
        built = build_localradar(tmp_path / f"{label}.db", x_snapshot=snap)
        by_id = {b["id"]: b for b in built["brands"]}
        snap_data = json.loads(Path(snap).read_text(encoding="utf-8"))
        if label == "old":
            assert set(_NEW_COFFEE).isdisjoint(snap_data["brands"])
            assert built["x_snapshot"]["brands_pending_x"] == 7
        else:
            assert set(_NEW_COFFEE) <= set(snap_data["brands"])
        assert built["x_snapshot"]["brands_pending_x"] == sum(
            1 for b in built["brands"] if b["source_type"] == "pending_x")
        for bid, expect in _NEW_COFFEE.items():
            b = by_id[bid]
            assert b["x"] == expect["x"] and b["ig"] == expect["ig"] and b["website"] == expect["website"]
            assert b["tiktok"] == expect["tiktok"] and b["metrics_pending"] is True
            assert b["origin_label"] == "本土" and b["value_score"] is None
            entry = snap_data["brands"].get(bid)
            if entry is None:
                _assert_pending_x_has_no_metrics(b)
                for key in _METRIC_KEYS:
                    assert b[key] is None
                blob = json.dumps(b, ensure_ascii=False)
                assert all(n not in blob for n in _REVIEWED_FOLLOWERS)
            else:
                assert b["source_type"] != "pending_x"
                _assert_metrics_match_snapshot(b, entry)
                for key in _METRIC_KEYS:
                    if key == "heat":
                        continue
                    assert b[key] is None

    published = json.loads((SNAP.parents[2] / "web/trend/data/local_brands.json").read_text(encoding="utf-8"))
    cited_name = published["x_snapshot"]["file"]
    cited = json.loads((SNAP.parent / cited_name).read_text(encoding="utf-8"))
    assert Path(cited_name).stem.removeprefix("x_snapshot_") >= _FIRST_X_CAPTURE
    assert set(_NEW_COFFEE) <= set(cited["brands"])
    pub = {b["id"]: b for b in published["brands"]}
    assert published["x_snapshot"]["brands_pending_x"] == sum(
        1 for b in published["brands"] if b["source_type"] == "pending_x")
    for bid, expect in _NEW_COFFEE.items():
        b = pub[bid]
        assert b["source_type"] != "pending_x"
        _assert_metrics_match_snapshot(b, cited["brands"][bid])
        assert b["x"] == expect["x"] and b["ig"] == expect["ig"] and b["website"] == expect["website"]
        assert b["metrics_pending"] is True
        for key in _METRIC_KEYS:
            if key == "heat":
                continue
            assert b[key] is None


def test_heat_formula():
    assert xs.heat_from_mentions(0) == 0.0
    assert xs.heat_from_mentions(xs.HEAT_REF_MENTIONS_7D) == 100.0
    assert xs.heat_from_mentions(10 ** 6) == 100.0
    with pytest.raises(ValueError):
        xs.heat_from_mentions(-1)
