"""Reproduce the Tier 2B fixed-site, zero-storage offtake replay."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys

from highspy import Highs, HighsModelStatus
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, eye, hstack, vstack


SLOTS = 48
DAILY_CAP_KG = 10_000.0
TRAIN_END = "2023-01-01"
TEST_END = "2026-01-01"
EPS = 1e-7
RULES = ("pace", "greedy", "rolling", "perfect")
V5_COUNTS = {"A": 8, "B": 11}
SOURCE_FILES = {
    "inputs/halfhour.csv.gz": "890ee68ae2014caa96f2e63e9c07ef14c37112799d5d5f97a16989da3294b4ae",
    "configuration.json": "0b15ef3cd7d1597028231471e264cf57a03b38a624dd5564a911aafa3de7f7a9",
    "model.py": "2cea30902eebdd9d0c2ed18666fdff894b9c92925651370b79da69f51d140bd5",
}


@dataclass(frozen=True)
class Equipment:
    module_mw: float
    minimum_mwh: float
    mwh_per_kg: float
    annual_gbp: float
    netback: float

    @property
    def daily_quota(self):
        return DAILY_CAP_KG * self.mwh_per_kg

    @property
    def value(self):
        return self.netback / self.mwh_per_kg


def load_inputs(source):
    for name, checksum in SOURCE_FILES.items():
        if sha256((source / name).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Unexpected Tier 1 v7 source: {name}")
    sys.path.insert(0, str(source))
    sys.dont_write_bytecode = True
    from model import annual_costs, frame_for

    config = json.loads((source / "configuration.json").read_text())
    _, electrolysers = annual_costs(config)
    module = next(h for h in electrolysers if h["id"] == "itm-neptune-v")
    assert config["dt_hours"] == 0.5 and module["variable_GBP_kg"] == 0
    plant = Equipment(
        module["MW"], module["MW"] * 0.5 * module["minimum"],
        module["kWh_kg"] / 1000, module["annual"] * 1e6, config["netback"],
    )
    frame = frame_for("2020-01-01", "2025-12-31")
    expected = pd.date_range("2020-01-01", TEST_END, freq="30min", inclusive="left", tz="UTC")
    assert frame.index.equals(expected)
    actual = frame[["g", "d", "price"]].to_numpy() * np.array([1000.0, 1000.0, 1.0])
    assert np.isfinite(actual).all() and (actual[:, :2] >= 0).all()
    return frame.index, actual, plant


def slot_bands(actual, policy, count, plant):
    generation, demand, price = actual.T
    surplus = np.maximum(generation - demand, 0)
    if policy == "A":
        free = np.where(price >= 0, surplus, generation)
        upper = generation
        opportunity_price = price.clip(min=0)
    else:
        free = upper = surplus
        opportunity_price = np.zeros_like(price)
    upper = np.minimum(upper, count * plant.module_mw * 0.5)
    upper[upper < plant.minimum_mwh] = 0
    return np.minimum(free, upper), opportunity_price, upper


def allocation(free, price, upper, quota, value):
    """Julian's lowest-cost-first knapsack with half-hour free and paid bands."""
    benefit = np.concatenate((np.full_like(free, value), value - price), axis=-1)
    capacity = np.concatenate((free, upper - free), axis=-1)
    order = np.argsort(-benefit, axis=-1, kind="stable")
    cap = np.take_along_axis(capacity, order, axis=-1)
    cap = np.where(np.take_along_axis(benefit, order, axis=-1) > 0, cap, 0)
    steps_before = np.cumsum(cap, axis=-1) - cap
    amount = np.empty_like(cap)
    np.put_along_axis(amount, order, np.minimum(np.maximum(quota - steps_before, 0), cap), axis=-1)
    length = free.shape[-1]
    return amount[..., :length] + amount[..., length:]


def contribution(load, free, price, value):
    return load * value - np.maximum(load - free, 0) * price


