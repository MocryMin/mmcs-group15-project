"""Small forced-asset cases that exercise the changed temporal semantics."""
import json
import numpy as np
import pandas as pd
from model import ROOT,solve
from verify import verify

cfg=json.loads((ROOT/'configuration.json').read_text())
idx=pd.date_range('2022-01-01',periods=48,freq='30min',tz='UTC')
def frame():
    return pd.DataFrame(dict(date=idx.strftime('%Y-%m-%d'),g=np.zeros(48),d=np.zeros(48),price=np.zeros(48)),index=idx)
fixed={p['id']:0 for p in cfg['batteries']+cfg['electrolysers']}
fixed['sungrow-st255cs-2h']=1
f=frame();f.iloc[0,f.columns.get_loc('g')]=.001;f.iloc[1,f.columns.get_loc('d')]=.001;f.iloc[1,f.columns.get_loc('price')]=100
solve(f,cfg,'A','test_halfhour_power_and_intraday',cap=0,seconds=30,fixed=fixed)
verify('test_halfhour_power_and_intraday')
s=pd.read_csv(ROOT/'results/test_halfhour_power_and_intraday_schedule.csv.gz')
assert abs(s.charge.iloc[0]-.5*.125/1000)<1e-9
assert s.battery_sale.iloc[1]>0
# Charge over multiple slots. B must discharge at its power cap, even at
# a low price before a later high-price period.
f=frame();f.loc[idx[:4],'g']=.001;f.loc[idx[4:8],'d']=.001;f.loc[idx[4:8],'price']=[1,2,3,1000]
solve(f,cfg,'B','test_B_power_limited_priority',cap=0,seconds=30,fixed=fixed)
verify('test_B_power_limited_priority')
s=pd.read_csv(ROOT/'results/test_B_power_limited_priority_schedule.csv.gz')
assert s.battery_sale.iloc[4]>.00006
assert s.battery_sale.iloc[4]<=.0000625+1e-9
# One small electrolyser can start and stop within a day; the daily offtake
# allowance must be shared across all slots.
fixed={p['id']:0 for p in cfg['batteries']+cfg['electrolysers']};fixed['nel-mc250']=1
f=frame();f['g']=.01
solve(f,cfg,'A','test_H2_daily_cap',cap=20,seconds=30,fixed=fixed)
verify('test_H2_daily_cap')
s=pd.read_csv(ROOT/'results/test_H2_daily_cap_schedule.csv.gz')
assert abs(s.h2_kg.sum()-20)<1e-5
assert s.h2_kg.max()<=22.125*.5+1e-6
print('ALL TEMPORAL BEHAVIOUR TESTS PASSED',flush=True)
