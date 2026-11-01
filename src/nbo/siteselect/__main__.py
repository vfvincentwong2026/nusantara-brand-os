"""CLI：python -m nbo.siteselect --db nbo.db --out web/map/data/site_select.json"""
import argparse
import json

from nbo.siteselect import build_siteselect, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="智能选址 → site_select.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_siteselect(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"candidates": len(d.get("candidates", [])), "demo": d.get("demo")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
