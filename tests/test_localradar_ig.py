"""Instagram Business Discovery：无凭证不请求，有凭证只抄接口原值，错误和限流不编造数字。"""
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from nbo.localradar import BRANDS, build_localradar
from nbo.localradar import igsnapshot as ig
from nbo.localradar import xsnapshot as xs

ROOT = Path(__file__).resolve().parents[1]
BRAND_LIST = ROOT / "data/radar/brand_list_coffee_tea_2026-11-04.json"
X_SNAP = ROOT / "data/radar/x_snapshot_2026-11-04.json"
TOKEN = "SUPER_SECRET_TOKEN_VALUE"
USER_ID = "17841405309211844"
NOW = datetime(2026, 11, 5, 2, 55, tzinfo=timezone.utc)


def _env(**extra):
    base = {ig.ENV_USER_ID: USER_ID, ig.ENV_ACCESS_TOKEN: TOKEN}
    base.update(extra)
    return base


def _row(brand, handle, repo_id=None):
    return {"brand": brand, "repo_id": repo_id, "ig_handle": handle}


def _ok_body(followers, media_count=2, media=None, paging=False):
    payload = {
        "followers_count": followers,
        "media_count": media_count,
        "id": "17841401441775531",
    }
    if media is not None:
        media_obj = {"data": media}
        if paging:
            media_obj["paging"] = {"cursors": {"after": "CURSOR"}}
        payload["media"] = media_obj
    return {"business_discovery": payload, "id": USER_ID}


def _username(url):
    fields = parse_qs(urlsplit(url).query)["fields"][0]
    marker = "business_discovery.username("
    start = fields.index(marker) + len(marker)
    return fields[start:fields.index(")", start)]


def _boom(url):
    raise AssertionError(f"不应请求: {url}")


def test_missing_credentials_do_not_request_or_write(tmp_path, capsys):
    cases = [
        {},
        {ig.ENV_USER_ID: USER_ID},
        {ig.ENV_ACCESS_TOKEN: TOKEN},
        {ig.ENV_USER_ID: "  ", ig.ENV_ACCESS_TOKEN: "  "},
        {ig.ENV_USER_ID: USER_ID, ig.ENV_ACCESS_TOKEN: ""},
    ]
    for env in cases:
        code = ig.main(["--out-dir", str(tmp_path), "--date", "2026-11-05"], env=env, http_get=_boom)
        err = capsys.readouterr().err
        assert code == 2
        assert "IG 未接通" in err
        assert TOKEN not in err
        assert list(tmp_path.glob("ig_snapshot_*.json")) == []
    with pytest.raises(ig.IGNotConnected):
        ig.collect(env={}, brand_list={"brands": []}, brands=[], http_get=_boom)


def test_recorded_handles_only_and_no_guessing():
    raw = json.loads(BRAND_LIST.read_text(encoding="utf-8"))
    targets, skipped = ig.recorded_targets(raw, BRANDS)
    recorded = []
    for row in raw["brands"]:
        parsed = ig.parse_recorded_handle(row.get("ig_handle"))
        if parsed["kind"] == "ok":
            recorded.append(parsed["username"])
    assert [t["username"] for t in targets if t["status"] == "recorded"] == recorded
    assert {s["id"] for s in skipped} == {"ID-05", "ID-08", "ID-09"}
    by_id = {t["id"]: t["username"] for t in targets if t["status"] == "recorded"}
    assert by_id["ID-01"] == "kopikenangan.id"
    assert by_id["ID-02"] == "kopijanjijiwa"
    assert by_id["ID-07"] == "tokokopituku"
    assert by_id["ID-11"] == "tomorocoffee.id"
    assert by_id["ID-12"] == "calaistea"
    assert "ExcelsoCoffee" in by_id.values()
    requested = set(by_id.values())
    assert "richeesefactory" not in requested
    assert "soursally" not in requested
    assert "rotiocomalang" not in requested
    assert "richeesefactory" not in json.dumps(skipped, ensure_ascii=False)

    brands = [{"id": "ID-99", "name": "Nope", "ig": "@guessed-from-seed"}]
    targets, skipped = ig.recorded_targets({"brands": []}, brands)
    assert targets == []
    assert skipped == [{"id": "ID-99", "brand": "Nope", "reason": "未记录 handle"}]

    brands = [
        {"id": "ID-01", "name": "Kopi Kenangan", "ig": "@should-not-use"},
        {"id": "ID-05", "name": "Richeese Factory", "ig": "@richeesefactory"},
    ]
    targets, skipped = ig.recorded_targets({"brands": [
        _row("Kopi Kenangan", "@kopikenangan.id", "ID-01"),
        _row("Richeese Factory", None, "ID-05"),
        _row("Weird", "not a handle / https://instagram.com/foo"),
        _row("Blank", "  "),
    ]}, brands)
    assert [t["username"] for t in targets if "username" in t] == ["kopikenangan.id"]
    assert any(t["status"] == "invalid_handle" and "not a handle" in t["seed_handle"] for t in targets)
    assert {s["id"] for s in skipped} == {"ID-05"}


