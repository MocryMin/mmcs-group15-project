"""Historical operating-value ceiling for fixed v6 electrolysers and H2 storage."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import diags, eye, hstack, vstack


HERE = Path(__file__).resolve().parent
V6 = HERE.parent / "tier1-multiproduct-20261110-v6"
TANK = HERE.parent / "hydrogen-storage-research-20261111" / "MODEL_INPUTS.json"
HYDROGEN_LHV = 33.33
FUEL_CELL_MW_PER_MODULE = 0.25


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def operate(schedule, devices, config, tank, policy, modules, efficiency):
    """Electricity in GWh, hydrogen in tonnes, objective in thousand GBP2020."""
    n = len(schedule)
    generation, demand, price = schedule[["generation", "demand", "price"]].to_numpy().T
    netback = config["netback"]
    offtake = config["cap_kg_day"] / 1000
    inventory = tank["technology"]["usable_capacity_kg"] * modules / 1000
    max_injection = tank["technology"]["charge_limit_kg_day"] * modules / 1000
    compression = tank["variable_costs"]["charging_kWh_per_kg"] / 1000
    power_per_tonne = HYDROGEN_LHV * efficiency / 1000
    max_hydrogen_for_power = (
        FUEL_CELL_MW_PER_MODULE * modules * 24 / (HYDROGEN_LHV * efficiency)
        if efficiency else 0.0
    )

    names = ["direct", "direct_h2", "injected", "released", "fuel", "stock"]
    names += [item["id"] for item in devices]
    identity = eye(n, format="csr")
    previous = diags([np.ones(n - 1)], [-1], shape=(n, n), format="csr")

    def row(terms):
        return hstack([
            coefficient * identity if np.isscalar(coefficient) else coefficient
            for coefficient in (terms.get(name, 0) for name in names)
        ], format="csr")

    energy_inputs = {item["id"]: item["kWh_kg"] / 1000 for item in devices}
    limits = vstack([
        row(dict(direct=1, injected=compression, **energy_inputs)),
        row(dict(direct=1, fuel=power_per_tonne)),
        row(dict(direct_h2=1, released=1)),
        row(dict(released=1, fuel=1, stock=-previous)),
    ], format="csr")
    limits_rhs = np.concatenate([generation, demand, np.full(n, offtake), np.zeros(n)])
    balance = vstack([
        row(dict(direct_h2=1, injected=1, **{item["id"]: -1 for item in devices})),
        row(dict(stock=identity - previous, injected=-1, released=1, fuel=1)),
    ], format="csr")
    bounds_direct = (
        [(q, q) for q in np.minimum(generation, demand)] if policy == "B" else [(0, None)] * n
    )
    bounds = bounds_direct + [(0, offtake)] * n + [(0, max_injection)] * n
    bounds += [(0, inventory)] * n + [(0, max_hydrogen_for_power)] * n
    bounds += [(0, inventory)] * (n - 1) + [(0, 0)]
    for item in devices:
        max_tonnes = item["physical_MW"] * item["count"] * 24 / item["kWh_kg"]
        bounds.extend([(0, max_tonnes)] * n)

    revenue = np.zeros((len(names), n))
    revenue[0] = price
    revenue[1] = netback
    revenue[3] = netback
    revenue[4] = price * power_per_tonne
    result = linprog(-revenue.ravel(), A_ub=limits, b_ub=limits_rhs,
                     A_eq=balance, b_eq=np.zeros(2 * n), bounds=bounds, method="highs")
    assert result.success, result.message
    flows = dict(zip(names, result.x.reshape(len(names), n)))
    error = max(float(np.max(limits @ result.x - limits_rhs)),
                float(np.max(np.abs(balance @ result.x))))
    assert error < 1e-7
    assert abs(flows["stock"][-1]) < 1e-8
    return {
        "receipts_GBP_year": -result.fun * 1000 / 6,
        "outlet_tonnes_year": float(flows["released"].sum() / 6),
        "fuel_cell_MWh_year": float(flows["fuel"].sum() * power_per_tonne * 1000 / 6),
        "stock_tonnes_peak": float(flows["stock"].max()),
        "max_balance_residual": error,
    }


def main():
    config = read_json(V6 / "configuration.json")
    tank = read_json(TANK)
    catalogue = {item["id"]: item for item in config["electrolysers"]}
    tank_fixed = tank["fixed_maintenance_GBP2020_per_module_year"]["annual_capital_and_fixed_maintenance"]
    diagnostics = {}
    rows = []
    for policy in "AB":
        name = f"{policy}_comparable_main"
        plan = read_json(V6 / "results" / f"{name}.json")
        schedule = pd.read_csv(V6 / "results" / f"{name}_schedule.csv")
        assert len(schedule) == 2192
        assert schedule.date.iloc[0] == "2020-01-01" and schedule.date.iloc[-1] == "2025-12-31"
        assert plan["battery_MWh"] == 0 and plan["annual_variable_stack_reserve_mGBP"] == 0
        devices = [
            dict(item, kWh_kg=catalogue[item["id"]]["kWh_kg"])
            for item in plan["investment"] if item["kind"] == "electrolyser" and item["count"] > 0
        ]
        baseline = plan["annual_operating_receipts_mGBP"] * 1e6
        relaxed_zero = operate(schedule, devices, config, tank, policy, 0, 0.0)
        diagnostics[policy] = {
            "zero_relaxation_gap_GBP_year": relaxed_zero["receipts_GBP_year"] - baseline,
            "h2_cap_days": int((schedule.h2_kg >= config["cap_kg_day"] - 0.05).sum()),
            "unused_days": int((schedule.unused > 0.001).sum()),
            "mean_annual_unused_GWh": float(schedule.unused.sum() / 6),
            "max_price_GBP_MWh": float(schedule.price.max()),
            "above_direct_h2_equivalent": {},
        }
        for efficiency in (0.5, 0.6):
            threshold = config["netback"] * 1000 / (HYDROGEN_LHV * efficiency)
            high = schedule.price > threshold
            diagnostics[policy]["above_direct_h2_equivalent"][str(efficiency)] = {
                "threshold_GBP_MWh": threshold,
                "days": int(high.sum()),
                "days_with_demand_headroom_in_v6": int((high & (schedule.unserved > 0.001)).sum()),
            }
        for modules in (1, 100):
            for efficiency in (0.0, 0.5, 0.6):
                result = operate(schedule, devices, config, tank, policy, modules, efficiency)
                gain = result["receipts_GBP_year"] - baseline
                fixed = tank_fixed * modules
                rows.append(dict(policy=policy, modules=modules, efficiency_LHV=efficiency,
                                 usable_tonnes=modules * tank["technology"]["usable_capacity_kg"] / 1000,
                                 fuel_cell_MW=modules * FUEL_CELL_MW_PER_MODULE if efficiency else 0.0,
                                 upper_gain_GBP_year=gain,
                                 tank_cost_GBP_year=fixed,
                                 upper_after_tank_before_fuel_cell_GBP_year=gain - fixed,
                                 **result))
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "screen_results.csv", index=False, float_format="%.9f")
    (HERE / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diagnostics, indent=2))
    print(table[["policy", "modules", "efficiency_LHV", "upper_gain_GBP_year",
                 "upper_after_tank_before_fuel_cell_GBP_year", "outlet_tonnes_year",
                 "fuel_cell_MWh_year"]].to_string(index=False))


if __name__ == "__main__":
    main()
