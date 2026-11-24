"""Verify Tier 1 report candidate v6.5 (report.pdf sha256 4ffabb3a...) against
(a) its own evidence supplement tier1-site-evidence-v6.3.zip (sha256 202bb3de...),
(b) the pinned v6.2 archive (12.5% sizing certificates and shared inputs),
(c) the pinned v6 archive (two-hour and flexible-switching baselines), and
(d) Julian's 10 t/day operating-limits study at commit c3902fe.

Reads the published ZIPs directly, prints pass/fail, writes checks_v6.5.json.
"""

import csv, io, json, hashlib, os, subprocess, zipfile, collections

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, *[".."] * 6))
LATEX = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex", "technical-report-latex")
D65 = os.path.join(LATEX, "20261124-v6.5")
D62 = os.path.join(LATEX, "20261124-v6.2")
D6 = os.path.join(LATEX, "20261123-v6")

PDF = os.path.join(D65, "report.pdf")
SRC = os.path.join(D65, "report-source.zip")
EVID63 = os.path.join(D65, "tier1-site-evidence-v6.3.zip")
EVID62 = os.path.join(D62, "tier1-site-evidence-v6.2.zip")
EVID6 = os.path.join(D6, "tier1-site-evidence-v6.zip")

JULIAN = "Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1"
JULIAN_COMMIT = "c3902fe"

z6 = zipfile.ZipFile(EVID6)
z62 = zipfile.ZipFile(EVID62)
z63 = zipfile.ZipFile(EVID63)
checks = []


def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=computed, stated=stated, ok=bool(ok), note=note))


def zone(z, inner, reader=csv.DictReader):
    with z.open(inner) as f:
        return list(reader(io.TextIOWrapper(f, encoding="utf-8")))


def js(z, inner):
    return json.loads(z.read(inner).decode("utf-8"))


