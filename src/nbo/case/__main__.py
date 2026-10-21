"""CLI：python -m nbo.case --db nbo.db --out web/case/data/case_ops.json"""
import argparse
import json

from nbo.case import build_case_ops, build_case_dashboard, build_case_map, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="案例运营数据 → case_ops.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None, help="case_ops.json 输出路径；缺省只打印摘要")
    ap.add_argument("--out-dashboard", default=None, help="案例门店版去化大屏 JSON")
    ap.add_argument("--out-map", default=None, help="渠道地图门店点位 JSON")
    args = ap.parse_args()
    if args.out:
        d = write_json(build_case_ops(args.db), args.out)
    else:
        d = build_case_ops(args.db)
    if args.out_dashboard:
        write_json(build_case_dashboard(args.db), args.out_dashboard)
    if args.out_map:
        write_json(build_case_map(args.db), args.out_map)
    print(json.dumps({"store": d.get("store", {}).get("id"),
                      "skus": len(d.get("skus", [])), "orders": len(d.get("orders", [])),
                      "energy": len(d.get("energy", [])), "media": len(d.get("media", [])),
                      "demo": d.get("demo")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
