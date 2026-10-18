"""一键部署：重算数据 -> 组装 site/ -> wrangler pages deploy。

用法：python scripts/deploy.py [--store store-jkt-2000]
前置：pip install -e ".[dev]" 已完成；wrangler 已登录（wrangler whoami）。
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PROJECT = "nusantara-brand-os"


def sh(args, shell=False, **kw):
    print(f"$ {' '.join(str(a) for a in args)}")
    return subprocess.run(args, cwd=ROOT, check=True, shell=shell, **kw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="store-jkt-2000")
    p.add_argument("--skip-data", action="store_true", help="只组装+部署，不重算数据")
    a = p.parse_args()

    if not a.skip_data:
        sh([sys.executable, "-m", "nbo.db", "seed"])
        sh([sys.executable, "-m", "nbo.dashboard", "--db", "nbo.db",
            "--store", a.store, "--out", "web/dashboard/data/dashboard.json"])
        sh([sys.executable, "-m", "nbo.channel", "--db", "nbo.db",
            "--out", "web/map/data/channel_map.json"])
        sh([sys.executable, "-m", "nbo.twin", "--db", "nbo.db",
            "--out-dir", "web/twin/data"])
        sh([sys.executable, "-m", "nbo.flow", "--db", "nbo.db",
            "--out-dir", "web/twin/data"])

    # 组装部署目录
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "dashboard/data").mkdir(parents=True)
    (SITE / "map/data").mkdir(parents=True)
    for f in ("index.html", "echarts.min.js"):
        shutil.copy(ROOT / "web/dashboard" / f, SITE / "dashboard")
    shutil.copy(ROOT / "web/dashboard/data/dashboard.json", SITE / "dashboard/data")
    for f in ("index.html", "leaflet.js", "leaflet.css"):
        shutil.copy(ROOT / "web/map" / f, SITE / "map")
    shutil.copy(ROOT / "web/map/data/channel_map.json", SITE / "map/data")
    # 数字孪生（2D/3D 共享 planogram JSON）
    (SITE / "twin/data").mkdir(parents=True)
    (SITE / "floorplan").mkdir(parents=True)
    (SITE / "three").mkdir(parents=True)
    out_dir = ROOT / "web/twin/data"
    for f in list(out_dir.glob("planogram-*.json")) + list(out_dir.glob("flow-*.json")):
        shutil.copy(f, SITE / "twin/data")
    shutil.copy(ROOT / "web/index.html", SITE / "index.html")
    shutil.copy(ROOT / "web/floorplan/index.html", SITE / "floorplan")
    shutil.copy(ROOT / "web/floorplan/konva.min.js", SITE / "floorplan")
    for f in ("index.html", "three.module.min.js", "OrbitControls.js", "RoomEnvironment.js"):
        shutil.copy(ROOT / "web/three" / f, SITE / "three")
    print(f"assembled: {SITE}")

    # wrangler 是 POSIX shim，Windows 下直接调 node + wrangler.js 入口（绕开 cmd 崩溃）
    wrangler_shim = shutil.which("wrangler")
    npm_global = Path(wrangler_shim).parent if wrangler_shim else None
    wrangler_js = npm_global / "node_modules" / "wrangler" / "bin" / "wrangler.js" if npm_global else None
    node = shutil.which("node")
    if wrangler_js and wrangler_js.exists() and node:
        sh([node, str(wrangler_js), "pages", "deploy", str(SITE),
            "--project-name", PROJECT, "--branch", "main"])
    else:
        sh(f"wrangler pages deploy {SITE} --project-name {PROJECT} --branch main", shell=True)
    print(f"deployed: https://{PROJECT}.pages.dev/")


if __name__ == "__main__":
    main()