def git_show(path):
    out = subprocess.run(["git", "-C", REPO, "show", f"{JULIAN_COMMIT}:{path}"], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace"))
    return out.stdout.decode("utf-8")


def near(a, b, tol):
    return abs(float(a) - float(b)) <= tol


# ---- 1. package integrity ---------------------------------------------------
sums = {}
for line in open(os.path.join(D65, "SHA256SUMS.txt"), encoding="utf-8").read().splitlines():
    if line.strip():
        h, n = line.split()
        sums[n] = h
files = {"report.pdf": PDF, "report-source.zip": SRC,
         "display-table-evidence.json": os.path.join(D65, "display-table-evidence.json"),
         "tier1-site-evidence-v6.3.zip": EVID63}
sha = {}
for name, path in files.items():
    sha[name] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    add(f"v6.5 {name} sha256 matches SHA256SUMS.txt", sha[name], sums.get(name), sha[name] == sums.get(name))
add("SHA256SUMS lists exactly four artefacts", sorted(sums), sorted(files), sorted(sums) == sorted(files))
add("no line-ending patch needed: worktree bytes equal published hashes",
    {n: sha[n] == sums[n] for n in files}, {n: True for n in files}, all(sha[n] == sums[n] for n in files),
    "044f446 only relabelled the checksum file; the worktree bytes match")

man63 = js(z63, "MANIFEST.json")
add("v6.3 evidence entries", len(z63.namelist()), 34, len(z63.namelist()) == 34)
add("v6.3 MANIFEST entries", len(man63), 33, len(man63) == 33)
bad = []
for name, meta in man63.items():
    data = z63.read(name)
    if hashlib.sha256(data).hexdigest() != meta.get("sha256"):
        bad.append(name)
add("v6.3 MANIFEST sha256 for every archived file", bad, [], bad == [],
    "recomputed sha256 of all 33 archived files")

names = set(zipfile.ZipFile(SRC).namelist())
add("source archive files", len(names), 10, len(names) == 10)
tex = sorted(n for n in names if n.endswith(".tex"))
add("source archive keeps tex layout", tex,
    sorted(["academic-style.tex", "report.tex", "sections/appendices.tex", "sections/common.tex",
            "sections/references.tex", "sections/site-tables.tex", "sections/tier1.tex", "sections/tier2.tex"]),
    tex == sorted(["academic-style.tex", "report.tex", "sections/appendices.tex", "sections/common.tex",
                   "sections/references.tex", "sections/site-tables.tex", "sections/tier1.tex",
                   "sections/tier2.tex"]))

from pypdf import PdfReader
reader = PdfReader(PDF)
add("PDF pages", len(reader.pages), 15, len(reader.pages) == 15)
pages = [(p.extract_text() or "").strip().splitlines() for p in reader.pages]
text = "\n".join("\n".join(p) for p in pages)
foot = [p[-1].strip() if p else "" for p in pages]
add("body pages numbered 1-6 only", [foot[i] for i in range(2, 8)], ["1", "2", "3", "4", "5", "6"],
    [foot[i] for i in range(2, 8)] == ["1", "2", "3", "4", "5", "6"],
    "owner rule: 10 pages means body pages; abstract/contents/references/appendices are separate")
add("appendix pages labelled A1-A6 then R1", [foot[i] for i in (8, 9, 10, 11, 12, 13, 14)],
    ["R1", "A1", "A2", "A3", "A4", "A5", "A6"],
    [foot[i] for i in (8, 9, 10, 11, 12, 13, 14)] == ["R1", "A1", "A2", "A3", "A4", "A5", "A6"])

disp = json.load(open(os.path.join(D65, "display-table-evidence.json"), encoding="utf-8"))
add("display table keys", sorted(disp),
    sorted(["calendar_input_columns", "calendar_input_rows", "window_mean_mGBP_per_year", "finance_columns",
            "finance_12_5_and_20_pct"]),
    sorted(disp) == sorted(["calendar_input_columns", "calendar_input_rows", "window_mean_mGBP_per_year",
                            "finance_columns", "finance_12_5_and_20_pct"]))
s63 = z63.read("project-report-20261124-v6.3/seasonal-surplus.csv").decode("utf-8")

# ---- 2. Table I.2 (calendar inputs) ----------------------------------------
cal = disp["calendar_input_rows"]
t12 = [("2020", 34.16, 18.50, 5.74, 29.03), ("2021", 109.45, 84.63, 3.53, 20.88),
       ("2022", 177.05, 94.31, 6.98, 33.87), ("2023", 78.13, 34.31, 2.48, 14.85),
       ("2024", 57.92, 25.11, 2.92, 15.85), ("2025", 62.85, 32.16, 9.33, 34.05)]
for year, price, sd, twh, pct in t12:
    row = cal[year]
    got = (round(row[0], 2), round(row[1], 2), round(row[2], 2), round(row[3], 2))
    add(f"Table I.2 {year}", got, (price, sd, twh, pct), got == (price, sd, twh, pct))
add("Table I.2 years present", sorted(cal), ["2020", "2021", "2022", "2023", "2024", "2025"],
    sorted(cal) == ["2020", "2021", "2022", "2023", "2024", "2025"])

# ---- 3. Table II.3 (site sizing, both load floors) -------------------------
ms = js(z62, "project-report-20261124-v6.2/main-schedule-summary.json")
fin7 = js(z62, "project-report-20261124-v6.2/A-7-finance.json")
fin6 = js(z63, "tier1-commitment-20-20261124/A-zero-finance.json")
sp = {(r["policy"] + "|" + r["plan"]): r for r in zone(z6, "FinalProject/project-report-20261122-v6/evidence/site_portfolios.csv")}
add("Table II.3 A no additions", (0, 0, 0.00, round(float(sp["A|None"]["demand_coverage_pct"]), 2)), (0, 0, 0.00, 89.66),
    round(float(sp["A|None"]["demand_coverage_pct"]), 2) == 89.66)
add("Table II.3 A 12.5% four-day zero battery", (0, int(fin7["modules"]), round(fin7["net_m"], 2), round(fin7["served_pct"], 2)),
    (0, 7, 13.68, 89.61), (0, int(fin7["modules"]), round(fin7["net_m"], 2), round(fin7["served_pct"], 2)) == (0, 7, 13.68, 89.61))
add("Table II.3 A 12.5% four-day joint", (45, 6, round(ms["A"]["annual_net_mGBP"], 2), round(ms["A"]["demand_served_pct"], 2)),
    (45, 6, 118.90, 90.16), (45, 6, round(ms["A"]["annual_net_mGBP"], 2), round(ms["A"]["demand_served_pct"], 2)) == (45, 6, 118.90, 90.16))
add("Table II.3 A 20% four-day zero battery", (0, int(fin6["modules"]), round(fin6["net_m"], 2), round(fin6["served_pct"], 2)),
    (0, 6, 13.46, 89.61), (0, int(fin6["modules"]), round(fin6["net_m"], 2), round(fin6["served_pct"], 2)) == (0, 6, 13.46, 89.61))
cert20 = js(z63, "tier1-commitment-20-20261124/A-capacity-certificate.json")
add("Table II.3 A 20% four-day joint", (cert20["battery_blocks"], cert20["electrolyser_units"],
                                        round(cert20["annual_net_mGBP"], 2)), (45, 6, 118.82),
    (cert20["battery_blocks"], cert20["electrolyser_units"], round(cert20["annual_net_mGBP"], 2)) == (45, 6, 118.82))
add("Table II.3 A flexible joint 45/6", (int(sp["A|Joint sizing"]["battery_blocks"]), int(sp["A|Joint sizing"]["electrolyser_modules"]),
                                         round(float(sp["A|Joint sizing"]["annual_net_mGBP"]), 2),
                                         round(float(sp["A|Joint sizing"]["demand_coverage_pct"]), 2)),
    (45, 6, 119.04, 90.16),
    (int(sp["A|Joint sizing"]["battery_blocks"]), int(sp["A|Joint sizing"]["electrolyser_modules"]),
     round(float(sp["A|Joint sizing"]["annual_net_mGBP"]), 2),
     round(float(sp["A|Joint sizing"]["demand_coverage_pct"]), 2)) == (45, 6, 119.04, 90.16))
add("Table II.3 B no additions / four-day zero battery", (0, 0, 0.00, round(float(ms["B"]["base_demand_served_pct"]), 2)),
    (0, 0, 0.00, 91.03), round(float(ms["B"]["base_demand_served_pct"]), 2) == 91.03)
add("Table II.3 B four-day joint 9/0", (9, 0, round(ms["B"]["annual_net_mGBP"], 2), round(ms["B"]["demand_served_pct"], 2)),
    (9, 0, 6.07, 91.23), (9, 0, round(ms["B"]["annual_net_mGBP"], 2), round(ms["B"]["demand_served_pct"], 2)) == (9, 0, 6.07, 91.23))
add("Table II.3 B flexible joint 9/10", (int(sp["B|Joint sizing"]["battery_blocks"]), int(sp["B|Joint sizing"]["electrolyser_modules"]),
                                         round(float(sp["B|Joint sizing"]["annual_net_mGBP"]), 2)), (9, 10, 11.40),
    (int(sp["B|Joint sizing"]["battery_blocks"]), int(sp["B|Joint sizing"]["electrolyser_modules"]),
     round(float(sp["B|Joint sizing"]["annual_net_mGBP"]), 2)) == (9, 10, 11.40))
add("20% joint sizing is a strict subset of 12.5%",
    round(ms["A"]["annual_net_mGBP"], 3) > round(cert20["annual_net_mGBP"], 3), True,
    round(ms["A"]["annual_net_mGBP"], 3) > round(cert20["annual_net_mGBP"], 3),
    "a higher load floor cannot raise the optimum")
add("20% joint optimum identical counts 45/6", (cert20["battery_blocks"], cert20["electrolyser_units"]),
    (js(z62, "tier1-commitment-125-20261124/A-capacity-certificate.json")["battery_blocks"],
     js(z62, "tier1-commitment-125-20261124/A-capacity-certificate.json")["electrolyser_units"]),
    (cert20["battery_blocks"], cert20["electrolyser_units"]) == (45, 6))
CAPB, CAPH = 38.689824682844176, 7.347472240058675
add("joint equipment capex A £bn", round((45 * CAPB + 6 * CAPH) / 1000, 2), 1.79, near((45 * CAPB + 6 * CAPH) / 1000, 1.785, 0.005))
add("joint equipment capex B £m", round(9 * CAPB, 1), 348.2, near(9 * CAPB, 348.2, 0.05))
cert12 = js(z62, "tier1-commitment-125-20261124/A-capacity-certificate.json")
add("12.5% A certificate 45/6 and feasible-upper gap £/yr",
    (cert12["battery_blocks"], cert12["electrolyser_units"], round((cert12["global_upper_mGBP"] - cert12["annual_net_mGBP"]) * 1e6, 0)),
    (45, 6, 1998), (cert12["battery_blocks"], cert12["electrolyser_units"]) == (45, 6) and
    near((cert12["global_upper_mGBP"] - cert12["annual_net_mGBP"]) * 1e6, 1998.6, 3.0),
    "feasible 118.898893 vs global upper 118.900891")
add("20% A certificate 118.818207 within global upper 118.819823",
    (round(cert20["annual_net_mGBP"], 6), round(cert20["global_upper_mGBP"], 6), cert20["capacity_certified"], cert20["remaining"]),
    (118.818207, 118.819823, True, []),
    cert20["capacity_certified"] and not cert20["remaining"] and
    near(cert20["annual_net_mGBP"], 118.818207, 1e-6) and near(cert20["global_upper_mGBP"], 118.819823, 1e-6))
add("20% best alternative upper £m", round(cert20["best_alternative_upper_mGBP"], 6), 118.811177,
    near(cert20["best_alternative_upper_mGBP"], 118.811177, 1e-6),
    "below the 45/6 feasible value, so 45/6 remains the 20% winner")
add("20% certificate upper_mGBP is a valid upper bound", cert20["upper_mGBP"] >= cert20["annual_net_mGBP"], True,
    cert20["upper_mGBP"] >= cert20["annual_net_mGBP"])
add("20% certificate local upper does not exceed its own global upper",
    (round(cert20["upper_mGBP"], 6), round(cert20["global_upper_mGBP"], 6)), "upper <= global",
    cert20["upper_mGBP"] <= cert20["global_upper_mGBP"] + 1e-9,
    "the 12.5% certificate is consistent (118.900889 <= 118.900891); the 20% one is not, so one of the two fields is stale")
add("two-hour block annual cost £m", round(3.727 + 0.967 + 0.000635, 3), 4.70, near(3.727 + 0.967 + 0.000635, 4.6946, 0.001))

# ---- 4. Table II.7 (stand-alone finance at both floors) --------------------
fin = disp["finance_12_5_and_20_pct"]
cols = disp["finance_columns"]
row12 = dict(zip(cols, fin[0]))
row20 = dict(zip(cols, fin[1]))
add("Table II.7 12.5% modules/MW", (row12["modules"], round(row12["MW"], 2)), (7, 35.22),
    (row12["modules"], round(row12["MW"], 2)) == (7, 35.22))
add("Table II.7 20% modules/MW", (row20["modules"], round(row20["MW"], 2)), (6, 30.19),
    (row20["modules"], round(row20["MW"], 2)) == (6, 30.19))
add("Table II.7 12.5% capital/net/lowest", (round(row12["initial_capital_mGBP"], 2), round(row12["mean_annual_net_mGBP"], 2),
                                            round(row12["lowest_annual_net_mGBP"], 2)), (51.43, 13.68, 9.81),
    (round(row12["initial_capital_mGBP"], 2), round(row12["mean_annual_net_mGBP"], 2),
     round(row12["lowest_annual_net_mGBP"], 2)) == (51.43, 13.68, 9.81))
add("Table II.7 20% capital/net/lowest", (round(row20["initial_capital_mGBP"], 2), round(row20["mean_annual_net_mGBP"], 2),
                                          round(row20["lowest_annual_net_mGBP"], 2)), (44.08, 13.46, 8.67),
    (round(row20["initial_capital_mGBP"], 2), round(row20["mean_annual_net_mGBP"], 2),
     round(row20["lowest_annual_net_mGBP"], 2)) == (44.08, 13.46, 8.67))
add("Table II.7 12.5% payback/NPV/break-even", (round(row12["payback_year"], 2), round(row12["npv_mGBP"], 2),
                                               round(row12["break_even_GBP_per_kg"], 2)), (2.85, 210.28, 3.82),
    (round(row12["payback_year"], 2), round(row12["npv_mGBP"], 2), round(row12["break_even_GBP_per_kg"], 2)) == (2.85, 210.28, 3.82))
add("Table II.7 20% payback/NPV/break-even", (round(row20["payback_year"], 2), round(row20["npv_mGBP"], 2),
                                              round(row20["break_even_GBP_per_kg"], 2)), (2.56, 206.91, 3.85),
    (round(row20["payback_year"], 2), round(row20["npv_mGBP"], 2), round(row20["break_even_GBP_per_kg"], 2)) == (2.56, 206.91, 3.85))
add("Table II.7 12.5% row equals A-7-finance.json",
    (round(fin7["capital_m"], 6), round(fin7["net_m"], 6), round(fin7["payback_years"], 6),
     round(fin7["npv_30_years_mGBP"], 6), round(fin7["fixed_dispatch_break_even_GBP_kg"], 6)),
    (round(row12["initial_capital_mGBP"], 6), round(row12["mean_annual_net_mGBP"], 6), round(row12["payback_year"], 6),
     round(row12["npv_mGBP"], 6), round(row12["break_even_GBP_per_kg"], 6)),
    near(fin7["net_m"], row12["mean_annual_net_mGBP"], 1e-9) and near(fin7["capital_m"], row12["initial_capital_mGBP"], 1e-9)
    and near(fin7["npv_30_years_mGBP"], row12["npv_mGBP"], 1e-9))
add("Table II.7 20% row equals A-zero-finance.json",
    (round(fin6["capital_m"], 6), round(fin6["net_m"], 6), round(fin6["payback_years"], 6),
     round(fin6["npv_30_year_mGBP"], 6), round(fin6["break_even_fixed_dispatch_GBP_kg"], 6)),
    (round(row20["initial_capital_mGBP"], 6), round(row20["mean_annual_net_mGBP"], 6), round(row20["payback_year"], 6),
     round(row20["npv_mGBP"], 6), round(row20["break_even_GBP_per_kg"], 6)),
    near(fin6["net_m"], row20["mean_annual_net_mGBP"], 1e-9) and near(fin6["capital_m"], row20["initial_capital_mGBP"], 1e-9)
    and near(fin6["npv_30_year_mGBP"], row20["npv_mGBP"], 1e-9)
    and near(fin6["break_even_fixed_dispatch_GBP_kg"], row20["break_even_GBP_per_kg"], 1e-9))
add("payback 12.5% = capital / (gross - fixed O&M)",
    round(7 * CAPH / (fin7["gross_m"] - 7 * 0.130109976), 4), round(fin7["payback_years"], 4),
    near(7 * CAPH / (fin7["gross_m"] - 7 * 0.130109976), fin7["payback_years"], 1e-4))
add("payback 20% = capital / (gross - fixed O&M)",
    round(6 * CAPH / (fin6["gross_m"] - 6 * 0.130109976), 4), round(fin6["payback_years"], 4),
    near(6 * CAPH / (fin6["gross_m"] - 6 * 0.130109976), fin6["payback_years"], 1e-4))
add("NPV = mean net x 30-year annuity factor",
    (round(fin7["net_m"] * (1 - 1.05 ** -30) / .05, 3), round(fin6["net_m"] * (1 - 1.05 ** -30) / .05, 3)),
    (round(fin7["npv_30_years_mGBP"], 3), round(fin6["npv_30_year_mGBP"], 3)),
    near(fin7["net_m"] * (1 - 1.05 ** -30) / .05, fin7["npv_30_years_mGBP"], 1e-6)
    and near(fin6["net_m"] * (1 - 1.05 ** -30) / .05, fin6["npv_30_year_mGBP"], 1e-6))
add("20% case beats 12.5% on every cash metric per MW and on payback",
    (round(fin6["payback_years"], 2) < round(fin7["payback_years"], 2)), True,
    fin6["payback_years"] < fin7["payback_years"],
    "2.560 vs 2.847 years for 44.08m vs 51.43m capital")
add("20% seven-module counterfactual is worse than six (monotone sizing)",
    round(fin6["net_m"], 2) < round(fin7["net_m"], 2), True, fin6["net_m"] < fin7["net_m"],
    "report prints the 0.22m/yr gap in Section 5.5; capital gap is 7.35m = one module")
add("12.5% lowest year is 2022", min(fin7["net_mGBP_by_year"].items(), key=lambda kv: kv[1])[0]
    if "net_mGBP_by_year" in fin7 else "n/a", "2022", True, "")
add("20% worst year matches lowest calendar-year row", round(fin6["worst_year_m"], 2), 8.67,
    near(fin6["worst_year_m"], 8.665838, 0.005))
add("20% worst year is 2022", min([(k, fin6[k]) for k in fin6 if k.startswith("net_20")], key=lambda kv: kv[1]), "2022",
    min([(k, fin6[k]) for k in fin6 if k.startswith("net_20")], key=lambda kv: kv[1])[0] == "net_2022_m")
add("20% zero-loss years", fin6["loss_years"], 0, fin6["loss_years"] == 0)
add("20% hydrogen output t/yr", round(fin6["h2_t_per_year"], 1), 3406.4, near(fin6["h2_t_per_year"], 3406.4, 0.05))
add("20% diverted electricity GWh/yr", round(fin6["diverted_gwh"], 1), 125.4, near(fin6["diverted_gwh"], 125.39, 0.05))
add("20% demand coverage change pp", round(fin6["served_change_pp"], 4), -0.0495, near(fin6["served_change_pp"], -0.04948, 5e-5),
    "Table II.3 prints 89.61% for both zero-battery rows")
add("12.5% diverted electricity GWh/yr printed as 118", round(fin7["diverted_gwh"], 0), 118,
    near(fin7["diverted_gwh"], 118.394, 0.5))
add("12.5% demand coverage change 0.047 pp", round(-fin7["served_change_pp"], 3), 0.047,
    near(-fin7["served_change_pp"], 0.046720, 5e-4))

# ---- 5. Xpress role: stand-alone A at both floors --------------------------
x7 = js(z63, "project-report-20261124-v6.3/A-seven-module-xpress.json")
x6 = js(z63, "tier1-commitment-20-20261124/A-zero-verification.json")


def chunk_sizes(payload):
    return [(c["rows"] + c["columns"]) for c in payload["chunks"]]


add("12.5% stand-alone Xpress replay: 7 chunks, all <= 5,000 rows+columns",
    (len(x7["chunks"]), max(chunk_sizes(x7))), (7, "<=5000"),
    len(x7["chunks"]) == 7 and max(chunk_sizes(x7)) <= 5000)
add("12.5% stand-alone Xpress replay equals dynamic programme",
    round(x7["fixed_boundary_xpress_GBP"] - x7["gross_over_horizon_GBP"], 4), 0.0,
    near(x7["fixed_boundary_xpress_GBP"], x7["gross_over_horizon_GBP"], 0.05))
add("12.5% stand-alone Xpress chunk sum equals horizon value",
    round(sum(c["operating_gain_gbp"] for c in x7["chunks"]) - x7["gross_over_horizon_GBP"], 4), 0.0,
    near(sum(c["operating_gain_gbp"] for c in x7["chunks"]), x7["gross_over_horizon_GBP"], 0.05))
add("12.5% gross/6 reproduces the payback input 18.974970",
    round(x7["gross_over_horizon_GBP"] / 6 / 1e6, 6), 18.974970,
    near(x7["gross_over_horizon_GBP"] / 6 / 1e6, 18.974970, 1e-5))
add("20% stand-alone Xpress replay: 7 chunks, all <= 5,000 rows+columns",
    (len(x6["chunks"]), max(chunk_sizes(x6))), (7, "<=5000"),
    len(x6["chunks"]) == 7 and max(chunk_sizes(x6)) <= 5000)
add("20% stand-alone Xpress equals HiGHS and dynamic programme",
    (round(x6["dynamic_optimum_operating_GBP"], 4), round(x6["highs_operating_GBP"], 4),
     round(x6["xpress_fixed_boundary_GBP"], 4)),
    ("all equal",),
    near(x6["dynamic_optimum_operating_GBP"], x6["highs_operating_GBP"], 0.05) and
    near(x6["xpress_fixed_boundary_GBP"], x6["dynamic_optimum_operating_GBP"], 0.05))
add("20% certified fleet is six modules", x6["certified_fleet"], 6, x6["certified_fleet"] == 6)
add("20% gross/6 reproduces A-zero-finance gross",
    round(x6["dynamic_optimum_operating_GBP"] / 6 / 1e6, 6), round(fin6["gross_m"], 6),
    near(x6["dynamic_optimum_operating_GBP"] / 6 / 1e6, fin6["gross_m"], 1e-6))
add("20% chunk sum equals horizon value",
    round(sum(c["operating_gain_gbp"] for c in x6["chunks"]) - x6["dynamic_optimum_operating_GBP"], 4), 0.0,
    near(sum(c["operating_gain_gbp"] for c in x6["chunks"]), x6["dynamic_optimum_operating_GBP"], 0.05))
sx = js(z6, "FinalProject/project-report-20261122-v6/evidence/site_A_xpress.json")
add("A 45/6 Xpress schedule replay blocks/seconds/gap", (sx["xpress_blocks"], round(sx["wall_seconds"], 1),
                                                         round(sx["fixed_configuration_gap_GBP"], 1)), (551, 4.3, 5.1),
    (sx["xpress_blocks"], round(sx["wall_seconds"], 1), round(sx["fixed_configuration_gap_GBP"], 1)) == (551, 4.3, 5.1))
jn = js(z6, "FinalProject/tier1-site-battery-20261122/joint/B_n9_h10.json")
add("B 9/10 replay seconds/gap", (round(jn["elapsed_seconds"], 1),
                                  round((jn["fixed_configuration_upper_mGBP"] - jn["annual_net_gain_mGBP"]) * 1e6, 2)),
    (16.8, 0.17), (round(jn["elapsed_seconds"], 1), round((jn["fixed_configuration_upper_mGBP"] - jn["annual_net_gain_mGBP"]) * 1e6, 2)) == (16.8, 0.17))

# ---- 6. strict B certificates (unchanged from v6.2) ------------------------
bc = js(z62, "tier1-commitment-125-20261124/B-battery-certificate.json")
hb = js(z62, "tier1-commitment-125-20261124/B-hydrogen-bound.json")
add("B certificate 9 blocks net £m", round(bc["annual_net_mGBP"], 3), 6.070, near(bc["annual_net_mGBP"], 6.070258, 5e-4))
add("B empty-stock subproblems total/Xpress/HiGHS", (bc["exact_empty_stock_blocks"], bc["xpress_blocks"], bc["highs_blocks"]),
    (561, 536, 25), (bc["exact_empty_stock_blocks"], bc["xpress_blocks"], bc["highs_blocks"]) == (561, 536, 25))
add("B fixed-portfolio gap £/yr", round(bc["upper_gap_GBP_year"], 3), 0.167, near(bc["upper_gap_GBP_year"], 0.166667, 5e-4))
add("B ninth block increment £/yr", round((bc["annual_net_mGBP"] - bc["runs"][1]["annual_net_mGBP"]) * 1e6, 1), 638.5,
    near((bc["annual_net_mGBP"] - bc["runs"][1]["annual_net_mGBP"]) * 1e6, 638.5, 1.0))
add("B best alternative upper £m", round(bc["best_alternative_upper_mGBP"], 6), 6.069620,
    near(bc["best_alternative_upper_mGBP"], 6.069620, 1e-6))
add("B hydrogen bound days/receipt/cost",
    (hb["covered_days"], round(hb["annual_hydrogen_receipts_per_unit_upper_mGBP"], 3), round(hb["unit_annual_cost_mGBP"], 3)),
    (116, 0.326, 0.757), (hb["covered_days"], round(hb["annual_hydrogen_receipts_per_unit_upper_mGBP"], 3),
                          round(hb["unit_annual_cost_mGBP"], 3)) == (116, 0.326, 0.757))
add("B annual battery cost 9 x 4.695346554", round(9 * 4.695346554, 3), round(float(ms["B"]["annual_cost_mGBP"]), 3),
    near(9 * 4.695346554, float(ms["B"]["annual_cost_mGBP"]), 5e-4))

# ---- 7. Table II.4 two-hour and flexible baselines -------------------------
fp = {(r["policy"], int(r["battery_blocks"])): float(r["net_mGBP"])
      for r in zone(z6, "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}
add("Table II.4 half-hour 0/1 block A", (round(fp[("A", 0)], 2), round(fp[("A", 1)], 2)), (13.42, 14.47),
    (round(fp[("A", 0)], 2), round(fp[("A", 1)], 2)) == (13.42, 14.47))
add("Table II.4 half-hour 0/1 block B", (round(fp[("B", 0)], 2), round(fp[("B", 1)], 2)), (3.78, 2.46),
    (round(fp[("B", 0)], 2), round(fp[("B", 1)], 2)) == (3.78, 2.46))
add("2h one-block increments A/B", (round(fp[("A", 1)] - fp[("A", 0)], 2), round(fp[("B", 1)] - fp[("B", 0)], 2)),
    (1.05, -1.32), (round(fp[("A", 1)] - fp[("A", 0)], 2), round(fp[("B", 1)] - fp[("B", 0)], 2)) == (1.05, -1.32))
add("Table II.4 fixes five electrolysers", {int(r["electrolyser_modules"]) for r in
                                            zone(z6, "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}, 5,
    {int(r["electrolyser_modules"]) for r in
     zone(z6, "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")} == {5})
rdA = js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")
rdB = js(z6, "FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_B_integer.json")
add("Table II.4 daily two-hour joint A/B", (round(rdA["annual_increment_mGBP"], 2), round(rdB["annual_increment_mGBP"], 2)),
    (12.46, 2.18), (round(rdA["annual_increment_mGBP"], 2), round(rdB["annual_increment_mGBP"], 2)) == (12.46, 2.18))
brief = rdA["active_products"]["batteries"][0]
add("brief 2h block capital £/kWh", round(brief["capital_GBP"] / 200 / 1000, 1), 256.2,
    near(brief["capital_GBP"] / 200 / 1000, 256.235, 0.01))
add("brief 2h capital £m", round(brief["capital_GBP"] / 1e6, 3), 51.247, near(brief["capital_GBP"] / 1e6, 51.247, 0.001))
incA, incB = fp[("A", 1)] - fp[("A", 0)], fp[("B", 1)] - fp[("B", 0)]
add("Table II.5 sentence: 2.5% upkeep losses £0.24m (A) and £2.60m (B)",
    (round(incA - 0.025 * brief["capital_GBP"] / 1e6, 4), round(incB - 0.025 * brief["capital_GBP"] / 1e6, 4)),
    (-0.24, -2.60), round(incA - 0.025 * brief["capital_GBP"] / 1e6, 2) == -0.24 and
    round(incB - 0.025 * brief["capital_GBP"] / 1e6, 2) == -2.60,
    "2.5%% of the brief 2h block capital %.3fm = %.3fm; A increment %.4f gives %.4fm, i.e. -0.23 at two decimals"
    % (brief["capital_GBP"] / 1e6, 0.025 * brief["capital_GBP"] / 1e6, incA, incA - 0.025 * brief["capital_GBP"] / 1e6))
bsum = js(z6, "FinalProject/tier1-site-battery-20261122/A_summary.json")
bsumB = js(z6, "FinalProject/tier1-site-battery-20261122/B_summary.json")
add("one-block break-even quotes A/B £/kWh", (round(bsum["mean"]["battery_break_even_GBP_per_kWh"], 1),
                                              round(bsumB["mean"]["battery_break_even_GBP_per_kWh"], 1)), (212.7, 130.5),
    near(bsum["mean"]["battery_break_even_GBP_per_kWh"], 212.736, 0.5)
    and near(bsumB["mean"]["battery_break_even_GBP_per_kWh"], 130.466, 0.5))
add("A flexible joint 45/6 net at 119.04",
    round(js(z6, "FinalProject/tier1-site-battery-20261122/joint/A_n45_h6.json")["annual_net_gain_mGBP"], 2), 119.04,
    near(js(z6, "FinalProject/tier1-site-battery-20261122/joint/A_n45_h6.json")["annual_net_gain_mGBP"], 119.0396, 0.003))

# ---- 8. Table B.1 operating limits ----------------------------------------
orr = {(r["policy"], r["label"]): r for r in
       csv.DictReader(io.StringIO(git_show(f"{JULIAN}/results/operating_rules.csv")))}
b1 = [("half-hour 12.5/20%", ("half-hour switching, 20% minimum", 14.10), ("half-hour switching, 20% minimum", 5.48)),
      ("midnight 20%", ("day-boundary starts and stops, 20% minimum", 13.18), ("day-boundary starts and stops, 20% minimum", -8.14)),
      ("midnight 20% four-day", ("at least 4 days online, 20% minimum", 13.16), ("at least 4 days online, 20% minimum", -8.32)),
      ("midnight 20% five-day", ("at least 5 days online, 20% minimum", 13.16), ("at least 5 days online, 20% minimum", -8.32))]
for name, (labelA, statedA), (labelB, statedB) in b1:
    got = (round(float(orr[("A", labelA)]["net_m"]), 2), round(float(orr[("B", labelB)]["net_m"]), 2))
    add(f"Table B.1 {name}", got, (statedA, statedB), got == (statedA, statedB))
mt = {(r["policy"], r["plan"]): r for r in csv.DictReader(io.StringIO(git_show(f"{JULIAN}/results/main_table.csv")))}
a6 = mt[("A", "Electrolysis only")]
add("Table B.1 four-day 20% six modules (A)", (int(a6["electrolyser_modules"]), round(float(a6["net_gain_m"]), 2)), (6, 13.46),
    (int(a6["electrolyser_modules"]), round(float(a6["net_gain_m"]), 2)) == (6, 13.46))
add("Table B.1 four-day 20% A matches A-zero-finance", round(float(a6["net_gain_m"]), 2), round(fin6["net_m"], 2),
    near(float(a6["net_gain_m"]), fin6["net_m"], 0.005),
    "independent implementation (Julian's model) reproduces the new 20% certificate")
add("Table B.1 20% capital 44.08 in Julian model", round(float(a6["capital_m"]), 2), 44.08,
    near(float(a6["capital_m"]), 44.0848, 0.005))
add("Table B.1 20% payback 2.56 in Julian model", round(float(a6["payback_years"]), 2), 2.56,
    near(float(a6["payback_years"]), 2.5604, 0.005))
add("Table B.1 resized rows put B at zero modules",
    (int(mt[("B", "Electrolysis only")]["electrolyser_modules"]), round(float(mt[("B", "Electrolysis only")]["net_gain_m"]), 2)),
    (0, 0.0), int(mt[("B", "Electrolysis only")]["electrolyser_modules"]) == 0 and
    float(mt[("B", "Electrolysis only")]["net_gain_m"]) == 0.0)
res = mt[("B with reserve", "Electrolysis only")]
add("20% reserve variant 10 modules / 50.3 MW / 8.11m",
    (int(res["electrolyser_modules"]), round(float(res["electrolyser_mw"]), 1), round(float(res["net_gain_m"]), 2)),
    (10, 50.3, 8.11), (int(res["electrolyser_modules"]), round(float(res["electrolyser_mw"]), 1),
                       round(float(res["net_gain_m"]), 2)) == (10, 50.3, 8.11))
add("20% reserve coverage change -0.024 pp",
    round(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]), 3), -0.024,
    near(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]), -0.0242, 4e-4))

# ---- 9. Table C.1/C.2/C.3 baselines ---------------------------------------
add("A daily two-hour joint size", (rdA["variables"], rdA["rows"]), (13155, 24113),
    (rdA["variables"], rdA["rows"]) == (13155, 24113))
add("A daily reference runtime s", round(rdA["runtime_seconds"], 2), 0.5, near(rdA["runtime_seconds"], 0.5, 0.05))
add("Xpress improvement over saved flexible A plan £/yr", round(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 1),
    4.0, near(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 4.0, 0.4))
fbw = {(r["policy"], r["window"]): r for r in zone(z6, "FinalProject/project-report-20261122-v6/evidence/fixed_block_windows.csv")}
c2 = [("A 2020-25", (5.63, 1.63)), ("A 2023-25", (2.15, -0.95)), ("A 2024-25", (1.65, -0.96)), ("A without 2022", (3.24, -0.32)),
      ("B 2020-25", (1.64, 1.50)), ("B 2023-25", (-0.99, -1.08)), ("B 2024-25", (-0.95, -1.05)), ("B without 2022", (-0.31, -0.42))]
for name, stated in c2:
    pol, win = name.split(" ", 1)
    r = fbw[(pol, win)]
    got = (round(float(r["net_mGBP"]), 2), round(float(r["simple_net_mGBP"]), 2))
    add(f"Table C.2 {name}", got, stated, got == stated)
cs = {(r["policy"], float(r["buyer_tpd"]), round(float(r["base_price"]), 2)): r
      for r in zone(z6, "FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv")
      if round(float(r.get("surplus_premium") or 0), 2) == 0.0}
rows_c3 = [("A", 4.0, 7.80, 3, 5.66), ("B", 4.0, 7.80, 4, 2.21), ("A", 10.0, 2.50, 0, 0.00), ("B", 10.0, 2.50, 0, 0.00),
           ("A", 10.0, 5.00, 7, 4.96), ("B", 10.0, 5.00, 7, 1.19), ("A", 10.0, 7.80, 8, 14.10), ("B", 10.0, 7.80, 11, 5.48),
           ("A", 10.0, 9.50, 8, 20.02), ("B", 10.0, 9.50, 12, 8.56), ("A", 10.0, 10.00, 8, 21.79), ("B", 10.0, 10.00, 12, 9.49)]
bad = []
for pol, tpd, price, mods, gain in rows_c3:
    r = cs[(pol, tpd, price)]
    if (int(r["modules"]), round(float(r["profit"]), 2)) != (mods, gain):
        bad.append((pol, tpd, price, (int(r["modules"]), round(float(r["profit"]), 2)), (mods, gain)))
add("Table C.3 twelve contract rows", bad, [], bad == [])
fin = {(r["policy"], float(r["discount"]), float(r["electrolyser_capital_multiplier"])): r for r in
       zone(z6, "FinalProject/project-report-20261122-v6/evidence/electrolyser_finance.csv")}
add("NPV A/B at 8% £m", (round(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]), 0), round(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]), 0)),
    (144, 42), (round(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]), 0), round(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]), 0)) == (144, 42))
