/* Traceable listing + field evidence store. Local additions stay in this browser. */
(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const KEY = 'nbo_site_evidence_v1';
  const FIELDS = ['record_type','id','candidate_id','city','area','title','rent_year_idr','building_sqm','observed_at','source_url','lon','lat','halal_status','exhaust_status','rider_status','notes'];
  let base = {listings:[],surveys:[]}, local = [], candidates = [], selected = null;
  let livePois = {universities:[],malls:[]};
  try { local = JSON.parse(localStorage.getItem(KEY) || '[]'); if(!Array.isArray(local)) local=[]; } catch { local=[]; }
  const all = () => [...local, ...base.listings, ...base.surveys];
  const listings = () => all().filter(x => x.record_type === 'listing');
  const surveys = () => all().filter(x => x.record_type === 'survey');
  const money = value => `Rp ${Number(value).toLocaleString('id-ID')}`;
  const status = value => ({pending:'待核验',pass:'符合',fail:'不符合',good:'可停靠',poor:'困难'}[value] || value || '待核验');
  const changed = () => { try { localStorage.setItem(KEY, JSON.stringify(local)); } catch {} render(); window.dispatchEvent(new Event('nbo-evidence-change')); };

  function normalize(row) {
    const out = {}; FIELDS.forEach(k => out[k] = String(row[k] ?? '').trim());
    if(!['listing','survey'].includes(out.record_type) || !out.id || !out.title || !/^\d{4}-\d{2}-\d{2}$/.test(out.observed_at)) throw new Error('记录类型、ID、标题和 ISO 日期为必填');
    if(out.source_url && !out.source_url.startsWith('https://')) throw new Error('来源链接必须使用 HTTPS');
    if(out.record_type === 'listing' && (!out.source_url || !(+out.rent_year_idr > 0))) throw new Error('公开租金必须有 HTTPS 来源和年租');
    if(out.record_type === 'survey' && !out.candidate_id) throw new Error('现场核验必须关联候选点');
    if(all().some(x => x.id === out.id)) throw new Error(`证据 ID 重复：${out.id}`);
    out.rent_year_idr = +out.rent_year_idr > 0 ? Math.round(+out.rent_year_idr) : null;
    out.rent_month_idr = out.rent_year_idr ? Math.round(out.rent_year_idr/12) : null;
    out.building_sqm = +out.building_sqm > 0 ? +out.building_sqm : null;
    out.lon = out.lon !== '' ? +out.lon : null; out.lat = out.lat !== '' ? +out.lat : null;
    if((out.lon === null) !== (out.lat === null) || (out.lon !== null && (!Number.isFinite(out.lon) || !Number.isFinite(out.lat) || Math.abs(out.lon)>180 || Math.abs(out.lat)>90))) throw new Error('经纬度必须成对且有效');
    out.location_precision = out.lon === null ? 'area' : 'exact';
    out.availability = out.record_type === 'listing' ? 'unverified' : 'field_recorded';
    out.storage = 'local';
    return out;
  }
  function parseCSV(text) {
    const rows=[]; let row=[],cell='',quoted=false;
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(quoted){ if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c; }
      else if(c==='"')quoted=true; else if(c===','){row.push(cell);cell='';}
      else if(c==='\n'){row.push(cell);if(row.some(x=>x.trim()))rows.push(row);row=[];cell='';}
      else if(c!=='\r')cell+=c;
    }
    row.push(cell);if(row.some(x=>x.trim()))rows.push(row);
    if(rows.length<2)return [];
    const head=rows[0].map(x=>x.trim());if(!FIELDS.every(k=>head.includes(k)))throw new Error('CSV 表头不符合模板');
    return rows.slice(1).map(values=>normalize(Object.fromEntries(head.map((k,i)=>[k,values[i]||'']))));
  }
  function csvText(rows) {
    const quote = value => `"${String(value ?? '').replace(/"/g,'""')}"`;
    return '\ufeff'+FIELDS.join(',')+'\n'+rows.map(r=>FIELDS.map(k=>quote(r[k])).join(',')).join('\n');
  }
  function download(name,text,type='text/csv;charset=utf-8') {
    const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function forCandidate(c) {
    return all().filter(x => x.candidate_id===c.id || (!x.candidate_id && x.city===c.city)).sort((a,b) => (a.candidate_id===c.id?-1:1)-(b.candidate_id===c.id?-1:1) || b.observed_at.localeCompare(a.observed_at));
  }
  function exactRent(c) {
    return all().filter(x => x.candidate_id===c.id && x.location_precision==='exact' && x.rent_month_idr).sort((a,b)=>b.observed_at.localeCompare(a.observed_at))[0] || null;
  }
  function completeness(c) {
    const linked=all().filter(x=>x.candidate_id===c.id),rent=exactRent(c);
    const hasSurvey=linked.some(x=>x.record_type==='survey'),hasExactLocation=linked.some(x=>x.location_precision==='exact');
    const score=(rent?50:0)+(hasSurvey?30:0)+(hasExactLocation?20:0);
    return {score,grade:score>=80?'A':score>=50?'B':score>0?'C':'D',factor:.85+.15*score/100,hasExactRent:!!rent,hasSurvey,hasExactLocation,linked:linked.length};
  }
  function decisionScore(c,base=c.suitability){return +(base*completeness(c).factor).toFixed(1);}
  function recordHTML(x,compact=false) {
    const rent=x.rent_month_idr?`${money(x.rent_month_idr)}/月（年租 ${money(x.rent_year_idr)}）`:'未记录租金';
    const survey=x.record_type==='survey'?`<br>Halal ${status(x.halal_status)} · 排烟 ${status(x.exhaust_status)} · 停靠 ${status(x.rider_status)}`:'';
    const source=x.source_url?` · <a href="${esc(x.source_url)}" target="_blank" rel="noopener">来源</a>`:'';
    return `<div class="evidence-row"><b>${esc(x.title)}</b><p>${rent} · ${esc(x.observed_at)}${source}<br>${x.location_precision==='exact'?'精确坐标':'区域参考'} · ${x.availability==='unverified'?'当前可用性未核验':'现场录入'}${survey}${!compact&&x.notes?`<br>${esc(x.notes)}`:''}</p></div>`;
  }
  function render() {
    if(!$('listingCount'))return;
    $('listingCount').textContent=listings().length;$('surveyCount').textContent=surveys().length;$('osmPoiCount').textContent=livePois.universities.length+livePois.malls.length;
    const c=candidates.find(x=>x.id===selected),records=c?forCandidate(c):all().sort((a,b)=>b.observed_at.localeCompare(a.observed_at));
    $('evidenceTitle').textContent=c?`${c.name} · 关联证据`:'最新证据 · 选择候选后按商圈过滤';
    $('evidenceList').innerHTML=records.length?records.slice(0,4).map(x=>recordHTML(x,true)).join(''):'<div class="empty">尚无关联证据。可导入公开挂牌或保存现场核验。</div>';
  }
  function saveSurvey() {
    const c=candidates.find(x=>x.id===$('surveyCandidate').value);if(!c)return;
    const month=+$('surveyRent').value;
    const row={record_type:'survey',id:`SURVEY-${Date.now()}`,candidate_id:c.id,city:c.city,area:c.area,
      title:`现场核验 · ${c.name}`,rent_year_idr:month>0?month*12:'',observed_at:$('surveyDate').value,
      source_url:$('surveySource').value,lon:$('surveyLon').value,lat:$('surveyLat').value,
      halal_status:$('surveyHalal').value,exhaust_status:$('surveyExhaust').value,rider_status:$('surveyRider').value,notes:$('surveyNotes').value};
    try { local.unshift(normalize(row));changed();$('surveyNotes').value='';$('surveySource').value='';$('surveyRent').value='';$('importStatus').textContent='现场核验已保存到本机浏览器。'; }
    catch(error){$('importStatus').textContent=error.message;}
  }
  function bind() {
    $('surveyCandidate').innerHTML=candidates.map(c=>`<option value="${esc(c.id)}">${esc(c.city)} · ${esc(c.name)}</option>`).join('');
    $('surveyDate').value=new Date().toISOString().slice(0,10);
    $('saveSurvey').onclick=saveSurvey;
    $('downloadTemplate').onclick=()=>download('nusantara-site-evidence-template.csv',csvText([]));
    $('exportEvidence').onclick=()=>download('nusantara-site-evidence.csv',csvText(all()));
    $('importEvidence').onchange=async event=>{const file=event.target.files[0];if(!file)return;try{const rows=parseCSV(await file.text());local=[...rows,...local];changed();$('importStatus').textContent=`已导入 ${rows.length} 条证据，仅保存在本机。`;}catch(error){$('importStatus').textContent=error.message;}event.target.value='';};
  }
  async function init(candidateData) {
    candidates=candidateData;
    base=await fetch('./data/site_evidence.json').then(r=>{if(!r.ok)throw new Error(`证据库 ${r.status}`);return r.json();});
    bind();render();return api;
  }
  function selectCandidate(id){selected=id;if($('surveyCandidate'))$('surveyCandidate').value=id;render();}
  function detailHTML(c){
    const records=forCandidate(c),rent=exactRent(c),q=completeness(c),decision=decisionScore(c),yn=v=>v?'已具备':'缺失';
    return `<div class="evidence-detail evidence-quality"><b>证据完整度 ${q.score}/100 · ${q.grade} 级</b><p>精确租金 ${yn(q.hasExactRent)} · 现场核验 ${yn(q.hasSurvey)} · 精确坐标 ${yn(q.hasExactLocation)}</p><p>空间 MCDA ${c.suitability} → 决策分 ${decision}（置信扣分 ${(c.suitability-decision).toFixed(1)}）；只调整候选排序，不改写原始空间因子；不代表 Halal 或其他合规已通过。</p></div><div class="evidence-detail"><b>真实证据 · ${records.length} 条</b>${rent?`<p>硬过滤采用精确租金证据 ${money(rent.rent_month_idr)}/月，不再使用该点租金代理。</p>`:'<p>当前无精确到铺位的租金证据，硬过滤仍使用明确标注的租金代理。</p>'}${records.length?records.slice(0,3).map(x=>recordHTML(x)).join(''):'<p>该区域尚无公开挂牌或现场记录。</p>'}</div>`;
  }
  function setLivePois(value){livePois=value;render();}
  const api={init,selectCandidate,forCandidate,detailHTML,exactRent,completeness,decisionScore,setLivePois,
    rentFor:(c,g)=>exactRent(c)?.rent_month_idr || g.rent_proxy_idr,
    points:()=>all().filter(x=>x.lon!==null&&x.lat!==null),
    universities:()=>livePois.universities,
    debug:()=>{const c=selected&&candidates.find(c=>c.id===selected);return {listings:listings().length,surveys:surveys().length,local:local.length,selected,osmUniversities:livePois.universities.length,osmMalls:livePois.malls.length,points:all().filter(x=>x.lon!==null).length,exactRent:c?exactRent(c)?.id||null:null,quality:c?completeness(c):null,decisionScore:c?decisionScore(c):null};}};
  window.NBOEvidence=api;
})();
