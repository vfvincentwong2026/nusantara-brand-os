/* 茶饮咖啡热度 × 单品价格指数：独立附加图层，不改写现有选址图层。 */
(() => {
  const css = `
  .bev-mark{display:flex;align-items:center;justify-content:center;gap:3px;width:50px;height:28px;padding:2px 5px 2px 2px;border:1px solid #ddd;border-radius:14px;background:#fff;box-shadow:0 1px 6px #0003;box-sizing:border-box}
  .bev-badge{position:relative;display:inline-flex;align-items:center;justify-content:center;flex:none;width:24px;height:24px;border:1px solid #e5e5e5;border-radius:50%;background:#fff;color:#111;overflow:hidden;box-sizing:border-box}
  .bev-badge i{font:800 8px/1 Inter,Arial,sans-serif;font-style:normal;letter-spacing:-.03em}.bev-badge.has-logo i{display:none}
  .bev-badge img{position:absolute;inset:2px;width:calc(100% - 4px);height:calc(100% - 4px);object-fit:contain}
  .bev-mark .bev-badge{width:22px;height:22px;border:0}.bev-price{font:800 11px Consolas,monospace}
  .bev-panel{border:1px solid #e5e5e5;border-radius:10px;margin:0 0 16px;overflow:hidden;background:#fff}
  .bev-panel summary{cursor:pointer;padding:10px 12px;font-weight:700;font-size:12.5px;background:#fafafa}
  .bev-note{padding:0 12px 8px;color:#767676;font-size:10.5px;line-height:1.55}
  .bev-filters{display:flex;gap:5px;padding:0 12px 8px}.bev-filters button{border:1px solid #e5e5e5;background:#fff;color:#767676;border-radius:999px;padding:2px 9px;font-size:10.5px;cursor:pointer}.bev-filters button.on{color:#111;border-color:#111}
  .bev-group-title{padding:8px 12px 4px;border-top:1px solid #f0f0f0;color:#767676;font-size:10px;font-weight:800;letter-spacing:.08em}
  .bev-row{display:flex;align-items:center;gap:7px;padding:6px 12px;border-top:1px solid #f7f7f7;font-size:11px;cursor:pointer}.bev-row:hover{background:#fafafa}.bev-row .nm{flex:1;font-weight:600}.bev-row .heat{color:#767676;font-size:10px}.bev-row .idx{font:700 12px Consolas,monospace}
  .bev-pop{min-width:230px;line-height:1.65}.bev-pop .price{font-size:18px;font-weight:800}.bev-pop .warn{display:block;margin-top:6px;padding-top:6px;border-top:1px dashed #e5e5e5;color:#767676;font-size:11px}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const layers = document.querySelector('.layers');
  const label = document.createElement('label');
  label.innerHTML = '<input type="checkbox" id="bevToggle" checked> <b style="color:#111">茶饮咖啡 · 价格指数</b>（核验点 / 候选 / 模型）';
  layers.appendChild(label);
  const sites = document.getElementById('sites');
  const panel = document.createElement('details'); panel.className = 'bev-panel'; panel.open = true;
  panel.innerHTML = '<summary>茶饮咖啡 · 品牌热度与单品价格指数</summary><div class="bev-note">雅加达同款 SKU = 100；标记内数字为价格指数。黑框仅代表 Google Maps 已核验坐标。</div><div class="bev-filters"><button class="on" data-f="all">全部 20</button><button data-f="奶茶">奶茶 10</button><button data-f="咖啡">咖啡 10</button></div><div id="bevBrands"></div><div class="bev-note" id="bevMeta"></div>';
  sites.parentNode.insertBefore(panel, sites.previousElementSibling);

  let data, group = L.layerGroup(), filter = 'all';
  const color = v => v <= 100 ? '#2e7d32' : v <= 108 ? '#b26a00' : '#e60023';
  const rp = n => 'Rp ' + n.toLocaleString('id-ID');
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const brandById = id => data.brands.find(b => b.id === id) || {short:'?'};
  const brandMark = b => `<span class="bev-badge${b.logo ? ' has-logo' : ''}">${b.logo ? `<img src="${esc(b.logo)}" alt="" loading="lazy" onerror="this.parentNode.classList.remove('has-logo');this.remove()">` : ''}<i>${esc(b.short)}</i></span>`;
  function visiblePoints() { return data.points.filter(p => filter === 'all' || p.category === filter); }
  function renderList() {
    const categories = filter === 'all' ? ['奶茶', '咖啡'] : [filter];
    document.getElementById('bevBrands').innerHTML = categories.map(category => {
      const rows = data.brands.filter(b => b.category === category).sort((a,b) => a.featured - b.featured).map(b =>
        `<div class="bev-row" data-id="${b.id}">${brandMark(b)}<span class="nm">${esc(b.name)}</span><span class="heat">${b.google_store_count ? b.google_store_count + ' 实点' : b.heat_score == null ? '热度 —' : '热度 ' + Math.round(b.heat_score)}</span><span class="idx" style="color:${color(b.max_price_index)}">${b.max_price_index}</span></div>`).join('');
      return `<div class="bev-group-title">${category} · TOP ${rows ? 10 : 0}</div>${rows}`;
    }).join('');
    document.querySelectorAll('.bev-row').forEach(el => el.onclick = () => {
      const p = data.points.find(x => x.brand_id === el.dataset.id && x.city === '雅加达');
      if (p && window._leaflet_map) window._leaflet_map.flyTo([p.lat, p.lon], 12);
    });
  }
  function renderMarkers() {
    group.clearLayers();
    visiblePoints().forEach(p => {
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
      marker.addTo(group);
    });
  }
  function init() {
    if (!window._leaflet_map) { setTimeout(init, 300); return; }
    const map = window._leaflet_map;
    renderMarkers(); group.addTo(map); renderList();
    document.getElementById('bevMeta').textContent = data.data_mode + '。' + data.location_note + ' ' + data.methodology;
    document.getElementById('bevToggle').onchange = e => e.target.checked ? group.addTo(map) : map.removeLayer(group);
    document.querySelectorAll('.bev-filters button').forEach(btn => btn.onclick = () => {
      filter = btn.dataset.f;
      document.querySelectorAll('.bev-filters button').forEach(b => b.classList.toggle('on', b === btn));
      renderMarkers(); renderList();
      if (document.getElementById('bevToggle').checked) group.addTo(map);
    });
  }
  fetch('./data/beverage_index.json').then(r => r.ok ? r.json() : null).then(d => { if (d) { data = d; init(); } }).catch(() => {});
})();
