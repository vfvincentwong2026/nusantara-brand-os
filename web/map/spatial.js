/* Three-level spatial funnel: MapLibre + Deck.gl + PMTiles + OSRM + NL2GIS. */
(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clamp = (v,a=0,b=100)=>Math.max(a,Math.min(b,v));
  const state = {data:null,beverage:null,map:null,overlay:null,level:'macro',metric:'mcda',category:'all',enabledBrands:new Set(),queryIds:null,queryMatches:0,selected:null,dynamicBarriers:new Map(),osrmRequest:0,osrmStatus:'idle',osrm:null,base:'gray',ready:false};
  const PMTILES = 'https://production-raw-data-api.s3.amazonaws.com/ISO3/IDN';
  const ESRI = {gray:'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',street:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'};
  const levelOf = z=>z<9?'macro':z<13?'meso':'micro';
  const visible = id => $(id)?.checked;
  const colorCache = new Map();
  const rgba = (hex,a=255)=>{const key=hex+a;if(colorCache.has(key))return colorCache.get(key);const v=hex.replace('#','');const full=v.length===3?v.split('').map(x=>x+x).join(''):v;const c=[parseInt(full.slice(0,2),16),parseInt(full.slice(2,4),16),parseInt(full.slice(4,6),16),a];colorCache.set(key,c);return c;};
  const distance = (a,b)=>{const r=Math.PI/180,lon1=a[0]*r,lat1=a[1]*r,lon2=b[0]*r,lat2=b[1]*r;const h=Math.sin((lat2-lat1)/2)**2+Math.cos(lat1)*Math.cos(lat2)*Math.sin((lon2-lon1)/2)**2;return 12742000*Math.asin(Math.sqrt(h));};
  const offset = (center,dx,dy)=>[center[0]+dx/(111320*Math.max(.1,Math.cos(center[1]*Math.PI/180))),center[1]+dy/110540];
  const square = (center,size)=>{const h=size/2,p=[offset(center,-h,-h),offset(center,h,-h),offset(center,h,h),offset(center,-h,h)];return [...p,p[0]];};
  const effective = g=>clamp(g.suitability-(state.dynamicBarriers.get(g.id)?18:0));

  function buildStyle(base){
    return {version:8,sources:{
      esri:{type:'raster',tiles:[ESRI[base]],tileSize:256,attribution:'Esri'},
      roads:{type:'vector',url:`pmtiles://${PMTILES}/roads/hotosm_idn_roads_osm.pmtiles`,maxzoom:13,attribution:'© OpenStreetMap contributors / HOT / HDX'},
      waterways:{type:'vector',url:`pmtiles://${PMTILES}/waterways/hotosm_idn_waterways_osm.pmtiles`,maxzoom:12,attribution:'© OpenStreetMap contributors / HOT / HDX'},
      poi:{type:'vector',url:`pmtiles://${PMTILES}/points_of_interest/hotosm_idn_points_of_interest_osm.pmtiles`,maxzoom:12,attribution:'© OpenStreetMap contributors / HOT / HDX'}
    },layers:[
      {id:'esri',type:'raster',source:'esri'},
      {id:'osm-major-roads',type:'line',source:'roads','source-layer':'roads',minzoom:8,filter:['match',['get','highway'],['motorway','trunk','primary'],true,false],layout:{visibility:'none'},paint:{'line-color':'#c24156','line-opacity':.72,'line-width':['interpolate',['linear'],['zoom'],8,.5,12,1.5,16,3.5]}},
      {id:'osm-waterways',type:'line',source:'waterways','source-layer':'waterways',minzoom:8,filter:['match',['get','waterway'],['river','canal'],true,false],layout:{visibility:'none'},paint:{'line-color':'#2687bd','line-opacity':.75,'line-width':['interpolate',['linear'],['zoom'],8,.6,12,1.8,16,4]}},
      {id:'osm-complements',type:'circle',source:'poi','source-layer':'points_of_interest',minzoom:12,filter:['any',['match',['get','shop'],['convenience','bakery'],true,false],['match',['get','amenity'],['fast_food'],true,false]],layout:{visibility:'none'},paint:{'circle-radius':['interpolate',['linear'],['zoom'],12,2.5,16,5],'circle-color':['match',['get','shop'],'convenience','#287a51','bakery','#b26a00','#767676'],'circle-stroke-color':'#fff','circle-stroke-width':1,'circle-opacity':.85}},
      {id:'osm-universities',type:'circle',source:'poi','source-layer':'points_of_interest',minzoom:11,filter:['match',['get','amenity'],['university','college'],true,false],layout:{visibility:'none'},paint:{'circle-radius':['interpolate',['linear'],['zoom'],11,3,16,7],'circle-color':'#7652aa','circle-stroke-color':'#fff','circle-stroke-width':1.2,'circle-opacity':.9}},
      {id:'osm-malls',type:'circle',source:'poi','source-layer':'points_of_interest',minzoom:11,filter:['match',['get','shop'],['mall','department_store'],true,false],layout:{visibility:'none'},paint:{'circle-radius':['interpolate',['linear'],['zoom'],11,3,16,7],'circle-color':'#2563a9','circle-stroke-color':'#fff','circle-stroke-width':1.2,'circle-opacity':.9}}
    ]};
  }
  function syncBaseLayers(){
    if(!state.map||!state.map.getStyle())return;
    const z=state.map.getZoom(),on=visible('barriers')&&z>=9,comp=visible('complements')&&z>=13;
    ['osm-major-roads','osm-waterways'].forEach(id=>{if(state.map.getLayer(id))state.map.setLayoutProperty(id,'visibility',on?'visible':'none');});
    if(state.map.getLayer('osm-complements'))state.map.setLayoutProperty('osm-complements','visibility',comp?'visible':'none');
    const triggers=visible('poiTrigger')&&z>=11;
    ['osm-universities','osm-malls'].forEach(id=>{if(state.map.getLayer(id))state.map.setLayoutProperty(id,'visibility',triggers?'visible':'none');});
  }
  function refreshLivePOIs(){
    if(!state.ready)return;
    const read=filter=>{
      const bounds=state.map.getBounds(),seen=new Set(),points=[];
      state.map.querySourceFeatures('poi',{sourceLayer:'points_of_interest',filter}).forEach(f=>{
        let center=null,g=f.geometry;
        if(g?.type==='Point')center=g.coordinates;
        else if(g?.type==='Polygon'&&g.coordinates[0]?.length){const ring=g.coordinates[0];center=[ring.reduce((s,p)=>s+p[0],0)/ring.length,ring.reduce((s,p)=>s+p[1],0)/ring.length];}
        if(!center||!bounds.contains(center))return;
        const key=f.id||center.map(x=>x.toFixed(6)).join(',');if(seen.has(key))return;seen.add(key);
        points.push({name:f.properties.name||'OSM POI',lon:center[0],lat:center[1],source:'OSM / HOT / HDX'});
      });return points;
    };
    NBOEvidence.setLivePois({universities:read(['match',['get','amenity'],['university','college'],true,false]),malls:read(['match',['get','shop'],['mall','department_store'],true,false])});
  }
  function filteredCompetitors(){return state.beverage.points.filter(p=>(state.category==='all'||p.category===state.category)&&state.enabledBrands.has(p.brand_id));}
  function filteredGrids(){return state.queryIds?state.data.grids.filter(g=>state.queryIds.has(g.id)):state.data.grids;}
  function filteredCandidates(){
    if(!state.queryIds)return state.data.candidates;
    const ids=new Set(state.data.grids.filter(g=>state.queryIds.has(g.id)).map(g=>g.candidate_id));
    return state.data.candidates.filter(c=>ids.has(c.id));
  }
  function metricColor(g){
    const metric=state.metric;
    if(metric==='mcda'){const v=effective(g);return v>=72?[39,139,34,155]:v>=62?[210,153,34,145]:[230,0,35,135];}
    if(metric==='saturation')return g.saturation>=65?[230,0,35,160]:g.saturation>=35?[210,153,34,145]:[39,139,34,135];
    const value=metric==='rent'?100-g.cost:g[metric]||0;
    return value>=72?metric==='rent'?[230,0,35,145]:[37,99,169,150]:value>=55?[210,153,34,135]:[180,190,200,105];
  }
  function transitPaths(){
    const out=[];state.data.transit_lines.forEach(line=>line.segments.forEach(path=>out.push({...line,path})));return out;
  }
  function deckLayers(){
    const d=state.data,z=state.map.getZoom(),level=levelOf(z),layers=[];
    if(level==='macro'){
      if(visible('demandHeat')||visible('middle')){
        layers.push(new deck.PolygonLayer({id:'city-economy',data:d.cities,getPolygon:x=>x.polygon,getFillColor:x=>x.grade==='A'?[37,99,169,90]:x.grade==='B'?[210,153,34,75]:[118,118,118,60],getLineColor:x=>x.grade==='A'?[37,99,169,190]:x.grade==='B'?[178,106,0,170]:[118,118,118,150],lineWidthMinPixels:1,pickable:true,onClick:({object})=>object&&focusCity(object.city)}));
        layers.push(new deck.TextLayer({id:'city-labels',data:d.cities,getPosition:x=>x.center,getText:x=>`${x.city} · ${x.grade}`,getSize:13,getColor:[17,17,17,230],getTextAnchor:'middle',getAlignmentBaseline:'center',fontSettings:{sdf:true},outlineWidth:2,outlineColor:[255,255,255,230]}));
      }
      if(visible('transitBands'))layers.push(new deck.ArcLayer({id:'supply-arcs',data:d.logistics,getSourcePosition:x=>x.from_coord,getTargetPosition:x=>x.to_coord,getSourceColor:[37,99,169,150],getTargetColor:x=>x.supply_proxy>60?[39,139,34,180]:[178,106,0,180],getWidth:2,greatCircle:true,getHeight:.25,pickable:true}));
    } else {
      if(visible('demandHeat'))layers.push(new deck.PolygonLayer({id:'districts',data:d.districts,getPolygon:x=>x.polygon,getFillColor:x=>x.grade==='A'?[37,99,169,45]:x.grade==='B'?[210,153,34,38]:[118,118,118,28],getLineColor:x=>x.grade==='A'?[37,99,169,150]:x.grade==='B'?[178,106,0,140]:[118,118,118,120],lineWidthMinPixels:1,pickable:true}));
      if(visible('saturation')&&level==='meso')layers.push(new deck.HeatmapLayer({id:'competition-heat',data:filteredCompetitors(),getPosition:x=>[x.lon,x.lat],getWeight:1,radiusPixels:55,intensity:1.15,threshold:.04,opacity:.55}));
    }
    if(level!=='macro'&&visible('transitBands')){
      const paths=transitPaths();
      layers.push(new deck.PathLayer({id:'transit-band',data:paths,getPath:x=>x.path,getColor:x=>rgba(x.color,32),getWidth:x=>x.mode==='BRT'?350:800,widthUnits:'meters',widthMinPixels:1,jointRounded:true,capRounded:true,parameters:{depthTest:false}}));
      layers.push(new deck.PathLayer({id:'transit-core',data:paths,getPath:x=>x.path,getColor:x=>rgba(x.color,210),getWidth:2,widthUnits:'pixels',widthMinPixels:1,pickable:true}));
      layers.push(new deck.ScatterplotLayer({id:'transit-stations',data:d.stations,getPosition:x=>[x.lon,x.lat],getRadius:x=>x.mode==='BRT'?35:65,radiusUnits:'meters',radiusMinPixels:2,radiusMaxPixels:8,getFillColor:x=>x.mode==='BRT'?[118,118,118,210]:[37,99,169,220],getLineColor:[255,255,255,230],stroked:true,lineWidthMinPixels:1,pickable:true}));
    }
    if(level!=='macro'&&visible('barriers'))layers.push(new deck.PathLayer({id:'rail-barriers',data:d.rail_barriers,getPath:x=>x.coordinates,getColor:[190,45,65,190],getWidth:1.5,widthUnits:'pixels',widthMinPixels:1}));
    if(level!=='macro'&&visible('poiTrigger'))layers.push(new deck.ScatterplotLayer({id:'trigger-poi',data:d.pois.filter(p=>p.kind==='schools'||p.kind==='offices'),getPosition:x=>[x.lon,x.lat],getRadius:x=>x.kind==='schools'?70:90,radiusUnits:'meters',radiusMinPixels:3,radiusMaxPixels:10,getFillColor:x=>x.kind==='schools'?[120,82,170,220]:[37,99,169,220],getLineColor:[255,255,255,240],stroked:true,lineWidthMinPixels:1,pickable:true}));
    if(level==='micro'){
      const metricOn=visible('mcdaGrid')||visible('demandHeat')||visible('youth')||visible('middle')||visible('saturation')||visible('rent');
      if(metricOn)layers.push(new deck.PolygonLayer({id:'mcda-grid',data:filteredGrids(),getPolygon:g=>g.polygon,getFillColor:metricColor,getLineColor:[255,255,255,80],lineWidthMinPixels:.25,pickable:true,onClick:({object})=>object&&selectCandidate(object.candidate_id,false),updateTriggers:{getFillColor:[state.metric,state.dynamicBarriers.size,state.queryMatches]}}));
      if(visible('competitors'))layers.push(new deck.ScatterplotLayer({id:'competitors',data:filteredCompetitors(),getPosition:p=>[p.lon,p.lat],getRadius:32,radiusUnits:'meters',radiusMinPixels:2,radiusMaxPixels:9,getFillColor:p=>p.price_idr<=25000?[39,139,34,220]:p.price_idr<=45000?[178,106,0,220]:[120,82,170,220],getLineColor:[255,255,255,230],stroked:true,lineWidthMinPixels:.6,pickable:true,onClick:({object,x,y})=>object&&showCompetitor(object)}));
    }
    if(level!=='macro'&&visible('candidates'))layers.push(new deck.ScatterplotLayer({id:'candidates',data:filteredCandidates(),getPosition:c=>[c.lon,c.lat],getRadius:100,radiusUnits:'meters',radiusMinPixels:6,radiusMaxPixels:18,getFillColor:c=>NBOEvidence.decisionScore(c)>=70?[39,139,34,235]:NBOEvidence.decisionScore(c)>=60?[178,106,0,235]:[230,0,35,225],getLineColor:[255,255,255,255],getLineWidth:2,stroked:true,pickable:true,onClick:({object})=>object&&selectCandidate(object.id,false)}));
    if(level!=='macro'&&visible('compliance')){
      const tasks=filteredCandidates();
      layers.push(new deck.ScatterplotLayer({id:'compliance-rings',data:tasks,getPosition:c=>[c.lon,c.lat],getRadius:145,radiusUnits:'meters',radiusMinPixels:10,radiusMaxPixels:24,getFillColor:[255,255,255,0],getLineColor:[178,106,0,255],getLineWidth:3,stroked:true,pickable:true,onClick:({object})=>object&&selectCandidate(object.id,false)}));
      layers.push(new deck.TextLayer({id:'compliance-tasks',data:tasks,getPosition:c=>[c.lon,c.lat],getText:'!',getSize:15,getColor:[178,106,0,255],getTextAnchor:'middle',getAlignmentBaseline:'center',fontWeight:700,outlineWidth:2,outlineColor:[255,255,255,255]}));
    }
    if(level==='micro'){
      layers.push(new deck.ScatterplotLayer({id:'evidence-points',data:NBOEvidence.points(),getPosition:x=>[x.lon,x.lat],getRadius:55,radiusUnits:'meters',radiusMinPixels:5,radiusMaxPixels:13,getFillColor:x=>x.record_type==='survey'?[39,139,34,240]:[37,99,169,240],getLineColor:[255,255,255,255],getLineWidth:2,stroked:true,pickable:true,onClick:({object})=>{if(!object)return;if(object.candidate_id)selectCandidate(object.candidate_id,false);else new maplibregl.Popup({maxWidth:'300px'}).setLngLat([object.lon,object.lat]).setHTML(`<b>${esc(object.title)}</b><br>${object.rent_month_idr?`Rp ${object.rent_month_idr.toLocaleString('id-ID')}/月`:esc(object.notes)}<br>${esc(object.observed_at)} · ${object.location_precision==='exact'?'精确坐标':'区域参考'}`).addTo(state.map);}}));
    }
    if(level==='micro'&&visible('isochrones')&&state.osrm){
      const cells=[...state.osrm.motor,...state.osrm.walk];
      layers.push(new deck.PolygonLayer({id:'osrm-cells',data:cells,getPolygon:x=>x.polygon,getFillColor:x=>x.profile==='walk'?(x.duration<=300?[37,99,169,80]:[100,100,100,20]):(x.duration<=180?[39,139,34,100]:x.duration<=300?[210,153,34,75]:[100,100,100,18]),getLineColor:x=>x.profile==='walk'?[37,99,169,80]:[39,139,34,65],lineWidthMinPixels:.4,pickable:true}));
      layers.push(new deck.ScatterplotLayer({id:'rider-stops',data:state.osrm.stops,getPosition:x=>[x.lon,x.lat],getRadius:24,radiusUnits:'meters',radiusMinPixels:4,radiusMaxPixels:10,getFillColor:[230,0,35,230],getLineColor:[255,255,255,255],stroked:true,pickable:true}));
    }
    return layers;
  }
  let frame=0;
  function updateLayers(){
    if(!state.ready)return;
    cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
      state.level=levelOf(state.map.getZoom());
      state.overlay.setProps({layers:deckLayers()});syncBaseLayers();renderLevel();renderLegend();
    });
  }
  function renderLevel(){
    const z=state.map.getZoom().toFixed(1),info=state.level==='macro'?['宏观 · 城市进入与供应链','MACRO / ZOOM 1–8']:state.level==='meso'?['中观 · 城市骨架与商圈','MESO / ZOOM 9–12']:['微观 · 街道与百米铺位','MICRO / ZOOM 13+'];
    $('level').innerHTML=`<b>${info[0]} · Z${z}</b><span>${info[1]}</span>`;
  }
  function renderLegend(){
    const html=state.level==='macro'?'<div><i class="sw" style="background:#2563a9"></i>A 级购买力代理</div><div><i class="sw" style="background:#d29a22"></i>B 级 / 培育城市</div><div><i class="sw" style="background:#767676"></i>C 级 / 平价优先</div><div>弧线＝供应链网络模型，非实际船期</div>':state.level==='meso'?'<div><i class="sw" style="background:#2563a9"></i>轨道带状辐射 800m</div><div><i class="sw" style="background:#c24156"></i>铁路 / 主干道割裂线</div><div><i class="sw" style="background:#2687bd"></i>河流割裂线</div>':`<div><i class="sw" style="background:#278b22"></i>${state.metric==='saturation'?'低竞争':'高适宜 / 高分'}</div><div><i class="sw" style="background:#d29a22"></i>中等等级</div><div><i class="sw" style="background:#e60023"></i>${state.metric==='saturation'?'高竞争':'低适宜 / 高分成本'}</div><div>100m 网格 · 点击候选计算 OSRM</div>`;
    $('legend').innerHTML=html;
  }
  function showCompetitor(p){
    new maplibregl.Popup({closeButton:true,maxWidth:'300px'}).setLngLat([p.lon,p.lat]).setHTML(`<b>${esc(p.brand)}</b> · ${esc(p.city)}<br>${esc(p.sku)}<br>Rp ${p.price_idr.toLocaleString('id-ID')} · 指数 ${p.price_index}<br><span style="color:#767676">${p.location_precision==='google_verified'?'Google Maps 已核验':'候选/模型点，沿用原数据口径'}</span>`).addTo(state.map);
  }
  function focusCity(city){
    const c=state.data.cities.find(x=>x.city===city);if(c)state.map.flyTo({center:c.center,zoom:10,duration:900});
  }
  function renderBrandList(){
    const brands=state.beverage.brands.filter(b=>state.category==='all'||b.category===state.category);
    $('brandList').innerHTML=`<div class="base" style="padding:5px 0">${['all','奶茶','咖啡'].map(c=>`<button data-category="${c}" class="${state.category===c?'on':''}">${c==='all'?'全部':c}</button>`).join('')}</div>`+brands.map(b=>`<label><input type="checkbox" data-brand="${b.id}" ${state.enabledBrands.has(b.id)?'checked':''}>${esc(b.name)} <span style="margin-left:auto;color:#999">${b.category}</span></label>`).join('');
    $('brandList').querySelectorAll('[data-brand]').forEach(el=>el.onchange=()=>{el.checked?state.enabledBrands.add(el.dataset.brand):state.enabledBrands.delete(el.dataset.brand);updateLayers();});
    $('brandList').querySelectorAll('[data-category]').forEach(el=>el.onclick=()=>{state.category=el.dataset.category;renderBrandList();updateLayers();});
  }
  function renderCandidates(){
    $('candidateList').innerHTML=[...state.data.candidates].sort((a,b)=>NBOEvidence.decisionScore(b)-NBOEvidence.decisionScore(a)).map(c=>{const q=NBOEvidence.completeness(c);return `<div class="candidate" data-id="${c.id}"><span class="v">${NBOEvidence.decisionScore(c)}</span><b>${esc(c.name)}</b><p>${esc(c.city)} · ${esc(c.model)} · ${esc(c.category)} · 证据 ${q.score}/100 ${q.grade} 级 · MCDA ${c.suitability}</p></div>`;}).join('');
    $('candidateList').querySelectorAll('.candidate').forEach(el=>el.onclick=()=>selectCandidate(el.dataset.id,true));
  }
  function radar(c){
    const labels=['需求','竞争','可达','履约','成本'],keys=['demand','competition','access','fulfillment','cost'],cx=88,cy=79,r=52;
    const point=(i,ratio)=>{const a=(-90+i*72)*Math.PI/180;return [cx+Math.cos(a)*r*ratio,cy+Math.sin(a)*r*ratio];};
    const polygon=ratio=>labels.map((_,i)=>point(i,ratio).map(v=>v.toFixed(1)).join(',')).join(' ');
    const values=keys.map(k=>c.mcda[k]),points=values.map((v,i)=>point(i,v/100).map(x=>x.toFixed(1)).join(',')).join(' ');
    return `<svg id="radar" viewBox="0 0 180 170" role="img" aria-label="五维得分雷达图">${[.33,.66,1].map(x=>`<polygon points="${polygon(x)}" fill="none" stroke="#e5e5e5"/>`).join('')}${labels.map((l,i)=>{const p=point(i,1),t=point(i,1.34);return `<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="#eee"/><text x="${t[0]}" y="${t[1]}" text-anchor="middle" font-size="9" fill="#666">${l}</text>`;}).join('')}<polygon points="${points}" fill="rgba(37,99,169,.22)" stroke="#2563a9" stroke-width="2"/>${values.map((v,i)=>{const p=point(i,v/100);return `<circle cx="${p[0]}" cy="${p[1]}" r="2.5" fill="#2563a9"><title>${labels[i]} ${v}</title></circle>`;}).join('')}</svg>`;
  }
  function insight(c){
    const entries=Object.entries(c.mcda).sort((a,b)=>a[1]-b[1]),low=entries[0][0];
    if(low==='competition')return '竞争生态是主要短板：同品类距离衰减辐射强，建议错开 300–500 米或更换价格带。';
    if(low==='fulfillment')return '履约是主要短板：骑手停靠与道路条件需先实测，再决定外卖占比。';
    if(low==='access')return '可达性是主要短板：需求存在，但轨道、街道可见性或割裂线削弱到店转化。';
    if(low==='cost')return '成本是主要短板：需求可能较好，需用精确租金与回本模型继续复核。';
    if(low==='demand')return '需求是主要短板：建议缩小店型，先用外卖与快取验证真实订单密度。';
    return '各因子较均衡，可进入铺位租金、Halal、排烟和停靠条件的现场核验。';
  }
  function renderDetail(){
    const c=state.data.candidates.find(x=>x.id===state.selected);if(!c){$('detail').classList.remove('show');return;}
    const labels={demand:'需求分',competition:'竞争分',access:'可达分',fulfillment:'履约分',cost:'成本分'};
    $('detail').classList.add('show');
    $('detailBody').innerHTML=`<div class="detail-title">${esc(c.name)}</div><div class="detail-sub">${esc(c.city)} · ${esc(c.site_type)} · ${esc(c.category)} · 空间 MCDA ${c.suitability} · 决策分 ${NBOEvidence.decisionScore(c)}</div><div class="radar-wrap">${radar(c)}<div class="factor-list">${Object.entries(labels).map(([k,l])=>`<div class="factor"><span>${l}</span><b>${c.mcda[k]}</b></div>`).join('')}</div></div><div class="insight">${insight(c)}</div><div class="detail-sub" style="margin-top:8px">${NBOEvidence.exactRent(c)?`硬过滤租金 Rp ${NBOEvidence.exactRent(c).rent_month_idr.toLocaleString('id-ID')}/月（精确证据） · 模型代理 Rp ${c.rent_proxy_idr.toLocaleString('id-ID')}/月`:`租金代理 Rp ${c.rent_proxy_idr.toLocaleString('id-ID')}/月（非挂牌）`} · 最近大学 ${c.nearest_university_m>99999?'无 100km 内种子':(c.nearest_university_m/1000).toFixed(1)+'km'}<br>骑手友好代理 ${c.rider_proxy} · 最佳网格 ${c.best_cell}<br><span style="color:#b26a00">现场任务：Halal 认证、排烟条件、商铺证照与骑手停靠均待核验。</span></div>${NBOEvidence.detailHTML(c)}<div class="osrm-status" id="osrmStatus">${osrmStatusText()}</div><div class="quick"><button id="osrmRetry">重新计算 OSRM</button><button id="focusBest">定位最佳网格</button></div>`;
    $('osrmRetry').onclick=()=>runOSRM(c);$('focusBest').onclick=()=>{const g=state.data.grids.find(x=>x.id===c.best_cell);if(g)state.map.flyTo({center:g.center,zoom:16});};
  }
  function osrmStatusText(){
    if(state.osrmStatus==='loading')return 'OSRM 正在沿真实路网计算摩托 3/5 分钟、步行 5 分钟及道路吸附停靠候选…';
    if(state.osrmStatus==='error')return 'OSRM 公共引擎本次不可用，未用直线圆替代；可点击重试。';
    if(state.osrmStatus==='ready'&&state.osrm)return `OSRM 已返回：摩托 ${state.osrm.motor.filter(x=>x.duration<=300).length} 个 5 分钟样本格，步行 ${state.osrm.walk.filter(x=>x.duration<=300).length} 个 5 分钟样本格，${state.osrm.stops.length} 个停靠候选。`;
    return '点击候选后自动计算 OSRM；无结果时不展示伪造等时圈。';
  }
  function selectCandidate(id,fly){
    state.selected=id;state.osrm=null;state.osrmStatus='idle';state.dynamicBarriers=new Map();NBOEvidence.selectCandidate(id);renderDetail();
    const c=state.data.candidates.find(x=>x.id===id);
    if(fly&&c)state.map.flyTo({center:[c.lon,c.lat],zoom:14,duration:900});
    if(c&&visible('isochrones'))runOSRM(c);updateLayers();
  }
  async function osrmTable(c,profile){
    const motor=profile==='car',step=motor?400:200,range=motor?1200:600,center=[c.lon,c.lat],destinations=[];
    for(let dy=-range;dy<=range;dy+=step)for(let dx=-range;dx<=range;dx+=step)destinations.push(offset(center,dx,dy));
    const coords=[center,...destinations].map(p=>p.map(x=>x.toFixed(6)).join(',')).join(';');
    const url=`https://routing.openstreetmap.de/routed-${profile}/table/v1/driving/${coords}?sources=0&annotations=duration`;
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);
    try{
      const res=await fetch(url,{signal:controller.signal});if(!res.ok)throw new Error(`OSRM ${res.status}`);const json=await res.json();
      if(!json.durations?.[0])throw new Error('OSRM no durations');
      return destinations.map((p,i)=>({profile:motor?'motor':'walk',duration:json.durations[0][i+1],center:p,polygon:square(p,step)})).filter(x=>Number.isFinite(x.duration));
    }finally{clearTimeout(timer);}
  }
  async function osrmStops(c){
    const res=await fetch(`https://routing.openstreetmap.de/routed-car/nearest/v1/driving/${c.lon},${c.lat}?number=3`);if(!res.ok)throw new Error('nearest failed');const json=await res.json();
    return (json.waypoints||[]).map(w=>({lon:w.location[0],lat:w.location[1],name:w.name||'道路吸附点'}));
  }
  async function runOSRM(c){
    const request=++state.osrmRequest;state.osrmStatus='loading';state.osrm=null;renderDetail();
    try{
      const [motor,walk,stops]=await Promise.all([osrmTable(c,'car'),osrmTable(c,'foot'),osrmStops(c).catch(()=>[])]);
      if(request!==state.osrmRequest)return;state.osrm={motor,walk,stops};state.osrmStatus='ready';renderDetail();updateLayers();
    }catch(e){if(request!==state.osrmRequest)return;state.osrmStatus='error';state.osrm=null;renderDetail();updateLayers();}
  }
  function orient(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
  function intersects(a,b,c,d){return orient(a,b,c)*orient(a,b,d)<=0&&orient(c,d,a)*orient(c,d,b)<=0;}
  function crosses(line,a,b){for(let i=0;i<line.length-1;i++)if(intersects(a,b,line[i],line[i+1]))return true;return false;}
  function geometryLines(g){return g?.type==='LineString'?[g.coordinates]:g?.type==='MultiLineString'?g.coordinates:[];}
  function updateDynamicBarriers(){
    if(!state.ready)return;
    if(state.map.getZoom()<13){state.dynamicBarriers=new Map();updateLayers();return;}
    try{
      const features=[
        ...state.map.querySourceFeatures('roads',{sourceLayer:'roads',filter:['match',['get','highway'],['motorway','trunk','primary'],true,false]}),
        ...state.map.querySourceFeatures('waterways',{sourceLayer:'waterways',filter:['match',['get','waterway'],['river','canal'],true,false]})
      ];
      const lines=[],seen=new Set();features.slice(0,1600).forEach(f=>{const key=(f.id||'')+JSON.stringify(f.geometry.coordinates[0]);if(seen.has(key))return;seen.add(key);geometryLines(f.geometry).forEach(line=>lines.push(line));});
      const bounds=state.map.getBounds(),grids=filteredGrids().filter(g=>bounds.contains(g.center)),candidates=new Map(state.data.candidates.map(c=>[c.id,c])),barriers=new Map();
      grids.forEach(g=>{const c=candidates.get(g.candidate_id),a=[c.lon,c.lat];if(distance(a,g.center)<50)return;barriers.set(g.id,lines.some(line=>crosses(line,a,g.center)));});
      state.dynamicBarriers=barriers;updateLayers();
    }catch(e){/* Tiles may not be loaded; static OSM rail barriers still apply. */}
  }
  function parseQuery(q){
    const parsed={city:null,rent_max:null,university_m:null,exclude_brand:null,exclude_radius_m:null,delivery:false,street:false,low_competition:false};
    parsed.city=state.data.candidates.map(c=>c.city).find(city=>q.includes(city))||null;
    let m=q.match(/(\d+(?:\.\d+)?)\s*万(?:印尼盾|IDR)?/i);if(m)parsed.rent_max=Math.round(+m[1]*10000);
    m=q.match(/(\d+(?:\.\d+)?)\s*(?:jt|百万)/i);if(m)parsed.rent_max=Math.round(+m[1]*1000000);
    if(q.includes('大学')){m=q.match(/(\d+(?:\.\d+)?)\s*公里[^，,]*大学/);parsed.university_m=m?+m[1]*1000:3000;}
    m=q.match(/(\d+)\s*米内无(蜜雪冰城|蜜雪|momoyo)/i);if(m){parsed.exclude_radius_m=+m[1];parsed.exclude_brand=m[2].toLowerCase()==='momoyo'?'momoyo':'mixue';}
    parsed.delivery=/外卖好做|外卖强|外卖友好/.test(q);parsed.street=/街边|街铺/.test(q);parsed.low_competition=/低竞争|竞争小/.test(q);return parsed;
  }
  function runQuery(){
    const q=$('query').value.trim();if(!q)return;const p=parseQuery(q),seedUniversities=state.data.pois.filter(x=>x.university),liveUniversities=NBOEvidence.universities();
    const universities=[...seedUniversities,...liveUniversities];
    const excluded=p.exclude_brand?state.beverage.points.filter(x=>x.brand_id===p.exclude_brand):[];
    const candidates=new Map(state.data.candidates.map(c=>[c.id,c]));
    const matches=state.data.grids.filter(g=>{
      const c=candidates.get(g.candidate_id);
      if(p.city&&c.city!==p.city)return false;
      if(p.rent_max&&NBOEvidence.rentFor(c,g)>p.rent_max)return false;
      if(p.street&&!c.street)return false;
      if(p.delivery&&g.rider_proxy<60)return false;
      if(p.low_competition&&g.saturation>35)return false;
      if(p.university_m&&!universities.some(u=>distance(g.center,[u.lon,u.lat])<=p.university_m))return false;
      if(p.exclude_brand){const degree=p.exclude_radius_m/100000+.004;const near=excluded.filter(x=>Math.abs(x.lon-g.center[0])<degree&&Math.abs(x.lat-g.center[1])<degree);if(near.some(x=>distance(g.center,[x.lon,x.lat])<=p.exclude_radius_m))return false;}
      return true;
    });
    state.queryIds=new Set(matches.map(g=>g.id));state.queryMatches=matches.length;state.dynamicBarriers=new Map();
    const byCandidate=new Map();matches.forEach(g=>byCandidate.set(g.candidate_id,Math.max(byCandidate.get(g.candidate_id)||0,effective(g))));
    const top=[...byCandidate.entries()].map(([id,base])=>{const c=candidates.get(id);return {c,base,quality:NBOEvidence.completeness(c),score:NBOEvidence.decisionScore(c,base)};}).sort((a,b)=>b.score-a.score).slice(0,3);
    const sql=`WHERE ${p.city?`city='${p.city}'`: 'city=ANY'}${p.rent_max?` AND rent_evidence_or_proxy<=${p.rent_max}`:''}${p.university_m?` AND university_distance<=${p.university_m}m`:''}${p.exclude_brand?` AND no_${p.exclude_brand}_within=${p.exclude_radius_m}m`:''}${p.delivery?' AND rider_proxy>=60':''}${p.street?' AND street=true':''}${p.low_competition?' AND saturation<=35':''}`;
    $('parse').classList.add('show');$('parse').textContent=`NL2GIS ${sql}\n命中 ${matches.length} 个 100m 网格 / ${byCandidate.size} 个候选；精确租金证据优先，其余用代理；Top3 按证据置信扣分后的决策分排序；大学含 ${liveUniversities.length} 个已加载 OSM 点。`;
    $('top3').innerHTML=top.length?top.map((x,i)=>`<div class="rec" data-id="${x.c.id}"><span class="score">${x.score.toFixed(1)}</span><b>${i+1}. ${esc(x.c.name)}</b><p>空间 ${x.base.toFixed(1)} · 证据 ${x.quality.score}/100 ${x.quality.grade} 级 · 置信扣分 ${(x.base-x.score).toFixed(1)}</p><p>需求 ${x.c.mcda.demand} · 竞争 ${x.c.mcda.competition} · 可达 ${x.c.mcda.access} · 履约 ${x.c.mcda.fulfillment}</p><p>${insight(x.c)}</p></div>`).join(''):'<div class="empty">没有网格同时满足全部硬条件。可减少预算、距离或竞品限制后重算。</div>';
    $('top3').querySelectorAll('.rec').forEach(el=>el.onclick=()=>selectCandidate(el.dataset.id,true));
    if(matches.length){const bounds=new maplibregl.LngLatBounds();matches.forEach(g=>bounds.extend(g.center));state.map.fitBounds(bounds,{padding:70,maxZoom:14,duration:900});}
    state.nlDebug={parsed:p,matches:matches.length,candidates:byCandidate.size,top3:top.map(x=>x.c.id),scores:top.map(x=>({id:x.c.id,base:+x.base.toFixed(1),decision:x.score,evidence:x.quality.score,grade:x.quality.grade})),liveUniversities:liveUniversities.length,sql};updateLayers();
  }
  function resetQuery(){
    state.queryIds=null;state.queryMatches=0;state.nlDebug=null;$('parse').classList.remove('show');$('top3').innerHTML='<div class="empty">输入条件后，系统会直接过滤空间网格并返回 Top3。</div>';state.map.flyTo({center:[117.5,-2.2],zoom:4.6,duration:800});updateLayers();
  }
  function bindControls(){
    const metricIds={mcdaGrid:'mcda',demandHeat:'demand',youth:'youth_proxy',middle:'middle_proxy',saturation:'saturation',rent:'rent'};
    Object.keys(metricIds).forEach(id=>$(id).addEventListener('change',()=>{if($(id).checked)state.metric=metricIds[id];else if(state.metric===metricIds[id])state.metric=$('mcdaGrid').checked?'mcda':'demand';updateLayers();}));
    ['poiTrigger','competitors','complements','transitBands','barriers','isochrones','compliance','candidates'].forEach(id=>$(id).addEventListener('change',updateLayers));
    $('runQuery').onclick=runQuery;$('query').onkeydown=e=>{if(e.key==='Enter')runQuery();};$('resetQuery').onclick=resetQuery;
    document.querySelectorAll('.quick [data-q]').forEach(btn=>btn.onclick=()=>{$('query').value=btn.dataset.q;runQuery();});
    $('baseGray').onclick=()=>setBase('gray');$('baseStreet').onclick=()=>setBase('street');
  }
  function setBase(base){
    if(state.base===base)return;state.base=base;$('baseGray').classList.toggle('on',base==='gray');$('baseStreet').classList.toggle('on',base==='street');
    state.map.getSource('esri').setTiles([ESRI[base]]);
  }
  function renderSources(){
    const d=state.data;$('sourceNote').innerHTML=Object.values(d.sources).map(esc).join('<br><br>')+'<br><br>'+Object.values(d.proxy_notes).map(esc).join('<br>');
  }
  async function init(){
    const [model,bev]=await Promise.all([fetch('./data/spatial_model.json').then(r=>r.json()),fetch('./data/beverage_index.json').then(r=>r.json())]);
    state.data=model;state.beverage=bev;bev.brands.forEach(b=>state.enabledBrands.add(b.id));await NBOEvidence.init(model.candidates);
    const protocol=new pmtiles.Protocol();maplibregl.addProtocol('pmtiles',protocol.tile);
    const map=new maplibregl.Map({container:'map',style:buildStyle('gray'),center:[117.5,-2.2],zoom:4.6,minZoom:4,maxZoom:19,attributionControl:{compact:true}});state.map=map;
    map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-left');
    map.on('load',()=>{state.overlay=new deck.MapboxOverlay({interleaved:false,layers:[]});map.addControl(state.overlay);state.ready=true;updateLayers();setTimeout(refreshLivePOIs,800);});
    map.on('zoom',updateLayers);map.on('moveend',()=>{updateLayers();setTimeout(updateDynamicBarriers,250);setTimeout(refreshLivePOIs,600);});map.on('styledata',syncBaseLayers);map.on('idle',refreshLivePOIs);
    window.addEventListener('nbo-evidence-change',()=>{renderDetail();renderCandidates();if(state.nlDebug)runQuery();else updateLayers();});
    renderBrandList();renderCandidates();renderSources();bindControls();
    window._spatialDebug=()=>({ready:state.ready,zoom:state.map.getZoom(),level:state.level,metric:state.metric,cities:state.data.cities.length,candidates:state.data.candidates.length,grids:state.data.grids.length,queryMatches:state.queryMatches,selected:state.selected,brands:state.enabledBrands.size,competitors:filteredCompetitors().length,transitLines:state.data.transit_lines.length,stations:state.data.stations.length,mrtStations:state.data.stations.filter(s=>s.mode==='MRT').length,railBarriers:state.data.rail_barriers.length,dynamicBarriers:[...state.dynamicBarriers.values()].filter(Boolean).length,osrmStatus:state.osrmStatus,base:state.base});
    window._nlDebug=()=>state.nlDebug;window._osrmDebug=()=>({status:state.osrmStatus,motor:state.osrm?.motor.length||0,walk:state.osrm?.walk.length||0,stops:state.osrm?.stops.length||0,motor5:state.osrm?.motor.filter(x=>x.duration<=300).length||0,walk5:state.osrm?.walk.filter(x=>x.duration<=300).length||0});
    window._evidenceDebug=()=>NBOEvidence.debug();
    window._poiDebug=()=>{const features=state.map.querySourceFeatures('poi',{sourceLayer:'points_of_interest'});return {count:features.length,properties:features.slice(0,12).map(f=>f.properties),types:[...new Set(features.map(f=>f.geometry?.type))]};};
  }
  init().catch(e=>{console.error(e);$('level').innerHTML='<b>空间数据加载失败</b><span>请检查本地数据与网络</span>';});
})();
