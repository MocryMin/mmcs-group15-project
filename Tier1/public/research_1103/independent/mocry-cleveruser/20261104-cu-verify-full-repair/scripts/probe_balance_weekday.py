import csv, gzip, json, os, statistics
from collections import defaultdict
import datetime

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

def load_dem(path):
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig", newline="")):
        k = (r.get("startTime") or r.get("date") or "")[:10]
        out[k] = float(r["demand"])
    return out

def load_tot(path):
    return {r["date"]: float(r["total_MW"])
            for r in csv.DictReader(open(path, encoding="utf-8-sig", newline=""))}

od, nd = load_dem(os.path.join(ROOT, "daily_demand.csv")), load_dem(os.path.join(PUB, "data", "daily_demand.csv"))
og, ng = load_tot(os.path.join(ROOT, "daily_generation_total.csv")), load_tot(os.path.join(PUB, "data", "daily_generation_total.csv"))

def gap_by_weekday(gen, dem):
    out = defaultdict(list)
    for d in set(gen) & set(dem):
        out[datetime.date.fromisoformat(d).strftime("%a")].append(gen[d] - dem[d])
    return {k: (len(v), round(statistics.mean(v), 1), round(sum(v) * 24 / 1e6, 2)) for k, v in sorted(out.items())}

print("OLD gap (gen-demand) by weekday [n, mean MW, TWh]:")
for k, v in gap_by_weekday(og, od).items():
    print("  ", k, v)
print("NEW gap by weekday:")
for k, v in gap_by_weekday(ng, nd).items():
    print("  ", k, v)

def overall(gen, dem):
    xs = [gen[d] - dem[d] for d in set(gen) & set(dem)]
    return {"n": len(xs), "mean": round(statistics.mean(xs), 1),
            "deficit_TWh": round(sum(x for x in xs if x < 0) * 24 / 1e6, 3),
            "surplus_TWh": round(sum(x for x in xs if x > 0) * 24 / 1e6, 3),
            "surplus_share": round(sum(1 for x in xs if x > 0) / len(xs), 4)}
print("OLD overall:", overall(og, od))
print("NEW overall:", overall(ng, nd))

print("\nOLD gen mean by weekday:", {k: round(statistics.mean(v), 1) for k, v in
      defaultdict(list, {k: [og[d] for d in og if datetime.date.fromisoformat(d).strftime('%a') == k]
                         for k in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')}).items() if v})
print("NEW gen mean by weekday:", {k: round(statistics.mean(v), 1) for k, v in
      defaultdict(list, {k: [ng[d] for d in ng if datetime.date.fromisoformat(d).strftime('%a') == k]
                         for k in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')}).items() if v})

neso = json.load(gzip.open(os.path.join(PUB, "evidence", "neso.json.gz"), "rt", encoding="utf-8"))
print("\nneso top keys:", list(neso))
print("neso metadata_notes:", json.dumps(neso.get("metadata_notes"), ensure_ascii=False)[:500])
res = neso.get("resources")
if isinstance(res, dict):
    for k, v in list(res.items())[:5]:
        print(" resource", k, type(v).__name__, len(v) if hasattr(v, "__len__") else "")
        if isinstance(v, dict):
            kk = sorted(v)[0]
            print("   first key", kk, "->", json.dumps(v[kk], ensure_ascii=False)[:200])
