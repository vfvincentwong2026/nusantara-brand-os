# -*- coding: utf-8 -*-
"""全站导航双语重写：主站(web/)与集装箱站(container/)各自独立导航。"""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

MAIN_NAV = """<nav class="nbo-nav" style="display:flex;gap:4px;align-items:center;padding:10px 20px;border-bottom:1px solid var(--hairline);flex-wrap:nowrap;overflow-x:auto;font-size:13px;">
  <a href="/" style="color:var(--paper);font-weight:600;letter-spacing:.1em;margin-right:10px;text-decoration:none;flex:0 0 auto;">NUSANTARA BRAND OS</a>
  <a class="nl" data-p="trend" href="/trend/">热点雷达<span class="nle">TREND</span></a>
  <a class="nl" data-p="launch" href="/launch/">选品评分<span class="nle">SCORE</span></a>
  <a class="nl" data-p="brandkit" href="/brandkit/">品牌设计<span class="nle">BRAND</span></a>
  <a class="nl" data-p="assembly" href="/assembly/">开店方案<span class="nle">ASSEMBLY</span></a>
  <a class="nl" data-p="franchise" href="/franchise/">加盟体系<span class="nle">FRANCHISE</span></a>
  <a class="nl" data-p="tower" href="/tower/">控制塔<span class="nle">TOWER</span></a>
  <a class="nl" data-p="map" href="/map/">渠道地图<span class="nle">MAP</span></a>
  <span style="color:var(--faint-warm);font-size:10px;letter-spacing:.08em;margin:0 4px 0 10px;white-space:nowrap;flex:0 0 auto;">底座 FOUNDATION</span>
  <a class="nl" data-p="playbook" href="/playbook/">培训体系<span class="nle">PLAYBOOK</span></a>
  <a class="nl" data-p="library" href="/library/">中央库<span class="nle">LIBRARY</span></a>
  <span style="color:var(--faint-warm);font-size:10px;letter-spacing:.08em;margin:0 4px 0 10px;white-space:nowrap;flex:0 0 auto;">兄弟项目</span>
  <a class="nl" href="https://nusantara-container.pages.dev/" target="_blank" rel="noopener">集装箱项目<span class="nle">CONTAINER ↗</span></a>
</nav>"""

CONTAINER_NAV = """<nav class="nbo-nav" style="display:flex;gap:4px;align-items:center;padding:10px 20px;border-bottom:1px solid var(--hairline);flex-wrap:nowrap;overflow-x:auto;font-size:13px;">
  <a href="/" style="color:var(--paper);font-weight:600;letter-spacing:.1em;margin-right:10px;text-decoration:none;flex:0 0 auto;">NUSANTARA CONTAINER</a>
  <a class="nl" data-p="case" href="/case/">集装箱店案例<span class="nle">CASE</span></a>
  <a class="nl" data-p="retail" href="/retail/">零售样板<span class="nle">RETAIL</span></a>
  <a class="nl" data-p="three" href="/three/">3D 门店<span class="nle">3D</span></a>
  <a class="nl" data-p="floorplan" href="/floorplan/">平面布局<span class="nle">PLAN</span></a>
  <a class="nl" data-p="dashboard" href="/dashboard/">库存大屏<span class="nle">STOCK</span></a>
  <a class="nl" data-p="store-dash" href="/store-dash/">门店大屏<span class="nle">LIVE</span></a>
  <a class="nl" href="https://nusantara-brand-os.pages.dev/" target="_blank" rel="noopener">品牌孵化主站<span class="nle">BRAND OS ↗</span></a>
</nav>"""

PAT = re.compile(r'<nav class="nbo-nav".*?</nav>', re.S)

def rewrite(path, nav):
    s = path.read_text(encoding='utf-8')
    s2, n = PAT.subn(nav, s, count=1)
    if n != 1:
        print(f'SKIP {path} (match={n})')
        return
    path.write_text(s2, encoding='utf-8')
    print(f'OK {path}')

for f in (ROOT / 'web').glob('*/index.html'):
    rewrite(f, MAIN_NAV)
rewrite(ROOT / 'web/index.html', MAIN_NAV)
for f in (ROOT / 'container').glob('*/index.html'):
    rewrite(f, CONTAINER_NAV)
