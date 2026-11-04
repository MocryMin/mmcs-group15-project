import csv, os, statistics
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

def load(path):
    d = defaultdict(dict)
    for r in csv.DictReader(open(path, encoding="utf-8-sig", newline="")):
        d[r["date"]][r["psrType"]] = float(r["MW"])
    return d

old = load(os.path.join(ROOT, "daily_generation_by_fuel.csv"))
new = load(os.path.join(PUB, "data", "daily_generation_by_fuel.csv"))
cats = ["Solar", "Wind Offshore", "Wind Onshore", "Nuclear", "Fossil Gas", "Biomass", "Hydro Pumped Storage"]
print("%-22s %-6s %10s %10s %8s" % ("category", "year", "old_mean", "new_mean", "delta"))
for c in cats:
    for y in ("2020", "2021", "2022", "2023", "2024", "2025", "2026"):
        o = [m.get(c, 0) for d, m in old.items() if d[:4] == y]
        n = [m.get(c, 0) for d, m in new.items() if d[:4] == y]
        if o and n:
            print("%-22s %-6s %10.1f %10.1f %8.1f" % (c, y, statistics.mean(o), statistics.mean(n), statistics.mean(n) - statistics.mean(o)))
