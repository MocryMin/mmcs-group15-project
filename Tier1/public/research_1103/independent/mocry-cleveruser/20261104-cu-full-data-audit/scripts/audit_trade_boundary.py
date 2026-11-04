# -*- coding: utf-8 -*-
"""Decisive test: is (course generation - course demand) a net-trade balance?

FUELHH publishes interconnector flows as pseudo-fuels (INT*), positive = flow into GB.
Also runs a control sample: course vs live AGPT daily totals on ordinary days.
"""
import csv
import json
import os
import statistics
import urllib.request
from collections import defaultdict

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
REPO = os.path.abspath(".")
AUD = os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser", "audit")

tot = {r["date"]: float(r["total_MW"])
       for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_total.csv"), encoding="utf-8", newline=""))}
dem = {r["startTime"][:10]: float(r["demand"])
       for r in csv.DictReader(open(os.path.join(REPO, "daily_demand.csv"), encoding="utf-8", newline=""))}
gen = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="")):
    gen[r["date"]][r["psrType"]] = float(r["MW"])

TESTS = ["2020-06-23", "2021-04-27", "2022-03-15", "2022-12-12", "2023-11-21",
         "2024-01-09", "2024-06-01", "2025-02-04", "2026-01-20", "2026-08-11"]
CONTROL = ["2022-03-15", "2022-11-08", "2023-06-12", "2023-10-03",
           "2024-05-20", "2025-07-15", "2026-03-10", "2021-09-15"]


def fetch(ds, day, extra=""):
    url = "%s/datasets/%s?settlementDateFrom=%s&settlementDateTo=%s&format=json%s" % (BASE, ds, day, day, extra)
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("data", [])


def fuelhh_utc(day):
    rows = fetch("FUELHH", day)
    acc = defaultdict(list)
    for r in rows:
        if r.get("generation") is None or r["startTime"][:10] != day:
            continue
        acc[r["fuelType"]].append(float(r["generation"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


def agpt_utc(day):
    rows = fetch("AGPT", day, "&PublishDateTimeFrom=%sT00:00Z&PublishDateTimeTo=%sT23:59Z" % (day, day))
    acc = defaultdict(list)
    for r in rows:
        if r.get("quantity") is None or r["startTime"][:10] != day:
            continue
        acc[r["psrType"]].append(float(r["quantity"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


res = {"trade_test": [], "control": []}
for d in TESTS:
    f = fuelhh_utc(d)
    ints = {k: v for k, v in f.items() if k.startswith("INT")}
    net_import = sum(ints.values())
    domestic = sum(v for k, v in f.items() if not k.startswith("INT"))
    rec = {
        "date": d,
        "course_total": tot.get(d), "course_demand": dem.get(d),
        "course_gap_MW": round(tot[d] - dem[d], 1) if d in tot and d in dem else None,
        "upstream_net_import_MW": round(net_import, 1),
        "upstream_import_links": {k: round(v, 1) for k, v in sorted(ints.items())},
        "upstream_domestic_sum_MW": round(domestic, 1),
        "upstream_total_incl_trade_MW": round(domestic + net_import, 1),
        "course_gen_minus_upstream_domestic": round(tot[d] - domestic, 1) if d in tot else None,
    }
    res["trade_test"].append(rec)
    print(json.dumps(rec, ensure_ascii=False)[:900])
    print()

pairs = [(r["course_gap_MW"], -r["upstream_net_import_MW"]) for r in res["trade_test"] if r["course_gap_MW"] is not None]
if len(pairs) > 2:
    xs = [p[1] for p in pairs]
    ys = [p[0] for p in pairs]
    res["trade_test_summary"] = {
        "n": len(pairs),
        "corr_gap_vs_minus_net_import": round(statistics.correlation(xs, ys), 4),
        "mean_abs_residual_MW": round(statistics.fmean([abs(y - x) for x, y in zip(xs, ys)]), 1),
        "slope_ls": round(sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs), 3),
    }
    print("trade summary:", res["trade_test_summary"])

for d in CONTROL:
    try:
        m = agpt_utc(d)
    except Exception as e:  # noqa
        res["control"].append({"date": d, "error": repr(e)[:150]})
        continue
    s = sum(m.values())
    rec = {"date": d, "course_total": tot.get(d), "agpt_total": round(s, 1),
           "pct_diff": round(100 * (tot[d] - s) / s, 2) if s else None, "n_types": len(m)}
    res["control"].append(rec)
    print("control", rec)

cs = [r["pct_diff"] for r in res["control"] if r.get("pct_diff") is not None]
if cs:
    res["control_summary"] = {"n": len(cs), "min_pct": min(cs), "max_pct": max(cs),
                              "mean_pct": round(statistics.fmean(cs), 2),
                              "mean_abs_pct": round(statistics.fmean([abs(c) for c in cs]), 2)}

json.dump(res, open(os.path.join(AUD, "trade_boundary_test.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\ncontrol summary:", res.get("control_summary"))