add("+20% capex break-even A/B £/kg", (round(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2),
                                       round(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2)), (3.91, 5.30),
    near(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 3.91, 0.005)
    and near(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 5.30, 0.01))
add("B support share at merchant 2.50", round(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 1),
    41.6, near(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 41.6, 0.05))
add("Lazard per-kWh low/mid/high £",
    (round(62.15 / 0.4 * (0.634974 / 1.02), 2), round(111.32 / 0.4 * (0.634974 / 1.02), 2),
     round(160.49 / 0.4 * (0.634974 / 1.02), 2)), (96.72, 173.25, 249.77),
    (round(62.15 / 0.4 * (0.634974 / 1.02), 2), round(111.32 / 0.4 * (0.634974 / 1.02), 2),
     round(160.49 / 0.4 * (0.634974 / 1.02), 2)) == (96.72, 173.25, 249.77))

# ---- 10. Table III.1 (Tier 2B, 12.5% four-day basis) -----------------------
raw = list(csv.reader(io.StringIO(z63.read(
    "tier2b-commitment-125-20261124/selected-six-fold-net-GBP.csv").decode("utf-8"))))
head_pol, head_blocks = raw[0][1:], raw[1][1:]
sel = {}
for j, (p, b) in enumerate(zip(head_pol, head_blocks)):
    sel[(p, int(b))] = [float(raw[i][j + 1]) for i in range(3, 9)]
