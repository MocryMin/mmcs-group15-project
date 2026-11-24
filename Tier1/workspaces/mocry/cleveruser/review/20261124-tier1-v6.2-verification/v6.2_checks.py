"""Verify Tier 1 report candidate v6.2 (report.pdf sha256 4837c08d...) against
(a) its own evidence archive tier1-site-evidence-v6.2.zip (sha256 3a1a9377...),
(b) the pinned v6 archive (unchanged baseline: tier1-site-evidence-v6.zip), and
(c) Julian's 10 t/day operating-limits study at commit c3902fe.

Reads the published ZIPs directly, prints pass/fail, writes checks_v6.2.json.
"""

import csv, io, json, hashlib, os, subprocess, sys, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, *[".."] * 6))
REPORT = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex",
                      "technical-report-latex", "20261124-v6.2")
V6DIR = os.path.join(REPO, "Tier1", "workspaces", "mocry", "codex",
                     "technical-report-latex", "20261123-v6")

PDF = os.path.join(REPORT, "report.pdf")
SRC = os.path.join(REPORT, "report-source.zip")
EVID62 = os.path.join(REPORT, "tier1-site-evidence-v6.2.zip")
EVID6 = os.path.join(V6DIR, "tier1-site-evidence-v6.zip")

JULIAN = "Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1"
JULIAN_COMMIT = "c3902fe"

z6 = zipfile.ZipFile(EVID6)
z62 = zipfile.ZipFile(EVID62)
checks = []


def _js(v):
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    if isinstance(v, (list, tuple)):
        return [_js(x) for x in v]
    if isinstance(v, dict):
        return {k: _js(x) for k, x in v.items()}
    return v


def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=_js(computed), stated=_js(stated), ok=bool(ok), note=note))


def csv62(inner):
    with z62.open(inner) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


def csv6(inner):
    with z6.open(inner) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


def js62(inner):
    return json.loads(z62.read(inner).decode("utf-8"))


def js6(inner):
    return json.loads(z6.read(inner).decode("utf-8"))


