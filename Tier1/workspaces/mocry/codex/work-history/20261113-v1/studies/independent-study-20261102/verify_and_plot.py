"""Independent hydrogen calculation, chronology counterexample, and figures."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_study import HERE,inputs,optimize,CRF,BASE_B_COST

results=json.loads((HERE/'results.json').read_text())
r={x['case']:x for x in results}
df=pd.read_csv(HERE/'aligned_data.csv',index_col='date',parse_dates=True)
train=inputs(df.loc['2023':'2024'])
S=train.surplus.to_numpy()
# With no battery, the best full-day hydrogen dispatch for a fixed H is explicit.
candidate=np.unique(np.r_[S[S>0]/24,S[S>0]/4.8])
q=np.minimum(S[:,None],24*candidate[None,:])
q=np.where(S[:,None]+1e-7>=4.8*candidate[None,:],q,0)
kg=q.sum(axis=0)/.0559/2
cost=candidate*1e6*(CRF+.03)
profit=9.5*kg-cost
i=profit.argmax()
check={
 'independent_hydrogen_optimum_MW':float(candidate[i]),
 'independent_net_GBP_year':float(profit[i]),
 'difference_from_Xpress_GBP':float(profit[i]-r['hydrogen_only']['net_increment_GBP_year']),
 'minimum_H2_price_for_any_profitable_capacity_GBP_kg':float(np.min(cost/kg)),
 'maximum_H2_capex_for_any_profitable_capacity_GBP_MW':float(np.max(9.5*kg/(candidate*(CRF+.03))))}
assert abs(check['difference_from_Xpress_GBP'])<1e-3
# Surplus after the only valuable discharge day cannot be used retrospectively.
toy=pd.DataFrame({'generation_MW':[0.,0.],'demand_MW':[1.,0.],
 'wind_MW':[0.,1.],'price_MWh':[100.,0.],'price_MWday':[2400.,0.]},
 index=pd.date_range('2025-01-01',periods=2))
chron=optimize('test_future_energy_unavailable',toy,fixed=(1,0),allow_h=False)
pooled=optimize('test_pooled_can_borrow_future',toy,mode='pooled',fixed=(1,0),allow_h=False)
assert chron['discharge_MWh_year']<1e-8
assert abs(pooled['discharge_MWh_year']-1.2*np.sqrt(.9))<1e-6
toy=toy.iloc[::-1].set_axis(pd.date_range('2025-01-01',periods=2))
forward=optimize('test_energy_loss_90pct',toy,fixed=(1,0),allow_h=False)
assert abs(forward['discharge_MWh_year']/forward['charge_MWh_year']-.9)<1e-7
check.update(chronology_reverse_discharge=chron['discharge_MWh_year'],
 pooled_reverse_discharge=pooled['discharge_MWh_year'],
 forward_round_trip=forward['discharge_MWh_year']/forward['charge_MWh_year'],
 all_main_cases_optimal=all(x.get('solstatus',1)==1 for x in results),
 main_case_count=len(results),xpress_solve_count=sum('solver' in x for x in results),
 max_main_numeric_violation=max(x['max_check_violation'] for x in results))
# Perfect-information dispatch is an upper bound on any feasible causal dispatch.
for prefix in ['2025_fixed_design','diagnostic_50MW']:
 pf='2025_fixed_design_perfect_foresight' if prefix.startswith('2025') else 'diagnostic_50MW_chronological'
 assert r[pf]['net_increment_GBP_year']+1e-4>=r[prefix+'_causal']['net_increment_GBP_year']
(HERE/'verification.json').write_text(json.dumps(check,indent=2)+'\n')

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
names=['tier2_chronological','wind_included_in_total','curtailment_pro_rata','hydrogen_price_6','hydrogen_cost_2000000','demand_plus10pct']
labels=['Trial base','Wind already in total','Pro-rata curtailment','H2 price GBP 6/kg','H2 capex GBP 2m/MW','Demand +10%']
axs[0].barh(labels,[r[n]['electrolyser_MW'] for n in names],color='#266c87');axs[0].invert_yaxis();axs[0].set_xlabel('Optimal electrolyser capacity (MW)');axs[0].set_title('Assumptions change the investment')
yrs=[2023,2024,2025]; energy=[inputs(df.loc[str(y)]).surplus.sum()/1e6 for y in yrs]
axs[1].bar(list(map(str,yrs)),energy,color=['#266c87','#266c87','#df963b']);axs[1].set_ylabel('Available wind surplus (TWh)');axs[1].set_title('2025 differs markedly from training years')
fig.savefig(HERE/'findings.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,3.2),layout='constrained')
schedule=pd.read_csv(HERE/'outputs/diagnostic_50MW_chronological.csv',parse_dates=['date'])
ax.plot(schedule.date,schedule.usable_SOC_MWh,lw=.9,color='#266c87');ax.set_ylim(0,63)
ax.set_ylabel('Usable SOC (MWh)');ax.set_title('Chronology test: fixed 50 MW / 100 MWh battery in 2025')
fig.savefig(HERE/'battery_chronology.png',dpi=160);plt.close(fig)
print(json.dumps(check,indent=2))
print(pd.DataFrame(results)[['case','battery_MW','electrolyser_MW','net_increment_GBP_year','capex_GBP']].to_string(index=False))
