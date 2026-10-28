"""CLI：python -m nbo.trend --db nbo.db --out web/trend/data/trend_snacks.json"""
import argparse
import json

from nbo.trend import build_trend, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="热点零食雷达 → trend_snacks.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None, help="输出路径；缺省只打印摘要")
    args = ap.parse_args()
    d = build_trend(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"snacks": len(d.get("snacks", [])), "regions": d.get("regions"),
                      "demo": d.get("demo")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
