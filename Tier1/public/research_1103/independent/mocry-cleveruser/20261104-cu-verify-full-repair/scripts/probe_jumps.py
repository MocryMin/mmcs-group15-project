import csv, os
from datetime import date

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

dem = {r["startTime"][:10]: float(r["demand"]) for r in csv.DictReader(open(os.path.join(PUB, "data", "daily_demand.csv"), encoding="utf-8-sig", newline=""))}
tot = {r["date"]: float(r["total_MW"]) for r in csv.DictReader(open(os.path.join(PUB, "data", "daily_generation_total.csv"), encoding="utf-8-sig", newline=""))}
flag = {r["date"]: (r["uses_cross_source_reconstruction"], r["uses_estimation_or_interpolation"], r["strict_no_imputation"])
        for r in csv.DictReader(open(os.path.join(PUB, "data", "date_quality.csv"), encoding="utf-8-sig", newline=""))}

def report(series, name, thresh):
    ds = sorted(series)
    out = []
    for a, b in zip(ds, ds[1:]):
        if (date.fromisoformat(b) - date.fromisoformat(a)).days == 1:
            j = abs(series[b] - series[a])
            if j >= thresh:
                out.append((j, b))
    out.sort(reverse=True)
    print("%s jumps >= %d MW: %d" % (name, thresh, len(out)))
    for j, b in out[:8]:
        prev = (date.fromisoformat(b).toordinal() - 1)
        a = date.fromordinal(prev).isoformat()
        print("  %s %.0f -> %.0f (%.0f) flags_prev=%s flags_cur=%s" % (b, series[a], series[b], j, flag.get(a), flag.get(b)))

report(dem, "demand", 5000)
report(tot, "generation", 8000)
