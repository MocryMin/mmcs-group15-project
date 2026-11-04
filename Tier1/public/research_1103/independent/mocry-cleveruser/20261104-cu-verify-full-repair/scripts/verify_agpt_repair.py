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
FUELS = ["Biomass", "Fossil Gas", "Fossil Hard coal", "Fossil Oil",
         "Hydro Pumped Storage", "Hydro Run-of-river and poundage", "Nuclear",
         "Other", "Solar", "Wind Offshore", "Wind Onshore"]

rep = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(PUB, "data", "daily_generation_by_fuel.csv"), encoding="utf-8-sig", newline="")):
    rep[r["date"]][r["psrType"]] = float(r["MW"])
agpt = json.load(gzip.open(os.path.join(PUB, "evidence", "agpt.json.gz"), "rt", encoding="utf-8"))["days"]

complete_days = 0
exact_days = 0
partial_days = 0
worst = []
for d, hh in agpt.items():
    if len(hh) != 48:
        continue
    complete_days += 1
    vals = list(hh.values())
    means = [statistics.mean(v[i] for v in vals) for i in range(11)]
    diffs = {FUELS[i]: rep[d][FUELS[i]] - means[i] for i in range(11)}
    maxdev = max(abs(x) for x in diffs.values())
    if maxdev <= 1.0:
        exact_days += 1
    else:
        partial_days += 1
        worst.append((maxdev, d, {k: round(v, 1) for k, v in diffs.items() if abs(v) > 1}))
worst.sort(reverse=True)
print("agpt days:", len(agpt), "with 48 half-hours:", complete_days)
print("repaired == AGPT daily mean (<=1 MW all 11 fields):", exact_days)
print("differing days:", partial_days)
for x in worst[:5]:
    print("  maxdev %.1f %s %s" % x)

# solar-zero course dates and their repaired basis
oz = [d for d, m in
      {r["date"]: r for r in csv.DictReader(open(os.path.join(ROOT, "daily_generation_by_fuel.csv"), encoding="utf-8-sig", newline=""))}.items()
      if False]
old = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(ROOT, "daily_generation_by_fuel.csv"), encoding="utf-8-sig", newline="")):
    old[r["date"]][r["psrType"]] = float(r["MW"])
sz = sorted(d for d, m in old.items() if m.get("Solar") == 0)
q = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(PUB, "data", "quality.csv"), encoding="utf-8-sig", newline="")):
    q[(r["date"], r["series"], r["field"] if "field" in r else "")] = r
print("\nquality.csv header:", list(next(iter(csv.DictReader(open(os.path.join(PUB, 'data', 'quality.csv'), encoding='utf-8-sig', newline='')))).keys()))
print("solar-zero dates:", len(sz))
for d in sz[:12]:
    print("  ", d, "old solar", old[d]["Solar"], "new solar", rep[d]["Solar"])
print("  ... all new solar > 0:", all(rep[d]["Solar"] > 0 for d in sz))
print("  new solar range on those dates:", min(rep[d]["Solar"] for d in sz), max(rep[d]["Solar"] for d in sz))

# restored 30 generation dates
missing = sorted(set(rep) - set(old))
print("\nrestored generation dates:", len(missing), missing)
print("their totals:", [round(sum(rep[d].values()), 0) for d in missing][:10])
