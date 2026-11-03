import csv
import datetime as dt
import json
from collections import Counter

B = "Tier1/workspaces/mocry/cleveruser/inputs/"
rows = list(csv.DictReader(open(B + "daily_generation_by_fuel.csv", encoding="utf-8-sig", newline="")))
by_date = {}
for r in rows:
    by_date.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
tot = {r["date"]: float(r["total_MW"])
       for r in csv.DictReader(open(B + "daily_generation_total.csv", encoding="utf-8-sig", newline=""))}
dem = {}
for r in csv.DictReader(open(B + "daily_demand.csv", encoding="utf-8-sig", newline="")):
    d = r["startTime"][:10]
    dem[d] = float(r["demand"])

low = sorted(d for d, v in tot.items() if v < 10000)
print("days total_MW<10000:", len(low), "of", len(tot))
print("by year:", dict(sorted(Counter(d[:4] for d in low).items())))
print("by month:", dict(sorted(Counter(d[:7] for d in low).items())))
for d in ["2022-12-11", "2023-04-25", "2026-07-30", "2022-12-12"]:
    mix = by_date.get(d, {})
    print(d, "total=%.0f demand=%s" % (tot.get(d, 0), dem.get(d)),
          {k: v for k, v in sorted(mix.items(), key=lambda x: -x[1])})
    print("   sum of fuels:", sum(mix.values()))
# how many days have every non-wind fuel exactly 0?
zero_days = [d for d, m in by_date.items()
             if all(v == 0 for k, v in m.items() if k not in ("Wind Onshore", "Wind Offshore", "Solar"))]
print("days with all non-wind/solar fuels zero:", len(zero_days), zero_days[:10])
