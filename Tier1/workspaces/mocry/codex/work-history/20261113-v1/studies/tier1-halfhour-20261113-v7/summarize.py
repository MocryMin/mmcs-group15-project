from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OLD=(ROOT/'source_data' if (ROOT/'source_data').exists() else ROOT.parent)/'tier1-multiproduct-20261110-v6'
def read(name):return json.loads((ROOT/'results'/f'{name}.json').read_text())
main={'A':read('full_A_candidate'),'B':read('full_B_candidate')}
cert={k:read('certificate_'+k) for k in main}
rows=[];annual=[];proof={}
for policy,v in main.items():
    old=json.loads((OLD/'results'/f'{policy}_comparable_main.json').read_text())
    gap=(cert[policy]['upper_increment_mGBP']-v['annual_increment_mGBP'])*1e6
    minimum=min(x['reduced_cost_lower'] for x in cert[policy]['pricing_audit'])*1e6
    proof[policy]={'global_upper_annual_increment_GBP':cert[policy]['upper_increment_mGBP']*1e6,
                   'feasible_annual_increment_GBP':v['annual_increment_mGBP']*1e6,
                   'global_absolute_gap_GBP':gap,'global_gap_percent':gap/(v['annual_increment_mGBP']*1e6)*100,
                   'minimum_integer_battery_dual_penalty_GBP':minimum,
                   'zero_battery_certified':minimum>gap+10,
                   'proof':'Any positive integer battery purchase lowers the continuous upper bound by at least its positive reduced cost. That penalty exceeds the gap to the zero-battery feasible integer plan. Numerical safety margin: GBP10/year.'}
    assert proof[policy]['zero_battery_certified']
    for scale,meta in [('daily_v6',old),('half_hour_v7',v)]:
        rows.append(dict(policy=policy,scale=scale,battery_MWh=meta['battery_MWh'],electrolyser_MW=meta['electrolyser_MW'],
                         annual_increment_mGBP=meta.get('annual_increment_mGBP',meta.get('annual_incremental_profit_mGBP')),
                         annual_h2_tonnes=meta['annual_h2_tonnes'],demand_coverage=meta['demand_coverage'],
                         initial_capex_mGBP=meta['initial_capex_mGBP']))
    s=pd.read_csv(ROOT/'results'/f'full_{policy}_candidate_schedule.csv.gz');s['year']=s.date.str[:4].astype(int)
    cfg=json.loads((ROOT/'configuration.json').read_text())
    for year,frame in s.groupby('year'):
        electricity=np.dot(frame.price,frame.sales)/1000
        hydrogen=frame.h2_kg.sum()*cfg['netback']/1e6
        reference=np.dot(frame.price,np.minimum(frame.g,frame.d)*(frame.price>=0 if policy=='A' else 1))/1000
        annual.append(dict(policy=policy,year=year,electricity_mGBP=electricity,hydrogen_mGBP=hydrogen,reference_mGBP=reference,
                           equipment_mGBP=v['annual_equipment_mGBP'],annual_increment_mGBP=electricity+hydrogen-reference-v['annual_equipment_mGBP'],
                           h2_tonnes=frame.h2_kg.sum()/1000,demand_coverage=frame.sales.sum()/frame.d.sum(),
                           unused_GWh=frame.unused.sum(),unserved_GWh=frame.unserved.sum()))
pd.DataFrame(rows).to_csv(ROOT/'results/comparison.csv',index=False)
annual=pd.DataFrame(annual);annual.to_csv(ROOT/'results/annual_results.csv',index=False)
(ROOT/'results/global_certificates.json').write_text(json.dumps(proof,indent=2))
for policy,v in main.items():
    assert abs(annual.loc[annual.policy==policy,'annual_increment_mGBP'].mean()-v['annual_increment_mGBP'])<1e-6
oldann=pd.read_csv(OLD/'results/annual_breakdown.csv')
fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
for ax,policy in zip(axes,['A','B']):
    old=oldann.loc[oldann['case']==policy+'_comparable_main'].sort_values('year')
    new=annual.loc[annual.policy==policy].sort_values('year');x=np.arange(6)
    ax.bar(x-.18,old.annual_incremental_profit_mGBP,.36,color='#808b96',label='Daily v6')
    ax.bar(x+.18,new.annual_increment_mGBP,.36,color='#234f72',label='Half-hour v7')
    ax.axhline(0,color='black',lw=.7);ax.set_xticks(x,new.year)
    ax.set_title('A: economic dispatch' if policy=='A' else 'B: electricity-sales priority')
    ax.set_ylabel('Increment over same-policy no investment (GBP m/year)')
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);ax.legend(frameon=False)
fig.savefig(ROOT/'results/annual_comparison.png',dpi=190);fig.savefig(ROOT/'results/annual_comparison.pdf')
print(json.dumps(proof,indent=2));print(annual[['policy','year','annual_increment_mGBP']].to_string(index=False))