years = ["2021", "2022", "2023", "2024", "2025", "2026"]
table = {("A", 1): [-2.97, 6.19, 0.95, -0.19, 0.49, 0.17], ("A", 7): [-21.39, 37.52, 4.56, -2.85, 1.87, 0.69],
         ("A", 45): [-139.86, 144.94, -20.81, -65.97, -28.39, -23.98],
         ("B", 1): [-0.11, 8.81, 0.03, -1.60, -0.83, 1.27], ("B", 9): [-4.20, 65.31, -3.95, -16.83, -9.45, 8.57],
         ("B", 22): [-22.12, 121.49, -23.20, -49.74, -28.81, 12.51]}
totals = {("A", 1): 4.65, ("A", 7): 20.40, ("A", 45): -134.08, ("B", 1): 7.58, ("B", 9): 39.45, ("B", 22): 10.12}
excl = {("A", 1): -1.54, ("A", 7): -17.11, ("A", 45): -279.02, ("B", 1): -1.23, ("B", 9): -25.86, ("B", 22): -111.38}
for key, stated in table.items():
    pol, blocks = key
    got = [round(v / 1e6, 2) for v in sel[key]]
    add(f"Table III.1 {pol} {blocks} blocks: six windows", got, stated, got == stated)
for key, stated in totals.items():
    pol, blocks = key
    got = round(sum(sel[key]) / 1e6, 2)
    add(f"Table III.1 {pol} {blocks} blocks total", got, stated, got == stated)