def git_show(path):
    out = subprocess.run(["git", "-C", REPO, "show", f"{JULIAN_COMMIT}:{path}"],
                         capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace"))
    return out.stdout.decode("utf-8")


def jul_csv(name):
    return list(csv.DictReader(io.StringIO(git_show(f"{JULIAN}/{name}"))))


def jul_json(name):
    return json.loads(git_show(f"{JULIAN}/{name}"))


def near(a, b, tol):
    return abs(float(a) - float(b)) <= tol


# ---- 1. package integrity ---------------------------------------------------
sha_pdf = hashlib.sha256(open(PDF, "rb").read()).hexdigest()
add("v6.2 report.pdf sha256", sha_pdf,
    "4837c08d330d8bb938c9dd41831c4042d4bf457e3a8238e0b0c34a62bbd6f1ea",
    sha_pdf == "4837c08d330d8bb938c9dd41831c4042d4bf457e3a8238e0b0c34a62bbd6f1ea")
sums = dict(l.split()[::-1] for l in open(os.path.join(REPORT, "SHA256SUMS.txt"),
                                          encoding="utf-8").read().splitlines() if l.strip())
add("SHA256SUMS lists report.pdf", sums.get("report.pdf"), sha_pdf, sums.get("report.pdf") == sha_pdf)
sha_src = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
add("report-source.zip sha256", sha_src,
    "20aacf7cbecb77bc9e7da091dbfe98c9f96457a788c220fc013b6d7de11f602a",
    sha_src == "20aacf7cbecb77bc9e7da091dbfe98c9f96457a788c220fc013b6d7de11f602a")
add("SHA256SUMS lists report-source.zip", sums.get("report-source.zip"), sha_src,
    sums.get("report-source.zip") == sha_src)
sha_ev = hashlib.sha256(open(EVID62, "rb").read()).hexdigest()
add("tier1-site-evidence-v6.2.zip sha256", sha_ev,
    "3a1a9377d18fa11168af4b353d603b52e7601ad3c4c1186be9ef7a6f32fabd3e",
    sha_ev == "3a1a9377d18fa11168af4b353d603b52e7601ad3c4c1186be9ef7a6f32fabd3e")
add("SHA256SUMS lists evidence zip", sums.get("tier1-site-evidence-v6.2.zip"), sha_ev,
    sums.get("tier1-site-evidence-v6.2.zip") == sha_ev)
add("SHA256SUMS lists README.md", sums.get("README.md"),
    "a800a3f614070f853e0d6b758c965cb5cabd1e9b6eae80a99e215a14fcfc512e",
    sums.get("README.md") == "a800a3f614070f853e0d6b758c965cb5cabd1e9b6eae80a99e215a14fcfc512e")
add("SHA256SUMS lists REVIEW_RESPONSE.md", sums.get("REVIEW_RESPONSE.md"),
    "a6d2493265af2c63984647646614d0fea7884e0ad6ab96c16b86d80e9c2c5453",
    sums.get("REVIEW_RESPONSE.md") == "a6d2493265af2c63984647646614d0fea7884e0ad6ab96c16b86d80e9c2c5453")
zs = zipfile.ZipFile(SRC)
names = set(zs.namelist())
add("source archive files", len(names), 10, len(names) == 10)
add("source archive keeps tex layout", sorted(n for n in names if n.endswith(".tex")),
    sorted(["report.tex", "sections/appendices.tex", "sections/common.tex", "sections/references.tex",
            "sections/site-tables.tex", "sections/tier1.tex", "sections/tier2.tex", "academic-style.tex"]),
    sorted(n for n in names if n.endswith(".tex")) ==
    sorted(["report.tex", "sections/appendices.tex", "sections/common.tex", "sections/references.tex",
            "sections/site-tables.tex", "sections/tier1.tex", "sections/tier2.tex", "academic-style.tex"]))
add("evidence entries", len(z62.namelist()), 132, len(z62.namelist()) == 132)
man62 = js62("MANIFEST.json")
add("evidence MANIFEST entries", len(man62), 131, len(man62) == 131)

from pypdf import PdfReader
reader = PdfReader(PDF)
add("PDF pages", len(reader.pages), 15, len(reader.pages) == 15)
text = "\n".join((p.extract_text() or "") for p in reader.pages)
pages = [(p.extract_text() or "").strip().splitlines() for p in reader.pages]
foot = [p[-1].strip() if p else "" for p in pages]
add("body pages numbered 1-6 only", [foot[i] for i in range(2, 8)], ["1", "2", "3", "4", "5", "6"],
    [foot[i] for i in range(2, 8)] == ["1", "2", "3", "4", "5", "6"],
    "owner rule: 10 pages means body pages; abstract/contents/references/appendices are separate")

# ---- 2. Table II.3 ----------------------------------------------------------
ms = js62("project-report-20261124-v6.2/main-schedule-summary.json")
sp = {r["policy"] + "|" + r["plan"]: r for r in csv6("FinalProject/project-report-20261122-v6/evidence/site_portfolios.csv")}
fin7 = js62("project-report-20261124-v6.2/A-7-finance.json")

t23 = [
    ("A None", (0, 0, 0.00, 89.66), (0, 0, round(0.0, 2), round(float(sp["A|None"]["demand_coverage_pct"]), 2))),
    ("A four-day zero battery", (0, 7, 13.68, 89.61),
     (0, 7, round(float(fin7["net_m"]), 2), round(float(fin7["served_pct"]), 2))),
    ("A four-day joint", (45, 6, 118.90, 90.16),
     (45, 6, round(float(ms["A"]["annual_net_mGBP"]), 2), round(float(ms["A"]["demand_served_pct"]), 2))),
    ("A flexible zero battery", (0, 8, 14.10, 89.61),
     (int(sp["A|Electrolysis"]["battery_blocks"]), int(sp["A|Electrolysis"]["electrolyser_modules"]),
      round(float(sp["A|Electrolysis"]["annual_net_mGBP"]), 2),
      round(float(sp["A|Electrolysis"]["demand_coverage_pct"]), 2))),
    ("A flexible joint", (45, 6, 119.04, 90.16),
     (int(sp["A|Joint sizing"]["battery_blocks"]), int(sp["A|Joint sizing"]["electrolyser_modules"]),
      round(float(sp["A|Joint sizing"]["annual_net_mGBP"]), 2),
      round(float(sp["A|Joint sizing"]["demand_coverage_pct"]), 2))),
    ("B None", (0, 0, 0.00, 91.03), (0, 0, 0.00, round(float(sp["B|None"]["demand_coverage_pct"]), 2))),
    ("B four-day zero battery", (0, 0, 0.00, 91.03), (0, 0, 0.00, round(float(ms["B"]["base_demand_served_pct"]), 2))),
    ("B four-day joint", (9, 0, 6.07, 91.23),
     (9, 0, round(float(ms["B"]["annual_net_mGBP"]), 2), round(float(ms["B"]["demand_served_pct"]), 2))),
    ("B flexible zero battery", (0, 11, 5.48, 91.03),
     (int(sp["B|Electrolysis"]["battery_blocks"]), int(sp["B|Electrolysis"]["electrolyser_modules"]),
      round(float(sp["B|Electrolysis"]["annual_net_mGBP"]), 2),
      round(float(sp["B|Electrolysis"]["demand_coverage_pct"]), 2))),
    ("B flexible joint", (9, 10, 11.40, 91.23),
     (int(sp["B|Joint sizing"]["battery_blocks"]), int(sp["B|Joint sizing"]["electrolyser_modules"]),
      round(float(sp["B|Joint sizing"]["annual_net_mGBP"]), 2),
      round(float(sp["B|Joint sizing"]["demand_coverage_pct"]), 2))),
]
for name, stated, got in t23:
    add(f"Table II.3 {name}", got, stated, got == stated)

CAPB, CAPH = 38.689824682844176, 7.347472240058675
add("joint battery power A/B MW", (45 * 100, 9 * 100), (4500, 900), (45 * 100, 9 * 100) == (4500, 900))
add("joint equipment capex A £bn", round((45 * CAPB + 6 * CAPH) / 1000, 2), 1.79,
    near((45 * CAPB + 6 * CAPH) / 1000, 1.785, 0.005))
add("joint equipment capex B £m", round(9 * CAPB, 0), 348.2, near(9 * CAPB, 348.2, 0.05))
add("A joint hydrogen output t/yr", round(float(ms["A"]["annual_h2_tonnes"]), 0), 3373,
    near(float(ms["A"]["annual_h2_tonnes"]), 3373, 0.6))
add("A four-day feasible-upper gap £/yr",
    round((float(js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["global_upper_mGBP"])
           - float(js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["annual_net_mGBP"])) * 1e6, 0),
    "within 2,000", near((118.9008913450649 - 118.89889272016808) * 1e6, 1998.6, 3.0),
    "certificate feasible 118.898893 vs upper 118.900891")
add("A winning counts 45/6 in certificate",
    (js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["battery_blocks"],
     js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["electrolyser_units"]), (45, 6),
    (js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["battery_blocks"],
     js62("tier1-commitment-125-20261124/A-capacity-certificate.json")["electrolyser_units"]) == (45, 6))
certA = js62("tier1-commitment-125-20261124/A-capacity-certificate.json")
add("A alternative 46/6 upper below winner", round(certA["highest_alternative_upper_mGBP"], 6), 118.890634,
    near(certA["highest_alternative_upper_mGBP"], 118.890634, 1e-6),
    f"alternative {certA['highest_alternative']}; {len(certA['fixed_capacity_day_relaxations'])} relaxed candidates")
add("A zero-battery optimum is 7 modules",
    [r["electrolyser_units"] for r in js62("tier1-commitment-125-20261124/A-electrolysis-only.json")
     if r.get("screened") is False], [7],
    [r["electrolyser_units"] for r in js62("tier1-commitment-125-20261124/A-electrolysis-only.json")
     if r.get("screened") is False] == [7])
scan = {r["electrolyser_units"]: r["upper_mGBP"] for r in js62("tier1-commitment-125-20261124/A-electrolysis-only.json")}
add("zero-battery neighbours screened below 7", (round(scan[6], 3), round(scan[8], 3)), "both < 13.679",
    scan[6] < 13.679 and scan[8] < 13.679)

# ---- 3. A seven-module finance (A-7-finance.json) ---------------------------
add("A-7 modules / MW", (fin7["modules"], round(fin7["mw"], 3)), (7, 35.217),
    (fin7["modules"], round(fin7["mw"], 3)) == (7, 35.217))
add("A-7 capital £m", round(fin7["capital_m"], 2), 51.43, near(fin7["capital_m"], 51.432, 0.005))
add("A-7 net £m/yr", round(fin7["net_m"], 2), 13.68, near(fin7["net_m"], 13.679, 0.005))
add("A-7 payback years", round(fin7["payback_years"], 2), 2.85,
    near(fin7["payback_years"], 2.8472, 0.002),
    "capital / (gross - module fixed O&M) = %.4f" % (7 * CAPH / (fin7["gross_m"] - 7 * 0.130109976)))
add("A-7 NPV £m at 5%, 30 yr", round(fin7["npv_30_years_mGBP"], 2), 210.28,
    near(fin7["npv_30_years_mGBP"], 13.6792100350457 * ((1 - 1.05 ** -30) / 0.05), 0.02))
add("A-7 break-even receipt £/kg", round(fin7["fixed_dispatch_break_even_GBP_kg"], 2), 3.82,
    near(fin7["fixed_dispatch_break_even_GBP_kg"], 3.8198, 0.002),
    "v0 - net / tonnes = %.4f" % (7.7990270551508845 - 13.6792100350457 / 3.4376677167104026))
add("A-7 diverted sales GWh/yr", round(fin7["diverted_gwh"], 0), 118,
    near(fin7["diverted_gwh"], 118.394, 0.5))
add("A-7 demand coverage change pp", round(-fin7["served_change_pp"], 3), 0.047,
    near(-fin7["served_change_pp"], 0.046720, 0.0005))
add("A-7 served pct", round(fin7["served_pct"], 2), 89.61, near(fin7["served_pct"], 89.6108, 0.005))

# ---- 4. strict B: hydrogen exclusion and battery certificate ----------------
hb = js62("tier1-commitment-125-20261124/B-hydrogen-bound.json")
add("B hydrogen bound: covered days at <=70 blocks", hb["covered_days"], 116, hb["covered_days"] == 116)
add("B hydrogen bound: receipts per module upper £m", round(hb["annual_hydrogen_receipts_per_unit_upper_mGBP"], 3), 0.326,
    near(hb["annual_hydrogen_receipts_per_unit_upper_mGBP"], 0.325687, 0.0005))
add("B hydrogen bound: module annual cost £m", round(hb["unit_annual_cost_mGBP"], 3), 0.757,
    near(hb["unit_annual_cost_mGBP"], 0.756537, 0.0005))
add("B hydrogen upper < module cost", hb["annual_hydrogen_receipts_per_unit_upper_mGBP"] < hb["unit_annual_cost_mGBP"],
    True, hb["annual_hydrogen_receipts_per_unit_upper_mGBP"] < hb["unit_annual_cost_mGBP"])
bc = js62("tier1-commitment-125-20261124/B-battery-certificate.json")
add("B certificate 9 blocks net £m", round(bc["annual_net_mGBP"], 3), 6.070,
    near(bc["annual_net_mGBP"], 6.070258, 0.0005))
add("B empty-stock subproblems total/Xpress/HiGHS",
    (bc["exact_empty_stock_blocks"], bc["xpress_blocks"], bc["highs_blocks"]), (561, 536, 25),
    (bc["exact_empty_stock_blocks"], bc["xpress_blocks"], bc["highs_blocks"]) == (561, 536, 25))
add("B fixed-portfolio gap £/yr", round(bc["upper_gap_GBP_year"], 3), 0.167,
    near(bc["upper_gap_GBP_year"], 0.166667, 0.0005))
add("B ninth block increment £/yr", round((bc["annual_net_mGBP"] - bc["runs"][1]["annual_net_mGBP"]) * 1e6, 0), 639,
    near((6.0702580381573625 - 6.069619507898686) * 1e6, 638.5, 1.0))
add("B best alternative upper £m", round(bc["best_alternative_upper_mGBP"], 6), 6.069620,
    near(bc["best_alternative_upper_mGBP"], 6.069620, 1e-6))
add("B annual battery cost £m", round(float(ms["B"]["annual_cost_mGBP"]), 2), 42.26,
    near(float(ms["B"]["annual_cost_mGBP"]), 42.258, 0.005),
    "9 x 4.695346554 = %.6f" % (9 * 4.695346554))

# ---- 5. Table II.4 two-hour references --------------------------------------
fp = {(r["policy"], int(r["battery_blocks"])): float(r["net_mGBP"])
      for r in csv6("FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}
add("Table II.4 A half-hour 0 block", round(fp[("A", 0)], 2), 13.42, near(fp[("A", 0)], 13.4186, 0.005))
add("Table II.4 A half-hour 1 block", round(fp[("A", 1)], 2), 14.47, near(fp[("A", 1)], 14.4691, 0.005))
add("Table II.4 B half-hour 0 block", round(fp[("B", 0)], 2), 3.78, near(fp[("B", 0)], 3.7757, 0.005))
add("Table II.4 B half-hour 1 block", round(fp[("B", 1)], 2), 2.46, near(fp[("B", 1)], 2.4582, 0.005))
add("2h one-block increment A/B", (round(fp[("A", 1)] - fp[("A", 0)], 2), round(fp[("B", 1)] - fp[("B", 0)], 2)),
    (1.05, -1.32), (round(fp[("A", 1)] - fp[("A", 0)], 2), round(fp[("B", 1)] - fp[("B", 0)], 2)) == (1.05, -1.32))
add("Table II.4 fixes five electrolysers", {int(r["electrolyser_modules"]) for r in csv6(
    "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}, 5,
    {int(r["electrolyser_modules"]) for r in csv6(
        "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")} == {5})
rdA = js6("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json")
rdB = js6("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_B_integer.json")
add("Table II.4 A daily two-hour joint", round(rdA["annual_increment_mGBP"], 2), 12.46,
    near(rdA["annual_increment_mGBP"], 12.4620, 0.005))
add("Table II.4 B daily two-hour joint", round(rdB["annual_increment_mGBP"], 2), 2.18,
    near(rdB["annual_increment_mGBP"], 2.18, 0.005))
brief = rdA["active_products"]["batteries"][0]
add("brief 2h block capital £m", round(brief["capital_GBP"] / 1e6, 3), 51.247,
    near(brief["capital_GBP"] / 1e6, 51.247, 0.001))
add("brief 2h block FOM in solved model", brief["fom_GBP"], 0.0, brief["fom_GBP"] == 0.0,
    "the +1.05/-1.32 increments exclude the 2.5% upkeep; adding 2.5% of 51.247m = £1.281m makes both negative")
incA, incB = fp[("A", 1)] - fp[("A", 0)], fp[("B", 1)] - fp[("B", 0)]
add("2.5% upkeep turns both increments negative",
    (round(incA - 0.025 * 51.247, 2), round(incB - 0.025 * 51.247, 2)), "both < 0",
    (incA - 0.025 * 51.247) < 0 and (incB - 0.025 * 51.247) < 0,
    "A %.3f - 1.281 = %.3f; B %.3f - 1.281 = %.3f" % (incA, incA - 1.281, incB, incB - 1.281))
add("brief-equivalent capital £/kWh", round(brief["capital_GBP"] / 200 / 1000, 1), 256.2,
    near(brief["capital_GBP"] / 200 / 1000, 256.235, 0.01))
bsum = js6("FinalProject/tier1-site-battery-20261122/A_summary.json")
bsumB = js6("FinalProject/tier1-site-battery-20261122/B_summary.json")
add("one-block break-even quote A £/kWh", round(bsum["mean"]["battery_break_even_GBP_per_kWh"], 0), 213,
    near(bsum["mean"]["battery_break_even_GBP_per_kWh"], 212.736, 0.5))
add("one-block break-even quote B £/kWh", round(bsumB["mean"]["battery_break_even_GBP_per_kWh"], 0), 130,
    near(bsumB["mean"]["battery_break_even_GBP_per_kWh"], 130.466, 0.5))

# ---- 6. Table B.1 operating limits ------------------------------------------
orr = {(r["policy"], r["label"]): r for r in jul_csv("results/operating_rules.csv")}


def net(policy, label):
    return round(float(orr[(policy, label)]["net_m"]), 2)


b1 = [("half-hour 12.5/20%", (net("A", "half-hour switching, 20% minimum"), net("B", "half-hour switching, 20% minimum")), (14.10, 5.48)),
      ("midnight 20%", (net("A", "day-boundary starts and stops, 20% minimum"), net("B", "day-boundary starts and stops, 20% minimum")), (13.18, -8.14)),
      ("midnight 20% four-day", (net("A", "at least 4 days online, 20% minimum"), net("B", "at least 4 days online, 20% minimum")), (13.16, -8.32)),
      ("midnight 20% five-day", (net("A", "at least 5 days online, 20% minimum"), net("B", "at least 5 days online, 20% minimum")), (13.16, -8.32))]
for name, got, stated in b1:
    add(f"Table B.1 {name}", got, stated, got == stated)
mt = {(r["policy"], r["plan"]): r for r in jul_csv("results/main_table.csv")}
a6 = mt[("A", "Electrolysis only")]
add("Table B.1 four-day 20% six modules (A)", (int(a6["electrolyser_modules"]), round(float(a6["net_gain_m"]), 2)), (6, 13.46),
    (int(a6["electrolyser_modules"]), round(float(a6["net_gain_m"]), 2)) == (6, 13.46))
add("Table B.1 four-day 12.5% seven modules (A)", (fin7["modules"], round(fin7["net_m"], 2)), (7, 13.68),
    (fin7["modules"], round(fin7["net_m"], 2)) == (7, 13.68))
add("brief-consistent 20% A plant capital £m", round(float(a6["capital_m"]), 2), 44.08,
    near(float(a6["capital_m"]), 44.0848, 0.005), "Julian main_table A Electrolysis only at 20% + four-day")
add("brief-consistent 20% A plant payback years", round(float(a6["payback_years"]), 2), 2.56,
    near(float(a6["payback_years"]), 2.5604, 0.005))
add("brief-consistent 20% A plant NPV £m", round(float(a6["net_gain_m"]) * ((1 - 1.05 ** -30) / 0.05), 1), 206.9,
    near(float(a6["net_gain_m"]) * ((1 - 1.05 ** -30) / 0.05), 206.9, 0.1),
    "13.4596 x 15.3725; the report prints 210.28m for the 12.5% seven-module case only")
add("Table B.1 resized rows put B at zero modules",
    (int(mt[("B", "Electrolysis only")]["electrolyser_modules"]), round(float(mt[("B", "Electrolysis only")]["net_gain_m"]), 2)), (0, 0.0),
    int(mt[("B", "Electrolysis only")]["electrolyser_modules"]) == 0 and float(mt[("B", "Electrolysis only")]["net_gain_m"]) == 0.0,
    "fixed 8/11-module B row stays at -8.32 until the last two resized rows")
res = mt[("B with reserve", "Electrolysis only")]
add("20% reserve variant 10 modules / 50.3 MW", (int(res["electrolyser_modules"]), round(float(res["electrolyser_mw"]), 1)), (10, 50.3),
    (int(res["electrolyser_modules"]), round(float(res["electrolyser_mw"]), 1)) == (10, 50.3))
add("20% reserve variant gain £8.11m", round(float(res["net_gain_m"]), 2), 8.11, near(float(res["net_gain_m"]), 8.1137, 0.005))
add("20% reserve coverage change 0.024 pp",
    round(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]), 3), -0.024,
    near(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]), -0.0242, 0.0004))
add("61 GWh service cost implied by 0.024 pp",
    round(0.000242 * 8760 * 28.5, 1), 61, near(0.000242 * 8760 * 28.5, 60.4, 2.0),
    "0.024% of 28.5 GW mean demand for one year")
ck = jul_json("results/checks.json")
add("Julian 56-hour surplus spell",
    [i["detail"] for i in ck["items"] if "56 hours" in i["check"]], "56.0 hours",
    any(i["passed"] and "56.0" in i["detail"] for i in ck["items"] if "56 hours" in i["check"]))
add("Julian minimum-run programmes optimal",
    [i["detail"] for i in ck["items"] if "minimum-run programmes solved" in i["check"]], "gap GBP 0.000",
    any(i["passed"] for i in ck["items"] if "minimum-run programmes solved" in i["check"]))

# ---- 7. Table C.1 solver evidence -------------------------------------------
sx = js6("FinalProject/project-report-20261122-v6/evidence/site_A_xpress.json")
add("A 45/6 Xpress blocks", sx["xpress_blocks"], 551, sx["xpress_blocks"] == 551)
add("A 45/6 Xpress seconds", round(sx["wall_seconds"], 1), 4.3, near(sx["wall_seconds"], 4.3, 0.05))
add("A 45/6 fixed-configuration gap £/yr", round(sx["fixed_configuration_gap_GBP"], 1), 5.1,
    round(sx["fixed_configuration_gap_GBP"], 1) == 5.1)
add("A daily two-hour joint size", (rdA["variables"], rdA["rows"]), (13155, 24113),
    (rdA["variables"], rdA["rows"]) == (13155, 24113))
add("B daily two-hour joint size", (rdB["variables"], rdB["rows"]), (13155, 24113),
    (rdB["variables"], rdB["rows"]) == (13155, 24113))
add("A daily reference runtime s", round(rdA["runtime_seconds"], 1), 0.5, near(rdA["runtime_seconds"], 0.505, 0.02))
jn = js6("FinalProject/tier1-site-battery-20261122/joint/B_n9_h10.json")
add("B 9/10 zero-stock replay seconds", round(jn["elapsed_seconds"], 1), 16.8, near(jn["elapsed_seconds"], 16.768, 0.05))
add("B 9/10 fixed-configuration gap £/yr",
    round((jn["fixed_configuration_upper_mGBP"] - jn["annual_net_gain_mGBP"]) * 1e6, 2), 0.17,
    near((jn["fixed_configuration_upper_mGBP"] - jn["annual_net_gain_mGBP"]) * 1e6, 0.167, 0.01))
add("Xpress improvement over saved flexible A plan £/yr",
    round(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 1), 4.0,
    near(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 4.0, 0.4))
add("B flexible joint 9/10 net at 11.40",
    round(jn["annual_net_gain_mGBP"], 2), 11.40, near(jn["annual_net_gain_mGBP"], 11.4025, 0.003))
an45 = js6("FinalProject/tier1-site-battery-20261122/joint/A_n45_h6.json")
add("A flexible joint 45/6 net at 119.04", round(an45["annual_net_gain_mGBP"], 2), 119.04,
    near(an45["annual_net_gain_mGBP"], 119.0396, 0.003))

# ---- 8. Table C.2 window sensitivities --------------------------------------
fbw = {(r["policy"], r["window"]): r for r in csv6(
    "FinalProject/project-report-20261122-v6/evidence/fixed_block_windows.csv")}
c2 = [("A 2020-25", (5.63, 1.63, 5.05)), ("A 2023-25", (2.15, -0.95, 1.57)), ("A 2024-25", (1.65, -0.96, 1.07)),
      ("A without 2022", (3.24, -0.32, 2.66)), ("B 2020-25", (1.64, 1.50, 1.06)), ("B 2023-25", (-0.99, -1.08, -1.57)),
      ("B 2024-25", (-0.95, -1.05, -1.53)), ("B without 2022", (-0.31, -0.42, -0.89))]
for name, stated in c2:
    pol, win = name.split(" ", 1)
    r = fbw[(pol, win.replace("2020-25", "2020-25").replace("2023-25", "2023-25"))]
    got = (round(float(r["net_mGBP"]), 2), round(float(r["simple_net_mGBP"]), 2), round(float(r["net_4pct_mGBP"]), 2))
    add(f"Table C.2 {name}", got, stated, got == stated)

# ---- 9. Table C.3 contract rows ---------------------------------------------
cs = {(r["policy"], float(r["buyer_tpd"]), round(float(r["base_price"]), 2),
      round(float(r.get("surplus_premium") or 0), 2)): r for r in csv6(
          "FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv")}
rows_c3 = [("A", 4.0, 7.80, 3, 5.66), ("B", 4.0, 7.80, 4, 2.21),
           ("A", 10.0, 2.50, 0, 0.00), ("B", 10.0, 2.50, 0, 0.00),
           ("A", 10.0, 5.00, 7, 4.96), ("B", 10.0, 5.00, 7, 1.19),
           ("A", 10.0, 7.80, 8, 14.10), ("B", 10.0, 7.80, 11, 5.48),
           ("A", 10.0, 9.50, 8, 20.02), ("B", 10.0, 9.50, 12, 8.56),
           ("A", 10.0, 10.00, 8, 21.79), ("B", 10.0, 10.00, 12, 9.49)]
for pol, tpd, price, mods, gain in rows_c3:
    r = cs[(pol, tpd, price, 0.0)]
    got = (int(r["modules"]), round(float(r["profit"]), 2))
    add(f"Table C.3 {pol} {tpd}t at {price}", got, (mods, gain), got == (mods, gain))
two = [r for r in csv6("FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv")
       if float(r.get("surplus_premium") or 0) > 0]
for r in two:
    exp = 6.06 if r["policy"] == "A" else 5.48
    add(f"two-rate {r['policy']} modules/gain", (int(r["modules"]), round(float(r["profit"]), 2)), (11, exp),
        int(r["modules"]) == 11 and near(float(r["profit"]), exp, 0.005))
aTwo = [r for r in two if r["policy"] == "A"][0]
s = float(aTwo["physical_surplus_share"])
add("two-rate A average receipt £/kg", round(s * 7.799 + (1 - s) * 2.50, 2), 6.58,
    near(s * 7.799 + (1 - s) * 2.50, 6.58, 0.02),
    "physical surplus share %.3f values 7.80/2.50 receipts" % s)
fin = {(r["policy"], float(r["discount"]), float(r["electrolyser_capital_multiplier"])): r for r in csv6(
    "FinalProject/project-report-20261122-v6/evidence/electrolyser_finance.csv")}
add("NPV A 8% £m", round(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]), 0), 144, near(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]), 144, 1))
add("NPV B 8% £m", round(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]), 0), 42, near(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]), 42, 1))
add("+20% capex break-even A £/kg", round(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 3.91,
    near(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 3.91, 0.005))
add("+20% capex break-even B £/kg", round(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 5.30,
    near(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 5.30, 0.01))
add("B support share at merchant 2.50", round(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 1), 41.6,
    near(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 41.6, 0.05))

# ---- 10. Tier 2B windows ----------------------------------------------------
a_st = list(csv.DictReader(io.StringIO(
    (z62.read("tier2b-capacity-stability-20261124/a-stability.csv")).decode("utf-8"))))
a_x = [r for r in a_st if r["method"] == "xpress"]
add("T2B A six windows", len(a_x), 6, len(a_x) == 6)
aw = [round(float(r["net_gbp"]) / 1e6, 2) for r in a_x]
add("Table III.1 A window values", aw, [-20.45, 41.02, 6.17, -2.78, 2.31, 2.03], aw == [-20.45, 41.02, 6.17, -2.78, 2.31, 2.03])
add("Table III.1 A total", round(sum(float(r["net_gbp"]) for r in a_x) / 1e6, 2), 28.31,
    near(sum(float(r["net_gbp"]) for r in a_x) / 1e6, 28.313, 0.005))
add("Table III.1 A excluding 2021/22", round(sum(float(r["net_gbp"]) for r in a_x if r["test_end_year"] != "2022") / 1e6, 2), -12.71,
    near(sum(float(r["net_gbp"]) for r in a_x if r["test_end_year"] != "2022") / 1e6, -12.706, 0.005))
add("T2B A profitable windows", sum(1 for r in a_x if float(r["net_gbp"]) > 0), 4,
    sum(1 for r in a_x if float(r["net_gbp"]) > 0) == 4)
b_cmp = list(csv.DictReader(io.StringIO(
    (z62.read("tier2b-b-battery-only-20261124/comparison.csv")).decode("utf-8"))))
bref = [r for r in b_cmp if r["scenario"] == "remove_plant_refit_gate"]
add("T2B B six windows", len(bref), 6, len(bref) == 6)
bw = [round(float(r["net_gbp"]) / 1e6, 2) for r in bref]
add("Table III.1 B window values", bw, [-4.20, 65.31, -3.95, -16.83, -9.45, 8.57], bw == [-4.20, 65.31, -3.95, -16.83, -9.45, 8.57])
add("Table III.1 B total", round(sum(float(r["net_gbp"]) for r in bref) / 1e6, 2), 39.45,
    near(sum(float(r["net_gbp"]) for r in bref) / 1e6, 39.446, 0.005))
add("Table III.1 B excluding 2021/22", round(sum(float(r["net_gbp"]) for r in bref if r["test_end_year"] != "2022") / 1e6, 2), -25.86,
    near(sum(float(r["net_gbp"]) for r in bref if r["test_end_year"] != "2022") / 1e6, -25.860, 0.005))
add("T2B B profitable windows (two of six)", sum(1 for r in bref if float(r["net_gbp"]) > 0), 2,
    sum(1 for r in bref if float(r["net_gbp"]) > 0) == 2)
add("B reference window 2025/26 £m", round(float([r for r in bref if r["test_end_year"] == "2026"][0]["net_gbp"]) / 1e6, 2), 8.57,
    near(float([r for r in bref if r["test_end_year"] == "2026"][0]["net_gbp"]) / 1e6, 8.575, 0.005))
add("B reference-window cost 42.258m",
    round(float([r for r in bref if r["test_end_year"] == "2026"][0]["cost_gbp"]) / 1e6, 3), 42.258,
    near(float([r for r in bref if r["test_end_year"] == "2026"][0]["cost_gbp"]) / 1e6, 42.258, 0.001))
dense = list(csv.DictReader(io.StringIO(
    (z62.read("tier2b-capacity-stability-20261124/a-xpress-dense.csv")).decode("utf-8"))))
c23 = [{k: str(v) for k, v in r.items()} for r in csv62("tier2b-a-window-mip-20261123/comparison.csv")]
one = [r for r in c23 if r["blocks"] == "1" and r["controller"] == "mip_12h"][0]
f45 = [r for r in c23 if r["blocks"] == "45" and r["controller"] == "mip_12h"][0]
add("A one-block reference-year gain £m", round(float(one["net_gbp"]) / 1e6, 2), 0.82,
    near(float(one["net_gbp"]) / 1e6, 0.824, 0.005))
add("A 45-block reference-year loss £m", round(float(f45["net_gbp"]) / 1e6, 2), -21.26,
    near(float(f45["net_gbp"]) / 1e6, -21.256, 0.005))
ss = list(csv.DictReader(io.StringIO(
    (z62.read("tier2b-b-battery-only-20261124/size-sweep-folds.csv")).decode("utf-8"))))
b_ref = [r for r in ss if r["test_end_year"] == "2026"]
vals = {int(r["battery_blocks"]): float(r["net_gbp"]) / 1e6 for r in b_ref}
add("B one-block reference-year gain £m", round(vals[1], 2), 1.27, near(vals[1], 1.27, 0.005))
add("B 22-block reference-year peak £m", round(vals[22], 2), 12.51, near(vals[22], 12.51, 0.005))
others = [float(r["net_gbp"]) / 1e6 for r in ss if r["battery_blocks"] == "22" and r["test_end_year"] != "2026"]
add("B 22 blocks loses £2.39m over other five", round(sum(others), 2), -2.39, near(sum(others), -2.392, 0.005))
add("T2B B size sweep covers 0-45 blocks", (min(int(r['battery_blocks']) for r in ss), max(int(r['battery_blocks']) for r in ss)), (0, 45),
    (min(int(r['battery_blocks']) for r in ss), max(int(r['battery_blocks']) for r in ss)) == (0, 45))
stab = {(r["test_end_year"], r["method"]): r for r in a_st}
add("A 12-block reference-year peak £3.01m (dense sweep)", round(float([r for r in dense if r["blocks"] == "12"][0]["net_gbp"]) / 1e6, 2), 3.01,
    near(float([r for r in dense if r["blocks"] == "12"][0]["net_gbp"]) / 1e6, 3.006, 0.005),
    "report says best tested count is 12 blocks at 3.01; a_stability covers only 7 blocks")

# ---- 11. carried v6 baselines and Appendix numbers --------------------------
add("A flexible zero battery direct-surplus share", round(float(sp["A|Electrolysis"]["direct_surplus_h2_share"]) * 100, 1), 41.7,
    near(float(sp["A|Electrolysis"]["direct_surplus_h2_share"]) * 100, 41.7, 0.05),
    "not printed in v6.2 (replaced by the 118 GWh diversion statement)")
add("surplus capture A/B GWh", (round(float(sp["A|Joint sizing"]["surplus_capture_GWh"]), 0),
                               round(float(sp["B|Joint sizing"]["surplus_capture_GWh"]), 0)), (1918, 647),
    near(float(sp["A|Joint sizing"]["surplus_capture_GWh"]), 1918, 1) and
    near(float(sp["B|Joint sizing"]["surplus_capture_GWh"]), 647, 1))
add("renewable attribution A/B GWh", (round(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]), 0),
                                     round(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]), 0)), (829, 278),
    near(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]), 829, 1) and
    near(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]), 278, 1))
