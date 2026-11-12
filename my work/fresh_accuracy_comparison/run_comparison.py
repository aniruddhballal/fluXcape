"""Independent, reproducible pre-SFT comparison; no SFT integration is imported."""
from pathlib import Path
import ast, hashlib, json, csv, shutil, warnings, importlib.util, sys, os
import numpy as np
from scipy.interpolate import RectBivariateSpline, CubicSpline
from scipy.ndimage import distance_transform_edt, map_coordinates
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u
import sunpy.map
from sunpy.coordinates import frames
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore', category=Warning)
OUT=Path(__file__).resolve().parent; ROOT=OUT.parent.parent
DATA=OUT.parent/'fits_files'; OBS=DATA/'observations/cr2191'
SOURCES=[ROOT/"ananya's research work/SFT/SFT.py",OUT.parent/'pre-sft/main.py']
Q=int(os.environ.get('QUADRATURE','8'))
if Q!=8: OUT=OUT/f'quadrature{Q}';OUT.mkdir(exist_ok=True)
(OUT/'originals').mkdir(exist_ok=True)
for p in SOURCES: shutil.copy2(p,OUT/'originals'/('ananya_SFT.py' if p.name=='SFT.py' else 'user_main.py'))
provenance={}; rows=[]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
for p in SOURCES: provenance[str(p.relative_to(ROOT))]=digest(p)
# Import only the user's pre-SFT module. Extract Ananya's omega AST, never execute SFT.py.
spec=importlib.util.spec_from_file_location('user_pre',SOURCES[1]); user=importlib.util.module_from_spec(spec);spec.loader.exec_module(user)
tree=ast.parse(SOURCES[0].read_text()); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='omega')
ns={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),'extracted_omega','exec'),ns)
lon=user.LONGITUDES; lat=user.LATITUDES; th=user.COLATITUDES; order=np.argsort(lon); slon=lon[order]
L,A=np.meshgrid(lon,lat); rate=.18-2.3*np.sin(np.deg2rad(A))**2-1.62*np.sin(np.deg2rad(A))**4
arrays=[np.array(user.B_prev,float),np.array(user.B_curr,float),np.array(user.B_next,float)]
for cr in [2190,2191,2192]:
 p=DATA/f'720x360/hmi.Synoptic_Mr_small.{cr}.fits';provenance[str(p.relative_to(ROOT))]=digest(p)
def fill(a):
 bad=~np.isfinite(a)
 return a[tuple(distance_transform_edt(bad,return_distances=False,return_indices=True))] if bad.any() else a

def ananya(maps, patched=False, physical=False):
 # Exact original grid, formula, neighboring-map order and tensor cubic interpolant.
 t=np.arcsin(np.linspace(-1,1,len(lat))); p=np.linspace(0,2*np.pi,len(lon))
 if physical: t=np.deg2rad(lat);p=np.deg2rad(slon);maps=[m[:,order] for m in maps]
 spl=[RectBivariateSpline(t,p,fill(m) if patched else m) for m in maps]
 tt,pp=np.meshgrid(t,p,indexing='ij'); om=ns['omega'](tt if not physical else np.pi/2-tt)
 src=pp+om/(13.2*np.pi/180/86400)*(pp-np.pi)
 result=np.empty_like(src)
 for idx,mask in [(0,src<0),(2,src>2*np.pi),(1,(src>=0)&(src<=2*np.pi))]:
  q=src[mask]+(2*np.pi if idx==0 else -2*np.pi if idx==2 else 0)
  result[mask]=spl[idx].ev(tt[mask],q)
 if physical: result=result[:,np.argsort(order)]
 return result

def mine(maps):
 old=user.B_prev,user.B_curr,user.B_next,user.SOURCE_SPLINES
 user.B_prev,user.B_curr,user.B_next=maps;user.SOURCE_SPLINES=user.build_source_splines()
 r=user.reconstruct_b_new();user.B_prev,user.B_curr,user.B_next,user.SOURCE_SPLINES=old
 return r

