"""Find the netback at which some nonzero electrolysis capacity pays."""

from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pandas as pd

ROOT = Path(__file__).resolve().parent
V6 = ROOT.parent / "tier1-multiproduct-20261110-v6"
sys.path.insert(0, str(V6))
import model


def threshold(case):
    policy, cap, scratch = case
    config = json.loads((V6 / "configuration.json").read_text(encoding="utf-8"))
    frame = pd.read_csv(V6 / "results/A_comparable_main_schedule.csv", index_col="date", parse_dates=True)
    frame = frame.rename(columns={"generation": "g", "demand": "d"})
    model.ROOT = Path(scratch) / f"{policy}-{cap:g}"
    (model.ROOT / "results").mkdir(exist_ok=True, parents=True)
    lo, hi = 0., config["netback"]
    history = []
    while hi - lo > .005:
        value = (lo + hi) / 2
        result, _ = model.solve(frame, config | {"netback": value}, policy,
                                cap=cap, fixed_battery={}, name=f"netback-{value:.8f}")
        bound = result["upper_profit_bound_mGBP"] * 1e6
        gain = result["annual_incremental_profit_mGBP"] * 1e6
        assert result["optimal"]
        history.append({"price": value, "gain_GBP_year": gain, "upper_GBP_year": bound,
                        "electrolyser_MW": result["electrolyser_MW"]})
        if gain > .05:
            hi = value
        else:
            assert bound <= .05
            lo = value
    return dict(policy=policy, cap_kg_day=cap, no_positive_gain_at=lo, positive_gain_at=hi, evaluations=history)


if __name__ == "__main__":
    with TemporaryDirectory(prefix="mmcs-contract-") as scratch:
        cases = [(p, cap, scratch) for p in "AB" for cap in (1558.9687748333345, 10000.)]
        with ProcessPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(threshold, cases))
    (ROOT / "contract-thresholds.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for item in results:
        print({key: value for key, value in item.items() if key != "evaluations"})
