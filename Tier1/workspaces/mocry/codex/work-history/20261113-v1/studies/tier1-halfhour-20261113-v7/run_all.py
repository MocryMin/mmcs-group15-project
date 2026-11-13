"""Reproduce the frozen-data main results without a monolithic million-row MIP."""
import json,math,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(script,*args):
    subprocess.run([sys.executable,str(ROOT/script),*args],cwd=ROOT,check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
if not (ROOT/'inputs/halfhour.csv.gz').exists():run('prepare_data.py')
for policy in ('A','B'):
    run('column_generation.py','--policy',policy,'--name','certificate_'+policy,'--maxiter','3')
    cert=json.loads((ROOT/'results'/f'certificate_{policy}.json').read_text())
    assert all(p['reduced_cost_lower']>0 for p in cert['pricing_audit']), 'Changed data require further joint-investment optimisation.'
    assert cert['battery_MWh']<1e-8
    fixed={k:math.ceil(v-1e-8) for k,v in cert['investment'].items()}
    dest=ROOT/'inputs'/f'fixed_{policy}_replay.json';dest.write_text(json.dumps(fixed,indent=2))
    run('model.py','--policy',policy,'--name',f'full_{policy}_candidate','--fixed',str(dest),'--seconds','120')
    run('verify.py',f'full_{policy}_candidate')
run('verify_certificate.py')
run('summarize.py')
print('MAIN RESULTS REPRODUCED AND VERIFIED')
