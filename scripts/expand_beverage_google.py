"""批量扩展 Mixue / Momoyo 的 Google Maps 真实门店点，不触碰其他品牌。

坐标只取搜索结果地点 URL 的 !3d/!4d；按 Place ID 全国去重。
运行：python scripts/expand_beverage_google.py
"""
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/beverage/google_locations_bulk_v1.json"
VERIFIED = ROOT / "data/beverage/google_locations_v1.json"
CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
CITIES = [
    ("jakarta", "雅加达", "Jakarta", -6.2088, 106.8456, 1.00),
    ("surabaya", "泗水", "Surabaya", -7.2575, 112.7521, 1.02),
    ("bandung", "万隆", "Bandung", -6.9175, 107.6191, 1.00),
    ("medan", "棉兰", "Medan", 3.5952, 98.6722, 1.08),
    ("denpasar", "登巴萨", "Denpasar", -8.6705, 115.2126, 1.06),
    ("balikpapan", "巴厘巴板", "Balikpapan", -1.2379, 116.8529, 1.12),
    ("makassar", "望加锡", "Makassar", -5.1477, 119.4327, 1.10),
    ("manado", "马那多", "Manado", 1.4748, 124.8421, 1.15),
    ("semarang", "三宝垄", "Semarang", -6.9667, 110.4167, 1.01),
    ("yogyakarta", "日惹", "Yogyakarta", -7.7956, 110.3695, 1.01),
    ("malang", "玛琅", "Malang", -7.9797, 112.6304, 1.02),
    ("bogor", "茂物", "Bogor", -6.5971, 106.8060, 1.00),
    ("bekasi", "勿加泗", "Bekasi", -6.2383, 106.9756, 1.00),
    ("tangerang", "丹格朗", "Tangerang", -6.1783, 106.6319, 1.00),
    ("depok", "德波", "Depok", -6.4025, 106.7942, 1.00),
    ("palembang", "巨港", "Palembang", -2.9761, 104.7754, 1.08),
    ("pekanbaru", "北干巴鲁", "Pekanbaru", 0.5071, 101.4478, 1.08),
    ("bandar-lampung", "楠榜", "Bandar Lampung", -5.4292, 105.2610, 1.07),
    ("pontianak", "坤甸", "Pontianak", -0.0263, 109.3425, 1.10),
    ("banjarmasin", "马辰", "Banjarmasin", -3.3186, 114.5944, 1.10),
    ("samarinda", "沙马林达", "Samarinda", -0.5022, 117.1536, 1.12),
    ("padang", "巴东", "Padang", -0.9471, 100.4172, 1.08),
    ("batam", "巴淡", "Batam", 1.0821, 104.0305, 1.08),
    ("kupang", "古邦", "Kupang", -10.1772, 123.6070, 1.15),
    ("jayapura", "查亚普拉", "Jayapura", -2.5916, 140.6690, 1.18),
]


def distance_km(a_lat, a_lon, b_lat, b_lon):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def parse_place(name, url):
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    place_id = re.search(r"!1s([^!]+)", url)
    if not match or not place_id:
        return None
    return {
        "branch_name": name.strip(),
        "address": None,
        "lat": float(match.group(1)),
        "lon": float(match.group(2)),
        "google_url": url,
        "google_place_id": place_id.group(1),
        "coordinate_basis": "Google Maps 搜索结果地点 URL !3d/!4d",
    }


def save(payload):
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "source": "Google Maps 城市搜索结果地点页；按 Place ID 去重",
        "verified_at": "2026-11-12",
        "cities": [{"id": c[0], "name": c[1], "search_name": c[2], "lat": c[3], "lon": c[4], "factor": c[5]} for c in CITIES],
        "locations": [],
    }
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for city_id, city, search_name, city_lat, city_lon, factor in CITIES:
            for brand_id, query_name in (("mixue", "Mixue"), ("momoyo", "Momoyo")):
                before = len(payload["locations"])
                try:
                    page.goto("https://www.google.com/maps/search/" + quote(f"{query_name} {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(1300)
                    feed = page.locator("div[role='feed']")
                    if feed.count():
                        for _ in range(2):
                            feed.evaluate("e => e.scrollBy(0, 2400)")
                            page.wait_for_timeout(650)
                    anchors = page.locator("a[href*='/maps/place/']")
                    found = []
                    for i in range(anchors.count()):
                        a = anchors.nth(i)
                        item = parse_place(a.get_attribute("aria-label") or "", a.get_attribute("href") or "")
                        if not item or item["google_place_id"] in seen:
                            continue
                        if distance_km(city_lat, city_lon, item["lat"], item["lon"]) > 120:
                            continue
                        context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                        if "永久停业" in context or "Permanently closed" in context:
                            continue
                        item.update({"brand_id": brand_id, "city_id": city_id, "city": city, "business_status": None})
                        found.append(item)
                        seen.add(item["google_place_id"])
                        if len(found) >= (12 if city_id == "jakarta" else 8):
                            break
                    # 单一结果时直接读地点页。
                    if not found and page.locator("[data-item-id='address']").count():
                        item = parse_place(page.locator("h1").first.inner_text(), page.url)
                        if item and item["google_place_id"] not in seen and distance_km(city_lat, city_lon, item["lat"], item["lon"]) <= 120:
                            item.update({"brand_id": brand_id, "city_id": city_id, "city": city, "business_status": "永久停业" if "永久停业" in page.locator("body").inner_text() else None})
                            found.append(item)
                            seen.add(item["google_place_id"])
                    payload["locations"].extend(found)
                    save(payload)
                    print(f"{city} {query_name}: +{len(found)}，累计 {len(payload['locations'])}", flush=True)
                except Exception as exc:
                    print(f"FAIL {city} {query_name}: {str(exc)[:150]}", flush=True)
        browser.close()
    print(f"DONE {len(payload['locations'])} additional stores -> {OUT}")


if __name__ == "__main__":
    main()
