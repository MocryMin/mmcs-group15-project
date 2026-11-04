# -*- coding: utf-8 -*-
"""Determine which aggregation (UTC day vs settlement day) and source reproduces the
course daily generation series. Compares FUELHH and AGPT for a small date window."""
import csv
import json
import os
import urllib.request
from collections import defaultdict

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
REPO = os.path.abspath(".")
WINDOW = ["2022-07-31", "2022-08-01", "2022-08-02", "2022-08-03", "2022-08-04"]

gen = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="")):
    gen[r["date"]][r["psrType"]] = float(r["MW"])


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8")).get("data", [])


rows = get("%s/datasets/FUELHH?settlementDateFrom=%s&settlementDateTo=%s&format=json"
           % (BASE, WINDOW[0], WINDOW[-1]))
print("FUELHH rows", len(rows), "keys", list(rows[0]) if rows else None)

by_utc = defaultdict(lambda: defaultdict(list))
by_sd = defaultdict(lambda: defaultdict(list))
for r in rows:
    if r.get("generation") is None:
        continue
    v = float(r["generation"])
    by_utc[r["startTime"][:10]][r["fuelType"]].append(v)
    by_sd[r["settlementDate"]][r["fuelType"]].append(v)


def means(d):
    return {k: round(sum(v) / len(v), 2) for k, v in d.items()}


for day in WINDOW:
    print("\n==", day)
    u = means(by_utc.get(day, {}))
    s = means(by_sd.get(day, {}))
    c = gen.get(day, {})
    print(" course:", {k: c.get(k) for k in sorted(c)})
    print(" UTCday:", {k: u.get(k) for k in sorted(u)})
    print(" setlDy:", {k: s.get(k) for k in sorted(s)})

# AGPT check
print("\n=== AGPT ===")
try:
    agpt = get("%s/datasets/AGPT?PublishDateTimeFrom=2022-08-02T00:00Z&PublishDateTimeTo=2022-08-03T00:00Z&format=json" % BASE)
    print("rows", len(agpt), "keys", list(agpt[0]) if agpt else None)
    acc = defaultdict(lambda: defaultdict(list))
    for r in agpt:
        if r.get("quantity") is None:
            continue
        acc[r["startTime"][:10]][r["fuelType"]].append(float(r["quantity"]))
    for day in ("2022-08-02",):
        m = means(acc.get(day, {}))
        print(day, "AGPT UTC:", {k: m[k] for k in sorted(m)})
        print(day, "course  :", {k: gen.get(day, {}).get(k) for k in sorted(m)})
except Exception as e:  # noqa
    print("AGPT ERR", repr(e)[:300])
