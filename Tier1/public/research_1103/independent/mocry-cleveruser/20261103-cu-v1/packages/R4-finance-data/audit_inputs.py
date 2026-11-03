#!/usr/bin/env python3
"""Independent audit of the five supplied MMCS project CSVs.

Package R4 (miscellaneous data, finance, implementation), gap IDs D-01..D-03.
Reads the byte-identical input copies in .../cleveruser/inputs/ and writes a
machine-readable audit to audit_results.json plus a text summary to
audit_summary.txt.  Nothing is cleaned, rewritten or copied: raw files are only
opened read-only.

Method (also stated in REPORT.md):
  * every file is hashed (sha256) and counted (bytes, data rows);
  * the date field of each file is parsed exactly as supplied
    (daily_demand.csv uses startTime "...T00:00:00Z", others a plain ISO date);
  * duplicate dates are counted, missing calendar days inside the file's own
    first..last range are listed;
  * numeric fields are parsed with float(); empty or non-numeric cells are
    counted separately, never silently coerced;
  * the fuel-level table is reconciled day by day against daily_generation_total.csv
    by summing the 11 psrType rows of each date;
  * the two price columns are checked row by row against the 24-hour identity
    per_MW_day = per_MWh * 24;
  * extremes are described by quantiles and by a robust median/MAD z-score
    (|z| > 6 flagged), never by deleting anything;
  * the common-date intersection of the five series is computed together with
    its maximal calendar-continuous segments and the intervening gaps.

Usage:  python audit_inputs.py [--inputs DIR] [--out DIR]
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

FILES = {
    "daily_demand.csv": {
        "date_col": "startTime",
        "date_kind": "iso_z",
        "value_cols": ["demand"],
        "id_cols": ["recordType"],
    },
    "daily_generation_total.csv": {
        "date_col": "date",
        "date_kind": "date",
        "value_cols": ["total_MW"],
        "id_cols": [],
    },
    "daily_generation_by_fuel.csv": {
        "date_col": "date",
        "date_kind": "date",
        "value_cols": ["MW"],
        "id_cols": ["psrType"],
    },
    "wind_farm_generation.csv": {
        "date_col": "date",
        "date_kind": "date",
        "value_cols": ["wind_farm_MW"],
        "id_cols": [],
    },
    "daily_market_index_price.csv": {
        "date_col": "date",
        "date_kind": "date",
        "value_cols": ["avg_price_\u00a3_per_MWh", "avg_price_\u00a3_per_MW_day"],
        "id_cols": [],
    },
}


def parse_date(raw, kind):
    raw = raw.strip()
    if kind == "iso_z":
        return dt.date.fromisoformat(raw.replace("Z", "").split("T")[0])
    return dt.date.fromisoformat(raw)


def quantile(sorted_vals, q):
    """Linear-interpolation quantile on an already sorted list (0..1)."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def describe(vals, dates):
    """Summary statistics + extreme rows for one numeric column."""
    if not vals:
        return {"n": 0}
    n = len(vals)
    mean = sum(vals) / n
    sd = statistics.pstdev(vals) if n > 1 else 0.0
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) if n > 1 else 0.0
    sigma_mad = 1.4826 * mad if mad > 0 else 0.0
    order = sorted(vals)
    out = {
        "n": n,
        "min": min(vals),
        "max": max(vals),
        "mean": round(mean, 6),
        "stdev": round(sd, 6),
        "median": med,
        "mad": mad,
        "p001": quantile(order, 0.001),
        "p01": quantile(order, 0.01),
        "p99": quantile(order, 0.99),
        "p999": quantile(order, 0.999),
        "n_zero": sum(1 for v in vals if v == 0),
        "n_negative": sum(1 for v in vals if v < 0),
    }
    idx_sorted = sorted(range(n), key=lambda i: vals[i])
    out["lowest_5"] = [
        {"date": dates[i].isoformat(), "value": vals[i]} for i in idx_sorted[:5]
    ]
    out["highest_5"] = [
        {"date": dates[i].isoformat(), "value": vals[i]} for i in idx_sorted[-5:][::-1]
    ]
    if sigma_mad > 0:
        out["n_robust_z_gt6"] = sum(1 for v in vals if abs(v - med) / sigma_mad > 6)
        out["robust_z_gt6_dates"] = [
            dates[i].isoformat()
            for i in range(n)
            if abs(vals[i] - med) / sigma_mad > 6
        ][:20]
    else:
        out["n_robust_z_gt6"] = 0
    return out


