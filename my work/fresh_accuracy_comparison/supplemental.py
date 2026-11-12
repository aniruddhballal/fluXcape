"""Fresh stress tests and numerical adapter checks, without observational rerun."""
from pathlib import Path
p=Path(__file__).with_name('run_comparison.py');exec(compile(p.read_text().split("for kind in ['constant'")[0],str(p),'exec'))
checks={}
checks['user_import_vs_adapter_max_error']=float(np.nanmax(abs(user.B_new-mine(arrays))))
# Verify exact scalar expressions from Ananya's original against batch evaluation.
r=ananya([fill(a) for a in arrays]);tt=np.arcsin(np.linspace(-1,1,360));pp=np.linspace(0,2*np.pi,720)
spl=[RectBivariateSpline(tt,pp,fill(a)) for a in arrays]
errs=[]
for i,j in [(0,0),(359,719),(180,360),(60,50),(300,680),(120,3),(100,716)]:
 pn=pp[j]+ns['omega'](tt[i])/(13.2*np.pi/180/86400)*(pp[j]-np.pi)
 k=0 if pn<0 else 2 if pn>2*np.pi else 1
 q=pn+2*np.pi if k==0 else pn-2*np.pi if k==2 else pn
 errs.append(abs(r[i,j]-spl[k](tt[i],q).item()))
checks['ananya_scalar_vs_batch_max_error']=float(max(errs))
# Radial-vector basis roundtrip including camera rotation and perspective.
tx,ty=.003,-.002;rot=np.array([[-1.,0],[0,-1.]])
n=np.array([.4,-.3,np.sqrt(.75)])
basis=np.array([[np.cos(tx),0,np.sin(tx)],[-np.sin(ty)*np.sin(tx),np.cos(ty),np.sin(ty)*np.cos(tx)],[-np.cos(ty)*np.sin(tx),-np.sin(ty),np.cos(ty)*np.cos(tx)]])
v=basis@n;v[:2]=rot.T@v[:2]
checks['vector_radial_roundtrip_error_G']=float(abs(100*np.dot(v,v)-100))
checks['constant_preservation_user_max_error']=float(np.nanmax(abs(mine([np.full_like(L,7.)]*3)-7)))
rng=np.random.default_rng(219019192)
for seed in range(3):
 truth=field(L,A,'bipoles');maps=[]
 for shift in [360,0,-360]:
  s=L+shift;t=(180-s)/13.2
  maps.append(field(s-rate*t,A,'bipoles')+rng.normal(0,3,L.shape))
 pred=models(maps);mask=metrics(f'synthetic_noise3G_seed{seed}',truth,pred,np.ones_like(L,bool))
 np.savez_compressed(OUT/f'synthetic_noise3G_seed{seed}.npz',truth=truth,mask=mask,**pred)
# Explicit emergence/decay: time-changing amplitude, truth at reference is unchanged.
truth=field(L,A,'bipoles');maps=[]
for shift in [360,0,-360]:
 s=L+shift;t=(180-s)/13.2
 maps.append(field(s-rate*t,A,'bipoles')*np.exp(.025*t))
pred=models(maps);mask=metrics('synthetic_evolution_2.5pct_per_day',truth,pred,np.ones_like(L,bool))
np.savez_compressed(OUT/'synthetic_evolution.npz',truth=truth,mask=mask,**pred)
(OUT/'supplemental_metrics.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
(OUT/'adapter_checks.json').write_text(json.dumps(checks,indent=2))
print(checks)
assert max(checks.values())<1e-9
