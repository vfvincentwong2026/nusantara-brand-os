"""CLI：python -m nbo.case --db nbo.db --out web/case/data/case_ops.json"""
import argparse
import json

from nbo.case import build_case_ops, write_case_ops


def main() -> None:
    ap = argparse.ArgumentParser(description="案例运营数据 → case_ops.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None, help="输出路径；缺省只打印摘要")
    args = ap.parse_args()
    if args.out:
        d = write_case_ops(args.out, db_path=args.db)
    else:
        d = build_case_ops(args.db)
    print(json.dumps({"store": d.get("store", {}).get("id"),
                      "skus": len(d.get("skus", [])), "orders": len(d.get("orders", [])),
                      "energy": len(d.get("energy", [])), "media": len(d.get("media", [])),
                      "demo": d.get("demo")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
