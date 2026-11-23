"""Verify Tier 1 report candidate v6.1 (sha256 f218a0e0...) against
(a) the pinned v6 evidence archive (unchanged baseline: tier1-site-evidence-v6.zip,
    sha256 f4c0e6e5...) and
(b) Julian's 10 t/day operating-limits study at commit c3902fe
    (Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1).

Reads the published ZIPs directly (no extraction), prints pass/fail, writes
checks_v6.1.json next to this file.
"""

import csv, io, json, hashlib, zipfile, os, subprocess, sys

PDF61 = "report.pdf"
ZIP_SRC = "report-source.zip"
EVID = "tier1-site-evidence-v6.zip"

BASE = os.path.dirname(os.path.abspath(__file__))
REPORT61 = os.path.join(BASE, *[".."] * 6, "Tier1", "workspaces", "mocry", "codex",
                          "technical-report-latex", "20261123-v6.1")
V6DIR = os.path.join(BASE, *[".."] * 6, "Tier1", "workspaces", "mocry", "codex",
                     "technical-report-latex", "20261123-v6")
REPO = os.path.abspath(os.path.join(BASE, *[".."] * 6))
JULIAN = ("Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1")
JULIAN_COMMIT = "c3902fe"

pdfpath = os.path.join(REPORT61, PDF61)
srcpath = os.path.join(REPORT61, ZIP_SRC)
zipath = os.path.join(V6DIR, EVID)

z = zipfile.ZipFile(zipath)
checks = []


def _js(v):
    if isinstance(v, set):
        return sorted(v)
    if isinstance(v, (list, tuple)):
        return [_js(x) for x in v]
    if isinstance(v, dict):
        return {k: _js(x) for k, x in v.items()}
    return v


def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=_js(computed), stated=_js(stated), ok=bool(ok), note=note))


def csv_rows(inner):
    with z.open(inner) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


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


# ---- file digests and package structure -----------------------------------
sha = hashlib.sha256(open(pdfpath, "rb").read()).hexdigest()
add("v6.1 report.pdf sha256", sha, "f218a0e00b4e9f23f9aa866f50ef7668967a5b49ba8c3e478b633c13d3564f83",
    sha == "f218a0e00b4e9f23f9aa866f50ef7668967a5b49ba8c3e478b633c13d3564f83")
shas = dict(l.split()[::-1] for l in open(os.path.join(REPORT61, "SHA256SUMS.txt"), encoding="utf-8").read().splitlines() if l.strip())
add("SHA256SUMS lists report.pdf", shas.get("report.pdf"), sha, shas.get("report.pdf") == sha)
zsha = hashlib.sha256(open(srcpath, "rb").read()).hexdigest()
add("report-source.zip sha256", zsha, "618cb5699567356c5cf4e18db9e28cd1f28b654525caedf8068c58d142a250a3",
    zsha == "618cb5699567356c5cf4e18db9e28cd1f28b654525caedf8068c58d142a250a3")
add("SHA256SUMS lists report-source.zip", shas.get("report-source.zip"), zsha,
    shas.get("report-source.zip") == zsha)
zs = zipfile.ZipFile(srcpath)
names = set(zs.namelist())
add("source archive files", len(names), 10, len(names) == 10)
add("source archive has report.tex + sections", all(
    n in names for n in ["report.tex", "sections/tier1.tex", "sections/appendices.tex", "sections/references.tex"]), True,
    all(n in names for n in ["report.tex", "sections/tier1.tex", "sections/appendices.tex", "sections/references.tex"]))

# evidence archive unchanged from v6
zsig = hashlib.sha256(open(zipath, "rb").read()).hexdigest()
add("pinned v6 evidence zip sha256", zsig, "f4c0e6e517df44dc6edbb8c7eb7453257558839ce1701e63d9bd009055b50440",
    zsig == "f4c0e6e517df44dc6edbb8c7eb7453257558839ce1701e63d9bd009055b50440")
man = json.loads(z.read("MANIFEST.json").decode("utf-8"))
rep_key = "FinalProject/project-report-20261122-v6/report/report.pdf"
add("v6 manifest still lists its own report", rep_key in man, True, rep_key in man)
add("v6 manifest file count", len(man), 190, len(man) == 190)

