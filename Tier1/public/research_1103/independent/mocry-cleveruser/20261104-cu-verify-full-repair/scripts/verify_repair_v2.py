"""Independent checks of the 20261104-v2 full data repair against course originals.

Does not import the repair scripts; only reads published CSVs and recomputes
identities, coverage and before/after comparisons.
"""
import csv
import json
import os
import statistics
from collections import defaultdict
from datetime import date, timedelta

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(here, "SOURCE_MANIFEST.json")) and os.path.exists(os.path.join(here, "PROJECT.md")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            raise SystemExit("project root not found above " + os.path.dirname(os.path.abspath(__file__)))
        here = parent


ROOT = _project_root()
PUB = os.path.join(ROOT, "Tier1", "public", "data_quality", "full_data_repair", "20261104-v2")
DATA = os.path.join(PUB, "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "audit", "verify_repair_v2.json")


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def date_range(a, b):
    d, out = a, []
    while d <= b:
        out.append(d)
        d += timedelta(days=1)
    return out


def mad(xs):
    return sum(abs(x) for x in xs) / len(xs) if xs else None


res = {}

# ---- generation by fuel ----
g = rows(os.path.join(DATA, "daily_generation_by_fuel.csv"))
tot = rows(os.path.join(DATA, "daily_generation_total.csv"))
pivot = defaultdict(dict)
cats = set()
bad = []
for r in g:
    v = float(r["MW"])
    pivot[r["date"]][r["psrType"]] = v
    cats.add(r["psrType"])
    if v < 0:
        bad.append((r["date"], r["psrType"], v))
total_rep = {r["date"]: float(r["total_MW"]) for r in tot}
cal = date_range(date(2020, 1, 1), date(2026, 9, 17))
res["gen_categories"] = sorted(cats)
res["gen_category_count"] = len(cats)
res["gen_dates"] = len(pivot)
res["total_dates"] = len(total_rep)
res["gen_missing_from_calendar"] = [d.isoformat() for d in cal if d.isoformat() not in pivot]
res["gen_extra_outside_calendar"] = sorted(set(pivot) - {d.isoformat() for d in cal})
res["negative_cells"] = bad[:20]
res["negative_cell_count"] = len(bad)
devs = []
for d, t in total_rep.items():
    s = sum(pivot[d].values())
    devs.append((abs(s - t), d, s, t))
devs.sort(reverse=True)
res["fuel_sum_max_dev"] = devs[0][0] if devs else None
res["fuel_sum_worst"] = devs[0][1:] if devs else None
res["fuel_sum_days_mismatch_gt_1e-6"] = sum(1 for x in devs if x[0] > 1e-6)

# ---- price ----
p = rows(os.path.join(DATA, "daily_market_index_price.csv"))
res["price_dates"] = len(p)
pdev = max(abs(float(r["avg_price_£_per_MW_day"]) - 24 * float(r["avg_price_£_per_MWh"])) for r in p)
res["price_identity_max_dev"] = pdev
new_price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in p}
res["price_negative_days"] = sorted(d for d, v in new_price.items() if v < 0)
res["price_zero_days"] = sorted(d for d, v in new_price.items() if v == 0)
res["price_min"] = min(new_price.items(), key=lambda kv: kv[1])
res["price_max"] = max(new_price.items(), key=lambda kv: kv[1])

# ---- demand ----
drows = rows(os.path.join(DATA, "daily_demand.csv"))
res["demand_header"] = list(drows[0].keys())
new_dem = {r["startTime"][:10]: float(r["demand"]) for r in drows}
res["demand_dates"] = len(new_dem)
res["demand_min"] = min(new_dem.items(), key=lambda kv: kv[1])
res["demand_2022_08_02"] = new_dem.get("2022-08-02")

# ---- wind farm ----
w = rows(os.path.join(DATA, "wind_farm_generation.csv"))
new_wind = {r["date"]: float(r["wind_farm_MW"]) for r in w}
res["wind_dates"] = len(new_wind)
res["wind_zero_days"] = sorted(d for d, v in new_wind.items() if v == 0)

# ---- originals ----
og = rows(os.path.join(ROOT, "daily_generation_by_fuel.csv"))
otot = rows(os.path.join(ROOT, "daily_generation_total.csv"))
op = rows(os.path.join(ROOT, "daily_market_index_price.csv"))
od = rows(os.path.join(ROOT, "daily_demand.csv"))
ow = rows(os.path.join(ROOT, "wind_farm_generation.csv"))
res["orig_rows"] = {"fuel": len(og), "total": len(otot), "price": len(op), "demand": len(od), "wind": len(ow)}
oprice = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in op}
ototal = {r["date"]: float(r["total_MW"]) for r in otot}
odem = {}
for r in od:
    k = r.get("startTime") or r.get("date") or ""
    odem[k[:10]] = float(r["demand"])

common = sorted(set(oprice) & set(new_price))
res["price_common_days"] = len(common)
res["price_changed_days"] = sum(1 for d in common if abs(oprice[d] - new_price[d]) > 1e-6)
ratio = [new_price[d] / oprice[d] for d in common if oprice[d] > 0]
res["price_ratio_new_over_old"] = {
    "mean": statistics.mean(ratio), "median": statistics.median(ratio),
    "min": min(ratio), "max": max(ratio),
}
annual = defaultdict(lambda: [[], []])
for d in common:
    annual[d[:4]][0].append(oprice[d])
    annual[d[:4]][1].append(new_price[d])
