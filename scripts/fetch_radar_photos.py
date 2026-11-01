"""雷达配图：从 Wikipedia / Wikimedia Commons 抓真实门店/品牌图，存到 web/assets/radar/。

用法：python scripts/fetch_radar_photos.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web/assets/radar"
UA = {"User-Agent": "NusantaraBrandOS-RadarBot/1.0 (demo; contact: local)"}

QUERIES = {
    # 品牌榜
    "ID-01": ["Kopi Kenangan", "en"], "ID-02": ["Kopi Janji Jiwa", "id"],
    "ID-03": ["Fore Coffee", "id"], "ID-04": ["Haus! Indonesia", "id"],
    "ID-05": ["Richeese Factory", "id"], "ID-06": ["Es Teh Indonesia", "id"],
    "ID-07": ["Kopi Tuku", "id"], "ID-08": ["Sour Sally", "id"],
    "ID-09": ["Roti'O", "id"], "ID-10": ["Gulu Gulu", "id"],
    # 潜力小店
    "SH-01": ["Sate Kambing H. Diding", "id"], "SH-02": ["Seblak", "id"],
    "SH-03": ["Ayam gepuk", "id"], "SH-04": ["Pisang goreng", "id"],
    "SH-05": ["Nasi goreng kambing", "id"], "SH-06": ["Kwetiau", "id"],
    "SH-07": ["Soto lamongan", "id"], "SH-08": ["Bubur ayam", "id"],
    "SH-09": ["Pempek", "id"], "SH-10": ["Rujak cingur", "id"],
}


def get(url: str) -> dict | None:
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(1.2)
    return None


def search_image(query: str, lang: str) -> str | None:
    api = f"https://{lang}.wikipedia.org/w/api.php"
    # 1) 直接 summary
    title = query.replace(" ", "_")
    d = get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}")
    if d and d.get("thumbnail", {}).get("source"):
        return d["thumbnail"]["source"]
    # 2) 搜索最佳条目
    d = get(f"{api}?action=query&format=json&list=search&srlimit=1&srsearch={urllib.parse.quote(query)}")
    hits = (d or {}).get("query", {}).get("search", [])
    if not hits:
        return None
    page = hits[0]["title"]
    d = get(f"{api}?action=query&format=json&prop=pageimages&piprop=thumbnail&pithumbsize=900"
            f"&titles={urllib.parse.quote(page)}")
    pages = (d or {}).get("query", {}).get("pages", {})
    for v in pages.values():
        if v.get("thumbnail", {}).get("source"):
            return v["thumbnail"]["source"]
    return None


def download(url: str, path: Path) -> bool:
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if len(data) < 3000:
                return False
            path.write_bytes(data)
            return True
        except Exception:
            time.sleep(1.2)
    return False


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ok, miss = [], []
    for eid, (query, lang) in QUERIES.items():
        dest = OUT / f"{eid}.jpg"
        if dest.exists() and dest.stat().st_size > 3000:
            ok.append(eid)
            continue
        img = search_image(query, lang)
        if img and download(img, dest):
            ok.append(eid)
        else:
            # 回退：Commons 搜索
            d = get("https://commons.wikimedia.org/w/api.php?action=query&format=json"
                    "&generator=search&gsrnamespace=6&gsrlimit=1"
                    f"&gsrsearch={urllib.parse.quote(query)}&prop=imageinfo"
                    "&iiprop=url&iiurlwidth=900")
            pages = (d or {}).get("query", {}).get("pages", {})
            hit = next(iter(pages.values()), None)
            thumb = (hit or {}).get("imageinfo", [{}])[0].get("thumburl")
            if thumb and download(thumb, dest):
                ok.append(eid)
            else:
                miss.append(eid)
        time.sleep(1.0)
    print(json.dumps({"ok": len(ok), "miss": miss}, ensure_ascii=False))


if __name__ == "__main__":
    main()
