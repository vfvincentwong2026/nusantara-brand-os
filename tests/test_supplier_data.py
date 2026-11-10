"""公开供应商研究数据：有价格必有来源和日期，文件里不出现联系方式。"""
import json
import re
from pathlib import Path

from nbo.localradar import BRANDS

ROOT = Path(__file__).resolve().parents[1]
SUPPLIERS = ROOT / "data/suppliers/suppliers_v1.json"
PRICES = ROOT / "data/suppliers/price_benchmark_v1.json"
BRAND_LIST = ROOT / "data/radar/brand_list_coffee_tea_2026-11-04.json"
BRAND_LIST_REVIEW = ROOT / "data/radar/brand_list_coffee_tea_2026-11-10.json"
PUBLISHED = ROOT / "web/trend/data/local_brands.json"

EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
WA_LINK = re.compile(r"wa\.me|api\.whatsapp\.com|whatsapp\.com/", re.I)
# 印尼手机号。前面不能再是数字，避免商品 ID（如 1600803113231）误伤。
PHONE = re.compile(
    r"(?<!\d)(?:\+62[\s\-]?|62[\s\-])8\d{7,12}(?!\d)"
    r"|(?<!\d)08\d{8,13}(?!\d)"
)
PRICE_KEYS = {"price", "unit_price", "price_tiers", "ref_idr", "price_idr", "unit_price_idr"}

# 品牌候选清单里已纠正的官方 IG。追踪名单另含 ID-11..ID-17，见 test_localradar_x。
IG_FROM_BRAND_LIST = {
    "ID-02": "@kopijanjijiwa",      # Janji Jiwa
    "ID-04": "@haus.indonesia",     # Haus
    "ID-06": "@esteh.indonesia",    # Es Teh Indonesia
    "ID-07": "@tokokopituku",       # Kopi Tuku
    "ID-10": "@guluguluid",         # Gulu Gulu
}


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _has_price(obj) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in PRICE_KEYS and value not in (None, "", [], {}):
                return True
            if _has_price(value):
                return True
    elif isinstance(obj, list):
        return any(_has_price(item) for item in obj)
    return False


def _entries(data: dict) -> list[dict]:
    found = []
    for key in ("suppliers", "items"):
        rows = data.get(key)
        if isinstance(rows, list):
            found.extend(row for row in rows if isinstance(row, dict))
    return found


def test_supplier_files_load():
    suppliers = _load(SUPPLIERS)
    prices = _load(PRICES)
    assert suppliers["suppliers"]
    assert prices["items"]
    assert prices["meta"]["generated"].startswith("2026-11-04")


def test_priced_entries_have_source_url_and_fetched_at():
    priced = 0
    for path in (SUPPLIERS, PRICES):
        for entry in _entries(_load(path)):
            if not _has_price(entry):
                continue
            priced += 1
            label = entry.get("product") or entry.get("name") or entry
            assert isinstance(entry.get("source_url"), str) and entry["source_url"].startswith("http"), label
            assert isinstance(entry.get("fetched_at"), str) and entry["fetched_at"].strip(), label
    assert priced == 27


def test_no_email_phone_or_whatsapp_link():
    for path in (SUPPLIERS, PRICES, BRAND_LIST, BRAND_LIST_REVIEW):
        text = path.read_text(encoding="utf-8")
        assert EMAIL.search(text) is None, path.name
        assert WA_LINK.search(text) is None, path.name
        assert PHONE.search(text) is None, path.name
        assert "mailto:" not in text.lower()


def test_five_ig_handles_match_brand_list():
    listed = {b["repo_id"]: b.get("ig_handle") for b in _load(BRAND_LIST)["brands"]}
    by_id = {b["id"]: b for b in BRANDS}
    assert [b["id"] for b in BRANDS] == [f"ID-{i:02d}" for i in range(1, 18)]
    published = {b["id"]: b for b in _load(PUBLISHED)["brands"]}
    for bid, handle in IG_FROM_BRAND_LIST.items():
        assert listed[bid] == handle
        assert by_id[bid]["ig"] == handle
        assert published[bid]["ig"] == handle
        assert published[bid]["provenance"]["ig"] == "demo_estimate"
        assert "ig_followers" not in published[bid]