def exact_repair(free, price, upper, quota, plant, seed):
    """Generalise the Tier 1 daily min-load repair to one contract window."""
    n = len(free)
    ident = eye(n, format="csr")
    zero = csr_matrix((n, n))
    sum_load = csr_matrix((np.ones(n), (np.zeros(n, dtype=int), np.arange(n))), shape=(1, 3 * n))
    matrix = vstack((
        hstack((ident, -ident, zero)),
        hstack((ident, zero, -ident.multiply(upper[:, None]))),
        hstack((-ident, zero, plant.minimum_mwh * ident)),
        sum_load,
    )).tocsr()
    solver = Highs()
    solver.silent()
    solver.setOptionValue("threads", 1)
    solver.setOptionValue("mip_rel_gap", 1e-10)
    solver.setOptionValue("mip_abs_gap", 1e-6)
    rhs = np.r_[free, np.zeros(2 * n), quota]
    empty_indices = np.array([], dtype=np.int32)
    solver.addCols(
        3 * n, np.r_[np.full(n, -plant.value), price, np.zeros(n)],
        np.zeros(3 * n), np.r_[upper, upper, (upper > 0).astype(float)],
        0, empty_indices, empty_indices, np.array([]),
    )
    solver.addRows(
        len(rhs), np.full(len(rhs), -np.inf), rhs, matrix.nnz,
        matrix.indptr.astype(np.int32), matrix.indices.astype(np.int32), matrix.data,
    )
    solver.changeColsIntegrality(n, np.arange(2 * n, 3 * n, dtype=np.int32), np.ones(n, dtype=np.uint8))
    seed = np.where(seed >= plant.minimum_mwh - EPS, seed, 0.0)
    solver.setSolution(
        3 * n, np.arange(3 * n, dtype=np.int32),
        np.r_[seed, np.maximum(seed - free, 0), (seed > EPS).astype(float)],
    )
    solver.run()
    if solver.getModelStatus() != HighsModelStatus.kOptimal:
        raise RuntimeError(f"Minimum-load repair failed: {solver.getModelStatus()}")
    load = np.array(solver.getSolution().col_value[:n]).clip(min=0)
    return np.where(load > EPS, load, 0.0)


def optimise_windows(free, price, upper, quota, plant):
    load = allocation(free, price, upper, quota, plant.value)
    repair = np.flatnonzero(np.any((load > EPS) & (load < plant.minimum_mwh - EPS), axis=1))
    for row in repair:
        load[row] = exact_repair(free[row], price[row], upper[row], quota, plant, load[row])
    return load, len(repair)


def size_equipment(train, plant):
    """Discard capacities whose continuous upper bound cannot improve investment."""
    years = 3
    max_modules = int(len(train) / SLOTS * DAILY_CAP_KG * plant.netback / (years * plant.annual_gbp))
    evidence = []
    selected = {}
    for policy in "AB":
        relaxed = {}
        for count in range(max_modules + 1):
            bands = tuple(x.reshape(-1, SLOTS) for x in slot_bands(train, policy, count, plant))
            load = allocation(*bands, plant.daily_quota, plant.value)
            gross = contribution(load, *bands[:2], plant.value).sum() / years
            relaxed[count] = gross - count * plant.annual_gbp
        best = -np.inf
        for count in sorted(relaxed, key=relaxed.get, reverse=True):
            net, repairs = None, None
            if relaxed[count] >= best - 1e-5 or count == V5_COUNTS[policy]:
                bands = tuple(x.reshape(-1, SLOTS) for x in slot_bands(train, policy, count, plant))
                load, repairs = optimise_windows(*bands, plant.daily_quota, plant)
                net = contribution(load, *bands[:2], plant.value).sum() / years - count * plant.annual_gbp
                assert net <= relaxed[count] + 1e-5
                if net > best + 1e-5:
                    selected[policy], best = count, net
            evidence.append(dict(
                policy=policy, modules=count, mw=count * plant.module_mw,
                relaxed_upper_gbp_per_year=relaxed[count], exact_gbp_per_year=net,
                windows_repaired=repairs,
            ))
        print(f"Pre-test design {policy}: {selected[policy]} modules, £{best:,.0f}/year", flush=True)
    table = pd.DataFrame(evidence).sort_values(["policy", "modules"])
    table["selected"] = table["modules"].eq(table["policy"].map(selected))
    return selected, table


def seasonal_history(actual):
    """Four same-weekday/same-slot analogues for each target."""
    seasonal = np.zeros_like(actual)
    week = 7 * SLOTS
    for offset in (week, 2 * week, 3 * week, 4 * week):
        seasonal[4 * week:] += actual[4 * week - offset:len(actual) - offset] / 4
    return seasonal


def windows(start, end, days):
    """Anchor W-day blocks at the start of the held-out period (Julian convention)."""
    return [(first, min(first + days * SLOTS, end)) for first in range(start, end, days * SLOTS)]


def forecast_path(seasonal, previous, current, end):
    # The latest observed deviation from the same-slot average decays with a
    # 2-hour half-life. No future target is a full week away from issuance.
    assert 0 < end - current <= 7 * SLOTS
    weights = np.exp2(-np.arange(end - current) / 4)[:, None]
    predicted = seasonal[current:end] + weights * (previous - seasonal[current - 1])
    predicted[:, :2] = predicted[:, :2].clip(min=0)
    return predicted


