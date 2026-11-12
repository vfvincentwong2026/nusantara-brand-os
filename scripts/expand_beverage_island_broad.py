"""用整岛关键词复查区域检索零结果；按最近城镇归属，不虚构门店。"""
import json
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, OUT, VERIFIED, distance_km, parse_place, save
from expand_beverage_islands import AREAS, BRANDS

ISLANDS = [
    ("勿里洞岛", "Belitung", -2.8500, 107.9500),
    ("龙目岛", "Lombok", -8.6500, 116.4500),
    ("松巴哇岛", "Sumbawa", -8.7500, 118.0000),
    ("松巴岛", "Sumba", -9.5500, 119.7500),
]


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for island, query_island, center_lat, center_lon in ISLANDS:
            areas = [a for a in AREAS if a[5] == island]
            for brand_id, query_name in BRANDS:
                try:
                    page.goto("https://www.google.com/maps/search/" + quote(f"{query_name} {query_island} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(1200)
                    feed = page.locator("div[role='feed']")
                    if feed.count():
                        for _ in range(4):
                            feed.evaluate("e => e.scrollBy(0, 2400)")
                            page.wait_for_timeout(600)
                    anchors = page.locator("a[href*='/maps/place/']")
                    found = []
                    for i in range(anchors.count()):
                        a = anchors.nth(i)
                        item = parse_place(a.get_attribute("aria-label") or "", a.get_attribute("href") or "")
                        if not item or item["google_place_id"] in seen:
                            continue
                        nearest = min(areas, key=lambda x: distance_km(x[3], x[4], item["lat"], item["lon"]))
                        if distance_km(nearest[3], nearest[4], item["lat"], item["lon"]) > 100:
                            continue
                        context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                        if "永久停业" in context or "Permanently closed" in context:
                            continue
                        item.update({"brand_id": brand_id, "city_id": nearest[0], "city": nearest[1], "business_status": None})
                        found.append(item)
                        seen.add(item["google_place_id"])
                        if len(found) >= 20:
                            break
                    payload["locations"].extend(found)
                    save(payload)
                    print(f"{island} {query_name}: +{len(found)}", flush=True)
                except Exception as exc:
                    print(f"FAIL {island} {query_name}: {str(exc)[:140]}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
