"""Verify Tier 1 report v6 (sha256 769b89e4...) against its own evidence archive.

Reads the published ZIP directly (no extraction) and compares printed values in
Chapter II / Appendix C with CSV/JSON records. Prints pass/fail and writes
checks_v6.json next to this file.
"""

import csv, io, json, hashlib, zipfile, os

ZIP = "tier1-site-evidence-v6.zip"
PDF = "report.pdf"
OUT = "checks_v6.json"
BASE = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE, *[".."] * 6, "Tier1", "workspaces", "mocry", "codex",
                          "technical-report-latex", "20261123-v6")

zippath = os.path.join(REPORT_DIR, ZIP)
pdfpath = os.path.join(REPORT_DIR, PDF)

z = zipfile.ZipFile(zippath)
checks = []

def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=computed, stated=stated, ok=bool(ok), note=note))

def csv_rows(inner):
    with z.open(inner) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))

def cnum(v):
    return float(v) if v not in ("", None) else None

# ---- file digests ---------------------------------------------------------
sha = hashlib.sha256(open(pdfpath, "rb").read()).hexdigest()
add("report.pdf sha256", sha, "769b89e4100b33ee6de555530fd147f6b90ff8b34af2832bc59743a71a442db8",
    sha == "769b89e4100b33ee6de555530fd147f6b90ff8b34af2832bc59743a71a442db8")
zp = hashlib.sha256(open(zippath, "rb").read()).hexdigest()
add("zip sha256", zp, "f4c0e6e517df44dc6edbb8c7eb7453257558839ce1701e63d9bd009055b50440",
    zp == "f4c0e6e517df44dc6edbb8c7eb7453257558839ce1701e63d9bd009055b50440")

man = json.loads(z.read("MANIFEST.json").decode("utf-8"))
rep_key = "FinalProject/project-report-20261122-v6/report/report.pdf"
add("manifest lists report.pdf", rep_key in man, True, rep_key in man)
add("manifest report sha matches", man.get(rep_key, {}).get("sha256"), sha,
    man.get(rep_key, {}).get("sha256") == sha)
add("manifest file count", len(man), "190", len(man) == 190)

# page count
from pypdf import PdfReader
pages = len(PdfReader(pdfpath).pages)
add("PDF pages", pages, "15 (body 1-6, R1, A1-A6)", pages == 15)

# ---- Table II.3 / site_portfolios.csv ------------------------------------
sp = {r["policy"] + "|" + r["plan"]: r for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/site_portfolios.csv")}
table = {
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
}
for pol, plan, blocks, mods, gain, served in table:
    r = sp[f"{pol}|{plan}"]
    got = (int(r["battery_blocks"]), int(r["electrolyser_modules"]), round(float(r["annual_net_mGBP"]), 2), round(float(r["demand_coverage_pct"]), 2))
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
add("unused decrease A", round(float(sp["A|None"]["annual_unused_GWh"]) - float(sp["A|Joint sizing"]["annual_unused_GWh"]), 0), 2092,
    abs(float(sp["A|None"]["annual_unused_GWh"]) - float(sp["A|Joint sizing"]["annual_unused_GWh"]) - 2092) < 2)
add("unused decrease B", round(float(sp["B|None"]["annual_unused_GWh"]) - float(sp["B|Joint sizing"]["annual_unused_GWh"]), 0), 647,
    abs(float(sp["B|None"]["annual_unused_GWh"]) - float(sp["B|Joint sizing"]["annual_unused_GWh"]) - 647) < 2)
add("renewable attribution A", round(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]), 0), 829,
    abs(float(sp["A|Joint sizing"]["renewable_mix_attribution_GWh"]) - 829) < 2)
add("renewable attribution B", round(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]), 0), 278,
    abs(float(sp["B|Joint sizing"]["renewable_mix_attribution_GWh"]) - 278) < 2)