def test_duplicate_brand_id_does_not_request():
    brand_list = {"brands": [
        _row("Kopi Kenangan", "@one", "ID-01"),
        _row("Kopi Kenangan", "@two"),
    ]}
    brands = [{"id": "ID-01", "name": "Kopi Kenangan", "ig": "@seed"}]
    with pytest.raises(ig.IGBrandDataError):
        ig.recorded_targets(brand_list, brands)
    with pytest.raises(ig.IGBrandDataError):
        ig.collect(env=_env(), brand_list=brand_list, brands=brands, http_get=_boom, now=NOW)


def test_success_parses_raw_fields_and_omits_token(tmp_path, capsys):
    calls = []

    def http_get(url):
        calls.append(url)
        assert urlsplit(url).netloc == "graph.facebook.com"
        assert urlsplit(url).path == f"/{ig.GRAPH_VERSION}/{USER_ID}"
        query = parse_qs(urlsplit(url).query)
        assert query["access_token"] == [TOKEN]
        username = _username(url)
        assert username == "kopikenangan.id"
        fields = query["fields"][0]
        assert "followers_count,media_count" in fields
        assert f"media.limit({ig.MEDIA_LIMIT})" in fields
        assert "timestamp,like_count,comments_count,permalink" in fields
        return 200, _ok_body(267793, 1205, media=[
            {
                "id": "17858843269216389",
                "timestamp": "2026-11-01T00:00:00+0000",
                "like_count": 5837,
                "comments_count": 50,
                "permalink": "https://www.instagram.com/p/AbC/",
            },
            {
                "id": "17894036119131554",
                "timestamp": "2026-10-02T03:04:05+0000",
                "comments_count": 0,
                "permalink": "https://www.instagram.com/p/Hide/",
            },
        ], paging=True)

    brands = [{"id": "ID-01", "name": "Kopi Kenangan", "ig": "@do-not-guess"}]
    code = ig.main(
        ["--out-dir", str(tmp_path)],
        env=_env(),
        http_get=http_get,
        brands=brands,
        brand_list={"brands": [_row("Kopi Kenangan", "@kopikenangan.id", "ID-01")]},
        brand_list_name="brand_list_test.json",
        now=NOW,
    )
    captured = capsys.readouterr()
    assert code == 0
    assert TOKEN not in captured.out and TOKEN not in captured.err
    assert len(calls) == 1
    path = tmp_path / "ig_snapshot_2026-11-05.json"
    snap = json.loads(path.read_text(encoding="utf-8"))
    assert TOKEN not in path.read_text(encoding="utf-8")
    assert snap["schema"] == "nbo.radar.ig_snapshot/v1"
    assert snap["platform"] == "instagram"
    assert snap["fetched_at"] == "2026-11-05T02:55:00Z"
    assert snap["fetched_at_local"] == "2026-11-05 09:55 (UTC+7)"
    assert snap["source"] == "Instagram Graph API business_discovery"
    assert snap["graph_version"] == "v27.0"
    assert snap["queried_ig_user_id"] == USER_ID
    assert snap["credential_source"] == "env:NBO_IG_USER_ID,env:NBO_IG_ACCESS_TOKEN"
    assert snap["brand_list"] == "brand_list_test.json"
    assert snap["ig_calls_used"] == 1
    entry = snap["brands"]["ID-01"]
    assert entry["status"] == "ok"
    assert entry["seed_handle"] == "@kopikenangan.id"
    assert entry["handle_source"] == "brand_list.ig_handle"
    assert entry["account"]["followers_count"] == 267793
    assert entry["account"]["media_count"] == 1205
    assert entry["media_truncated"] is True
    assert entry["media"][0]["like_count"] == 5837
    assert entry["media"][0]["comments_count"] == 50
    assert entry["media"][0]["permalink"] == "https://www.instagram.com/p/AbC/"
    assert entry["media"][0]["timestamp"] == "2026-11-01T00:00:00+0000"
    assert entry["media"][1]["like_count"] is None
    assert entry["media"][1]["comments_count"] == 0
    assert "do-not-guess" not in path.read_text(encoding="utf-8")
    summary = json.loads(captured.out)
    assert summary["file"] == "ig_snapshot_2026-11-05.json"
    assert summary["source"] == snap["source"]
    assert summary["ok"] == 1


