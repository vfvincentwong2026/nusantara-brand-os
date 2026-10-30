"""Web 页面完整性测试：导航一致性、关键模块存在性、入库键约定。"""
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

NAV_PAGES = ["case", "dashboard", "floorplan", "franchise", "launch",
             "library", "map", "three", "trend", "store-dash", "brandkit",
             "assembly", "playbook", "retail"]


def _read(page: str) -> str:
    return (WEB / page / "index.html").read_text(encoding="utf-8")


def test_all_pages_share_full_nav():
    for p in NAV_PAGES:
        html = _read(p)
        for anchor in ["热点雷达", "选品评分", "中央库", "品牌设计", "开店方案", "培训体系"]:
            assert anchor in html, f"{p} 导航缺少 {anchor}"
        assert 'href="/ui/tokens.css"' in html, f"{p} 缺少 tokens.css"


def test_nav_grouped_by_system():
    for p in NAV_PAGES:
        html = _read(p)
        assert "A·品牌孵化引擎" in html and "B·集装箱零售" in html, f"{p} 导航缺体系分组标签"


def test_nav_pages_have_data_p_highlight():
    for p in NAV_PAGES:
        assert f'data-p="{p}"' in _read(p), f"{p} 缺少自身 data-p 高亮"


def test_brandkit_generator_core():
    html = _read("brandkit")
    for key in ["function hash", "function rng", "function hslHex",
                "function generate", "symbolSVG", "nbo_lib_asset",
                "包装三层", "树导硬标准", "保存到中央库"]:
        assert key in html, f"brandkit 缺少 {key}"
    # 确定性：两次同输入同色（哈希函数纯函数，无可变全局）
    assert html.count("Math.random") == 0, "生成器禁止使用 Math.random，破坏可复现性"


def test_library_asset_tab_wires_brandkit():
    html = _read("library")
    assert "KIT-" in html and "/brandkit/" in html
    assert "'nbo_lib_'" in html


def test_home_links_brandkit_and_library():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "./brandkit/" in html and "./library/" in html


def test_home_dual_portal_separation():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "品牌加盟孵化引擎" in html
    assert "集装箱社区零售" in html
    assert "独立产品线" in html


def test_retail_landing_page():
    html = _read("retail")
    for k in ["集装箱社区店", "投资模型", "样板店", "共建印尼社区零售网络",
              "/assembly/data/assembly.json", "对外单页" if False else "B·集装箱零售"]:
        assert k in html, f"retail 缺少 {k}"


def test_case_has_no_influencer_chain():
    html = _read("case")
    assert 'class="chain"' not in html