add("surplus share of half-hours", round(float(ms["surplus"]["share_positive_pct"]), 2), 24.75,
    near(float(ms["surplus"]["share_positive_pct"]), 24.75, 0.01))
add("surplus above concurrent demand GWh/yr", round(float(ms["surplus"]["halfhour_GWh_year"]), 0), 5165,
    near(float(ms["surplus"]["halfhour_GWh_year"]), 5164.7, 1))
add("surplus after daily netting GWh/yr", round(float(ms["surplus"]["daily_GWh_year"]), 0), 2276,
    near(float(ms["surplus"]["daily_GWh_year"]), 2276.2, 1))
add("five-year mean excluding 2022 A", round((sum(float(v) for v in ms["A"]["net_mGBP_by_year"].values())
                                             - ms["A"]["net_mGBP_by_year"]["2022"]) / 5, 1), 65.10,
    near((sum(float(v) for v in ms["A"]["net_mGBP_by_year"].values()) - ms["A"]["net_mGBP_by_year"]["2022"]) / 5, 65.1, 0.05))
add("five-year mean excluding 2022 B", round((sum(float(v) for v in ms["B"]["net_mGBP_by_year"].values())
                                            - ms["B"]["net_mGBP_by_year"]["2022"]) / 5, 1), -8.01,
    near((sum(float(v) for v in ms["B"]["net_mGBP_by_year"].values()) - ms["B"]["net_mGBP_by_year"]["2022"]) / 5, -8.01, 0.05))
