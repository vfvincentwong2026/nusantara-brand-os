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
        sh([sys.executable, "-m", "nbo.space", "--db", "nbo.db",
            "--store", a.store, "--out-dir", "web/twin/data"])
        sh([sys.executable, "-m", "nbo.case", "--db", "nbo.db",
            "--out", "web/case/data/case_ops.json",
            "--out-dashboard", "web/case/data/dashboard-case.json",
            "--out-map", "web/map/data/case_store.json"])
        sh([sys.executable, "-m", "nbo.trend", "--db", "nbo.db",
            "--out", "web/trend/data/trend_snacks.json"])
        sh([sys.executable, "-m", "nbo.launch", "--db", "nbo.db",
            "--out", "web/launch/data/launch.json"])
        sh([sys.executable, "-m", "nbo.franchise", "--db", "nbo.db",
            "--out", "web/franchise/data/franchise.json"])

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
    shutil.copy(ROOT / "web/map/data/case_store.json", SITE / "map/data")
    # 案例页（社区集装箱店）
    (SITE / "case/data").mkdir(parents=True)
    (SITE / "case/assets").mkdir(parents=True)
    shutil.copy(ROOT / "web/case/index.html", SITE / "case")
    for f in (ROOT / "web/case/data").glob("*.json"):
        shutil.copy(f, SITE / "case/data")
    for f in (ROOT / "web/case/assets").glob("*.jpg"):
        shutil.copy(f, SITE / "case/assets")
    # 热点雷达
    (SITE / "trend/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/trend/index.html", SITE / "trend")
    shutil.copy(ROOT / "web/trend/data/trend_snacks.json", SITE / "trend/data")
    # 概念落地评分
    (SITE / "launch/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/launch/index.html", SITE / "launch")
    shutil.copy(ROOT / "web/launch/data/launch.json", SITE / "launch/data")
    # 加盟体系
    (SITE / "franchise/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/franchise/index.html", SITE / "franchise")
    shutil.copy(ROOT / "web/franchise/data/franchise.json", SITE / "franchise/data")
    # 数字孪生（2D/3D 共享 planogram JSON）
    (SITE / "twin/data").mkdir(parents=True)
    (SITE / "floorplan").mkdir(parents=True)
    (SITE / "three").mkdir(parents=True)
    out_dir = ROOT / "web/twin/data"
    for f in list(out_dir.glob("planogram-*.json")) + list(out_dir.glob("flow-*.json")) + list(out_dir.glob("optimize-*.json")):
        shutil.copy(f, SITE / "twin/data")
    shutil.copy(ROOT / "web/index.html", SITE / "index.html")
    (SITE / "ui").mkdir(exist_ok=True)
    for f in (ROOT / "web/ui").glob("*.css"):
        shutil.copy(f, SITE / "ui")
    (SITE / "assets").mkdir(exist_ok=True)
    for f in list((ROOT / "web/assets").glob("*.png")) + list((ROOT / "web/assets").glob("*.jpg")):
        shutil.copy(f, SITE / "assets")
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
