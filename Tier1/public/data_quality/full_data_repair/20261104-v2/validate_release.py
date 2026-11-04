"""Independent arithmetic and completeness checks on the versioned data release."""
import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def rows(name, base=None):
    with ((base or HERE / "data") / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-root", type=Path, required=True)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    audit = json.loads((HERE / "REPAIR_AUDIT.json").read_text(encoding="utf-8"))
    expected = {(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(2452)}
    fuel = defaultdict(dict)
    for r in rows("daily_generation_by_fuel.csv"):
        assert r["psrType"] not in fuel[r["date"]]
        fuel[r["date"]][r["psrType"]] = int(r["MW"])
    total = {r["date"]: int(r["total_MW"]) for r in rows("daily_generation_total.csv")}
    demand = {r["startTime"][:10]: int(r["demand"]) for r in rows("daily_demand.csv")}
    prices = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in rows("daily_market_index_price.csv")}
    wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows("wind_farm_generation.csv")}
    for panel in (fuel, total, demand, prices, wind):
        assert panel.keys() == expected
    assert all(len(v) == 11 and all(math.isfinite(x) and x >= 0 for x in v.values()) for v in fuel.values())
    assert all(total[d] == sum(fuel[d].values()) for d in expected)
    assert min(demand.values()) >= 10000
    assert all(fuel[d]["Solar"] > 0 for d in expected)
    for r in rows("daily_market_index_price.csv"):
        assert abs(float(r["avg_price_£_per_MWh"]) * 24 - float(r["avg_price_£_per_MW_day"])) < 1e-8
    original_wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows("wind_farm_generation.csv", args.course_root)}
    assert all(wind[d] == original_wind[d] for d in expected)
    original = defaultdict(dict)
    for r in rows("daily_generation_by_fuel.csv", args.course_root):
        original[r["date"]][r["psrType"]] = int(r["MW"])
    eight = ["Biomass", "Fossil Gas", "Fossil Hard coal", "Fossil Oil", "Hydro Pumped Storage",
             "Hydro Run-of-river and poundage", "Nuclear", "Other"]
    old_107 = [d for d, v in original.items() if all(v[k] == 0 for k in eight)]
    assert len(old_107) == 107
    assert all(fuel[d]["Nuclear"] > 0 and fuel[d]["Fossil Gas"] > 0 for d in old_107)
    old_solar = [d for d, v in original.items() if v["Solar"] == 0]
    assert len(old_solar) == 42 and all(fuel[d]["Solar"] > 0 for d in old_solar)
    original_demand = {r["startTime"][:10]: int(r["demand"]) for r in rows("daily_demand.csv", args.course_root)}
    with gzip.open(HERE / "evidence/demand.json.gz", "rt", encoding="utf-8") as stream:
        vd = json.load(stream)["days"]
    snapshots = [d for d in original_demand if date.fromisoformat(d).weekday() == 1 or d == "2026-09-17"]
    assert len(snapshots) == 350
    assert all(vd[d][d + "T00:00:00Z"] == original_demand[d] for d in snapshots)
    with gzip.open(HERE / "evidence/mid.json.gz", "rt", encoding="utf-8") as stream:
        mid = json.load(stream)
    same_price = 0
    placeholder_records = 0
    zero_price_with_volume = 0
    original_prices = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in rows("daily_market_index_price.csv", args.course_root)}
    reproduced_original_prices = 0
    for day, periods in mid["days"].items():
        active = []
        for providers in periods.values():
            valid = [(p, v) for p, v in providers.values() if v > 0]
            placeholder_records += sum(v == 0 for p, v in providers.values())
            zero_price_with_volume += sum(p == 0 and v > 0 for p, v in providers.values())
            if valid:
                active.append(sum(p * v for p, v in valid) / sum(v for p, v in valid))
        if len(active) == 48:
            assert abs(prices[day] - mean(active)) < 1e-8
            same_price += 1
        if day in original_prices:
            if date.fromisoformat(day).weekday() == 1 or day == "2026-09-17":
                old_method = mean(p for p, v in periods[day + "T00:00:00Z"].values())
            else:
                old_method = mean(p for providers in periods.values() for p, v in providers.values())
            assert abs(old_method - original_prices[day]) < 1e-8
            reproduced_original_prices += 1
    for name, checksum in audit["output_sha256"].items():
        assert hashlib.sha256((HERE / "data" / name).read_bytes()).hexdigest() == checksum
    for name, checksum in audit["original_sha256"].items():
        assert hashlib.sha256((args.course_root / name).read_bytes()).hexdigest() == checksum
    result = {
        "date_count_per_file": 2452,
        "fuel_cells": 2452 * 11,
        "original_107_dates_fixed": 107,
        "original_zero_solar_dates_fixed": 42,
        "price_days_independently_recomputed": same_price,
        "original_demand_midnight_values_reproduced": 350,
        "original_price_values_reproduced": reproduced_original_prices,
        "excluded_zero_volume_provider_records": placeholder_records,
        "retained_zero_price_positive_volume_records": zero_price_with_volume,
        "negative_final_price_days": sum(p < 0 for p in prices.values()),
        "wind_zero_days_preserved": sum(v == 0 for v in wind.values()),
        "demand_2022_08_02_MW": demand["2022-08-02"],
        "quality_panel_counts": audit["quality_panel_counts"],
        "all_assertions_passed": True,
    }
    if args.write_report:
        (HERE / "VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
