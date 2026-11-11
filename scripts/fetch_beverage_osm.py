"""用 Nominatim 逐城市核实 Mixue/Momoyo 门店；遵循 1 req/s，失败保留城市模型。"""
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/beverage/locations_v1.json"
BRANDS = {"mixue": "Mixue", "momoyo": "Momoyo"}
CITIES = {
    "jakarta": ("雅加达", "Jakarta", (106.30, -5.70, 107.35, -6.70)),
    "surabaya": ("泗水", "Surabaya", (112.20, -6.75, 113.25, -7.75)),
    "bandung": ("万隆", "Bandung", (107.10, -6.45, 108.10, -7.35)),
    "medan": ("棉兰", "Medan", (98.15, 4.05, 99.20, 3.10)),
    "denpasar": ("登巴萨", "Denpasar", (114.70, -8.15, 115.70, -9.15)),
    "balikpapan": ("巴厘巴板", "Balikpapan", (116.35, -0.75, 117.35, -1.75)),
    "makassar": ("望加锡", "Makassar", (118.90, -4.65, 119.95, -5.65)),
    "manado": ("马那多", "Manado", (124.35, 1.95, 125.35, 0.95)),
}


def main():
    session = requests.Session()
    session.headers["User-Agent"] = "NusantaraBrandOS/1.0 (beverage location research)"
    found, misses = [], []
    for brand_id, brand in BRANDS.items():
        for city_id, (city_cn, city_en, box) in CITIES.items():
            params = {"q": f"{brand}, {city_en}, Indonesia", "format": "jsonv2", "limit": 5,
                      "bounded": 1, "viewbox": ",".join(map(str, box))}
            try:
                r = session.get("https://nominatim.openstreetmap.org/search", params=params, timeout=15)
                r.raise_for_status()
                rows = r.json()
                hit = next((x for x in rows if brand.lower() in (x.get("name", "") + " " + x.get("display_name", "")).lower()), None)
                if hit:
                    found.append({"brand_id": brand_id, "city_id": city_id, "city": city_cn,
                                  "name": hit.get("name") or hit["display_name"].split(",")[0],
                                  "lat": round(float(hit["lat"]), 6), "lon": round(float(hit["lon"]), 6),
                                  "location_precision": "osm_named_place",
                                  "location_source": f"https://www.openstreetmap.org/{hit['osm_type']}/{hit['osm_id']}",
                                  "display_name": hit["display_name"]})
                    print("OK", brand_id, city_id, found[-1]["name"], flush=True)
                else:
                    misses.append(f"{brand_id}-{city_id}")
                    print("MISS", brand_id, city_id, flush=True)
            except Exception as e:
                misses.append(f"{brand_id}-{city_id}")
                print("ERR", brand_id, city_id, type(e).__name__, flush=True)
            time.sleep(1.1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "OpenStreetMap contributors / Nominatim", "locations": found,
                               "unverified": misses}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"verified={len(found)} unresolved={len(misses)}")


if __name__ == "__main__":
    main()
