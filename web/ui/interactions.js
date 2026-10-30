// NBO 共享交互层：磁吸光标 + 滚动渐显 + 标题线框图标
// 约定：body 加 .cursor-on 启用磁吸光标；h1/h2/h3 自动注入极度简约线框图标
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

  // ── 标题线框图标（1.5px 描边、无填充、currentColor）────
  const P = {
    radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18.5 5.5"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>',
    trend: '<path d="M3 17 9 11l4 4 8-8"/><path d="M15 7h6v6"/>',
    star: '<path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z"/>',
    cart: '<circle cx="9" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/><path d="M3 4h2.5l2.4 11h9.4l2.2-8H6.6"/>',
    store: '<path d="M4 9 5.5 4h13L20 9"/><path d="M4 9v11h16V9"/><path d="M9.5 20v-6h5v6"/><path d="M4 9c1.5 1.6 3 1.6 4.5 0 1.5 1.6 3 1.6 4.5 0 1.5 1.6 3 1.6 4.5 0"/>',
    box: '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5 12 12l8-4.5"/><path d="M12 12v9"/>',
    brand: '<path d="m12 19 7-7 3 3-7 7-3-3z"/><path d="m18 13-1.5-7.5L4 4l1.5 12.5L13 18z"/><path d="M4 4l7.6 7.6"/><circle cx="15.5" cy="8.5" r="1"/>',
    paint: '<path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 1.4-2.2-.7-1.4.1-2.8 1.6-2.8H17a4 4 0 0 0 4-4c0-5-4-9-9-9z"/><circle cx="7.5" cy="11" r="1.1"/><circle cx="12" cy="7.5" r="1.1"/><circle cx="16.5" cy="11" r="1.1"/>',
    cube: '<path d="m12 2.5 8 4.5v9l-8 4.5-8-4.5v-9z"/><path d="M4 7l8 4.5L20 7"/><path d="M12 11.5v9"/>',
    map: '<path d="m9 4-5 2v14l5-2 6 2 5-2V4l-5 2z"/><path d="M9 4v14M15 6v14"/>',
    pin: '<path d="M12 21s-7-5.6-7-11a7 7 0 1 1 14 0c0 5.4-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/>',
    layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
    layers: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    screen: '<rect x="2.5" y="4" width="19" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    gauge: '<path d="M4 14a8 8 0 1 1 16 0"/><path d="M12 14 15.5 8"/><path d="M3 18h18"/>',
    award: '<circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 7 5-3 5 3-1.5-7"/>',
    book: '<path d="M4 19V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19a2 2 0 0 0 2 2h13"/><path d="M9 7h6"/>',
    grad: '<path d="m12 4 10 5-10 5L2 9z"/><path d="M6 11.5V16c0 1.5 2.7 3 6 3s6-1.5 6-3v-4.5"/><path d="M22 9v5"/>',
    truck: '<path d="M1 8h13v9H1z"/><path d="M14 11h4l3 3v3h-7"/><circle cx="6" cy="19" r="1.8"/><circle cx="17" cy="19" r="1.8"/>',
    link: '<path d="M10 14a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 10a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    alert: '<path d="M12 3 2.5 20h19z"/><path d="M12 9.5V14"/><circle cx="12" cy="17" r="0.9" fill="currentColor" stroke="none"/>',
    trophy: '<path d="M8 21h8M12 17v4M7 4h10v6a5 5 0 0 1-10 0z"/><path d="M7 6H4a1 1 0 0 0-1 1c0 2.5 2 4 4 4M17 6h3a1 1 0 0 1 1 1c0 2.5-2 4-4 4"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 15v-4M12 17V7M17 13v-6"/>',
    zap: '<path d="M13 2 4 14h6l-1 8 9-12h-6z"/>',
    clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4a2 2 0 0 1 6 0"/><path d="M9 11h6M9 15h4"/>',
    cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9.5h18M8 3v4M16 3v4"/>',
    filter: '<path d="M3 5h18l-7 8v6l-4-2v-4z"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a13.5 13.5 0 0 1 0 18M12 3a13.5 13.5 0 0 0 0 18"/>',
    coins: '<ellipse cx="9" cy="7" rx="6.5" ry="3"/><path d="M2.5 7v5c0 1.7 2.9 3 6.5 3s6.5-1.3 6.5-3V7"/><path d="M2.5 12v5c0 1.7 2.9 3 6.5 3s6.5-1.3 6.5-3v-2"/><path d="M15.5 10.2c2.9.2 5.9 1.3 5.9 2.8 0 1.5-2.7 2.6-5.5 2.8"/>',
    money: '<rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5h.01M18 14.5h.01"/>',
    activity: '<path d="M3 12h4l2.5-7 5 14L17 12h4"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.7a3.5 3.5 0 0 1 0 6.6M17.5 14.4a6.5 6.5 0 0 1 4 5.6"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    db: '<ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v13c0 1.7 3.6 3 8 3s8-1.3 8-3v-13"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    check: '<path d="m4.5 12.5 5 5 10-11"/>',
    gear: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3M5.5 5.5l2.1 2.1M16.4 16.4l2.1 2.1M18.5 5.5l-2.1 2.1M7.6 16.4l-2.1 2.1"/>',
    arrow: '<path d="M4 12h15M13 6l6 6-6 6"/>',
    play: '<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/>',
    grid: '<rect x="3" y="3" width="7.5" height="7.5"/><rect x="13.5" y="3" width="7.5" height="7.5"/><rect x="3" y="13.5" width="7.5" height="7.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5"/>',
    badge: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="12" cy="10" r="2.5"/><path d="M7.5 16a4.5 4.5 0 0 1 9 0"/>',
    camera: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="m8.5 7 1.5-3h4l1.5 3"/><circle cx="12" cy="13" r="3.5"/>',
  };
  const MAP = [
    ['雷达', 'radar'], ['爆款', 'trend'], ['热点', 'radar'], ['评分', 'gauge'], ['因子', 'gauge'],
    ['定级', 'star'], ['选品', 'star'], ['色板', 'paint'], ['字标', 'brand'], ['品牌库', 'award'],
    ['品牌', 'brand'], ['符号', 'star'], ['包装', 'box'], ['实物效果', 'paint'], ['字体', 'brand'],
    ['开店方案', 'store'], ['装配', 'box'], ['业态', 'store'], ['加盟品牌', 'award'], ['加盟', 'badge'],
    ['推车', 'cart'], ['移动', 'cart'], ['集装箱店样板', 'store'], ['样板店', 'store'],
    ['集装箱', 'box'], ['案例', 'box'], ['社区店', 'store'], ['门店大屏', 'screen'], ['门店', 'store'],
    ['流水', 'money'], ['预警', 'alert'], ['畅销', 'trophy'], ['补货', 'truck'], ['在架', 'db'],
    ['库存', 'db'], ['去化', 'chart'], ['供应链', 'link'], ['履约', 'clipboard'], ['订单', 'clipboard'],
    ['能源', 'zap'], ['设备', 'gear'], ['音视频', 'play'], ['排期', 'cal'], ['合规', 'check'],
    ['快照', 'camera'], ['数据边界', 'alert'], ['平面', 'layout'], ['布局', 'layout'], ['视图', 'layout'],
    ['货架', 'grid'], ['统计', 'chart'], ['选中', 'check'], ['数据', 'db'], ['导出', 'arrow'], ['导入', 'arrow'],
    ['渠道地图', 'pin'], ['渠道', 'pin'], ['铺货', 'pin'], ['覆盖缺口', 'target'], ['打分', 'star'],
    ['区域', 'globe'], ['地图', 'map'], ['认证', 'award'], ['培训', 'grad'], ['手册', 'book'],
    ['冷启动', 'cal'], ['计划', 'cal'], ['中央库', 'db'], ['中央资源库', 'db'], ['资源库', 'db'],
    ['供应商', 'truck'], ['选址', 'pin'], ['资产', 'db'], ['清单', 'list'], ['交付物', 'list'],
    ['投资模型', 'coins'], ['投资', 'coins'], ['成本', 'money'], ['回本', 'coins'], ['建店', 'store'],
    ['网络', 'globe'], ['共建', 'users'], ['三步', 'list'], ['五步', 'list'], ['链路', 'link'],
    ['起点', 'arrow'], ['落地', 'pin'], ['空间优化', 'cube'], ['3D', 'cube'], ['数字孪生', 'cube'],
    ['热力图', 'zap'], ['客流', 'users'], ['漫游', 'play'], ['入库', 'db'], ['供应', 'truck'],
    ['起点', 'arrow'], ['流量', 'activity'], ['转化', 'filter'], ['复购', 'activity'], ['毛利', 'money'],
    ['搜索', 'search'], ['区域筛选', 'filter'], ['黄金', 'award'], ['课程', 'book'], ['考试', 'check'],
    ['SOP', 'book'], ['筛选', 'filter'], ['结果', 'list'], ['规则', 'list'], ['机制', 'gear'],
    ['启动', 'zap'], ['传播', 'trend'], ['场景', 'pin'], ['情绪', 'activity'], ['视觉', 'paint'],
    ['对比', 'layout'], ['推荐', 'star'], ['档位', 'layers'], ['面积', 'layout'], ['工期', 'cal'],
    ['证照', 'check'], ['风险', 'alert'], ['结论', 'check'], ['行动', 'zap'], [' SKU', 'db'],
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
      const size = h.tagName === 'H1' ? 24 : 17;
      h.insertAdjacentHTML('afterbegin',
        `<svg class="hic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" ` +
        `stroke-linecap="round" stroke-linejoin="round" style="width:${size}px;height:${size}px;` +
        `display:inline-block;vertical-align:-0.14em;margin-right:0.45em;color:var(--dim-warm,#888)">` +
        `${iconFor(t)}</svg>`);
    });
  }
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', decorate);
  else decorate();
  addEventListener('load', () => setTimeout(decorate, 800)); // 覆盖 fetch 晚渲染的卡片标题
})();
