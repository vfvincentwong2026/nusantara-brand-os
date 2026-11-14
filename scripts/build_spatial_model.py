"""Build the three-level retail spatial funnel from audited local/source data.

Real coordinates: beverage stores, site POIs, Citylines transit, HOT/OSM rail.
Proxy scores are explicitly labelled and formula-driven; no official rent/income claims.
"""
from __future__ import annotations
import argparse
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YEAR = 2026
CITYLINES_URL = "https://www.citylines.co/api/jakarta/"
HDX_RAIL_URL = "https://production-raw-data-api.s3.amazonaws.com/ISO3/IDN/railways/hotosm_idn_railways_osm_geojson.zip"


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def distance(a, b):
    """Haversine metres; points are [lon, lat]."""
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 12742000 * math.asin(math.sqrt(h))


def offset(center, dx, dy):
    lon, lat = center
    return [lon + dx/(111320*max(.1, math.cos(math.radians(lat)))), lat + dy/110540]


def square(center, size):
    half = size/2
    ring = [offset(center,-half,-half), offset(center,half,-half), offset(center,half,half), offset(center,-half,half)]
    return ring + [ring[0]]


def orient(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def intersects(a, b, c, d):
    return orient(a,b,c)*orient(a,b,d) <= 0 and orient(c,d,a)*orient(c,d,b) <= 0


def crosses(line, a, b):
    return any(intersects(a,b,line[i],line[i+1]) for i in range(len(line)-1))


def active(feature):
    p = feature["properties"]
    return (p.get("opening") or 0) <= YEAR < (p.get("closure") or 999999)


def rounded_ring(ring):
    return [[round(x,6), round(y,6)] for x,y in ring]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--citylines", default="tmp_gmap/citylines_jakarta_data.json")
    ap.add_argument("--railway-zip", default="tmp_gmap/idn_railways_geojson.zip")
    ap.add_argument("--out", default="web/map/data/spatial_model.json")
    args = ap.parse_args()
    site = json.loads((ROOT/"web/map/data/site_select.json").read_text(encoding="utf-8"))
    beverage = json.loads((ROOT/"web/map/data/beverage_index.json").read_text(encoding="utf-8"))
    citylines = json.loads((ROOT/args.citylines).read_text(encoding="utf-8"))
    rail = json.loads(zipfile.ZipFile(ROOT/args.railway_zip).read("railways.geojson"))

    base = citylines["view/base_data"]
    lines_meta = {x["url_name"]:x for x in base["lines"]}
    systems = {x["id"]:x["name"] for x in base["systems"]}
    mode_by_system = {51:"BRT",675:"MRT",662:"LRT",678:"LRT",676:"KRL",677:"AIRPORT"}
    sections = defaultdict(list)
    for f in citylines["source/sections"]["features"]:
        p = f["properties"]
        if active(f) and p.get("line_url_name") in lines_meta:
            sections[p["line_url_name"]].append(f["geometry"]["coordinates"])
    transit_lines, allowed_line_ids = [], set()
    for url_name, segments in sorted(sections.items()):
        meta = lines_meta[url_name]
        if meta["system_id"] not in mode_by_system:
            continue
        allowed_line_ids.add(url_name)
        transit_lines.append({
            "id":f"citylines:{url_name}", "name":meta["name"],
            "system":systems[meta["system_id"]], "mode":mode_by_system[meta["system_id"]],
            "color":meta.get("color") or "#2563a9", "segments":[[[round(x,6),round(y,6)] for x,y in seg] for seg in segments],
            "source":"Citylines", "source_id":url_name,
        })
    stations = []
    for f in citylines["source/stations"]["features"]:
        p = f["properties"]
        if active(f) and p.get("line_url_name") in allowed_line_ids:
            meta = lines_meta[p["line_url_name"]]
            lon,lat = f["geometry"]["coordinates"]
            stations.append({"name":p.get("name") or "未命名站", "mode":mode_by_system[meta["system_id"]],
                "lat":round(lat,6),"lon":round(lon,6),"source":"Citylines","source_id":p["id"]})

    candidate_centers = [[c["lon"],c["lat"]] for c in site["candidates"]]
    def near_candidates(point, degrees=.7):
        return any(abs(point[0]-c[0])<degrees and abs(point[1]-c[1])<degrees for c in candidate_centers)
    rail_lines = []
    for f in rail["features"]:
        if f["geometry"]["type"] != "LineString":
            continue
        coords = f["geometry"]["coordinates"]
        if any(near_candidates(p,.35) for p in coords[::max(1,len(coords)//4)]):
            rail_lines.append({"id":f["properties"]["id"],"name":f["properties"].get("name") or "铁路",
                "coordinates":[[round(x,6),round(y,6)] for x,y in coords],"source":"HOT/OSM via HDX"})
    jakarta_station_keys = {(s["name"],round(s["lat"],3),round(s["lon"],3)) for s in stations}
    for f in rail["features"]:
        if f["geometry"]["type"] != "Point":
            continue
        lon,lat = f["geometry"]["coordinates"]
        if not near_candidates([lon,lat],.7):
            continue
        p = f["properties"]
        key = (p.get("name") or "未命名站",round(lat,3),round(lon,3))
        if key in jakarta_station_keys:
            continue
        stations.append({"name":p.get("name") or "未命名站","mode":"RAIL","lat":round(lat,6),"lon":round(lon,6),
            "source":"HOT/OSM via HDX","source_id":p["id"]})

    poi = []
    university_names = {"UI Depok","UNJ Rawamangun","Atma Jaya Semanggi","Bina Nusantara Kemanggisan","UPH BSD","ITB Bandung","ITS Surabaya","UGM Yogyakarta","USU Medan","UNM Makassar"}
    for kind, items in site["pois"].items():
        for p in items:
            poi.append({**p,"kind":kind,"university":kind=="schools" and p["name"] in university_names})
    competitors = [{"brand":p["brand"],"brand_id":p["brand_id"],"category":p["category"],"lon":p["lon"],"lat":p["lat"],
        "price_idr":p["price_idr"],"price_index":p["price_index"]} for p in beverage["points"]]

    cities = defaultdict(list)
    for c in site["candidates"]:
        cities[c["city"]].append(c)
    hubs = {"雅加达":[106.8207,-6.1952],"泗水":[112.7522,-7.2578],"望加锡":[119.4227,-5.1477],
            "棉兰":[98.6722,3.5952],"登巴萨":[115.221,-8.6675],"巴厘巴板":[116.852,-1.237]}
    city_features, logistics = [], []
    for city, items in sorted(cities.items()):
        center = [sum(c["lon"] for c in items)/len(items),sum(c["lat"] for c in items)/len(items)]
        urban = sum(c["urban_pct"] for c in items)/len(items)
        rent = sum(c["rent_pressure"] for c in items)/len(items)
        experience = sum(next(m["score"] for m in c["models"] if m["key"]=="experience") for c in items)/len(items)
        purchase = round(clamp(.45*urban+.30*rent+.25*experience),1)
        grade = "A" if purchase>=68 else "B" if purchase>=55 else "C"
        hub_name = min(hubs,key=lambda h:distance(center,hubs[h]))
        supply_distance = distance(center,hubs[hub_name])/1000
        supply_score = round(clamp(100-supply_distance/25),1)
        positioning = "中高端咖啡 / 体验店" if grade=="A" else "平价奶茶 + 中端咖啡" if grade=="B" else "平价奶茶 / 轻店模型"
        city_features.append({"city":city,"center":[round(x,6) for x in center],"polygon":rounded_ring(square(center,28000)),
            "population_m":max(c["city_pop_m"] for c in items),"urban_pct":round(urban,1),"purchase_proxy":purchase,
            "grade":grade,"positioning":positioning,"supply_proxy":supply_score,"hub":hub_name})
        logistics.append({"from":hub_name,"to":city,"from_coord":hubs[hub_name],"to_coord":[round(x,6) for x in center],
            "distance_km":round(supply_distance,1),"supply_proxy":supply_score,"cross_island":hub_name!=city})

    grids, enriched = [], []
    for c in site["candidates"]:
        center = [c["lon"],c["lat"]]
        local_comp = [p for p in competitors if abs(p["lon"]-center[0])<.035 and abs(p["lat"]-center[1])<.035]
        local_poi = [p for p in poi if abs(p["lon"]-center[0])<.04 and abs(p["lat"]-center[1])<.04]
        local_stations = [s for s in stations if abs(s["lon"]-center[0])<.03 and abs(s["lat"]-center[1])<.03]
        local_rail = [r for r in rail_lines if any(abs(p[0]-center[0])<.025 and abs(p[1]-center[1])<.025 for p in r["coordinates"])]
        category = "咖啡" if c["best_model"]["key"]=="experience" else "奶茶"
        base_demand = clamp(.40*c["foot_traffic"]+.30*c["crowd_fit"]+.15*c["urban_pct"]+.15*min(100,c["catchment"]["pop_wan"]*8))
        base_access = clamp(.35*c["visibility"]+.30*c["delivery_fit"]+.20*c["foot_traffic"]+.15*c["car_traffic"])
        rider = round(clamp(.45*c["delivery_fit"]+.25*c["visibility"]+.20*(100-c["car_traffic"])+.10*(100-c["foot_traffic"])),1)
        rent_estimate = int(5_000_000+c["rent_pressure"]*450_000)
        cell_ids = []
        for iy,dy in enumerate(range(-300,301,100)):
            for ix,dx in enumerate(range(-300,301,100)):
                cell_center = offset(center,dx,dy)
                triggers = 0.0
                youth = 0.0
                middle = 0.0
                for p in local_poi:
                    d = distance(cell_center,[p["lon"],p["lat"]])
                    weight = {"schools":12,"offices":10,"malls":9,"communities":7}[p["kind"]]
                    triggers += weight/(1+d/250)
                    if p["kind"]=="schools": youth += (22 if p["university"] else 10)/(1+d/350)
                    if p["kind"] in ("offices","malls"): middle += 12/(1+d/400)
                huf = 0.0
                same_count = 0
                for p in local_comp:
                    d = distance(cell_center,[p["lon"],p["lat"]])
                    if d>1800: continue
                    huf += 1/(1+d/250)**2
                    if p["category"]==category and d<=500: same_count += 1
                saturation = round(clamp(100*(1-math.exp(-huf/1.5))),1)
                demand = clamp(.52*base_demand+.28*clamp(triggers*4)+.20*clamp(.55*c["crowd_fit"]+youth))
                competition = 100-saturation
                transit = max([1-distance(cell_center,[s["lon"],s["lat"]])/800 for s in local_stations]+[0])
                access = clamp(base_access+18*max(0,transit))
                mall_distance = min([distance(cell_center,[p["lon"],p["lat"]]) for p in local_poi if p["kind"]=="malls"]+[5000])
                rent_gradient = clamp(c["rent_pressure"]+10*math.exp(-mall_distance/500)-5*math.exp(-math.hypot(dx,dy)/500))
                cost = 100-rent_gradient
                static_barrier = any(crosses(r["coordinates"],center,cell_center) for r in local_rail) and math.hypot(dx,dy)>50
                suitability = clamp(.32*demand+.22*competition+.20*access+.14*rider+.12*cost-(18 if static_barrier else 0))
                cid = f"{c['id']}-{iy}{ix}"
                cell_ids.append(cid)
                grids.append({"id":cid,"candidate_id":c["id"],"city":c["city"],"center":[round(x,6) for x in cell_center],
                    "polygon":rounded_ring(square(cell_center,100)),"demand":round(demand,1),"youth_proxy":round(clamp(.55*c["crowd_fit"]+youth),1),
                    "middle_proxy":round(clamp(.45*c["urban_pct"]+.30*c["rent_pressure"]+middle),1),"competition":round(competition,1),
                    "saturation":saturation,"competitors_500m":same_count,"access":round(access,1),"rider_proxy":rider,
                    "cost":round(cost,1),"rent_proxy_idr":int(5_000_000+rent_gradient*450_000),"static_barrier":static_barrier,
                    "suitability":round(suitability,1)})
        own = [g for g in grids if g["candidate_id"]==c["id"]]
        avg = lambda k:round(sum(g[k] for g in own)/len(own),1)
        universities = [p for p in local_poi if p["university"]]
        nearest_university = min([distance(center,[p["lon"],p["lat"]]) for p in universities]+[999999])
        enriched.append({"id":c["id"],"name":c["name"],"city":c["city"],"area":c["area"],"lon":c["lon"],"lat":c["lat"],
            "site_type":c["site_type"],"category":category,"model":c["best_model"]["name"],"base_score":c["score"],
            "mcda":{"demand":avg("demand"),"competition":avg("competition"),"access":avg("access"),"fulfillment":avg("rider_proxy"),"cost":avg("cost")},
            "suitability":avg("suitability"),"best_cell":max(own,key=lambda g:g["suitability"])["id"],
            "rent_proxy_idr":rent_estimate,"rider_proxy":rider,"nearest_university_m":round(nearest_university),
            "street":c["site_type"] not in ("商场食阁",),"grid_ids":cell_ids})

    districts = []
    for c in enriched:
        source = next(x for x in site["candidates"] if x["id"]==c["id"])
        district_type = "大学城" if source["site_type"]=="学校旁" else "CBD" if source["site_type"]=="办公区" else "大型商圈" if source["site_type"]=="商场食阁" else "中产社区" if source["site_type"]=="社区口" and source["rent_pressure"]>=60 else "TOD" if source["site_type"]=="交通枢纽" else "社区商圈"
        strength = clamp(.45*source["foot_traffic"]+.35*source["crowd_fit"]+.20*source["rent_pressure"])
        districts.append({"candidate_id":c["id"],"name":c["area"],"city":c["city"],"type":district_type,
            "grade":"A" if strength>=75 else "B" if strength>=62 else "C","day_night":"白天办公客流" if source["site_type"]=="办公区" else "夜间社区客流" if source["site_type"]=="社区口" else "全时段客流",
            "center":[c["lon"],c["lat"]],"polygon":rounded_ring(square([c["lon"],c["lat"]],1200)),"strength":round(strength,1)})

    out = {"generated_at":"2026-11-14","grid_size_m":100,"analysis_year":YEAR,
        "sources":{"beverage":"web/map/data/beverage_index.json；Google 实点/候选/模型口径沿用原数据",
            "poi":"web/map/data/site_select.json；演示种子，非全量 POI",
            "transit":"Citylines Jakarta，当前运营要素按 opening<=2026<closure 筛选；ODbL",
            "rail":"OpenStreetMap contributors via HOT/HDX；snapshot 2026-10-09；ODC-ODbL",
            "roads_water":"HOT/OSM via HDX PMTiles，浏览器按视野加载"},
        "proxy_notes":{"purchase":"购买力代理 = 45% 城镇集中度 + 30% 租金压力 + 25% 体验店适配分；非官方收入统计。",
            "rent":"月租代理 = IDR 5,000,000 + 租金压力 × IDR 450,000；非挂牌租金。",
            "rider":"骑手友好度代理 = 45% 外卖适配 + 25% 可见性 + 20% 低车流 + 10% 低人流拥堵；非平台实测。",
            "saturation":"哈夫距离衰减：1/(1+d/250m)^2 汇总，再转为 0–100 饱和指数。",
            "compliance":"清真与排烟仅生成待核验提示，不绘制虚构行政严管区。"},
        "cities":city_features,"logistics":logistics,"districts":districts,"candidates":enriched,"grids":grids,
        "transit_lines":transit_lines,"stations":stations,"rail_barriers":rail_lines,"pois":poi}
    target = ROOT/args.out
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(json.dumps({"out":str(target),"cities":len(city_features),"candidates":len(enriched),"grids":len(grids),
        "transit_lines":len(transit_lines),"stations":len(stations),"rail_barriers":len(rail_lines),"bytes":target.stat().st_size},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
