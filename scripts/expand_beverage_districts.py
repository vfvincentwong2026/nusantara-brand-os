"""按重点城市行政区继续补蜜雪/Momoyo门店，Place ID 全国去重。"""
import json
import os
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, OUT, VERIFIED, distance_km, parse_place, save

QUERIES = [
    ("jakarta", "Jakarta Pusat"), ("jakarta", "Jakarta Selatan"), ("jakarta", "Jakarta Timur"),
    ("jakarta", "Jakarta Barat"), ("jakarta", "Jakarta Utara"),
    ("surabaya", "Surabaya Pusat"), ("surabaya", "Surabaya Timur"), ("surabaya", "Surabaya Barat"),
    ("surabaya", "Surabaya Utara"), ("surabaya", "Surabaya Selatan"),
    ("bandung", "Bandung Wetan"), ("bandung", "Coblong Bandung"), ("bandung", "Cicendo Bandung"),
    ("bandung", "Buahbatu Bandung"), ("bandung", "Antapani Bandung"),
    ("medan", "Medan Kota"), ("medan", "Medan Selayang"), ("medan", "Medan Sunggal"), ("medan", "Medan Marelan"),
    ("semarang", "Semarang Tengah"), ("semarang", "Semarang Timur"), ("semarang", "Semarang Barat"), ("semarang", "Tembalang"),
    ("yogyakarta", "Sleman"), ("yogyakarta", "Yogyakarta City"), ("yogyakarta", "Depok Sleman"), ("yogyakarta", "Bantul"),
    ("makassar", "Panakkukang Makassar"), ("makassar", "Rappocini Makassar"),
    ("makassar", "Tamalanrea Makassar"), ("makassar", "Ujung Pandang Makassar"),
    ("denpasar", "Denpasar Barat"), ("denpasar", "Denpasar Timur"), ("denpasar", "Denpasar Selatan"), ("denpasar", "Kuta Bali"),
    ("palembang", "Palembang Ilir"), ("palembang", "Palembang Ulu"), ("palembang", "Sukarami Palembang"),
    ("pekanbaru", "Pekanbaru Kota"), ("pekanbaru", "Sukajadi Pekanbaru"), ("pekanbaru", "Marpoyan Damai"),
    ("balikpapan", "Balikpapan Kota"), ("balikpapan", "Balikpapan Timur"), ("balikpapan", "Balikpapan Selatan"),
    ("batam", "Batam Kota"), ("batam", "Lubuk Baja"), ("batam", "Nagoya Batam"),
    ("pontianak", "Pontianak Kota"), ("pontianak", "Pontianak Selatan"), ("pontianak", "Pontianak Timur"),
    ("banjarmasin", "Banjarmasin Tengah"), ("banjarmasin", "Banjarmasin Timur"), ("banjarmasin", "Banjarmasin Selatan"),
]
TARGET = 1000


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    cities = {c["id"]: c for c in payload["cities"]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        stop = False
        query_offset = int(os.environ.get("QUERY_OFFSET", "0"))
        for city_id, district in QUERIES[query_offset:]:
            if stop:
                break
            city = cities[city_id]
            for brand_id, name in (("mixue", "Mixue"), ("momoyo", "Momoyo")):
                try:
                    query = f"{name} {district} Indonesia"
                    page.goto("https://www.google.com/maps/search/" + quote(query), wait_until="domcontentloaded", timeout=40000)
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
                        if distance_km(city["lat"], city["lon"], item["lat"], item["lon"]) > 120:
                            continue
                        context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                        if "永久停业" in context or "Permanently closed" in context:
                            continue
                        item.update({"brand_id": brand_id, "city_id": city_id, "city": city["name"], "business_status": None, "search_district": district})
                        found.append(item)
                        seen.add(item["google_place_id"])
                        if len(found) >= 12:
                            break
                    payload["locations"].extend(found)
                    save(payload)
                    print(f"{district} {name}: +{len(found)}，累计 {len(payload['locations'])}", flush=True)
                    if len(payload["locations"]) >= TARGET:
                        stop = True
                        break
                except Exception as exc:
                    print(f"FAIL {district} {name}: {str(exc)[:140]}", flush=True)
        browser.close()
    print(f"DONE {len(payload['locations'])} additional stores")


if __name__ == "__main__":
    main()
