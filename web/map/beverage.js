/* 茶饮咖啡热度 × 单品价格指数：独立附加图层，不改写现有选址图层。 */
(() => {
  const css = `
  .bev-mark{display:flex;align-items:center;justify-content:center;width:32px;height:20px;border:1.5px solid #fff;border-radius:6px;color:#fff;font:700 10px Consolas,monospace;box-shadow:0 1px 6px #0003}
  .bev-panel{border:1px solid #e5e5e5;border-radius:10px;margin:0 0 16px;overflow:hidden;background:#fff}
  .bev-panel summary{cursor:pointer;padding:10px 12px;font-weight:700;font-size:12.5px;background:#fafafa}
  .bev-note{padding:0 12px 8px;color:#767676;font-size:10.5px;line-height:1.55}
  .bev-filters{display:flex;gap:5px;padding:0 12px 8px}.bev-filters button{border:1px solid #e5e5e5;background:#fff;color:#767676;border-radius:999px;padding:2px 9px;font-size:10.5px;cursor:pointer}.bev-filters button.on{color:#111;border-color:#111}
  .bev-row{display:flex;align-items:center;gap:7px;padding:6px 12px;border-top:1px solid #f0f0f0;font-size:11px;cursor:pointer}.bev-row:hover{background:#fafafa}.bev-row .short{width:25px;font-weight:800}.bev-row .nm{flex:1;font-weight:600}.bev-row .heat{color:#767676;font-size:10px}.bev-row .idx{font:700 12px Consolas,monospace}
  .bev-pop{min-width:230px;line-height:1.65}.bev-pop .price{font-size:18px;font-weight:800}.bev-pop .warn{display:block;margin-top:6px;padding-top:6px;border-top:1px dashed #e5e5e5;color:#767676;font-size:11px}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const layers = document.querySelector('.layers');
  const label = document.createElement('label');
  label.innerHTML = '<input type="checkbox" id="bevToggle" checked> <b style="color:#111">茶饮咖啡 · 价格指数</b>（城市模型）';
  layers.appendChild(label);
  const sites = document.getElementById('sites');
  const panel = document.createElement('details'); panel.className = 'bev-panel'; panel.open = true;
  panel.innerHTML = '<summary>茶饮咖啡 · 品牌热度与单品价格指数</summary><div class="bev-note">雅加达同款 SKU = 100；标记内数字为价格指数。热度沿用雷达 X 数据，— 为待接入。</div><div class="bev-filters"><button class="on" data-f="all">全部</button><button data-f="茶饮">茶饮</button><button data-f="咖啡">咖啡</button></div><div id="bevBrands"></div><div class="bev-note" id="bevMeta"></div>';
  sites.parentNode.insertBefore(panel, sites.previousElementSibling);

  let data, group = L.layerGroup(), filter = 'all';
  const color = v => v <= 100 ? '#2e7d32' : v <= 108 ? '#b26a00' : '#e60023';
  const rp = n => 'Rp ' + n.toLocaleString('id-ID');
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  function visiblePoints() { return data.points.filter(p => filter === 'all' || p.category === filter); }
  function renderList() {
    document.getElementById('bevBrands').innerHTML = data.brands.filter(b => filter === 'all' || b.category === filter).sort((a,b) => a.featured - b.featured).map(b =>
      `<div class="bev-row" data-id="${b.id}"><span class="short">${esc(b.short)}</span><span class="nm">${esc(b.name)}</span><span class="heat">${b.heat_score == null ? '热度 —' : '热度 ' + Math.round(b.heat_score)}</span><span class="idx" style="color:${color(b.max_price_index)}">${b.max_price_index}</span></div>`).join('');
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
      const marker = L.marker([p.lat, p.lon], {icon: L.divIcon({className:'', iconSize:[32,20], iconAnchor:[16,10], html:`<div class="bev-mark" style="background:${color(p.price_index)}">${p.price_index}</div>`})})
        .bindPopup(`<div class="bev-pop"><b>${esc(p.brand)}</b> · ${esc(p.city)}（${esc(p.island)}）<br><span style="color:#767676">${esc(p.sku)}</span><br><span class="price">${rp(p.price_idr)}</span> · 指数 <b style="color:${color(p.price_index)}">${p.price_index}</b><br>雅加达基准 ${rp(p.jakarta_price_idr)} = 100<br>口径：${esc(p.price_basis)}<br>雷达热度：${p.heat_score == null ? '待接入' : Math.round(p.heat_score)}<br>${sourceHtml}<span class="warn">城市展示点，非门店地址。价格为公开参考或模型估算，不作为实时菜单承诺。</span></div>`);
      marker.bindTooltip(`${esc(p.short)} · ${p.price_index}`, {direction:'top', offset:[0,-8]});
      marker.addTo(group);
    });
  }
  function init() {
    if (!window._leaflet_map) { setTimeout(init, 300); return; }
    const map = window._leaflet_map;
    renderMarkers(); group.addTo(map); renderList();
    document.getElementById('bevMeta').textContent = data.location_note + ' ' + data.methodology;
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
