"""Run calculations, tests, preservation verification and report generation."""
import json
from pathlib import Path
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent


def main():
    (OUT/'logs').mkdir(exist_ok=True)
    commands=[('calculations',[str(OUT/'run_audit.py')]),
              ('discrepancies',[str(OUT/'investigate_discrepancies.py')]),
              ('raw_checksums',[str(OUT/'check_fits.py')]),
              ('existing_tests',['-m','unittest','discover','-s',str(ROOT/'SFT'),'-p','test_coordinate_registration.py','-v']),
              ('tests',['-m','unittest','discover','-s',str(OUT),'-p','test_audit.py','-v']),
              ('preservation',[str(OUT/'inventory.py'),'--verify'])]
    finishing='--finish' in sys.argv
    if finishing:
        commands=[c for c in commands if c[0] in ('discrepancies','tests','preservation')]
    records=json.loads((OUT/'execution.json').read_text()) if finishing else []
    for name,args in commands:
        print(f'Running {name}...',flush=True)
        start=time.monotonic()
        with (OUT/'logs'/f'{name}.log').open('w',encoding='utf-8') as log:
            p=subprocess.Popen([sys.executable,'-B',*args],cwd=ROOT,stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in p.stdout:
                log.write(line); log.flush()
                if not line.startswith(('WARNING:',' [astropy','<unknown>')):
                    print(line,end='',flush=True)
            code=p.wait()
        records.append({'stage':name,'command':[sys.executable,'-B',*args],
                        'returncode':code,'elapsed_seconds':time.monotonic()-start})
        (OUT/'execution.json').write_text(json.dumps(records,indent=2)+'\n')
        if code:
            raise SystemExit(code)
    subprocess.run([sys.executable,'-B',str(OUT/'make_reports.py')],cwd=ROOT,check=True)
    print('Calculations, tests, preservation checks and reports completed.',flush=True)


if __name__=='__main__':
    main()
