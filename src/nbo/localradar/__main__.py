"""CLI：python -m nbo.localradar --db nbo.db --out web/trend/data/local_brands.json [--x-snapshot PATH | --no-x]

默认自动使用 data/radar/ 下最新的 x_snapshot_*.json（X 公开数据实抓）；--no-x 输出纯演示数据。
"""
import argparse
import json

from nbo.localradar import build_localradar, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="印尼本地网红品牌雷达 → local_brands.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    ap.add_argument("--x-snapshot", default="auto", help="X 快照路径；默认 auto=data/radar 最新一份")
    ap.add_argument("--no-x", action="store_true", help="不叠加 X 实抓数据（纯演示）")
    args = ap.parse_args()
    d = build_localradar(args.db, x_snapshot=None if args.no_x else args.x_snapshot)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"brands": len(d.get("brands", [])), "demo": d.get("demo"),
                      "x_snapshot": (d.get("x_snapshot") or {}).get("file"),
                      "brands_with_x": (d.get("x_snapshot") or {}).get("brands_with_x", 0)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
