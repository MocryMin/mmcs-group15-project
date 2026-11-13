"""Reopen exported schedules, reconcile all rows, and check zero-battery choices independently."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import legacy_model as old
from verify_model import check

ROOT = Path(__file__).resolve().parent


def run():
    data = old.load_data()
    audits, enumeration, xpress = {}, {}, []
    for path in sorted((ROOT / 'results').glob('*_schedule.csv')):
        case = path.stem.removesuffix('_schedule')
        summary = json.loads(path.with_name(case + '.json').read_text(encoding='utf-8'))
        schedule = pd.read_csv(path, index_col='date', parse_dates=True)
        econ = old.Economics(**summary['economics'])
        econ = old.replace(econ, stack_years=tuple(econ.stack_years))
        frame = data.loc[schedule.index]
        audits[case] = check(frame, econ, summary, schedule)
        if summary['battery_modules'] == 0:
            candidates = [old.hydrogen_enumeration(frame, econ, summary['policy'], n,
                                                   econ.netback, summary['cap_kg_day'])[0]
                          for n in range(summary['safe_capacity_bounds']['electrolyser_modules'] + 1)]
            best = max(range(len(candidates)), key=lambda i: (round(candidates[i], 8), -i))
            assert best == summary['electrolyser_modules'], (case,best,summary['electrolyser_modules'])
            error = abs(candidates[best] - summary['annual_incremental_profit_mGBP'])
            assert error < 1e-5, (case,error)
            enumeration[case] = dict(candidates=len(candidates), best_modules=best, objective_error_mGBP=error)
        assert summary['optimal'], (case,summary['gap'])
    # Full common-capacity problem exceeds the locally installed Community limit.
    # These year-by-year checks fit that licence and use the original Xpress code.
    for policy in ('A','B'):
        summary=json.loads((ROOT/'results'/f'{policy}_national_upper2020_25.json').read_text(encoding='utf-8'))
        assert summary['battery_modules']==0
        econ=old.Economics(**summary['economics'])
        profits=[]
        for year in range(2020,2026):
            result=old.solve(data.loc[str(year)],econ,policy,fixed=(0,summary['electrolyser_modules']),
                             offtake=summary['cap_kg_day'])[0]
            profits.append(result['net'])
            xpress.append(dict(policy=policy,year=year,fixed_MW=result['h2_MW'],
                                incremental_profit_mGBP=result['net'],solver=result['solver']))
        assert abs(np.mean(profits)-summary['annual_incremental_profit_mGBP'])<1e-5
    report=dict(saved_schedules=len(audits),schedule_audits=audits,
                independent_zero_battery_enumeration=enumeration,
                annual_Xpress_replays=xpress,
                largest_profit_error_mGBP=max(a['profit_error_mGBP'] for a in audits.values()),
                largest_flow_error_GWh=max(max(a['errors_GWh'].values()) for a in audits.values()))
    (ROOT/'results'/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('VERIFIED',len(audits),'saved schedules;',len(enumeration),'independent capacity enumerations;',
          len(xpress),'Xpress annual replays',flush=True)


if __name__=='__main__':
    run()
