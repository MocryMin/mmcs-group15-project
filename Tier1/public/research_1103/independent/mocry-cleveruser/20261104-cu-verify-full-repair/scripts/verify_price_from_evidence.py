import csv, gzip, json, os, statistics
from collections import defaultdict

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(here, "SOURCE_MANIFEST.json")) and os.path.exists(os.path.join(here, "PROJECT.md")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            raise SystemExit("project root not found above " + os.path.dirname(os.path.abspath(__file__)))
        here = parent


ROOT = _project_root()
PUB = os.path.join(ROOT, "Tier1", "public", "data_quality", "full_data_repair", "20261104-v2")

old = {r["date"]: float(r["avg_price_£_per_MWh"])
       for r in csv.DictReader(open(os.path.join(ROOT, "daily_market_index_price.csv"), encoding="utf-8-sig", newline=""))}
new = {r["date"]: float(r["avg_price_£_per_MWh"])
       for r in csv.DictReader(open(os.path.join(PUB, "data", "daily_market_index_price.csv"), encoding="utf-8-sig", newline=""))}
mid = json.load(gzip.open(os.path.join(PUB, "evidence", "mid.json.gz"), "rt", encoding="utf-8"))["days"]

res = {"days": 0, "active_vw_match_new": 0, "all_provider_mean_match_old": 0,
       "midnight_value_match_old": 0, "inactive_records": 0, "active_records": 0,
       "mismatch_examples": [], "old_full_day_vs_midnight_dates": []}

for d, halfhours in mid.items():
    res["days"] += 1
    hh_active, hh_all, hh_last = [], [], None
    for ts in sorted(halfhours):
        providers = halfhours[ts]
        num = den = 0.0
        allp = []
        for name, rec in providers.items():
            price, vol = float(rec[0]), float(rec[1])
            allp.append(price)
            if vol > 0:
                num += price * vol
                den += vol
                res["active_records"] += 1
            else:
                res["inactive_records"] += 1
        if den > 0:
            hh_active.append(num / den)
        hh_all.append(statistics.mean(allp))
        hh_last = statistics.mean(allp)
    a = statistics.mean(hh_active) if hh_active else None
    b = statistics.mean(hh_all)
    n = new.get(d)
    o = old.get(d)
    if a is not None and n is not None and abs(a - n) <= 1e-4:
        res["active_vw_match_new"] += 1
    if o is not None and abs(b - o) <= 1e-4:
        res["all_provider_mean_match_old"] += 1
    if o is not None and abs(hh_last - o) <= 1e-4:
        res["midnight_value_match_old"] += 1
        res["old_full_day_vs_midnight_dates"].append(d)
    if len(res["mismatch_examples"]) < 5 and (a is None or n is None or abs(a - n) > 1e-4):
        res["mismatch_examples"].append({"date": d, "evidence_active_vw": a, "new": n,
                                         "old": o, "evidence_all_provider": b,
                                         "halfhours": len(halfhours)})

res["old_full_day_vs_midnight_dates_count"] = len(res["old_full_day_vs_midnight_dates"])
res["old_full_day_vs_midnight_dates"] = sorted(res["old_full_day_vs_midnight_dates"])[:400]
print(json.dumps({k: v for k, v in res.items() if k != "old_full_day_vs_midnight_dates"}, indent=1))

# demand evidence structure
dem = json.load(gzip.open(os.path.join(PUB, "evidence", "demand.json.gz"), "rt", encoding="utf-8"))
print("demand keys:", list(dem)[:5], "n days:", len(dem.get("days", {})))
kd = sorted(dem["days"])[0]
print("first demand day:", kd, type(dem["days"][kd]).__name__)
sample = dem["days"][kd]
if isinstance(sample, dict):
    items = list(sample.items())[:3]
    print("sample items:", json.dumps(items, ensure_ascii=False)[:400])
elif isinstance(sample, list):
    print("sample len", len(sample), json.dumps(sample[:3], ensure_ascii=False)[:400])
json.dump(res, open(os.path.join(os.path.dirname(__file__), "..", "audit", "verify_price_evidence.json"), "w", encoding="utf-8"), indent=1)
