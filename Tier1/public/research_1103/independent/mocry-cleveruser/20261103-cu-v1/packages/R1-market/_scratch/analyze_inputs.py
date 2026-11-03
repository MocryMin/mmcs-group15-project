"""Descriptive checks on the supplied price/demand/generation series for R1.

Reads only the byte-identical input copies under cleveruser/inputs/.
Prints: row counts, date coverage, price unit reconciliation, negative-price days,
and simple generation-vs-demand scale indicators relevant to a price-taking check.
"""
import csv
import datetime as dt
import os
import statistics

BASE = os.path.join("Tier1", "workspaces", "mocry", "cleveruser", "inputs")


def load(path, datecol, valuecols):
    rows = []
    with open(os.path.join(BASE, path), newline="", encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        for r in rdr:
            raw_date = r[datecol].strip()
            d = dt.date.fromisoformat(raw_date[:10])
            rec = {"date": d}
            for c in valuecols:
                raw = (r.get(c) or "").strip()
                rec[c] = float(raw) if raw not in ("", "NA", "NaN", "null") else None
            rows.append(rec)
    return rows


price = load("daily_market_index_price.csv", "date", ["avg_price_\u00a3_per_MWh", "avg_price_\u00a3_per_MW_day"])
dem_types = {}
with open(os.path.join(BASE, "daily_demand.csv"), newline="", encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        k = (r["recordType"] or "").strip()
        dem_types[k] = dem_types.get(k, 0) + 1
print("demand recordType counts:", dem_types)
dem = load("daily_demand.csv", "startTime", ["demand"])
gen = load("daily_generation_total.csv", "date", ["total_MW"])
wind = load("wind_farm_generation.csv", "date", ["wind_farm_MW"])

print("rows: price=%d demand=%d gen=%d wind=%d" % (len(price), len(dem), len(gen), len(wind)))
for name, rows in (("price", price), ("demand", dem), ("gen", gen), ("wind", wind)):
    print("%s coverage %s .. %s" % (name, rows[0]["date"], rows[-1]["date"]))

# date intersection
sets = {n: {r["date"] for r in rows} for n, rows in (("price", price), ("demand", dem), ("gen", gen), ("wind", wind))}
inter = set.intersection(*sets.values())
print("intersection days = %d (%s .. %s)" % (len(inter), min(inter), max(inter)))
for n, s in sets.items():
    print("  %-6s missing vs intersection: %d" % (n, len(s - inter)))

# price stats
vals = [r["avg_price_\u00a3_per_MWh"] for r in price if r["avg_price_\u00a3_per_MWh"] is not None]
print("price MWh: n=%d mean=%.2f median=%.2f min=%.2f max=%.2f" % (
    len(vals), statistics.mean(vals), statistics.median(vals), min(vals), max(vals)))
neg = [r for r in price if r["avg_price_\u00a3_per_MWh"] is not None and r["avg_price_\u00a3_per_MWh"] < 0]
print("negative-price days=%d (%.2f%% of days)" % (len(neg), 100.0 * len(neg) / len(vals)))
if neg:
    print("  first=%s last=%s min=%.2f" % (neg[0]["date"], neg[-1]["date"],
                                           min(r["avg_price_\u00a3_per_MWh"] for r in neg)))
by_year = {}
for r in neg:
    by_year[r["date"].year] = by_year.get(r["date"].year, 0) + 1
print("  negative days by year:", dict(sorted(by_year.items())))

# unit reconciliation: MW_day == 24 * per_MWh ?
diffs = []
for r in price:
    a, b = r["avg_price_\u00a3_per_MWh"], r["avg_price_\u00a3_per_MW_day"]
    if a is None or b is None:
        continue
    diffs.append(abs(b - 24.0 * a))
print("max |MW_day - 24*MWh| = %.6f over %d rows" % (max(diffs), len(diffs)))
not24 = sum(1 for d in diffs if d > 0.05)
print("rows failing 24x identity (>0.05):", not24)

# scale: demand vs generation
dvals = [r["demand"] for r in dem if r["demand"] is not None]
gvals = [r["total_MW"] for r in gen if r["total_MW"] is not None]
wvals = [r["wind_farm_MW"] for r in wind if r["wind_farm_MW"] is not None]
print("demand MW: mean=%.0f p1=%.0f p99=%.0f max=%.0f" % (
    statistics.mean(dvals), sorted(dvals)[int(0.01 * len(dvals))], sorted(dvals)[int(0.99 * len(dvals))], max(dvals)))
print("total gen MW: mean=%.0f p1=%.0f p99=%.0f max=%.0f" % (
    statistics.mean(gvals), sorted(gvals)[int(0.01 * len(gvals))], sorted(gvals)[int(0.99 * len(gvals))], max(gvals)))
print("wind farm MW: mean=%.1f max=%.1f" % (statistics.mean(wvals), max(wvals)))

# implied MWh/day scale
print("implied demand GWh/day mean = %.1f" % (statistics.mean(dvals) * 24 / 1000.0))
print("implied total gen GWh/day mean = %.1f" % (statistics.mean(gvals) * 24 / 1000.0))

# share of system represented by a hypothetical 100/500 MW farm at mean output
for mw in (100, 200, 500):
    print("a %d MW farm at 35%% load factor = %.0f MW = %.2f%% of mean demand" % (
        mw, 0.35 * mw, 100 * 0.35 * mw / statistics.mean(dvals)))