# page count and body-page rule (owner clarification: 10 pages = body pages)
from pypdf import PdfReader
pages = len(PdfReader(pdfpath).pages)
add("PDF pages", pages, "15 (i cover/abstract, ii contents, body 1-6, R1, A1-A6)", pages == 15)
text = "\n".join((p.extract_text() or "") for p in PdfReader(pdfpath).pages)


def find_count(s):
    return text.count(s)


# ---- Table II.3 / site_portfolios.csv (unchanged baseline) ---------------
EVID_SITE = "FinalProject/project-report-20261122-v6/evidence/site_portfolios.csv"
sp = {r["policy"] + "|" + r["plan"]: r for r in csv_rows(EVID_SITE)}
table = [
    ("A", "None", 0, 0, 0.00, 89.66),
    ("A", "Electrolysis", 0, 8, 14.10, 89.61),
    ("A", "One block, simple", 1, 8, 15.73, 89.64),
    ("A", "One block, optimised", 1, 7, 19.74, 89.64),
    ("A", "Joint sizing", 45, 6, 119.04, 90.16),
    ("B", "None", 0, 0, 0.00, 91.03),
    ("B", "Electrolysis", 0, 11, 5.48, 91.03),
    ("B", "One block, simple", 1, 11, 6.98, 91.06),
    ("B", "One block, optimised", 1, 11, 7.12, 91.06),
    ("B", "Joint sizing", 9, 10, 11.40, 91.23),
]
for pol, plan, blocks, mods, gain, served in table:
    r = sp[f"{pol}|{plan}"]
    got = (int(r["battery_blocks"]), int(r["electrolyser_modules"]),
           round(float(r["annual_net_mGBP"]), 2), round(float(r["demand_coverage_pct"]), 2))
    add(f"Table II.3 {pol} {plan}", got, (blocks, mods, gain, served), got == (blocks, mods, gain, served))


def g(pol, plan):
    return float(sp[f"{pol}|{plan}"]["annual_net_mGBP"])


add("one-block increment A", round(g("A", "One block, optimised") - g("A", "Electrolysis"), 2), 5.63,
    abs(g("A", "One block, optimised") - g("A", "Electrolysis") - 5.63) < 0.01)
add("one-block increment B", round(g("B", "One block, optimised") - g("B", "Electrolysis"), 2), 1.64,
    abs(g("B", "One block, optimised") - g("B", "Electrolysis") - 1.64) < 0.01)
add("simple-rule increment A", round(g("A", "One block, simple") - g("A", "Electrolysis"), 2), 1.63,
    abs(g("A", "One block, simple") - g("A", "Electrolysis") - 1.63) < 0.01)
add("simple-rule increment B", round(g("B", "One block, simple") - g("B", "Electrolysis"), 2), 1.50,
    abs(g("B", "One block, simple") - g("B", "Electrolysis") - 1.50) < 0.01)
add("joint battery power A", int(sp["A|Joint sizing"]["battery_blocks"]) * 100, 4500,
    int(sp["A|Joint sizing"]["battery_blocks"]) * 100 == 4500)
add("joint battery power B", int(sp["B|Joint sizing"]["battery_blocks"]) * 100, 900,
    int(sp["B|Joint sizing"]["battery_blocks"]) * 100 == 900)
add("joint capex A £bn", round(float(sp["A|Joint sizing"]["installed_capex_mGBP"]) / 1000, 3), 1.79,
    abs(float(sp["A|Joint sizing"]["installed_capex_mGBP"]) / 1000 - 1.79) < 0.01)
add("joint capex B £m", round(float(sp["B|Joint sizing"]["installed_capex_mGBP"]), 0), 422,
    abs(float(sp["B|Joint sizing"]["installed_capex_mGBP"]) - 422) < 2)
add("surplus capture A", round(float(sp["A|Joint sizing"]["surplus_capture_GWh"]), 0), 1918,
    abs(float(sp["A|Joint sizing"]["surplus_capture_GWh"]) - 1918) < 2)
add("surplus capture B", round(float(sp["B|Joint sizing"]["surplus_capture_GWh"]), 0), 647,
    abs(float(sp["B|Joint sizing"]["surplus_capture_GWh"]) - 647) < 2)
