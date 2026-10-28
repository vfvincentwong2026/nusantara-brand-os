"""CLI：python -m nbo.storedash --db nbo.db --out web/store-dash/data/store-dash.json"""
import argparse
import json

from nbo.storedash import build_store_dash, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="小店版大屏 → store-dash.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_store_dash(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"store": d.get("store", {}).get("name"),
                      "revenue": d.get("kpi", {}).get("today_revenue"),
                      "alerts": d.get("kpi", {}).get("alert_count"), "demo": d.get("demo")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
