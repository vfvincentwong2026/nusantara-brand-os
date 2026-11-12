"""Momoyo 高密度实点扩容：取消城市 12 点上限，按 Place ID 全国去重。"""
import json
import os
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, CITIES, OUT, VERIFIED, distance_km, parse_place, save
from expand_beverage_districts import QUERIES as DISTRICTS

CITY = {c[0]: c for c in CITIES}
QUERIES = [(c[0], c[2], c[3], c[4], c[1]) for c in CITIES]
QUERIES += [(city_id, district, CITY[city_id][3], CITY[city_id][4], CITY[city_id][1]) for city_id, district in DISTRICTS]


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    offset = int(os.environ.get("QUERY_OFFSET", "0"))
    limit = int(os.environ.get("QUERY_LIMIT", str(len(QUERIES))))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for city_id, search_name, city_lat, city_lon, city in QUERIES[offset:offset + limit]:
            try:
                page.goto("https://www.google.com/maps/search/" + quote(f"Momoyo {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(1200)
                feed = page.locator("div[role='feed']")
                if feed.count():
                    stable = 0
                    previous = 0
                    for _ in range(16):
                        feed.evaluate("e => e.scrollBy(0, 3200)")
                        page.wait_for_timeout(500)
                        count = page.locator("a[href*='/maps/place/']").count()
                        stable = stable + 1 if count == previous else 0
                        previous = count
                        if stable >= 3:
                            break
                anchors = page.locator("a[href*='/maps/place/']")
                found = []
                for i in range(anchors.count()):
                    a = anchors.nth(i)
                    item = parse_place(a.get_attribute("aria-label") or "", a.get_attribute("href") or "")
                    if not item or item["google_place_id"] in seen or "momoyo" not in item["branch_name"].lower():
                        continue
                    if distance_km(city_lat, city_lon, item["lat"], item["lon"]) > 120:
                        continue
                    context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                    if "永久停业" in context or "Permanently closed" in context:
                        continue
                    item.update({"brand_id": "momoyo", "city_id": city_id, "city": city, "business_status": None})
                    found.append(item)
                    seen.add(item["google_place_id"])
                    if len(found) >= 80:
                        break
                if not found and page.locator("[data-item-id='address']").count():
                    item = parse_place(page.locator("h1").first.inner_text(), page.url)
                    if item and "momoyo" in item["branch_name"].lower() and item["google_place_id"] not in seen and distance_km(city_lat, city_lon, item["lat"], item["lon"]) <= 120:
                        item.update({"brand_id": "momoyo", "city_id": city_id, "city": city, "business_status": "永久停业" if "永久停业" in page.locator("body").inner_text() else None})
                        found.append(item)
                        seen.add(item["google_place_id"])
                payload["locations"].extend(found)
                save(payload)
                total = sum(x["brand_id"] == "momoyo" for x in payload["locations"])
                print(f"{search_name}: +{len(found)}，Momoyo 累计 {total}", flush=True)
            except Exception as exc:
                print(f"FAIL {search_name}: {str(exc)[:140]}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