def test_real_brand_list_requests_each_recorded_handle_once(tmp_path):
    raw = json.loads(BRAND_LIST.read_text(encoding="utf-8"))
    calls = []

    def http_get(url):
        username = _username(url)
        calls.append(username)
        return 200, _ok_body(1000 + len(username), 4, media=[
            {"timestamp": "2026-11-01T00:00:00+0000", "like_count": 2, "comments_count": 1,
             "permalink": f"https://www.instagram.com/{username}/"},
        ])

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05", "--brand-list", str(BRAND_LIST)],
        env=_env(),
        http_get=http_get,
        now=NOW,
    )
    assert code == 0
    expected = []
    for row in raw["brands"]:
        parsed = ig.parse_recorded_handle(row.get("ig_handle"))
        if parsed["kind"] == "ok":
            expected.append(parsed["username"])
    assert calls == expected
    snap = json.loads((tmp_path / "ig_snapshot_2026-11-05.json").read_text(encoding="utf-8"))
    assert TOKEN not in json.dumps(snap)
    assert {s["id"] for s in snap["skipped"]} == {"ID-05", "ID-08", "ID-09"}
    assert snap["brands"]["ID-01"]["account"]["followers_count"] == 1000 + len("kopikenangan.id")
    assert snap["brands"]["ID-11"]["username"] == "tomorocoffee.id"
    blob = json.dumps(snap)
    assert "richeesefactory" not in blob
    assert "soursally" not in blob
    assert "rotiocomalang" not in blob


@pytest.mark.parametrize("status,body", [
    (429, {"error": {"message": "too many", "type": "OAuthException", "code": 4}}),
    (400, {"error": {"message": "Application request limit reached", "type": "OAuthException", "code": 4}}),
    (403, {"error": {"message": "User request limit reached", "type": "OAuthException", "code": 17}}),
    (400, {"error": {"message": "Page request limit reached", "type": "OAuthException", "code": 32}}),
    (400, {"error": {"message": "Calls to this api have exceeded the rate limit", "code": 613}}),
    (400, {"error": {"message": "too many calls to this instagram account", "code": 80002}}),
])
def test_rate_limit_stops_and_writes_nothing(tmp_path, capsys, status, body):
    calls = []

    def http_get(url):
        calls.append(_username(url))
        if len(calls) == 1:
            return 200, _ok_body(10, 1, media=[])
        return status, body

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [
            _row("One", "@alpha.one"),
            _row("Two", "@beta.two"),
            _row("Three", "@gamma.three"),
        ]},
        now=NOW,
    )
    err = capsys.readouterr().err
    assert code == 3
    assert calls == ["alpha.one", "beta.two"]
    assert "限流" in err
    assert TOKEN not in err
    assert list(tmp_path.glob("ig_snapshot_*.json")) == []
    assert list(tmp_path.glob("*.tmp")) == []


def test_auth_and_permission_stop_without_leaking_token(tmp_path, capsys):
    calls = []

    def http_get(url):
        calls.append(_username(url))
        return 400, {"error": {
            "message": f"Invalid OAuth access token {TOKEN}",
            "type": "OAuthException",
            "code": 190,
        }}

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha"), _row("Two", "@beta")]},
        now=NOW,
    )
    err = capsys.readouterr().err
    assert code == 4
    assert calls == ["alpha"]
    assert TOKEN not in err
    assert "[redacted]" in err
    assert list(tmp_path.glob("ig_snapshot_*.json")) == []

    calls.clear()

    def http_get_permission(url):
        calls.append(_username(url))
        return 403, {"error": {"message": "permission", "type": "OAuthException", "code": 10}}

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get_permission,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha"), _row("Two", "@beta")]},
        now=NOW,
    )
    assert code == 4 and calls == ["alpha"]


def test_misconfigured_professional_account_stops(tmp_path, capsys):
    calls = []

    def http_get(url):
        calls.append(url)
        return 400, {"error": {
            "message": "(#100) Tried accessing nonexisting field (business_discovery) on node type (User)",
            "type": "OAuthException",
            "code": 100,
        }}

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(NBO_IG_USER_ID="12345"),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha"), _row("Two", "@beta")]},
        now=NOW,
    )
    assert code == 4
    assert len(calls) == 1
    assert list(tmp_path.iterdir()) == []


