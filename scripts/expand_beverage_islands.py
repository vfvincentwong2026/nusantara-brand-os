"""补勿里洞、龙目、松巴哇、松巴岛区域实点；三品牌按 Place ID 全国去重。"""
import json
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, OUT, VERIFIED, distance_km, parse_place, save

AREAS = [
    ("tanjungpandan", "丹戎潘丹", "Tanjung Pandan Belitung", -2.7414, 107.6300, "勿里洞岛", 1.10),
    ("manggar", "曼加尔", "Manggar Belitung Timur", -2.8833, 108.2667, "勿里洞岛", 1.12),
    ("mataram", "马塔兰", "Mataram Lombok", -8.5833, 116.1167, "龙目岛", 1.10),
    ("praya", "普拉亚", "Praya Lombok Tengah", -8.7054, 116.2700, "龙目岛", 1.10),
    ("selong", "塞隆", "Selong Lombok Timur", -8.6514, 116.5370, "龙目岛", 1.12),
    ("gerung", "格隆", "Gerung Lombok Barat", -8.7230, 116.1210, "龙目岛", 1.10),
    ("mandalika", "曼达利卡", "Kuta Mandalika Lombok", -8.8950, 116.2870, "龙目岛", 1.12),
    ("sumbawa-besar", "大松巴哇", "Sumbawa Besar", -8.4930, 117.4200, "松巴哇岛", 1.12),
    ("dompu", "栋普", "Dompu Sumbawa", -8.5365, 118.4630, "松巴哇岛", 1.15),
    ("taliwang", "塔利旺", "Taliwang Sumbawa Barat", -8.7410, 116.8400, "松巴哇岛", 1.15),
    ("bima", "比马", "Bima Sumbawa", -8.4667, 118.7167, "松巴哇岛", 1.12),
    ("waingapu", "瓦英阿普", "Waingapu Sumba Timur", -9.6567, 120.2640, "松巴岛", 1.18),
    ("waikabubak", "瓦伊卡布巴克", "Waikabubak Sumba Barat", -9.6360, 119.3870, "松巴岛", 1.18),
    ("tambolaka", "坦博拉卡", "Tambolaka Sumba Barat Daya", -9.4350, 119.2360, "松巴岛", 1.20),
]
BRANDS = (("mixue", "Mixue"), ("momoyo", "Momoyo"), ("tianlala", "Tianlala"))


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    cities = {c["id"]: c for c in payload["cities"]}
    for city_id, name, search, lat, lon, island, factor in AREAS:
        cities[city_id] = {"id": city_id, "name": name, "search_name": search, "lat": lat, "lon": lon, "island": island, "factor": factor}
    payload["cities"] = list(cities.values())
    save(payload)
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for city_id, city, search_name, city_lat, city_lon, island, factor in AREAS:
            for brand_id, query_name in BRANDS:
                try:
                    page.goto("https://www.google.com/maps/search/" + quote(f"{query_name} {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(1200)
                    feed = page.locator("div[role='feed']")
                    if feed.count():
                        for _ in range(3):
                            feed.evaluate("e => e.scrollBy(0, 2400)")
                            page.wait_for_timeout(600)
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
                        if len(found) >= 12:
                            break
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
                    print(f"FAIL {city} {query_name}: {str(exc)[:140]}", flush=True)
        browser.close()
    print(f"DONE {len(payload['locations'])} additional stores")


if __name__ == "__main__":
    main()
