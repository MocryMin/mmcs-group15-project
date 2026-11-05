"""Build the daily model input table from the repaired 20261104-v2 data.

Inputs:  data/*.csv (copied from Tier1/public/data_quality/full_data_repair/20261104-v2/data)
Output:  data/daily_model_inputs.csv
"""
import csv, io, json, pathlib
from collections import defaultdict

PKG = pathlib.Path(__file__).resolve().parents[1]
DATA = PKG / "data"

MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

def rows(name):
    with io.open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def cpi_monthly():
    out = {}
    with io.open(DATA / "ONS-CPI-D7BT.csv", encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if len(r) != 2:
                continue
            k, v = r
            parts = k.split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1] in MONTHS:
                out[(int(parts[0]), MONTHS[parts[1]])] = float(v)
    return out

def main():
    cpi = cpi_monthly()
    total = {r["date"]: float(r["total_MW"]) for r in rows("daily_generation_total.csv")}
    wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows("wind_farm_generation.csv")}
    demand = {r["startTime"][:10]: float(r["demand"]) for r in rows("daily_demand.csv")}
    price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in rows("daily_market_index_price.csv")}
    strict = {r["date"]: int(r["strict_no_imputation"]) for r in rows("date_quality.csv")}
    fuel = defaultdict(dict)
    for r in rows("daily_generation_by_fuel.csv"):
        fuel[r["date"]][r["psrType"]] = float(r["MW"])

    renewable_types = ["Wind Onshore", "Wind Offshore", "Solar", "Hydro Run-of-river and poundage", "Biomass"]
    dates = sorted(total)
    out = []
    for d in dates:
        y, m = int(d[:4]), int(d[5:7])
        c = cpi.get((y, m))
        if c is None:
            raise SystemExit(f"missing monthly CPI for {d}")
        gt = total[d] + wind[d]          # MW daily mean, national total + specified farm
        g = gt * 24.0 / 1000.0           # GWh/day
        dm = demand[d]
        dd = dm * 24.0 / 1000.0
        p = price[d]
        p_real = p * 108.7 / c
        ren_mw = wind[d] + sum(fuel[d].get(t, 0.0) for t in renewable_types)
        ren = ren_mw * 24.0 / 1000.0
        out.append({
            "date": d, "G_GWh": round(g, 9), "D_GWh": round(dd, 9),
            "price_nominal_GBP_MWh": round(p, 9), "price_GBP2020_MWh": round(p_real, 9),
            "wind_farm_GWh": round(wind[d] * 24 / 1000.0, 9),
            "renewable_GWh": round(ren, 9), "other_GWh": round(g - ren, 9),
            "strict_no_imputation": strict[d], "cpi_month": c,
        })

    fn = ["date", "G_GWh", "D_GWh", "price_nominal_GBP_MWh", "price_GBP2020_MWh",
          "wind_farm_GWh", "renewable_GWh", "other_GWh", "strict_no_imputation", "cpi_month"]
    with io.open(PKG / "data" / "daily_model_inputs.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        w.writerows(out)

    summary = {
        "days": len(out), "first": out[0]["date"], "last": out[-1]["date"],
        "years": {y: sum(1 for r in out if r["date"].startswith(str(y))) for y in range(2020, 2027)},
        "cpi_2020": 108.7, "deflator": "p_real = p_nominal * 108.7 / CPI_month (ONS D7BT, 2015=100)",
        "G_2023_GWh": round(sum(r["G_GWh"] for r in out if r["date"].startswith("2023")), 3),
        "D_2023_GWh": round(sum(r["D_GWh"] for r in out if r["date"].startswith("2023")), 3),
        "surplus_2023_GWh": round(sum(max(0.0, r["G_GWh"] - r["D_GWh"]) for r in out if r["date"].startswith("2023")), 3),
        "median_price_2023_GBP2020": sorted(r["price_GBP2020_MWh"] for r in out if r["date"].startswith("2023"))[182],
        "strict_days_2023": sum(1 for r in out if r["date"].startswith("2023") and r["strict_no_imputation"] == 1),
        "negative_or_zero_price_days": sum(1 for r in out if r["price_nominal_GBP_MWh"] <= 0),
    }
    (PKG / "data" / "DATA_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
