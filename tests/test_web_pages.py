"""Web 页面完整性测试：导航一致性、关键模块存在性、入库键约定。
2026-11 拆分：主站(web/)与集装箱兄弟项目站(container/)各自独立导航。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CT = ROOT / "container"

NAV_PAGES = ["franchise", "launch", "library", "map", "trend",
             "brandkit", "assembly", "playbook", "tower"]
CT_PAGES = ["case", "dashboard", "retail", "three", "floorplan", "store-dash"]

MAIN_NAV_ANCHORS = ["热点雷达", "选品评分", "中央库", "品牌设计", "开店方案", "培训体系"]
CT_URL = "https://nusantara-container.pages.dev/"
MAIN_URL = "https://nusantara-brand-os.pages.dev/"


def _read(root: Path, page: str) -> str:
    return (root / page / "index.html").read_text(encoding="utf-8")


def test_main_pages_share_full_nav():
    for p in NAV_PAGES:
        html = _read(WEB, p)
        for anchor in MAIN_NAV_ANCHORS:
            assert anchor in html, f"{p} 导航缺少 {anchor}"
        assert 'href="/ui/tokens.css"' in html, f"{p} 缺少 tokens.css"
        assert CT_URL in html, f"{p} 缺少集装箱兄弟项目外链"
        assert 'class="nl bline"' not in html, f"{p} 仍残留旧 bline 分组导航"


def test_main_nav_pages_have_data_p_highlight():
    for p in NAV_PAGES:
        assert f'data-p="{p}"' in _read(WEB, p), f"{p} 缺少自身 data-p 高亮"


def test_container_pages_share_container_nav():
    for p in CT_PAGES:
        html = _read(CT, p)
        for anchor in ["集装箱店案例", "3D 门店", "平面布局", "库存大屏"]:
            assert anchor in html, f"container/{p} 导航缺少 {anchor}"
        assert MAIN_URL in html, f"container/{p} 缺少主站回链"
        assert 'href="/ui/tokens.css"' in html, f"container/{p} 缺少 tokens.css"


def test_container_nav_pages_have_data_p_highlight():
    for p in CT_PAGES:
        assert f'data-p="{p}"' in _read(CT, p), f"container/{p} 缺少自身 data-p 高亮"


def test_container_landing_exists():
    html = (CT / "index.html").read_text(encoding="utf-8")
    assert "NUSANTARA CONTAINER" in html and MAIN_URL in html


def test_brandkit_generator_core():
    html = _read(WEB, "brandkit")
    for key in ["function hash", "function rng", "function hslHex",
                "function generate", "symbolSVG", "nbo_lib_asset",
                "包装三层", "树导硬标准", "保存到中央库"]:
        assert key in html, f"brandkit 缺少 {key}"
    # 确定性：两次同输入同色（哈希函数纯函数，无可变全局）
    assert html.count("Math.random") == 0, "生成器禁止使用 Math.random，破坏可复现性"


def test_library_asset_tab_wires_brandkit():
    html = _read(WEB, "library")
    assert "KIT-" in html and "/brandkit/" in html
    assert "'nbo_lib_'" in html


def test_home_links_brandkit_and_library():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "./brandkit/" in html and "./library/" in html


def test_home_dual_portal_separation():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "品牌复刻引擎" in html
    assert "兄弟项目 · 集装箱零售" in html
    assert "聚焦主线" in html
    assert CT_URL in html, "首页缺少集装箱独立站外链"


def test_retail_landing_page():
    html = _read(CT, "retail")
    for k in ["集装箱社区店", "投资模型", "样板店", "共建印尼社区零售网络",
              "./data/assembly.json", "NUSANTARA CONTAINER"]:
        assert k in html, f"retail 缺少 {k}"


def test_case_has_no_influencer_chain():
    html = _read(CT, "case")
    assert 'class="chain"' not in html
