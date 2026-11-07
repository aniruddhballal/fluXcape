import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Activity, ArrowRightLeft, CircleHelp, Compass, Expand, Globe2, Layers2, Move3D, RotateCcw, ScanLine, Sun, ZoomIn } from 'lucide-react';
import './style.css';

type Data = { rotation:number; rotations:number[]; width:number; height:number; original:string; reconstructed:string; coordinates:Record<string,number>; metrics:{bias:number;mae:number;rmse:number;valid:number;total:number} };
type Prepared = Omit<Data,'original'|'reconstructed'> & {original:Float32Array; reconstructed:Float32Array};
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
 const [data,setData]=useState<Prepared|null>(null),[error,setError]=useState(''),[mode,setMode]=useState<'2d'|'3d'>('2d'),[reconstructed,setReconstructed]=useState(false),[limit,setLimit]=useState(100),[hover,setHover]=useState<string>('Move over the map to inspect a pixel');
 useEffect(()=>{fetch('/maps.json').then(r=>{if(!r.ok)throw Error('Run the data preparation command first.');return r.json()}).then((d:Data)=>setData({...d,original:decode(d.original),reconstructed:decode(d.reconstructed)})).catch(e=>setError(String(e)))},[]);
 const canvas=useRef<HTMLCanvasElement>(null);const active=data?(reconstructed?data.reconstructed:data.original):null;
 const flat=useMemo(()=>data&&active?makeTexture(active,data,limit,false):null,[data,active,limit]);
 const spherical=useMemo(()=>data&&active&&mode==='3d'?makeTexture(active,data,limit,true):null,[data,active,limit,mode]);
 useEffect(()=>{if(flat&&canvas.current){canvas.current.width=flat.width;canvas.current.height=flat.height;canvas.current.getContext('2d')!.drawImage(flat,0,0)}},[flat,mode]);
 function inspect(e:React.MouseEvent<HTMLCanvasElement>){if(!data||!active)return;const rect=e.currentTarget.getBoundingClientRect(),x=Math.max(0,Math.min(data.width-1,Math.floor((e.clientX-rect.left)/rect.width*data.width))),y=Math.max(0,Math.min(data.height-1,data.height-1-Math.floor((e.clientY-rect.top)/rect.height*data.height)));const h=data.coordinates;const phi=((h.CRVAL1+(x+1-h.CRPIX1)*h.CDELT1)%360+360)%360;const sine=h.CRVAL2+(y+1-h.CRPIX2)*h.CDELT2;const theta=Math.acos(Math.max(-1,Math.min(1,sine)))*180/Math.PI;const v=active[y*data.width+x];setHover(`φ ${phi.toFixed(1)}°  ·  θ ${theta.toFixed(1)}°  ·  ${Number.isFinite(v)?v.toFixed(2)+' G':'No data'}`)}
 return <div className="app"><header className="top"><div className="brand"><span className="brand-icon"><Sun size={20}/></span><span>flu<span className="brand-x">X</span>cape</span><span className="brand-divider"/><span className="brand-product">SYNOPTIC STUDIO</span></div><div className="top-right"><span className="dot"/> LOCAL WORKSPACE <span className="top-divider"/><span>SDO / HMI</span></div></header>
 <main><div className="breadcrumb"><span>WORKSPACE</span><span>/</span><span className="crumb-active">SYNOPTIC RECONSTRUCTION</span></div>
 <section className="heading"><div><div className="eyebrow"><span className="mini-line"/> SOLAR SURFACE MAGNETIC FIELD</div><h1>Synoptic <em>reconstruction</em></h1><p>Explore how differential rotation reshapes a Carrington map.</p></div><div className="heading-meta"><span className="meta-label">CURRENT ROTATION</span><strong>CR {data?.rotation ?? '—'}</strong><span>SDO / HMI · Radial field</span></div></section>
 {error?<div className="error">Unable to load reconstruction data. {error}<br/>Run <code>.\.venv\Scripts\python.exe SFT\prepare_viewer_data.py</code> from the repo root.</div>:!data?<div className="loading">Preparing your solar maps…</div>:<div className="workspace"><section className="viewer-card"><div className="card-header"><div><div className="section-kicker"><span className="dot"/> MAGNETOGRAM VIEWER</div><h2>Solar surface <span> / CR {data.rotation}</span></h2></div><div className="view-switch" role="group" aria-label="View mode"><button className={mode==='2d'?'selected':''} onClick={()=>setMode('2d')}><Layers2 size={15}/> 2D map</button><button className={mode==='3d'?'selected':''} onClick={()=>setMode('3d')}><Globe2 size={15}/> 3D globe</button></div></div>
 <div className="stage"><div className="stage-top"><span className="stage-tag"><span className={reconstructed?'status reconstructed':'status'}/>{reconstructed?'RECONSTRUCTED':'ORIGINAL MAP'}</span><span className="stage-res">{data.width} × {data.height} PX</span></div>{mode==='2d'?<div className="map-wrap"><div className="map-y"><span>0°</span><span>90°</span><span>180°</span></div><div className="map-inner"><canvas ref={canvas} className="map-canvas" onMouseMove={inspect} onMouseLeave={()=>setHover('Move over the map to inspect a pixel')}/><div className="map-x"><span>360°</span><span>270°</span><span>180°</span><span>90°</span><span>0°</span></div><div className="axis-name">CARRINGTON LONGITUDE φ</div></div></div>:spherical&&<><Globe texture={spherical}/><div className="globe-hint"><Move3D size={14}/> DRAG TO ROTATE <span>·</span> SCROLL TO ZOOM</div></>}
 <div className="stage-bottom"><span>{mode==='2d'?hover:'Spherical display · north pole up'}</span><span>{mode==='2d'?'COLATITUDE θ':'3D EXPLORER'}</span></div></div>
 <div className="legend"><div className="legend-top"><span>RADIAL MAGNETIC FIELD <b>B<sub>r</sub></b></span><span>GAUSS</span></div><div className="gradient"/><div className="legend-labels"><span>−{limit} G</span><span>INWARD</span><span>0</span><span>OUTWARD</span><span>+{limit} G</span></div></div>
 <div className="action-bar"><div><span className="action-title">{reconstructed?'Reconstruction applied':'Ready to reconstruct'}</span><span className="action-sub">{reconstructed?'Compare with the original map at any time.':'Apply the calculated longitude shifts to the map.'}</span></div><button className="primary" onClick={()=>setReconstructed(!reconstructed)}>{reconstructed?<><RotateCcw size={16}/> Show original</>:<><ArrowRightLeft size={16}/> Apply reconstruction</>}</button></div></section>
 <aside><div className="side-card"><div className="side-header"><div><div className="section-kicker">ANALYSIS</div><h2>Map comparison</h2></div><Activity size={18}/></div><p className="side-desc">Reconstructed map compared with the original synoptic map.</p><div className="metric"><div><span>Mean difference</span><small>Signed bias</small></div><strong>{data.metrics.bias.toFixed(3)} <i>G</i></strong></div><div className="metric"><div><span>Mean absolute difference</span><small>MAE</small></div><strong>{data.metrics.mae.toFixed(3)} <i>G</i></strong></div><div className="metric"><div><span>Root mean square</span><small>RMSE</small></div><strong>{data.metrics.rmse.toFixed(3)} <i>G</i></strong></div><div className="coverage"><span>VALID PIXELS</span><strong>{data.metrics.valid.toLocaleString()} <i>/ {data.metrics.total.toLocaleString()}</i></strong><div className="coverage-line"><span style={{width:`${100*data.metrics.valid/data.metrics.total}%`}}/></div></div><div className="note"><CircleHelp size={15}/><span>These values measure change from the original map, not error against ground truth.</span></div></div>
 <div className="side-card settings"><div className="section-kicker">DISPLAY SETTINGS</div><div className="setting-title"><span>Field saturation</span><strong>±{limit} G</strong></div><input aria-label="Field saturation in gauss" type="range" min="20" max="500" step="10" value={limit} onChange={e=>setLimit(Number(e.target.value))}/><div className="range-labels"><span>20 G</span><span>500 G</span></div><p>Adjust contrast without changing the map data.</p></div>
 <div className="source-note"><ScanLine size={15}/> <span>INPUT MAPS <b>CR {data.rotations.join(' · CR ')}</b></span></div></aside></div>}
 <footer><span>fluXcape <span className="footer-dot">·</span> SYNOPTIC STUDIO</span><span>BUILT FOR SOLAR EXPLORATION <Compass size={13}/></span></footer></main></div>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
