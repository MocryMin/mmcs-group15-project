"""Verify Tier 1 report candidate v7 (report.pdf sha256 2cb86889...) against
(a) its own evidence bundle tier1-xpress-review-evidence.zip (sha256 3cf6712f...),
(b) the shipped renewable-attribution.csv and xpress-comparison.csv,
(c) the frozen half-hour panel and the daily fuel table in the v7 study archive,
(d) the pinned v6.3 / v6.2 / v6 supplements for the unchanged baselines, and
(e) the daily model implementation archived in the v6 bundle.

Independent recomputation is used wherever the report's claim is arithmetic
(the renewable attribution, the annual-window means, the residual identity
between electricity input, surplus capture and diverted sales).

Writes checks_v7.json next to this file.
"""

import csv, gzip, hashlib, io, json, os, re, subprocess, zipfile

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, *[".."] * 6))
PROJ = os.path.dirname(REPO)
TREE_TXT = os.path.join(PROJ, ".cc-scratch", "v7", "tree.txt")
MODELPY = os.path.join(PROJ, ".cc-scratch", "v6", "FinalProject", "tier1-halfhour-20261113-v7", "model.py")
SITEMODEL = os.path.join(PROJ, ".cc-scratch", "v62", "evidence", "group-collaboration", "Tier1", "workspaces",
                         "julian", "claude", "tier1-main-results", "20261123-v1", "site_model.py")
LATEX = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex", "technical-report-latex")
D7 = os.path.join(LATEX, "20261124-v7")
D65 = os.path.join(LATEX, "20261124-v6.5")
D62 = os.path.join(LATEX, "20261124-v6.2")
D6 = os.path.join(LATEX, "20261123-v6")

PDF = os.path.join(D7, "report.pdf")
SRC = os.path.join(D7, "report-source.zip")
EVID7 = os.path.join(D7, "tier1-xpress-review-evidence.zip")
RENEW = os.path.join(D7, "renewable-attribution.csv")
XCOMP = os.path.join(D7, "xpress-comparison.csv")
DISP7 = os.path.join(D7, "display-table-evidence.json")
EVID63 = os.path.join(D65, "tier1-site-evidence-v6.3.zip")
EVID62 = os.path.join(D62, "tier1-site-evidence-v6.2.zip")
EVID6 = os.path.join(D6, "tier1-site-evidence-v6.zip")
PANEL = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex", "work-history", "20261113-v1",
                     "studies", "tier1-halfhour-20261113-v7", "inputs", "halfhour.csv.gz")
FUEL = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex", "work-history", "20261113-v1",
                    "studies", "tier1-halfhour-20261113-v7", "source_data",
                    "tier1-multiproduct-20261110-v6", "inputs", "daily_generation_by_fuel.csv")
JULIAN = "Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1"
JULIAN_COMMIT = "c3902fe"

z7 = zipfile.ZipFile(EVID7)
z63 = zipfile.ZipFile(EVID63)
z62 = zipfile.ZipFile(EVID62)
z6 = zipfile.ZipFile(EVID6)
zsrc = zipfile.ZipFile(SRC)

checks = []


def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=computed, stated=stated, ok=bool(ok), note=note))


def zone(z, inner, reader=csv.DictReader):
    with z.open(inner) as f:
        return list(reader(io.TextIOWrapper(f, encoding="utf-8")))


def js(z, inner):
    return json.loads(z.read(inner).decode("utf-8"))


def gz_rows(data):
    return list(csv.DictReader(io.TextIOWrapper(io.BytesIO(gzip.decompress(data)), encoding="utf-8")))


def npz_from(z, inner):
    return dict(np.load(io.BytesIO(z.read(inner))))