res["price_annual_mean_old_vs_new"] = {
    y: {"old": round(statistics.mean(v[0]), 3), "new": round(statistics.mean(v[1]), 3),
        "ratio": round(statistics.mean(v[1]) / statistics.mean(v[0]), 4) if statistics.mean(v[0]) else None}
    for y, v in sorted(annual.items())
}
res["price_2020_01_01"] = {"old": oprice.get("2020-01-01"), "new": new_price.get("2020-01-01")}

dcommon = sorted(set(odem) & set(new_dem))
deltas = [new_dem[d] - odem[d] for d in dcommon]
res["demand_common_days"] = len(dcommon)
res["demand_changed_days"] = sum(1 for x in deltas if abs(x) > 1e-6)
res["demand_delta_stats"] = {
    "mean": statistics.mean(deltas), "median": statistics.median(deltas),
    "min": min(deltas), "max": max(deltas), "abs_mean": statistics.mean(abs(x) for x in deltas),
}
res["demand_delta_max_day"] = dcommon[deltas.index(min(deltas))]

tcommon = sorted(set(ototal) & set(total_rep))
tdeltas = [total_rep[d] - ototal[d] for d in tcommon]
res["gen_common_days"] = len(tcommon)
res["gen_changed_days"] = sum(1 for x in tdeltas if abs(x) > 1e-6)
res["gen_delta_stats"] = {
    "mean": statistics.mean(tdeltas), "median": statistics.median(tdeltas),
    "min": min(tdeltas), "max": max(tdeltas), "abs_mean": statistics.mean(abs(x) for x in tdeltas),
}
res["gen_annual_mean_old_vs_new"] = {}
for y in sorted({d[:4] for d in tcommon}):
    o = [ototal[d] for d in tcommon if d[:4] == y]
    n = [total_rep[d] for d in tcommon if d[:4] == y]
    res["gen_annual_mean_old_vs_new"][y] = {"old": round(statistics.mean(o), 1), "new": round(statistics.mean(n), 1)}

# ---- solar zero family ----
solar_zero_old = sorted(d for d, m in pivot.items() if False)
og_pivot = defaultdict(dict)
for r in og:
    og_pivot[r["date"]][r["psrType"]] = float(r["MW"])
res["old_solar_zero_count"] = sum(1 for d, m in og_pivot.items() if m.get("Solar") == 0)
res["new_solar_zero_dates"] = sorted(d for d, m in pivot.items() if m.get("Solar") == 0)
res["new_solar_zero_count"] = len(res["new_solar_zero_dates"])
sz = [d for d, m in og_pivot.items() if m.get("Solar") == 0]
res["solar_zero_repaired_values"] = {
    d: {"old": og_pivot[d].get("Solar"), "new": pivot[d].get("Solar")} for d in sorted(sz)
}

# ---- 107 zero-family dates (from 20261103-v1 audit) ----
prev = os.path.join(ROOT, "Tier1", "public", "data_quality", "generation_repair", "20261103-v1",
                    "generation_repair_audit.json")
if os.path.exists(prev):
    pj = json.load(open(prev, encoding="utf-8"))
    dates = pj.get("changed_dates") or pj.get("dates") or []
    if dates and isinstance(dates[0], dict):
        dates = [x.get("date") for x in dates]
    dates = [d for d in dates if d]
    res["repaired_107_count"] = len(dates)
    still = []
    for d in dates:
        m = pivot.get(d, {})
        others = {k: v for k, v in m.items() if k not in ("Wind Onshore", "Wind Offshore", "Solar")}
        if others and all(abs(v) < 1e-9 for v in others.values()):
            still.append(d)
    res["repaired_107_still_all_zero"] = still

# ---- balance panel ----
def gap_stats(dates):
    gaps, tot_w = [], []
    for d in dates:
        gen = total_rep.get(d)
        dem = new_dem.get(d)
        wf = new_wind.get(d)
        if None in (gen, dem):
            continue
        gaps.append(gen - dem)
        tot_w.append(gen + (wf or 0) - dem)
    ng = [x for x in gaps if x < 0]
    nw = [x for x in tot_w if x < 0]
    return {"days": len(gaps), "gap_mean": statistics.mean(gaps),
            "net_mean": statistics.mean(tot_w),
            "deficit_TWh": sum(ng) * 24 / 1e6, "surplus_TWh": sum(x for x in tot_w if x > 0) * 24 / 1e6}


panel = [d.isoformat() for d in cal if d.isoformat() in total_rep and d.isoformat() in new_dem]
res["panel_days"] = len(panel)
res["balance_new_domestic"] = gap_stats(panel)
res["balance_new_plus_wind"] = gap_stats(panel)
yearly = {}
for y in sorted({d[:4] for d in panel}):
    s = gap_stats([d for d in panel if d[:4] == y])
    yearly[y] = {k: round(v, 1) for k, v in s.items()}
res["balance_yearly_plus_wind"] = yearly

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps({
    k: res[k] for k in ("gen_dates", "total_dates", "price_dates", "demand_dates", "wind_dates",
                        "gen_category_count", "fuel_sum_max_dev", "fuel_sum_days_mismatch_gt_1e-6",
                        "negative_cell_count", "price_identity_max_dev", "price_changed_days",
                        "new_solar_zero_count", "panel_days")}, indent=1))
print("full ->", os.path.relpath(OUT, ROOT))
