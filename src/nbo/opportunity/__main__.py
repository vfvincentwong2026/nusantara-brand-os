"""CLI：python -m nbo.opportunity --db nbo.db --out web/map/data/opportunity.json"""
import argparse
import json

from nbo.opportunity import build_opportunity, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="加盟机会图层 → opportunity.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_opportunity(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"zones": len(d.get("zones", [])), "protection": len(d.get("protection", [])),
                      "s_grade": d.get("kpi", {}).get("s_grade"), "demo": d.get("demo")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
