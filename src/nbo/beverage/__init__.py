"""茶饮咖啡品牌热度与单品价格指数。V1 明确区分公开菜单参考、模型估算与城市展示点。"""
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SEED = ROOT / "data/beverage/brands_v1.json"
RADAR = ROOT / "web/trend/data/local_brands.json"
LOCATIONS = ROOT / "data/beverage/locations_v1.json"


def price_index(price: int, jakarta_price: int) -> int:
    if jakarta_price <= 0:
        raise ValueError("雅加达基准价必须大于 0")
    return round(price / jakarta_price * 100)


def build_beverage(seed_path=SEED, radar_path=RADAR, locations_path=LOCATIONS) -> dict:
    seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    radar = json.loads(Path(radar_path).read_text(encoding="utf-8"))
    heat = {b["id"]: b.get("heat") for b in radar.get("brands", [])}
    locations = {}
    if Path(locations_path).is_file():
        raw_locations = json.loads(Path(locations_path).read_text(encoding="utf-8"))
        locations = {(x["brand_id"], x["city_id"]): x for x in raw_locations.get("locations", [])}
    points = []
    for bi, brand in enumerate(seed["brands"]):
        angle = math.radians(bi * 36)
        for city in seed["cities"]:
            # 未核实点使用城市展示坐标；Nominatim 核实点替换为真实命名地点坐标。
            lat = city["lat"] + 0.035 * math.sin(angle)
            lon = city["lon"] + 0.035 * math.cos(angle)
            location = locations.get((brand["id"], city["id"]), {})
            jakarta = city["id"] == "jakarta"
            price = brand["base_price_idr"] if jakarta else round(brand["base_price_idr"] * city["factor"] / 500) * 500
            points.append({
                "id": f"{brand['id']}-{city['id']}", "brand_id": brand["id"],
                "brand": brand["name"], "short": brand["short"], "category": brand["category"],
                "city": city["name"], "island": city["island"],
                "lat": location.get("lat", round(lat, 6)), "lon": location.get("lon", round(lon, 6)),
                "location_precision": location.get("location_precision", "city_model"),
                "location_name": location.get("name"), "location_source": location.get("location_source"),
                "sku": brand["sku"],
                "price_idr": price, "jakarta_price_idr": brand["base_price_idr"],
                "price_index": price_index(price, brand["base_price_idr"]),
                "price_basis": "公开菜单参考" if jakarta and brand["price_basis"] == "公开菜单参考" else brand["price_basis"] if jakarta else "城市物流模型估算",
                "price_source": brand["source"] if jakarta else None, "source_date": brand["source_date"] if jakarta else None,
                "heat_score": heat.get(brand.get("radar_id")), "featured": brand["featured"],
            })
    brands = []
    for brand in seed["brands"]:
        rows = [p for p in points if p["brand_id"] == brand["id"]]
        brands.append({**brand, "heat_score": heat.get(brand.get("radar_id")),
                       "avg_price_index": round(sum(p["price_index"] for p in rows) / len(rows)),
                       "max_price_index": max(p["price_index"] for p in rows)})
    verified = sum(p["location_precision"] == "osm_named_place" for p in points)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"), "version": seed["version"],
        "data_mode": f"公开地图命名地点 {verified} 点 + 城市模型 {len(points) - verified} 点（非全量真实门店）",
        "methodology": "单品价格指数 = 城市同款 SKU 价格 ÷ 雅加达同款 SKU 基准价 × 100；雅加达=100。外岛及缺少实测的城市价格由物流系数估算，实测后逐点替换。",
        "location_note": seed["location_note"], "cities": seed["cities"], "brands": brands, "points": points,
    }


def write_json(data: dict, out_path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