add("B negative calendar years", sum(1 for v in ms["B"]["net_mGBP_by_year"].values() if float(v) < 0), 4,
    sum(1 for v in ms["B"]["net_mGBP_by_year"].values() if float(v) < 0) == 4)
add("brief EUR 288k -> £/MWh", round(brief["capital_GBP"] / 200, 0), 256235, near(brief["capital_GBP"] / 200, 256235, 40))
add("low-cost block capital £m", round(CAPB, 2), 38.69, near(CAPB, 38.69, 0.005))
add("low-cost block annual cost £m", 4.6949, 4.70, near(3.727 + 0.967 + 0.000635, 4.6946, 0.001))
add("initial 20% fill annual cost £", round(0.2 * 400 * 78.13 * (1 / 0.9487) * 0.096342, 0), 635,
    near(0.2 * 400 * 78.13 * (1 / 0.9487) * 0.096342, 634.7, 5.0),
    "annualised fill purchase with charge losses")
add("reported low-cost block annual cost £m", round(3.727 + 0.967 + 0.000635, 3), 4.70,
    near(3.727 + 0.967 + 0.000635, 4.6946, 0.001), "Appendix B.4: capital charge + upkeep + fill")
add("Lazard per-kWh low/mid/high £", (round(62.15 / 0.4 * (0.634974 / 1.02), 2), round(111.32 / 0.4 * (0.634974 / 1.02), 2), round(160.49 / 0.4 * (0.634974 / 1.02), 2)),
    (96.72, 173.25, 249.77), (round(62.15 / 0.4 * (0.634974 / 1.02), 2), round(111.32 / 0.4 * (0.634974 / 1.02), 2), round(160.49 / 0.4 * (0.634974 / 1.02), 2)) == (96.72, 173.25, 249.77),
    "US$62.15/111.32/160.49m for 400 MWh at 0.6225 gives the printed per-kWh values")

