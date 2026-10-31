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
SITE_CT = ROOT / "site-container"
PROJECT = "nusantara-brand-os"
PROJECT_CT = "nusantara-container"
CONTAINER_URL = f"https://{PROJECT_CT}.pages.dev/"


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
            "--store", a.store, "--out", "container/dashboard/data/dashboard.json"])
        sh([sys.executable, "-m", "nbo.channel", "--db", "nbo.db",
            "--out", "web/map/data/channel_map.json"])
        sh([sys.executable, "-m", "nbo.opportunity", "--db", "nbo.db",
            "--out", "web/map/data/opportunity.json"])
        sh([sys.executable, "-m", "nbo.twin", "--db", "nbo.db",
            "--out-dir", "container/twin/data"])
        sh([sys.executable, "-m", "nbo.flow", "--db", "nbo.db",
            "--out-dir", "container/twin/data"])
        sh([sys.executable, "-m", "nbo.space", "--db", "nbo.db",
            "--store", a.store, "--out-dir", "container/twin/data"])
        sh([sys.executable, "-m", "nbo.case", "--db", "nbo.db",
            "--out", "container/case/data/case_ops.json",
            "--out-dashboard", "container/case/data/dashboard-case.json",
            "--out-map", "web/map/data/case_store.json"])
        sh([sys.executable, "-m", "nbo.trend", "--db", "nbo.db",
            "--out", "web/trend/data/trend_snacks.json"])
        sh([sys.executable, "-m", "nbo.hotbrand", "--db", "nbo.db",
            "--out", "web/trend/data/hotbrands.json"])
        sh([sys.executable, "-m", "nbo.assembly", "--db", "nbo.db",
            "--out", "web/assembly/data/assembly.json"])
        sh([sys.executable, "-m", "nbo.cart", "--db", "nbo.db",
            "--out", "web/cart/data/carts.json"])
        sh([sys.executable, "-m", "nbo.launch", "--db", "nbo.db",
            "--out", "web/launch/data/launch.json"])
        sh([sys.executable, "-m", "nbo.franchise", "--db", "nbo.db",
            "--out", "web/franchise/data/franchise.json"])
        sh([sys.executable, "-m", "nbo.storedash", "--db", "nbo.db",
            "--out", "container/store-dash/data/store-dash.json"])

    # ═══ 主站（品牌孵化 Nusantara Brand OS）═══
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "map/data").mkdir(parents=True)
    for f in ("index.html", "leaflet.js", "leaflet.css"):
        shutil.copy(ROOT / "web/map" / f, SITE / "map")
    shutil.copy(ROOT / "web/map/data/channel_map.json", SITE / "map/data")
    shutil.copy(ROOT / "web/map/data/case_store.json", SITE / "map/data")
    shutil.copy(ROOT / "web/map/data/opportunity.json", SITE / "map/data")
    # 热点雷达
    (SITE / "trend/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/trend/index.html", SITE / "trend")
    for f in (ROOT / "web/trend/data").glob("*.json"):
        shutil.copy(f, SITE / "trend/data")
    # 概念落地评分
    (SITE / "launch/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/launch/index.html", SITE / "launch")
    shutil.copy(ROOT / "web/launch/data/launch.json", SITE / "launch/data")
    # 加盟体系
    (SITE / "franchise/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/franchise/index.html", SITE / "franchise")
    shutil.copy(ROOT / "web/franchise/data/franchise.json", SITE / "franchise/data")
    # 中央库
    (SITE / "library").mkdir(parents=True)
    shutil.copy(ROOT / "web/library/index.html", SITE / "library")
    # 孵化控制塔（五幕总览，读取 trend/launch JSON）
    (SITE / "tower").mkdir(parents=True)
    shutil.copy(ROOT / "web/tower/index.html", SITE / "tower")
    # 品牌设计生成器
    (SITE / "brandkit").mkdir(parents=True)
    shutil.copy(ROOT / "web/brandkit/index.html", SITE / "brandkit")
    # 装配方案对比
    (SITE / "assembly/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/assembly/index.html", SITE / "assembly")
    shutil.copy(ROOT / "web/assembly/data/assembly.json", SITE / "assembly/data")
    # 手册培训
    (SITE / "playbook").mkdir(parents=True)
    shutil.copy(ROOT / "web/playbook/index.html", SITE / "playbook")
    # 移动推车加盟数据
    (SITE / "cart/data").mkdir(parents=True)
    shutil.copy(ROOT / "web/cart/data/carts.json", SITE / "cart/data")
    shutil.copy(ROOT / "web/index.html", SITE / "index.html")
    # 已迁出页面 301 至集装箱独立站（Pages 旧部署文件仍会残留可访问）
    (SITE / "_redirects").write_text(
        "\n".join([
            "/case https://nusantara-container.pages.dev/case/ 301",
            "/case/* https://nusantara-container.pages.dev/case/:splat 301",
            "/dashboard https://nusantara-container.pages.dev/dashboard/ 301",
            "/dashboard/* https://nusantara-container.pages.dev/dashboard/:splat 301",
            "/retail https://nusantara-container.pages.dev/retail/ 301",
            "/retail/* https://nusantara-container.pages.dev/retail/:splat 301",
            "/three https://nusantara-container.pages.dev/three/ 301",
            "/three/* https://nusantara-container.pages.dev/three/:splat 301",
            "/floorplan https://nusantara-container.pages.dev/floorplan/ 301",
            "/floorplan/* https://nusantara-container.pages.dev/floorplan/:splat 301",
            "/store-dash https://nusantara-container.pages.dev/store-dash/ 301",
            "/store-dash/* https://nusantara-container.pages.dev/store-dash/:splat 301",
            "",
        ]), encoding="utf-8")
    (SITE / "ui").mkdir(exist_ok=True)
    for f in list((ROOT / "web/ui").glob("*.css")) + list((ROOT / "web/ui").glob("*.js")):
        shutil.copy(f, SITE / "ui")
    (SITE / "assets").mkdir(exist_ok=True)
    for f in list((ROOT / "web/assets").glob("*.png")) + list((ROOT / "web/assets").glob("*.jpg")):
        shutil.copy(f, SITE / "assets")
    print(f"assembled: {SITE}")

    # ═══ 集装箱兄弟项目独立站（Nusantara Container）═══
    CT = ROOT / "container"
    if SITE_CT.exists():
        shutil.rmtree(SITE_CT)
    SITE_CT.mkdir(parents=True)
    shutil.copy(CT / "index.html", SITE_CT / "index.html")
    (SITE_CT / "case/data").mkdir(parents=True)
    (SITE_CT / "case/assets").mkdir(parents=True)
    shutil.copy(CT / "case/index.html", SITE_CT / "case")
    for f in (CT / "case/data").glob("*.json"):
        shutil.copy(f, SITE_CT / "case/data")
    for f in (CT / "case/assets").glob("*.jpg"):
        shutil.copy(f, SITE_CT / "case/assets")
    (SITE_CT / "dashboard/data").mkdir(parents=True)
    for f in ("index.html", "echarts.min.js"):
        shutil.copy(CT / "dashboard" / f, SITE_CT / "dashboard")
    shutil.copy(CT / "dashboard/data/dashboard.json", SITE_CT / "dashboard/data")
    (SITE_CT / "retail/data").mkdir(parents=True)
    shutil.copy(CT / "retail/index.html", SITE_CT / "retail")
    shutil.copy(ROOT / "web/assembly/data/assembly.json", SITE_CT / "retail/data")
    (SITE_CT / "floorplan").mkdir(parents=True)
    shutil.copy(CT / "floorplan/index.html", SITE_CT / "floorplan")
    shutil.copy(CT / "floorplan/konva.min.js", SITE_CT / "floorplan")
    (SITE_CT / "three").mkdir(parents=True)
    for f in ("index.html", "three.module.min.js", "OrbitControls.js", "RoomEnvironment.js"):
        shutil.copy(CT / "three" / f, SITE_CT / "three")
    (SITE_CT / "twin/data").mkdir(parents=True)
    out_dir = CT / "twin/data"
    for f in list(out_dir.glob("planogram-*.json")) + list(out_dir.glob("flow-*.json")) + list(out_dir.glob("optimize-*.json")):
        shutil.copy(f, SITE_CT / "twin/data")
    (SITE_CT / "store-dash/data").mkdir(parents=True)
    shutil.copy(CT / "store-dash/index.html", SITE_CT / "store-dash")
    shutil.copy(CT / "store-dash/data/store-dash.json", SITE_CT / "store-dash/data")
    (SITE_CT / "ui").mkdir(exist_ok=True)
    for f in list((ROOT / "web/ui").glob("*.css")) + list((ROOT / "web/ui").glob("*.js")):
        shutil.copy(f, SITE_CT / "ui")
    (SITE_CT / "assets").mkdir(exist_ok=True)
    for f in list((ROOT / "web/assets").glob("*.png")) + list((ROOT / "web/assets").glob("*.jpg")):
        shutil.copy(f, SITE_CT / "assets")
    print(f"assembled: {SITE_CT}")

    # wrangler 是 POSIX shim，Windows 下直接调 node + wrangler.js 入口（绕开 cmd 崩溃）
    wrangler_shim = shutil.which("wrangler")
    npm_global = Path(wrangler_shim).parent if wrangler_shim else None
    wrangler_js = npm_global / "node_modules" / "wrangler" / "bin" / "wrangler.js" if npm_global else None
    node = shutil.which("node")
    if wrangler_js and wrangler_js.exists() and node:
        # 容器项目首次部署前确保项目存在（已存在时创建命令会报错，忽略）
        r = subprocess.run([node, str(wrangler_js), "pages", "project", "create", PROJECT_CT,
                            "--production-branch", "main"],
                           cwd=ROOT, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0 and "already exists" not in out:
            print(out)
        sh([node, str(wrangler_js), "pages", "deploy", str(SITE),
            "--project-name", PROJECT, "--branch", "main"])
        sh([node, str(wrangler_js), "pages", "deploy", str(SITE_CT),
            "--project-name", PROJECT_CT, "--branch", "main"])
    else:
        sh(f"wrangler pages deploy {SITE} --project-name {PROJECT} --branch main", shell=True)
        sh(f"wrangler pages deploy {SITE_CT} --project-name {PROJECT_CT} --branch main", shell=True)
    print(f"deployed: https://{PROJECT}.pages.dev/")
    print(f"deployed: {CONTAINER_URL}")


if __name__ == "__main__":
    main()
