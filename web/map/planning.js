/* 商业选址与城市规划分析层：人口/商圈/分区/轨道/TOD。 */
(() => {
  const css = `
  .plan-pop{display:flex;flex-direction:column;align-items:center;justify-content:center;width:58px;height:38px;border:1px solid #7aa7d9;border-radius:8px;background:rgba(255,255,255,.94);color:#24578a;box-shadow:0 1px 5px #0002;box-sizing:border-box;pointer-events:auto}
  .plan-pop b{font:800 12px/1.1 Inter,Arial,sans-serif}.plan-pop span{margin-top:3px;font:600 9px/1 Inter,"Microsoft YaHei",sans-serif;color:#555}
  .plan-poi{width:18px;height:18px;border:2px solid #fff;border-radius:50%;background:#b26a00;box-shadow:0 1px 5px #0003;box-sizing:border-box}
  .plan-poi.district{border-radius:4px;background:#7c5aa6}.plan-station{width:20px;height:20px;border:2px solid #fff;border-radius:5px;background:#2563a9;color:#fff;display:flex;align-items:center;justify-content:center;font:800 9px/1 Inter,Arial,sans-serif;box-shadow:0 1px 5px #0003;box-sizing:border-box}
  .plan-station.krl{background:#b26a00}.planning-note{margin:-5px 0 14px;padding:8px 10px;border-left:2px solid #b26a00;background:#fafafa;color:#767676;font-size:10.5px;line-height:1.55}`;
  const style = document.createElement('style'); style.textContent = css; document.head.appendChild(style);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const colors = {experience:'#2563a9',pickup:'#767676',drive:'#b26a00',value:'#2e7d32',cart:'#7c5aa6'};
  const note = document.createElement('div'); note.className = 'planning-note';
  document.getElementById('meta').after(note);
  let map, plan, registry = {};
  const addToggle = (id, layer, on = false) => {
    registry[id] = layer;
    const input = document.getElementById(id);
    if (!input) return;
    input.checked = on;
    input.onchange = e => e.target.checked ? layer.addTo(map) : map.removeLayer(layer);
    if (on) layer.addTo(map);
  };
  const popupSource = () => `<br><span style="color:#767676">规划分析示意／非政府法定规划</span>`;
  function buildCommercial(site) {
    const population = L.layerGroup(), commercial = L.layerGroup(), districts = L.layerGroup();
    const cities = new Map();
    site.candidates.forEach(c => { if (!cities.has(c.city)) cities.set(c.city, []); cities.get(c.city).push(c); });
    cities.forEach((items, city) => {
      const c = items[0], lat = items.reduce((s,x) => s + x.lat, 0) / items.length, lon = items.reduce((s,x) => s + x.lon, 0) / items.length;
      L.marker([lat,lon], {icon:L.divIcon({className:'',iconSize:[58,38],iconAnchor:[29,19],html:`<div class="plan-pop"><b>${c.city_pop_m}m</b><span>${esc(city)}</span></div>`})})
        .bindPopup(`<b>${esc(city)} · 人口/城镇分析</b><br>都市圈人口种子 ${c.city_pop_m} 百万人<br>城镇集中度 ${c.urban_pct}%<br>候选点 ${items.length} 个 · ${esc(c.island)}<br><span style="color:#767676">沿用选址模型种子，不是最新官方人口统计。</span>`).addTo(population);
    });
    site.pois.malls.forEach(p => {
      const near = site.candidates.filter(c => Math.hypot(c.lat-p.lat,c.lon-p.lon) < 0.09);
      const traffic = near.length ? Math.round(near.reduce((s,c) => s+c.foot_traffic,0)/near.length) : null;
      const popup = `<b>${esc(p.name)}</b><br>大型商业 · 900 米商圈分析圈<br>周边候选 ${near.length} 个${traffic == null ? '' : ` · 平均人流因子 ${traffic}`}${popupSource()}`;
      L.circle([p.lat,p.lon],{radius:900,color:'#b26a00',weight:1,fillColor:'#b26a00',fillOpacity:.05}).bindPopup(popup).addTo(commercial);
      L.marker([p.lat,p.lon],{icon:L.divIcon({className:'',iconSize:[18,18],iconAnchor:[9,9],html:'<div class="plan-poi"></div>'})}).bindPopup(popup).bindTooltip(esc(p.name),{direction:'top',offset:[0,-8]}).addTo(commercial);
    });
    site.candidates.forEach(c => {
      const color = colors[c.best_model?.key] || '#7c5aa6';
      const popup = `<b>${esc(c.name)}</b><br>${esc(c.city)} · ${esc(c.site_type)}<br>主导业态 ${esc(c.best_model?.name || c.recommended_model)} · 综合分 ${c.score}<br>分析半径 ${Math.max(1200,c.catchment.radius_m)} 米${popupSource()}`;
      L.circle([c.lat,c.lon],{radius:Math.max(1200,c.catchment.radius_m),color,weight:1,dashArray:'5 5',fillColor:color,fillOpacity:.04}).bindPopup(popup).addTo(districts);
      L.marker([c.lat,c.lon],{icon:L.divIcon({className:'',iconSize:[18,18],iconAnchor:[9,9],html:'<div class="plan-poi district"></div>'})}).bindPopup(popup).bindTooltip(esc(c.area),{direction:'top',offset:[0,-8]}).addTo(districts);
    });
    addToggle('planPopulation',population);
    addToggle('planCommercial',commercial);
    addToggle('planDistrict',districts);
    return {cities:cities.size,commercial:site.pois.malls.length,districts:site.candidates.length};
  }
  function buildTransit() {
    const lines = L.layerGroup(), stations = L.layerGroup(), tod = L.layerGroup();
    plan.rail_lines.forEach(line => {
      L.polyline(line.coordinates,{color:line.color,weight:3,opacity:.75,dashArray:'8 5'}).bindPopup(`<b>${esc(line.name)}</b><br>直线连接示意，非真实轨道矢量${popupSource()}`).addTo(lines);
    });
    plan.stations.forEach(s => {
      const popup = `<b>${esc(s.name)}</b><br>${esc(s.mode)} 轨道站点分析种子<br>TOD 步行可达分析半径 ${s.tod_radius_m} 米${popupSource()}`;
      L.marker([s.lat,s.lon],{icon:L.divIcon({className:'',iconSize:[20,20],iconAnchor:[10,10],html:`<div class="plan-station ${s.mode.toLowerCase()}">${s.mode === 'MRT' ? 'M' : 'K'}</div>`})}).bindPopup(popup).bindTooltip(esc(s.name),{direction:'top',offset:[0,-8]}).addTo(stations);
      L.circle([s.lat,s.lon],{radius:s.tod_radius_m,color:'#b26a00',weight:1.2,dashArray:'4 4',fillColor:'#b26a00',fillOpacity:.055}).bindPopup(popup).addTo(tod);
    });
    addToggle('planRail',lines,true);
    addToggle('planStation',stations,true);
    addToggle('planTod',tod);
    return {lines:plan.rail_lines.length,stations:plan.stations.length,tod:plan.stations.length};
  }
  const currentSite = () => typeof siteSel !== 'undefined' ? siteSel : null;
  function init() {
    map = window._leaflet_map;
    const site = currentSite();
    if (!map || !site || !plan) { setTimeout(init,250); return; }
    const counts = {...buildCommercial(site),...buildTransit()};
    note.textContent = plan.source_note + ' 人口、商圈与分区沿用当前选址演示种子；启用对应图层查看。';
    window._planningDebug = () => ({...counts,source_note:plan.source_note,layers:Object.fromEntries(Object.entries(registry).map(([k,v]) => [k,map.hasLayer(v)]))});
  }
  Promise.all([
    fetch('./data/planning_layers.json').then(r => r.ok ? r.json() : null),
    new Promise(resolve => {
      const wait = () => currentSite() ? resolve(currentSite()) : setTimeout(wait,250); wait();
    })
  ]).then(([d]) => { if (d) { plan = d; init(); } }).catch(() => { note.textContent = '规划分析层暂未加载，基础选址功能不受影响。'; });
})();
