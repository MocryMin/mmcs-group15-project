"""Build immutable dated research groups from official calendar and repaired fuels."""
from pathlib import Path
import json,hashlib
import pandas as pd,numpy as np
from features import ROOT

def save(name,frame,meta):
    p=ROOT/'features'/(name+'.csv');raw=frame.to_csv(index_label='date').encode()
    if p.exists():assert p.read_bytes()==raw,'Version a changed feature group rather than overwrite it'
    else:p.write_bytes(raw)
    record={'group':name,'rows':len(frame),'features':list(frame),'sha256':hashlib.sha256(raw).hexdigest(),**meta}
    (ROOT/'features'/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

idx=pd.date_range('2021-01-01','2026-09-17');target=idx+pd.Timedelta(days=1)
official=json.loads((ROOT/'research/govuk_bank_holidays.json').read_text());cal=pd.DataFrame(index=idx)
for region in ['england-and-wales','scotland']:
    dates=pd.DatetimeIndex([r['date'] for r in official[region]['events']])
    for shift in [-1,0,1]:cal[region+'_target_offset'+str(shift)]=(target+pd.Timedelta(days=shift)).isin(dates).astype(int)
save('bank_holidays',cal,{'source':'https://www.gov.uk/bank-holidays.json','availability':'Published holiday calendar; target date known before end-of-origin. Special-announcement vintage not reconstructed, but only +/-1 day flags used.','mechanism':'Working activity and demand differ on public holidays and adjacent days; GB uses England/Wales and Scotland flags, excluding Northern Ireland.'})
fuel=ROOT/'inputs/course_generation_by_fuel.csv'
if not fuel.exists():fuel=ROOT.parent/'data-repair-20261104-v2/data/daily_generation_by_fuel.csv'
d=pd.read_csv(fuel,parse_dates=['date']).pivot(index='date',columns='psrType',values='MW').reindex(idx)
assert d.notna().all().all()
selected=['Fossil Gas','Nuclear','Solar','Wind Offshore','Wind Onshore'];mix=pd.DataFrame(index=idx)
for col in selected:mix[col+'_origin_MW']=d[col];mix[col+'_mean7_MW']=d[col].rolling(7,min_periods=1).mean()
mix['nonwind_nonsolar_origin_MW']=d.drop(columns=['Solar','Wind Offshore','Wind Onshore']).sum(axis=1)
mix['wind_share_origin']=(d['Wind Offshore']+d['Wind Onshore'])/d.sum(axis=1).clip(lower=1000)
mix['solar_share_origin']=d.Solar/d.sum(axis=1).clip(lower=1000)
save('fuel_mix',mix,{'source':str(fuel.relative_to(ROOT.parent)),'source_sha256':hashlib.sha256(fuel.read_bytes()).hexdigest(),'availability':'Origin day measured/repaired values; same end-of-day availability assumption as base generation. No target-day fuel outputs used. Source vintage not independently audited.','mechanism':'Separate weather-driven wind/solar from persistent nuclear and dispatchable gas output; supply persistence differs across technologies.'})
print('built bank_holidays and fuel_mix')
