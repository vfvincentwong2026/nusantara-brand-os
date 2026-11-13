/* 茶饮咖啡热度 × 单品价格指数：品牌独立开关 + 低缩放聚合。 */
(() => {
  const css = `
  .bev-mark{display:flex;align-items:center;justify-content:center;gap:3px;width:50px;height:28px;padding:2px 5px 2px 2px;border:1px solid #ddd;border-radius:14px;background:#fff;box-shadow:0 1px 6px #0003;box-sizing:border-box}
  .bev-badge{position:relative;display:inline-flex;align-items:center;justify-content:center;flex:none;width:24px;height:24px;border:1px solid #e5e5e5;border-radius:50%;background:#fff;color:#111;overflow:hidden;box-sizing:border-box}
  .bev-badge i{font:800 8px/1 Inter,Arial,sans-serif;font-style:normal;letter-spacing:-.03em}.bev-badge.has-logo i{display:none}
  .bev-badge img{position:absolute;inset:2px;width:calc(100% - 4px);height:calc(100% - 4px);object-fit:contain}
  .bev-mark .bev-badge{width:22px;height:22px;border:0}.bev-price{font:800 11px Consolas,monospace}
  .bev-cluster{display:flex;flex-direction:column;align-items:center;justify-content:center;width:58px;height:58px;border:2px solid #fff;border-radius:50%;background:#111;color:#fff;box-shadow:0 2px 12px #0004;box-sizing:border-box}
  .bev-cluster strong{font:800 17px/1.05 Inter,Arial,sans-serif}.bev-cluster span{margin-top:4px;font:600 9px/1 Inter,Arial,sans-serif;opacity:.8}
  .bev-panel{border:1px solid #e5e5e5;border-radius:10px;margin:0 0 16px;overflow:hidden;background:#fff}
  .bev-panel summary{cursor:pointer;padding:10px 12px;font-weight:700;font-size:12.5px;background:#fafafa}
  .bev-note{padding:0 12px 8px;color:#767676;font-size:10.5px;line-height:1.55}
  .bev-filters{display:flex;gap:5px;padding:0 12px 8px;flex-wrap:wrap}.bev-filters button,.bev-brand-actions button{border:1px solid #e5e5e5;background:#fff;color:#767676;border-radius:999px;padding:2px 9px;font-size:10.5px;cursor:pointer}.bev-filters button.on{color:#111;border-color:#111}
  .bev-brand-actions{display:flex;gap:5px;padding:0 12px 8px}.bev-brand-actions button{border-radius:5px;padding:2px 7px}
  .bev-group-title{padding:8px 12px 4px;border-top:1px solid #f0f0f0;color:#767676;font-size:10px;font-weight:800;letter-spacing:.08em}
  .bev-row{display:flex;align-items:center;gap:7px;padding:6px 12px;border-top:1px solid #f7f7f7;font-size:11px;cursor:pointer}.bev-row:hover{background:#fafafa}.bev-row input{flex:none;margin:0;accent-color:#111}.bev-row .nm{flex:1;font-weight:600}.bev-row .heat{color:#767676;font-size:10px}.bev-row .idx{font:700 12px Consolas,monospace}
  .bev-pop{min-width:230px;line-height:1.65}.bev-pop .price{font-size:18px;font-weight:800}.bev-pop .warn{display:block;margin-top:6px;padding-top:6px;border-top:1px dashed #e5e5e5;color:#767676;font-size:11px}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const layers = document.querySelector('.layers');
  const label = document.createElement('label');
  label.innerHTML = '<input type="checkbox" id="bevToggle" checked> <b style="color:#111">茶饮咖啡 · 价格指数</b>（≤7 聚合 / ≥8 门店）';
  const baseTitle = document.getElementById('baseGray')?.parentElement.previousElementSibling;
  baseTitle ? layers.insertBefore(label, baseTitle) : layers.appendChild(label);
  const sites = document.getElementById('sites');
  const panel = document.createElement('details'); panel.className = 'bev-panel'; panel.open = true;
  panel.innerHTML = '<summary>茶饮咖啡 · 品牌热度与单品价格指数</summary><div class="bev-note">雅加达同款 SKU = 100；标记内数字为价格指数。黑框仅代表 Google Maps 已核验坐标。勾选品牌可独立开关，全国缩放自动聚合。</div><div class="bev-filters"><button class="on" data-f="all">全部</button><button data-f="奶茶">奶茶</button><button data-f="咖啡">咖啡</button></div><div class="bev-brand-actions"><button data-a="on">本类全选</button><button data-a="off">本类清空</button></div><div id="bevBrands"></div><div class="bev-note" id="bevMeta"></div>';
  sites.parentNode.insertBefore(panel, sites.previousElementSibling);

  let data, filter = 'all', map, renderFrame = 0;
  let stats = { visible: 0, clusters: 0, represented: 0, stores: 0 };
  const enabledBrands = new Set();
  const clusterGroup = L.layerGroup(), storeGroup = L.layerGroup();
  const group = L.layerGroup([clusterGroup, storeGroup]);
  const color = v => v <= 100 ? '#2e7d32' : v <= 108 ? '#b26a00' : '#e60023';
  const rp = n => 'Rp ' + n.toLocaleString('id-ID');
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const brandById = id => data.brands.find(b => b.id === id) || {short:'?'};
  const brandMark = b => `<span class="bev-badge${b.logo ? ' has-logo' : ''}">${b.logo ? `<img src="${esc(b.logo)}" alt="" loading="lazy" onerror="this.parentNode.classList.remove('has-logo');this.remove()">` : ''}<i>${esc(b.short)}</i></span>`;
  const inCategory = b => filter === 'all' || b.category === filter;
  function visiblePoints() { return data.points.filter(p => inCategory(p) && enabledBrands.has(p.brand_id)); }
  function renderList() {
    const categories = filter === 'all' ? ['奶茶', '咖啡'] : [filter];
    document.getElementById('bevBrands').innerHTML = categories.map(category => {
      const brands = data.brands.filter(b => b.category === category).sort((a,b) => a.featured - b.featured);
      const rows = brands.map(b =>
        `<div class="bev-row" data-id="${b.id}"><input type="checkbox" data-brand="${b.id}" aria-label="显示 ${esc(b.name)}" ${enabledBrands.has(b.id) ? 'checked' : ''}>${brandMark(b)}<span class="nm">${esc(b.name)}</span><span class="heat">${b.google_store_count ? b.google_store_count + ' 实点' : b.heat_score == null ? '热度 —' : '热度 ' + Math.round(b.heat_score)}</span><span class="idx" style="color:${color(b.max_price_index)}">${b.max_price_index}</span></div>`).join('');
      return `<div class="bev-group-title">${category} · TOP ${brands.length}</div>${rows}`;
    }).join('');
    document.querySelectorAll('.bev-row').forEach(el => {
      el.onclick = e => {
        if (e.target.matches('input')) return;
        const p = data.points.find(x => x.brand_id === el.dataset.id && x.city === '雅加达');
        if (p && map) map.flyTo([p.lat, p.lon], 12);
      };
      el.querySelector('input').onchange = e => {
        e.target.checked ? enabledBrands.add(el.dataset.id) : enabledBrands.delete(el.dataset.id);
        renderMarkers();
      };
    });
  }
  function renderClusters(points) {
    const size = map.getZoom() <= 5 ? 72 : 62, buckets = new Map();
    points.forEach(p => {
      const xy = map.latLngToLayerPoint([p.lat, p.lon]);
      const key = Math.floor(xy.x / size) + ':' + Math.floor(xy.y / size);
      if (!buckets.has(key)) buckets.set(key, {points: [], x: 0, y: 0, brands: new Set()});
      const b = buckets.get(key); b.points.push(p); b.x += xy.x; b.y += xy.y; b.brands.add(p.brand_id);
    });
    buckets.forEach(b => {
      const count = b.points.length, center = map.layerPointToLatLng([b.x / count, b.y / count]);
      const marker = L.marker(center, {icon: L.divIcon({className: '', iconSize: [58,58], iconAnchor: [29,29], html: `<div class="bev-cluster" data-count="${count}"><strong>${count.toLocaleString('id-ID')}</strong><span>${b.brands.size} 品牌</span></div>`})})
        .bindTooltip(`${count} 家门店 · ${b.brands.size} 个品牌<br>点击放大查看价格`, {direction: 'top', offset: [0,-24]});
      marker.on('click', () => {
        const bounds = L.latLngBounds(b.points.map(p => [p.lat, p.lon]));
        map.fitBounds(bounds.pad(0.3), {maxZoom: 9});
      });
      marker.addTo(clusterGroup);
    });
    stats = {visible: points.length, clusters: buckets.size, represented: points.length, stores: 0};
  }
  function renderStores(points) {
    points.forEach(p => {
      const link = document.createElement('a');
      if (p.price_source) { link.setAttribute('href', 'https://' + p.price_source.split('://')[1]); link.target = '_blank'; link.rel = 'noopener'; link.textContent = '价格来源 ↗'; }
      const sourceHtml = p.price_source ? `${link.outerHTML} · ${esc(p.source_date || '日期待核')}` : '无独立菜单来源';
      const placeLink = document.createElement('a');
      if (p.location_source) { placeLink.setAttribute('href', 'https://' + p.location_source.split('://')[1]); placeLink.target = '_blank'; placeLink.rel = 'noopener'; placeLink.textContent = p.location_precision === 'google_verified' ? 'Google Maps ↗' : 'OSM 来源 ↗'; }
      const locationHtml = p.location_precision === 'google_verified'
        ? `<b>Google Maps 已核验</b>：${esc(p.location_name)}${p.business_status ? `<br><b style="color:#c00">Google 状态：${esc(p.business_status)}</b>` : ''}<br>${p.location_address ? esc(p.location_address) + ' · ' : '详细地址见 '}${placeLink.outerHTML}${p.osm_distance_m == null ? '' : `<br>与原 OSM 点相距约 ${p.osm_distance_m} 米`}`
        : p.location_precision === 'osm_candidate'
          ? `<b>OSM 候选点</b>：${esc(p.location_address)} · ${placeLink.outerHTML}<br>待 Google 复核，不作精准点位`
          : '城市展示点，非门店地址';
      const outline = p.location_precision === 'google_verified' ? 'outline:2px solid #111;outline-offset:2px' : p.location_precision === 'osm_candidate' ? 'outline:2px dashed #999;outline-offset:2px' : '';
      const marker = L.marker([p.lat, p.lon], {zIndexOffset: p.location_precision === 'google_verified' ? 1200 : p.location_precision === 'osm_candidate' ? 600 : 0, riseOnHover: true, icon: L.divIcon({className:'', iconSize:[50,28], iconAnchor:[25,14], html:`<div class="bev-mark" style="${outline}">${brandMark(brandById(p.brand_id))}<span class="bev-price" style="color:${color(p.price_index)}">${p.price_index}</span></div>`})})
        .bindPopup(`<div class="bev-pop"><b>${esc(p.brand)}</b> · ${esc(p.city)}（${esc(p.island)}）<br><span style="color:#767676">${esc(p.sku)}</span><br><span class="price">${rp(p.price_idr)}</span> · 指数 <b style="color:${color(p.price_index)}">${p.price_index}</b><br>雅加达基准 ${rp(p.jakarta_price_idr)} = 100<br>口径：${esc(p.price_basis)}<br>雷达热度：${p.heat_score == null ? '待接入' : Math.round(p.heat_score)}<br>${sourceHtml}<span class="warn">${locationHtml}<br>价格为公开参考或模型估算，不作为实时菜单承诺。</span></div>`);
      marker.bindTooltip(`${esc(p.short)} · ${p.price_index}`, {direction:'top', offset:[0,-8]});
      marker.addTo(storeGroup);
    });
    stats = {visible: points.length, clusters: 0, represented: 0, stores: points.length};
  }
  function updateMeta() {
    const mode = map.getZoom() <= 7 ? `聚合 ${stats.clusters} 组，覆盖 ${stats.represented} 店` : `门店 ${stats.stores} 家`;
    document.getElementById('bevMeta').textContent = `当前 ${mode} · 缩放 ≤7 聚合，≥8 显示价格。${data.data_mode}。${data.location_note}`;
  }
  function renderMarkers() {
    if (!map || !data) return;
    clusterGroup.clearLayers(); storeGroup.clearLayers();
    const points = visiblePoints();
    map.getZoom() <= 7 ? renderClusters(points) : renderStores(points);
    updateMeta();
  }
  function scheduleRender() {
    cancelAnimationFrame(renderFrame);
    renderFrame = requestAnimationFrame(renderMarkers);
  }
  function init() {
    map = window._leaflet_map;
    if (!map) { setTimeout(init, 300); return; }
    data.brands.forEach(b => enabledBrands.add(b.id));
    renderMarkers(); group.addTo(map); renderList();
    document.getElementById('bevToggle').onchange = e => e.target.checked ? group.addTo(map) : map.removeLayer(group);
    document.querySelectorAll('.bev-filters button').forEach(btn => btn.onclick = () => {
      filter = btn.dataset.f;
      document.querySelectorAll('.bev-filters button').forEach(b => b.classList.toggle('on', b === btn));
      renderMarkers(); renderList();
    });
    document.querySelectorAll('.bev-brand-actions button').forEach(btn => btn.onclick = () => {
      data.brands.filter(inCategory).forEach(b => btn.dataset.a === 'on' ? enabledBrands.add(b.id) : enabledBrands.delete(b.id));
      renderList(); renderMarkers();
    });
    map.on('zoomend moveend', scheduleRender);
    window._bevDebug = () => ({zoom: map.getZoom(), filter, enabled: [...enabledBrands], ...stats});
  }
  fetch('./data/beverage_index.json').then(r => r.ok ? r.json() : null).then(d => { if (d) { data = d; init(); } }).catch(() => {});
})();
