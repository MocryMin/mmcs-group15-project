#!/usr/bin/env python3
"""Controller cross-check of the R4 claim: dates where every dispatchable fuel is exactly 0 MW.

Also recomputes the deficit/surplus with those dates and the 2022-08-02 demand outlier excluded.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
DISPATCHABLE = {"Fossil Gas", "Fossil Hard coal", "Fossil Oil", "Nuclear", "Biomass",
                "Hydro Run-of-river and poundage", "Hydro Pumped Storage", "Other"}


def rows(name):
    text = (REPO / name).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


fuel = rows("daily_generation_by_fuel.csv")
total = {r["date"]: float(r["total_MW"]) for r in rows("daily_generation_total.csv")}
demand = {r["startTime"][:10]: float(r["demand"]) for r in rows("daily_demand.csv")}
wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows("wind_farm_generation.csv")}
price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in rows("daily_market_index_price.csv")}

by_date: dict[str, dict[str, float]] = {}
for r in fuel:
    by_date.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])

zero_dates = sorted(d for d, mix in by_date.items()
                    if mix and all(mix.get(f, 0.0) == 0.0 for f in DISPATCHABLE))
common = sorted(set(demand) & set(total) & set(wind) & set(price))
zero_in_common = [d for d in zero_dates if d in common]

# contiguous blocks
blocks = []
for d in zero_dates:
    from datetime import date as _d, timedelta
    y, m, dd = map(int, d.split("-"))
    cur = _d(y, m, dd)
    if blocks and cur - blocks[-1][1] == timedelta(days=1):
        blocks[-1][1] = cur
    else:
        blocks.append([cur, cur])

def surplus_deficit(days):
    s = sum(max(0.0, (total[d] + wind[d]) - demand[d]) * 24 for d in days)
    df = sum(max(0.0, demand[d] - (total[d] + wind[d])) * 24 for d in days)
    return round(s, 1), round(df, 1)

s_all, d_all = surplus_deficit(common)
keep = [d for d in common if d not in set(zero_in_common) and d != "2022-08-02"]
s_kept, d_kept = surplus_deficit(keep)

out = {
    "dispatchable_set": sorted(DISPATCHABLE),
    "dates_all_dispatchable_zero": len(zero_dates),
    "dates_all_dispatchable_zero_in_common": len(zero_in_common),
    "blocks": [{"start": b[0].isoformat(), "end": b[1].isoformat(),
                "days": (b[1] - b[0]).days + 1} for b in blocks],
    "example_dates": zero_dates[:5],
    "total_MW_on_zero_dates_stats": {
        "min": min(total[d] for d in zero_dates) if zero_dates else None,
        "max": max(total[d] for d in zero_dates) if zero_dates else None,
    },
    "surplus_deficit_all_days_MWh": {"surplus": s_all, "deficit": d_all},
    "surplus_deficit_excluding_zero_dates_and_2022_08_02": {"surplus": s_kept, "deficit": d_kept,
                                                            "days": len(keep)},
}
(AUDIT := Path(__file__).resolve().parents[1] / "audit" / "crosscheck_r4_artefact.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