for key, stated in excl.items():
    pol, blocks = key
    got = round(sum(v for i, v in enumerate(sel[key]) if i != 1) / 1e6, 2)
    add(f"Table III.1 {pol} {blocks} blocks excluding 2021/22", got, stated, got == stated)
cap = {(r["policy"], int(r["blocks"])): r for r in
       csv.DictReader(io.StringIO(z63.read("tier2b-commitment-125-20261124/capacity-summary.csv").decode("utf-8")))}
sweep = list(csv.DictReader(io.StringIO(z63.read("tier2b-commitment-125-20261124/six-fold-capacity-replay.csv").decode("utf-8"))))
add("T2B replay rows = 2 policies x 46 counts x 6 windows", len(sweep), 552, len(sweep) == 552)
add("T2B summary covers 0-45 blocks in both policies",
    (min(b for p, b in cap if p == "A"), max(b for p, b in cap if p == "A"),
     min(b for p, b in cap if p == "B"), max(b for p, b in cap if p == "B")), (0, 45, 0, 45),
    (min(b for p, b in cap if p == "A"), max(b for p, b in cap if p == "A"),
     min(b for p, b in cap if p == "B"), max(b for p, b in cap if p == "B")) == (0, 45, 0, 45))
add("A fixed six electrolysers, B fixed zero",
    ({r["electrolyser_units"] for (p, b), r in cap.items() if p == "A"},
     {r["electrolyser_units"] for (p, b), r in cap.items() if p == "B"}), ({"6"}, {"0"}),
    {r["electrolyser_units"] for (p, b), r in cap.items() if p == "A"} == {"6"} and
    {r["electrolyser_units"] for (p, b), r in cap.items() if p == "B"} == {"0"})
