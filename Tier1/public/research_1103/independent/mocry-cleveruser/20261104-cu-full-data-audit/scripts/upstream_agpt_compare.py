# -*- coding: utf-8 -*-
"""Compare the course generation series against AGPT (psrType/quantity) directly."""
import csv
import json
import os
import urllib.request
from collections import defaultdict

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
REPO = os.path.abspath(".")

gen = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="")):
    gen[r["date"]][r["psrType"]] = float(r["MW"])
tot = {r["date"]: float(r["total_MW"])
       for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_total.csv"), encoding="utf-8", newline=""))}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("data", [])


for day in ("2022-08-01", "2022-08-02", "2024-01-07", "2026-09-17"):
    rows = get("%s/datasets/AGPT?PublishDateTimeFrom=%sT00:00Z&PublishDateTimeTo=%sT23:59Z&format=json"
               % (BASE, day, day))
    acc = defaultdict(lambda: defaultdict(list))
    psr = set()
    for r in rows:
        psr.add(r.get("psrType"))
        if r.get("quantity") is None:
            continue
        acc[r["startTime"][:10]][r["psrType"]].append(float(r["quantity"]))
    m = {k: round(sum(v) / len(v), 2) for k, v in acc.get(day, {}).items()}
    c = gen.get(day, {})
    print("\n==", day, "AGPT rows", len(rows), "psrTypes", sorted(p for p in psr if p))
    keys = sorted(set(m) | set(c))
    for k in keys:
        print("   %-34s course=%-8s agpt=%s" % (k, c.get(k), m.get(k)))
    print("   totals: course", tot.get(day), "agpt_sum", round(sum(m.values()), 1),
          "agpt_n", len(m))
