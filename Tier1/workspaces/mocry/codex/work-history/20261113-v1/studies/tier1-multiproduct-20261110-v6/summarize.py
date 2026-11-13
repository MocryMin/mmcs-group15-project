"""Export study tables and reconcile the legacy reference against v5."""
import csv
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'

def read(name):return json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))

def summarize():
    sys.stdout.reconfigure(encoding='utf-8')
    cfg=json.loads((ROOT/'configuration.json').read_text(encoding='utf-8'))
    audits=read('independent_audits')
    summaries=[];years=[];products=[]
    names=sorted(n for n in audits if not n.startswith('test_'))
    expected={'A_comparable_main_reference_only':(1637.39228121016,3640),
              'B_comparable_main_reference_only':(37.71258799914,740)}
    for name,(profit,mw) in expected.items():
        s=read(name)
        assert abs(s['annual_incremental_profit_mGBP']-profit)<1e-7 and abs(s['electrolyser_MW']-mw)<1e-8
    for name in names:
        s=read(name)
        summaries.append({k:v for k,v in s.items() if k not in ('investment','active_products','iterations')})
        for product in s['investment']:products.append(dict(case=name,**product))
        f=pd.read_csv(OUT/(name+'_schedule.csv'),index_col='date',parse_dates=True)
        for year,part in f.groupby(f.index.year):
            net_sale=np.dot(part.price,part.sales)/1000
            base_sale=np.minimum(part.generation,part.demand)
            if s['policy']=='A':base_sale=np.where(part.price>=0,base_sale,0)
            ref=np.dot(part.price,base_sale)/1000
            h2_value=part.h2_kg.sum()*cfg['netback']/1e6
            reserve=sum(part[h['id']+'__kg'].sum()*h['variable_GBP_kg']/1e6 for h in s['active_products']['electrolysers'])
            net=net_sale-ref+h2_value-reserve-s['annual_equipment_fixed_cost_mGBP']
            years.append(dict(case=name,year=year,annual_incremental_profit_mGBP=net,
                electricity_receipts_mGBP=net_sale,reference_receipts_mGBP=ref,hydrogen_receipts_mGBP=h2_value,
                stack_reserve_mGBP=reserve,annual_equipment_fixed_cost_mGBP=s['annual_equipment_fixed_cost_mGBP'],
                hydrogen_tonnes=part.h2_kg.sum()/1000,demand_coverage=part.sales.sum()/part.demand.sum(),
                unserved_GWh=part.unserved.sum(),unused_GWh=part.unused.sum(),battery_to_h2_GWh=part.battery_h2.sum(),
                battery_to_sales_GWh=part.battery_sale.sum()))
        assert abs(np.mean([v['annual_incremental_profit_mGBP'] for v in years if v['case']==name])-
                   s['annual_incremental_profit_mGBP'])<1e-6
    for filename,rows in [('case_summary.csv',summaries),('annual_breakdown.csv',years),('equipment_selection.csv',products)]:
        with (OUT/filename).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    status=dict(study_cases=len(names),forced_storage_cases=len(audits)-len(names),
        all_optimal=all(s['optimal'] for s in summaries),
        max_reported_relative_gap=max(s['gap'] for s in summaries),
        max_balance_error_GWh=max(v['maximum_error_GWh'] for v in audits.values()),
        max_profit_recalculation_error_mGBP=max(v['profit_error_mGBP'] for v in audits.values()),
        max_independent_daily_dispatch_error_mGBP=max(v['independent_daily_dispatch_error_mGBP']
            for v in audits.values() if v['independent_daily_dispatch_error_mGBP'] is not None),
        v5_replay_passed=True)
    (OUT/'verification_summary.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2),flush=True)

if __name__=='__main__':summarize()
