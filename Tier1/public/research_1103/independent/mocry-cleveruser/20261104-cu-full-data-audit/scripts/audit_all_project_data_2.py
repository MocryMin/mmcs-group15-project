# -*- coding: utf-8 -*-
"""Second pass: resolve the deficit-metric discrepancy and pin down per-fuel anomalies."""
import csv
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])


def load(path, key, val, cast=float):
    rows = list(csv.reader(open(os.path.join(REPO, path), encoding="utf-8", newline="")))
    hdr = rows[0]
    return [{c: r[i] for i, c in enumerate(hdr)} for r in rows[1:]]


gen = defaultdict(dict)
for r in load("daily_generation_by_fuel.csv", None, None):
    gen[r["date"]][r["psrType"]] = float(r["MW"])
tot = {r["date"]: float(r["total_MW"]) for r in load("daily_generation_total.csv", None, None)}
dem_rows = load("daily_demand.csv", None, None)
dem = {r["startTime"][:10]: float(r["demand"]) for r in dem_rows}
wf = {r["date"]: float(r["wind_farm_MW"]) for r in load("wind_farm_generation.csv", None, None)}
price = {r["date"]: (float(r["avg_price_£_per_MWh"]), float(r["avg_price_£_per_MW_day"]))
         for r in load("daily_market_index_price.csv", None, None)}
rep_dir = os.path.join(REPO, "Tier1", "public", "data_quality", "generation_repair", "20261103-v1")
rtot = {r["date"]: float(r["total_MW"])
        for r in load(os.path.join(rep_dir, "daily_generation_total.csv"), None, None)}

common = sorted(set(dem) & set(tot) & set(price) & set(wf))
res = {"n_common": len(common)}

# ---- A. the three possible balance definitions
def bal(total, days, add_wind):
    out = []
    for d in days:
        g = total[d] + (wf[d] if add_wind else 0.0)
        out.append((d, g - dem[d]))
    return out

for tag, add_wind in (("gen_only", False), ("gen_plus_windfarm", True)):
    for src, total in (("orig", tot), ("rep", rtot)):
        b = bal(total, [d for d in common if d in total], add_wind)
        defi = sum(-x for _, x in b if x < 0) * 24 / 1e6
        sur = sum(x for _, x in b if x > 0) * 24 / 1e6
        res.setdefault("balance_variants", {})["%s_%s" % (tag, src)] = {
            "days": len(b), "deficit_TWh": round(defi, 3), "surplus_TWh": round(sur, 3),
            "net_TWh": round(sum(x for _, x in b) * 24 / 1e6, 3),
            "mean_gap_MW": round(statistics.fmean([x for _, x in b]), 1),
        }

# ---- B. extreme balance days
b = bal(tot, common, False)
b.sort(key=lambda t: t[1])
res["worst_deficit_days"] = [
    {"date": d, "gap_MW": round(g, 1), "gen": tot[d], "demand": dem[d],
     "wind_fuel": round(gen[d].get("Wind Onshore", 0) + gen[d].get("Wind Offshore", 0), 1),
     "solar": gen[d].get("Solar"), "price": price[d][0],
     "nonwind_sum": round(sum(v for k, v in gen[d].items() if "Wind" not in k), 1)}
    for d, g in b[:12]
]
res["worst_surplus_days"] = [
    {"date": d, "gap_MW": round(g, 1), "gen": tot[d], "demand": dem[d],
     "wind_fuel": round(gen[d].get("Wind Onshore", 0) + gen[d].get("Wind Offshore", 0), 1),
     "solar": gen[d].get("Solar"), "price": price[d][0],
     "nonwind_sum": round(sum(v for k, v in gen[d].items() if "Wind" not in k), 1)}
    for d, g in b[-12:]
]

# ---- C. demand anomalies & record types
rt = Counter(r["recordType"] for r in dem_rows)
res["demand_record_types"] = dict(rt)
res["demand_non_integer"] = sum(1 for v in dem.values() if not float(v).is_integer())
dvals = sorted(((v, d) for d, v in dem.items()))
res["demand_extremes"] = {"top": dvals[-8:], "bottom": dvals[:8],
                          "median": statistics.median(dem.values())}
res["demand_2022_08_02"] = dem.get("2022-08-02")

# ---- D. zero-day structure per fuel
zero_sets = {}
for p in sorted({p for d in gen for p in gen[d]}):
    zero_sets[p] = {d for d in gen if gen[d].get(p) == 0}
