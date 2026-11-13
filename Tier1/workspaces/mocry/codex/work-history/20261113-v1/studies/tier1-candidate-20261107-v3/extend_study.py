"""Complete the cross-year appraisal, contract tests and independent reconciliation."""
import json
import math
from dataclasses import replace

import numpy as np
import pandas as pd

import run_study as model


def run():
    frame, econ = model.load_data(), model.economics()
    summary = json.loads((model.OUT / "study.json").read_text(encoding="utf-8"))
    cases = summary["cases"]
    design = frame.loc["2023"]
    whole_years = frame.loc["2020":"2025"]
    extras = {}

    def save(name, answer):
        result, schedule = answer
        extras[name] = result
        schedule.to_csv(model.OUT / "schedules" / f"{name}.csv", index_label="date")
        return result

    annual_rows = []
    for year in range(2020, 2027):
        year_frame = frame.loc[str(year)]
        surplus = (year_frame.g - year_frame.d).clip(lower=0)
        a, b = cases[f"A_fixed20_{year}"], cases[f"B_fixed20_{year}"]
        annual_rows.append(dict(
            year=year, days=len(year_frame), full_year=year < 2026,
            surplus_days=int((surplus > 1e-9).sum()), surplus_GWh=float(surplus.sum()),
            A_gain=a["net"], B_gain=b["net"], A_H2_input_GWh=a["h2_GWh"],
            B_H2_input_GWh=b["h2_GWh"], A_capture_GWh=a["capture_GWh"],
            A_surplus_share=a["capture_GWh"] / a["h2_GWh"],
        ))
    yearly = pd.DataFrame(annual_rows)
    yearly.to_csv(model.OUT / "annual_replay.csv", index=False)
    assert yearly.loc[yearly.full_year, "surplus_GWh"].idxmin() == 3

    # The annual mean of the free-charge bound excludes batteries in the pooled case.
    # Enumerating all possible electrolyser counts therefore solves the common-size model.
    pooled = {}
    bounds = {}
    for policy in ("A", "B"):
        bounds[policy] = model.battery_bound(whole_years, econ, policy)
        assert bounds[policy]["ruled_out"]
        values = []
        upper = math.ceil(econ.offtake / (econ.kg_per_gwh * econ.h2_unit))
        for count in range(upper + 1):
            gain, h, online = model.hydrogen_enumeration(
                whole_years, econ, policy, count, econ.netback, econ.offtake)
            values.append(dict(modules=count, gain=gain))
        best = max(values, key=lambda item: (item["gain"], -item["modules"]))
        pooled[policy] = dict(best=best, candidates=values)
        gain, h, online = model.hydrogen_enumeration(
            whole_years, econ, policy, best["modules"], econ.netback, econ.offtake)
        q = model.direct_reference(whole_years, policy)
        if policy == "A":
            q = np.where(whole_years.price.to_numpy() >= 0,
                         np.minimum(whole_years.g.to_numpy() - h, whole_years.d.to_numpy()), 0.)
        zeros = np.zeros(len(whole_years))
        result = save(f"{policy}_common2020_25", model.measure(
            whole_years, econ, policy, 0, best["modules"], q, zeros, zeros, h, online,
            zeros, False, econ.netback, econ.offtake))
        assert abs(result["net"] - gain) < 1e-9
        result["solver"] = "Exact enumeration, with battery revenue bound"
        assert best["modules"] == 1
        assert abs(result["net"] - yearly.loc[yearly.full_year, f"{policy}_gain"].mean()) < 1e-8

    for policy in ("A", "B"):
        save(f"{policy}_fixed40_2023", model.solve(design, econ, policy, fixed=(0, 2)))
        save(f"{policy}_offtake50_2023", model.solve(design, econ, policy, offtake=50000))
        save(f"{policy}_low_netback_2023", model.solve(design, econ, policy, netback=3.))
    sales = cases["A_zero"]["baseline_sales_GWh"]
    for floor in (.9999, 1.):
        save(f"A_floor_{floor:.4f}", model.solve(design, econ, "A", service_floor=sales * floor))
    for rate in (0., .12):
        save(f"A_rate_{rate:.2f}", model.solve(design, replace(econ, rate=rate), "A", fixed=(0, 1)))
    for scale in (.75, 1.25):
        save(f"A_capital_{scale:.2f}", model.solve(
            design, replace(econ, hydrogen_capex=econ.hydrogen_capex * scale), "A", fixed=(0, 1)))

    lower, upper = 0., econ.offtake
    for _ in range(42):
        midpoint = (lower + upper) / 2
        value = model.hydrogen_enumeration(design, econ, "A", 1, econ.netback, midpoint)[0]
        if value > 0:
            upper = midpoint
        else:
            lower = midpoint

    peer = pd.read_csv(model.ROOT / "references/independent-b-cases.csv").set_index("case")
    reconciliation = {}
    for policy in ("A", "B"):
        for year in range(2020, 2027):
            name = f"{policy}_fixed20_{year}"
            ours, theirs = cases[name], peer.loc[name]
            delta = abs(ours["net"] - theirs.increment_mGBP) * 1e6
            assert delta < 50.01
            reconciliation[name] = delta
    floor_case = extras["A_floor_0.9999"]
    assert abs(floor_case["displacement_GWh"] - sales * .0001) < 1e-8
    assert extras["A_floor_1.0000"]["nh"] == 0
    assert abs(extras["A_fixed40_2023"]["net"] - 7.470699682269822) < 1e-8
    assert extras["A_offtake50_2023"]["nh"] == 6
    extras_frame = pd.DataFrame.from_dict(extras, orient="index")
    extras_frame.to_csv(model.OUT / "additional_cases.csv", index_label="case")
    model.write_json(model.OUT / "extension.json", dict(
        cases=extras, common_size=pooled, battery_bounds=bounds,
        offtake_break_even_kg_day=upper, independent_yearly_differences_GBP=reconciliation,
        physical_cap_GWh=float(np.minimum(
            (design.g - design.d).clip(lower=0), econ.offtake / econ.kg_per_gwh).sum()),
        complete_years=6, partial_year=2026,
    ))
    print("Six-year appraisal and additional checks passed.", flush=True)


if __name__ == "__main__":
    run()
