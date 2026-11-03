#!/usr/bin/env python3
"""Controller-side independent check of mocry-codex's 107-day generation repair release.

Does NOT import their verify_repair.py. Rebuilds every comparison from the pinned
course files and their published CSVs, then reports differences.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
DISPATCHABLE = {"Fossil Gas", "Fossil Hard coal", "Fossil Oil", "Nuclear", "Biomass",
                "Hydro Run-of-river and poundage", "Hydro Pumped Storage", "Other"}
RENEWABLE = {"Wind Onshore", "Wind Offshore", "Solar"}


def rows(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def fuel_map(path: Path):
    out: dict[str, dict[str, float]] = {}
    for r in rows(path):
        out.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
    return out


def total_map(path: Path):
    return {r["date"]: float(r["total_MW"]) for r in rows(path)}


def col_map(path: Path, key: str, val: str):
    return {r[key][:10]: float(r[val]) for r in rows(path)}


orig_fuel = fuel_map(REPO / "daily_generation_by_fuel.csv")
rep_fuel = fuel_map(REL / "daily_generation_by_fuel.csv")
orig_total = total_map(REPO / "daily_generation_total.csv")
rep_total = total_map(REL / "daily_generation_total.csv")
demand = col_map(REPO / "daily_demand.csv", "startTime", "demand")
wind = col_map(REPO / "wind_farm_generation.csv", "date", "wind_farm_MW")
price = col_map(REPO / "daily_market_index_price.csv", "date", "avg_price_\u00a3_per_MWh")

res: dict[str, object] = {}

res["date_keys"] = {
    "orig_fuel": len(orig_fuel), "rep_fuel": len(rep_fuel),
    "orig_total": len(orig_total), "rep_total": len(rep_total),
    "same_fuel_keys": set(orig_fuel) == set(rep_fuel),
    "same_total_keys": set(orig_total) == set(rep_total),
}

# my earlier definition of the artifact
my_zero = sorted(d for d, mix in orig_fuel.items()
                 if mix and all(mix.get(f, 0.0) == 0.0 for f in DISPATCHABLE))

changed_dates = sorted(d for d in rep_total if d in orig_total and rep_total[d] != orig_total[d])
changed_fuel = sorted(d for d in rep_fuel if d in orig_fuel and rep_fuel[d] != orig_fuel[d])
res["changed"] = {
    "total_changed_count": len(changed_dates),
    "fuel_changed_count": len(changed_fuel),
    "same_sets": set(changed_dates) == set(my_zero),
    "only_in_repair": sorted(set(changed_dates) - set(my_zero))[:10],
    "only_in_mine": sorted(set(my_zero) - set(changed_dates))[:10],
    "changed_fuel_minus_total": sorted(set(changed_fuel) ^ set(changed_dates))[:10],
}

# unchanged dates must be byte-identical in values
unchanged_mismatch = [d for d in orig_total if d in rep_total and d not in set(changed_dates)
                      and rep_total[d] != orig_total[d]]
res["unchanged_rows_identical"] = not unchanged_mismatch

# per-fuel internal consistency of repaired table
sum_gap = []
for d, mix in rep_fuel.items():
    if d in rep_total:
        s = sum(mix.values())
        if abs(s - rep_total[d]) > 0.51:
            sum_gap.append((d, round(s, 2), rep_total[d]))
res["repair_fuel_sum_vs_total_mismatches"] = {"count": len(sum_gap), "examples": sum_gap[:5]}

# renewables must be untouched on repaired dates
ren_changed = []
for d in changed_dates:
    if d not in orig_fuel:
        continue
    for f in RENEWABLE:
        if abs(orig_fuel[d].get(f, 0.0) - rep_fuel[d].get(f, 0.0)) > 1e-9:
            ren_changed.append((d, f, orig_fuel[d].get(f), rep_fuel[d].get(f)))
res["renewables_changed_on_repaired_dates"] = {"count": len(ren_changed), "examples": ren_changed[:5]}

common = sorted(set(demand) & set(orig_total) & set(wind) & set(price))
common_rep = sorted(set(demand) & set(rep_total) & set(wind) & set(price))


def surplus_deficit(total, days):
    s = sum(max(0.0, (total[d] + wind[d]) - demand[d]) * 24 for d in days)
    df = sum(max(0.0, demand[d] - (total[d] + wind[d])) * 24 for d in days)
    return round(s / 1e6, 2), round(df / 1e6, 2)  # TWh


s0, d0 = surplus_deficit(orig_total, common)
s1, d1 = surplus_deficit(rep_total, common_rep)
keep = [d for d in common if d not in set(my_zero) and d != "2022-08-02"]
s2, d2 = surplus_deficit(orig_total, keep)
res["totals_TWh"] = {
    "common_days": len(common),
    "original": {"surplus": s0, "deficit": d0},
    "repaired": {"surplus": s1, "deficit": d1},
    "original_minus_107_and_2022_08_02(keep=%d)" % len(keep): {"surplus": s2, "deficit": d2},
}

# what the repair does day by day on the 107 dates
per_day = []
for d in my_zero:
    if d not in common:
        continue
    b = (orig_total[d] + wind[d]) - demand[d]
    a = (rep_total[d] + wind[d]) - demand[d]
    per_day.append({"date": d, "demand_MW": demand[d], "orig_gen_MW": orig_total[d],
                    "rep_gen_MW": rep_total[d], "orig_bal_TWh": round(b * 24 / 1e6, 4),
                    "rep_bal_TWh": round(a * 24 / 1e6, 4)})
res["repaired_day_balance"] = {
    "days_in_common": len(per_day),
    "orig_deficit_TWh": round(sum(-x["orig_bal_TWh"] for x in per_day if x["orig_bal_TWh"] < 0), 2),
    "orig_surplus_TWh": round(sum(x["orig_bal_TWh"] for x in per_day if x["orig_bal_TWh"] > 0), 2),
    "rep_deficit_TWh": round(sum(-x["rep_bal_TWh"] for x in per_day if x["rep_bal_TWh"] < 0), 2),
    "rep_surplus_TWh": round(sum(x["rep_bal_TWh"] for x in per_day if x["rep_bal_TWh"] > 0), 2),
    "rep_gen_vs_demand_ratio_min": round(min(x["rep_gen_MW"] / x["demand_MW"] for x in per_day), 3),
    "rep_gen_vs_demand_ratio_max": round(max(x["rep_gen_MW"] / x["demand_MW"] for x in per_day), 3),
    "days_still_short_after_repair": sum(1 for x in per_day if x["rep_bal_TWh"] < 0),
}

# plausibility of repaired nuclear / gas levels on repaired dates
for f in ("Nuclear", "Fossil Gas"):
    vals = [rep_fuel[d].get(f, 0.0) for d in my_zero if d in rep_fuel]
    lo = sorted(vals)[:3]
    hi = sorted(vals)[-3:]
    res.setdefault("level_check", {})[f] = {
        "min": round(min(vals), 1), "max": round(max(vals), 1),
        "lowest3": [round(v, 1) for v in lo], "highest3": [round(v, 1) for v in hi],
        "zeros_remaining": sum(1 for v in vals if v == 0),
    }

# any remaining all-dispatchable-zero dates in the repaired table
rep_zero = sorted(d for d, mix in rep_fuel.items()
                  if mix and all(mix.get(f, 0.0) == 0.0 for f in DISPATCHABLE))
res["remaining_all_zero_dates"] = {"count": len(rep_zero), "examples": rep_zero[:8]}

# 2022-08-02 status
res["demand_outlier_2022_08_02"] = {
    "orig_gen": orig_total.get("2022-08-02"), "rep_gen": rep_total.get("2022-08-02"),
    "demand": demand.get("2022-08-02"),
}

out = Path(__file__).resolve().parents[1] / "audit" / "verify_repair_release.json"
out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
print(json.dumps(res, indent=2))