def test_invalid_user_id_does_not_request(tmp_path, capsys):
    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(NBO_IG_USER_ID="not-an-id"),
        http_get=_boom,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha")]},
        now=NOW,
    )
    err = capsys.readouterr().err
    assert code == 4
    assert "IG 未接通" not in err
    assert list(tmp_path.iterdir()) == []


def test_per_brand_error_keeps_other_brands_and_invents_nothing(tmp_path):
    def http_get(url):
        username = _username(url)
        if username == "missing.one":
            return 400, {"error": {
                "message": "Invalid user id",
                "type": "OAuthException",
                "code": 110,
                "error_subcode": 2207013,
                "fbtrace_id": "trace",
            }}
        if username == "bad.payload":
            return 200, {"business_discovery": {"id": "x", "media_count": 9, "followers_count": -1}}
        return 200, _ok_body(42, 7, media=[
            {"timestamp": "2026-11-03T00:00:00+0000", "like_count": 0, "comments_count": 3,
             "permalink": "https://www.instagram.com/p/Ok/"},
        ])

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [
            _row("Missing", "@missing.one"),
            _row("Bad", "@bad.payload"),
            _row("Ok", "@ok.brand"),
            _row("Nope", "see bio"),
        ]},
        now=NOW,
    )
    assert code == 0
    snap = json.loads((tmp_path / "ig_snapshot_2026-11-05.json").read_text(encoding="utf-8"))
    brands = list(snap["brands"].values())
    missing, bad, ok, invalid = brands
    assert missing["status"] == "error"
    assert missing["error"]["code"] == 110
    assert missing["error"]["error_subcode"] == 2207013
    assert "account" not in missing and "media" not in missing
    assert "followers_count" not in missing
    assert bad["status"] == "error"
    assert "account" not in bad and "media" not in bad
    assert "-1" not in json.dumps(bad)
    assert "9" not in json.dumps(bad["error"])
    assert ok["status"] == "ok"
    assert ok["account"] == {"id": "17841401441775531", "followers_count": 42, "media_count": 7}
    assert ok["media"][0]["like_count"] == 0
    assert ok["media"][0]["comments_count"] == 3
    assert invalid["status"] == "invalid_handle"
    assert "username" not in invalid
    assert snap["ig_calls_used"] == 3


def test_server_error_writes_nothing(tmp_path, capsys):
    calls = []

    def http_get(url):
        calls.append(_username(url))
        if len(calls) == 1:
            return 200, _ok_body(10, 1, media=[])
        return 500, {"error": {"message": "unknown", "code": 1}}

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha"), _row("Two", "@beta")]},
        now=NOW,
    )
    err = capsys.readouterr().err
    assert code == 1
    assert calls == ["alpha", "beta"]
    assert "服务器错误" in err
    assert list(tmp_path.iterdir()) == []


def test_transport_error_writes_nothing(tmp_path, capsys):
    def http_get(url):
        raise ConnectionError(f"failed {TOKEN} {url}")

    code = ig.main(
        ["--out-dir", str(tmp_path), "--date", "2026-11-05"],
        env=_env(),
        http_get=http_get,
        brands=[],
        brand_list={"brands": [_row("One", "@alpha")]},
        now=NOW,
    )
    err = capsys.readouterr().err
    assert code == 1
    assert TOKEN not in err
    assert list(tmp_path.iterdir()) == []


def test_rebuild_keeps_demo_labels_without_using_ig_snapshot(tmp_path):
    ig_file = tmp_path / "ig_snapshot_2026-11-05.json"
    ig_file.write_text(json.dumps({
        "platform": "instagram",
        "brands": {"ID-01": {"account": {"followers_count": 424242}}},
    }), encoding="utf-8")
    assert "igsnapshot" not in inspect.getsource(build_localradar)
    assert "ig_snapshot" not in inspect.getsource(build_localradar)
    assert xs.latest_snapshot_path(tmp_path) is None
    with pytest.raises(ValueError):
        xs.load_snapshot(ig_file)
    demo = build_localradar(tmp_path / "t.db", x_snapshot=None)
    assert demo["demo"] is True
    assert demo["x_snapshot"] is None
    assert demo.get("ig_snapshot") is None
    assert "演示" in demo["source_note"]
    assert "424242" not in json.dumps(demo)

    mixed = build_localradar(tmp_path / "x.db", x_snapshot=X_SNAP)
    assert "演示估算" in mixed["source_note"]
    assert mixed.get("ig_snapshot") is None
    for brand in mixed["brands"]:
        assert brand["provenance"]["ig"] == "demo_estimate"
        assert "ig_followers" not in brand
        assert "followers_count" not in brand
