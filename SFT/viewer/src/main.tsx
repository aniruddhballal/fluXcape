import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Globe2, Layers2, Sun } from 'lucide-react';
import './style.css';

type Metrics = {bias:number;mae:number;rmse:number;valid:number;total:number};
type ObservationScore = {count:number;bias_gauss:number;mae_gauss:number;rmse_gauss:number;pearson_r:number};
type ObservationValidation = {scores:Record<'original'|'ananya'|'fixed',ObservationScore>;observation:{T_OBS_utc:string};method:{mu_min:number}};
type Data = { rotation:number; rotations:number[]; width:number; height:number; original:string; reconstructions:Record<'ananya'|'fixed',{data:string;metrics:Metrics}>; coordinates:Record<string,number>; observational_validation:ObservationValidation|null };
type Prepared = Omit<Data,'original'|'reconstructions'> & {original:Float32Array; reconstructions:Record<'ananya'|'fixed',{data:Float32Array;metrics:Metrics}>};
type Version = 'original'|'ananya'|'fixed';
function decode(s:string) { const raw=atob(s), bytes=new Uint8Array(raw.length); for(let i=0;i<raw.length;i++) bytes[i]=raw.charCodeAt(i); return new Float32Array(bytes.buffer); }
function color(value:number, limit:number): [number,number,number] {
 if(!Number.isFinite(value)) return [36,39,51];
 const n=Math.max(0,Math.min(1,(value+limit)/(2*limit))); let t:number;
 if(n<.4){t=n/.4;return [100+t*155,t*200,0]}
 if(n<.48){t=(n-.4)/.08;return [255-t*55,200-t*50,t*150]}
 if(n<.52)return [150,150,150];
 if(n<.6){t=(n-.52)/.08;return [150-t*150,150+t*105,150-t*50]}
 t=(n-.6)/.4;return [0,255-t*255,100+t*155];
}
function makeTexture(data:Float32Array, d:Prepared, limit:number, spherical:boolean) {
 const canvas=document.createElement('canvas'); canvas.width=d.width;canvas.height=d.height;
 const context=canvas.getContext('2d')!;const im=context.createImageData(d.width,d.height);
 for(let y=0;y<d.height;y++) {
  // FITS rows are uniform in sine latitude. Sphere UV rows are uniform in latitude.
  const row=spherical ? Math.round((Math.cos(Math.PI*(y+.5)/d.height)-d.coordinates.CRVAL2)/d.coordinates.CDELT2+d.coordinates.CRPIX2-1) : d.height-1-y;
  for(let x=0;x<d.width;x++) {const i=(y*d.width+x)*4; const v=row>=0&&row<d.height?data[row*d.width+x]:NaN; const [r,g,b]=color(v,limit);im.data[i]=r;im.data[i+1]=g;im.data[i+2]=b;im.data[i+3]=255;}
 }
 context.putImageData(im,0,0);return canvas;
}
function Globe({texture}:{texture:HTMLCanvasElement}) {
 const mount=useRef<HTMLDivElement>(null);const material=useRef<THREE.MeshBasicMaterial|null>(null);
 useEffect(()=>{if(!mount.current)return;const element=mount.current;
  const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(38,1,.1,100);camera.position.set(0,0,3.7);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;element.appendChild(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=2.2;controls.maxDistance=7;
  const geo=new THREE.SphereGeometry(1,160,96); const mat=new THREE.MeshBasicMaterial();material.current=mat;const sphere=new THREE.Mesh(geo,mat);scene.add(sphere);
  const halo=new THREE.Mesh(new THREE.SphereGeometry(1.025,100,64),new THREE.MeshBasicMaterial({color:0x6b91ff,transparent:true,opacity:.06,side:THREE.BackSide}));scene.add(halo);
  const resize=()=>{const w=element.clientWidth,h=element.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()};const observer=new ResizeObserver(resize);observer.observe(element);resize();let id=0;
  const loop=()=>{controls.update();renderer.render(scene,camera);id=requestAnimationFrame(loop)};loop();
  return()=>{cancelAnimationFrame(id);observer.disconnect();controls.dispose();geo.dispose();mat.map?.dispose();mat.dispose();halo.geometry.dispose();(halo.material as THREE.Material).dispose();renderer.dispose();renderer.domElement.remove();material.current=null};
 },[]);
 useEffect(()=>{if(!material.current)return;const tex=new THREE.CanvasTexture(texture);tex.colorSpace=THREE.SRGBColorSpace;tex.wrapS=THREE.RepeatWrapping;material.current.map?.dispose();material.current.map=tex;material.current.needsUpdate=true},[texture]);
 return <div className="globe" ref={mount} aria-label="Interactive 3D solar surface. Drag to rotate, scroll to zoom."/>;
}
function App(){
 const [data,setData]=useState<Prepared|null>(null),[error,setError]=useState(''),[mode,setMode]=useState<'2d'|'3d'>('2d'),[version,setVersion]=useState<Version>('original'),[limit,setLimit]=useState(100),[hover,setHover]=useState<string>('Move over the map to inspect a pixel');
 useEffect(()=>{fetch('/maps.json').then(r=>{if(!r.ok)throw Error('Run the data preparation command first.');return r.json()}).then((d:Data)=>setData({...d,original:decode(d.original),reconstructions:{ananya:{...d.reconstructions.ananya,data:decode(d.reconstructions.ananya.data)},fixed:{...d.reconstructions.fixed,data:decode(d.reconstructions.fixed.data)}}})).catch(e=>setError(String(e)))},[]);
 const canvas=useRef<HTMLCanvasElement>(null);const active=data?(version==='original'?data.original:data.reconstructions[version].data):null;
 const validation=data?.observational_validation;
 const metrics=validation?validation.scores[version]:null;
 const flat=useMemo(()=>data&&active?makeTexture(active,data,limit,false):null,[data,active,limit]);
 const spherical=useMemo(()=>data&&active&&mode==='3d'?makeTexture(active,data,limit,true):null,[data,active,limit,mode]);
 useEffect(()=>{if(flat&&canvas.current){canvas.current.width=flat.width;canvas.current.height=flat.height;canvas.current.getContext('2d')!.drawImage(flat,0,0)}},[flat,mode]);
 function inspect(e:React.MouseEvent<HTMLCanvasElement>){if(!data||!active)return;const rect=e.currentTarget.getBoundingClientRect(),x=Math.max(0,Math.min(data.width-1,Math.floor((e.clientX-rect.left)/rect.width*data.width))),y=Math.max(0,Math.min(data.height-1,data.height-1-Math.floor((e.clientY-rect.top)/rect.height*data.height)));const h=data.coordinates;const phi=((h.CRVAL1+(x+1-h.CRPIX1)*h.CDELT1)%360+360)%360;const sine=h.CRVAL2+(y+1-h.CRPIX2)*h.CDELT2;const theta=Math.acos(Math.max(-1,Math.min(1,sine)))*180/Math.PI;const v=active[y*data.width+x];setHover(`φ ${phi.toFixed(1)}°  ·  θ ${theta.toFixed(1)}°  ·  ${Number.isFinite(v)?v.toFixed(2)+' G':'No data'}`)}
 return <div className="app">
 <header className="top"><div className="brand"><Sun size={22}/><span>fluXcape</span><span className="brand-product">Synoptic reconstruction viewer</span></div></header>
 <main>
 {error?<div className="error">Unable to load the maps. {error}<br/>Run <code>.\.venv\Scripts\python.exe SFT\prepare_viewer_data.py</code> from the repo root.</div>:!data?<div className="loading">Loading maps...</div>:<div className="workspace">
 <section className="viewer-card">
 <div className="card-header"><h2>{version==='original'?'Original map':version==='ananya'?'Reconstruction: Ananya':'Reconstruction: Fixed'} <span>&middot; CR {data.rotation} &middot; SDO / HMI</span></h2>
 <div className="viewer-controls"><label className="version-label"><span className="sr-only">Map version</span><select value={version} onChange={e=>setVersion(e.target.value as Version)}><option value="original">OG</option><option value="ananya">Recons Ananya</option><option value="fixed">Recons fixed</option></select></label><div className="settings"><label htmlFor="saturation">Color range <strong>&plusmn;{limit} G</strong></label><input id="saturation" type="range" min="20" max="500" step="10" value={limit} onChange={e=>setLimit(Number(e.target.value))}/></div><div className="view-switch" role="group" aria-label="View mode"><button className={mode==='2d'?'selected':''} aria-pressed={mode==='2d'} onClick={()=>setMode('2d')}><Layers2 size={16}/> 2D map</button><button className={mode==='3d'?'selected':''} aria-pressed={mode==='3d'} onClick={()=>setMode('3d')}><Globe2 size={16}/> 3D globe</button></div></div></div>
 <div className="map-layout"><div className="stage"><div className="field-scale" aria-label={`Radial magnetic field from minus ${limit} to plus ${limit} gauss`}><span className="field-scale-title">B<sub>r</sub></span><div className="field-scale-body"><div className="field-scale-gradient"/><div className="field-scale-labels"><span>+{limit}</span><span>0</span><span>&minus;{limit}</span></div></div><span className="field-scale-unit">Gauss</span></div>{mode==='2d'?<div className="map-wrap"><div className="map-inner"><div className="map-row"><div className="map-y"><span>0&deg;</span><span>90&deg;</span><span>180&deg;</span></div><canvas ref={canvas} className="map-canvas" onMouseMove={inspect} onMouseLeave={()=>setHover('Move over the map to inspect a pixel')}/></div><div className="map-x">{[0,.25,.5,.75,1].map(f=>{const h=data.coordinates;const lon=((h.CRVAL1+(f*(data.width-1)+1-h.CRPIX1)*h.CDELT1)%360+360)%360;return <span key={f}>{Math.round(lon)}&deg;</span>})}</div><div className="axis-name">Carrington longitude &phi;</div></div></div>:spherical&&<Globe texture={spherical}/>}
 {mode==='2d'&&<div className="stage-bottom"><span>{hover}</span><span>Colatitude &theta;</span></div>}</div><aside className="map-stats" aria-label="Comparison with HMI observation"><h3>HMI observation comparison</h3>{validation?<p>45-second image, {validation.observation.T_OBS_utc.replace('T', ' ')} UTC. Shared mask, &mu; &ge; {validation.method.mu_min}.</p>:<p>Validation unavailable or out of date. Run the observational validation and prepare the viewer data again.</p>}{metrics?<><div className="stat"><span>Mean difference (bias)</span><strong>{metrics.bias_gauss.toFixed(3)} G</strong></div><div className="stat"><span>Mean absolute error</span><strong>{metrics.mae_gauss.toFixed(3)} G</strong></div><div className="stat"><span>Root mean square error</span><strong>{metrics.rmse_gauss.toFixed(3)} G</strong></div><div className="stat"><span>Correlation (Pearson r)</span><strong>{metrics.pearson_r.toFixed(3)}</strong></div><div className="stat"><span>Compared pixels</span><strong>{metrics.count.toLocaleString()}</strong></div></>:validation&&<p>Select a reconstruction to see its comparison.</p>}</aside></div>
 </section>
 </div>}
 </main></div>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
