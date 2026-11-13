"""Co-optimize paid batteries and electrolysers over independent stress factors."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tier1-volatility-20261111"))
from sweep import scenario

CASES = ROOT / "cases"
GAP_GRID = (1., 1.025, 1.05, 1.1, 1.25, 1.5, 2., 4., 8.)
PRICE_GRID = (1., 16., 32., 40., 64., 80., 100., 120., 127., 150.)


def job(policy, gap, price, seconds, threads, bound_capacity):
    target = CASES / f"{policy}_joint_{price:.8g}_gap{gap:.10g}.json"
    old = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    incumbent_profit = old["no_battery_annual_profit_GBP"] + old["objective_lower_GBP"] if old and bound_capacity else None
    row = scenario(policy, "joint", price, seconds, threads, gap_factor=gap, case_directory=CASES,
                   incumbent_profit=incumbent_profit)
    if old is None:
        return row

    def absolute(case, field):
        return case["no_battery_annual_profit_GBP"] + case[field]

    incumbent = max((old, row), key=lambda x: absolute(x, "objective_lower_GBP"))
    zero = max((old, row), key=lambda x: x["no_battery_annual_profit_GBP"])
    no_battery = zero["no_battery_annual_profit_GBP"]
    zero_upper = min(absolute(old, "zero_upper_minus_feasible_GBP"),
                     absolute(row, "zero_upper_minus_feasible_GBP"))
    lower = max(no_battery, absolute(incumbent, "objective_lower_GBP"))
    supplied_upper = [absolute(case, "objective_upper_GBP") for case in (old, row)]
    consistent = [bound for bound in supplied_upper if lower <= bound + .05]
    assert consistent, (policy, gap, price, lower, supplied_upper)
    upper = min(consistent)
    decision = ("positive" if lower > max(no_battery, zero_upper) + .5 else
                "zero_within_50p" if upper < no_battery + .5 and incumbent["battery_MWh"] == 0 else
                "unresolved")
    merged = incumbent | dict(
        objective_lower_GBP=lower - no_battery, objective_upper_GBP=max(lower, upper) - no_battery,
        no_battery_annual_profit_GBP=no_battery, zero_upper_minus_feasible_GBP=max(0, zero_upper-no_battery),
        no_battery_electrolyser_counts=zero["no_battery_electrolyser_counts"],
        no_battery_electrolyser_MW=zero["no_battery_electrolyser_MW"], decision=decision)
    if len(consistent) < len(supplied_upper):
        merged["discarded_inconsistent_annual_profit_upper_GBP"] = min(supplied_upper)
    target.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gaps", type=float, nargs="+", default=GAP_GRID)
    parser.add_argument("--prices", type=float, nargs="+", default=PRICE_GRID)
    parser.add_argument("--policy", default="AB")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=32)
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--bound-capacity", action="store_true")
    args = parser.parse_args()
    CASES.mkdir(exist_ok=True)
    keys = [(policy, gap, price) for price in args.prices for gap in args.gaps for policy in args.policy]
    pending = []
    for policy, gap, price in keys:
        target = CASES / f"{policy}_joint_{price:.8g}_gap{gap:.10g}.json"
        if target.exists():
            if not args.refine:
                continue
            old = json.loads(target.read_text(encoding="utf-8"))
            if old["decision"] != "unresolved" and old["objective_upper_GBP"] - old["objective_lower_GBP"] < 20:
                continue
        pending.append((policy, gap, price))
    print(f"Solving {len(pending)} of {len(keys)} cases.", flush=True)
    failures = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(job, *case, args.seconds, args.threads, args.bound_capacity): case for case in pending}
        for n, future in enumerate(as_completed(futures), 1):
            case = futures[future]
            try:
                row = future.result()
                print(f"{n}/{len(pending)} {case} {row['decision']} "
                      f"{row['battery_MWh']:.3f} MWh "
                      f"[{row['objective_lower_GBP']:.2f}, {row['objective_upper_GBP']:.2f}] GBP/y "
                      f"{row['elapsed_seconds']:.1f}s", flush=True)
            except Exception as error:
                failures.append(case)
                print(f"{case}: {error!r}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} cases failed: {failures}")


if __name__ == "__main__":
    main()