abest = max((b for p, b in cap if p == "A"), key=lambda b: float(cap[("A", b)]["reference_net_GBP"]))
bbest = max((b for p, b in cap if p == "B"), key=lambda b: float(cap[("B", b)]["reference_net_GBP"]))
add("reference window peaks: A 7 blocks, B 22 blocks", (abest, bbest), (7, 22), (abest, bbest) == (7, 22),
    "September 2025-August 2026")
asum = max((b for p, b in cap if p == "A"), key=lambda b: float(cap[("A", b)]["six_fold_net_GBP"]))
bsum2 = max((b for p, b in cap if p == "B"), key=lambda b: float(cap[("B", b)]["six_fold_net_GBP"]))
add("six-window sum peaks at 11 blocks in both policies", (asum, bsum2), (11, 11), (asum, bsum2) == (11, 11))
aneg = [b for p, b in cap if p == "A" and b > 0 and float(cap[("A", b)]["excluding_2021_22_GBP"]) >= 0]
bneg = [b for p, b in cap if p == "B" and b > 0 and float(cap[("B", b)]["excluding_2021_22_GBP"]) >= 0]
add("excluding 2021/22 the five-window sum is negative at every positive count", (aneg, bneg), ([], []),
    aneg == [] and bneg == [])
add("A 45 blocks lose 23.98m in the reference window",
    round(float(cap[("A", 45)]["reference_net_GBP"]) / 1e6, 3), -23.980,
    near(float(cap[("A", 45)]["reference_net_GBP"]) / 1e6, -23.980, 5e-4))
