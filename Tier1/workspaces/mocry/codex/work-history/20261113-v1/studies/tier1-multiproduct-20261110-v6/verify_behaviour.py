"""Force installed storage so new paths are exercised even if optimum buys none."""
import copy
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from model import solve
from verify_results import check

ROOT=Path(__file__).resolve().parent
def frame(g,d,p):return pd.DataFrame(dict(g=g,d=d,price=p),index=pd.date_range('2023-01-01',periods=len(g)))

def run():
    sys.stdout.reconfigure(encoding='utf-8');cases={}
    cfg=json.loads((ROOT/'configuration.json').read_text(encoding='utf-8'))
    # Artificial2day tests intentionally fix1000Sungrow units, not a proposed purchase.
    fixed={'sungrow-st255cs-2h':1000}
    data=frame([.4,0],[0,0],[0,0])
    a,s=solve(data,cfg,'A',cap=1000,fixed_battery=fixed,name='test_crossday_H2',seconds=30)
    assert s.battery_h2.iloc[1]>.055
    cases[a['name']]=check(a,s)
    data=frame([0,.4],[0,0],[0,0])
    a,s=solve(data,cfg,'A',cap=1000,fixed_battery=fixed,name='test_no_future_borrowing',seconds=30)
    assert abs(s.h2_kg.iloc[0])<1e-5;cases[a['name']]=check(a,s)
    for deficit in (.03,.3):
        data=frame([.4,0],[0,deficit],[0,-100])
        a,s=solve(data,cfg,'B',cap=1000,fixed_battery=fixed,name=f'test_B_priority_{deficit}',seconds=30)
        if deficit<.1:
            assert abs(s.battery_sale.iloc[1]-deficit)<1e-7 and s.battery_h2.iloc[1]>.01
        else:assert s.unserved.iloc[1]>.1 and abs(s.battery_h2.iloc[1])<1e-7
        cases[a['name']]=check(a,s)
    data=frame([.4,0,0],[0,.03,.06],[0,-100,300])
    for policy in ('A','B'):
        a,s=solve(data,cfg,policy,cap=0,fixed_battery=fixed,name='test_negative_'+policy,seconds=30)
        if policy=='A':assert abs(s.battery_sale.iloc[1])<1e-7
        else:assert abs(s.battery_sale.iloc[1]-.03)<1e-7
        cases[a['name']]=check(a,s)
    (ROOT/'results/behavioural_checks.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
    print('PASS',len(cases),'forced-storage behaviours')

if __name__=='__main__':run()