def contiguous_runs(sorted_dates):
    """Maximal runs of consecutive calendar days."""
    runs = []
    if not sorted_dates:
        return runs
    start = prev = sorted_dates[0]
    for d in sorted_dates[1:]:
        if (d - prev).days == 1:
            prev = d
            continue
        runs.append({"start": start.isoformat(), "end": prev.isoformat(),
                     "days": (prev - start).days + 1})
        start = prev = d
    runs.append({"start": start.isoformat(), "end": prev.isoformat(),
                 "days": (prev - start).days + 1})
    return runs


def audit_file(path, spec, sha_cache):
    raw = open(path, "rb").read()
    sha_cache[os.path.basename(path)] = hashlib.sha256(raw).hexdigest()
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    dates, values = [], {c: [] for c in spec["value_cols"]}
    bad_numeric = {c: 0 for c in spec["value_cols"]}
    empty_cells = {c: 0 for c in spec["value_cols"]}
    date_parse_errors = 0
    extra_id = defaultdict(Counter)
    for r in rows:
        try:
            d = parse_date(r[spec["date_col"]], spec["date_kind"])
        except Exception:
            date_parse_errors += 1
            continue
        dates.append(d)
        for c in spec["value_cols"]:
            cell = (r.get(c) or "").strip()
            if cell == "":
                empty_cells[c] += 1
                continue
            try:
                values[c].append(float(cell))
            except ValueError:
                bad_numeric[c] += 1
        for c in spec["id_cols"]:
            extra_id[c][r[c]] += 1
    date_counts = Counter(dates)
    dup_dates = sorted([d for d, n in date_counts.items() if n > 1])
    uniq = sorted(date_counts)
    span_days = (uniq[-1] - uniq[0]).days + 1 if uniq else 0
    missing = []
    if uniq:
        present = set(uniq)
        cur = uniq[0]
        while cur <= uniq[-1]:
            if cur not in present:
                missing.append(cur)
            cur += dt.timedelta(days=1)
    result = {
        "path": os.path.basename(path),
        "bytes": len(raw),
        "sha256": sha_cache[os.path.basename(path)],
        "data_rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "date_first": uniq[0].isoformat() if uniq else None,
        "date_last": uniq[-1].isoformat() if uniq else None,
        "distinct_dates": len(uniq),
        "span_calendar_days": span_days,
        "duplicate_date_rows": len(rows) - len(uniq),
        "duplicate_dates": [d.isoformat() for d in dup_dates[:20]],
        "n_duplicate_dates": len(dup_dates),
        "missing_calendar_days_in_span": len(missing),
        "missing_calendar_days_first30": [d.isoformat() for d in missing[:30]],
        "date_parse_errors": date_parse_errors,
        "empty_value_cells": empty_cells,
        "non_numeric_value_cells": bad_numeric,
        "id_column_counts": {c: dict(v) for c, v in extra_id.items()},
        "value_stats": {c: describe(values[c], dates) for c in spec["value_cols"]},
    }
    if spec["value_cols"]:
        result["value_pairs"] = len(values[spec["value_cols"][0]])
    result["_dates"] = uniq
    return result, values, dates


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--inputs", default=os.path.normpath(os.path.join(here, "..", "..", "inputs")))
    ap.add_argument("--out", default=here)
    args = ap.parse_args()

    audit = {"inputs_dir": os.path.abspath(args.inputs), "files": {}, "checks": {}}
    sha_cache = {}
    per_date_values = {}
    date_sets = {}

    for fname, spec in FILES.items():
        path = os.path.join(args.inputs, fname)
        if not os.path.exists(path):
            audit["files"][fname] = {"error": "missing input file"}
            continue
        res, values, dates = audit_file(path, spec, sha_cache)
        audit["files"][fname] = {k: v for k, v in res.items() if k != "_dates"}
        date_sets[fname] = set(res["_dates"])
        per_date_values[fname] = values

    # ---------- fuel vs total reconciliation ----------
    by_date = defaultdict(float)
    fuel_rows = defaultdict(int)
    psr_types = Counter()
    dup_pairs = defaultdict(int)
    with open(os.path.join(args.inputs, "daily_generation_by_fuel.csv"),
              "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            d = r["date"].strip()
            psr_types[r["psrType"]] += 1
            dup_pairs[(d, r["psrType"])] += 1
            by_date[d] += float(r["MW"])
            fuel_rows[d] += 1
    total = {}
    with open(os.path.join(args.inputs, "daily_generation_total.csv"),
              "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            total[r["date"].strip()] = float(r["total_MW"])
    common = sorted(set(by_date) & set(total))
    diffs = [(d, by_date[d], total[d], by_date[d] - total[d]) for d in common]
    exact = [x for x in diffs if abs(x[3]) < 1e-9]
    nonzero = [x for x in diffs if abs(x[3]) >= 1e-9]
    audit["checks"]["fuel_vs_total"] = {
        "fuel_distinct_dates": len(by_date),
        "total_distinct_dates": len(total),
        "common_dates": len(common),
        "fuel_only_dates": sorted(set(by_date) - set(total))[:20],
        "total_only_dates": sorted(set(total) - set(by_date))[:20],
        "dates_summing_exactly": len(exact),
        "dates_with_nonzero_difference": len(nonzero),
        "max_abs_difference_MW": round(max((abs(x[3]) for x in diffs), default=0.0), 9),
        "example_nonzero_differences": [
            {"date": d, "fuel_sum_MW": a, "total_MW": b, "diff_MW": round(c, 6)}
            for d, a, b, c in nonzero[:10]
        ],
        "fuel_rows_per_date": dict(Counter(fuel_rows.values())),
        "psrType_row_counts": dict(psr_types),
        "duplicate_date_psrType_pairs": sum(1 for v in dup_pairs.values() if v > 1),
    }

    # ---------- price column consistency ----------
    price = {"n": 0, "n_ratio_24": 0, "n_ratio_other": 0,
             "max_rel_dev_from_24": 0.0, "examples": []}
    with open(os.path.join(args.inputs, "daily_market_index_price.csv"),
              "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            a = float(r["avg_price_\u00a3_per_MWh"])
            b = float(r["avg_price_\u00a3_per_MW_day"])
            price["n"] += 1
            if a == 0 and b == 0:
                price["n_ratio_24"] += 1
                continue
            if a == 0:
                price["n_ratio_other"] += 1
                if len(price["examples"]) < 10:
                    price["examples"].append({"date": r["date"], "per_MWh": a, "per_MW_day": b,
                                              "ratio": None})
                continue
            ratio = b / a
            dev = abs(ratio - 24.0)
            price["max_rel_dev_from_24"] = max(price["max_rel_dev_from_24"], dev / 24.0)
            if dev < 1e-9:
                price["n_ratio_24"] += 1
            else:
                price["n_ratio_other"] += 1
                if len(price["examples"]) < 10:
                    price["examples"].append({"date": r["date"], "per_MWh": a,
                                              "per_MW_day": b, "ratio": ratio})
    audit["checks"]["price_column_identity"] = price

    # ---------- common-date intersection + segments ----------
    order = ["daily_generation_total.csv", "daily_demand.csv",
             "daily_market_index_price.csv", "wind_farm_generation.csv"]
    inter = set.intersection(*[date_sets[f] for f in order + ["daily_generation_by_fuel.csv"]])
    inter_sorted = sorted(inter)
    union_span = sorted(set().union(*[date_sets[f] for f in order + ["daily_generation_by_fuel.csv"]]))
    runs = contiguous_runs(inter_sorted)
    gaps = []
    for a, b in zip(inter_sorted, inter_sorted[1:]):
        if (b - a).days > 1:
            gaps.append({"after": a.isoformat(), "before": b.isoformat(),
                         "missing_days": (b - a).days - 1})
    audit["checks"]["date_intersection"] = {
        "series_compared": order + ["daily_generation_by_fuel.csv"],
        "n_common_dates": len(inter_sorted),
        "first": inter_sorted[0].isoformat() if inter_sorted else None,
        "last": inter_sorted[-1].isoformat() if inter_sorted else None,
        "n_continuous_segments": len(runs),
        "segments": runs,
        "n_gaps": len(gaps),
        "gaps": gaps,
        "sum_days_in_segments": sum(r["days"] for r in runs),
        "per_file_date_counts": {f: len(date_sets[f]) for f in date_sets},
        "n_union_dates": len(union_span),
        "union_first": union_span[0].isoformat() if union_span else None,
        "union_last": union_span[-1].isoformat() if union_span else None,
    }

    # ---------- pairwise date differences (files do not drop the same days) ----------
    pair = {}
    for a in date_sets:
        for b in date_sets:
            if a == b:
                continue
            only = sorted(date_sets[a] - date_sets[b])
            pair["%s|%s" % (a, b)] = {
                "n_dates_in_first_not_second": len(only),
                "dates_first20": [d.isoformat() for d in only[:20]],
            }
    audit["checks"]["pairwise_date_differences"] = pair

    # ---------- implied daily energy on the common dates ----------
    fuel = per_date_values["daily_generation_total.csv"]["total_MW"]
    wind = per_date_values["wind_farm_generation.csv"]["wind_farm_MW"]
    dem = per_date_values["daily_demand.csv"]["demand"]
    price_v = per_date_values["daily_market_index_price.csv"]["avg_price_\u00a3_per_MWh"]
    gen_map = dict(zip(date_sets_gen := sorted(date_sets["daily_generation_total.csv"]), fuel))
    wind_map = dict(zip(sorted(date_sets["wind_farm_generation.csv"]), wind))
    dem_map = dict(zip(sorted(date_sets["daily_demand.csv"]), dem))
    p_map = dict(zip(sorted(date_sets["daily_market_index_price.csv"]), price_v))
    rows = []
    for d in inter_sorted:
        g = gen_map[d] + wind_map[d]
        rows.append((d, g, dem_map[d], p_map[d]))
    surplus_days = sum(1 for _, g, dd, _ in rows if g > dd)
    deficit_days = sum(1 for _, g, dd, _ in rows if g < dd)
    tot_g = sum(g * 24.0 for _, g, _, _ in rows)          # MWh, 24 h per day
    tot_d = sum(dd * 24.0 for _, _, dd, _ in rows)
    neg_price_days = [d.isoformat() for d, _, _, p in rows if p < 0]
    audit["checks"]["common_date_system"] = {
        "note": "energy_MWh = MW * 24 for every calendar day (24 h convention); "
                "generation here = total_MW + wind_farm_MW, the Baseline 1103 connection",
        "n_dates": len(rows),
        "generation_MWh_total": round(tot_g, 1),
        "demand_MWh_total": round(tot_d, 1),
        "mean_generation_MW": round(tot_g / (24.0 * len(rows)), 3),
        "mean_demand_MW": round(tot_d / (24.0 * len(rows)), 3),
        "days_generation_gt_demand": surplus_days,
        "days_generation_lt_demand": deficit_days,
        "max_surplus_day": max(((d.isoformat(), round((g - dd) * 24.0, 1))
                                for d, g, dd, _ in rows), key=lambda x: x[1]),
        "max_deficit_day": min(((d.isoformat(), round((g - dd) * 24.0, 1))
                                for d, g, dd, _ in rows), key=lambda x: x[1]),
        "negative_price_days_on_intersection": len(neg_price_days),
        "negative_price_dates_first10": neg_price_days[:10],
        "n_negative_price_days_all": audit["files"]["daily_market_index_price.csv"]
            ["value_stats"]["avg_price_\u00a3_per_MWh"].get("n_negative"),
    }

    # ---------- annual price and generation/demand context ----------
    ann = defaultdict(lambda: {"n": 0, "price_sum": 0.0, "gen_sum": 0.0, "dem_sum": 0.0})
    for d, g, dd, p in rows:
        a = ann[d.year]
        a["n"] += 1
        a["price_sum"] += p
        a["gen_sum"] += g
        a["dem_sum"] += dd
    audit["checks"]["annual_context"] = {
        str(y): {
            "n_common_days": v["n"],
            "mean_price_gbp_per_MWh": round(v["price_sum"] / v["n"], 3),
            "mean_generation_MW": round(v["gen_sum"] / v["n"], 1),
            "mean_demand_MW": round(v["dem_sum"] / v["n"], 1),
        }
        for y, v in sorted(ann.items())
    }

    audit["file_sha256"] = sha_cache
    out_json = os.path.join(args.out, "audit_results.json")
    with open(out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(audit, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # ---------- human-readable summary ----------
    lines = []
    w = lines.append
    w("AUDIT SUMMARY - five supplied MMCS CSVs (package R4, D-01..D-03)")
    w("inputs dir: %s" % audit["inputs_dir"])
    w("")
    for fname in FILES:
        f = audit["files"].get(fname, {})
        if "error" in f:
            w("%-32s MISSING" % fname)
            continue
        w("%-32s rows=%-6d dates=%-5d %s..%s  dup_date_rows=%d  missing_in_span=%d  bytes=%d"
          % (fname, f["data_rows"], f["distinct_dates"], f["date_first"], f["date_last"],
             f["duplicate_date_rows"], f["missing_calendar_days_in_span"], f["bytes"]))
        for c, st in f["value_stats"].items():
            w("    %-28s n=%d min=%.6g max=%.6g mean=%.6g median=%.6g neg=%d zero=%d"
              % (c, st["n"], st["min"], st["max"], st["mean"], st["median"],
                 st["n_negative"], st["n_zero"]))
        w("    sha256=%s" % f["sha256"])
    w("")
    fv = audit["checks"]["fuel_vs_total"]
    w("FUEL vs TOTAL: common=%d equal=%d differ=%d max|diff|=%.6g MW; rows/date=%s; psrTypes=%d"
      % (fv["common_dates"], fv["dates_summing_exactly"],
         fv["dates_with_nonzero_difference"], fv["max_abs_difference_MW"],
         fv["fuel_rows_per_date"], len(fv["psrType_row_counts"])))
    pc = audit["checks"]["price_column_identity"]
    w("PRICE IDENTITY b/a=24: n=%d ok=%d deviating=%d max_rel_dev=%.3g"
      % (pc["n"], pc["n_ratio_24"], pc["n_ratio_other"], pc["max_rel_dev_from_24"]))
    di = audit["checks"]["date_intersection"]
    w("INTERSECTION: n=%d (%s..%s) segments=%d gaps=%d"
      % (di["n_common_dates"], di["first"], di["last"],
         di["n_continuous_segments"], di["n_gaps"]))
    for r in di["segments"]:
        w("    segment %s..%s  days=%d" % (r["start"], r["end"], r["days"]))
    for g in di["gaps"]:
        w("    gap after %s before %s  missing=%d" % (g["after"], g["before"], g["missing_days"]))
    cs = audit["checks"]["common_date_system"]
    w("SYSTEM on intersection: gen=%.0f MWh dem=%.0f MWh meanG=%.1f MW meanD=%.1f MW "
      "surplus_days=%d deficit_days=%d neg_price_days=%d"
      % (cs["generation_MWh_total"], cs["demand_MWh_total"], cs["mean_generation_MW"],
         cs["mean_demand_MW"], cs["days_generation_gt_demand"], cs["days_generation_lt_demand"],
         cs["negative_price_days_on_intersection"]))
    w("ANNUAL: " + "; ".join("%s n=%d price=%.2f G=%.0f D=%.0f" %
                             (y, v["n_common_days"], v["mean_price_gbp_per_MWh"],
                              v["mean_generation_MW"], v["mean_demand_MW"])
                             for y, v in audit["checks"]["annual_context"].items()))
    text = "\n".join(lines) + "\n"
    with open(os.path.join(args.out, "audit_summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write(text)
    sys.stdout.write("\nwrote %s\n" % out_json)


if __name__ == "__main__":
    main()