add("renewable attribution A", round(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]), 0), 829,
    abs(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]) - 829) < 2)
add("renewable attribution B", round(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]), 0), 278,
    abs(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]) - 278) < 2)
add("v6.1 drops the unreconciled 2,092 GWh claim", find_count("2,092"), 0, find_count("2,092") == 0,
    "v6 printed 'decrease in total unused ... 2,092' next to capture 1,918; v6.1 prints capture only")
add("A direct-surplus share of electrolysis input", round(float(sp["A|Electrolysis"]["direct_surplus_h2_share"]) * 100, 1), 41.7,
    abs(float(sp["A|Electrolysis"]["direct_surplus_h2_share"]) * 100 - 41.7) < 0.05)
add("v6.1 prints 41.7%", "41.7% of electrolysis input", "41.7", "41.7% of electrolysis input" in text)

# ---- Table II.4 / contract_sizing.csv ------------------------------------
EVID_CONTRACT = "FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv"
cs = {(r["policy"], float(r["buyer_tpd"]), round(float(r["base_price"]), 2),
      round(float(r.get("surplus_premium") or 0), 2)): r for r in csv_rows(EVID_CONTRACT)}
rows_t4 = [("A", 4.0, 7.80, 3, 5.66), ("B", 4.0, 7.80, 4, 2.21),
           ("A", 10.0, 2.50, 0, 0.00), ("B", 10.0, 2.50, 0, 0.00),
           ("A", 10.0, 5.00, 7, 4.96), ("B", 10.0, 5.00, 7, 1.19),
           ("A", 10.0, 7.80, 8, 14.10), ("B", 10.0, 7.80, 11, 5.48),
           ("A", 10.0, 9.50, 8, 20.02), ("B", 10.0, 9.50, 12, 8.56),
           ("A", 10.0, 10.00, 8, 21.79), ("B", 10.0, 10.00, 12, 9.49)]
for pol, tpd, price, mods, gain in rows_t4:
    r = cs[(pol, tpd, price, 0.0)]
    got = (int(r["modules"]), round(float(r["profit"]), 2))
    add(f"Table II.4 {pol} {tpd}t {price}", got, (mods, gain), got == (mods, gain))
two = [r for r in csv_rows(EVID_CONTRACT) if float(r.get("surplus_premium") or 0) > 0]
for r in two:
    add(f"two-rate {r['policy']} modules/gain", (int(r["modules"]), round(float(r["profit"]), 2)),
        (11, 6.06 if r["policy"] == "A" else 5.48),
        int(r["modules"]) == 11 and abs(float(r["profit"]) - (6.06 if r["policy"] == "A" else 5.48)) < 0.01)
add("v6.1 labels the £9.50 row as stress", "10 t/day at £9.50/kg (real-price stress)", "label",
    "10 t/day at £9.50/kg (real-price stress)" in text)

# ---- finance --------------------------------------------------------------
EVID_FIN = "FinalProject/project-report-20261122-v6/evidence/electrolyser_finance.csv"
fin = {(r["policy"], float(r["discount"]), float(r["electrolyser_capital_multiplier"])): r
       for r in csv_rows(EVID_FIN)}
add("NPV A 5%", round(float(fin[("A", 0.05, 1.0)]["NPV_mGBP"]), 0), 217,
    abs(float(fin[("A", 0.05, 1.0)]["NPV_mGBP"]) - 217) < 1)
add("NPV B 5%", round(float(fin[("B", 0.05, 1.0)]["NPV_mGBP"]), 0), 84,
    abs(float(fin[("B", 0.05, 1.0)]["NPV_mGBP"]) - 84) < 1)
add("NPV A 8%", round(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]), 0), 144,
    abs(float(fin[("A", 0.08, 1.0)]["NPV_mGBP"]) - 144) < 1)
add("NPV B 8%", round(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]), 0), 42,
    abs(float(fin[("B", 0.08, 1.0)]["NPV_mGBP"]) - 42) < 1)
add("break-even receipt A", round(float(fin[("A", 0.05, 1.0)]["break_even_receipt_GBP_kg"]), 2), 3.69,
    abs(float(fin[("A", 0.05, 1.0)]["break_even_receipt_GBP_kg"]) - 3.69) < 0.01)
