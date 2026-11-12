from pathlib import Path
import json,hashlib
import numpy as np
O=Path(__file__).resolve().parent;ROOT=O.parent.parent
rows=json.loads((O/'metrics.json').read_text())+json.loads((O/'supplemental_metrics.json').read_text())
pred=np.load(O/'reconstructions.npz');checked=0;maxerr=0.
for r in rows:
 if r['region'] not in ['all','mu_gt_0.7'] or not r['n']:continue
 if r['case'].startswith('observation_'):
  f=np.load(O/(r['case']+'.npz'));x=f['reference'];y=pred[r['model']];m=f['mask']
 else:
  name='synthetic_evolution' if 'evolution' in r['case'] else r['case']
  f=np.load(O/(name+'.npz'));x=f['truth'];y=f[r['model']];m=f['mask']
 m=m&np.isfinite(x)&np.isfinite(y)
 assert int(m.sum())==r['n']
 e=y[m]-x[m]
 for k,v in [('rmse',np.sqrt(np.mean(e*e))),('mae',np.mean(abs(e))),('bias',np.mean(e))]:
  delta=abs(v-r[k]);maxerr=max(maxerr,float(delta));assert delta<1e-10
 checked+=1
pro=json.loads((O/'provenance.json').read_text())
for name,h in pro['sha256'].items():
 f=ROOT/name;digest=hashlib.sha256()
 with f.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1<<20),b''):digest.update(chunk)
 assert digest.hexdigest()==h,name
results={'primary_metric_rows_recomputed_from_saved_arrays':checked,'max_absolute_metric_difference':maxerr,'all_consumed_input_hashes_rechecked':len(pro['sha256']),'originals_unchanged':True}
(O/'verification.json').write_text(json.dumps(results,indent=2));print(results)
