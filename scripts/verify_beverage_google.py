"""用真实 Chrome 核验当前命名门店；仅接受 Google 地点页 !3d/!4d 坐标。

运行：python scripts/verify_beverage_google.py
默认只处理 google_locations_v1.json 中尚未覆盖的 OSM 候选点。
"""
import json
import math
import re
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OSM_PATH = ROOT / "data/beverage/locations_v1.json"
OUT_PATH = ROOT / "data/beverage/google_locations_v1.json"
CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
QUERIES = {
    ("mixue", "bandung"): "Mixue Antapani Jl Terusan Jakarta No 92 Bandung",
    ("mixue", "denpasar"): "Mixue Gatot Subroto Denpasar Bali",
    ("mixue", "makassar"): "Mixue Biringkanaya Jl Pajaiang Makassar",
    ("mixue", "manado"): "Mixue Sam Ratulangi Manado",
    ("momoyo", "bandung"): "Momoyo Ujungberung Abdul Haris Nasution Bandung",
    ("momoyo", "medan"): "Momoyo Medan Marelan",
    ("momoyo", "makassar"): "Momoyo Somba Opu Makassar",
}


def distance_m(a_lat, a_lon, b_lat, b_lon):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def coords(url):
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    return (float(match.group(1)), float(match.group(2))) if match else None


def place_details(page, share_url=None):
    url = page.url
    point = coords(url)
    if not point:
        return None
    heading = page.locator("h1").first.inner_text().strip()
    address_node = page.locator("[data-item-id='address']").first
    address = address_node.get_attribute("aria-label") or "" if address_node.count() else ""
    address = re.sub(r"^地址:\s*", "", address).strip()
    place_id = re.search(r"!1s([^!]+)", url)
    return {
        "branch_name": heading,
        "address": address,
        "lat": point[0],
        "lon": point[1],
        "google_url": url,
        "google_place_id": place_id.group(1) if place_id else None,
        "google_share_url": share_url,
        "business_status": "永久停业" if "永久停业" in page.locator("body").inner_text() else None,
    }


def verify_one(page, item):
    query = QUERIES.get((item["brand_id"], item["city_id"]), item["display_name"])
    page.goto("https://www.google.com/maps/search/" + quote(query), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_selector("h1", timeout=20000)
    page.wait_for_timeout(1000)
    detail = place_details(page)
    if detail is None and page.locator("[data-item-id='address']").count():
        # 部分地点页停留在 search URL：从 Google 分享弹窗取短链，再解析地点页精确坐标。
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
        page.locator("button[aria-label='分享']").first.click()
        page.get_by_role("button", name="Copy Link").wait_for(timeout=10000)
        page.get_by_role("button", name="Copy Link").click()
        page.wait_for_timeout(600)
        share_url = page.evaluate("navigator.clipboard.readText()")
        if not share_url.startswith("https://maps.app.goo.gl/"):
            raise RuntimeError("Google 分享弹窗未返回门店短链")
        page.goto(share_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_selector("h1", timeout=20000)
        page.wait_for_timeout(700)
        detail = place_details(page, share_url)
    if detail is None or detail["branch_name"] == "结果":
        anchors = page.locator("a[href*='/maps/place/']")
        candidates = []
        for i in range(min(anchors.count(), 12)):
            href = anchors.nth(i).get_attribute("href") or ""
            point = coords(href)
            if point:
                candidates.append((distance_m(item["lat"], item["lon"], *point), href))
        if not candidates:
            raise RuntimeError("没有带精确坐标的 Google 地点结果")
        distance, href = min(candidates)
        if distance > 500:
            raise RuntimeError(f"最近 Google 结果距 OSM {distance:.0f} 米，拒绝自动匹配")
        page.goto(href, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_selector("h1", timeout=20000)
        page.wait_for_timeout(700)
        detail = place_details(page)
    if not detail or not detail["google_place_id"] or not detail["address"]:
        raise RuntimeError("Google 地点页缺少坐标、Place ID 或地址")
    distance = distance_m(item["lat"], item["lon"], detail["lat"], detail["lon"])
    if distance > 500:
        raise RuntimeError(f"地点页距 OSM {distance:.0f} 米，拒绝自动匹配")
    return detail, round(distance)


def main():
    osm = json.loads(OSM_PATH.read_text(encoding="utf-8"))["locations"]
    existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    verified = {(x["brand_id"], x["city_id"]): x for x in existing["locations"]}
    missing = [x for x in osm if (x["brand_id"], x["city_id"]) not in verified]
    print(f"待核验 {len(missing)} 点")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        for item in missing:
            key = (item["brand_id"], item["city_id"])
            page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
            try:
                detail, distance = verify_one(page, item)
                verified[key] = {"brand_id": item["brand_id"], "city_id": item["city_id"], **detail}
                print("OK", "-".join(key), detail["branch_name"], detail["lat"], detail["lon"], f"距OSM {distance}m")
            except Exception as exc:
                print("FAIL", "-".join(key), str(exc)[:180], page.title(), page.url[:160])
                print("PAGE", page.locator("body").inner_text()[:240].replace("\n", " | "))
            page.close()
        browser.close()
    ordered = [verified[(x["brand_id"], x["city_id"])] for x in osm if (x["brand_id"], x["city_id"]) in verified]
    OUT_PATH.write_text(json.dumps({**existing, "locations": ordered}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存 {len(ordered)}/{len(osm)} 点 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
