"""Data-quality screen for the supplied generation/demand series (R4, D-02).

Screen S1 (pre-registered, structural): a date is flagged 'fuel-reporting incomplete'
when every fuel row except Solar, Wind Onshore and Wind Offshore is exactly 0 MW.
S2: total_MW < 10,000 MW (about one third of mean demand).
S3: demand < 15,000 MW (robust-z outlier on the demand series).
S4: exactly 0 MW wind-farm output (possible simulation floor, not an error by itself).
S5: exactly 1,125.0 MW wind-farm output (apparent installed-capacity cap / clipping).

Nothing is removed here: the file reports counts, dates, runs and the effect of an
exclusion scenario so that the team can decide explicitly.
"""

import csv
import datetime as dt
import json
import os
from collections import Counter

B = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..", "inputs")) + os.sep
HERE = os.path.dirname(os.path.abspath(__file__))


def d(s):
    return dt.date.fromisoformat(s.replace("Z", "").split("T")[0])


fuel = {}
for r in csv.DictReader(open(B + "daily_generation_by_fuel.csv", encoding="utf-8-sig", newline="")):
    fuel.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
tot = {r["date"]: float(r["total_MW"])
       for r in csv.DictReader(open(B + "daily_generation_total.csv", encoding="utf-8-sig", newline=""))}
dem = {r["startTime"][:10]: float(r["demand"])
       for r in csv.DictReader(open(B + "daily_demand.csv", encoding="utf-8-sig", newline=""))}
wind = {r["date"]: float(r["wind_farm_MW"])
        for r in csv.DictReader(open(B + "wind_farm_generation.csv", encoding="utf-8-sig", newline=""))}
price = {r["date"]: float(r["avg_price_\u00a3_per_MWh"])
         for r in csv.DictReader(open(B + "daily_market_index_price.csv", encoding="utf-8-sig", newline=""))}

VAR = ("Biomass", "Fossil Gas", "Fossil Hard coal", "Fossil Oil",
       "Hydro Pumped Storage", "Hydro Run-of-river and poundage", "Nuclear", "Other")
s1 = sorted(x for x, m in fuel.items() if all(m.get(k, 0.0) == 0.0 for k in VAR))
s2 = sorted(x for x, v in tot.items() if v < 10000)
s3 = sorted(x for x, v in dem.items() if v < 15000)
s4 = sorted(x for x, v in wind.items() if v == 0.0)
s5 = sorted(x for x, v in wind.items() if v >= 1124.999)

common = sorted(set(tot) & set(dem) & set(wind) & set(price))


def runs(dates):
    out = []
    ds = [d(x) for x in sorted(dates)]
    if not ds:
        return out
    a = b = ds[0]
    for x in ds[1:]:
        if (x - b).days == 1:
            b = x
            continue
        out.append({"start": a.isoformat(), "end": b.isoformat(), "days": (b - a).days + 1})
        a = b = x
    out.append({"start": a.isoformat(), "end": b.isoformat(), "days": (b - a).days + 1})
    return out


def system(dates):
    g = sum((tot[x] + wind[x]) * 24.0 for x in dates)
    dd = sum(dem[x] * 24.0 for x in dates)
    sur = sum(max(tot[x] + wind[x] - dem[x], 0.0) * 24.0 for x in dates)
    defi = sum(max(dem[x] - tot[x] - wind[x], 0.0) * 24.0 for x in dates)
    return {"n_dates": len(dates),
            "generation_MWh": round(g, 1), "demand_MWh": round(dd, 1),
            "surplus_MWh": round(sur, 1), "deficit_MWh": round(defi, 1),
            "mean_price_gbp_per_MWh": round(sum(price[x] for x in dates) / len(dates), 3)}


excl = set(s1) | set(s3)
kept = [x for x in common if x not in excl]
runs_s1 = runs(s1)
out = {
    "screens": {
        "S1_all_dispatchable_fuels_zero": {
            "n": len(s1), "by_year": dict(sorted(Counter(x[:4] for x in s1).items())),
            "longest_runs": sorted(runs_s1, key=lambda r: -r["days"])[:5],
            "dates": s1,
        },
        "S2_total_generation_below_10000_MW": {
            "n": len(s2), "by_year": dict(sorted(Counter(x[:4] for x in s2).items())),
            "all_also_S1": all(x in set(s1) for x in s2),
        },
        "S3_demand_below_15000_MW": {"n": len(s3), "dates": s3},
        "S4_wind_farm_zero_output": {"n": len(s4), "dates": s4},
        "S5_wind_farm_at_cap_1125_MW": {"n": len(s5), "dates": s5},
    },
    "system_all_common_dates": system(common),
    "system_excluding_S1_and_S3": system(kept),
    "n_common_dates": len(common),
    "n_dates_after_exclusion": len(kept),
}
with open("data_quality.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print(json.dumps(out, indent=1, sort_keys=True)[:2500])
