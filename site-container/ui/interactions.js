// NBO 共享交互层：磁吸光标 + 滚动渐显 + 标题线框图标
// 约定：body 加 .cursor-on 启用磁吸光标；h1/h2/h3 自动注入极简线框图标
(function () {
  const fine = matchMedia('(pointer:fine)').matches;

  // ── 磁吸光标（白点白环）────────────────────────────
  if (fine && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.body.classList.add('cursor-on');
    const dot = document.createElement('div'); dot.className = 'cursor-dot';
    const ring = document.createElement('div'); ring.className = 'cursor-ring';
    document.body.append(dot, ring);
    let mx = -100, my = -100, rx = -100, ry = -100;
    addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
    (function loop() {
      rx += (mx - rx) * 0.16; ry += (my - ry) * 0.16;
      dot.style.transform = `translate(${mx - 3}px,${my - 3}px)`;
      ring.style.transform = `translate(${rx - 17}px,${ry - 17}px)`;
      requestAnimationFrame(loop);
    })();
    document.querySelectorAll('a,button').forEach(el => {
      el.addEventListener('pointerenter', () => ring.classList.add('big'));
      el.addEventListener('pointerleave', () => ring.classList.remove('big'));
    });
  }

  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('rv-in'); io.unobserve(e.target); }
  }), { threshold: .08, rootMargin: '0px 0px -4% 0px' });
  document.querySelectorAll(
    '.head,.hero-grid,.stats,.panel,.card,.fmt,.tier,.portal,.ed-row,.marquee,.partner .tags,.ed-sec,.rules,.layout,.plan'
  ).forEach(el => { el.classList.add('rv'); io.observe(el); });

  // ── 标题线框图标 v2 · 圆润极简风（Lucide 风格路径）────
  const P = {
    radar: '<path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h.01"/><path d="M2.29 9.62A10 10 0 1 0 21.31 8.35"/><path d="M16.24 7.76A6 6 0 1 0 8.23 16.49"/><path d="M12 18h.01"/><path d="m13.41 10.59 5.66-5.66"/>',
    sparkles: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.287 1.288L3 12l5.8 1.9a2 2 0 0 1 1.288 1.287L12 21l1.9-5.8a2 2 0 0 1 1.287-1.288L21 12l-5.8-1.9a2 2 0 0 1-1.288-1.287Z"/><path d="M5 3v4M3 5h4M19 17v4M17 19h4"/>',
    gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.6 9.7l5.9-.9z"/>',
    store: '<path d="m2 7 4.4-4.4A2 2 0 0 1 7.8 2h8.4a2 2 0 0 1 1.4.6L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/><path d="M22 7v3a2.5 2.5 0 0 1-5 0V7M17 7v3a2.5 2.5 0 0 1-5 0V7M12 7v3a2.5 2.5 0 0 1-5 0V7M7 7v3a2.5 2.5 0 0 1-5 0"/>',
    box: '<path d="m7.5 4.3 9 5.2"/><path d="M21 8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    cube: '<path d="m21 8-9-5-9 5v8l9 5 9-5Z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
    pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    palette: '<path d="M12 2.5a9.5 9.5 0 0 0 0 19c1.8 0 2.7-1.1 2.1-2.4-.6-1.4.3-2.9 1.9-2.9H17a4 4 0 0 0 4-4c0-5.4-4-9.7-9-9.7z"/><circle cx="7.6" cy="10.5" r="1.05"/><circle cx="12" cy="7.4" r="1.05"/><circle cx="16.4" cy="10.5" r="1.05"/>',
    donut: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.4"/><path d="M7.5 8h.01M16.5 15.5h.01M9 17.5h.01M16 8.5h.01"/>',
    bakery: '<path d="M4.6 13.1 12 8.9l7.4 4.2c1.9 1 1 3.9-1.3 3.9H5.9c-2.3 0-3.2-2.9-1.3-3.9z"/><path d="M8 16v2M12 16.5V19M16 16v2"/>',
    coffee: '<path d="M17 8h1a4 4 0 1 1 0 8h-1"/><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/><path d="M6.5 2v2M10.5 2v2M14.5 2v2"/>',
    truck: '<path d="M14 17V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a1 1 0 0 0 1 1h2"/><path d="M15 17h-5"/><path d="M19 17h2a1 1 0 0 0 1-1v-3.7a1 1 0 0 0-.2-.6l-3.5-4.4a1 1 0 0 0-.8-.4H14"/><circle cx="7" cy="17.5" r="2"/><circle cx="17" cy="17.5" r="2"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    alert: '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.7V17c0 .5-.5 1-1 1.2-1.2.5-2 2-2 3.8"/><path d="M14 14.7V17c0 .5.5 1 1 1.2 1.2.5 2 2 2 3.8"/><path d="M18 2H6v7a6 6 0 0 0 12 0Z"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>',
    chart: '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9M13 17V5M8 17v-3"/>',
    zap: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    clipboard: '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4M12 16h4M8 11h.01M8 16h.01"/>',
    cal: '<path d="M8 2v4M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    filter: '<polygon points="22 3 2 3 10 12.5 10 19 14 21 14 12.5 22 3"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4"/>',
    globe: '<circle cx="12" cy="12" r="9.5"/><path d="M12 2.5a14.5 14.5 0 0 0 0 19 14.5 14.5 0 0 0 0-19"/><path d="M2.5 12h19"/>',
    coins: '<circle cx="8" cy="8" r="5.5"/><path d="M18.1 10.4a5.5 5.5 0 1 1-7.8 7.8"/><path d="M7 5.8h2v4.4"/><path d="m16.8 13.9.7.7-2.9 2.9"/>',
    money: '<rect width="20" height="14" x="2" y="5" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5h.01M18 14.5h.01"/>',
    activity: '<path d="M22 12h-2.5a2 2 0 0 0-1.9 1.5l-2.4 8.3a.25.25 0 0 1-.5 0L9.2 2.2a.25.25 0 0 0-.5 0l-2.4 8.3A2 2 0 0 1 4.5 12H2"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    search: '<circle cx="11" cy="11" r="7.5"/><path d="m21.5 21.5-4.3-4.3"/>',
    db: '<ellipse cx="12" cy="5" rx="8.5" ry="3"/><path d="M3.5 5v14c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3V5"/><path d="M3.5 12c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3"/>',
    check: '<circle cx="12" cy="12" r="9.5"/><path d="m8.5 12.5 2.5 2.5 5-5.5"/>',
    badge: '<path d="M3.9 8.6a4 4 0 0 1 4.8-4.8 4 4 0 0 1 6.6 0 4 4 0 0 1 4.8 4.8 4 4 0 0 1 0 6.6 4 4 0 0 1-4.8 4.8 4 4 0 0 1-6.6 0 4 4 0 0 1-4.8-4.8 4 4 0 0 1 0-6.6z"/><path d="m9 12 2 2 4-4"/>',
    gear: '<path d="M12.2 2h-.4a2 2 0 0 0-2 2v.2a2 2 0 0 1-1 1.7l-.4.3a2 2 0 0 1-2 0l-.2-.1a2 2 0 0 0-2.7.7l-.2.4a2 2 0 0 0 .7 2.7l.2.1a2 2 0 0 1 1 1.8v.4a2 2 0 0 1-1 1.8l-.2.1a2 2 0 0 0-.7 2.7l.2.4a2 2 0 0 0 2.7.7l.2-.1a2 2 0 0 1 2 0l.4.3a2 2 0 0 1 1 1.7v.2a2 2 0 0 0 2 2h.4a2 2 0 0 0 2-2v-.2a2 2 0 0 1 1-1.7l.4-.3a2 2 0 0 1 2 0l.2.1a2 2 0 0 0 2.7-.7l.2-.4a2 2 0 0 0-.7-2.7l-.2-.1a2 2 0 0 1-1-1.8v-.4a2 2 0 0 1 1-1.8l.2-.1a2 2 0 0 0 .7-2.7l-.2-.4a2 2 0 0 0-2.7-.7l-.2.1a2 2 0 0 1-2 0l-.4-.3a2 2 0 0 1-1-1.7V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    shield: '<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    arrow: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    play: '<circle cx="12" cy="12" r="9.5"/><path d="m10 8.2 6 3.8-6 3.8z"/>',
    grid: '<rect width="7.5" height="9.5" x="3" y="3" rx="1.5"/><rect width="7.5" height="5.5" x="13.5" y="3" rx="1.5"/><rect width="7.5" height="5.5" x="13.5" y="11.5" rx="1.5"/><rect width="7.5" height="5.5" x="3" y="15.5" rx="1.5"/>',
    pin: '<path d="M20 10c0 5-5.5 10.2-7.4 11.8a1 1 0 0 1-1.2 0C9.5 20.2 4 15 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    map: '<path d="M14.1 5.6a2 2 0 0 0 1.8 0l3.7-1.8A1 1 0 0 1 21 4.6v12.8a1 1 0 0 1-.6.9l-4.6 2.3a2 2 0 0 1-1.8 0l-4.2-2.1a2 2 0 0 0-1.8 0l-3.7 1.8A1 1 0 0 1 3 19.4V6.6a1 1 0 0 1 .6-.9l4.6-2.3a2 2 0 0 1 1.8 0z"/><path d="M15 5.8v15M9 3.2v15"/>',
    book: '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    grad: '<path d="M21.4 10.9a1 1 0 0 0 0-1.8L12.8 5.2a2 2 0 0 0-1.6 0L2.6 9.1a1 1 0 0 0 0 1.8l8.6 3.9a2 2 0 0 0 1.6 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
    bag: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    cart: '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.1 2.1h2l2.7 12.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6l1.7-7.4H5.1"/>',
    layout: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18M9 21V9"/>',
    layers: '<path d="m12 2.5 9 5-9 5-9-5z"/><path d="m3 13.5 9 5 9-5"/>',
    screen: '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8M12 17v4"/>',
    award: '<circle cx="12" cy="8" r="5.5"/><path d="M15.5 12.9 17 22l-5-3-5 3 1.5-9.1"/>',
    rocket: '<path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.2 2.2 0 0 0-2.9-.1z"/><path d="m12 15-3-3a22 22 0 0 1 2-4A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22 22 0 0 1-4 2z"/><path d="M9 12H4s.6-3 2-4c1.6-1 5 0 5 0"/><path d="M12 15v5s3-.6 4-2c1-1.6 0-5 0-5"/>',
    wallet: '<path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/>',
    flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3.2"/>',
  };
  const MAP = [
    ['雷达', 'radar'], ['热点', 'radar'], ['爆款', 'sparkles'], ['评分', 'gauge'], ['因子', 'gauge'],
    ['定级', 'star'], ['选品', 'star'], ['色板', 'palette'], ['字标', 'pen'], ['品牌库', 'award'],
    ['品牌', 'pen'], ['符号', 'sparkles'], ['包装', 'box'], ['实物效果', 'palette'], ['字体', 'pen'],
    ['开店方案', 'store'], ['装配', 'box'], ['业态', 'store'], ['加盟品牌', 'badge'], ['加盟', 'badge'],
    ['推车', 'cart'], ['移动', 'cart'], ['集装箱店样板', 'store'], ['样板店', 'store'],
    ['集装箱', 'box'], ['案例', 'box'], ['社区店', 'store'], ['门店大屏', 'screen'], ['门店', 'store'],
    ['流水', 'money'], ['预警', 'alert'], ['畅销', 'trophy'], ['补货', 'truck'], ['在架', 'db'],
    ['库存', 'db'], ['去化', 'chart'], ['供应链', 'link'], ['履约', 'clipboard'], ['订单', 'clipboard'],
    ['能源', 'zap'], ['设备', 'gear'], ['音视频', 'play'], ['排期', 'cal'], ['合规', 'shield'],
    ['快照', 'camera'], ['数据边界', 'alert'], ['平面', 'layout'], ['布局', 'layout'], ['视图', 'layout'],
    ['货架', 'grid'], ['统计', 'chart'], ['选中', 'check'], ['导出', 'arrow'], ['导入', 'arrow'],
    ['渠道地图', 'pin'], ['渠道', 'pin'], ['铺货', 'pin'], ['覆盖缺口', 'target'], ['打分', 'star'],
    ['区域', 'globe'], ['地图', 'map'], ['认证', 'award'], ['培训', 'grad'], ['手册', 'book'],
    ['冷启动', 'rocket'], ['计划', 'cal'], ['中央库', 'db'], ['中央资源库', 'db'], ['资源库', 'db'],
    ['供应商', 'truck'], ['选址', 'pin'], ['资产', 'db'], ['清单', 'list'], ['交付物', 'list'],
    ['投资模型', 'coins'], ['投资', 'coins'], ['成本', 'money'], ['回本', 'coins'], ['建店', 'store'],
    ['网络', 'globe'], ['共建', 'users'], ['三步', 'list'], ['五步', 'list'], ['链路', 'link'],
    ['落地', 'pin'], ['空间优化', 'cube'], ['3D', 'cube'], ['数字孪生', 'cube'],
    ['热力图', 'flame'], ['客流', 'users'], ['漫游', 'play'],
    ['流量', 'activity'], ['转化', 'filter'], ['复购', 'activity'], ['毛利', 'money'],
    ['搜索', 'search'], ['区域筛选', 'filter'], ['黄金', 'award'], ['课程', 'book'], ['考试', 'check'],
    ['筛选', 'filter'], ['结果', 'list'], ['规则', 'list'], ['机制', 'gear'],
    ['启动', 'rocket'], ['传播', 'sparkles'], ['场景', 'pin'], ['情绪', 'activity'], ['视觉', 'palette'],
    ['对比', 'layout'], ['推荐', 'star'], ['档位', 'layers'], ['面积', 'layout'], ['工期', 'cal'],
    ['证照', 'shield'], ['风险', 'alert'], ['结论', 'check'], ['行动', 'zap'],
    ['甜甜圈', 'donut'], ['烘焙', 'bakery'], ['糕点', 'bakery'], ['奶茶', 'coffee'], ['咖啡', 'coffee'],
    ['熟食', 'flame'], ['鱿鱼', 'flame'], ['饼干', 'bakery'], ['蛋糕', 'bakery'], ['三明治', 'bakery'],
    ['药果', 'bakery'], ['太阳饼', 'bakery'], ['零食', 'bag'],
  ];
  const FALLBACK = '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/>';
  const EMOJI = /([\u{1F000}-\u{1FAFF}\u{2190}-\u{21FF}\u{2300}-\u{27BF}\u{FE0F}])/gu;

  function iconFor(t) {
    for (const [k, v] of MAP) if (t.includes(k)) return P[v] || FALLBACK;
    return FALLBACK;
  }
  function decorate() {
    document.querySelectorAll('h1,h2,h3').forEach(h => {
      if (h.closest('nav') || h.closest('.chain') || h.querySelector('svg.hic')) return;
      const t = h.textContent.replace(EMOJI, '').trim();
      if (!t) return;
      h.innerHTML = h.innerHTML.replace(EMOJI, '');
      const size = h.tagName === 'H1' ? 26 : 18;
      h.insertAdjacentHTML('afterbegin',
        `<svg class="hic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" ` +
        `stroke-linecap="round" stroke-linejoin="round" style="width:${size}px;height:${size}px;` +
        `display:inline-block;vertical-align:-0.16em;margin-right:0.5em;color:var(--dim-warm,#9a9a9a)">` +
        `${iconFor(t)}</svg>`);
    });
  }
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', decorate);
  else decorate();
  addEventListener('load', () => setTimeout(decorate, 800)); // 覆盖 fetch 晚渲染的卡片标题
})();
