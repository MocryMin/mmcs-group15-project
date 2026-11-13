"""Replay authentic high-variance GB price windows in the v6 investment model."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
V6 = ROOT.parent / "tier1-multiproduct-20261110-v6"
sys.path.insert(0, str(V6))
import legacy_model
import model
from run_study import reference_assets
from verify_results import check

WINDOWS = (30, 60, 90, 180, 365, 730)
REPLAY_WINDOWS = (60, 90, 180, 365)


def load_frame():
    raw = pd.read_csv(V6 / "results/A_comparable_main_schedule.csv", index_col="date", parse_dates=True)
    data = raw[["generation", "demand", "price"]].rename(columns={"generation": "g", "demand": "d"})
    assert data.index.equals(pd.date_range("2020-01-01", "2025-12-31"))
    return data


def maxima(frame):
    price = frame.price
    baseline_variance = price.var(ddof=0)
    rows = []
    for days in WINDOWS:
        end = price.rolling(days).var(ddof=0).idxmax()
        values = price.loc[:end].tail(days)
        farthest = (values - values.mean()).abs().idxmax()
        rows.append({
            "days": days, "start": str(values.index[0].date()), "end": str(end.date()),
            "mean_GBP2020_MWh": values.mean(), "sd_GBP2020_MWh": values.std(ddof=0),
            "variance_ratio_to_v6": values.var(ddof=0) / baseline_variance,
            "min_GBP2020_MWh": values.min(), "max_GBP2020_MWh": values.max(),
            "sd_without_most_extreme_day": values.drop(farthest).std(ddof=0),
            "most_extreme_date": str(farthest.date()),
        })
    return pd.DataFrame(rows).set_index("days")


def replay(task):
    policy, days, start, end = task
    frame = load_frame().loc[start:end]
    assert len(frame) == days
    model.ROOT = ROOT
    config = json.loads((V6 / "configuration.json").read_text(encoding="utf-8"))
    with_reference = config | {"batteries": reference_assets(config, True)["batteries"]}
    tests = [
        ("zero", config, {}),
        ("joint", config, None),
        ("one_reference", with_reference, {"v5-reference-battery": 1}),
    ]
    solutions = {}
    for label, assets, fixed in tests:
        answer, schedule = model.solve(frame, assets, policy, fixed_battery=fixed, seconds=45,
                                       name=f"{policy}_{days}_{label}")
        assert answer["optimal"], (policy, days, label, answer["status"])
        check(answer, schedule)
        solutions[label] = answer
    base = solutions["zero"]
    joint = solutions["joint"]
    reference = solutions["one_reference"]
    n = next(row for row in reference["investment"] if row["id"] == "v5-reference-battery")
    fixed_cost = n["annual_fixed_GBP"]
    joint_gain = (joint["annual_incremental_profit_mGBP"] - base["annual_incremental_profit_mGBP"]) * 1e6
    reference_gain = (reference["annual_incremental_profit_mGBP"] - base["annual_incremental_profit_mGBP"]) * 1e6
    joint_upper = (joint["upper_profit_bound_mGBP"] - base["annual_incremental_profit_mGBP"]) * 1e6
    if joint["battery_MWh"] == 0:
        assert abs(joint_gain) < .50
    return {
        "policy": policy, "days": days, "start": start, "end": end, "window_year_fraction": base["years"],
        "optimal_battery_MWh": joint["battery_MWh"], "optimal_electrolyser_MW": joint["electrolyser_MW"],
        "no_battery_electrolyser_MW": base["electrolyser_MW"],
        "joint_net_gain_annual_equivalent_GBP2020": max(0., joint_gain),
        "joint_net_gain_upper_annual_equivalent_GBP2020": max(0., joint_upper),
        "reference_increment_before_battery_cost_annual_equivalent_GBP2020": reference_gain + fixed_cost,
        "reference_annual_cost_GBP2020": fixed_cost,
        "reference_increment_before_battery_cost_window_GBP2020": (reference_gain + fixed_cost) * base["years"],
        "reference_cost_prorated_window_GBP2020": fixed_cost * base["years"],
        "reference_net_gain_window_GBP2020": reference_gain * base["years"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    (ROOT / "results").mkdir(exist_ok=True)
    metrics = maxima(load_frame())
    metrics.to_csv(ROOT / "window-variance.csv")
    jobs = [(policy, days, metrics.loc[days, "start"], metrics.loc[days, "end"])
            for days in REPLAY_WINDOWS for policy in "AB"]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        result = pd.DataFrame(pool.map(replay, jobs))
    assert len(result) == len(jobs)
    assert np.isfinite(result.select_dtypes("number")).all().all()
    result.to_csv(ROOT / "replay-summary.csv", index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
