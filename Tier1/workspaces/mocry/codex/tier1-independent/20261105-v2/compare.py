"""Reconcile the pinned independent studies and re-solve the report's added cases."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
V1 = ROOT.parent / "20261105-v1"
CU = ROOT.parents[2] / "cleveruser/tier1/20261105-v1"
sys.path.insert(0, str(V1))
import run_study as study


def run():
    data = study.load_data()
    econ = study.economics()
    cu_data = pd.read_csv(CU / "data/daily_model_inputs.csv", index_col="date", parse_dates=True)
    assert data.index.equals(cu_data.index)
    aligned = {
        "g": "G_GWh", "d": "D_GWh", "price": "price_GBP2020_MWh",
        "wind": "wind_farm_GWh", "strict": "strict_no_imputation",
    }
    errors = {k: float(abs(data[k] - cu_data[v]).max()) for k, v in aligned.items()}
    assert max(errors.values()) < 1e-8
    fuel = pd.read_csv(V1 / "inputs/daily_generation_by_fuel.csv", parse_dates=["date"])
    extra = fuel[fuel.psrType.isin(["Biomass", "Hydro Run-of-river and poundage"])]
    extra = extra.groupby("date").MW.sum().reindex(data.index, fill_value=0) * .024
    assert np.allclose(data.renewable + extra, cu_data.renewable_GWh, atol=1e-8, rtol=0)

    own = json.loads((V1 / "results/study.json").read_text(encoding="utf-8"))["cases"]
    cu = pd.read_csv(CU / "results/cases.csv").set_index("case")
    comparisons = {}
    for p in ("A", "B"):
        names = {"zero": "0", "battery": "battery", "hydrogen": "h2", "joint": "both",
                 "simple20_2023": "simple20"}
        names.update({f"fixed20_{y}": f"fixed20_{y}" for y in range(2022, 2026)})
        for a, b in names.items():
            key = f"{p}_{a}"
            x, y = own[key], cu.loc[f"{p}_{b}"]
            assert (x["nb"], x["nh"]) == (y.n_battery_units, y.n_h2_modules)
            error = abs(x["net"] - y.increment_mGBP) * 1e6
            assert error <= 50.01
            assert abs(x["h2_GWh"] - y.h2_input_GWh) < 0.000051
            comparisons[key] = {"gain": x["net"], "cu_rounded_gain": float(y.increment_mGBP),
                                "gain_abs_diff_GBP": error, "capacity_MW": x["h2_MW"]}

    design = data.loc["2023"]
    sized = {}
    for policy in ("A", "B"):
        for limit in (10000, 50000):
            max_count = math.ceil(limit / (econ.kg_per_gwh * econ.h2_unit))
            rows = []
            for count in range(max_count + 1):
                gain, h, _ = study.hydrogen_enumeration(design, econ, policy, count, econ.netback, limit)
                rows.append(dict(MW=count * 20, gain=gain, h2_input_GWh=float(h.sum()),
                                 capital=count * econ.hydrogen_capex))
            best = max(rows, key=lambda row: row["gain"])
            full = study.solve(design, econ, policy, offtake=limit)[0]
            assert full["nb"] == 0 and full["h2_MW"] == best["MW"]
            assert abs(full["net"] - best["gain"]) < 1e-6
            sized[f"{policy}_{limit}"] = rows
    second_module = study.solve(design, econ, "A", fixed=(0, 2), offtake=10000)[0]
    assert abs(second_module["net"] - sized["A_10000"][2]["gain"]) < 1e-6

    sales_base = own["A_zero"]["baseline_sales_GWh"]
    floor_rows = []
    for ratio in (.9999, 1.):
        x = study.solve(design, econ, "A", service_floor=sales_base * ratio)[0]
        gain = 0. if abs(x["net"]) < 1e-9 else x["net"]
        floor_rows.append(dict(floor_pct=100 * ratio, gain=gain, h2_MW=x["h2_MW"],
                               sales_given_up=x["displacement_GWh"]))
    assert abs(floor_rows[0]["gain"] - 1.0393) < .000051
    schedule = pd.read_csv(V1 / "results/schedules/A_joint.csv", index_col="date", parse_dates=True)
    broad_renewable = cu_data.loc[design.index, "renewable_GWh"]
    upper = float(np.minimum(schedule.capture, broad_renewable).sum())
    lower = float(np.maximum(0, schedule.capture - (design.g - broad_renewable)).sum())
    renewable = dict(broad_lower=lower, broad_upper=upper,
                     narrow_lower=own["A_joint"]["renewable_capture_low_GWh"],
                     narrow_upper=own["A_joint"]["renewable_capture_high_GWh"])

    pool, stock = (own[f"A_battery1_{kind}"] for kind in ("pool", "stock"))
    gross_pool = (pool["direct_change"] + pool["discharge_value"]) * 1e6
    gross_stock = (stock["direct_change"] + stock["discharge_value"]) * 1e6
    cu_commission = .6 * 78.1261430580068
    check = dict(days=len(data), max_input_errors=errors, comparable_cases=comparisons,
                 size_cases=sized, sales_base_GWh=sales_base, floors=floor_rows, renewable=renewable,
                 fixed_40MW_Xpress_gain=second_module["net"],
                 battery=dict(gross_pool_GBP=gross_pool, gross_stock_GBP=gross_stock,
                              cu_annual_commission_GBP=cu_commission,
                              cu_pool_after_commission_GBP=gross_pool - cu_commission,
                              codex_annual_commission_GBP=econ.battery_commission * econ.annuity(econ.battery_life) * 1e6))
    (ROOT / "crosscheck.json").write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
