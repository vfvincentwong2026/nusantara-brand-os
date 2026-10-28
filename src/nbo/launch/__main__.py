"""CLI：python -m nbo.launch --db nbo.db --out web/launch/data/launch.json"""
import argparse
import json

from nbo.launch import build_launch, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="概念落地评分 → launch.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None, help="输出路径；缺省只打印摘要")
    args = ap.parse_args()
    d = build_launch(args.db)
    if args.out:
        write_json(d, args.out)
    top = d.get("ranked", [{}])[0]
    print(json.dumps({"ranked": len(d.get("ranked", [])), "factors": len(d.get("factors", [])),
                      "top": top.get("name"), "total": top.get("total"), "grade": top.get("grade"),
                      "demo": d.get("demo")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