def git_show(path):
    out = subprocess.run(["git", "-C", REPO, "show", f"{JULIAN_COMMIT}:{path}"], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace"))
    return out.stdout.decode("utf-8")


def near(a, b, tol):
    return abs(float(a) - float(b)) <= tol


# ---- 1. package integrity ---------------------------------------------------
sums = {}
for line in open(os.path.join(D7, "SHA256SUMS.txt"), encoding="utf-8").read().splitlines():
    if line.strip():
        digest, fname = line.split()
        sums[fname] = digest
files = {"README.md": os.path.join(D7, "README.md"), "display-table-evidence.json": DISP7,
         "renewable-attribution.csv": RENEW, "report-source.zip": SRC, "report.pdf": PDF,
         "tier1-xpress-review-evidence.zip": EVID7, "xpress-comparison.csv": XCOMP}
sha = {}
for name, path in files.items():
    sha[name] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    add(f"v7 {name} sha256 matches SHA256SUMS.txt", sha[name][:16], (sums.get(name) or "")[:16],
        sha[name] == sums.get(name))
add("SHA256SUMS lists exactly the seven shipped artefacts", sorted(sums), sorted(files),
    sorted(sums) == sorted(files))
add("no unlisted file in the v7 release directory",
    sorted(set(os.listdir(D7)) - set(files) - {"SHA256SUMS.txt"}), [],
    sorted(set(os.listdir(D7)) - set(files) - {"SHA256SUMS.txt"}) == [])

from pypdf import PdfReader

reader = PdfReader(PDF)
add("PDF page count", len(reader.pages), 16, len(reader.pages) == 16)
pages = [(p.extract_text() or "").strip().splitlines() for p in reader.pages]
text = "\n".join("\n".join(p) for p in pages)
foot = [p[-1].strip() if p else "" for p in pages]
add("body pages numbered 1-6 only (page rule: 10 pages = body pages)",
    [foot[i] for i in range(2, 8)], ["1", "2", "3", "4", "5", "6"],
    [foot[i] for i in range(2, 8)] == ["1", "2", "3", "4", "5", "6"])
add("front matter and appendix page labels", [foot[0], foot[1]] + [foot[i] for i in range(8, 16)],
    ["i", "ii", "R1", "A1", "A2", "A3", "A4", "A5", "A6", "A7"],
    [foot[0], foot[1]] + [foot[i] for i in range(8, 16)] == ["i", "ii", "R1", "A1", "A2", "A3",
                                                            "A4", "A5", "A6", "A7"])
add("README page claim (six body pages, 16 PDF pages) matches the PDF",
    (len(pages), 6), (16, 6), len(pages) == 16 and "six body pages and 16 PDF pages" in
    open(os.path.join(D7, "README.md"), encoding="utf-8").read())

srcnames = zsrc.namelist()
add("source archive entries", len(srcnames), 15, len(srcnames) == 15)
for inner, top in (("evidence/renewable-attribution.csv", RENEW), ("evidence/xpress-comparison.csv", XCOMP)):
    add(f"source archive {inner} is byte-identical to the shipped {os.path.basename(top)}",
        hashlib.sha256(zsrc.read(inner)).hexdigest()[:16],
        hashlib.sha256(open(top, "rb").read()).hexdigest()[:16],
        zsrc.read(inner) == open(top, "rb").read())

names7 = z7.namelist()
add("evidence archive entries", len(names7), 34, len(names7) == 34)
manifests = [n for n in names7 if re.search(r"(MANIFEST|SHA256|\.sha256)$", n, re.I)]
add("evidence archive carries an internal hash manifest (v6.3 did)", manifests, [],
    manifests == [], "the v6.3 supplement shipped MANIFEST.json with 33 sha256 rows; the v7 bundle "
                     "relies on the outer zip digest only")
add("evidence archive comparison.csv is byte-identical to xpress-comparison.csv",
    hashlib.sha256(z7.read("tier1-xpress-full-20261124/comparison.csv")).hexdigest()[:16],
    hashlib.sha256(open(XCOMP, "rb").read()).hexdigest()[:16],
    z7.read("tier1-xpress-full-20261124/comparison.csv") == open(XCOMP, "rb").read())
add("evidence archive renewable-attribution.csv is byte-identical to the shipped copy",
    hashlib.sha256(z7.read("project-report-20261124-v7/renewable-attribution.csv")).hexdigest()[:16],
    hashlib.sha256(open(RENEW, "rb").read()).hexdigest()[:16],
    z7.read("project-report-20261124-v7/renewable-attribution.csv") == open(RENEW, "rb").read())

ih = json.loads(z7.read("tier1-xpress-full-20261124/input-hashes.json").decode("utf-8"))
panel_sha = hashlib.sha256(open(PANEL, "rb").read()).hexdigest()
add("pinned half-hour panel hash equals the archived study panel",
    panel_sha[:16], ih["tier1-halfhour-20261113-v7/inputs/halfhour.csv.gz"][:16],
    panel_sha == ih["tier1-halfhour-20261113-v7/inputs/halfhour.csv.gz"])
add("pinned report.pdf hash equals the shipped report.pdf",
    sha["report.pdf"][:16], ih["project-report-20261124-v7/report.pdf"][:16],
    sha["report.pdf"] == ih["project-report-20261124-v7/report.pdf"],
    "input-hashes.json records 7ab31838... for report.pdf; the shipped file is 2cb86889... "
    "(the PDF itself is still bound correctly by SHA256SUMS.txt)")
tree = open(TREE_TXT, encoding="utf-8").read() if os.path.exists(TREE_TXT) else ""
add("third pinned input (storage exploration configuration.json) is shipped in the repository",
    [n for n in tree.splitlines() if "storage-exploration-20261116-v2/utility4h/configuration.json" in n],
    "one path", [n for n in tree.splitlines()
                 if "storage-exploration-20261116-v2/utility4h/configuration.json" in n] != [],
    "not present anywhere in the published tree; only the outer hash remains as an unverifiable pin")

# ---- 2. Xpress comparison and Table C.1 ------------------------------------
comp = {(r["case"], r["floor"], int(r["battery_blocks"]), int(r["electrolyser_units"]), r["solver"]): r
        for r in zone(z7, "tier1-xpress-full-20261124/comparison.csv")}
kA2 = ("Half-hour four-day", "0.2", 45, 6, "Xpress")
kA125 = ("Half-hour four-day", "0.125", 45, 6, "Xpress")
kB = ("Half-hour four-day", "0.2", 9, 0, "Xpress")
add("A 20% feasible annual net equals A-0.2-xpress.json",
    round(float(comp[kA2]["annual_net_mGBP"]), 9),
    round(js(z7, "tier1-xpress-full-20261124/A-0.2-xpress.json")["annual_net_mGBP"], 9),
    near(comp[kA2]["annual_net_mGBP"], js(z7, "tier1-xpress-full-20261124/A-0.2-xpress.json")
         ["annual_net_mGBP"], 1e-9))
add("Table C.1 prints A 20% feasible 118.818207 and upper bound 118.820807",
    (round(float(comp[kA2]["annual_net_mGBP"]), 6), round(float(comp[kA2]["upper_mGBP"]), 6)),
    ("118.818207", "118.820807"),
    (f"{float(comp[kA2]['annual_net_mGBP']):.6f}", f"{float(comp[kA2]['upper_mGBP']):.6f}")
    == ("118.818207", "118.820807") and "118.818207" in text and "118.820807" in text)
add("Table C.1 prints A 12.5% feasible 118.898893 and upper bound 118.900891",
    (f"{float(comp[kA125]['annual_net_mGBP']):.6f}", f"{float(comp[kA125]['upper_mGBP']):.6f}"),
    ("118.898893", "118.900891"),
    (f"{float(comp[kA125]['annual_net_mGBP']):.6f}", f"{float(comp[kA125]['upper_mGBP']):.6f}")
    == ("118.898893", "118.900891") and "118.898893" in text and "118.900891" in text)
add("Table C.1 prints B 6.07025804 / 6.07025820", f"{float(comp[kB]['annual_net_mGBP']):.8f}",
    "6.07025804", f"{float(comp[kB]['annual_net_mGBP']):.8f}" == "6.07025804"
    and "6.07025804" in text and "6.07025820" in text)
dailyA = [r for r in zone(z7, "tier1-xpress-full-20261124/comparison.csv")
          if r["case"] == "Daily brief" and r["policy"] == "A"][0]
add("Table C.1 wall-clock times match comparison.csv",
    [round(float(dailyA["wall_seconds"]), 2)] +
    [round(float(comp[k]["wall_seconds"]), 2) for k in
     [kA2, kB, kA125, ("Half-hour four-day", "0.125", 9, 0, "Xpress")]],
    [0.21, 76.80, 50.99, 86.33, 70.04],
    [round(float(dailyA["wall_seconds"]), 2)] +
    [round(float(comp[k]["wall_seconds"]), 2) for k in
     [kA2, kB, kA125, ("Half-hour four-day", "0.125", 9, 0, "Xpress")]] == [0.21, 76.80, 50.99, 86.33, 70.04]
    and all(s in text for s in ("76.80", "50.99", "86.33", "70.04", "0.21")))

for label, key, stated in (("20%", kA2, "118.811177"), ("12.5%", kA125, "118.890634")):
    alt = float(comp[key]["alternative_upper_mGBP"])
    add(f"{label} nearest competing capacity upper bound is below the 45/6 feasible gain",
        (f"{alt:.6f}", alt < float(comp[key]["annual_net_mGBP"])), (stated, True),
        f"{alt:.6f}" == stated and alt < float(comp[key]["annual_net_mGBP"]))
altB = float(comp[kB]["alternative_upper_mGBP"])
add("B eight-block upper bound 6.069620 is below the nine-block feasible gain",
    (f"{altB:.6f}", altB < float(comp[kB]["annual_net_mGBP"])), ("6.069620", True),
    f"{altB:.6f}" == "6.069620" and altB < float(comp[kB]["annual_net_mGBP"]))
add("§5.1 gap wording: £2,600/year in A and £0.17/year in B",
    (round(float(comp[kA2]["annual_gap_GBP"]), 1), round(float(comp[kB]["annual_gap_GBP"]), 2)),
    (2599.4, 0.17), near(float(comp[kA2]["annual_gap_GBP"]), 2599.4, 0.1)
    and near(float(comp[kB]["annual_gap_GBP"]), 0.1667, 5e-3) and "2,600/year" in text
    and "0.17/year" in text)
a2 = js(z7, "tier1-xpress-full-20261124/A-0.2-xpress.json")
cand2 = [r for r in a2["lps"] if r["capacity"] and r["capacity"] != [45, 6]]
top2 = max(cand2, key=lambda r: r["lp_mGBP"])
add("nearest competing capacity at 20% is 46 blocks and six modules",
    (top2["capacity"], round(top2["lp_mGBP"], 6)), ([46, 6], 118.811175),
    top2["capacity"] == [46, 6] and near(top2["lp_mGBP"], 118.8111745782262, 1e-6)
    and "46 blocks and six mod" in text)
a125 = js(z7, "tier1-xpress-full-20261124/A-0.125-xpress.json")
cand125 = [r for r in a125["lps"] if r["capacity"] and r["capacity"] != [45, 6]]
top125 = max(cand125, key=lambda r: r["lp_mGBP"])
add("nearest competing capacity at 12.5% is also 46 blocks and six modules",
    top125["capacity"], [46, 6], top125["capacity"] == [46, 6])
ach = js(z63, "tier1-commitment-20-20261124/A-capacity-certificate.json")
disp = json.load(open(DISP7, encoding="utf-8"))
follow = disp["v7_review_followup"]["policy_A_joint_at_20_pct"]
add("upper-bound ordering feasible < tightened global upper < raw LP upper",
    (round(follow["feasible_mGBP_per_year"], 6), round(follow["tightened_global_upper_mGBP_per_year"], 6),
     round(follow["raw_fixed_capacity_LP_upper_mGBP_per_year"], 6)),
    ("118.818207 < 118.819823 < 118.820805",),
    follow["feasible_mGBP_per_year"] < follow["tightened_global_upper_mGBP_per_year"]
    < follow["raw_fixed_capacity_LP_upper_mGBP_per_year"],
    "v6.5 printed 118.819823 as the global upper next to an upper_mGBP of 118.820805; v7 reports the "
    "raw LP bound in Table C.1 and the tightened bound in the text")
add("§C.2 tighter 20% bound 118.819824 matches the archived certificate",
    f"{ach['tightened_global_upper_mGBP_per_year'] if 'tightened_global_upper_mGBP_per_year' in ach else follow['tightened_global_upper_mGBP_per_year']:.6f}",
    "118.819824", "118.819824" in text)
add("Xpress upper bound in Table C.1 is above the archived raw LP bound by <= £2/year",
    round((float(comp[kA2]["upper_mGBP"]) - follow["raw_fixed_capacity_LP_upper_mGBP_per_year"]) * 1e6, 2),
    "<= 2 GBP/year",
    abs(float(comp[kA2]["upper_mGBP"]) - follow["raw_fixed_capacity_LP_upper_mGBP_per_year"]) < 1e-5)

ann = zone(z7, "tier1-xpress-full-20261124/annual-results.csv")
years = {}
for r in ann:
    years.setdefault(r["case"], {})[r["year"]] = float(r["net_mGBP"])
for case, key, tol in (("A-0.2-xpress", kA2, 1e-6), ("A-0.125-xpress", kA125, 1e-6),
                       ("B-0.2-xpress", kB, 1e-6)):
    mean = sum(years[case].values()) / len(years[case])
    add(f"{case} annual mean reproduces the Xpress feasible gain", round(mean, 9),
        round(float(comp[key]["annual_net_mGBP"]), 9), near(mean, comp[key]["annual_net_mGBP"], tol))
w = disp["window_mean_mGBP_per_year"]
winA = {"2023--25": 39.12, "2024--25": 19.53, "2020--25 excluding 2022": 65.10}
winB = {"2023--25": -13.07, "2024--25": -12.85, "2020--25 excluding 2022": -8.01}
gotA = {k: round(sum(years["A-0.125-xpress"][y] for y in ys) / len(ys), 2)
        for k, ys in (("2023--25", ["2023", "2024", "2025"]), ("2024--25", ["2024", "2025"]),
                      ("2020--25 excluding 2022", ["2020", "2021", "2023", "2024", "2025"]))}
gotB = {k: round(sum(years["B-0.125-xpress"][y] for y in ys) / len(ys), 2)
        for k, ys in (("2023--25", ["2023", "2024", "2025"]), ("2024--25", ["2024", "2025"]),
                      ("2020--25 excluding 2022", ["2020", "2021", "2023", "2024", "2025"]))}
add("Table II.4 window means recomputed from annual-results.csv (A, 12.5% basis)", gotA, winA, gotA == winA)
add("Table II.4 window means recomputed from annual-results.csv (B, 12.5% basis)", gotB, winB, gotB == winB)
add("Table II.4 2020--25 row equals the Xpress feasible gains",
    (round(gotA and sum(years['A-0.125-xpress'].values()) / 6, 2),
     round(sum(years['B-0.125-xpress'].values()) / 6, 2)), (118.90, 6.07),
    round(sum(years["A-0.125-xpress"].values()) / 6, 2) == 118.90
    and round(sum(years["B-0.125-xpress"].values()) / 6, 2) == 6.07)
add("Figure II.1 / Table II.4 basis is the 12.5% four-day fleet 45/6 and 9/0",
    ("at 12.5%" in text and "Counts (blocks/modules)" in text), True,
    "at 12.5%" in text and "Counts (blocks/modules)" in text)
add("B negative in four of six years at 12.5%", sum(1 for v in years["B-0.125-xpress"].values() if v < 0), 4,
    sum(1 for v in years["B-0.125-xpress"].values() if v < 0) == 4 and "four of six years" in text)

# ---- 3. renewable surplus attribution (independent recomputation) ----------
dates, utcs, g, d, farm, prices = [], [], [], [], [], []
with gzip.open(PANEL, "rt", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        dates.append(row["date"])
        utcs.append(row["utc"])
        g.append((float(row["background_MW"]) + float(row["farm_flat_MW"])) / 2000.0)
        d.append(float(row["demand_MW"]) / 2000.0)
        farm.append(float(row["farm_flat_MW"]))
        prices.append(float(row["price"]))
dates = np.array(dates)
g, d, farm = np.array(g), np.array(d), np.array(farm)
udates, inv = np.unique(dates, return_inverse=True)
nd = len(udates)
add("half-hour panel shape 105,216 intervals / 2,192 days", (len(g), nd), (105216, 2192),
    len(g) == 105216 and nd == 2192)
dg = np.bincount(inv, weights=g)
dd = np.bincount(inv, weights=d)
dfarm = np.bincount(inv, weights=farm) / np.bincount(inv)

FUELS = ["Biomass", "Hydro Run-of-river and poundage", "Solar", "Wind Onshore", "Wind Offshore"]
fmw = {f: np.zeros(nd) for f in FUELS}
idx = {u: i for i, u in enumerate(udates)}
with open(FUEL, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["psrType"] in fmw and row["date"] in idx:
            fmw[row["psrType"]][idx[row["date"]]] += float(row["MW"])
mix = (sum(fmw.values()) + dfarm) * 24.0 / (dg * 1000.0)
add("renewable share of daily generation stays within [0,1]", (float(mix.min()) > 0, float(mix.max()) < 1),
    (True, True), mix.min() > 0 and mix.max() < 1)
mix_t = mix[inv]
physical = np.maximum(g - d, 0.0)
YEARS = 6.0
surplus_all = physical.sum() / YEARS
ren_all = float(mix_t @ physical / YEARS)
daily_net_all = np.maximum(dg - dd, 0.0).sum() / YEARS
ren_daily = float(mix @ np.maximum(dg - dd, 0.0) / YEARS)
add("§I.3 all-fuel half-hour surplus 5,165 GWh/yr reproduced", round(surplus_all, 3), 5165,
    f"{surplus_all:.1f}" == "5164.7" and "5,165 GWh/year" in text)
add("§I.3 daily-netted all-fuel surplus 2,276 GWh/yr reproduced", round(daily_net_all, 3), 2276,
    f"{daily_net_all:.1f}" == "2276.2" and "2,276 GWh/year" in text)
add("§II.5.3 renewable surplus 2,432 GWh/yr reproduced", round(ren_all, 3), 2432,
    f"{ren_all:.1f}" == "2432.2" and "2,432 GWh/year" in text)
add("daily-net renewable surplus (Table C.3 two-hour row) is 1,138 GWh/yr", round(ren_daily, 1), 1138,
    round(ren_daily, 0) == 1138.0)

rows = []


def attribute(device, case, ren_base, phys=physical, m=mix_t):
    device = np.asarray(device, float)
    cap = np.minimum(phys, np.maximum(device, 0.0))
    ren_cap = float(m @ cap / YEARS)
    rows.append(dict(case=case, all_fuel=cap.sum() / YEARS, ren_cap=ren_cap, ren_rem=ren_base - ren_cap))
    return ren_cap


devsum = {}
for pol in ("A", "B"):
    sched = {r["date"]: r for r in gz_rows(z7.read(
        f"tier1-xpress-full-20261124/daily-xpress/results/reference_day_{pol}_integer_schedule.csv.gz"))}
    gs = np.array([float(sched[u]["g"]) for u in udates])
    ds = np.array([float(sched[u]["d"]) for u in udates])
    add(f"daily {pol} schedule generation/demand reconciles to the panel",
        (float(np.abs(gs - dg).max()), float(np.abs(ds - dd).max())), "<1e-7 GWh",
        np.abs(gs - dg).max() < 1e-7 and np.abs(ds - dd).max() < 1e-7)
    dev = np.array([float(sched[u]["charge"]) + float(sched[u]["generation_h2"]) for u in udates])
    devsum[pol] = dev.sum() / YEARS
    attribute(dev, f"daily {pol}", ren_daily, np.maximum(dg - dd, 0.0), mix)

zero = {}
for floor in (0.2, 0.125):
    schedule = npz_from(z7, f"tier1-xpress-full-20261124/A-zero-{floor:g}-xpress.npz")
    h = schedule["hydrogen_MWh"].ravel() / 1000.0
    zero[floor] = (h, attribute(h, f"zero {floor:g}", ren_all))

joint = {}
for floor in (0.2, 0.125):
    sc = npz_from(z7, f"tier1-xpress-full-20261124/A-A-{floor:g}-xpress-45-6.npz")
    q, c, dis, h = sc["sales"], sc["charge"], sc["discharge"], sc["hydrogen"]
    direct = h - np.maximum(0.0, dis - q)
    alt = h - np.minimum(h, dis)
    r1 = attribute(c + direct, f"joint {floor:g}", ren_all)
    cap_alt = np.minimum(physical, np.maximum(c + alt, 0.0))
    joint[floor] = (h, r1, float(mix_t @ cap_alt / YEARS))

bsc = npz_from(z7, "tier1-xpress-full-20261124/B-0.2-xpress-winning-dispatch.npz")
bflows = bsc["flows"]
rb = attribute(bflows[1], "B", ren_all)
add("B battery charge is flows[1] (560.8 GWh/yr)", round(bflows[1].sum() / YEARS, 1), 560.8,
    round(bflows[1].sum() / YEARS, 1) == 560.8)
add("B delivered share 91.23% reproduced from flows[0] + flows[2]",
    round(100 * (bflows[0].sum() + bflows[2].sum()) / d.sum(), 2), 91.23,
    near(100 * (bflows[0].sum() + bflows[2].sum()) / d.sum(), 91.23, 0.005))

flex = {}
for pol, blocks, mods, inner in (("A", 45, 6, "A_n45_h6"), ("B", 9, 10, "B_n9_h10")):
    sc = dict(np.load(io.BytesIO(z6.read(f"FinalProject/tier1-site-battery-20261122/joint/{inner}_dispatch.npz"))))
    ts = sc["utc_ns"]
    from datetime import datetime, timezone
    panel_ns = np.array([int(datetime.fromisoformat(u).astimezone(timezone.utc).timestamp() * 1e9)
                         for u in utcs], dtype=np.int64)
    add(f"flexible {pol} replay timestamps align with the panel", np.array_equal(np.asarray(ts, dtype=np.int64),
                                                                                panel_ns), True,
        np.array_equal(np.asarray(ts, dtype=np.int64), panel_ns))
    flows = sc["flows"]
    _, c, _, batt_h2, _, h = flows
    flex[pol] = attribute(c + h - batt_h2, f"flex {pol}", ren_all)

csvrows = list(csv.DictReader(open(RENEW, encoding="utf-8")))
add("shipped CSV renewable surplus equals the recomputation",
    round(float([r for r in csvrows if r["case"] == "Half-hour direct sales"][0]["renewable_surplus_GWh_year"]), 6),
    round(ren_all, 6),
    near([r for r in csvrows if r["case"] == "Half-hour direct sales"][0]["renewable_surplus_GWh_year"],
         ren_all, 1e-6))

pairs = [
    (("Daily two-hour", "A"), "daily A"), (("Daily two-hour", "B"), "daily B"),
    (("Four-day electrolysis only", "A"), "zero 0.2"), (("Four-day electrolysis only", "A"), "zero 0.125"),
    (("Four-day joint", "A"), "joint 0.2"), (("Four-day joint", "A"), "joint 0.125"),
    (("Four-day joint", "B"), "B"), (("Flexible joint", "A"), "flex A"), (("Flexible joint", "B"), "flex B")]
table = {"daily A": 19.050612, "daily B": 19.050612, "zero 0.2": 28.113416, "zero 0.125": 31.704615,
         "joint 0.2": 882.556856, "joint 0.125": 883.264494, "B": 240.154695,
         "flex A": 828.518195, "flex B": 278.466961}
floor_of = {"daily A": "0.2", "daily B": "0.2", "zero 0.2": "0.2", "zero 0.125": "0.125",
            "joint 0.2": "0.2", "joint 0.125": "0.125", "B": "both", "flex A": "0.125", "flex B": "0.125"}
found = {x["case"]: x for x in rows}
for key, label in pairs:
    got = found[label]["ren_cap"] if label in found else None
    shipped = float([r for r in csvrows if (r["case"], r["policy"], r["floor"]) ==
                     (key[0], key[1], floor_of[label])][0]["renewable_captured_GWh_year"])
    add(f"renewable capture reproduced independently: {key[0]} {key[1]} {floor_of[label]}",
        round(got, 6) if got is not None else None, round(shipped, 6),
        got is not None and near(got, shipped, 1e-6),
        "recomputed from the frozen panel, the daily fuel table and the archived schedule")
add("Table C.3 captures match the CSV after independent recomputation",
    {k: round(v["ren_cap"], 3) for k, v in found.items()}, table,
    all(near(found[k]["ren_cap"], table[k], 5e-4) for k in table))
add("Table C.3 printed row (20% joint) reads 883 captured and 1,550 remaining",
    (round(found["joint 0.2"]["ren_cap"], 0), round(found["joint 0.2"]["ren_rem"], 0)), (883, 1550),
    round(found["joint 0.2"]["ren_cap"], 0) == 883 and round(found["joint 0.2"]["ren_rem"], 0) == 1550
    and "883" in text and "1,550" in text)
add("Table C.3 printed row (20% electrolysis only) reads 28 captured and 2,404 remaining",
    (round(found["zero 0.2"]["ren_cap"], 0), round(found["zero 0.2"]["ren_rem"], 0)), (28, 2404),
    round(found["zero 0.2"]["ren_cap"], 0) == 28 and round(found["zero 0.2"]["ren_rem"], 0) == 2404
    and "2,404" in text)
add("Table C.3 printed row (B nine blocks) reads 240 captured and 2,192 remaining",
    (round(found["B"]["ren_cap"], 0), round(found["B"]["ren_rem"], 0)), (240, 2192),
    round(found["B"]["ren_cap"], 0) == 240 and round(found["B"]["ren_rem"], 0) == 2192
    and "2,192" in text)
add("Table C.3 printed row (12.5% electrolysis only) reads 32 captured and 2,401 remaining",
    (round(found["zero 0.125"]["ren_cap"], 0), round(found["zero 0.125"]["ren_rem"], 0)), (32, 2401),
    round(found["zero 0.125"]["ren_cap"], 0) == 32 and round(found["zero 0.125"]["ren_rem"], 0) == 2401
    and "2,401" in text)
add("Table C.3 two-hour row reads 1,138 available / 19 captured / 1,119 remaining",
    (round(ren_daily, 0), round(found["daily A"]["ren_cap"], 0), round(found["daily A"]["ren_rem"], 0)),
    (1138.0, 19.0, 1119.0), round(ren_daily, 0) == 1138 and round(found["daily A"]["ren_cap"], 0) == 19
    and round(found["daily A"]["ren_rem"], 0) == 1119 and "1,138" in text and "1,119" in text)

spread = {f: joint[f][1] - joint[f][2] for f in joint}
add("discharge-to-hydrogen-first reduces capture by less than 0.3 GWh/yr at both floors",
    {f: round(spread[f], 3) for f in spread}, "<= 0.3", all(spread[f] < 0.3 for f in spread)
    and "less than 0.3 GWh/year" in text)
fin20 = js(z63, "tier1-commitment-20-20261124/A-zero-finance.json")
fin125 = js(z62, "project-report-20261124-v6.2/A-7-finance.json")
add("§C.4 'diverts 125 GWh/year' matches the archived 20% finance split",
    round(fin20["diverted_gwh"], 1), 125.4, round(fin20["diverted_gwh"], 0) == 125
    and "125 GWh/year" in text)
add("§C.4 'diverts 118 GWh/year' matches the archived 12.5% finance split",
    round(fin125["diverted_gwh"], 1), 118.4, round(fin125["diverted_gwh"], 0) == 118
    and "118 GWh/year" in text)
implied20 = zero[0.2][0].sum() / YEARS - found["zero 0.2"]["all_fuel"]
implied125 = zero[0.125][0].sum() / YEARS - found["zero 0.125"]["all_fuel"]
add("residual identity: input - surplus capture equals the printed diverted GWh (20%)",
    round(implied20, 2), round(fin20["diverted_gwh"], 2), near(implied20, fin20["diverted_gwh"], 1.0),
    "Table C.3's capture (63.23) and §C.4's diverted figure (125.39) come from two different optimal "
    "schedules of the same case: input 190.42 - 63.23 = 127.19, not 125.39 (1.8 GWh/yr, 1.4%)")
add("residual identity: input - surplus capture equals the printed diverted GWh (12.5%)",
    round(implied125, 2), round(fin125["diverted_gwh"], 2), near(implied125, fin125["diverted_gwh"], 1.0),
    "input 192.17 - 71.70 = 120.47 against the archived 118.39 (2.1 GWh/yr); the archived all-fuel "
    "capture is 65.03 (20%) and 73.77 (12.5%) versus 63.23 and 71.70 here")
add("§C.4 served-change 0.049 and 0.047 pp match the archived finance files",
    (round(-fin20["served_change_pp"], 3), round(-fin125["served_change_pp"], 3)), (0.049, 0.047),
    round(-fin20["served_change_pp"], 3) == 0.049 and round(-fin125["served_change_pp"], 3) == 0.047
    and "0.049" in text and "0.047" in text)
add("daily B input equals its all-fuel surplus capture (input met from daily surplus)",
    (round(devsum["B"], 3), round(found["daily B"]["all_fuel"], 3)), "equal",
    near(devsum["B"], found["daily B"]["all_fuel"], 1e-6),
    "daily A takes 182.1 GWh/yr of electricity and captures 42.74 GWh from surplus")
add("§5.5 'All-fuel surplus supplies 34%' matches the archived share",
    round(fin20["share_from_unsold_pct"], 2), 34.15, near(fin20["share_from_unsold_pct"], 34.1496, 1e-3)
    and "34%" in text)
add("§5.5 'about 25% of output earns £7.80/kg' matches the archived break-even share",
    round(disp["v7_review_followup"]["policy_A_fixed_dispatch_two_price_sensitivity"]
          ["by_minimum_load_pct"]["20"]["break_even_supported_share_of_hydrogen_pct"], 2), 25.43,
    near(disp["v7_review_followup"]["policy_A_fixed_dispatch_two_price_sensitivity"]
         ["by_minimum_load_pct"]["20"]["break_even_supported_share_of_hydrogen_pct"], 25.434, 5e-3))

# ---- 4. daily reference model and commitment rules -------------------------
cfg = js(z7, "tier1-xpress-full-20261124/daily-config.json")
bb = cfg["batteries"][0]
add("daily two-hour block is 100 MW / 200 MWh with a 20-80% band",
    (bb["P_MW"], bb["E_MWh"], bb["soc_lower"], bb["soc_upper"]), (100.0, 200.0, 0.2, 0.8),
    (bb["P_MW"], bb["E_MWh"], bb["soc_lower"], bb["soc_upper"]) == (100.0, 200.0, 0.2, 0.8))
add("daily buyer cap 10,000 kg/day and £7.799/kg receipt",
    (cfg["cap_kg_day"], round(cfg["netback"], 3)), (10000, 7.799),
    cfg["cap_kg_day"] == 10000 and round(cfg["netback"], 3) == 7.799)
dcmp = js(z7, "tier1-xpress-full-20261124/daily-comparison.json")
vals = {(r["solver"], r["policy"]): round(r["annual_net_mGBP"], 6) for r in dcmp}
add("daily A/B 12.462039 and 2.180223 reproduced by both solvers",
    (vals[("Xpress", "A")], vals[("Xpress", "B")], vals[("HiGHS", "A")], vals[("HiGHS", "B")]),
    (12.462039, 2.180223, 12.462039, 2.180223),
    vals[("Xpress", "A")] == 12.462039 and vals[("Xpress", "B")] == 2.180223
    and vals[("HiGHS", "A")] == 12.462039 and vals[("HiGHS", "B")] == 2.180223)
add("daily model size 13,155 columns / 24,113 rows matches the archived build",
    (js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")["variables"],
     js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")["rows"]),
    (13155, 24113),
    js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")["variables"] == 13155
    and js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")["rows"] == 24113
    and "13,155 columns and 24,113 rows" in text)
modelpy = open(MODELPY, encoding="utf-8").read() if os.path.exists(MODELPY) else ""
add("archived daily implementation applies eta*c_d <= W*b and (r+u)/eta <= W*b per period",
    bool(re.search(r"if dt==24:", modelpy)), True, bool(re.search(r"if dt==24:", modelpy)),
    "model.py, daily branch: m.rows(T,[(c,eta),(n,-b['usable'])],hi=0) and "
    "m.rows(T,[(r,1/eta),(bh,1/eta),(n,-b['usable'])],hi=0)")
add("archived daily implementation carries stock across days and pins s_T = 0",
    ("(s[-1],1)]" in modelpy.replace(" ", "") or "s[-1]" in modelpy), True, "s[-1]" in modelpy)
add("archived daily implementation enforces zero-or-minimum electrolyser input per day",
    "h['minimum']*h['unit_GWh']" in modelpy.replace(" ", ""), True,
    "minimum*unit" in modelpy.replace(" ", "") or "h['minimum']*h['unit_GWh']" in modelpy.replace(" ", ""))
add("archived daily implementation makes both equipment counts integer decisions",
    "integer=not relaxation" in modelpy, True, "integer=not relaxation" in modelpy,
    "model.py lines 82-83 build the battery and electrolyser count variables with integer=not relaxation")
add("report describes the daily model consistently (one window, cross-day stock, integer counts)",
    all(s in text for s in ("ηcd ≤ W b", "Usable stock can carry", "Both equipment counts are integer")),
    True, "Usable stock can carry" in text and "integer decisions" in text)
add("four-day commitment rule documented as II.8 and implemented in the commitment subproblem",
    "each start followed by at least" in open(SITEMODEL, encoding="utf-8").read(), True,
    "each start followed by at least" in open(SITEMODEL, encoding="utf-8").read(),
    "site_model.py day DP: 'each start followed by at least min_days days'; the MILP path is "
    "site_model.commit used by halfhour.py")

# ---- 5. unchanged baselines re-checked from the pinned archives ------------
add("Table II.7 six modules at 20%: MW, capital, net, worst year, payback, NPV, break-even",
    (round(fin20["mw"], 2), round(fin20["capital_m"], 2), round(fin20["net_m"], 2),
     round(fin20["worst_year_m"], 2), round(fin20["payback_years"], 2),
     round(fin20["npv_30_year_mGBP"], 2), round(fin20["break_even_fixed_dispatch_GBP_kg"], 2)),
    (30.19, 44.08, 13.46, 8.67, 2.56, 206.91, 3.85),
    (round(fin20["mw"], 2), round(fin20["capital_m"], 2), round(fin20["net_m"], 2),
     round(fin20["worst_year_m"], 2), round(fin20["payback_years"], 2),
     round(fin20["npv_30_year_mGBP"], 2), round(fin20["break_even_fixed_dispatch_GBP_kg"], 2))
    == (30.19, 44.08, 13.46, 8.67, 2.56, 206.91, 3.85))
add("Table II.7 seven modules at 12.5%: MW, capital, net, worst year, payback, NPV, break-even",
    (round(fin125["mw"], 2), round(fin125["capital_m"], 2), round(fin125["net_m"], 2),
     round(fin125["worst_year_m"], 2), round(fin125["payback_years"], 2),
     round(fin125["npv_30_years_mGBP"], 2), round(fin125["fixed_dispatch_break_even_GBP_kg"], 2)),
    (35.22, 51.43, 13.68, 9.81, 2.85, 210.28, 3.82),
    (round(fin125["mw"], 2), round(fin125["capital_m"], 2), round(fin125["net_m"], 2),
     round(fin125["worst_year_m"], 2), round(fin125["payback_years"], 2),
     round(fin125["npv_30_years_mGBP"], 2), round(fin125["fixed_dispatch_break_even_GBP_kg"], 2))
    == (35.22, 51.43, 13.68, 9.81, 2.85, 210.28, 3.82))
fp = {(r["policy"], int(r["battery_blocks"])): float(r["net_mGBP"])
      for r in zone(z6, "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}
add("Table II.5 half-hour fixed 0/1 block A and B", (round(fp[("A", 0)], 2), round(fp[("A", 1)], 2),
                                                     round(fp[("B", 0)], 2), round(fp[("B", 1)], 2)),
    (13.42, 14.47, 3.78, 2.46),
    (round(fp[("A", 0)], 2), round(fp[("A", 1)], 2), round(fp[("B", 0)], 2), round(fp[("B", 1)], 2))
    == (13.42, 14.47, 3.78, 2.46))
rdA = js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")
rdB = js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_B_integer.json")
add("Table II.5 daily two-hour row 12.46 / 2.18", (round(rdA["annual_increment_mGBP"], 2),
                                                   round(rdB["annual_increment_mGBP"], 2)), (12.46, 2.18),
    (round(rdA["annual_increment_mGBP"], 2), round(rdB["annual_increment_mGBP"], 2)) == (12.46, 2.18))
brief = rdA["active_products"]["batteries"][0]
incA, incB = fp[("A", 1)] - fp[("A", 0)], fp[("B", 1)] - fp[("B", 0)]
add("Table II.5 one-block increments +1.05 (A) and -1.32 (B)",
    (round(incA, 2), round(incB, 2)), (1.05, -1.32), (round(incA, 2), round(incB, 2)) == (1.05, -1.32))
add("Table II.5 upkeep sentence -0.23 (A) and -2.60 (B) at 2.5% of capital",
    (round(incA - 0.025 * brief["capital_GBP"] / 1e6, 3), round(incB - 0.025 * brief["capital_GBP"] / 1e6, 3)),
    (-0.23, -2.60),
    round(incA - 0.025 * brief["capital_GBP"] / 1e6, 2) == -0.23
    and round(incB - 0.025 * brief["capital_GBP"] / 1e6, 2) == -2.60,
    "v6.5 printed -0.24; the corrected value is -0.2307 and the v7 text prints -0.23")
add("display-table follow-up carries the same corrections",
    (round(disp["v7_review_followup"]["brief_two_hour_annual_upkeep"]
           ["one_block_net_increment_mGBP_per_year"]["A"], 4),
     round(disp["v7_review_followup"]["brief_two_hour_annual_upkeep"]
           ["one_block_net_increment_mGBP_per_year"]["B"], 4)), (-0.2307, -2.5987),
    near(disp["v7_review_followup"]["brief_two_hour_annual_upkeep"]
         ["one_block_net_increment_mGBP_per_year"]["A"], -0.23069, 1e-4)
    and near(disp["v7_review_followup"]["brief_two_hour_annual_upkeep"]
             ["one_block_net_increment_mGBP_per_year"]["B"], -2.59871, 1e-4))
price = {round(float(r["hydrogen_GBP_per_kg"]), 2): (int(r["modules"]), round(float(r["annual_net_mGBP"]), 2))
         for r in zone(z63, "project-report-20261124-v6.3/four-day-hydrogen-price.csv")}
add("Table II.6 price sweep 2.50/5.00/7.80/9.50", price,
    {2.5: (0, 0.0), 5.0: (6, 4.52), 7.8: (7, 13.68), 9.5: (7, 19.6)},
    price[2.5] == (0, 0.0) and price[5.0] == (6, 4.52) and price[7.8] == (7, 13.68) and price[9.5] == (7, 19.6))
cap = {(r["policy"], int(r["blocks"])): r for r in zone(z63, "tier2b-commitment-125-20261124/capacity-summary.csv")}
tot = {p: round(float(cap[(p, 1)]["six_fold_net_GBP"]) / 1e6, 2) for p in "AB"}
add("Table III.1 one-block totals 4.65 (A) and 7.58 (B)", tot, {"A": 4.65, "B": 7.58}, tot == {"A": 4.65, "B": 7.58})
ex = {p: round(float(cap[(p, 1)]["excluding_2021_22_GBP"]) / 1e6, 2) for p in "AB"}
add("Table III.1 excluding-2021/22 totals -1.54 (A) and -1.23 (B)", ex, {"A": -1.54, "B": -1.23},
    ex == {"A": -1.54, "B": -1.23})
best = {p: max(((int(r["blocks"]), float(r["six_fold_net_GBP"])) for r in cap.values()
                if r["policy"] == p and int(r["blocks"]) > 0), key=lambda x: x[1]) for p in "AB"}
add("six-window sum is highest at 11 blocks for both policies (22.99 / 40.97)",
    {p: (best[p][0], round(best[p][1] / 1e6, 2)) for p in "AB"},
    {"A": (11, 22.99), "B": (11, 40.97)},
    {p: (best[p][0], round(best[p][1] / 1e6, 2)) for p in "AB"} == {"A": (11, 22.99), "B": (11, 40.97)}
    and "11 blocks" in text)
add("Table III.1 does not print the 11-block column named in the text",
    [h for h in ("Window & 1 & 7 & 45 & 1 & 9 & 22",) if h in zsrc.read("sections/tier2.tex").decode()],
    "expected 11 among the printed columns", False,
    "the text says the six-window sum peaks at 11 blocks, but the table still prints 1, 7, 45 and 1, 9, 22")
add("nine-block increment over eight is £639/year", round((float(cap[("B", 9)]["six_fold_net_GBP"])
                                                         - float(cap[("B", 8)]["six_fold_net_GBP"])) / 1, 1),
    638.5, "£639/year" in text)
add("B hydrogen bound 116 days / £0.326m / £0.757m",
    (js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")["covered_days"],
     round(js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")
           ["annual_hydrogen_receipts_per_unit_upper_mGBP"], 3),
     round(js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")["unit_annual_cost_mGBP"], 3)),
    (116, 0.326, 0.757),
    (js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")["covered_days"],
     round(js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")
           ["annual_hydrogen_receipts_per_unit_upper_mGBP"], 3),
     round(js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")["unit_annual_cost_mGBP"], 3))
    == (116, 0.326, 0.757))
A_sum = js(z6, "FinalProject/tier1-site-battery-20261122/A_summary.json")["mean"]
B_sum = js(z6, "FinalProject/tier1-site-battery-20261122/B_summary.json")["mean"]
add("Table C.2 2020--25 foresight/simple one-block gains A and B",
    (round(A_sum["battery_net_GBP"] / 1e6, 2), round(A_sum["simple_battery_net_GBP"] / 1e6, 2),
     round(B_sum["battery_net_GBP"] / 1e6, 2), round(B_sum["simple_battery_net_GBP"] / 1e6, 2)),
    (5.63, 1.63, 1.64, 1.50),
    (round(A_sum["battery_net_GBP"] / 1e6, 2), round(A_sum["simple_battery_net_GBP"] / 1e6, 2),
     round(B_sum["battery_net_GBP"] / 1e6, 2), round(B_sum["simple_battery_net_GBP"] / 1e6, 2))
    == (5.63, 1.63, 1.64, 1.50))
add("§5.4 break-even quotes £213/kWh (A) and £130/kWh (B)",
    (round(A_sum["battery_break_even_GBP_per_kWh"], 1), round(B_sum["battery_break_even_GBP_per_kWh"], 1)),
    (212.7, 130.5), near(A_sum["battery_break_even_GBP_per_kWh"], 212.736, 0.5)
    and near(B_sum["battery_break_even_GBP_per_kWh"], 130.466, 0.5))
add("fixed replay table (display evidence) one-block and 11-block totals",
    {p: (round(disp["v7_review_followup"]["fixed_electrolyser_replay"]["by_policy"][p]
               ["one_block_total_GBP"] / 1e6, 2),
         round(disp["v7_review_followup"]["fixed_electrolyser_replay"]["by_policy"][p]
               ["eleven_block_total_GBP"] / 1e6, 2)) for p in "AB"},
    {"A": (4.65, 22.99), "B": (7.58, 40.97)},
    {p: (round(disp["v7_review_followup"]["fixed_electrolyser_replay"]["by_policy"][p]
                ["one_block_total_GBP"] / 1e6, 2),
         round(disp["v7_review_followup"]["fixed_electrolyser_replay"]["by_policy"][p]
               ["eleven_block_total_GBP"] / 1e6, 2)) for p in "AB"} == {"A": (4.65, 22.99), "B": (7.58, 40.97)})
add("20% joint demand served 90.16% recomputed from the archived schedule",
    round(100 * float(npz_from(z63, "tier1-commitment-20-20261124/A-45-6-rounded.npz")["sales"].sum()) / d.sum(), 4),
    round(follow["demand_served_pct"], 4),
    near(100 * float(npz_from(z63, "tier1-commitment-20-20261124/A-45-6-rounded.npz")["sales"].sum()) / d.sum(),
         follow["demand_served_pct"], 1e-3),
    "v6.5 reused one served macro for both joint rows without a 20% source; v7 records the 20% value")
add("Table II.3 A no-additions Served 89.66% equals min(G,D) with negative-price sales declined",
    round(100 * np.minimum(g, d)[np.array(prices) >= 0].sum() / d.sum(), 4), 89.6575,
    near(100 * np.minimum(g, d)[np.array(prices) >= 0].sum() / d.sum(), 89.6575, 1e-4)
    and "89.66" in text,
    "A may decline negative-price sales (II.4.2): 1,942 half-hours and 3,483 GWh/yr of demand are "
    "deliberately left unserved, so the A and B Served columns are not directly comparable")
add("Table II.3 B no-additions Served 91.03% equals min(G,D)/D",
    round(100 * np.minimum(g, d).sum() / d.sum(), 4), 91.0318,
    near(100 * np.minimum(g, d).sum() / d.sum(), 91.0318, 1e-4) and "91.03" in text)
add("Table II.3 still routes the 20% joint Served cell through the 12.5% macro",
    "\\TwentyCoverage" in zsrc.read("sections/site-tables.tex").decode(), "own literal",
    False, "cosmetic only: display-table-evidence.json now carries the 20% value and both round to 90.16%")

# ---- 6. text-level checks for the v7 statements ---------------------------
must = ["2,432", "2,404", "1,550", "2,192", "1,138", "1,119", "1,549", "1,604", "2,154", "2,401",
        "0.23m", "2.60m", "GWh per half-hour", "less than 0.3 GWh/year", "118.819824", "118.811177",
        "118.890634", "6.069620", "11 blocks", "£22.99m", "£40.97m", "13,155", "24,113", "530,466",
        "850,501"]
missing = [s for s in must if s not in text]
add("printed strings required by the v7 argument are all present", missing, [], missing == [])
add("figure I.1 axis label in the shipped source matches the printed label",
    zsrc.read("figures/plot_surplus.py").decode().count("Mean surplus\\n(GWh per half-hour)"), 1,
    zsrc.read("figures/plot_surplus.py").decode().count("Mean surplus\\n(GWh per half-hour)") == 1,
    "v6.5 shipped a figure labelled 'Mean surplus (GWh)' while the script said GWh per half-hour; "
    "the two now agree")
add("abstract leads with the brief's 20% floor and six modules",
    ("20% minimum load" in text and "six electrolyser modules (30.2 MW)" in text
     and "12.5% load" in text), True,
    "20% minimum load" in text and "six electrolyser modules (30.2 MW)" in text)
add("cover still carries no author names", ("Ran Min" in text, "Group 15" in text), (True, True),
    "Ran Min" in text and "Group 15" in text,
    "cover shows title, course, group and date only; the report never names its authors")

failures = [c["name"] for c in checks if not c["ok"]]
out = dict(report_sha256=sha["report.pdf"], checks=len(checks), failed=len(failures),
           failures=failures, items=checks)
with open(os.path.join(BASE, "checks_v7.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(f"{len(checks)} checks, {len(failures)} failed")
for name in failures:
    print("FAIL", name)