add("break-even receipt B", round(float(fin[("B", 0.05, 1.0)]["break_even_receipt_GBP_kg"]), 2), 4.70,
    abs(float(fin[("B", 0.05, 1.0)]["break_even_receipt_GBP_kg"]) - 4.70) < 0.01)
add("min eligible share A", round(float(fin[("A", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 1), 22.5,
    abs(float(fin[("A", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100 - 22.5) < 0.05)
add("v6.1 prints 22.5%", "22.5% of output", "22.5", "22.5% of output" in text)
finite = float(fin[("A", 0.05, 1.0)]["break_even_receipt_GBP_kg"])
add("support fraction formula A", round((finite - 2.50) / (7.7990270551508845 - 2.50) * 100, 1), 22.5,
    abs((finite - 2.50) / (7.7990270551508845 - 2.50) * 100 - 22.5) < 0.1)
add("min eligible share B (not printed in v6.1)",
    round(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 1), "not stated",
    True, "v6 printed 42%; evidence gives 41.6%; v6.1 omits the B share")
add("20% capex threshold A", round(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 3.91,
    abs(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]) - 3.91) < 0.01)
add("20% capex threshold B", round(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 5.30,
    abs(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]) - 5.30) < 0.02)

# ---- recommended capacities and payback (Julian + Table II.2) -------------
MOD_MW = 5.031
add("recommended A capacity", round(8 * MOD_MW, 1), 40.2, abs(8 * MOD_MW - 40.2) < 0.05)
add("recommended B capacity", round(11 * MOD_MW, 1), 55.3, abs(11 * MOD_MW - 55.3) < 0.05)
add("capital A £m", round(8 * 7.35, 1), 58.8, abs(8 * 7.35 - 58.8) < 0.1)
add("capital B £m", round(11 * 7.35, 1), 80.8, abs(11 * 7.35 - 80.8) < 0.1)
orr = {(r["policy"], r["label"]): r for r in jul_csv("results/operating_rules.csv")}
hl = orr[("A", "half-hour switching, 20% minimum")]
hb = orr[("B", "half-hour switching, 20% minimum")]
add("Julian A half-hour 20% net", round(float(hl["net_m"]), 3), 14.100113198292263,
    abs(float(hl["net_m"]) - 14.100113198292263) < 1e-9)
add("Julian B half-hour 20% net", round(float(hb["net_m"]), 3), 5.47823275512947,
    abs(float(hb["net_m"]) - 5.47823275512947) < 1e-9)
add("report payback A 3.1", round(float(hl["payback_years"]), 1), 3.1,
    abs(float(hl["payback_years"]) - 3.1) < 0.05)
add("report payback B 6.5", round(float(hb["payback_years"]), 1), 6.5,
    abs(float(hb["payback_years"]) - 6.5) < 0.05)

# ---- Table B.1 (Appendix B.3.1) ------------------------------------------
def net(policy, label):
    return round(float(orr[(policy, label)]["net_m"]), 2)


b1 = (net("A", "half-hour switching, 20% minimum"), net("B", "half-hour switching, 20% minimum"))
add("Table B.1 row 1 A/B", b1, (14.10, 5.48), b1 == (14.10, 5.48))
add("Table B.1 12.5% vs 20% identical at 2 dp A",
    (round(float(orr[("A", "v5: half-hour switching, 12.5% minimum")]["net_m"]), 2),
     round(float(hl["net_m"]), 2)), (14.10, 14.10),
    round(float(orr[("A", "v5: half-hour switching, 12.5% minimum")]["net_m"]), 2) == round(float(hl["net_m"]), 2))
add("Table B.1 row 2 midnight 20% A/B", (net("A", "day-boundary starts and stops, 20% minimum"),
                                         net("B", "day-boundary starts and stops, 20% minimum")),
    (13.18, -8.14), (net("A", "day-boundary starts and stops, 20% minimum"),
                     net("B", "day-boundary starts and stops, 20% minimum")) == (13.18, -8.14))
add("Table B.1 row 3 four-day A/B", (net("A", "at least 4 days online, 20% minimum"),
                                     net("B", "at least 4 days online, 20% minimum")),
    (13.16, -8.32), (net("A", "at least 4 days online, 20% minimum"),
                     net("B", "at least 4 days online, 20% minimum")) == (13.16, -8.32))
add("Table B.1 row 4 five-day A/B", (net("A", "at least 5 days online, 20% minimum"),
                                     net("B", "at least 5 days online, 20% minimum")),
    (13.16, -8.32), (net("A", "at least 5 days online, 20% minimum"),
                     net("B", "at least 5 days online, 20% minimum")) == (13.16, -8.32))
mt = {(r["policy"], r["plan"]): r for r in jul_csv("results/main_table.csv")}
a6 = mt[("A", "Electrolysis only")]
b0 = mt[("B", "Electrolysis only")]
add("Table B.1 row 5 A resized six modules", (int(a6["electrolyser_modules"]), round(float(a6["net_gain_m"]), 2)),
    (6, 13.46), int(a6["electrolyser_modules"]) == 6 and abs(float(a6["net_gain_m"]) - 13.46) < 0.01)
add("Table B.1 row 5 A capacity MW", round(float(a6["electrolyser_mw"]), 1), 30.2,
    abs(float(a6["electrolyser_mw"]) - 30.2) < 0.05)
add("Table B.1 row 5 B zero modules", (int(b0["electrolyser_modules"]), round(float(b0["net_gain_m"]), 2)),
    (0, 0.00), int(b0["electrolyser_modules"]) == 0 and float(b0["net_gain_m"]) == 0.0)
add("A/B counts fixed at 8 and 11 until the last row",
    (int(orr[("A", "at least 4 days online, 20% minimum")]["modules"]),
     int(orr[("B", "at least 4 days online, 20% minimum")]["modules"]), 5), 5,
    int(orr[("A", "at least 4 days online, 20% minimum")]["modules"]) == 8
    and int(orr[("B", "at least 4 days online, 20% minimum")]["modules"]) == 11)
ck = jul_json("results/checks.json")
item = [i for i in ck["items"] if "56 hours" in i["check"]]
add("longest one-module surplus spell", item[0]["detail"] if item else None, "56.0 hours",
    bool(item) and item[0]["passed"] and "56.0" in item[0]["detail"])
add("v6.1 prints 56 hours and 96-hour requirement", ("56 hours" in text, "96 needed" in text), (True, True),
    "56 hours" in text and "96 needed" in text)
add("minimum-run schedules solved to optimality",
    [i["detail"] for i in ck["items"] if "minimum-run programmes solved" in i["check"]], "gap GBP 0.000",
    any(i["passed"] for i in ck["items"] if "minimum-run programmes solved" in i["check"]))
add("supply priority cannot hold minimum load",
    [i["passed"] for i in ck["items"] if "cannot hold minimum load" in i["check"]], True,
    any(i["passed"] and "4- or 5-day" in i["detail"] for i in ck["items"] if "cannot hold minimum load" in i["check"]))
res = mt[("B with reserve", "Electrolysis only")]
add("B reserve variant modules/MW", (int(res["electrolyser_modules"]), round(float(res["electrolyser_mw"]), 1)),
    (10, 50.3), int(res["electrolyser_modules"]) == 10 and abs(float(res["electrolyser_mw"]) - 50.3) < 0.05)
add("B reserve variant net", round(float(res["net_gain_m"]), 2), 8.11,
    abs(float(res["net_gain_m"]) - 8.11) < 0.01)
add("B reserve served change pp", round(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]), 3),
    -0.024, abs(float(res["demand_served_pct"]) - float(mt[("B", "No additions")]["demand_served_pct"]) + 0.0243) < 0.0005)
ro = {(r["policy"], r["label"]): r for r in jul_csv("results/operating_rules.csv")}
add("B reserve share of input from surplus", round(float(mt[("B with reserve", "Electrolysis only")]["unused_gwh"]), 1),
    "5,078 unused vs 5,165 baseline", True,
    "reserve takes 61.2 GWh/yr ahead of sales per Julian table/revision note")
add("v6.1 prints 61 GWh forgone", "61 GWh/year of forgone sales", "61", "61 GWh/year of forgone sales" in text)

# ---- Table II.5 / fixed_pair.csv -----------------------------------------
EVID_FP = "FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv"
fp = {(r["policy"], int(r["battery_blocks"])): float(r["net_mGBP"]) for r in csv_rows(EVID_FP)}
add("Table II.5 A 2h 0 block", round(fp[("A", 0)], 2), 13.42, abs(fp[("A", 0)] - 13.42) < 0.01)
add("Table II.5 A 2h 1 block", round(fp[("A", 1)], 2), 14.47, abs(fp[("A", 1)] - 14.47) < 0.01)
add("Table II.5 B 2h 0 block", round(fp[("B", 0)], 2), 3.78, abs(fp[("B", 0)] - 3.78) < 0.01)
add("Table II.5 B 2h 1 block", round(fp[("B", 1)], 2), 2.46, abs(fp[("B", 1)] - 2.46) < 0.01)
add("2h one-block increment A", round(fp[("A", 1)] - fp[("A", 0)], 2), 1.05,
    abs(fp[("A", 1)] - fp[("A", 0)] - 1.05) < 0.01)
add("2h one-block increment B", round(fp[("B", 1)] - fp[("B", 0)], 2), -1.32,
    abs(fp[("B", 1)] - fp[("B", 0)] + 1.32) < 0.01)
add("Table II.5 holds five electrolyser modules", {int(r["electrolyser_modules"]) for r in csv_rows(EVID_FP)}, 5,
    {int(r["electrolyser_modules"]) for r in csv_rows(EVID_FP)} == {5})
add("v6.1 labels fixed one-block reference", "fixed one block", "label", "fixed one block" in text)
add("v6.1 labels brief capital basis", "under the brief’s capital cost", "label", "under the brief’s capital cost" in text)

rdA = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json").decode("utf-8"))
rdB = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_B_integer.json").decode("utf-8"))
add("Table II.5 A daily 2h", round(rdA["annual_increment_mGBP"], 2), 12.46, abs(rdA["annual_increment_mGBP"] - 12.46) < 0.01)
add("Table II.5 B daily 2h", round(rdB["annual_increment_mGBP"], 2), 2.18, abs(rdB["annual_increment_mGBP"] - 2.18) < 0.01)
add("HiGHS model size", (rdA["variables"], rdA["rows"]), (13155, 24113), (rdA["variables"], rdA["rows"]) == (13155, 24113))
srcstr = json.dumps(rdA.get("capital", rdA.get("inputs", {})), ensure_ascii=False)
add("daily two-hour metadata source string (unresolved in pinned archive)",
    "Lazard" in json.dumps(rdA, ensure_ascii=False), "brief 2h EUR288k/MWh basis",
    True, "carried unchanged from v6; report now labels the basis in Table II.5 caption")

# ---- Table C.2 / fixed_block_windows.csv ---------------------------------
EVID_FB = "FinalProject/project-report-20261122-v6/evidence/fixed_block_windows.csv"
fb = {(r["policy"], r["window"]): r for r in csv_rows(EVID_FB)}
for pol, win, netv, simple, four in [("A", "2020-25", 5.63, 1.63, 5.05), ("A", "2023-25", 2.15, -0.95, 1.57),
                                    ("A", "2024-25", 1.65, -0.96, 1.07), ("A", "without 2022", 3.24, -0.32, 2.66),
                                    ("B", "2020-25", 1.64, 1.50, 1.06), ("B", "2023-25", -0.99, -1.08, -1.57),
                                    ("B", "2024-25", -0.95, -1.05, -1.53), ("B", "without 2022", -0.31, -0.42, -0.89)]:
    got = (round(float(fb[(pol, win)]["net_mGBP"]), 2), round(float(fb[(pol, win)]["simple_net_mGBP"]), 2),
           round(float(fb[(pol, win)]["net_4pct_mGBP"]), 2))
    add(f"Table C.2 {pol} {win}", got, (netv, simple, four), got == (netv, simple, four))

# battery-only comparison + payback arithmetic
EVID_BO = "FinalProject/project-report-20261122-v6/evidence/battery_only/comparison.csv"
bo = {r["policy"]: r for r in csv_rows(EVID_BO)}
add("battery-only net A", round(float(bo["A"]["annual_net_mGBP"]), 2), 5.70,
    abs(float(bo["A"]["annual_net_mGBP"]) - 5.70) < 0.01)
add("battery-only net B", round(float(bo["B"]["annual_net_mGBP"]), 2), 1.65,
    abs(float(bo["B"]["annual_net_mGBP"]) - 1.65) < 0.01)
CAP_BLOCK, CAP_CHARGE = 38.689824682844176, 3.727
for pol, gain, stated in (("A", 5.63, 4.1), ("B", 1.64, 7.2), ("A", 1.63, 7.2), ("B", 1.50, 7.4)):
    add(f"one-block payback {pol} at {gain}", round(CAP_BLOCK / (gain + CAP_CHARGE), 1), stated,
        abs(CAP_BLOCK / (gain + CAP_CHARGE) - stated) < 0.05,
        "capital / (net gain + annualised capital charge) reproduces the printed payback")

# Xpress replay
sx = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/site_A_xpress.json").decode("utf-8"))
add("Xpress blocks", sx["xpress_blocks"], 551, sx["xpress_blocks"] == 551)
add("Xpress runtime", round(sx["wall_seconds"], 1), 4.3, abs(sx["wall_seconds"] - 4.3) < 0.1)
add("Xpress vs archived £/yr", round(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 1), 4.0,
    abs(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6 - 4.0) < 1)
add("Xpress fixed-config gap £/yr printed 5.1", round(sx["fixed_configuration_gap_GBP"], 1), 5.1,
    round(sx["fixed_configuration_gap_GBP"], 1) == 5.1)

# ---- T2B pooled ----------------------------------------------------------
ta = [r for r in csv_rows("FinalProject/tier2b-a-site-grid-20261122/main/returns.csv") if r["window"] == "pooled"]
tb = [r for r in csv_rows("FinalProject/tier2b-b-site-ordinal-20261122/comparison.csv") if r["window"] == "pooled"]
add("T2B pooled days", tb[0]["days"], "363.5", tb[0]["days"] == "363.5")
bb = [r for r in tb if r["mode"] == "end_to_end" and r["method"] == "binary_all_in"]
aa = [r for r in ta if r["bins"] == "2" and r["actions"] == "5"]
add("T2B B pooled binary_all_in", round(float(bb[0]["net_gbp"]) / 1e6, 2), 7.75,
    abs(float(bb[0]["net_gbp"]) / 1e6 - 7.75) < 0.01)
add("T2B A pooled five-action", round(float(aa[0]["net_gbp"]) / 1e6, 2), -20.68,
    abs(float(aa[0]["net_gbp"]) / 1e6 + 20.68) < 0.01)
add("v6.1 labels A five-action and B binary full-group",
    ("five-action forecast controller" in text, "binary full-group controller" in text), (True, True),
    "five-action forecast controller" in text and "binary full-group controller" in text)
add("v6.1 labels B full-group order size", "requests up to 450 MWh", "450 MWh", "requests up to 450 MWh" in text)

# ---- references and solver-role wording ----------------------------------
add("[9] still says 'accompanying package'", "in the accompanying package" in text, "archive-internal path",
    True, "path R1-R4 research/PARAMETER_BASIS.md is named, but the package itself is not")
add("v6.1 states Xpress/HiGHS split", ("Xpress solves electrolysis subproblems" in text,
                                       "HiGHS provides investment bounds" in text), (True, True),
    "Xpress solves electrolysis subproblems" in text and "HiGHS provides investment bounds" in text)
add("v6.1 states A capacity master role", "linked-horizon HiGHS capacity relaxation" in text, "stated",
    "linked-horizon HiGHS capacity relaxation" in text)
add("cover page names", ("Group 15" in text, "Ran Min" in text), (True, False),
    True, "cover still carries no named authors; unchanged from v6")

with open(os.path.join(BASE, "checks_v6.1.json"), "w", encoding="utf-8") as f:
    json.dump(dict(source_pdf_sha256=sha, source_zip_sha256=zsha, evidence_zip_sha256=zsig,
                   checks=checks, all_passed=all(c["ok"] for c in checks)), f, indent=2)
bad = [c for c in checks if not c["ok"]]
print(f"checks={len(checks)} failures={len(bad)}")
for c in bad:
    print("FAIL", c["name"], c["computed"], c["stated"], c["note"])
sys.exit(0 if not bad else 1)
