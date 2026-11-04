# -*- coding: utf-8 -*-
"""Random-sample regression: what is (course generation - course demand)?

Sample clean dates only (exclude the 107 repair days, the 41 solar-zero days,
2022-08-02, and the 30 dates without generation).
For each date: FUELHH net interconnector flow, AGPT total (fidelity check).
"""
import csv
import json
import os
import random
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

a1 = json.load(open(os.path.join(AUD, "all_data_audit.json"), encoding="utf-8"))
a2 = json.load(open(os.path.join(AUD, "all_data_audit2.json"), encoding="utf-8"))
repair = set(a1["repair"]["changed_dates"])
solar_zero = set(a2["solar_zero_dates"])
missing = set(a1["series"]["generation_by_fuel"]["missing_calendar_days"])

bad = repair | solar_zero | missing | {"2022-08-02"}
clean = sorted(d for d in set(tot) & set(dem) if d not in bad)
print("clean days:", len(clean))

random.seed(20261104)
late = [d for d in clean if d >= "2022-01-01"]
early = [d for d in clean if d < "2022-01-01"]
sample_late = sorted(random.sample(late, 50))
sample_early = sorted(random.sample(early, 10))
sample = sample_late + sample_early


def fetch(ds, day, extra=""):
    url = "%s/datasets/%s?settlementDateFrom=%s&settlementDateTo=%s&format=json%s" % (BASE, ds, day, day, extra)
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("data", [])


def mean_by(rows, key, val, day):
    acc = defaultdict(list)
    for r in rows:
        if r.get(val) is None or r["startTime"][:10] != day:
            continue
        acc[r[key]].append(float(r[val]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


rows_out = []
for d in sample:
    try:
        f = mean_by(fetch("FUELHH", d), "fuelType", "generation", d)
    except Exception as e:  # noqa
        rows_out.append({"date": d, "error_f": repr(e)[:120]})
        continue
    ni = sum(v for k, v in f.items() if k.startswith("INT"))
    dom = sum(v for k, v in f.items() if not k.startswith("INT"))
    rec = {
        "date": d,
        "course_total": tot[d], "course_demand": dem[d],
        "gap": round(tot[d] - dem[d], 1),
        "fus_net_import": round(ni, 1),
        "fus_domestic": round(dom, 1),
        "fus_wind": round(f.get("WIND", 0.0), 1),
        "course_wind": round(gen[d].get("Wind Onshore", 0) + gen[d].get("Wind Offshore", 0), 1),
        "course_solar": gen[d].get("Solar"),
    }
    if d >= "2022-01-01":
        try:
            a = mean_by(fetch("AGPT", d, "&PublishDateTimeFrom=%sT00:00Z&PublishDateTimeTo=%sT23:59Z" % (d, d)),
                        "psrType", "quantity", d)
            rec["agpt_total"] = round(sum(a.values()), 1) if a else None
            rec["agpt_solar"] = round(a.get("Solar", 0.0), 1) if a else None
            if rec["agpt_total"]:
                rec["fidelity_pct"] = round(100 * (tot[d] - rec["agpt_total"]) / rec["agpt_total"], 2)
        except Exception as e:  # noqa
            rec["agpt_err"] = repr(e)[:120]
    rec["E_gap_plus_netimport"] = round(rec["gap"] + rec["fus_net_import"], 1)
    rows_out.append(rec)
    print(json.dumps(rec, ensure_ascii=False))

# ---- summaries
ok = [r for r in rows_out if "gap" in r]
def corr(a, b):
    return round(statistics.correlation(a, b), 4) if len(a) > 2 else None

res = {
    "n_sample": len(ok),
    "fidelity": {
        "n": sum(1 for r in ok if r.get("fidelity_pct") is not None),
        "mean_pct": round(statistics.fmean([r["fidelity_pct"] for r in ok if r.get("fidelity_pct") is not None]), 2),
        "min_pct": min([r["fidelity_pct"] for r in ok if r.get("fidelity_pct") is not None], default=None),
        "max_pct": max([r["fidelity_pct"] for r in ok if r.get("fidelity_pct") is not None], default=None),
        "mean_abs_pct": round(statistics.fmean([abs(r["fidelity_pct"]) for r in ok if r.get("fidelity_pct") is not None]), 2),
    },
    "gap_stats": {
        "mean": round(statistics.fmean([r["gap"] for r in ok]), 1),
        "sd": round(statistics.pstdev([r["gap"] for r in ok]), 1),
        "min": min(r["gap"] for r in ok), "max": max(r["gap"] for r in ok),
        "share_negative": round(sum(1 for r in ok if r["gap"] < 0) / len(ok), 3),
    },
    "net_import_stats": {
        "mean": round(statistics.fmean([r["fus_net_import"] for r in ok]), 1),
        "sd": round(statistics.pstdev([r["fus_net_import"] for r in ok]), 1),
    },
    "corr_gap_netimport": corr([r["gap"] for r in ok], [r["fus_net_import"] for r in ok]),
    "corr_E_solar": corr([r["E_gap_plus_netimport"] for r in ok], [r["course_solar"] for r in ok]),
    "corr_E_wind": corr([r["E_gap_plus_netimport"] for r in ok], [r["course_wind"] for r in ok]),
    "corr_E_demand": corr([r["E_gap_plus_netimport"] for r in ok], [r["course_demand"] for r in ok]),
    "E_mean": round(statistics.fmean([r["E_gap_plus_netimport"] for r in ok]), 1),
    "E_sd": round(statistics.pstdev([r["E_gap_plus_netimport"] for r in ok]), 1),
    "wind_discrepancy": {
        "mean_course_minus_fus_wind": round(statistics.fmean([r["course_wind"] - r["fus_wind"] for r in ok]), 1),
        "sd": round(statistics.pstdev([r["course_wind"] - r["fus_wind"] for r in ok]), 1),
    },
}
# regression gap = a + b*net_import
xs = [r["fus_net_import"] for r in ok]
ys = [r["gap"] for r in ok]
mx, my = statistics.fmean(xs), statistics.fmean(ys)
b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
a = my - b * mx
ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
ss_tot = sum((y - my) ** 2 for y in ys)
res["regression_gap_on_netimport"] = {"intercept": round(a, 1), "slope": round(b, 3),
                                      "r2": round(1 - ss_res / ss_tot, 3)}
json.dump({"rows": rows_out, "summary": res},
          open(os.path.join(AUD, "sample_regression.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nSUMMARY", json.dumps(res, ensure_ascii=False, indent=1))
