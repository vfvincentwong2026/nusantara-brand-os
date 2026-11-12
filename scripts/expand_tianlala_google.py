"""采集甜啦啦 Google Maps 实点；Place ID 全国去重，并覆盖 8 个基础城市模型点。"""
import json
import os
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, CITIES, OUT, VERIFIED, distance_km, parse_place, save


def promote_base_cities(payload):
    """每个基础城市选首个已核验点，替换该城市的展示模型点。"""
    verified = json.loads(VERIFIED.read_text(encoding="utf-8"))
    by_key = {(x["brand_id"], x["city_id"]): x for x in verified["locations"]}
    for city_id, *_ in CITIES[:8]:
        item = next((x for x in payload["locations"] if x["brand_id"] == "tianlala" and x["city_id"] == city_id), None)
        if item:
            by_key[("tianlala", city_id)] = dict(item)
    verified["locations"] = list(by_key.values())
    VERIFIED.write_text(json.dumps(verified, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    offset = int(os.environ.get("CITY_OFFSET", "0"))
    limit = int(os.environ.get("CITY_LIMIT", "60"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for city_id, city, search_name, city_lat, city_lon, factor in CITIES[offset:offset + limit]:
            try:
                page.goto("https://www.google.com/maps/search/" + quote(f"Tianlala {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
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
                    item.update({"brand_id": "tianlala", "city_id": city_id, "city": city, "business_status": None})
                    found.append(item)
                    seen.add(item["google_place_id"])
                    if len(found) >= (16 if city_id == "jakarta" else 12):
                        break
                if not found and page.locator("[data-item-id='address']").count():
                    item = parse_place(page.locator("h1").first.inner_text(), page.url)
                    if item and item["google_place_id"] not in seen and distance_km(city_lat, city_lon, item["lat"], item["lon"]) <= 120:
                        item.update({"brand_id": "tianlala", "city_id": city_id, "city": city, "business_status": "永久停业" if "永久停业" in page.locator("body").inner_text() else None})
                        found.append(item)
                        seen.add(item["google_place_id"])
                payload["locations"].extend(found)
                save(payload)
                promote_base_cities(payload)
                total = sum(x["brand_id"] == "tianlala" for x in payload["locations"])
                print(f"{city} Tianlala: +{len(found)}，甜啦啦累计 {total}", flush=True)
            except Exception as exc:
                print(f"FAIL {city} Tianlala: {str(exc)[:150]}", flush=True)
        browser.close()
    print(f"DONE {sum(x['brand_id'] == 'tianlala' for x in payload['locations'])} Tianlala stores")


if __name__ == "__main__":
    main()
