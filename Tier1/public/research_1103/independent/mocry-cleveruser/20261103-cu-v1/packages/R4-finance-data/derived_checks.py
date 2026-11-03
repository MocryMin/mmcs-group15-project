"""Derived R4 checks: data anomalies, sample length, discount factors, CRF, FX/CPI conversions.

Reads only the input CSVs and finance_evidence.json (produced by fetch_finance.py).
Writes derived_checks.json.
"""

import csv
import datetime as dt
import json
import os

B = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..", "inputs")) + os.sep
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path, col, vcol, datecol="date"):
    out = {}
    for r in csv.DictReader(open(B + path, encoding="utf-8-sig", newline="")):
        d = dt.date.fromisoformat(r[datecol].replace("Z", "").split("T")[0])
        out[d] = float(r[vcol])
    return out


gen = load("daily_generation_total.csv", "date", "total_MW")
dem = load("daily_demand.csv", "startTime", "demand", "startTime")
wind = load("wind_farm_generation.csv", "date", "wind_farm_MW")
price = load("daily_market_index_price.csv", "date", "avg_price_\u00a3_per_MWh")

common = sorted(set(gen) & set(dem) & set(wind) & set(price))
res = {"n_common_dates": len(common),
       "sample_years_365_25": round(len(common) / 365.25, 4)}

# --- anomaly candidates (reported, not removed) ---
res["wind_at_exact_cap_1125_MW"] = {
    "count_all_dates": sum(1 for v in wind.values() if v >= 1124.999),
    "dates": [d.isoformat() for d, v in sorted(wind.items()) if v >= 1124.999],
}
low_gen = sorted((v, d) for d, v in gen.items() if v < 10000)
res["generation_total_below_10000_MW"] = [
    {"date": d.isoformat(), "total_MW": v, "demand_MW": dem.get(d)} for v, d in low_gen]
res["demand_below_15000_MW"] = [
    {"date": d.isoformat(), "demand_MW": v, "generation_MW": gen.get(d)}
    for d, v in sorted(dem.items()) if v < 15000]

# --- surplus / deficit on the common dates, 24 h per day ---
surplus = sum(max(gen[d] + wind[d] - dem[d], 0.0) * 24.0 for d in common)
deficit = sum(max(dem[d] - gen[d] - wind[d], 0.0) * 24.0 for d in common)
res["energy"] = {
    "surplus_MWh_total": round(surplus, 1),
    "deficit_MWh_total": round(deficit, 1),
    "surplus_MWh_per_year": round(surplus / (len(common) / 365.25), 1),
    "deficit_MWh_per_year": round(deficit / (len(common) / 365.25), 1),
    "share_of_days_with_surplus": round(
        sum(1 for d in common if gen[d] + wind[d] > dem[d]) / len(common), 4),
}
ex = [d for d in common if d.isoformat() not in
      {x["date"] for x in res["generation_total_below_10000_MW"] + res["demand_below_15000_MW"]}]
res["without_suspect_days"] = {
    "n_dates": len(ex),
    "mean_generation_MW": round(sum(gen[d] + wind[d] for d in ex) / len(ex), 2),
    "mean_demand_MW": round(sum(dem[d] for d in ex) / len(ex), 2),
    "mean_price_gbp_per_MWh": round(sum(price[d] for d in ex) / len(ex), 3),
}

# --- discount factors and capital recovery factors ---
def df(rate, t):
    return round(1.0 / (1.0 + rate) ** t, 6)


def crf(rate, n):
    return round(rate / (1.0 - (1.0 + rate) ** -n), 6)


rates = [0.03, 0.035, 0.05, 0.07, 0.10]
res["discount_factors"] = {str(r): {str(t): df(r, t) for t in (1, 5, 10, 15, 20, 25)}
                           for r in rates}
res["capital_recovery_factors"] = {str(r): {str(n): crf(r, n) for n in (10, 15, 20, 25)}
                                   for r in rates}
# NPV of a level annual real cash flow of 1 for N years
res["annuity_factors"] = {str(r): {str(n): round((1 - (1 + r) ** -n) / r, 6)
                                   for n in (10, 15, 20, 25)} for r in rates}

# --- FX and CPI conversions from finance_evidence.json ---
fe = json.load(open("finance_evidence.json", encoding="utf-8"))
fx = fe["ecb_exr_gbp_eur"]["annual_mean_gbp_per_eur"]
cpi = fe["cpi_index_annual"]
npv = {}
for y, rate in fx.items():
    npv[y] = round(0.288e6 * rate, 0)
res["battery_capex_gbp_per_MWh_by_fx_year"] = npv
res["battery_capex_gbp_per_MW_2h_battery_2026fx"] = round(2 * 0.288e6 * fx["2026"], 0)
res["cpi_deflator_2025_to_2026_mean"] = round(cpi["2026"]["mean_index"] / cpi["2025"]["mean_index"], 6)
res["cpi_deflator_2020_to_2026_mean"] = round(cpi["2026"]["mean_index"] / cpi["2020"]["mean_index"], 6)
res["cpi_deflator_2020_to_2025_mean"] = round(cpi["2025"]["mean_index"] / cpi["2020"]["mean_index"], 6)

with open("derived_checks.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(res, fh, indent=2, sort_keys=True)
    fh.write("\n")

print(json.dumps(res, indent=1, sort_keys=True)[:4000])
