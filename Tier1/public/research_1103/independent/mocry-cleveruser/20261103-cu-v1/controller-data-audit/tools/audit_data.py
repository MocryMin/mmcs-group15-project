#!/usr/bin/env python3
"""Controller-side deterministic audit of the five supplied CSVs.

Every figure here is recomputed from the repository bytes; nothing is copied from
another agent's research. Output: data_audit.json + a short console summary.
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
OUT = REPO / "Tier1/workspaces/mocry/cleveruser/audit"
FILES = [
    "daily_demand.csv",
    "daily_generation_by_fuel.csv",
    "daily_generation_total.csv",
    "daily_market_index_price.csv",
    "wind_farm_generation.csv",
]


def read_rows(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    return raw, rows


def parse_date(value: str) -> date:
    value = value.strip()
    if "T" in value:  # ISO timestamp such as 2020-01-01T00:00:00Z
        value = value.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date: {value!r}")


def segments(dates: list[date]) -> list[dict]:
    out = []
    if not dates:
        return out
    start = prev = dates[0]
    for d in dates[1:]:
        if d - prev == timedelta(days=1):
            prev = d
            continue
        out.append({"start": start.isoformat(), "end": prev.isoformat(),
                    "days": (prev - start).days + 1,
                    "calendar_span_days": (prev - start).days + 1})
        start = prev = d
    out.append({"start": start.isoformat(), "end": prev.isoformat(),
                "days": (prev - start).days + 1,
                "calendar_span_days": (prev - start).days + 1})
    return out


def stats(values: list[float]) -> dict:
    if not values:
        return {}
    s = sorted(values)
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.fmean(values), 4),
        "median": statistics.median(values),
        "p01": s[max(0, int(round(0.01 * (len(s) - 1))))],
        "p99": s[min(len(s) - 1, int(round(0.99 * (len(s) - 1))))],
        "sum": round(sum(values), 4),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "generated_by": "mocry-cleveruser (controller-side deterministic audit)",
        "note": "All values recomputed from the five root CSVs; no inherited figures.",
        "files": {},
    }

    # --- raw file facts -------------------------------------------------------
    parsed: dict[str, dict] = {}
    for name in FILES:
        path = REPO / name
        raw, rows = read_rows(path)
        header = list(rows[0].keys()) if rows else []
        result["files"][name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "data_rows": len(rows),
            "header": header,
        }
        parsed[name] = {"rows": rows, "header": header}

    # --- demand ---------------------------------------------------------------
    demand = parsed["daily_demand.csv"]
    dc, vc = "startTime", "demand"
    record_types = sorted({r["recordType"] for r in demand["rows"]})
    demand_by_date = {}
    dup = []
    for r in demand["rows"]:
        d = parse_date(r[dc])
        if d in demand_by_date:
            dup.append(d.isoformat())
        demand_by_date[d] = float(r[vc])
    result["demand"] = {
        "date_column": dc,
        "value_column": vc,
        "record_type_values": record_types,
        "rows": len(demand["rows"]),
        "unique_dates": len(demand_by_date),
        "duplicate_dates": dup,
        "date_min": min(demand_by_date).isoformat(),
        "date_max": max(demand_by_date).isoformat(),
        "value_stats": stats(list(demand_by_date.values())),
    }

    # --- generation total -----------------------------------------------------
    gen = parsed["daily_generation_total.csv"]
    gc, gv = gen["header"][0], gen["header"][1]
    gen_total = {parse_date(r[gc]): float(r[gv]) for r in gen["rows"]}
    result["generation_total"] = {
        "date_column": gc,
        "value_column": gv,
        "rows": len(gen["rows"]),
        "unique_dates": len(gen_total),
        "date_min": min(gen_total).isoformat(),
        "date_max": max(gen_total).isoformat(),
        "value_stats": stats(list(gen_total.values())),
        "negative_or_zero_days": sum(1 for v in gen_total.values() if v <= 0),
    }

    # --- generation by fuel ---------------------------------------------------
    fuel = parsed["daily_generation_by_fuel.csv"]
    fh = fuel["header"]
    f_dc, fuel_col, val_col = fh[0], fh[1], fh[2]
    per_date = defaultdict(float)
    per_fuel = defaultdict(float)
    fuel_dates = set()
    fuels = set()
    for r in fuel["rows"]:
        d = parse_date(r[f_dc])
        fuel_dates.add(d)
        per_date[d] += float(r[val_col])
        per_fuel[r[fuel_col]] += float(r[val_col])
        fuels.add(r[fuel_col])
    result["generation_by_fuel"] = {
        "columns": fh,
        "rows": len(fuel["rows"]),
        "unique_dates": len(fuel_dates),
        "date_min": min(fuel_dates).isoformat(),
        "date_max": max(fuel_dates).isoformat(),
        "technologies": sorted(fuels),
        "technology_count": len(fuels),
        "technology_totals_MW_summed_over_days": {k: round(v, 3) for k, v in sorted(per_fuel.items())},
    }

    # --- reconciliation fuel sum vs total ------------------------------------
    common_ft = sorted(set(gen_total) & fuel_dates)
    diffs = [abs(per_date[d] - gen_total[d]) for d in common_ft]
    rel = [abs(per_date[d] - gen_total[d]) / gen_total[d] for d in common_ft if gen_total[d]]
    result["fuel_vs_total_reconciliation"] = {
        "common_dates": len(common_ft),
        "dates_only_in_total": len(set(gen_total) - fuel_dates),
        "dates_only_in_fuel": len(fuel_dates - set(gen_total)),
        "max_abs_diff_MW": round(max(diffs), 6) if diffs else None,
        "mean_abs_diff_MW": round(statistics.fmean(diffs), 6) if diffs else None,
        "max_relative_diff": round(max(rel), 12) if rel else None,
        "dates_with_rel_diff_gt_1e-6": sum(1 for x in rel if x > 1e-6),
    }

    # --- prices ---------------------------------------------------------------
    price = parsed["daily_market_index_price.csv"]
    ph = price["header"]
    p_dc = ph[0]
    p_by_date = {}
    for r in price["rows"]:
        p_by_date[parse_date(r[p_dc])] = {k: r[k] for k in ph[1:]}
    price_cols = ph[1:]
    result["prices"] = {
        "date_column": p_dc,
        "value_columns": price_cols,
        "rows": len(price["rows"]),
        "unique_dates": len(p_by_date),
        "date_min": min(p_by_date).isoformat(),
        "date_max": max(p_by_date).isoformat(),
    }
    if len(price_cols) >= 2:
        a, b = price_cols[0], price_cols[1]
        try:
            pa = {d: float(v[a]) for d, v in p_by_date.items()}
            pb = {d: float(v[b]) for d, v in p_by_date.items()}
            diff = {d: pb[d] - 24.0 * pa[d] for d in pa}
            rel = {d: abs(diff[d]) / abs(pb[d]) for d in pb if pb[d]}
            result["prices"]["cols"] = {
                a: stats(list(pa.values())),
                b: stats(list(pb.values())),
                "consistency_24x": {
                    "n": len(diff),
                    "max_abs_diff": round(max(abs(x) for x in diff.values()), 9),
                    "n_days_rel_diff_gt_1e-9": sum(1 for x in rel.values() if x > 1e-9),
                    "note": "GBP per MW-day should equal 24 x GBP per MWh if the two columns are consistent.",
                },
                "negative_price_days": {a: sum(1 for v in pa.values() if v < 0),
                                        b: sum(1 for v in pb.values() if v < 0)},
                "zero_price_days": {a: sum(1 for v in pa.values() if v == 0),
                                    b: sum(1 for v in pb.values() if v == 0)},
            }
        except ValueError as exc:  # non-numeric cell
            result["prices"]["cols_error"] = str(exc)

    # --- wind farm ------------------------------------------------------------
    wind = parsed["wind_farm_generation.csv"]
    wh = wind["header"]
    w_dc = wh[0]
    wind_by_date = {parse_date(r[w_dc]): float(r[wh[1]]) for r in wind["rows"]}
    result["wind_farm"] = {
        "date_column": w_dc,
        "value_column": wh[1],
        "rows": len(wind["rows"]),
        "unique_dates": len(wind_by_date),
        "date_min": min(wind_by_date).isoformat(),
        "date_max": max(wind_by_date).isoformat(),
        "value_stats": stats(list(wind_by_date.values())),
        "negative_days": sum(1 for v in wind_by_date.values() if v < 0),
    }

    # --- common dates and continuity -----------------------------------------
    sets = {"demand": set(demand_by_date), "generation_total": set(gen_total),
            "generation_by_fuel": fuel_dates, "price": set(p_by_date),
            "wind_farm": set(wind_by_date)}
    common = set.intersection(*sets.values())
    common_sorted = sorted(common)
    result["coverage"] = {
        "per_file_dates": {k: len(v) for k, v in sets.items()},
        "common_dates": len(common_sorted),
        "common_date_min": common_sorted[0].isoformat() if common_sorted else None,
        "common_date_max": common_sorted[-1].isoformat() if common_sorted else None,
        "segments": segments(common_sorted),
        "segment_count": len(segments(common_sorted)),
        "missing_dates_between_min_and_max": (
            (common_sorted[-1] - common_sorted[0]).days + 1 - len(common_sorted)) if common_sorted else None,
    }

    # --- combined system view on common dates --------------------------------
    G = {d: gen_total[d] + wind_by_date[d] for d in common_sorted}
    D = {d: demand_by_date[d] for d in common_sorted}
    P = {d: float(p_by_date[d][price_cols[0]]) for d in common_sorted}
    surplus = {d: max(0.0, G[d] - D[d]) for d in common_sorted}
    shortfall = {d: max(0.0, D[d] - G[d]) for d in common_sorted}
    hours = 24.0
    result["combined_system"] = {
        "definition": "G = total_MW + wind_farm_MW; D = demand; both treated as average MW over the day; MWh = 24 x MW assuming a constant daily mean.",
        "G_stats": stats([G[d] for d in common_sorted]),
        "D_stats": stats([D[d] for d in common_sorted]),
        "days_G_gt_D": sum(1 for d in common_sorted if G[d] > D[d]),
        "share_days_G_gt_D": round(sum(1 for d in common_sorted if G[d] > D[d]) / len(common_sorted), 4),
        "total_surplus_MWh_over_window": round(sum(surplus.values()) * hours, 1),
        "total_shortfall_MWh_over_window": round(sum(shortfall.values()) * hours, 1),
        "mean_annual_surplus_MWh": round(sum(surplus.values()) * hours * 365.0 / len(common_sorted), 1),
        "surplus_MWh_stats": stats([surplus[d] * hours for d in common_sorted]),
        "total_G_MWh": round(sum(G.values()) * hours, 1),
        "total_D_MWh": round(sum(D.values()) * hours, 1),
        "surplus_as_share_of_G": round(sum(surplus.values()) / sum(G.values()), 4),
        "surplus_as_share_of_D": round(sum(surplus.values()) / sum(D.values()), 4),
        "price_stats_on_common": stats([P[d] for d in common_sorted]),
        "price_negative_days_common": sum(1 for d in common_sorted if P[d] < 0),
        "value_of_surplus_if_sold_at_price_GBP": round(sum(surplus[d] * hours * P[d] for d in common_sorted), 1),
    }

    # --- extreme days ---------------------------------------------------------
    ranked = sorted(common_sorted, key=lambda d: surplus[d], reverse=True)[:5]
    result["combined_system"]["top5_surplus_days"] = [
        {"date": d.isoformat(), "G_MW": round(G[d], 2), "D_MW": round(D[d], 2),
         "surplus_MWh": round(surplus[d] * hours, 1), "price_GBP_per_MWh": P[d]} for d in ranked]
    lowest_demand = sorted(common_sorted, key=lambda d: D[d])[:3]
    result["combined_system"]["three_lowest_demand_days"] = [
        {"date": d.isoformat(), "D_MW": D[d], "rank_median_D": None} for d in lowest_demand]
    priciest = sorted(common_sorted, key=lambda d: P[d], reverse=True)[:3]
    result["combined_system"]["three_highest_price_days"] = [
        {"date": d.isoformat(), "price": P[d]} for d in priciest]

    (OUT / "data_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    # console summary
    print("files:", len(result["files"]))
    print("common dates:", result["coverage"]["common_dates"],
          "segments:", result["coverage"]["segment_count"],
          "range:", result["coverage"]["common_date_min"], "->", result["coverage"]["common_date_max"])
    rec = result["fuel_vs_total_reconciliation"]
    print("fuel-vs-total: max_abs_diff", rec["max_abs_diff_MW"], "rel>1e-6 dates", rec["dates_with_rel_diff_gt_1e-6"])
    if "cols" in result["prices"]:
        print("price 24x check:", result["prices"]["cols"]["consistency_24x"])
    cs = result["combined_system"]
    print("G>D days:", cs["days_G_gt_D"], "surplus share of G:", cs["surplus_as_share_of_G"],
          "total surplus MWh:", cs["total_surplus_MWh_over_window"],
          "mean annual:", cs["mean_annual_surplus_MWh"])
    print("negative price days (common):", cs["price_negative_days_common"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