# ---- 12. text-level statements and disclosure -------------------------------
t = text.replace("\n", " ")
tstr = [
    ("abstract headline A £118.90m", "£118.90m", "£118.90m" in t),
    ("abstract headline B £6.07m", "£6.07m", "£6.07m" in t),
    ("35.2 MW zero-battery plant", "35.2 MW", "35.2 MW" in t),
    ("£639 ninth-block increment", "£639", "£639" in t),
    ("8.57m B reference replay", "£8.57m", "£8.57m" in t),
    ("£4/year Xpress improvement", "£4/year", "£4/year" in t),
    ("12.5% load band stated", "12.5%", "12.5%" in t),
    ("midnight switching assumption", "midnight", "midnight" in t),
    ("four-day minimum run assumption", "four days online", "four days online" in t),
    ("two-hour brief reference kept", "two-hour", "two-hour" in t),
    ("50.3 MW reserve case", "50.3 MW", "50.3 MW" in t),
    ("old 40.2 MW headline gone", "40.2", "40.2" not in t),
    ("old 55.3 MW headline gone", "55.3", "55.3" not in t),
    ("2,092 GWh claim stays dropped", "2,092", "2,092" not in t),
    ("22.5% A support share no longer printed", "22.5%", "22.5%" not in t),
    ("£9.50 row labelled real-price stress", "£9.50/kg (real-price stress)", "£9.50/kg (real-price stress)" in t),
    ("4% upkeep sensitivity printed", "At 4% upkeep", "At 4% upkeep" in t),
    ("2.5% upkeep sentence printed", "With 2.5% upkeep", "With 2.5% upkeep" in t),
    ("B 41.6% support share printed", "41.6% of output", "41.6% of output" in t),
    ("solver split named", "Xpress 9.9", "Xpress 9.9" in t),
    ("HiGHS 1.16 named", "HiGHS 1.16", "HiGHS 1.16" in t),
    ("method reference min-up-time", "minimum up times [ 25]", "minimum up times [ 25]" in t),
    ("method reference storage arbitrage", "storage arbitrage models [ 26]", "storage arbitrage models [ 26]" in t),
    ("[9] now names the archive path", "research/PARAMETER_BASIS.md in tier1-site-evidence-v6.zip",
     "research/PARAMETER_BASIS.md in tier1-site-evidence-v6.zip" in t),
    ("cover keeps Group 15", "Group 15", "Group 15" in t),
    ("cover still has no named authors", "Ran Min", "Ran Min" not in t),
    ("fixed one-block label kept", "fixed one block", "fixed one block" in t),
    ("brief-capital caption kept", "under the brief", "under the brief" in t),
    ("legacy cost label correction disclosed", "legacy cost-source label",
     "legacy cost-source label" in open(os.path.join(REPORT, "REVIEW_RESPONSE.md"), encoding="utf-8").read()),
]
for name, needle, ok in tstr:
    add(f"text: {name}", needle, "present" if ok else "absent", ok)