def models(maps, real=False):
 d={'baseline':maps[1], 'user':mine(maps),'ananya_native':ananya(maps)}
 if real:
  d['ananya_nan_filled']=ananya(maps,True)
  d['ananya_coordinate_adapted']=ananya(maps,True,True)
 return d

def metrics(case,truth,preds,mask,region='all'):
 common=mask & np.isfinite(truth)
 # Primary common mask uses operational NaN-filled Ananya when original is unusable.
 chosen=['baseline','user','ananya_nan_filled','ananya_coordinate_adapted'] if 'ananya_nan_filled' in preds else list(preds)
 for n in chosen:common &=np.isfinite(preds[n])
 for n,p in preds.items():
  valid=common & np.isfinite(p);npx=int(valid.sum())
  r={'case':case,'region':region,'model':n,'n':npx,'truth_valid':int((mask&np.isfinite(truth)).sum())}
  if npx:
   x=truth[valid];y=p[valid];e=y-x;rmse=np.sqrt(np.mean(e*e))
   r.update(rmse=float(rmse),mae=float(np.mean(abs(e))),bias=float(e.mean()),correlation=float(np.corrcoef(x,y)[0,1]) if min(np.std(x),np.std(y))>1e-10 else None,nrmse_std=float(rmse/np.std(x)) if np.std(x)>0 else None,p95_abs_error=float(np.percentile(abs(e),95)),sign_agreement=float(np.mean(np.sign(x)==np.sign(y))),truth_rms=float(np.sqrt(np.mean(x*x))),prediction_mean=float(y.mean()),truth_mean=float(x.mean()),unsigned_ratio=float(np.mean(abs(y))/np.mean(abs(x))) if np.mean(abs(x)) else None)
  rows.append(r)
 return common

def plot_maps(name,truth,preds,mask):
 names=list(preds); fig,axes=plt.subplots(2,len(names)+1,figsize=(4*(len(names)+1),6),squeeze=False)
 scale=max(5,np.nanpercentile(abs(truth[mask]),98));
 for j,(n,p) in enumerate([('reference',truth)]+list(preds.items())):
  axes[0,j].imshow(np.where(mask,p,np.nan),origin='lower',aspect='auto',cmap='RdBu_r',vmin=-scale,vmax=scale);axes[0,j].set_title(n)
  axes[1,j].imshow(np.where(mask,p-truth,np.nan),origin='lower',aspect='auto',cmap='RdBu_r',vmin=-scale,vmax=scale);axes[1,j].set_title('error [G]')
 for ax in axes.flat:ax.set_xlabel('native longitude column');ax.set_ylabel('sin(latitude) row')
 fig.suptitle(name+'; common scale ±'+f'{scale:.1f} G');fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=130);plt.close(fig)
# Analytic ground truth is advected independently in continuous time. Source observation
# time at unwrapped Carrington longitude s is (180-s)/13.2 days.
def field(p,a,kind):
 x=np.deg2rad(p);y=np.deg2rad(a)
 if kind=='smooth':return 15*np.sin(y)+30*np.cos(y)**2*np.cos(3*x)+12*np.sin(2*x+2*y)
 if kind=='fine':return 30*np.cos(y)*np.sin(24*x+3*y)+10*np.cos(47*x-y)
 if kind=='constant':return np.full_like(p,7.)
 d=lambda c:(p-c+180)%360-180
 return 200*np.exp(-(d(70)**2/100+(a-25)**2/36))-180*np.exp(-(d(80)**2/100+(a-25)**2/36))+100*np.exp(-(d(359)**2/49+(a+50)**2/64))+10*np.sin(y)
for kind in ['constant','smooth','fine','bipoles']:
 truth=field(L,A,kind)
 for factor in [0,1,.7]:
  maps=[]
  for shift in [360,0,-360]:
   s=L+shift;time=(180-s)/13.2
   maps.append(field(s-rate*factor*time,A,kind))
  pred=models(maps);case=f'synthetic_{kind}_rotation{factor:g}'
  mask=metrics(case,truth,pred,np.ones_like(truth,bool))
  for reg,m in [('low_lat',abs(A)<30),('mid_lat',(abs(A)>=30)&(abs(A)<60)),('polar',abs(A)>=60),('seam',(L<20)|(L>340))]:metrics(case,truth,pred,m,reg)
  np.savez_compressed(OUT/(case+'.npz'),truth=truth,mask=mask,**pred)
  if factor==1 and kind!='constant':plot_maps(case,truth,pred,mask)
