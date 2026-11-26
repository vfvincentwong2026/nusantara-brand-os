"""线上冒烟脚本的离线约定：编码、跳过外链、工作流只在 deploy 成功后跑。"""
import importlib.util
import json
import threading
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "smoke_live_site.py"
    spec = importlib.util.spec_from_file_location("smoke_live_site", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chinese_query_is_percent_encoded_once():
    mod = _load()
    page = mod.BASE_URL + "library/"
    url = mod.resolve_same_site(page, "../map/?label=合作提案")
    assert url == (
        "https://vfvincentwong2026.github.io/nusantara-brand-os/map/"
        "?label=%E5%90%88%E4%BD%9C%E6%8F%90%E6%A1%88"
    )
    assert url.isascii()
    assert mod.encode_url(url) == url


def test_space_in_query_is_encoded_and_not_doubled():
    mod = _load()
    once = mod.encode_url(
        "https://vfvincentwong2026.github.io/nusantara-brand-os/map/?label=合作 提案"
    )
    assert once.endswith("label=%E5%90%88%E4%BD%9C%20%E6%8F%90%E6%A1%88")
    assert mod.encode_url(once) == once


def test_skips_external_mailto_templates_and_identifiers():
    mod = _load()
    page = mod.BASE_URL + "trend/"
    html = """
    <a href="https://nusantara-container.pages.dev/store-dash/">ext</a>
    <a href="mailto:a@b.c?subject=合作提案">mail</a>
    <a href="../map/?focus=RD-${s.id}">tmpl</a>
    <a href="javascript:void(0)">js</a>
    <script>fetch(u)</script>
    <script>fetch('./data/local_brands.json')</script>
    <img src="../assets/a.jpg">
    """
    assert mod.extract_links(html, page) == [
        mod.BASE_URL + "trend/data/local_brands.json",
        mod.BASE_URL + "assets/a.jpg",
    ]


def test_json_assets_resolve_at_site_root():
    mod = _load()
    assert mod.asset_string_url("assets/radar/ID-01.jpg") == (
        mod.BASE_URL + "assets/radar/ID-01.jpg"
    )
    assert mod.asset_string_url("https://example.com/assets/a.jpg") is None
    assert mod.asset_string_url("/assets/a.jpg") is None
    encoded = mod.asset_string_url("assets/a.jpg?q=合作")
    assert encoded == mod.BASE_URL + "assets/a.jpg?q=%E5%90%88%E4%BD%9C"
    assert "合作" not in encoded


def test_homepage_retries_then_records_later_404s(tmp_path):
    mod = _load()
    web = tmp_path / "web"
    data = web / "trend" / "data"
    data.mkdir(parents=True)
    (data / "brands.json").write_text(
        json.dumps({"photo": "assets/missing.jpg", "abs": "https://example.com/x"}),
        encoding="utf-8",
    )
    home = mod.BASE_URL
    sleeps: list[float] = []
    calls = {"home": 0}
    requested: list[str] = []
    lock = threading.Lock()

    def request(url, save_body=False):
        with lock:
            requested.append(url)
        assert urlsplit(url).netloc == "vfvincentwong2026.github.io"
        assert url.isascii()
        if url == home:
            calls["home"] += 1
            if calls["home"] < 3:
                return 404, "", ""
            return 200, '<a href="map/?label=合作"><script src="site.js"></script>', ""
        if url.endswith("/site.js"):
            return 200, "fetch('./data/local_brands.json')", ""
        if url.endswith("/data/local_brands.json") or url.endswith("/assets/missing.jpg"):
            return 404, "", ""
        return 200, "", ""

    statuses, failures = mod.run_smoke(
        request,
        web,
        sleep=sleeps.append,
        homepage_attempts=5,
        homepage_delay=4,
    )
    assert calls["home"] == 3
    assert sleeps == [4, 4]
    failed = {url: status for url, status, _origin, _err in failures}
    assert failed == {
        mod.BASE_URL + "data/local_brands.json": 404,
        mod.BASE_URL + "assets/missing.jpg": 404,
    }
    assert statuses[mod.BASE_URL + "map/?label=%E5%90%88%E4%BD%9C"] == 200
    assert all("example.com" not in url for url in requested)
    assert all(url.isascii() for url in requested)


def test_deploy_workflow_smokes_only_after_deploy():
    text = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert "path: web" in text
    assert "test -f web/index.html" in text
    smoke = text.split("\n  smoke:", 1)[1]
    assert "needs: deploy" in smoke
    assert "needs.deploy.result == 'success'" in smoke
    assert "contents: read" in smoke
    assert "python3 scripts/smoke_live_site.py" in smoke
    assert "pages: write" not in smoke
    assert "id-token" not in smoke
