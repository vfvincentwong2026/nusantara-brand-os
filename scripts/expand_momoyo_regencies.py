"""补 Momoyo 未覆盖重点城市与县域；门店坐标只取 Google 地点 URL。"""
import json
import os
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from expand_beverage_google import CHROME, OUT, VERIFIED, distance_km, parse_place, save

AREAS = [
    ("binjai", "宾贾伊", "Binjai", 3.5901, 98.4856, "苏门答腊", 1.08),
    ("bukittinggi", "武吉丁宜", "Bukittinggi", -0.3050, 100.3690, "苏门答腊", 1.08),
    ("padang-panjang", "巴东班让", "Padang Panjang", -0.4630, 100.3980, "苏门答腊", 1.08),
    ("payakumbuh", "帕亚孔布", "Payakumbuh", -0.2290, 100.6330, "苏门答腊", 1.08),
    ("muaro-jambi", "穆阿罗占碑", "Muaro Jambi", -1.6000, 103.6000, "苏门答腊", 1.08),
    ("prabumulih", "普拉布穆利", "Prabumulih", -3.4320, 104.2350, "苏门答腊", 1.08),
    ("lahat", "拉哈特", "Lahat", -3.8000, 103.5330, "苏门答腊", 1.10),
    ("metro-lampung", "梅特罗", "Metro Lampung", -5.1130, 105.3060, "苏门答腊", 1.07),
    ("cirebon", "井里汶", "Cirebon", -6.7320, 108.5520, "爪哇", 1.01),
    ("indramayu", "因德拉马尤", "Indramayu", -6.3270, 108.3190, "爪哇", 1.01),
    ("karawang", "加拉璜", "Karawang", -6.3030, 107.3020, "爪哇", 1.00),
    ("purwakarta", "普哇加达", "Purwakarta", -6.5560, 107.4430, "爪哇", 1.00),
    ("subang", "梳邦", "Subang", -6.5710, 107.7590, "爪哇", 1.01),
    ("cianjur", "展玉", "Cianjur", -6.8170, 107.1420, "爪哇", 1.00),
    ("garut", "加鲁特", "Garut", -7.2270, 107.9080, "爪哇", 1.01),
    ("ciamis", "芝亚米斯", "Ciamis", -7.3260, 108.3530, "爪哇", 1.01),
    ("pekalongan", "北加浪岸", "Pekalongan", -6.8880, 109.6750, "爪哇", 1.01),
    ("kudus", "古突士", "Kudus", -6.8040, 110.8410, "爪哇", 1.01),
    ("jepara", "哲帕拉", "Jepara", -6.5890, 110.6680, "爪哇", 1.01),
    ("magelang", "马格朗", "Magelang", -7.4790, 110.2170, "爪哇", 1.01),
    ("salatiga", "沙拉迪加", "Salatiga", -7.3300, 110.5080, "爪哇", 1.01),
    ("klaten", "克拉登", "Klaten", -7.7050, 110.6060, "爪哇", 1.01),
    ("cilacap", "芝拉扎", "Cilacap", -7.7180, 109.0150, "爪哇", 1.01),
    ("kebumen", "克布门", "Kebumen", -7.6690, 109.6600, "爪哇", 1.01),
    ("sidoarjo", "诗都阿佐", "Sidoarjo", -7.4470, 112.7180, "爪哇", 1.02),
    ("gresik", "格雷西", "Gresik", -7.1560, 112.6560, "爪哇", 1.02),
    ("mojokerto", "莫佐克托", "Mojokerto", -7.4720, 112.4330, "爪哇", 1.02),
    ("kediri", "谏义里", "Kediri", -7.8160, 112.0110, "爪哇", 1.02),
    ("blitar", "勿里达", "Blitar", -8.0950, 112.1680, "爪哇", 1.02),
    ("tulungagung", "图隆阿贡", "Tulungagung", -8.0660, 111.9020, "爪哇", 1.02),
    ("jember", "任抹", "Jember", -8.1840, 113.7030, "爪哇", 1.02),
    ("banyuwangi", "外南梦", "Banyuwangi", -8.2190, 114.3690, "爪哇", 1.02),
    ("bangkalan", "邦卡兰", "Bangkalan Madura", -7.0300, 112.7450, "马都拉岛", 1.02),
    ("pamekasan", "巴米加三", "Pamekasan Madura", -7.1560, 113.4820, "马都拉岛", 1.02),
    ("ketapang", "吉打邦", "Ketapang Kalimantan", -1.8590, 109.9810, "加里曼丹", 1.10),
    ("sampit", "桑皮特", "Sampit", -2.5320, 112.9500, "加里曼丹", 1.10),
    ("pangkalan-bun", "庞卡兰布恩", "Pangkalan Bun", -2.6830, 111.6250, "加里曼丹", 1.10),
    ("banjarbaru", "班贾尔巴鲁", "Banjarbaru", -3.4420, 114.8310, "加里曼丹", 1.10),
    ("bontang", "邦唐", "Bontang", 0.1330, 117.5000, "加里曼丹", 1.12),
    ("bitung", "比通", "Bitung", 1.4450, 125.1820, "苏拉威西", 1.15),
    ("palopo", "帕洛波", "Palopo", -3.0000, 120.2000, "苏拉威西", 1.12),
    ("parepare", "巴里巴里", "Parepare", -4.0160, 119.6230, "苏拉威西", 1.12),
]


def main():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    cities = {c["id"]: c for c in payload["cities"]}
    for city_id, name, search, lat, lon, island, factor in AREAS:
        cities[city_id] = {"id": city_id, "name": name, "search_name": search, "lat": lat, "lon": lon, "island": island, "factor": factor}
    payload["cities"] = list(cities.values())
    save(payload)
    original = json.loads(VERIFIED.read_text(encoding="utf-8"))["locations"]
    seen = {x["google_place_id"] for x in original} | {x["google_place_id"] for x in payload["locations"]}
    offset = int(os.environ.get("REGENCY_OFFSET", "0"))
    limit = int(os.environ.get("REGENCY_LIMIT", str(len(AREAS))))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        for city_id, city, search_name, city_lat, city_lon, island, factor in AREAS[offset:offset + limit]:
            try:
                page.goto("https://www.google.com/maps/search/" + quote(f"Momoyo {search_name} Indonesia"), wait_until="domcontentloaded", timeout=40000)
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
                    if distance_km(city_lat, city_lon, item["lat"], item["lon"]) > 100:
                        continue
                    context = a.evaluate("a => (a.closest('[role=article]') || a.parentElement?.parentElement)?.innerText || ''")
                    if "永久停业" in context or "Permanently closed" in context:
                        continue
                    item.update({"brand_id": "momoyo", "city_id": city_id, "city": city, "business_status": None})
                    found.append(item)
                    seen.add(item["google_place_id"])
                    if len(found) >= 80:
                        break
                payload["locations"].extend(found)
                save(payload)
                total = sum(x["brand_id"] == "momoyo" for x in payload["locations"])
                print(f"{search_name}: +{len(found)}，Momoyo 累计 {total}", flush=True)
            except Exception as exc:
                print(f"FAIL {search_name}: {str(exc)[:140]}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
