"""CLI：python -m nbo.hotbrand --db nbo.db --out web/trend/data/hotbrands.json"""
import argparse
import json

from nbo.hotbrand import build_hotbrand, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="热点品牌 → hotbrands.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_hotbrand(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"brands": len(d.get("brands", [])), "demo": d.get("demo")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
