"""批量扩展 Mixue / Momoyo 的 Google Maps 真实门店点，不触碰其他品牌。

坐标只取搜索结果地点 URL 的 !3d/!4d；按 Place ID 全国去重。
运行：python scripts/expand_beverage_google.py
"""
import json
import math
import os
import re
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
    ("surakarta", "梭罗", "Surakarta", -7.5667, 110.8167, 1.01),
    ("mataram", "马塔兰", "Mataram", -8.5833, 116.1167, 1.10),
    ("jambi", "占碑", "Jambi", -1.6101, 103.6131, 1.08),
    ("bengkulu", "明古鲁", "Bengkulu", -3.8004, 102.2655, 1.10),
    ("gorontalo", "哥伦打洛", "Gorontalo", 0.5412, 123.0595, 1.12),
    ("palu", "帕卢", "Palu", -0.8917, 119.8707, 1.12),
    ("kendari", "肯达里", "Kendari", -3.9985, 122.5129, 1.12),
    ("ambon", "安汶", "Ambon", -3.6954, 128.1814, 1.18),
    ("ternate", "特尔纳特", "Ternate", 0.7930, 127.3840, 1.18),
    ("sorong", "索龙", "Sorong", -0.8762, 131.2558, 1.20),
    ("tegal", "直葛", "Tegal", -6.8794, 109.1256, 1.01),
    ("purwokerto", "普禾加多", "Purwokerto", -7.4314, 109.2478, 1.01),
    ("madiun", "茉莉芬", "Madiun", -7.6298, 111.5239, 1.02),
    ("probolinggo", "庞越", "Probolinggo", -7.7543, 113.2159, 1.02),
    ("pasuruan", "岩望", "Pasuruan", -7.6453, 112.9075, 1.02),
    ("tasikmalaya", "打横", "Tasikmalaya", -7.3506, 108.2172, 1.01),
    ("sukabumi", "苏加武眉", "Sukabumi", -6.9277, 106.9270, 1.00),
    ("serang", "西冷", "Serang", -6.1149, 106.1502, 1.00),
    ("cilegon", "芝勒贡", "Cilegon", -6.0023, 106.0112, 1.00),
    ("lubuklinggau", "卢布林高", "Lubuklinggau", -3.2967, 102.8614, 1.08),
    ("padang-sidempuan", "巴东塞德姆普安", "Padang Sidempuan", 1.3804, 99.2684, 1.10),
    ("pematang-siantar", "先达", "Pematangsiantar", 2.9595, 99.0687, 1.08),
    ("banda-aceh", "班达亚齐", "Banda Aceh", 5.5483, 95.3238, 1.12),
    ("lhokseumawe", "洛克苏马韦", "Lhokseumawe", 5.1801, 97.1507, 1.12),
    ("tanjung-pinang", "丹戎槟榔", "Tanjung Pinang", 0.9186, 104.4554, 1.10),
    ("singkawang", "山口洋", "Singkawang", 0.9088, 108.9846, 1.10),
    ("palangkaraya", "帕朗卡拉亚", "Palangkaraya", -2.2096, 113.9213, 1.10),
    ("tarakan", "打拉根", "Tarakan", 3.3000, 117.6000, 1.15),
    ("mamuju", "马穆朱", "Mamuju", -2.6740, 118.8880, 1.12),
    ("luwuk", "卢武克", "Luwuk", -0.9516, 122.7880, 1.15),
    ("baubau", "包包", "Baubau", -5.4667, 122.6167, 1.15),
    ("bima", "比马", "Bima", -8.4667, 118.7167, 1.12),
    ("singaraja", "新加拉惹", "Singaraja", -8.1167, 115.0833, 1.08),
    ("timika", "蒂米卡", "Timika", -4.5467, 136.8833, 1.20),
    ("merauke", "马老奇", "Merauke", -8.4667, 140.4000, 1.20),
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
    known_cities = {c["id"] for c in payload["cities"]}
    payload["cities"].extend({"id": c[0], "name": c[1], "search_name": c[2], "lat": c[3], "lon": c[4], "factor": c[5]} for c in CITIES if c[0] not in known_cities)
    save(payload)
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        city_offset = int(os.environ.get("CITY_OFFSET", "0"))
        for city_id, city, search_name, city_lat, city_lon, factor in CITIES[city_offset:]:
            for brand_id, query_name in (("mixue", "Mixue"), ("momoyo", "Momoyo")):
                try:
                    page.goto("https://www.google.com/maps/search/" + quote(f"{query_name} {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(1300)
                    feed = page.locator("div[role='feed']")
                    if feed.count():
                        for _ in range(3):
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
                        if len(found) >= (16 if city_id == "jakarta" else 12):
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
