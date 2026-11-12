"""茶饮咖啡品牌热度与单品价格指数。V1 明确区分公开菜单参考、模型估算与城市展示点。"""
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SEED = ROOT / "data/beverage/brands_v1.json"
RADAR = ROOT / "web/trend/data/local_brands.json"
LOCATIONS = ROOT / "data/beverage/locations_v1.json"
GOOGLE_LOCATIONS = ROOT / "data/beverage/google_locations_v1.json"


def price_index(price: int, jakarta_price: int) -> int:
    if jakarta_price <= 0:
        raise ValueError("雅加达基准价必须大于 0")
    return round(price / jakarta_price * 100)


def distance_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> int:
    """用于展示 Google 与 OSM 坐标的偏差，不参与门店核验。"""
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(6371000 * 2 * math.asin(math.sqrt(h)))


def build_beverage(seed_path=SEED, radar_path=RADAR, locations_path=LOCATIONS,
                   google_path=GOOGLE_LOCATIONS,
                   bulk_path=ROOT / "data/beverage/google_locations_bulk_v1.json") -> dict:
    seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    radar = json.loads(Path(radar_path).read_text(encoding="utf-8"))
    heat = {b["id"]: b.get("heat") for b in radar.get("brands", [])}

    def read_locations(path):
        if not Path(path).is_file():
            return {}
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return {(x["brand_id"], x["city_id"]): x for x in raw.get("locations", [])}

    locations = read_locations(locations_path)
    google_locations = read_locations(google_path)
    points = []
    for bi, brand in enumerate(seed["brands"]):
        angle = math.radians(bi * 36)
        for city in seed["cities"]:
            lat = city["lat"] + 0.035 * math.sin(angle)
            lon = city["lon"] + 0.035 * math.cos(angle)
            key = (brand["id"], city["id"])
            osm = locations.get(key, {})
            google = google_locations.get(key)
            jakarta = city["id"] == "jakarta"
            price = brand["base_price_idr"] if jakarta else round(brand["base_price_idr"] * city["factor"] / 500) * 500
            precision = "google_verified" if google else "osm_candidate" if osm else "city_model"
            points.append({
                "id": f"{brand['id']}-{city['id']}", "brand_id": brand["id"],
                "brand": brand["name"], "short": brand["short"], "category": brand["category"],
                "city": city["name"], "island": city["island"],
                "lat": google["lat"] if google else osm.get("lat", round(lat, 6)),
                "lon": google["lon"] if google else osm.get("lon", round(lon, 6)),
                "location_precision": precision,
                "location_name": google["branch_name"] if google else osm.get("name"),
                "location_address": google.get("address") if google else osm.get("display_name"),
                "location_source": google["google_url"] if google else osm.get("location_source"),
                "google_place_id": google.get("google_place_id") if google else None,
                "business_status": google.get("business_status") if google else None,
                "coordinate_basis": google.get("coordinate_basis", "Google Maps 地点页 !3d/!4d") if google else None,
                "osm_source": osm.get("location_source") if google and osm else None,
                "osm_distance_m": distance_m(google["lat"], google["lon"], osm["lat"], osm["lon"]) if google and osm else None,
                "sku": brand["sku"], "price_idr": price, "jakarta_price_idr": brand["base_price_idr"],
                "price_index": price_index(price, brand["base_price_idr"]),
                "price_basis": "公开菜单参考" if jakarta and brand["price_basis"] == "公开菜单参考" else brand["price_basis"] if jakarta else "城市物流模型估算",
                "price_source": brand["source"] if jakarta else None, "source_date": brand["source_date"] if jakarta else None,
                "heat_score": heat.get(brand.get("radar_id")), "featured": brand["featured"],
            })

    # 仅追加 Mixue / Momoyo / Tianlala 真实 Google 门店；其他品牌的原始城市模型保持不变。
    bulk = json.loads(Path(bulk_path).read_text(encoding="utf-8")) if Path(bulk_path).is_file() else {"cities": [], "locations": []}
    brand_by_id = {b["id"]: b for b in seed["brands"]}
    city_by_id = {c["id"]: c for c in seed["cities"]}
    city_by_id.update({c["id"]: c for c in bulk.get("cities", [])})
    seen_places = {p["google_place_id"] for p in points if p.get("google_place_id")}
    for item in bulk.get("locations", []):
        if item["google_place_id"] in seen_places or item["brand_id"] not in {"mixue", "momoyo", "tianlala"}:
            continue
        seen_places.add(item["google_place_id"])
        brand, city = brand_by_id[item["brand_id"]], city_by_id[item["city_id"]]
        jakarta = city["id"] == "jakarta"
        price = brand["base_price_idr"] if jakarta else round(brand["base_price_idr"] * city["factor"] / 500) * 500
        gid = item["google_place_id"].replace(":", "")[-12:]
        points.append({
            "id": f"{brand['id']}-{city['id']}-{gid}", "brand_id": brand["id"],
            "brand": brand["name"], "short": brand["short"], "category": brand["category"],
            "city": city["name"], "island": city.get("island", "印尼其他岛屿"),
            "lat": item["lat"], "lon": item["lon"], "location_precision": "google_verified",
            "location_name": item["branch_name"], "location_address": item.get("address"),
            "location_source": item["google_url"], "google_place_id": item["google_place_id"],
            "business_status": item.get("business_status"), "coordinate_basis": item["coordinate_basis"],
            "osm_source": None, "osm_distance_m": None,
            "sku": brand["sku"], "price_idr": price, "jakarta_price_idr": brand["base_price_idr"],
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
                       "max_price_index": max(p["price_index"] for p in rows),
                       "google_store_count": sum(p["location_precision"] == "google_verified" for p in rows)})
    verified = sum(p["location_precision"] == "google_verified" for p in points)
    candidates = sum(p["location_precision"] == "osm_candidate" for p in points)
    all_cities = seed["cities"] + [c for c in bulk.get("cities", []) if c["id"] not in {x["id"] for x in seed["cities"]}]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"), "version": seed["version"],
        "data_mode": f"Google Maps 已核验 {verified} 点 + OSM 候选 {candidates} 点 + 城市模型 {len(points) - verified - candidates} 点（非全量真实门店）",
        "methodology": "单品价格指数 = 城市同款 SKU 价格 ÷ 雅加达同款 SKU 基准价 × 100；雅加达=100。外岛及缺少实测的城市价格由物流系数估算，实测后逐点替换。Google 坐标取地点页、嵌入地点页或搜索结果地点 URL 的门店坐标，不取视口中心。",
        "location_note": seed["location_note"], "cities": all_cities, "brands": brands, "points": points,
    }


def write_json(data: dict, out_path) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