def replay_window(actual, seasonal, start, end, policy, count, plant, rule):
    quota = plant.daily_quota * ((end - start) / SLOTS)
    free, price, upper = slot_bands(actual[start:end], policy, count, plant)
    if rule == "perfect":
        solved, repairs = optimise_windows(free[None, :], price[None, :], upper[None, :], quota, plant)
        return solved[0], solved[0], repairs

    request = np.zeros(end - start)
    load = np.zeros(end - start)
    left, day_left, repairs = quota, plant.daily_quota, 0
    for i, t in enumerate(range(start, end)):
        if i % SLOTS == 0:
            day_left = plant.daily_quota
        budget = min(left, day_left) if rule == "pace" else left
        if budget < plant.minimum_mwh - EPS:
            continue
        if policy == "B" and rule in ("pace", "greedy"):
            # Request up to the plant limit. A physical interlock admits only
            # power that remains after serving actual demand.
            desired = min(count * plant.module_mw * 0.5, budget)
        elif rule in ("pace", "greedy"):
            predicted = forecast_path(seasonal, actual[t - 1], t, t + 1)
            f, p, u = slot_bands(predicted, policy, count, plant)
            desired = min(budget, u[0] if p[0] < plant.value else f[0])
        else:
            predicted = forecast_path(seasonal, actual[t - 1], t, end)
            bands = tuple(col[None, :] for col in slot_bands(predicted, policy, count, plant))
            planned, repaired = optimise_windows(*bands, budget, plant)
            desired = planned[0, 0]
            repairs += repaired
        request[i] = desired if desired >= plant.minimum_mwh - EPS else 0.0
        executed = min(request[i], upper[i])
        load[i] = executed if executed >= plant.minimum_mwh - EPS else 0.0
        left = max(0.0, left - load[i])
        day_left = max(0.0, day_left - load[i])
    return request, load, repairs


def verify_window(request, load, upper, quota, plant):
    if not (
        (load >= -EPS).all()
        and (load <= upper + EPS).all()
        and (load <= request + EPS).all()
        and ((load <= EPS) | (load >= plant.minimum_mwh - EPS)).all()
        and load.sum() <= quota + EPS
    ):
        raise AssertionError("Energy, request, minimum-load or offtake constraint failed")


def replay(index, actual, plant, designs):
    seasonal = seasonal_history(actual)
    start = index.get_loc(pd.Timestamp(TRAIN_END, tz="UTC"))
    # Alter the current and all future actuals. Dispatch requests issued at the
    # first test slot must not change, though their physical execution can.
    alternate = actual.copy()
    alternate[start:] *= 0.2
    seasonal_alternate = seasonal_history(alternate)
    for policy in "AB":
        for rule in RULES[:-1]:
            args = (start, start + SLOTS * 7, policy, designs["pre_test"][policy], plant, rule)
            original = replay_window(actual, seasonal, *args)[0][0]
            changed = replay_window(alternate, seasonal_alternate, *args)[0][0]
            assert original == changed, (policy, rule)

    periods, day_rows = [], []
    for design, counts in designs.items():
        for policy, count in counts.items():
            for days in (1, 7):
                print(f"Replay {design}, policy {policy}, {days}-day", flush=True)
                for first, end in windows(start, len(index), days):
                    free, price, upper = slot_bands(actual[first:end], policy, count, plant)
                    quota = plant.daily_quota * ((end - first) / SLOTS)
                    cash_by_rule = {}
                    day_index = index[first:end:SLOTS]
                    for rule in RULES:
                        request, load, repairs = replay_window(
                            actual, seasonal, first, end, policy, count, plant, rule
                        )
                        verify_window(request, load, upper, quota, plant)
                        h2 = load / plant.mwh_per_kg
                        opportunity = np.maximum(load - free, 0) * price
                        cash = contribution(load, free, price, plant.value)
                        assert np.allclose(cash, h2 * plant.netback - opportunity, atol=1e-9)
                        cash_by_rule[rule] = cash.sum()
                        case = dict(design=design, policy=policy, modules=count, window_days=days, rule=rule)
                        periods.append(dict(
                            **case, start_date=str(index[first].date()), end_date=str(day_index[-1].date()),
                            days=len(day_index), cap_kg=quota / plant.mwh_per_kg,
                            hydrogen_kg=h2.sum(), expired_quota_kg=max(0, (quota - load.sum()) / plant.mwh_per_kg),
                            operating_gain_gbp=cash.sum(), foregone_sales_gbp=opportunity.sum(),
                            electrolyser_mwh=load.sum(), clipped_request_mwh=(request - load).sum(),
                            min_load_repairs=repairs,
                        ))
                        for date, mass, gain in zip(
                            day_index, h2.reshape(-1, SLOTS).sum(axis=1), cash.reshape(-1, SLOTS).sum(axis=1)
                        ):
                            fraction = 1 / (366 if date.is_leap_year else 365)
                            day_rows.append(dict(
                                **case, year=date.year, year_fraction=fraction, hydrogen_kg=mass,
                                operating_gain_gbp=gain, annual_cost_gbp=count * plant.annual_gbp * fraction,
                            ))
                    assert all(cash_by_rule["perfect"] + 1e-5 >= cash for cash in cash_by_rule.values())
    return pd.DataFrame(periods), pd.DataFrame(day_rows)


