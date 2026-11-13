"""Recompute the revised model and preserve the old candidate as a frozen input."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

import pandas as pd

import legacy_model as legacy
from market_inputs import build
from model import Specification, save, solve
from verify_model import check

ROOT = Path(__file__).resolve().parent


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', choices=['main', 'sensitivity', 'reference'], default='main')
    parser.add_argument('--seconds', type=int, default=240)
    args = parser.parse_args()
    legacy.prepare_inputs()
    data, econ = legacy.load_data(), legacy.economics()
    cap = build()
    config = dict(version='v5-20261110',
                  active_economic_basis='inputs/parameters.json (frozen v4.1 financial values)',
                  overrides=dict(hydrogen_limit_kg=cap),
                  market_case='national historical annual demand high-envelope, smoothed daily',
                  chronology='daily contiguous state balance, zero initial and terminal usable stock',
                  battery_routes=['electricity sales', 'electrolyser electricity input'],
                  policy_B='current generation first; stored usable energy must next cover remaining demand',
                  equipment_grid='3MWh/1.5MW generic BESS and 20MW reference PEM; not a universal product set',
                  new_product_catalogue='research/EQUIPMENT_OPTIONS.md; not silently substituted into baseline',
                  unchanged=['constant H2 netback', 'no H2 storage/reconversion', 'no grid imports',
                             'two-hour batteries', '20-80% SOC', 'one net charge/discharge action per day',
                             'initial investment once', 'real5% and existing maintenance convention'],
                  full_study_solver='SciPy/HiGHS; installed Xpress Community is limited to5000rows+columns',
                  solver_crosscheck='same-row Xpress behavioural examples, plus fixed-capacity annual Xpress replays')
    (ROOT / 'configuration.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    full = data.loc['2020':'2025']
    full.to_csv(ROOT / 'results' / 'daily_model_inputs.csv', index_label='date')
    if args.suite == 'main':
        jobs = [(f'{policy}_national_upper2020_25', full, policy, cap, {}, econ)
                for policy in ('A', 'B')]
    elif args.suite == 'sensitivity':
        jobs = []
        for policy in ('A', 'B'):
            jobs.append((f'{policy}_old10t2020_25', full, policy, 10000., {}, econ))
            for share in (.001, .01, .1):
                jobs.append((f'{policy}_share{share:g}_2020_25', full, policy, cap * share, {}, econ))
        # The unresolved source maintenance convention must remain visible.
        jobs += [(f'{policy}_low_battery_fom2020_25', full, policy, cap, {},
                  replace(econ, battery_fom=econ.battery_fom / 2)) for policy in ('A', 'B')]
    else:
        jobs = [(f'{policy}_old_routes10t2020_25', full, policy, 10000.,
                 dict(spec=Specification(battery_to_hydrogen=False, battery_supply_priority=False)), econ)
                for policy in ('A', 'B')]
        jobs += [(f'{policy}_national_upper2023', data.loc['2023'], policy, cap, {}, econ)
                 for policy in ('A', 'B')]
    manifest = {}
    for name, frame, policy, limit, options, economics in jobs:
        economics = replace(economics, offtake=limit)
        summary, schedule = solve(frame, economics, policy, limit, seconds=args.seconds, **options)
        checks = check(frame, economics, summary, schedule)
        (ROOT / 'results' / (name + '_audit.json')).write_text(
            json.dumps(checks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest[name] = save(name, (summary, schedule))
        # Persist after every finished optimisation so a longer run is reviewable.
        (ROOT / 'results' / (args.suite + '_summary.json')).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    pd.DataFrame(manifest.values()).drop(columns=['economics', 'specification', 'safe_capacity_bounds']).to_csv(
        ROOT / 'results' / (args.suite + '_summary.csv'), index=False)


if __name__ == '__main__':
    run()
