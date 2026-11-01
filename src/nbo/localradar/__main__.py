"""CLI：python -m nbo.localradar --db nbo.db --out web/trend/data/local_brands.json"""
import argparse
import json

from nbo.localradar import build_localradar, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="印尼本地网红品牌雷达 → local_brands.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_localradar(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"brands": len(d.get("brands", [])), "demo": d.get("demo")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