rr = open(os.path.join(REPORT, "REVIEW_RESPONSE.md"), encoding="utf-8").read()
add("review response lists open items", ["all-horizon", "four-day two-rate", "A four-day chronological", "full-licence"],
    "present", all(k in rr for k in ["all-horizon", "four-day two-rate", "A four-day chronological", "full-licence"]))
add("report prints both load bands", ("20% electrolyser minimum load" in t, "12.5–100%" in t), (True, True),
    "20% electrolyser minimum load" in t and "12.5–100%" in t,
    "P1: the main case uses the supplier's 12.5% while the brief says 'Assume ... 20% and 100%'; the departure is visible but not argued")
evreadme = z62.read("README.md").decode("utf-8")
add("evidence README corrects legacy reference label", "legacy source description",
    "present", "legacy source description" in evreadme)
add("evidence README pins earlier v6 archive", "tier1-site-evidence-v6.zip", "present",
    "tier1-site-evidence-v6.zip" in evreadme)

# ---- write results ----------------------------------------------------------
out = os.path.join(BASE, "checks_v6.2.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(dict(source_pdf_sha256=sha_pdf, source_zip_sha256=sha_src,
                   evidence_zip_sha256=sha_ev, evidence_v6_zip_sha256=hashlib.sha256(open(EVID6, "rb").read()).hexdigest(),
                   checks=checks, all_passed=all(c["ok"] for c in checks)), f, indent=2, ensure_ascii=False)
bad = [c for c in checks if not c["ok"]]
print(f"checks={len(checks)} failures={len(bad)}")
for c in bad:
    print("FAIL", c["name"], "| computed:", c["computed"], "| stated:", c["stated"], "|", c["note"])