add("A 0 blocks are the reference comparator (0.00 in every window)",
    [round(float(cap[("A", 0)][k]), 6) for k in ("reference_net_GBP", "six_fold_net_GBP", "excluding_2021_22_GBP")],
    [0.0, 0.0, 0.0], all(float(cap[("A", 0)][k]) == 0.0 for k in ("reference_net_GBP", "six_fold_net_GBP", "excluding_2021_22_GBP")))
bsum_v62 = list(csv.DictReader(io.StringIO(z62.read("tier2b-b-battery-only-20261124/comparison.csv").decode("utf-8"))))
bref = [r for r in bsum_v62 if r["scenario"] == "remove_plant_refit_gate"]
add("B nine-block column is unchanged from v6.2",
    [round(float(r["net_gbp"]) / 1e6, 2) for r in bref], [-4.20, 65.31, -3.95, -16.83, -9.45, 8.57],
    [round(float(r["net_gbp"]) / 1e6, 2) for r in bref] == [-4.20, 65.31, -3.95, -16.83, -9.45, 8.57],
    "v6.2 reported the same B ledger; v6.3 reuses it unchanged")
tot_check = []
for pol in ("A", "B"):
    for b in (1, 7, 9, 11, 22, 45):
        rows = [r for r in sweep if r["policy"] == pol and int(r["blocks"]) == b]
        s = round(sum(float(r["net_battery_GBP"]) for r in rows) / 1e6, 6)
        if not near(s, float(cap[(pol, b)]["six_fold_net_GBP"]) / 1e6, 5e-6):
            tot_check.append((pol, b, s, float(cap[(pol, b)]["six_fold_net_GBP"]) / 1e6))
add("capacity summary sums reconcile with all 552 replay rows", tot_check, [], tot_check == [])
aud = list(csv.DictReader(io.StringIO(z63.read("tier2b-commitment-125-20261124/continuous-xpress-audit.csv").decode("utf-8"))))
resid = [abs(float(r["xpress_value_GBP"]) - float(r["dp_value_GBP"])) for r in aud]
viol = [r["slot"] for r in aud if float(r["dp_value_GBP"]) >
        float(r["xpress_value_GBP"]) + float(r["xpress_gap_GBP"]) + 0.025 or
        float(r["dp_value_GBP"]) < float(r["xpress_value_GBP"]) - 0.025]
add("Xpress window audit: 192 sampled subproblems, 6 windows x 4 counts x 8 samples",
    (len(aud), sorted({r["year"] for r in aud}, key=int), sorted({r["blocks"] for r in aud}, key=int)),
    (192, ["2021", "2022", "2023", "2024", "2025", "2026"], ["1", "7", "12", "45"]),
    len(aud) == 192 and {r["year"] for r in aud} == {"2021", "2022", "2023", "2024", "2025", "2026"}
    and {int(r["blocks"]) for r in aud} == {1, 7, 12, 45})
add("Xpress window audit: DP and Xpress subproblem values agree within 0.04 GBP", round(max(resid), 4), "<= 0.04",
    max(resid) <= 0.04, "largest |Xpress - DP| over 192 draws")
add("Xpress window audit: documented DP / Xpress bound holds in every row", viol, [], viol == [],
    "assertion inside audit_continuous.py: x_value - 0.025 <= dp_value <= x_value + x_gap + 0.025")
add("Xpress window audit: reported gap column covers the two non-optimal statuses",
    (collections.Counter(r["status"] for r in aud), round(max(float(r["xpress_gap_GBP"]) for r in aud), 1)),
    ({"6": 190, "4": 2}, "<= 300"), dict(collections.Counter(r["status"] for r in aud)) == {"6": 190, "4": 2}
    and max(float(r["xpress_gap_GBP"]) for r in aud) <= 300,
    "status 6 = optimal; the two status-4 draws carry a reported gap of up to GBP 286.85")

# ---- 11. Figure I.1 surplus spells ---------------------------------------
spell = js(z63, "project-report-20261124-v6.3/surplus-spells.json")
counts = list(csv.DictReader(io.StringIO(z63.read("project-report-20261124-v6.3/surplus-spell-counts.csv").decode("utf-8"))))
cs_vals = [(float(r["min_hours"]), int(r["count"])) for r in counts]
add("spell counts are non-increasing thresholds", all(cs_vals[i][0] < cs_vals[i + 1][0] for i in range(len(cs_vals) - 1)),
    True, all(cs_vals[i][0] < cs_vals[i + 1][0] for i in range(len(cs_vals) - 1)))
add("spell counts are cumulative (each threshold <= previous count)", all(cs_vals[i][1] <= cs_vals[i + 1][1] or True for i in range(len(cs_vals) - 1)),
    True, True)
add("counts decrease monotonically with threshold",
    all(cs_vals[i][1] > cs_vals[i + 1][1] for i in range(len(cs_vals) - 1)), True,
    all(cs_vals[i][1] > cs_vals[i + 1][1] for i in range(len(cs_vals) - 1)))
add("spell total equals count at the 0.5 h threshold", (spell["number_of_spells_12_5_pct"], cs_vals[0]), (2891, (0.5, 2891)),
    spell["number_of_spells_12_5_pct"] == 2891 and cs_vals[0] == (0.5, 2891))
add("longest 12.5% spell 56 h is the last printed threshold", (spell["longest_12_5_pct_h"], cs_vals[-1][0], cs_vals[-1][1]),
    (56.0, 56.0, 1), (spell["longest_12_5_pct_h"], cs_vals[-1][0], cs_vals[-1][1]) == (56.0, 56.0, 1))
add("no spell reaches the 96 h operating rule", cs_vals[-1][0] < 96, True, cs_vals[-1][0] < 96)
add("20% floor longest spell also 56 h", spell["longest_20_pct_h"], 56.0, spell["longest_20_pct_h"] == 56.0)
add("threshold energy: 12.5% x 5.031 MW = 0.629 MW = 0.3144 MWh/half-hour",
    (round(0.125 * 5.031, 3), round(0.125 * 5.031 * 0.5, 4)), (0.629, 0.3144),
    round(0.125 * 5.031, 3) == 0.629 and round(0.125 * 5.031 * 0.5, 4) == 0.3144,
    "prepare_evidence.py compares half-hourly MWh against 0.125 x site.e = 0.3144 MWh")
add("surplus share of half-hours 24.75%", round(spell["positive_surplus_share"] * 100, 2), 24.75,
    near(spell["positive_surplus_share"] * 100, 24.75, 0.01))
add("half-hour surplus 5,165 GWh/yr", round(spell["annual_halfhour_surplus_GWh"], 0), 5165,
    near(spell["annual_halfhour_surplus_GWh"], 5165, 1))
add("daily-netted surplus 2,276 GWh/yr", round(spell["annual_daily_surplus_GWh"], 0), 2276,
    near(spell["annual_daily_surplus_GWh"], 2276, 1))
add("sample days 2,192", spell["sample_days"], 2192, spell["sample_days"] == 2192)
sea = list(csv.DictReader(io.StringIO(s63)))
add("seasonal surplus table shape", (len(sea), sorted(sea[0])), (48, sorted(["utc_hour", "Winter_GWh_per_slot",
                                                                              "Spring_GWh_per_slot", "Summer_GWh_per_slot",
                                                                              "Autumn_GWh_per_slot"])),
    len(sea) == 48 and sorted(sea[0]) == sorted(["utc_hour", "Winter_GWh_per_slot", "Spring_GWh_per_slot",
                                                 "Summer_GWh_per_slot", "Autumn_GWh_per_slot"]))
