'use strict';
const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
let rows = [], busy = false, lastText = '', dragging = false;
const zoomViews = new Map();
const hoverPositions = new Map();
function parseCSV(text) {
  // Only accept complete lines: the writer may be appending the last row.
  const lines = text.split(/\r?\n/); lines.pop();
  if (!lines.length) return [];
  const headers = lines.shift().split(',');
  for (const key of ['timestamp','elapsed_seconds','accepted_steps','attempts','rejected_attempts','L','next_dt','event'])
    if (!headers.includes(key)) throw new Error('CSV header is missing ' + key);
  return lines.filter(Boolean).map(line => {
    const fields=line.split(','); if(fields.length!==headers.length)return null;
    const r=Object.fromEntries(headers.map((key,i)=>[key,fields[i]]));
    const result={timestamp:r.timestamp,elapsed:Number(r.elapsed_seconds),iteration:Number(r.accepted_steps),
      attempt:Number(r.attempts),rejected:Number(r.rejected_attempts),change:Number(r.L),dt:Number(r.next_dt),
      normalised:r.L_normalised===''?null:Number(r.L_normalised),event:r.event,
      speed:r.seconds_per_attempt===''?null:Number(r.seconds_per_attempt)};
    return r.L!=='' && Number.isFinite(result.change) && result.change>=0 &&
      Number.isInteger(result.iteration) && result.iteration>=0 && Number.isInteger(result.attempt) &&
      Number.isFinite(result.elapsed) && result.elapsed>=0 ? result : null;
  }).filter(Boolean);
}
function element(tag, attributes={}, content='') {
  const el=document.createElementNS(NS,tag);
  Object.entries(attributes).forEach(([key,value])=>el.setAttribute(key,value));
  el.textContent=content;return el;
}
function chart(id, points, log, height, threshold=null) {
  const svg=$(id);svg.replaceChildren();
  const width=svg.clientWidth || 1000; height=svg.clientHeight || height;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  const left=70,right=18,top=24,bottom=38,plotW=width-left-right,plotH=height-top-bottom;
  if (!points.length) {svg.append(element('text',{x:width/2,y:height/2,'text-anchor':'middle'},'Waiting for logged data'));return;}
  const isTime=$('axis').value==='time';
  const getX=r=>isTime?r.elapsed/60:r.attempt;
  const maxX=Math.max(...points.map(getX),1);
  let low,high;
  if(log){
    const positives=points.map(r=>r.value).filter(v=>v>0);
    if(Number.isFinite(threshold)&&threshold>0)positives.push(threshold);
    const min=positives.length?Math.min(...positives):1e-12;
    const max=positives.length?Math.max(...positives):1e-11;
    const lo=Math.log10(min),hi=Math.log10(max),pad=Math.max((hi-lo)*.1,.00001);
    low=lo-pad;high=hi+pad;
    if(points.some(r=>r.value===0))low=Math.min(low,lo-1);
  } else {low=0;high=Math.max(...points.map(r=>r.value),.001)*1.15;}
  const full={x0:0,x1:maxX,y0:low,y1:high};
  const view=zoomViews.get(id) || full;
  const {x0,x1,y0,y1}=view;
  svg.dataset.zoomed=String(zoomViews.has(id));
  svg.dataset.xMin=x0;svg.dataset.xMax=x1;svg.dataset.yMin=y0;svg.dataset.yMax=y1;
  const reset=document.querySelector(`[data-reset="${id}"]`);if(reset)reset.disabled=!zoomViews.has(id);
  const x=r=>left+(getX(r)-x0)/(x1-x0)*plotW;
  const transform=value=>log?Math.log10(Math.max(value,10**full.y0)):value;
  const y=value=>top+plotH-(transform(value)-y0)/(y1-y0)*plotH;
  const precision=Math.min(8,Math.max(2,Math.ceil(-Math.log10(y1-y0))+2));
  for(let i=0;i<=5;i++){
    const xx=left+plotW*i/5, yy=top+plotH*i/5;
    svg.append(element('line',{x1:xx,x2:xx,y1:top,y2:top+plotH,class:'grid'}));
    svg.append(element('text',{x:xx,y:height-24,'text-anchor':'middle'},(x0+(x1-x0)*i/5).toLocaleString(undefined,{maximumFractionDigits:isTime?3:2})));
    svg.append(element('line',{x1:left,x2:width-right,y1:yy,y2:yy,class:'grid'}));
    const transformed=y1-(y1-y0)*i/5;
    const value=log?10**transformed:transformed;
    svg.append(element('text',{x:left-10,y:yy+4,'text-anchor':'end'},log?value.toExponential(precision):Number(value.toPrecision(6)).toString()));
  }
  const defs=element('defs'),clip=element('clipPath',{id:`clip-${id}`});
  clip.append(element('rect',{x:left,y:top,width:plotW,height:plotH}));defs.append(clip);svg.append(defs);
  const curve=element('g',{'clip-path':`url(#clip-${id})`});
  if(Number.isFinite(threshold)&&threshold>0){
    const yy=y(threshold);
    curve.append(element('line',{x1:left,x2:left+plotW,y1:yy,y2:yy,class:'target'}));
    curve.append(element('text',{x:left+plotW-6,y:yy-6,'text-anchor':'end'},`Initial dt / 1000 · ${threshold.toExponential(1)}`));
  }
  curve.append(element('path',{d:points.map((r,i)=>(i?'L':'M')+x(r).toFixed(2)+','+y(r.value).toFixed(2)).join(' '),class:'line'}));
  const latest=points[points.length-1];curve.append(element('circle',{cx:x(latest),cy:y(latest.value),r:3,fill:'#18765e'}));svg.append(curve);
  svg.append(element('text',{x:left+plotW/2,y:height-5,'text-anchor':'middle'},isTime?'Wall-clock elapsed (minutes)':'Attempt'));
  const selection=element('rect',{class:'zoom-selection',visibility:'hidden','pointer-events':'none'});
  svg.append(selection);
  const overlay=element('rect',{x:left,y:top,width:plotW,height:plotH,fill:'transparent',class:'zoom-overlay'});
  const position=event=>{
    const rect=svg.getBoundingClientRect();
    return {x:Math.max(left,Math.min(left+plotW,(event.clientX-rect.left)*width/rect.width)),
            y:Math.max(top,Math.min(top+plotH,(event.clientY-rect.top)*height/rect.height))};
  };
  const hover=element('g',{class:'hover-point',visibility:'hidden','pointer-events':'none'});
  const guide=element('line',{y1:top,y2:top+plotH,class:'hover-guide'});
  const halo=element('circle',{r:10,class:'hover-halo'});
  const dot=element('circle',{r:5,class:'hover-dot'});
  const bubble=element('g',{class:'hover-tooltip'});
  const box=element('rect',{rx:6,height:66});
  const labels=[0,1,2].map(i=>element('text',{x:10,y:18+i*17}));
  bubble.append(box,...labels);hover.append(guide,halo,dot,bubble);
  function showHover(pos){
    const visible=points.filter(r=>x(r)>=left && x(r)<=left+plotW && y(r.value)>=top && y(r.value)<=top+plotH);
    if(!visible.length){hover.setAttribute('visibility','hidden');return;}
    let nearest=visible[0];
    for(const r of visible){
      const dx=Math.abs(x(r)-pos.x),best=Math.abs(x(nearest)-pos.x);
      if(dx<best || (Math.abs(dx-best)<1e-8 && Math.abs(y(r.value)-pos.y)<Math.abs(y(nearest.value)-pos.y)))nearest=r;
    }
    const px=x(nearest),py=y(nearest.value);
    guide.setAttribute('x1',px);guide.setAttribute('x2',px);
    for(const circle of [halo,dot]){circle.setAttribute('cx',px);circle.setAttribute('cy',py);}
    const metric=id==='dtChart'?`Next dt: ${nearest.dt.toExponential(6)}`:
      id==='speedChart'?`Time / attempt: ${nearest.speed.toFixed(6)} s`:`L: ${nearest.change.toExponential(6)}`;
    labels[0].textContent=metric;
    labels[1].textContent=`Attempt ${nearest.attempt.toLocaleString()} · accepted ${nearest.iteration.toLocaleString()}`;
    labels[2].textContent=`${(nearest.elapsed/60).toFixed(3)} min · ${nearest.event}`;
    hover.setAttribute('visibility','visible');
    const boxW=Math.min(plotW-8,Math.max(...labels.map(t=>t.getComputedTextLength()))+20);
    box.setAttribute('width',boxW);
    let bx=px+14;if(bx+boxW>left+plotW)bx=px-boxW-14;
    bx=Math.max(left+4,Math.min(left+plotW-boxW-4,bx));
    let by=py-78;if(by<top)by=py+14;
    by=Math.max(top+2,Math.min(top+plotH-68,by));
    bubble.setAttribute('transform',`translate(${bx},${by})`);
    const detail=id==='dtChart'?'dtHover':id==='errorChart'?'hover':null;
    if(detail)$(detail).textContent=`${metric} · attempt ${nearest.attempt} · ${nearest.timestamp}`;
    dot.dataset.attempt=nearest.attempt;dot.dataset.value=nearest.value;
  }
  const dataX=px=>x0+(px-left)/plotW*(x1-x0);
  const dataY=py=>y1-(py-top)/plotH*(y1-y0);
  function setView(next){
    if(next.x1-next.x0 <= Math.max(1,Math.abs(next.x1))*1e-12 || next.y1-next.y0 <= Math.max(1,Math.abs(next.y1))*1e-12)return;
    zoomViews.set(id,next);render();
  }
  let anchor=null;
  overlay.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;
    event.preventDefault();anchor=position(event);dragging=true;
    hoverPositions.delete(id);hover.setAttribute('visibility','hidden');
    try{overlay.setPointerCapture(event.pointerId);}catch(_){}
    selection.setAttribute('visibility','visible');
    for(const [key,value] of Object.entries({x:anchor.x,y:anchor.y,width:0,height:0}))selection.setAttribute(key,value);
  });
  overlay.addEventListener('pointermove',event=>{
    const pos=position(event);
    if(anchor){
      for(const [key,value] of Object.entries({x:Math.min(pos.x,anchor.x),y:Math.min(pos.y,anchor.y),width:Math.abs(pos.x-anchor.x),height:Math.abs(pos.y-anchor.y)}))selection.setAttribute(key,value);
      return;
    }
    hoverPositions.set(id,{x:(pos.x-left)/plotW,y:(pos.y-top)/plotH});
    showHover(pos);
  });
  overlay.addEventListener('pointerleave',()=>{hoverPositions.delete(id);hover.setAttribute('visibility','hidden');});
  overlay.addEventListener('pointerup',event=>{
    if(!anchor)return;
    const pos=position(event),dx=Math.abs(pos.x-anchor.x),dy=Math.abs(pos.y-anchor.y);
    const next={x0:dx>8?dataX(Math.min(pos.x,anchor.x)):x0,x1:dx>8?dataX(Math.max(pos.x,anchor.x)):x1,
                y0:dy>8?dataY(Math.max(pos.y,anchor.y)):y0,y1:dy>8?dataY(Math.min(pos.y,anchor.y)):y1};
    anchor=null;dragging=false;
    if(dx>8||dy>8)setView(next);else render();
  });
  overlay.addEventListener('pointercancel',()=>{anchor=null;dragging=false;render();});
  overlay.addEventListener('dblclick',()=>{zoomViews.delete(id);render();});
  overlay.addEventListener('wheel',event=>{
    event.preventDefault();if(dragging)return;
    const pos=position(event),cx=dataX(pos.x),cy=dataY(pos.y);
    const factor=Math.exp(Math.max(-300,Math.min(300,event.deltaY))*.002);
    const fit=(center,a,b,min,max)=>{
      const span=Math.min((b-a)*factor,max-min);
      const fraction=(center-a)/(b-a);
      const start=Math.max(min,Math.min(max-span,center-span*fraction));return [start,start+span];
    };
    const [a,b]=fit(cx,x0,x1,full.x0,full.x1),[c,d]=fit(cy,y0,y1,full.y0,full.y1);
    setView({x0:a,x1:b,y0:c,y1:d});
  },{passive:false});
  svg.append(overlay,hover);
  const remembered=hoverPositions.get(id);
  if(remembered)showHover({x:left+remembered.x*plotW,y:top+remembered.y*plotH});
}
function render(){
  if(dragging)return;
  if(rows.length){
    const last=rows[rows.length-1];
    $('iteration').textContent=last.iteration.toLocaleString();
    $('attempts').textContent=`${last.attempt.toLocaleString()} attempts · ${last.rejected.toLocaleString()} rejected`;
    $('change').textContent=last.change.toExponential(4);
    $('distance').textContent=last.normalised!==null&&Number.isFinite(last.normalised)?`L / initial L = ${last.normalised.toFixed(6)}`:'Initial L is zero';
    $('elapsed').textContent=last.elapsed<60?last.elapsed.toFixed(1)+' s':(last.elapsed/60).toFixed(1)+' min';
    $('stamp').textContent=last.timestamp;
    const timed=rows.filter(r=>r.speed!==null&&Number.isFinite(r.speed));
    $('speed').textContent=timed.length?timed[timed.length-1].speed.toFixed(3)+' s':'—';
    $('dt').textContent=Number.isFinite(last.dt)?last.dt.toExponential(3):'—';
    const initial=rows.find(r=>r.event==='initial'&&Number.isFinite(r.dt)&&r.dt>0);
    const ratio=initial&&Number.isFinite(last.dt)?last.dt/initial.dt:null;
    $('dtFraction').textContent=ratio!==null?`${(ratio*100).toFixed(3)}% × initial dt`:'— × initial dt';
    $('dtFloor').textContent=ratio!==null?`${(ratio*1000).toFixed(3)} × final dt`:'— × final dt';
    $('dtFraction').title=initial?`Starting dt: ${initial.dt.toExponential(6)}`:'';
    $('dtFloor').title=initial?`Stopping threshold: starting dt / 1000 = ${(initial.dt/1000).toExponential(6)}; checked after rejection`:'';
    const minDt=rows.reduce((minimum,r)=>Number.isFinite(r.dt)&&r.dt>0?Math.min(minimum,r.dt):minimum,Infinity);
    $('minDt').textContent=`Lowest recorded dt: ${Number.isFinite(minDt)?minDt.toExponential(6):'—'}`;
    $('event').textContent=last.event==='finished'?'Code finished normally':`Latest event: ${last.event}`;
  }
  chart('errorChart',rows.map(r=>({...r,value:r.change})),true,320);
  const startingDt=rows.find(r=>r.event==='initial'&&Number.isFinite(r.dt)&&r.dt>0)?.dt;
  chart('dtChart',rows.filter(r=>Number.isFinite(r.dt)&&r.dt>0).map(r=>({...r,value:r.dt})),true,320,startingDt?startingDt/1000:null);
  chart('speedChart',rows.filter(r=>r.speed!==null&&Number.isFinite(r.speed)).map(r=>({...r,value:r.speed})),false,260);
}
async function refresh(){
  if(busy)return;busy=true;
  try{
    const response=await fetch('/data.csv',{cache:'no-store',signal:AbortSignal.timeout(5000)});
    if(!response.ok)throw new Error('CSV unavailable (HTTP '+response.status+')');
    const text=await response.text();const parsed=parseCSV(text);
    if(text!==lastText){rows=parsed;lastText=text;render();}
    $('status').textContent=rows.length?'Reading CSV · '+rows.length.toLocaleString()+' points':'Waiting for complete CSV rows';$('status').classList.remove('error');
    $('checked').textContent='Checked '+new Date().toLocaleTimeString()+' · refresh every 2 s';
    const last=rows[rows.length-1];
    const age=last?Math.max(0,(Date.now()-new Date(last.timestamp).getTime())/1000):null;
    $('activity').textContent=last?'Last logged sample '+(Number.isFinite(age)?Math.floor(age)+' seconds ago. ':'')+'CSV polling continues; this does not establish whether the solver is still running.':'Waiting for initial L. The field setup may still be running.';
  }catch(error){$('status').textContent='Refresh failed';$('status').classList.add('error');$('checked').textContent=error.message+' · retrying';}
  finally{busy=false;}
}
document.querySelectorAll('[data-fullscreen]').forEach(button=>button.addEventListener('click',async()=>{
  const panel=$(button.dataset.fullscreen).closest('.panel');
  try{
    if(document.fullscreenElement===panel)await document.exitFullscreen();
    else await panel.requestFullscreen();
  }catch(error){$('checked').textContent='Could not open fullscreen: '+error.message;}
}));
document.addEventListener('fullscreenchange',()=>{
  dragging=false;
  document.querySelectorAll('[data-fullscreen]').forEach(button=>{
    const active=document.fullscreenElement===$(button.dataset.fullscreen).closest('.panel');
    button.textContent=active?'Exit fullscreen':'Fullscreen';
    button.setAttribute('aria-pressed',String(active));
    button.setAttribute('aria-label',(active?'Exit fullscreen':'Fullscreen')+' graph');
  });
  requestAnimationFrame(render);
});
window.addEventListener('resize',render);
$('axis').addEventListener('change',()=>{zoomViews.clear();dragging=false;render();});
document.querySelectorAll('[data-reset]').forEach(button=>button.addEventListener('click',()=>{zoomViews.delete(button.dataset.reset);dragging=false;render();}));$('refresh').addEventListener('click',refresh);
fetch('/info',{cache:'no-store'}).then(r=>r.json()).then(info=>{$('source').textContent=info.csv;$('source').title=info.csv;}).catch(()=>{$('source').textContent='Local convergence.csv';});
render();refresh();setInterval(refresh,2000);
