"""Check training-prefix capacity and battery bounds without fitting a predictor."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tier1-root',type=Path,default=HERE.parent/'tier1-candidate-20261107-v4.1-academic')
    args=parser.parse_args()
    root=args.tier1_root.resolve()
    sys.path.insert(0,str(root))
    import run_study as model
    model.prepare_inputs()
    frame,econ=model.load_data().loc['2020':'2022'],model.economics()
    result=dict(scope='Preliminary Tier2B structural check, not a forecast/controller experiment',
                training_years='2020-2022',training_days=len(frame),
                netback_GBP2020_kg=econ.netback,
                hydrogen_equivalent_GBP2020_MWh=econ.netback/.0559,
                conditions='Current daily throughput, costs, A/B policies; no cross-day sales budget or hydrogen stock',
                model_sha256=hashlib.sha256((root/'run_study.py').read_bytes()).hexdigest(),policies={})
    for policy in 'AB':
        bound=model.battery_bound(frame,econ,policy)
        candidates=[dict(modules=n,gain_mGBP2020_year=model.hydrogen_enumeration(
            frame,econ,policy,n,econ.netback,econ.offtake)[0]) for n in range(3)]
        best=max(candidates,key=lambda x:(x['gain_mGBP2020_year'],-x['modules']))
        assert bound['ruled_out'] and best['modules']==1
        result['policies'][policy]=dict(battery_bound=bound,hydrogen_candidates=candidates,
                                        chosen_battery_modules=0,chosen_electrolyser_modules=best['modules'])
    (HERE/'STRUCTURAL_CHECK.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