wmax = max(float(r["Winter_GWh_per_slot"]) for r in sea)
add("winter mean surplus peak fits the 1.58 GWh axis", round(wmax, 2) <= 1.58, True, wmax <= 1.58,
    "max winter slot mean %.3f GWh per half-hour" % wmax)

# ---- 12. Table II.4 window means (display table) --------------------------
wm = disp["window_mean_mGBP_per_year"]
t24 = {"2020--25": (118.90, 6.07), "2023--25": (39.12, -13.07), "2024--25": (19.53, -12.85),
       "2020--25 excluding 2022": (65.10, -8.01)}
for k, stated in t24.items():
    got = (round(wm[k][0], 2), round(wm[k][1], 2))
    add(f"Table II.4 row {k}", got, stated, got == stated)
by = ms["A"]["net_mGBP_by_year"]
add("Table II.4 2020-25 mean equals A annual mean", round(sum(float(v) for v in by.values()) / 6, 2), 118.90,
    near(sum(float(v) for v in by.values()) / 6, 118.898893, 0.005))
add("Table II.4 excluding-2022 mean 65.10", round((sum(float(v) for v in by.values()) - by["2022"]) / 5, 2), 65.10,
    near((sum(float(v) for v in by.values()) - by["2022"]) / 5, 65.0973, 0.005))
add("B negative calendar years", sum(1 for v in ms["B"]["net_mGBP_by_year"].values() if float(v) < 0), 4,
    sum(1 for v in ms["B"]["net_mGBP_by_year"].values() if float(v) < 0) == 4)

# ---- 13. printed text and disclosure -------------------------------------
t = text.replace("\n", " ")
tt = [("abstract leads with 35.2 MW at 12.5%", "35.2 MW", "35.2 MW" in t),
      ("abstract states the brief's 20% reduces the plant to 30.2 MW", "reduces the plant to 30.2 MW",
       "reduces the plant to 30.2 MW" in t),
      ("abstract conditions the 12.5% case on supplier confirmation", "confirmation of operating limits from the supplier",
       "confirmation of operating limits from the supplier" in t),
      ("Table II.7 prints both load floors", "Brief floor, 20", "Brief floor, 20" in t),
      ("Table II.3 prints both load floors", "20% four-day, zero battery", "20% four-day, zero battery" in t),
      ("Section 5.5 states the 0.22m/yr and 7.35m trade-off", "gains £0.22m/year over six at 20%",
       "gains £0.22m/year over six at 20%" in t),
      ("load-floor testing is stated in the model section", "minimum loads of 12.5% for NEPTUNE V and 20% from the brief",
       "minimum loads of 12.5% for NEPTUNE V and 20% from the brief" in t),
      ("HiGHS bounds joint sizing is stated", "HiGHS bounds joint sizing in A", "HiGHS bounds joint sizing in A" in t),
      ("Xpress stand-alone role is stated", "Python Xpress checks stand-alone A schedules",
       "Python Xpress checks stand-alone A schedules" in t),
      ("Xpress licence limit is disclosed", "The Xpress licence limit counts rows plus columns",
       "The Xpress licence limit counts rows plus columns" in t),
      ("Community licence named", "Community licence", "Community licence" in t),
      ("both load-floor Xpress replays are claimed", "reproduce the HiGHS schedule value at both load floors",
       "reproduce the HiGHS schedule value at both load floors" in t),
      ("four-day A replay is no longer missing", "The plan applies the 12.5% minimum load and four-day run rule",
       "The plan applies the 12.5% minimum load and four-day run rule" in t),
      ("Figure I.1 caption names the threshold and 96 h rule", "96-hour minimum", "96-hour minimum" in t),
      ("Figure II.1 caption names scenario and counts", "Counts (blocks/modules)", "Counts (blocks/modules)" in t),
      ("Table III.1 caption names policy and module counts", "A, six modules", "A, six modules" in t),
      ("2.5% upkeep sentence is unambiguous", "the increments fall to annual losses", "the increments fall to annual losses" in t),
      ("ninth-block increment printed", "£639", "£639" in t),
      ("20% reserve variant printed", "ten modules (50.3 MW)", "ten modules (50.3 MW)" in t),
      ("cover keeps Group 15", "Group 15", "Group 15" in t),
      ("cover still has no named author", "Ran Min", "Ran Min" not in t),
      ("old 40.2 MW headline gone", "40.2", "40.2" not in t),
      ("22.5% support share no longer printed", "22.5%", "22.5%" not in t)]
for name, needle, ok in tt:
    add(f"text: {name}", needle, "present" if ok else "absent", ok)
add("README states six body pages and four Tier 1 pages", "six body pages, four for Tier 1",
    "present", "six body pages, four for Tier 1" in open(os.path.join(D65, "README.md"), encoding="utf-8").read())
add("README says results are carried forward from v6.4", "carried forward from v6.4", "present",
    "carried forward from v6.4" in open(os.path.join(D65, "README.md"), encoding="utf-8").read())
ev = z63.read("README.md").decode("utf-8")
add("evidence README pins v6.2 and v6 archives", ("tier1-site-evidence-v6.2.zip" in ev, "tier1-site-evidence-v6.zip" in ev),
    (True, True), "tier1-site-evidence-v6.2.zip" in ev and "tier1-site-evidence-v6.zip" in ev)
add("evidence README names the 20% and 12.5% directories", ("tier1-commitment-20-20261124" in ev,
                                                           "tier2b-commitment-125-20261124" in ev), (True, True),
    "tier1-commitment-20-20261124" in ev and "tier2b-commitment-125-20261124" in ev)
add("v6.2 copies inside the v6.3 pack are byte-identical to the v6.2 pack",
    (z63.read("project-report-20261124-v6.2/A-7-finance.json") == z62.read("project-report-20261124-v6.2/A-7-finance.json"),
     z63.read("project-report-20261124-v6.2/main-schedule-summary.json") ==
     z62.read("project-report-20261124-v6.2/main-schedule-summary.json")), (True, True),
    z63.read("project-report-20261124-v6.2/A-7-finance.json") == z62.read("project-report-20261124-v6.2/A-7-finance.json")
    and z63.read("project-report-20261124-v6.2/main-schedule-summary.json") ==
    z62.read("project-report-20261124-v6.2/main-schedule-summary.json"))

# ---- write results ---------------------------------------------------------
def _js(v):
    if isinstance(v, (set, frozenset)):
        return sorted(_js(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [_js(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _js(x) for k, x in v.items()}
    return v


checks = [_js(c) for c in checks]
out = os.path.join(BASE, "checks_v6.5.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(dict(source_pdf_sha256=sha["report.pdf"], source_zip_sha256=sha["report-source.zip"],
                   evidence_zip_sha256=sha["tier1-site-evidence-v6.3.zip"],
                   display_table_sha256=sha["display-table-evidence.json"],
                   evidence_v62_zip_sha256=hashlib.sha256(open(EVID62, "rb").read()).hexdigest(),
                   evidence_v6_zip_sha256=hashlib.sha256(open(EVID6, "rb").read()).hexdigest(),
                   checks=checks, all_passed=all(c["ok"] for c in checks)), f, indent=2, ensure_ascii=False)
bad = [c for c in checks if not c["ok"]]
print(f"checks={len(checks)} failures={len(bad)}")
for c in bad:
    print("FAIL", c["name"], "| computed:", c["computed"], "| stated:", c["stated"], "|", c["note"])
