import json, pathlib
R = json.loads((pathlib.Path(__file__).resolve().parents[1] / "results/results.json").read_text(encoding="utf-8"))
print("== cases")
for c in R["cases"]:
    print(f"{c['case']:14s} nb={c['n_battery_units']:3d} nh={c['n_h2_modules']:3d} incr={c['increment_mGBP']:9.4f} "
          f"capex={c['capex_mGBP']:9.3f} pb_pre={c['payback_pre_stack_years']} pb_after={c['payback_after_stack_years']} "
          f"roi={c['roi']} npv={c['npv30_mGBP']} h2={c['h2_input_GWh']:8.3f} unused={c['unused_GWh']:9.3f} cov={c['demand_coverage']}")
print("== robustness")
for c in R["robustness"]:
    print(f"{c['case']:18s} incr={c['increment_mGBP']:9.4f} h2={c['h2_input_GWh']:8.3f} cov={c['demand_coverage']}")
print("== sensitivity")
for c in R["sensitivity"]:
    print(f"{c['case']:26s} nh={c['n_h2_modules']:2d} incr={c['increment_mGBP']:9.4f} h2={c['h2_input_GWh']:8.3f}")
print("== battery sweep")
for r in R["battery_sweep"]:
    print(r)
print("== trigger grid (rows netback, cols offtake -> modules)")
Ls = sorted({g["offtake_kg_day"] for g in R["trigger_grid"]})
print("L:", Ls)
for v in sorted({g["netback_GBP2020_kg"] for g in R["trigger_grid"]}):
    row = [str(next(g["MW"] for g in R["trigger_grid"] if g["netback_GBP2020_kg"] == v and g["offtake_kg_day"] == L)) for L in Ls]
    inc = [f"{next(g['increment_mGBP'] for g in R['trigger_grid'] if g['netback_GBP2020_kg'] == v and g['offtake_kg_day'] == L):.2f}" for L in Ls]
    print(f"v={v:6.2f} MW {row}")
    print(f"         incr {inc}")
print("== supply frontier")
for r in R["supply_frontier"]:
    print(r)
