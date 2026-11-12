"""按印尼 34 省补 Momoyo 县域实点，结果归入最近已覆盖城镇。"""
import json
import os
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, CITIES, OUT, VERIFIED, distance_km, parse_place, save
from expand_beverage_islands import AREAS

CITY = {c[0]: (c[0], c[1], c[3], c[4]) for c in CITIES}
CITY.update({a[0]: (a[0], a[1], a[3], a[4]) for a in AREAS})
PROVINCES = [
    ("Aceh", ["banda-aceh", "lhokseumawe"]),
    ("Sumatera Utara", ["medan", "padang-sidempuan", "pematang-siantar"]),
    ("Sumatera Barat", ["padang"]), ("Riau", ["pekanbaru"]),
    ("Kepulauan Riau", ["batam", "tanjung-pinang"]), ("Jambi", ["jambi"]),
    ("Sumatera Selatan", ["palembang", "lubuklinggau"]), ("Bengkulu", ["bengkulu"]),
    ("Lampung", ["bandar-lampung"]), ("Kepulauan Bangka Belitung", ["tanjungpandan", "manggar"]),
    ("DKI Jakarta", ["jakarta"]),
    ("Jawa Barat", ["bandung", "bogor", "bekasi", "depok", "sukabumi", "tasikmalaya"]),
    ("Banten", ["serang", "cilegon", "tangerang"]),
    ("Jawa Tengah", ["semarang", "surakarta", "tegal", "purwokerto"]),
    ("DI Yogyakarta", ["yogyakarta"]),
    ("Jawa Timur", ["surabaya", "malang", "madiun", "probolinggo", "pasuruan"]),
    ("Bali", ["denpasar", "singaraja"]),
    ("Nusa Tenggara Barat", ["mataram", "praya", "selong", "gerung", "mandalika", "sumbawa-besar", "dompu", "taliwang", "bima"]),
    ("Nusa Tenggara Timur", ["kupang", "waingapu", "waikabubak", "tambolaka"]),
    ("Kalimantan Barat", ["pontianak", "singkawang"]), ("Kalimantan Tengah", ["palangkaraya"]),
    ("Kalimantan Selatan", ["banjarmasin"]), ("Kalimantan Timur", ["balikpapan", "samarinda"]),
    ("Kalimantan Utara", ["tarakan"]), ("Sulawesi Utara", ["manado"]),
    ("Gorontalo", ["gorontalo"]), ("Sulawesi Tengah", ["palu", "luwuk"]),
    ("Sulawesi Barat", ["mamuju"]), ("Sulawesi Selatan", ["makassar"]),
    ("Sulawesi Tenggara", ["kendari", "baubau"]), ("Maluku", ["ambon"]),
    ("Maluku Utara", ["ternate"]), ("Papua", ["jayapura"]),
    ("Papua Tengah", ["timika"]), ("Papua Selatan", ["merauke"]),
]


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    offset = int(os.environ.get("PROVINCE_OFFSET", "0"))
    limit = int(os.environ.get("PROVINCE_LIMIT", str(len(PROVINCES))))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for province, city_ids in PROVINCES[offset:offset + limit]:
            try:
                page.goto("https://www.google.com/maps/search/" + quote(f"Momoyo {province} Indonesia"), wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(1200)
                feed = page.locator("div[role='feed']")
                if feed.count():
                    for _ in range(16):
                        feed.evaluate("e => e.scrollBy(0, 3200)")
                        page.wait_for_timeout(450)
                anchors = page.locator("a[href*='/maps/place/']")
                found = []
                for i in range(anchors.count()):
                    a = anchors.nth(i)
                    item = parse_place(a.get_attribute("aria-label") or "", a.get_attribute("href") or "")
                    if not item or item["google_place_id"] in seen or "momoyo" not in item["branch_name"].lower():
                        continue
                    nearest = min((CITY[x] for x in city_ids), key=lambda c: distance_km(c[2], c[3], item["lat"], item["lon"]))
                    if distance_km(nearest[2], nearest[3], item["lat"], item["lon"]) > 180:
                        continue
                    context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                    if "永久停业" in context or "Permanently closed" in context:
                        continue
                    item.update({"brand_id": "momoyo", "city_id": nearest[0], "city": nearest[1], "business_status": None, "search_province": province})
                    found.append(item)
                    seen.add(item["google_place_id"])
                    if len(found) >= 100:
                        break
                payload["locations"].extend(found)
                save(payload)
                total = sum(x["brand_id"] == "momoyo" for x in payload["locations"])
                print(f"{province}: +{len(found)}，Momoyo 累计 {total}", flush=True)
            except Exception as exc:
                print(f"FAIL {province}: {str(exc)[:140]}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
