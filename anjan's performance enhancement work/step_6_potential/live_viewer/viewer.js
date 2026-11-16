'use strict';
const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
let rows = [], busy = false, lastText = '';
function parseCSV(text) {
  // Only accept complete lines: the writer may be appending the last row.
  const lines = text.split(/\r?\n/); lines.pop();
  if (!lines.length) return [];
  const headers = lines.shift().split(',');
  for (const key of ['timestamp','solver_elapsed_seconds','iteration','max_change'])
    if (!headers.includes(key)) throw new Error('CSV header is missing ' + key);
  return lines.filter(Boolean).map(line => {
    const fields = line.split(',');
    if (fields.length !== headers.length) return null;
    const r = Object.fromEntries(headers.map((key,i) => [key,fields[i]]));
    const result = {timestamp:r.timestamp,iteration:Number(r.iteration),elapsed:Number(r.solver_elapsed_seconds),change:Number(r.max_change),speed:r.mean_seconds_per_iteration === '' ? null : Number(r.mean_seconds_per_iteration)};
    return fields[headers.indexOf('iteration')] !== '' && fields[headers.indexOf('max_change')] !== '' && Number.isInteger(result.iteration) && result.iteration>=0 && Number.isFinite(result.elapsed) && result.elapsed>=0 && Number.isFinite(result.change) && result.change>=0 ? result : null;
  }).filter(Boolean);
}
function element(tag, attributes={}, content='') {
  const el=document.createElementNS(NS,tag);
  Object.entries(attributes).forEach(([key,value])=>el.setAttribute(key,value));
  el.textContent=content;return el;
}
function chart(id, points, log, height) {
  const svg=$(id);svg.replaceChildren();
  const width=svg.clientWidth || 1000; height=svg.clientHeight || height;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  const left=62,right=18,top=24,bottom=38,plotW=width-left-right,plotH=height-top-bottom;
  if (!points.length) {svg.append(element('text',{x:width/2,y:height/2,'text-anchor':'middle'},'Waiting for logged data'));return;}
  const isTime=$('axis').value==='time';
  const getX=r=>isTime?r.elapsed/60:r.iteration;
  let maxX=Math.max(...points.map(getX),1);
  let low,high;
  if(log){low=Math.floor(Math.log10(Math.min(.001,...points.filter(r=>r.value>0).map(r=>r.value))));high=Math.ceil(Math.log10(Math.max(.001,...points.map(r=>r.value))));if(high<=low)high=low+1;}
  else {low=0;high=Math.max(...points.map(r=>r.value),.001)*1.15;}
  const x=r=>left+getX(r)/maxX*plotW;
  const y=value=>top+plotH-(log?(Math.log10(Math.max(value,10**low))-low)/(high-low):(value-low)/(high-low))*plotH;
  for(let i=0;i<=5;i++){
    const xx=left+plotW*i/5, yy=top+plotH*i/5;
    svg.append(element('line',{x1:xx,x2:xx,y1:top,y2:top+plotH,class:'grid'}));
    svg.append(element('text',{x:xx,y:height-24,'text-anchor':'middle'},(maxX*i/5).toLocaleString(undefined,{maximumFractionDigits:isTime?1:0})));
    svg.append(element('line',{x1:left,x2:width-right,y1:yy,y2:yy,class:'grid'}));
    const value=log?10**(high-(high-low)*i/5):high*(1-i/5);
    svg.append(element('text',{x:left-10,y:yy+4,'text-anchor':'end'},log?value.toExponential(1):value.toFixed(3)));
  }
  if(log){svg.append(element('line',{x1:left,x2:width-right,y1:y(.001),y2:y(.001),class:'target'}));svg.append(element('text',{x:width-right,y:y(.001)-7,'text-anchor':'end'},'Target 0.001'));}
  svg.append(element('path',{d:points.map((r,i)=>(i?'L':'M')+x(r).toFixed(2)+','+y(r.value).toFixed(2)).join(' '),class:'line'}));
  const latest=points[points.length-1];svg.append(element('circle',{cx:x(latest),cy:y(latest.value),r:3,fill:'#18765e'}));
  svg.append(element('text',{x:left+plotW/2,y:height-5,'text-anchor':'middle'},isTime?'Solver elapsed (minutes)':'Iteration'));
  if(log){
    const overlay=element('rect',{x:left,y:top,width:plotW,height:plotH,fill:'transparent'});
    overlay.addEventListener('pointermove',event=>{
      const rect=svg.getBoundingClientRect();const position=((event.clientX-rect.left)*width/rect.width-left)/plotW*maxX;
      let nearest=points[0];for(const r of points)if(Math.abs(getX(r)-position)<Math.abs(getX(nearest)-position))nearest=r;
      $('hover').textContent=`Iteration ${nearest.iteration.toLocaleString()} · max change ${nearest.change.toExponential(6)} · ${(nearest.elapsed/60).toFixed(2)} min · ${nearest.timestamp}`;
    });svg.append(overlay);
  }
}
function render(){
  if(rows.length){const last=rows[rows.length-1];$('iteration').textContent=last.iteration.toLocaleString();$('change').textContent=last.change.toExponential(3);$('elapsed').textContent=last.elapsed<60?last.elapsed.toFixed(1)+' s':(last.elapsed/60).toFixed(1)+' min';$('stamp').textContent=last.timestamp;$('speed').textContent=last.speed!==null&&Number.isFinite(last.speed)?last.speed.toFixed(3)+' s':'—';$('distance').textContent=last.change<.001?'Below the 0.001 tolerance':(last.change/.001).toFixed(2)+'× the 0.001 tolerance';}
  chart('errorChart',rows.map(r=>({...r,value:r.change})),true,320);
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
    $('activity').textContent=last?'Last logged sample '+(Number.isFinite(age)?Math.floor(age)+' seconds ago. ':'')+'CSV polling continues; this does not establish whether the solver is still running.':'Waiting for iteration 0. The solver may still be starting.';
  }catch(error){$('status').textContent='Refresh failed';$('status').classList.add('error');$('checked').textContent=error.message+' · retrying';}
  finally{busy=false;}
}
window.addEventListener('resize',render);
$('axis').addEventListener('change',render);$('refresh').addEventListener('click',refresh);
fetch('/info',{cache:'no-store'}).then(r=>r.json()).then(info=>{$('source').textContent=info.csv;$('source').title=info.csv;}).catch(()=>{$('source').textContent='Local convergence.csv';});
render();refresh();setInterval(refresh,2000);
