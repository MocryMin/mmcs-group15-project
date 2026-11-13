import argparse
import json
from pathlib import Path
import sys
import legacy_model as legacy
from model import solve

ROOT=Path(__file__).resolve().parent

def reference_assets(config, include):
    """Restore the v5 generic grid exactly, either alone or beside real products."""
    p=json.loads((ROOT/'inputs/parameters.json').read_text(encoding='utf-8'))
    capex=3*p['battery_cost_MWh'];fom=1.5*p['battery_FOM_MW']
    b=dict(id='v5-reference-battery',E_MWh=3.,P_MW=1.5,rte=p['eta']**2,life=p['battery_life'],
        capital_GBP=capex,fom_GBP=fom,fom_literal_GBP=fom/2,soc_lower=.2,soc_upper=.8,self_discharge=0.)
    h=dict(id='v5-reference-PEM',MW=20.,kg_hour=20000/p['hydrogen_kWh_kg'],
        kWh_kg=p['hydrogen_kWh_kg'],minimum=p['hydrogen_min'],life=p['hydrogen_life'],
        comparable=dict(capital_GBP=20*p['hydrogen_cost_MW'],fom_GBP=20*p['hydrogen_FOM_MW'],
            replacement_GBP=20*p['hydrogen_replacement_MW'],replacement_years=p['hydrogen_replacement_years'],
            variable_GBP_kg=0.))
    return config|dict(batteries=(config['batteries'] if include else [])+[b],
        electrolysers=(config['electrolysers'] if include else [])+[h])

def run():
    sys.stdout.reconfigure(encoding='utf-8')
    a=argparse.ArgumentParser();a.add_argument('--case',default='comparable');a.add_argument('--policy',default='AB')
    a.add_argument('--seconds',type=int,default=240);a.add_argument('--cap',type=float)
    a.add_argument('--battery-cost',default='main');a.add_argument('--single-h')
    a.add_argument('--reference',choices=['only','included']);a.add_argument('--research-battery-operation',action='store_true')
    args=a.parse_args()
    cfg=json.loads((ROOT/'configuration.json').read_text(encoding='utf-8'))
    legacy.prepare_inputs();frame=legacy.load_data().loc['2020':'2025']
    (ROOT/'results').mkdir(exist_ok=True)
    if args.reference:
        assert args.case=='comparable'
        cfg=reference_assets(cfg,args.reference=='included')
    if args.research_battery_operation:
        for b in cfg['batteries']:
            b['soc_lower']=.1;b['soc_upper']=.9;b['self_discharge']=b['research_self_discharge']
    for policy in args.policy:
        name=f'{policy}_{args.case}_{args.battery_cost}'
        if args.cap is not None:name+=f'_cap{args.cap:g}'
        if args.single_h:name+='_'+args.single_h
        if args.reference:name+='_reference_'+args.reference
        if args.research_battery_operation:name+='_research_battery_operation'
        solve(frame,cfg,policy,args.case,args.battery_cost,args.cap,args.seconds,single_h=args.single_h,name=name)

if __name__=='__main__':run()
