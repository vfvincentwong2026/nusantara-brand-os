"""CLI：python -m nbo.cart --db nbo.db --out web/cart/data/carts.json"""
import argparse
import json

from nbo.cart import build_cart, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="移动推车加盟 → carts.json")
    ap.add_argument("--db", default="nbo.db")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = build_cart(args.db)
    if args.out:
        write_json(d, args.out)
    print(json.dumps({"carts": len(d["carts"]),
                      "min_startup_wan": min(c["startup"]["wan_cny"][0] for c in d["carts"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
