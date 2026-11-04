import csv, gzip, json, os, statistics, sys
from collections import defaultdict

HERE = os.path.dirname(__file__)
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
flag = {r["date"]: r for r in csv.DictReader(open(os.path.join(PUB, "data", "date_quality.csv"), encoding="utf-8-sig", newline=""))}
ev = json.load(gzip.open(os.path.join(PUB, "evidence", "demand.json.gz"), "rt", encoding="utf-8"))["days"]

# parse NESO TSD from the archived CSV text (independent of repair_data.py)
neso = json.load(gzip.open(os.path.join(PUB, "evidence", "neso.json.gz"), "rt", encoding="utf-8"))
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
    london = ZoneInfo("Europe/London")
except Exception as exc:
    print("tz unavailable:", exc); sys.exit(1)

tsd = defaultdict(dict)
for res in neso["resources"].values():
    if res.get("status") != 200:
        continue
    for row in csv.DictReader(res["text"].splitlines()):
        text = row["SETTLEMENT_DATE"]
        local = None
        for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d"):
            try:
                local = datetime.strptime(text, fmt).replace(tzinfo=london); break
            except ValueError:
                continue
        if local is None:
            continue
        utc = local.astimezone(timezone.utc) + timedelta(minutes=30 * (int(row["SETTLEMENT_PERIOD"]) - 1))
        tsd[utc.date().isoformat()][int(utc.timestamp() // 60)] = float(row["TSD"])

clean, recon = [], []
for d in sorted(dem):
    if len(tsd.get(d, {})) != 48:
        continue
    t = statistics.mean(tsd[d].values())
    rec = ev.get(d, {})
    vals = [v for _, v in rec.items()]
    off = t - dem[d]
    if len(vals) >= 288 and min(vals) > 10000:
        clean.append((d, off, t, dem[d]))
    else:
        recon.append((d, off, t, dem[d], len(vals), min(vals) if vals else None))

co = [x[1] for x in clean]
print("clean days:", len(co), "TSD-VD offset mean=%.1f median=%.1f sd=%.1f" % (
    statistics.mean(co), statistics.median(co), statistics.pstdev(co)))
ro = [x[1] for x in recon]
print("reconstructed days:", len(ro))
if ro:
    ro_sorted = sorted(ro)
    inside = sum(1 for x in ro if abs(x - statistics.median(co)) <= 3 * statistics.pstdev(co))
    print("  within 3 sd of clean offset: %d/%d" % (inside, len(ro)))
    print("  worst deviations:")
    for x in sorted(recon, key=lambda y: -abs(y[1]))[:6]:
        print("   %s TSD=%.0f new=%.0f offset=%.0f n_rec=%d min=%s flags=%s" % (
            x[0], x[2], x[3], x[1], x[4], x[5],
            (flag[x[0]]["uses_cross_source_reconstruction"], flag[x[0]]["uses_estimation_or_interpolation"])))