def summary(periods, day_rows):
    keys = ["design", "policy", "modules", "window_days", "rule"]
    annual = day_rows.groupby(keys + ["year"], as_index=False).sum(numeric_only=True)
    annual["net_gain_gbp"] = annual["operating_gain_gbp"] - annual["annual_cost_gbp"]
    pooled = annual.groupby(keys, as_index=False).agg(
        years=("year_fraction", "sum"), gross=("operating_gain_gbp", "sum"),
        cost=("annual_cost_gbp", "sum"), hydrogen=("hydrogen_kg", "sum"),
    )
    pooled["annual_operating_gain_gbp"] = pooled.pop("gross") / pooled["years"]
    pooled["annual_fixed_cost_gbp"] = pooled.pop("cost") / pooled["years"]
    pooled["annual_net_gain_gbp"] = pooled["annual_operating_gain_gbp"] - pooled["annual_fixed_cost_gbp"]
    pooled["annual_hydrogen_kg"] = pooled.pop("hydrogen") / pooled["years"]
    cap = periods.assign(near_cap=periods["hydrogen_kg"].ge(0.95 * periods["cap_kg"]))
    cap = cap.groupby(keys, as_index=False).agg(
        windows=("days", "size"), cap_kg=("cap_kg", "sum"),
        hydrogen_kg=("hydrogen_kg", "sum"), near_cap=("near_cap", "mean"),
    )
    pooled = pooled.merge(cap, on=keys, validate="one_to_one")
    assert np.allclose(pooled["hydrogen_kg"], pooled["annual_hydrogen_kg"] * pooled["years"], atol=1e-5)
    pooled["quota_used_pct"] = 100 * pooled.pop("hydrogen_kg") / pooled.pop("cap_kg")
    pooled["windows_at_least_95pct_pct"] = 100 * pooled.pop("near_cap")
    paired_keys = ["design", "policy", "modules", "window_days"]
    greedy = pooled[pooled["rule"].eq("greedy")].set_index(paired_keys)["annual_net_gain_gbp"]
    paired = pooled.set_index(paired_keys)
    paired["gain_vs_greedy_gbp_per_year"] = paired["annual_net_gain_gbp"] - greedy
    return annual, paired.reset_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, required=True, help="Frozen v7 input/model directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index, actual, plant = load_inputs(args.study_dir.resolve())
    start = index.get_loc(pd.Timestamp(TRAIN_END, tz="UTC"))
    selected, sizing = size_equipment(actual[:start], plant)
    designs = {"pre_test": selected}
    if selected != V5_COUNTS:
        designs["v5_appraisal"] = V5_COUNTS
    periods, day_rows = replay(index, actual, plant, designs)
    annual, pooled = summary(periods, day_rows)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, table in (("train_sizing", sizing), ("summary", pooled),
                        ("annual", annual), ("contract_windows", periods)):
        table.to_csv(args.output / f"{name}.csv", index=False, float_format="%.9f")
    assumptions = {
        "training_utc": ["2020-01-01", TRAIN_END],
        "test_utc": [TRAIN_END, TEST_END],
        "end_dates_exclusive": True,
        "input_sha256": SOURCE_FILES,
        "input_reference": "b0377299dc452bf01f387c0dd60f6e7f6510e1a2",
        "half_hour_slots": len(index) - start,
        "designs": designs,
        "battery_mw": 0,
        "battery_mwh": 0,
        "hydrogen_inventory_kg": 0,
        "daily_equivalent_acceptance_kg": DAILY_CAP_KG,
        "currency": "GBP2020",
        "equipment": vars(plant),
        "checks": {
            "verified_windows": len(periods),
            "min_load_repairs_by_rule": periods.groupby("rule")["min_load_repairs"].sum().to_dict(),
            "matched_request_and_physical_limits": True,
            "first_issue_unchanged_when_future_actuals_perturbed": True,
            "perfect_dominates_all_other_rules_each_window": True,
        },
    }
    (args.output / "audit.json").write_text(json.dumps(assumptions, indent=2) + "\n")
    print(pooled[["design", "policy", "window_days", "rule", "annual_net_gain_gbp", "quota_used_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
