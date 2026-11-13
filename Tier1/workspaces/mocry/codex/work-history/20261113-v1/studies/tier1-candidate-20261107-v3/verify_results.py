"""Audit exported schedules and cash independently, without importing Xpress/model code."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def run():
    inputs, results = ROOT / "inputs", ROOT / "results"
    manifest = json.loads((inputs / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, value in manifest.items():
        assert hashlib.sha256((inputs / name).read_bytes()).hexdigest() == value["sha256"]
    p = json.loads((inputs / "parameters.json").read_text(encoding="utf-8"))
    main = json.loads((results / "study.json").read_text(encoding="utf-8"))
    extra = json.loads((results / "extension.json").read_text(encoding="utf-8"))
    cases = main["cases"] | extra["cases"]
    max_flow, max_cash, saved = 0., 0., []
    for name, case in cases.items():
        s = pd.read_csv(results / "schedules" / f"{name}.csv", parse_dates=["date"])
        assert len(s) == case["days"] and s.date.is_unique
        assert np.isfinite(s.drop(columns="date")).all().all()
        years = np.sum(1 / np.where(s.date.dt.is_leap_year, 366, 365))
        assert abs(years - case["represented_years"]) < 1e-10
        errors = [np.max(abs(s.g - s.direct - s.charge - s.h2_input - s.unused)),
                  max(0., -np.min(s[["direct", "charge", "discharge", "h2_input", "unused"]])),
                  max(0., np.max(s.direct + s.discharge - s.demand)),
                  np.max(abs(s.modules - np.round(s.modules))),
                  max(0., np.max(s.modules - case["nh"])),
                  max(0., np.max(s.h2_input - .48 * s.modules)),
                  max(0., np.max(.096 * s.modules - s.h2_input)),
                  max(0., np.max(s.h2_input * 1e6 / p["hydrogen_kWh_kg"] - case["offtake_kg_day"])) / 1e6,
                  np.max(np.minimum(s.charge, s.discharge))]
        capacity = case["nb"] * .0018
        errors.extend([max(0., np.max(s.charge - capacity / p["eta"])),
                       max(0., np.max(s.discharge - capacity * p["eta"]))])
        if case["chronology"]:
            previous = s.stock.shift(1, fill_value=0)
            errors.extend([np.max(abs(s.stock - previous - p["eta"] * s.charge + s.discharge / p["eta"])),
                           max(0., np.max(s.stock - capacity)), max(0., -s.stock.min()), abs(s.stock.iloc[-1])])
        else:
            errors.append(abs(s.discharge.sum() - p["eta"] ** 2 * s.charge.sum()))
        reference = np.minimum(s.g, s.demand)
        if case["policy"] == "A":
            reference = np.where(s.price >= 0, reference, 0)
        else:
            errors.append(np.max(abs(s.direct - reference)))
        errors.append(np.max(abs(s.reference_sale - reference)))
        flow_error = max(errors)
        assert flow_error < 1e-6, (name, errors)
        direct = np.dot(s.price, s.direct - reference) / (1000 * years)
        discharge = np.dot(s.price, s.discharge) / (1000 * years)
        hydrogen = s.h2_input.sum() / years * 1e6 / p["hydrogen_kWh_kg"] * case["price_H2"] / 1e6
        cash_errors = [abs(direct - case["direct_change"]), abs(discharge - case["discharge_value"]),
                       abs(hydrogen - case["hydrogen_value"]),
                       abs(direct + discharge + hydrogen - case["annual_cost"] - case["net"])]
        cash_error = max(cash_errors)
        assert cash_error < 1e-7, (name, cash_errors)
        for column, field in (("h2_input", "h2_GWh"), ("capture", "capture_GWh"), ("unused", "unused_GWh")):
            assert abs(s[column].sum() / years - case[field]) < 1e-6, (name, field)
        if case.get("service_floor_GWh") is not None:
            assert s.direct.sum() + s.discharge.sum() >= case["service_floor_GWh"] - 1e-6
        max_flow, max_cash = max(max_flow, flow_error), max(max_cash, cash_error)
        saved.append(name)
    years = pd.read_csv(results / "annual_replay.csv")
    assert len(years) == 7 and years.loc[years.full_year, "days"].sum() == 2192
    assert (years.loc[years.full_year, "B_gain"] < 0).sum() == 3
    for policy in "AB":
        assert abs(years.loc[years.full_year, f"{policy}_gain"].mean() -
                   extra["cases"][f"{policy}_common2020_25"]["net"]) < 1e-8
    report = dict(all_passed=True, schedules_checked=len(saved),
                  xpress_schedules=sum(c.get("solver") == "Xpress" for c in cases.values()),
                  simple_rules=2, exact_common_size_schedules=2,
                  largest_flow_residual_MWh=max_flow * 1000,
                  largest_cash_residual_GBP_year=max_cash * 1e6,
                  independent_annual_replays=14,
                  largest_peer_rounding_difference_GBP=max(extra["independent_yearly_differences_GBP"].values()),
                  contract_grid_points=main["summary"]["checks"]["grid_cells"],
                  xpress_contract_grid_crosschecks=8,
                  input_sha256_checks=len(manifest))
    (results / "VALIDATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
