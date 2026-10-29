"""Web 页面完整性测试：导航一致性、关键模块存在性、入库键约定。"""
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

NAV_PAGES = ["case", "dashboard", "floorplan", "franchise", "launch",
             "library", "map", "three", "trend", "store-dash", "brandkit",
             "assembly"]


def _read(page: str) -> str:
    return (WEB / page / "index.html").read_text(encoding="utf-8")


def test_all_pages_share_full_nav():
    for p in NAV_PAGES:
        html = _read(p)
        for anchor in ["热点雷达", "落地评分", "中央库", "品牌生成", "装配对比"]:
            assert anchor in html, f"{p} 导航缺少 {anchor}"
        assert 'href="/ui/tokens.css"' in html, f"{p} 缺少 tokens.css"


def test_nav_pages_have_data_p_highlight():
    for p in NAV_PAGES:
        assert f'data-p="{p}"' in _read(p), f"{p} 缺少自身 data-p 高亮"


def test_brandkit_generator_core():
    html = _read("brandkit")
    for key in ["function hash", "function rng", "function hslHex",
                "function generate", "symbolSVG", "nbo_lib_asset",
                "包装三层", "SHUDAO", "保存到中央库"]:
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