# ---- Table II.4 / contract_sizing.csv ------------------------------------
cs = {(r["policy"], float(r["buyer_tpd"]), round(float(r["base_price"]), 2), round(float(r.get("surplus_premium") or 0), 2)): r
      for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv")}
rows_t4 = [("A", 4.0, 7.80, 3, 5.66), ("B", 4.0, 7.80, 4, 2.21),
           ("A", 10.0, 2.50, 0, 0.00), ("B", 10.0, 2.50, 0, 0.00),
           ("A", 10.0, 5.00, 7, 4.96), ("B", 10.0, 5.00, 7, 1.19),
           ("A", 10.0, 7.80, 8, 14.10), ("B", 10.0, 7.80, 11, 5.48),
           ("A", 10.0, 9.50, 8, 20.02), ("B", 10.0, 9.50, 12, 8.56),
           ("A", 10.0, 10.00, 8, 21.79), ("B", 10.0, 10.00, 12, 9.49)]
for pol, tpd, price, mods, gain in rows_t4:
    key = (pol, tpd, price, 0.0)
    r = cs[key]
    got = (int(r["modules"]), round(float(r["profit"]), 2))
    add(f"Table II.4 {pol} {tpd}t {price}", got, (mods, gain), got == (mods, gain))

two = [r for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/contract_sizing.csv")
       if float(r.get("surplus_premium") or 0) > 0]
for r in two:
    add(f"two-rate {r['policy']} modules/gain", (int(r["modules"]), round(float(r["profit"]), 2)),
        (11, 6.06 if r["policy"] == "A" else 5.48),
        int(r["modules"]) == 11 and abs(float(r["profit"]) - (6.06 if r["policy"] == "A" else 5.48)) < 0.01)

# ---- finance --------------------------------------------------------------
fin = {(r["policy"], float(r["discount"]), float(r["electrolyser_capital_multiplier"])): r
       for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/electrolyser_finance.csv")}
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
add("min eligible share A", round(float(fin[("A", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 0), 22,
    abs(float(fin[("A", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100 - 22) < 1)
add("min eligible share B", round(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100, 0), 42,
    abs(float(fin[("B", 0.05, 1.0)]["minimum_eligible_share_at_merchant_2_50"]) * 100 - 42) < 1)
add("20% capex threshold A", round(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 3.91,
    abs(float(fin[("A", 0.05, 1.2)]["break_even_receipt_GBP_kg"]) - 3.91) < 0.01)
add("20% capex threshold B", round(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]), 2), 5.30,
    abs(float(fin[("B", 0.05, 1.2)]["break_even_receipt_GBP_kg"]) - 5.30) < 0.02)

# ---- two-hour reference ---------------------------------------------------
fp = {(r["policy"], int(r["battery_blocks"])): float(r["net_mGBP"])
      for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/reference/fixed_pair.csv")}
add("Table II.5 A 2h 0 block", round(fp[("A", 0)], 2), 13.42, abs(fp[("A", 0)] - 13.42) < 0.01)
add("Table II.5 A 2h 1 block", round(fp[("A", 1)], 2), 14.47, abs(fp[("A", 1)] - 14.47) < 0.01)
add("Table II.5 B 2h 0 block", round(fp[("B", 0)], 2), 3.78, abs(fp[("B", 0)] - 3.78) < 0.01)
add("Table II.5 B 2h 1 block", round(fp[("B", 1)], 2), 2.46, abs(fp[("B", 1)] - 2.46) < 0.01)
add("2h one-block increment A", round(fp[("A", 1)] - fp[("A", 0)], 2), 1.05,
    abs(fp[("A", 1)] - fp[("A", 0)] - 1.05) < 0.01)
add("2h one-block increment B", round(fp[("B", 1)] - fp[("B", 0)], 2), -1.32,
    abs(fp[("B", 1)] - fp[("B", 0)] + 1.32) < 0.01)

rdA = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_A_integer.json").decode("utf-8"))
rdB = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/reference/results/reference_day_B_integer.json").decode("utf-8"))
add("Table II.5 A daily 2h", round(rdA["annual_increment_mGBP"], 2), 12.46,
    abs(rdA["annual_increment_mGBP"] - 12.46) < 0.01)
add("Table II.5 B daily 2h", round(rdB["annual_increment_mGBP"], 2), 2.18,
    abs(rdB["annual_increment_mGBP"] - 2.18) < 0.01)
add("HiGHS model size", (rdA["variables"], rdA["rows"]), (13155, 24113),
    (rdA["variables"], rdA["rows"]) == (13155, 24113))

# ---- fixed block windows / Table C.2 -------------------------------------
fb = {(r["policy"], r["window"]): r for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/fixed_block_windows.csv")}
for pol, win, net, simple, four in [("A", "2020-25", 5.63, 1.63, 5.05), ("A", "2023-25", 2.15, -0.95, 1.57),
                                    ("A", "2024-25", 1.65, -0.96, 1.07), ("A", "without 2022", 3.24, -0.32, 2.66),
                                    ("B", "2020-25", 1.64, 1.50, 1.06), ("B", "2023-25", -0.99, -1.08, -1.57),
                                    ("B", "2024-25", -0.95, -1.05, -1.53), ("B", "without 2022", -0.31, -0.42, -0.89)]:
    got = (round(float(fb[(pol, win)]["net_mGBP"]), 2), round(float(fb[(pol, win)]["simple_net_mGBP"]), 2), round(float(fb[(pol, win)]["net_4pct_mGBP"]), 2))
    add(f"Table C.2 {pol} {win}", got, (net, simple, four), got == (net, simple, four))

# battery only comparison
bo = {r["policy"]: r for r in csv_rows("FinalProject/project-report-20261122-v6/evidence/battery_only/comparison.csv")}
add("battery-only net A", round(float(bo["A"]["annual_net_mGBP"]), 2), 5.70,
    abs(float(bo["A"]["annual_net_mGBP"]) - 5.70) < 0.01)
add("battery-only net B", round(float(bo["B"]["annual_net_mGBP"]), 2), 1.65,
    abs(float(bo["B"]["annual_net_mGBP"]) - 1.65) < 0.01)

# Xpress replay
sx = json.loads(z.read("FinalProject/project-report-20261122-v6/evidence/site_A_xpress.json").decode("utf-8"))
add("Xpress blocks", sx["xpress_blocks"], 551, sx["xpress_blocks"] == 551)
add("Xpress runtime", round(sx["wall_seconds"], 1), 4.3, abs(sx["wall_seconds"] - 4.3) < 0.1)
add("Xpress vs archived £/yr", round(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6, 1), 4.0,
    abs(abs(sx["annual_net_mGBP"] - sx["archived_net_mGBP"]) * 1e6 - 4.0) < 1)
add("Xpress fixed-config gap £/yr", round(sx["fixed_configuration_gap_GBP"], 2), 5.13,
    abs(sx["fixed_configuration_gap_GBP"] - 5.13) < 0.01)

# T2B pooled
tb = [r for r in csv_rows("FinalProject/tier2b-b-site-ordinal-20261122/comparison.csv") if r["window"] == "pooled"]
ta = [r for r in csv_rows("FinalProject/tier2b-a-site-grid-20261122/main/returns.csv") if r["window"] == "pooled"]
add("T2B pooled days", tb[0]["days"], "363.5", tb[0]["days"] == "363.5")
bb = [r for r in tb if r["mode"] == "end_to_end" and r["method"] == "binary_all_in"]
aa = [r for r in ta if r["bins"] == "2" and r["actions"] == "5"]
add("T2B B pooled binary_all_in", round(float(bb[0]["net_gbp"]) / 1e6, 2), 7.75,
    abs(float(bb[0]["net_gbp"]) / 1e6 - 7.75) < 0.01)
add("T2B A pooled five-action", round(float(aa[0]["net_gbp"]) / 1e6, 2), -20.68,
    abs(float(aa[0]["net_gbp"]) / 1e6 + 20.68) < 0.01)

with open(os.path.join(BASE, OUT), "w", encoding="utf-8") as f:
    json.dump(dict(source_pdf_sha256=sha, zip_sha256=zp, checks=checks), f, indent=2)
bad = [c for c in checks if not c["ok"]]
print(f"checks={len(checks)} failures={len(bad)} -> {OUT}")
for c in bad:
    print("FAIL", c["name"], c["computed"], c["stated"], c["note"])
