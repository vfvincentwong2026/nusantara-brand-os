"""python -m nbo.db migrate|seed"""
import sys

from nbo.db import migrate, seed

cmd = sys.argv[1] if len(sys.argv) > 1 else "migrate"
if cmd == "migrate":
    migrate()
    print("migrate ok")
elif cmd == "seed":
    print(f"seed ok: {seed()} stores")
else:
    sys.exit("用法: python -m nbo.db [migrate|seed]")
