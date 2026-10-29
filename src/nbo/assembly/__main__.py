"""CLI：python -m nbo.assembly --out web/assembly/data/assembly.json"""
import argparse
import json

from nbo.assembly import build_assembly, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="装配方案对比 → assembly.json")
    ap.add_argument("--db", default="nbo.db")  # 预留：后续接真实询价数据
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_assembly()
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"schemes": len(d["schemes"]), "budget_fit": d["budget_fit_ids"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
