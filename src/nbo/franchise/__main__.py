"""CLI：python -m nbo.franchise --db nbo.db --out web/franchise/data/franchise.json"""
import argparse
import json

from nbo.franchise import build_franchise, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="加盟体系 → franchise.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_franchise(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"formats": len(d.get("formats", [])), "brands": len(d.get("brands", [])),
                      "demo": d.get("demo")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
