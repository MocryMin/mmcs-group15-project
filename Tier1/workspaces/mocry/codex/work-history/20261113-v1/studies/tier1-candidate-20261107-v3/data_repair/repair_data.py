"""Rebuild the five course CSVs from dated public evidence and audit every cell."""
from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

START = date(2020, 1, 1)
END = date(2026, 9, 17)
DATES = [(START + timedelta(days=i)).isoformat() for i in range((END - START).days + 1)]
FUELS = ["Biomass", "Fossil Gas", "Fossil Hard coal", "Fossil Oil",
         "Hydro Pumped Storage", "Hydro Run-of-river and poundage", "Nuclear",
         "Other", "Solar", "Wind Offshore", "Wind Onshore"]
SOURCE_IDS = {
    "AGPT": "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type",
    "FUELHH": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH",
    "VD": "https://data.elexon.co.uk/bmrs/api/v1/demand/outturn/summary",
    "MID": "https://data.elexon.co.uk/bmrs/api/v1/datasets/MID",
    "NESO": "https://www.neso.energy/data-portal/historic-demand-data",
}
LOW_DEMAND = 10000


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def encoded_csv(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def rounded(value):
    return math.floor(value + 0.5)


def stamp_minutes(stamp):
    return int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() // 60)


def daily_start(day):
    return stamp_minutes(day + "T00:00:00Z")


def expected_times(day, step):
    start = daily_start(day)
    return list(range(start, start + 1440, step))


def finite(value):
    return value is not None and math.isfinite(value)


def interpolate(points, target):
    keys = sorted(points)
    if not keys:
        raise ValueError("No observations available for interpolation")
    index = bisect.bisect_left(keys, target)
    if index == 0:
        return points[keys[0]]
    if index == len(keys):
        return points[keys[-1]]
    left, right = keys[index - 1], keys[index]
    return points[left] + (points[right] - points[left]) * (target - left) / (right - left)


def error_stats(actual, predicted):
    errors = [p - a for a, p in zip(actual, predicted)]
    absolute = sorted(abs(x) for x in errors)
    return {
        "n": len(errors),
        "bias": statistics.mean(errors),
        "mae": statistics.mean(absolute),
        "p95_absolute": absolute[math.ceil(0.95 * len(absolute)) - 1],
        "mape_percent": statistics.mean(abs(e) / a * 100 for a, e in zip(actual, errors) if a > 0),
    }


def fit_ratio(rows):
    denominator = sum(x * x for x, _ in rows)
    return sum(x * y for x, y in rows) / denominator if denominator else 1.0


def fit_two_predictors(rows):
    aa = sum(a * a for a, b, y in rows)
    ab = sum(a * b for a, b, y in rows)
    bb = sum(b * b for a, b, y in rows)
    ay = sum(a * y for a, b, y in rows)
    by = sum(b * y for a, b, y in rows)
    det = aa * bb - ab * ab
    if det <= 0:
        return (fit_ratio([(a, y) for a, b, y in rows]), 0.0)
    return ((ay * bb - by * ab) / det, (by * aa - ay * ab) / det)


def local_wind_estimate(day, field, training, fuel_mean, neso_mean):
    target = date.fromisoformat(day)
    nearest = sorted(training, key=lambda row: abs((date.fromisoformat(row[0]) - target).days))[:60]
    coefficients = fit_two_predictors([(fuel_mean[d][8], neso_mean[d][3], values[field])
                                       for d, values in nearest])
    return max(0, coefficients[0] * fuel_mean[day][8] + coefficients[1] * neso_mean[day][3])


def parse_neso(bundle):
    result = defaultdict(dict)
    london = ZoneInfo("Europe/London")
    keys = ["TSD", "ND", "EMBEDDED_SOLAR_GENERATION", "EMBEDDED_WIND_GENERATION"]
    for resource in bundle["resources"].values():
        if resource["status"] != 200:
            raise ValueError("NESO download failed")
        for row in csv.DictReader(io.StringIO(resource["text"])):
            text = row["SETTLEMENT_DATE"]
            for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d"):
                try:
                    local = datetime.strptime(text, fmt).replace(tzinfo=london)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Unknown NESO date {text}")
            utc = local.astimezone(timezone.utc) + timedelta(minutes=30 * (int(row["SETTLEMENT_PERIOD"]) - 1))
            day = utc.date().isoformat()
            if DATES[0] <= day <= DATES[-1]:
                result[day][int(utc.timestamp() // 60)] = [float(row[k]) for k in keys]
    for day in DATES:
        if len(result[day]) != 48:
            raise ValueError(f"NESO lacks a complete UTC day {day}")
    return result


def repair(repo, here):
    source = {}
    for name in ("agpt", "fuelhh", "neso", "mid", "demand"):
        with gzip.open(here / "evidence" / (name + ".json.gz"), "rt", encoding="utf-8") as stream:
            source[name] = json.load(stream)
        if source[name].get("summary", {}).get("errors"):
            raise ValueError(f"Unresolved source requests in {name}")
    neso = parse_neso(source["neso"])
    neso_mean = {d: [statistics.mean(v[i] for v in neso[d].values()) for i in range(4)] for d in DATES}

    original_fuel = defaultdict(dict)
    for row in load_csv(repo / "daily_generation_by_fuel.csv"):
        original_fuel[row["date"]][row["psrType"]] = int(row["MW"])
    original_total = {r["date"]: int(r["total_MW"]) for r in load_csv(repo / "daily_generation_total.csv")}
    original_demand = {r["startTime"][:10]: int(r["demand"]) for r in load_csv(repo / "daily_demand.csv")}
    original_price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in load_csv(repo / "daily_market_index_price.csv")}
    original_wind = {r["date"]: float(r["wind_farm_MW"]) for r in load_csv(repo / "wind_farm_generation.csv")}
    prior_audit = json.loads((repo / "Tier1/public/data_quality/generation_repair/20261103-v1/generation_repair_audit.json").read_text(encoding="utf-8"))
    old_2026_differences = {r[0] for r in prior_audit["provenance_test"]["current_agpt_differences_2026"]}
    audit, issue_dates, quality = [], defaultdict(set), []
    diagnostics = {}

    def record(day, series, field, old, value, method, sources, issues):
        changed = old is None or abs(value - old) > 1e-9
        quality.append([day, series, field, method, "|".join(sources), "|".join(issues), int(changed)])
        for issue in issues:
            issue_dates[issue].add(day)
        if changed or issues:
            audit.append([day, series, field, "" if old is None else old, value, method,
                          "|".join(sources), "|".join(issues)])

    # Repair the independent half-hour outturn before using it as a fallback.
    fuel_values, fuel_bad = {}, {}
    for day in DATES:
        rows = {stamp_minutes(t): r for t, r in source["fuelhh"]["days"].get(day, {}).items()}
        mapped = {}
        for t, r in rows.items():
            fields = ["BIOMASS", "CCGT", "OCGT", "COAL", "OIL", "PS", "NPSHYD", "NUCLEAR", "OTHER", "WIND"]
            if not all(finite(r.get(k)) for k in fields):
                continue
            mapped[t] = [r["BIOMASS"], r["CCGT"] + r["OCGT"], r["COAL"], r["OIL"],
                         max(0, r["PS"]), r["NPSHYD"], r["NUCLEAR"], r["OTHER"], r["WIND"]]
        med = [statistics.median(v[i] for v in mapped.values()) for i in range(9)]
        bad = {t for t, v in mapped.items()
               if v[1] < 0.4 * med[1] and v[6] < 0.4 * med[6]
               and sum(v[i] < 0.4 * med[i] for i in (0, 1, 5, 6) if med[i] > 100) >= 3}
        good = {t: v for t, v in mapped.items() if t not in bad}
        fixed = {}
        for t in expected_times(day, 30):
            fixed[t] = [max(0.0, interpolate({s: v[i] for s, v in good.items()}, t))
                        for i in range(9)]
        fuel_values[day] = fixed
        fuel_bad[day] = set(expected_times(day, 30)) - good.keys()
    fuel_mean = {d: [statistics.mean(v[i] for v in fuel_values[d].values()) for i in range(9)] for d in DATES}
    diagnostics["fuelhh_filled_intervals_minutes_UTC"] = {
        d: [t - daily_start(d) for t in sorted(times)] for d, times in fuel_bad.items() if times
    }

    # Fit cross-source renewable estimates only to complete AGPT observations.
    raw_agpt, joint_bad, clean = {}, {}, []
    for day in DATES:
        rows = {stamp_minutes(t): v for t, v in source["agpt"]["days"].get(day, {}).items()}
        raw_agpt[day] = rows
        joint_bad[day] = {t for t, v in rows.items() if all(x == 0 for x in v[:8])}
        if len(rows) == 48 and not joint_bad[day] and all(all(finite(x) for x in v) for v in rows.values()):
            means = [statistics.mean(v[i] for v in rows.values()) for i in range(11)]
            if means[8] > 0:
                clean.append((day, means))
    models, calibration, renewable_training = {}, {}, {}
    for year in range(2020, 2027):
        rows = [(d, v) for d, v in clean if d.startswith(str(year))]
        train = [(d, v) for d, v in rows if date.fromisoformat(d).toordinal() % 5 != 0]
        test = [(d, v) for d, v in rows if date.fromisoformat(d).toordinal() % 5 == 0]
        renewable_training[str(year)] = train
        solar_fit = fit_ratio([(neso_mean[d][2], v[8]) for d, v in train])
        wind_fits = [fit_two_predictors([(fuel_mean[d][8], neso_mean[d][3], v[i]) for d, v in train])
                     for i in (9, 10)]
        models[str(year)] = [solar_fit, *wind_fits]
        predicted = [
            [solar_fit * neso_mean[d][2],
             local_wind_estimate(d, 9, train, fuel_mean, neso_mean),
             local_wind_estimate(d, 10, train, fuel_mean, neso_mean)]
            for d, _ in test
        ]
        calibration[str(year)] = {
            "training_days": len(train), "holdout_days": len(test), "solar_factor": solar_fit,
            "wind_coefficients": wind_fits,
            "wind_reconstruction": "Local fit to the nearest 60 clean training days in the same year",
            "holdout_error_MW": {
                name: error_stats([v[i] for _, v in test], [p[j] for p in predicted])
                for j, (name, i) in enumerate((("solar", 8), ("offshore", 9), ("onshore", 10)))
            },
        }
    diagnostics["renewable_models"] = calibration

    generation, generation_total = {}, {}
    for day in DATES:
        rows = raw_agpt[day]
        issues = []
        if not original_fuel.get(day):
            issues.append("missing_generation_date")
        elif all(original_fuel[day][k] == 0 for k in FUELS[:8]):
            issues.append("raw_simultaneous_eight_fuel_zero")
        if day in old_2026_differences:
            issues.append("original_2026_export_difference")
        if len(rows) != 48:
            issues.append("incomplete_AGPT_day")
        if joint_bad[day]:
            issues.append("simultaneous_eight_fuel_zero")
        if original_fuel.get(day, {}).get("Solar") == 0:
            issues.append("zero_daily_solar")
        # Historical full-year endpoint values were midnight records on these dates.
        if day in {"2021-01-01", "2022-01-03", "2023-01-05", "2024-01-07",
                   "2025-01-08", "2026-01-10", "2026-09-17"}:
            issues.append("generation_midnight_snapshot")
        new, methods = [], []
        model = models[day[:4]]
        for i, field in enumerate(FUELS):
            observed = {t: v[i] for t, v in rows.items()
                        if finite(v[i]) and (i >= 8 or t not in joint_bad[day])}
            if len(rows) >= 42 and len(observed) >= 42:
                value = statistics.mean(max(0, interpolate(observed, t)) for t in expected_times(day, 30))
                method = "same_source_daily_mean" if len(observed) == 48 else "same_source_short_interpolation"
                used = ["AGPT"]
            elif i < 8:
                value = fuel_mean[day][i]
                method = "FUELHH_reconstruction"
                if fuel_bad[day]:
                    method += "_interpolated"
                used = ["FUELHH"]
            else:
                if i == 8:
                    value = model[0] * neso_mean[day][2]
                else:
                    value = local_wind_estimate(day, i, renewable_training[day[:4]], fuel_mean, neso_mean)
                method, used = "cross_source_estimate", ["NESO", "FUELHH"] if i > 8 else ["NESO"]
            value = rounded(max(0, value))
            old = original_fuel.get(day, {}).get(field)
            field_issues = issues.copy()
            if old is not None and value != old and not field_issues:
                field_issues.append("refreshed_source_aggregation")
            if "interpol" in method:
                field_issues.append("source_intervals_interpolated")
            if method == "cross_source_estimate":
                field_issues.append("estimated_generation")
            record(day, "generation", field, old, value, method, used, field_issues)
            new.append(value)
            methods.append(method)
        generation[day] = new
        generation_total[day] = sum(new)
        record(day, "generation_total", "total_MW", original_total.get(day), sum(new),
               "sum_of_eleven_repaired_categories", ["AGPT", "FUELHH", "NESO"], issues)

    # Recompute every day from the full VD time grid, rather than query endpoints.
    raw_demand, daily_offsets = {}, {}
    for day in DATES:
        rows = {stamp_minutes(t): v for t, v in source["demand"]["days"].get(day, {}).items()}
        good = {t: v for t, v in rows.items() if finite(v) and v >= LOW_DEMAND}
        raw_demand[day] = good
        differences = [v - neso[day][t - t % 30][0] for t, v in good.items()
                       if neso[day][t - t % 30][0] >= LOW_DEMAND]
        if len(differences) >= 144:
            daily_offsets[day] = statistics.median(differences)
    demand, demand_details = {}, []
    for day in DATES:
        rows, good = source["demand"]["days"].get(day, {}), raw_demand[day]
        targets = expected_times(day, 5)
        issues = []
        if day not in original_demand:
            issues.append("missing_demand_date")
        if day in original_demand and (date.fromisoformat(day).weekday() == 1 or day == END.isoformat()):
            issues.append("demand_midnight_snapshot")
        if len(rows) != 288:
            issues.append("incomplete_VD_day")
        low_count = sum(v < LOW_DEMAND for v in rows.values())
        if low_count:
            issues.append("implausible_VD_interval")
        neighbours = [v for d, v in daily_offsets.items()
                      if abs((date.fromisoformat(d) - date.fromisoformat(day)).days) <= 14]
        background_offset = statistics.median(neighbours)
        replacements, values = [], []
        for t in targets:
            if t in good:
                values.append(good[t])
                continue
            near = [(s, v) for s, v in good.items() if abs(s - t) <= 240]
            diffs = [v - neso[day][s - s % 30][0] for s, v in near
                     if neso[day][s - s % 30][0] >= LOW_DEMAND]
            offset = statistics.median(diffs) if len(diffs) >= 12 else background_offset
            replacement = neso[day][t - t % 30][0] + offset
            if replacement < LOW_DEMAND:
                replacement = interpolate(good, t)
            values.append(replacement)
            replacements.append([t - daily_start(day), rows.get(datetime.fromtimestamp(t * 60, timezone.utc).isoformat().replace("+00:00", "Z")), replacement])
        value = rounded(statistics.mean(values))
        method = "same_source_daily_mean" if not replacements else "VD_plus_calibrated_NESO_TSD"
        if replacements:
            issues.append("estimated_demand_intervals")
        record(day, "demand", "demand", original_demand.get(day), value, method,
               ["VD"] if not replacements else ["VD", "NESO"], issues)
        demand[day] = value
        if replacements:
            demand_details.append({"date": day, "replaced_intervals": replacements,
                                   "observed_interval_count": len(rows), "value_MW": value})
    diagnostics["demand_reconstructions"] = demand_details

    # Calculate a period price only from providers that actually report trades.
    price_points, inactive_counts = {}, Counter()
    for day, records in source["mid"]["days"].items():
        for stamp, providers in records.items():
            active = [(p, v) for p, v in providers.values() if v > 0 and finite(p)]
            inactive_counts[day] += len(providers) - len(active)
            if active:
                price_points[stamp_minutes(stamp)] = sum(p * v for p, v in active) / sum(v for p, v in active)
    known = sorted(price_points)
    price_replay = {"midnight_endpoint_matches": 0, "daily_provider_mean_matches": 0, "rows": len(original_price)}
    for day, original in original_price.items():
        records = source["mid"]["days"][day]
        if date.fromisoformat(day).weekday() == 1 or day == END.isoformat():
            candidates = [p for p, v in records[day + "T00:00:00Z"].values()]
            price_replay["midnight_endpoint_matches"] += abs(statistics.mean(candidates) - original) < 1e-8
        else:
            candidates = [p for providers in records.values() for p, v in providers.values()]
            price_replay["daily_provider_mean_matches"] += abs(statistics.mean(candidates) - original) < 1e-8
    diagnostics["original_price_algorithm_replay"] = price_replay
    price, price_details = {}, []
    for day in DATES:
        targets = expected_times(day, 30)
        native = [t for t in targets if t in price_points]
        issues = []
        if day in original_price and (date.fromisoformat(day).weekday() == 1 or day == END.isoformat()):
            issues.append("price_midnight_snapshot")
        if day not in original_price:
            issues.append("missing_price_date")
        if inactive_counts[day]:
            issues.append("zero_volume_price_placeholder")
        if len(native) != 48:
            issues.append("missing_active_MID_periods")
        if len(native) < 24:
            # Whole-day/long gaps use the average of the nearest observed same-weekday days.
            peers = []
            for delta in (7, -7, 14, -14, 21, -21):
                d = (date.fromisoformat(day) + timedelta(days=delta)).isoformat()
                pts = [price_points[t] for t in expected_times(d, 30) if t in price_points]
                if len(pts) >= 42:
                    peers.append(statistics.mean(pts))
                if len(peers) == 4:
                    break
            value = statistics.mean(peers)
            method = "estimated_same_weekday_price"
        else:
            values = []
            for t in targets:
                if t in price_points:
                    values.append(price_points[t])
                    continue
                index = bisect.bisect_left(known, t)
                left, right = known[max(0, index - 1)], known[min(len(known) - 1, index)]
                values.append(interpolate({left: price_points[left], right: price_points[right]}, t))
            value = statistics.mean(values)
            method = "active_MID_daily_mean" if len(native) == 48 else "active_MID_short_interpolation"
        price[day] = value
        record(day, "price", "avg_price_£_per_MWh", original_price.get(day), value, method, ["MID"], issues)
        old_secondary = original_price.get(day)
        record(day, "price", "avg_price_£_per_MW_day", None if old_secondary is None else old_secondary * 24,
               value * 24, "24_times_repaired_price", ["MID"], issues)
        price_details.append([day, len(native), inactive_counts[day], method, value])
    diagnostics["price_period_coverage"] = price_details
    # Simulation zeros are physically possible with turbine cut-in/cut-out and are retained.
    for day in DATES:
        record(day, "wind_farm", "wind_farm_MW", original_wind[day], original_wind[day],
               "course_simulation_retained", ["course"], ["simulated_wind_zero_reviewed"] if original_wind[day] == 0 else [])

    per_date = defaultdict(list)
    for row in quality:
        per_date[row[0]].append(row)
    daily_quality = []
    for day in DATES:
        methods = {r[3] for r in per_date[day]}
        cross_source = any("reconstruction" in m or "NESO" in m or "cross_source" in m for m in methods)
        estimated = any("interpol" in m or "estimated" in m or "NESO" in m or "cross_source" in m for m in methods)
        daily_quality.append([day, int(cross_source), int(estimated), int(not cross_source and not estimated)])
    diagnostics["quality_panel_counts"] = {
        "cross_source_dates": sum(r[1] for r in daily_quality),
        "estimated_dates": sum(r[2] for r in daily_quality),
        "strict_no_imputation_dates": sum(r[3] for r in daily_quality),
    }
    files = {
        "daily_generation_by_fuel.csv": encoded_csv(["date", "psrType", "MW"],
            [(d, k, generation[d][i]) for d in DATES for i, k in enumerate(FUELS)]),
        "daily_generation_total.csv": encoded_csv(["date", "total_MW"], [(d, generation_total[d]) for d in DATES]),
        "daily_demand.csv": encoded_csv(["recordType", "startTime", "demand"],
            [("VD", d + "T00:00:00Z", demand[d]) for d in DATES]),
        "daily_market_index_price.csv": encoded_csv(["date", "avg_price_£_per_MWh", "avg_price_£_per_MW_day"],
            [(d, price[d], price[d] * 24) for d in DATES]),
        "wind_farm_generation.csv": encoded_csv(["date", "wind_farm_MW"], [(d, original_wind[d]) for d in DATES]),
        "cell_audit.csv": encoded_csv(["date", "series", "field", "original", "repaired", "method", "source_ids", "issue_types"], audit),
        "quality.csv": encoded_csv(["date", "series", "field", "method", "source_ids", "issue_types", "changed"], quality),
        "date_quality.csv": encoded_csv(["date", "uses_cross_source_reconstruction", "uses_estimation_or_interpolation", "strict_no_imputation"], daily_quality),
    }
    diagnostics["sources"] = SOURCE_IDS
    diagnostics["issues"] = {k: sorted(v) for k, v in issue_dates.items()}
    diagnostics["counts"] = {"dates": len(DATES), "audited_cells": len(quality), "audit_rows": len(audit),
                             "issue_dates": {k: len(v) for k, v in issue_dates.items()}}
    diagnostics["output_sha256"] = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
    diagnostics["original_sha256"] = {n: hashlib.sha256((repo / n).read_bytes()).hexdigest()
                                     for n in files if (repo / n).is_file()}
    diagnostics["preserved_wind_zeros"] = [d for d in DATES if original_wind[d] == 0]
    diagnostics["window"] = {"start": DATES[0], "end": DATES[-1], "wind_extra_date_excluded": "2026-09-18"}
    diagnostics["financial_convention"] = "Nominal historical GBP/MWh, with 24 h conversion only in the second price field."
    diagnostics["boundary"] = "Constructed client-system convention. Supplied generation, demand and extra simulated wind are not a reconstructed physical GB energy balance."
    return files, diagnostics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    files, report = repair(args.course_root, here)
    destination = here / "data"
    if args.verify:
        for name, content in files.items():
            if (destination / name).read_bytes() != content:
                raise SystemExit(f"Reproduction differs for {name}")
        print("All eight data and audit files reproduce exactly.")
    else:
        destination.mkdir(exist_ok=True)
        for name, content in files.items():
            (destination / name).write_bytes(content)
        (here / "REPAIR_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