rep_changed = set(json.load(open(os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser",
                                              "audit", "all_data_audit.json"), encoding="utf-8"))["repair"]["changed_dates"]) \
    if os.path.exists(os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser", "audit", "all_data_audit.json")) else set()
res["zero_days"] = {}
for p, s in zero_sets.items():
    res["zero_days"][p] = {
        "n": len(s), "in_107_repair_set": len(s & rep_changed) if rep_changed else None,
        "outside_repair_set": sorted(s - rep_changed)[:15] if rep_changed else None,
        "n_outside": len(s - rep_changed) if rep_changed else None,
    }
core = [p for p in zero_sets if len(zero_sets[p]) == 107]
res["zero_days"]["_shared_107_identical"] = {
    "fuels": core, "all_equal": all(zero_sets[p] == zero_sets[core[0]] for p in core) if core else None,
    "equals_repair_set": (zero_sets[core[0]] == rep_changed) if core and rep_changed else None,
}
# coal retirement
coal = [(d, gen[d]["Fossil Hard coal"]) for d in sorted(gen) if "Fossil Hard coal" in gen[d]]
nz = [x for x in coal if x[1] > 0]
res["coal"] = {"first_nonzero": nz[0], "last_nonzero": nz[-1],
               "nonzero_after_last_quarter_2024": [x for x in nz if x[0] > "2024-09-30"][:20],
               "nonzero_after_2024_06": sum(1 for x in nz if x[0] > "2024-06-30")}
# solar zero days
res["solar_zero_dates"] = sorted(zero_sets.get("Solar", set()))
res["oil_all_zero"] = all(gen[d].get("Fossil Oil", 0) == 0 for d in gen)

# ---- E. wind farm vs national wind
wind_cols = ["Wind Onshore", "Wind Offshore"]
nat = {d: sum(gen[d].get(p, 0.0) for p in wind_cols) for d in gen}
pairs = [(d, wf[d], nat[d]) for d in sorted(set(wf) & set(gen))]
ratios = [w / n for _, w, n in pairs if n > 0]
res["windfarm_vs_national"] = {
    "wf_mean": round(statistics.fmean([w for _, w, _ in pairs]), 2),
    "national_mean": round(statistics.fmean([n for _, _, n in pairs]), 2),
    "ratio_mean": round(statistics.fmean(ratios), 5),
    "ratio_min": round(min(ratios), 5), "ratio_max": round(max(ratios), 5),
    "wf_max": max(w for _, w, _ in pairs), "wf_min": min(w for _, w, _ in pairs),
    "n_wf_zero": sum(1 for _, w, _ in pairs if w == 0),
    "corr": round(statistics.correlation([w for _, w, _ in pairs], [n for _, _, n in pairs]), 4),
}
# monthly ratio to see if it tracks a fixed farm share
mon = defaultdict(list)
for d, w, n in pairs:
    mon[d[:7]].append(w / n if n else 0)
res["windfarm_ratio_by_month"] = {k: round(statistics.fmean(v), 4) for k, v in sorted(mon.items())}

# ---- F. price year profile
py = defaultdict(list)
for d in sorted(price):
    py[d[:4]].append(price[d][0])
res["price_by_year"] = {y: {"n": len(v), "mean": round(statistics.fmean(v), 2), "min": min(v), "max": max(v),
                            "neg": sum(1 for x in v if x < 0), "zero": sum(1 for x in v if x == 0),
                            "p05": sorted(v)[int(0.05 * (len(v) - 1))], "p95": sorted(v)[int(0.95 * (len(v) - 1))]}
                        for y, v in sorted(py.items())}
res["neg_price_days"] = [(d, price[d][0]) for d in sorted(price) if price[d][0] < 0]
res["price_abs_max"] = max(((abs(v[0]), d, v[0]) for d, v in price.items()))

# ---- G. metering-boundary test: does gap track solar(+wind)?
xs_solar = [gen[d].get("Solar", 0.0) for d in common]
xs_wind = [nat[d] for d in common]
ys = [tot[d] - dem[d] for d in common]
res["boundary_test"] = {
    "mean_gap_MW": round(statistics.fmean(ys), 1),
    "mean_solar_MW": round(statistics.fmean(xs_solar), 1),
    "mean_wind_MW": round(statistics.fmean(xs_wind), 1),
    "corr_gap_solar": round(statistics.correlation(ys, xs_solar), 4),
    "corr_gap_wind": round(statistics.correlation(ys, xs_wind), 4),
    "share_days_gap_negative": round(sum(1 for y in ys if y < 0) / len(ys), 4),
    "mean_gap_summer": round(statistics.fmean([tot[d] - dem[d] for d in common if d[5:7] in ("05", "06", "07", "08")]), 1),
    "mean_gap_winter": round(statistics.fmean([tot[d] - dem[d] for d in common if d[5:7] in ("11", "12", "01", "02")]), 1),
}
# direct estimate of embedded energy: gap should equal -(embedded solar+wind)
embedded_hypothesis = statistics.fmean([x for x in ys]) + statistics.fmean(xs_solar)
res["boundary_test"]["gap_plus_solar_mean_MW"] = round(embedded_hypothesis, 1)

# ---- H. per-fuel 2026 vs earlier share shift (sanity on units)
for y in ("2020", "2023", "2026"):
    ds = [d for d in gen if d.startswith(y)]
    res.setdefault("fuel_share_by_year", {})[y] = {
        p: round(statistics.fmean([gen[d].get(p, 0) for d in ds]), 1) for p in sorted(gen[ds[0]])
    }

json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