print('Synthetic calculations complete',flush=True)
real=models(arrays,True)
np.savez_compressed(OUT/'reconstructions.npz',longitude=lon,latitude=lat,**real)
for n,a in real.items(): print(n,'finite',np.isfinite(a).sum(),flush=True)
def read_segment(folder,stamp,seg):
 p=OBS/folder/f'{folder}.{stamp}.{seg}.fits';provenance[str(p.relative_to(ROOT))]=digest(p)
 with fits.open(p,memmap=False) as h:return np.asarray(h[1].data,dtype=float)

def sample(arr,x,y):return map_coordinates(arr,[y,x],order=1,mode='constant',cval=np.nan,prefilter=False)
obsmeta=[]
for rec in sorted((OBS/'hmi.M_720s').glob('*.record.json')):
 stamp=rec.name.split('.')[0]; print('Observations',stamp,flush=True)
 km=json.loads(rec.read_text())['keywords'];kb=json.loads((OBS/'hmi.B_720s'/rec.name).read_text())['keywords']
 for p in [rec,OBS/'hmi.B_720s'/rec.name]:provenance[str(p.relative_to(ROOT))]=digest(p)
 def make_map(k):
  meta={}
  for key,val in k.items():
   try:meta[key]=float(val)
   except (ValueError,TypeError):meta[key]=val
  # FITS standard time representation with explicit TAI scale (SunPy parses date-obs).
  meta['DATE-OBS']=str(k['T_OBS']).replace('.','-',2).replace('_','T',1).replace('_TAI','');meta['TIMESYS']='TAI'
  return sunpy.map.Map(np.zeros((4096,4096),dtype=np.uint8),meta)
 mm=make_map(km);bm=make_map(kb)
 los=read_segment('hmi.M_720s',stamp,'magnetogram')
 bf=read_segment('hmi.B_720s',stamp,'field');inc=np.deg2rad(read_segment('hmi.B_720s',stamp,'inclination'));azi=np.deg2rad(read_segment('hmi.B_720s',stamp,'azimuth'));dis=read_segment('hmi.B_720s',stamp,'disambig')
 # Full disk bit 2 selects the radial acute-angle weak-field solution.
 # High-confidence strong-field pixels use minimum energy; report them separately.
 azi=azi+np.pi*((dis.astype(np.uint16)>>2)&1)
 bx=-bf*np.sin(inc)*np.sin(azi);by=bf*np.sin(inc)*np.cos(azi);bz=bf*np.cos(inc)
 del bf,inc,azi,dis
 conf=read_segment('hmi.B_720s',stamp,'conf_disambig');conv=read_segment('hmi.B_720s',stamp,'conv_flag')
 sums={n:np.zeros_like(L) for n in ['los_radial_proxy','vector_radial','mu','confidence','converged','high_confidence_fraction']};counts=np.zeros_like(L)
 # Equal-area 8x8 quadrature within each target CEA pixel.
 for dy in (np.arange(Q)+.5)/Q-.5:
  for dx in (np.arange(Q)+.5)/Q-.5:
   ll=L+dx*.5;aa=np.rad2deg(np.arcsin(np.clip(np.sin(np.deg2rad(A))+dy*float(user.CURRENT_HEADER['CDELT2']),-1,1)))
   sky=SkyCoord(ll*u.deg,aa*u.deg,frame=frames.HeliographicCarrington,observer=mm.observer_coordinate,obstime=mm.date)
   hp=sky.transform_to(mm.coordinate_frame);xx,yy=mm.world_to_pixel(hp);x=xx.value;y=yy.value
   hc=sky.transform_to(frames.Heliocentric(observer=bm.observer_coordinate,obstime=bm.date));nx=hc.cartesian.x.to_value(u.m)/bm.rsun_meters.to_value(u.m);ny=hc.cartesian.y.to_value(u.m)/bm.rsun_meters.to_value(u.m);nz=hc.cartesian.z.to_value(u.m)/bm.rsun_meters.to_value(u.m)
   # Local normal dot the actual observer ray (finite observer distance).
   ds=float(km['DSUN_OBS'])/float(km['RSUN_REF']);mu=(ds*nz-1)/np.sqrt(ds*ds+1-2*ds*nz)
   xb,yb=bm.world_to_pixel(sky.transform_to(bm.coordinate_frame));xb=xb.value;yb=yb.value
   rot=np.asarray(bm.rotation_matrix)
   hpb=sky.transform_to(bm.coordinate_frame);tx=hpb.Tx.to_value(u.rad);ty=hpb.Ty.to_value(u.rad)
   # Project the normal into the local observer-ray tangent basis before CCD rotation.
   nwest=nx*np.cos(tx)+nz*np.sin(tx)
   nnorth=-nx*np.sin(ty)*np.sin(tx)+ny*np.cos(ty)+nz*np.sin(ty)*np.cos(tx)
   nlos=-nx*np.cos(ty)*np.sin(tx)-ny*np.sin(ty)+nz*np.cos(ty)*np.cos(tx)
   nxi=rot[0,0]*nwest+rot[1,0]*nnorth;nyi=rot[0,1]*nwest+rot[1,1]*nnorth
   vr=sample(bx,xb,yb)*nxi+sample(by,xb,yb)*nyi+sample(bz,xb,yb)*nlos
   lr=sample(los,x,y)/mu
   cf=map_coordinates(conf,[yb,xb],order=0,mode='constant',cval=0,prefilter=False)
   cv=map_coordinates(conv,[yb,xb],order=0,mode='constant',cval=-1,prefilter=False)
   good=(mu>.3)&np.isfinite(lr)&np.isfinite(vr)
   counts+=good
   for n,v in [('los_radial_proxy',lr),('vector_radial',vr),('mu',mu),('confidence',cf),('converged',(cv==0).astype(float)),('high_confidence_fraction',(cf>=90).astype(float))]:sums[n]+=np.where(good,v,0)
 del los,bx,by,bz,conf,conv
 avg={n:np.divide(v,counts,out=np.full_like(v,np.nan),where=counts==Q*Q) for n,v in sums.items()}
 base=(counts==Q*Q)&(avg['mu']>.7)
 for target in ['los_radial_proxy','vector_radial']:
  for region,mask in [('mu_gt_0.7',base),('mu_gt_0.9',base&(avg['mu']>.9)),('strong_reference',base&(abs(avg[target])>50)),('high_confidence',base&(avg['high_confidence_fraction']>=.5)&(avg['converged']==1)),('strict_high_confidence',base&(avg['confidence']>=90)&(avg['converged']==1))]:
   common=metrics(f'observation_{stamp}_{target}',avg[target],real,mask,region)
   if region=='mu_gt_0.7':
    np.savez_compressed(OUT/f'observation_{stamp}_{target}.npz',reference=avg[target],mask=common,**avg)
    if '110000' in stamp:plot_maps(f'observation_{stamp}_{target}',avg[target],{n:real[n] for n in ['baseline','user','ananya_nan_filled','ananya_coordinate_adapted']},common)
 obsmeta.append({'stamp':stamp,'M_T_OBS':km['T_OBS'],'B_T_OBS':kb['T_OBS'],'quality_M':km['QUALITY'],'quality_B':kb['QUALITY'],'observer_lon':km['CRLN_OBS'],'coverage_mu_gt_07':int(base.sum()),'rotation_matrix':rot.tolist()})
 print('Completed',stamp,flush=True)
# Save portable numerical results.
(OUT/'metrics.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
keys=list(dict.fromkeys(k for r in rows for k in r))
with (OUT/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
(OUT/'provenance.json').write_text(json.dumps({'sha256':provenance,'observations':obsmeta,'versions':{n:__import__(n).__version__ for n in ['numpy','scipy','astropy','sunpy','matplotlib']},'python':sys.version},indent=2))
assert all(digest(p)==provenance[str(p.relative_to(ROOT))] for p in SOURCES)
print('DONE',len(rows),'metric rows',flush=True)
