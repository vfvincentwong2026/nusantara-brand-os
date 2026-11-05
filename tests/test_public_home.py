"""对外官网：根路径首页、无价格、无演示邮箱，雷达只承诺 X 公开字段。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
PUBLIC = [WEB / "index.html", WEB / "site.css", WEB / "site.js"]
MAIL = "ptxdirectionpublicrelations@gmail.com"
HANDLE = re.compile(r"^@[A-Za-z0-9_]+$")
ROOT_URL = re.compile(r"""(?:href|src)\s*=\s*['"]/""")
PHONE = re.compile(r"(?<!\d)(?:\+62|08)\d{8,13}(?!\d)")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _public_blob() -> str:
    return "\n".join(_text(path) for path in PUBLIC)


def _rows():
    data = json.loads((WEB / "trend" / "data" / "local_brands.json").read_text(encoding="utf-8"))
    brands = data["brands"]

    def public_number(row, key):
        if (row.get("provenance") or {}).get(key) != "x_public":
            return None
        value = row.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return value

    def public_handle(row):
        if (row.get("provenance") or {}).get("x") != "x_public":
            return None
        handle = row.get("x")
        if not isinstance(handle, str) or not HANDLE.fullmatch(handle):
            return None
        return handle

    ranked = sorted(
        (b for b in brands if public_number(b, "heat") is not None and str(b.get("name") or "").strip()),
        key=lambda b: (-public_number(b, "heat"), b["name"]),
    )[:5]
    return data, ranked, public_number, public_handle


def test_public_home_exists_and_defaults_to_indonesian():
    html = _text(WEB / "index.html")
    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="id">' in html
    assert "PT XDirection Public Relations" in html
    assert f"mailto:{MAIL}" in html
    assert 'href="trend/"' in html
    assert 'href="app/"' in html
    assert 'src="site.js"' in html
    assert 'href="site.css"' in html
    assert 'data-set-lang="id"' in html
    assert 'data-set-lang="zh"' in html
    assert 'data-set-lang="en"' in html
    assert "<form" not in html.lower()
    assert "中国品牌落地印尼的作战系统" not in html


def test_public_home_uses_relative_urls_and_states_no_price():
    blob = _public_blob()
    assert ROOT_URL.search(blob) is None
    assert "demo.nbo" not in blob
    assert "¥" not in blob and "￥" not in blob and "&yen;" not in blob
    assert not re.search(r"\$\d", blob)
    assert re.search(r"\bRp\b", blob) is None
    assert re.search(r"\bIDR\b", blob) is None
    assert re.search(r"\bprice\b", blob, re.I) is None
    assert "harga" not in blob
    assert "价格" not in blob and "万起" not in blob and "万元" not in blob and "万盾" not in blob
    assert PHONE.search(blob) is None
    assert "wa.me" not in blob.lower()
    for banned in ("客户数", "testimoni", "testimonial", "studi kasus", "case study", "客户评价"):
        assert banned not in blob.lower() if banned.isascii() else banned not in blob


def test_radar_script_reads_public_x_only():
    js = _text(WEB / "site.js")
    assert 'RADAR_URL = "trend/data/local_brands.json"' in js
    assert '!== "x_public"' in js
    assert "textContent" in js
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    for banned in ("followers_wan", "views_wan", "likes_wan", "shares_wan",
                   "growth_30d", "heat_demo", '["ig"]', "['ig']", '["tiktok"]',
                   "['tiktok']", ".tiktok"):
        assert banned not in js
    data, ranked, public_number, public_handle = _rows()
    assert data["x_snapshot"]["fetched_at"]
    assert "X 公开数据" in data["source_note"]
    assert "TikTok" in data["source_note"]
    assert ranked
    for row in ranked:
        assert public_number(row, "heat") is not None
        handle = public_handle(row)
        if handle is not None:
            assert "不合法" not in handle
        followers = public_number(row, "x_followers")
        if followers is not None:
            assert row["provenance"]["x_followers"] == "x_public"
        # 展示逻辑不会把 IG/TikTok 演示数字当成公开指标
        assert row["provenance"].get("ig") != "x_public"
        assert row["provenance"].get("tiktok") != "x_public"


def test_demo_mailbox_replaced_in_radar_sources():
    published = _text(WEB / "trend" / "data" / "local_brands.json")
    source = _text(ROOT / "src" / "nbo" / "localradar" / "__init__.py")
    assert "demo.nbo" not in published and "demo.nbo" not in source
    assert published.count(MAIL) >= 1
    assert source.count(MAIL) >= 1
    data = json.loads(published)
    contacts = {b.get("contact") for b in data["brands"]}
    assert MAIL in contacts
    assert "partnership@demo.nbo" not in contacts


def test_tool_home_moved_and_keeps_relative_links():
    html = _text(WEB / "app" / "index.html")
    assert "品牌复刻引擎" in html
    assert "../trend/" in html and "../brandkit/" in html and "../library/" in html
    assert 'href="/' not in html and 'src="/' not in html
    assert "location.href='/" not in html
    assert (WEB / "trend" / "index.html").is_file()


def test_footer_links_privacy_and_terms_outside_the_menu():
    html = _text(WEB / "index.html")
    footer = html.split("<footer>", 1)[1].split("</footer>", 1)[0]
    nav = html.split("<nav", 1)[1].split("</nav>", 1)[0]
    assert 'href="privacy/"' in footer and 'href="terms/"' in footer
    assert "Kebijakan privasi" in footer and "Ketentuan layanan" in footer
    assert "privacy/" not in nav and "terms/" not in nav
    assert 'class="legal-links"' in footer


def test_legal_pages_are_bilingual_drafts():
    js = _text(WEB / "legal.js")
    assert "UU 27/2022" in js
    assert "Undang-Undang Nomor 27 Tahun 2022" in js
    assert "草稿" in js and "隐私政策" in js and "服务条款" in js
    assert "公开社媒" in js and "品牌授权" in js
    assert "撤回授权" in js and "删除" in js
    assert "不解释该法的具体条款" in js
    assert MAIL in js
    assert "PT XDirection Public Relations" in js
    assert not re.search(r"Pasal\s+\d+", js)
    assert not re.search(r"第\s*\d+\s*条", js)
    for banned in ("完全符合", "mematuhi seluruh", "fully compliant", "tersertifikasi"):
        assert banned not in js
    for name in ("privacy", "terms"):
        html = _text(WEB / name / "index.html")
        assert '<html lang="id">' in html
        assert "Draf" in html
        assert "PT XDirection Public Relations" in html
        assert f"mailto:{MAIL}" in html
        assert "UU 27/2022" in html
        assert "<form" not in html.lower()
        assert ROOT_URL.search(html) is None
        assert 'href="../site.css"' in html and 'src="../legal.js"' in html
        footer = html.split("<footer>", 1)[1]
        assert 'href="../privacy/"' in footer and 'href="../terms/"' in footer
        assert "¥" not in html and "demo.nbo" not in html
        assert PHONE.search(html) is None


def test_pages_assemble_keeps_public_home_and_tool_home():
    deploy = _text(ROOT / "scripts" / "deploy.py")
    assert "web/app/index.html" in deploy
    assert "site.css" in deploy and "site.js" in deploy
    assert "legal.js" in deploy
    assert '"privacy"' in deploy and '"terms"' in deploy
    workflow = _text(ROOT / ".github" / "workflows" / "deploy.yml")
    assert "path: web" in workflow
    assert "test -f web/index.html" in workflow
