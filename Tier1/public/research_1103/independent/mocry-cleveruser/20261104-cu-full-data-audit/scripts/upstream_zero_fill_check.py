# -*- coding: utf-8 -*-
"""Verify suspected zero-fill defects and missing dates against live Elexon FUELHH.

Daily mean MW by UTC day from FUELHH (startTime is UTC; settlementDate is local and
would shift BST days by an hour - the bug found earlier).
"""
import json
import csv
import os
import urllib.request
import urllib.error
from collections import defaultdict

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
REPO = os.path.abspath(".")

# course data
gen = defaultdict(dict)
with open(os.path.join(REPO, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        gen[r["date"]][r["psrType"]] = float(r["MW"])
tot = {}
with open(os.path.join(REPO, "daily_generation_total.csv"), encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        tot[r["date"]] = float(r["total_MW"])

TESTS = [
    ("solar_zero", "2021-01-01"), ("solar_zero", "2022-09-18"), ("solar_zero", "2024-01-07"),
    ("solar_zero", "2026-09-17"),
    ("missing_day", "2022-01-27"), ("missing_day", "2020-11-01"),
    ("demand_outlier", "2022-08-02"),
]


def fetch_fuelhh(day):
    url = "%s/datasets/FUELHH?settlementDateFrom=%s&settlementDateTo=%s&format=json" % (BASE, day, day)
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read().decode("utf-8"))
    return body.get("data", [])


out = []
for kind, day in TESTS:
    try:
        rows = fetch_fuelhh(day)
    except Exception as e:  # noqa
        out.append({"kind": kind, "date": day, "error": repr(e)[:200]})
        print(kind, day, "ERR", repr(e)[:150])
        continue
    # restrict to the UTC calendar day, not the settlement day
    acc = defaultdict(list)
    for r in rows:
        if r.get("startTime", "")[:10] != day:
            continue
        if r.get("generation") is None:
            continue
        acc[r["fuelType"]].append(float(r["generation"]))
    upstream = {k: round(sum(v) / len(v), 2) for k, v in acc.items()}
    rec = {
        "kind": kind, "date": day, "n_utc_periods": len(next(iter(acc.values()))) if acc else 0,
        "upstream_fuel_daily_mean": upstream,
        "upstream_total": round(sum(upstream.values()), 2) if upstream else None,
        "course_total": tot.get(day),
        "course_solar": gen.get(day, {}).get("Solar"),
        "course_ps": gen.get(day, {}).get("Hydro Pumped Storage"),
        "course_n_fuels": len(gen.get(day, {})),
    }
    if day in gen:
        # per-fuel comparison
        diff = {}
        for k, v in upstream.items():
            c = gen[day].get(k)
            if c is not None:
                diff[k] = round(c - v, 2)
        rec["course_minus_upstream"] = diff
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False)[:1200])
    print()

json.dump(out, open(os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser", "audit",
                                "upstream_zero_fill.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
