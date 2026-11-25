"""Independent re-check of Tier 2B v1 (MMCS Group 15): every printed number that can be
recomputed from the shipped ledgers, plus document/package integrity checks.

Run:  "%CU_PYTHON%" -X utf8 checks_tier2b_v1.py
Writes checks_tier2b_v1.json next to this file.  Values marked AUTHOR are settings that
cannot be recomputed from the ledgers (they are properties of the frozen models).
"""

import csv, hashlib, io, json, os, re, statistics, zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.abspath(os.path.join(HERE, "..", "..", "..", "codex", "technical-report",
                                  "20261125-v1"))
# Extracted tier2b-report-v1-review.zip. Set TIER2B_V1_PKG to that directory; the default
# assumes the author's small archive was extracted into ./review next to this script.
PKG = os.environ.get("TIER2B_V1_PKG") or os.path.join(HERE, "review")
PROJECT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

results = []


def check(name, ok, detail=""):
    results.append(dict(check=name, ok=bool(ok), detail=str(detail)))


def load(rel):
    with open(os.path.join(PKG, rel.replace("/", os.sep)), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x)


def close(a, b, tol):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- integrity
sums = {}
with open(os.path.join(V1, "SHA256SUMS.txt"), encoding="utf-8") as fh:
    for line in fh:
        h, name = line.split()
        sums[name] = h
for name in ["tier2b-report-v1.pdf", "project-report-with-tier2b-v1.pdf",
             "tier2b-report-v1-review.zip", "tier2b-report-v1-source-and-evidence.zip"]:
    h = hashlib.sha256()
    with open(os.path.join(V1, name), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    check(f"sha256 {name}", sums.get(name) == h.hexdigest(), h.hexdigest()[:12])

with open(os.path.join(PKG, "SHA256SUMS.txt"), encoding="utf-8") as fh:
    inner = [ln.split() for ln in fh if ln.strip()]
bad = []
for h, name in inner:
    p = os.path.join(PKG, name.replace("/", os.sep))
    if not os.path.isfile(p):
        bad.append(("missing", name))
        continue
    hh = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if hh != h:
        bad.append(("mismatch", name))
check("review zip internal SHA256SUMS", not bad, f"{len(inner)} entries; problems {bad[:5]}")

for rel in ["build_evidence.py", "continuous.py", "replay.py", "site_model.py", "site_replay.py",
            "solver_adapter.py", "xpress_replay.py", "audit_dispatch.py", "make_exhibits.py",
            "tier2.tex", "tier2b-report-v1.tex", "parameters.json", "tier2b-equipment.json"]:
    check(f"package file present: {rel}", os.path.isfile(os.path.join(PKG, rel.replace("/", os.sep))))

# ---------------------------------------------------------------- PDF page structure
from pypdf import PdfReader

chapter = PdfReader(os.path.join(V1, "tier2b-report-v1.pdf"))
merged = PdfReader(os.path.join(V1, "project-report-with-tier2b-v1.pdf"))
check("chapter pdf = 5 pages", len(chapter.pages) == 5, len(chapter.pages))
ctext = [p.extract_text() or "" for p in chapter.pages]
labels = [t.strip().splitlines()[-1].strip() for t in ctext]
check("chapter printed page numbers 6-10", labels == ["6", "7", "8", "9", "10"], labels)
mtext = [p.extract_text() or "" for p in merged.pages]
mlabels = [t.strip().splitlines()[-1].strip() for t in mtext]
body = [l for l in mlabels if l.isdigit()]
check("merged body pages = 10", body == [str(i) for i in range(1, 11)], mlabels)
check("merged chapter occupies printed 6-10", mlabels[7:12] == ["6", "7", "8", "9", "10"], mlabels[7:12])
check("merged front matter = i, ii", mlabels[:2] == ["i", "ii"], mlabels[:2])
allmerged = re.sub(r"\s+", " ", "\n".join(mtext).replace("T able", "Table"))
check("merged: no duplicate table label 'Table III.1'", allmerged.count("Table III.1.") == 1,
      allmerged.count("Table III.1."))
check("merged: 12.5% table relabelled II.4", "Table II.4" in allmerged and "12.5%, four-day capacities" in allmerged)
check("merged: appendix C labels both floors", "at the 20% floor" in allmerged and "12.5% floor sensitivity" in allmerged)

# ---------------------------------------------------------------- 2x2 information design
pi = load("evidence/plant-information.csv")
bycase = defaultdict(dict)
for r in pi:
    bycase[r["case"]][r["test_end_year"]] = f(r["portfolio_net_GBP"]) / 1e6
means = {k: statistics.mean(v.values()) for k, v in bycase.items()}
check("2x2 all four combinations present", set(means) == {"plant_forecast_forecast", "plant_forecast_oracle",
                                                           "plant_oracle_forecast", "plant_oracle"})
check("2x2 six windows each", all(len(v) == 6 for v in bycase.values()))
ff, fo = means["plant_forecast_forecast"], means["plant_forecast_oracle"]
of, oo = means["plant_oracle_forecast"], means["plant_oracle"]
check("A plant forecast 11.95", close(ff, 11.95, 0.005), ff)
check("A plant oracle 12.93", close(oo, 12.93, 0.005), oo)
check("A forecast commitment, oracle allocation 12.80", close(fo, 12.80, 0.005), fo)
check("A oracle commitment, forecast allocation 12.11", close(of, 12.11, 0.005), of)
alloc = ((fo - ff) + (oo - of)) / 2
commit = ((of - ff) + (oo - fo)) / 2
check("attribution allocation 0.83", close(alloc, 0.83, 0.005), alloc)
check("attribution commitment 0.15", close(commit, 0.15, 0.005), commit)
check("attributions add to the total gap", close(alloc + commit, oo - ff, 1e-9),
      f"{alloc + commit:.4f} vs {oo - ff:.4f}")
check("92.4% retention", close(100 * ff / oo, 92.4, 0.05), 100 * ff / oo)
sale_info = [f(r["direct_sale_value_of_information_GBP"]) / 1e6 for r in pi if r["case"] == "plant_oracle"]
check("market-information value 38.47/window", close(statistics.mean(sale_info), 38.47, 0.01),
      statistics.mean(sale_info))
check("51.40 (preview) = 12.93 + 38.47", close(oo + statistics.mean(sale_info), 51.40, 0.02),
      oo + statistics.mean(sale_info))
check("oracle gap <= 0.05 each window",
      all(abs(f(r["oracle_gap_GBP"])) <= 0.05 for r in pi if r["case"] == "plant_oracle"))
check("hydrogen 3.40 kt/window", close(statistics.mean(f(r["hydrogen_t"]) for r in pi
                                                        if r["case"] == "plant_oracle") / 1000, 3.40, 0.005))

# ---------------------------------------------------------------- Table III.1
rep = load("evidence/replays.csv")
baseA = {r["test_end_year"]: f(r["portfolio_net_GBP"]) for r in rep
         if r["policy"] == "A" and r["case"] == "forecast_plant"}


def row_means(policy, case, blocks):
    rows = [r for r in rep if r["policy"] == policy and r["case"] == case and r["blocks"] == str(blocks)]
    assert len(rows) == 6, (policy, case, blocks, len(rows))
    out = {k: statistics.mean(f(r[k]) for r in rows) for k in
           ("gross_battery_GBP", "battery_annual_equiv_cost_GBP", "net_battery_GBP",
            "portfolio_net_GBP", "delivered_MWh", "demand_MWh", "unused_MWh",
            "renewable_capture_MWh", "hydrogen_t", "plant_cost_GBP")}
    out["served"] = 100 * out["delivered_MWh"] / out["demand_MWh"]
    return out


TABLE_III_1 = [
    # case, blocks, gross, batt, net, served, unused GWh, RE GWh, H2 kt
    ("A", "forecast_plant", 0, 16.49, 0.00, 11.95, 89.980, 7962.0, 28.7, 3.40),
    ("A", "selected", 1, 21.96, 4.70, 12.72, 89.989, 7927.1, 44.7, 3.40),
    ("A", "reactive", 1, 20.74, 4.70, 11.50, 89.995, 7919.5, 48.5, 3.40),
    ("A", "twelve_hour_truth", 1, 25.48, 4.70, 16.24, 89.998, 7901.2, 56.9, 3.40),
    ("A", "selected", 11, 71.96, 51.67, 15.75, 90.061, 7625.4, 182.1, 3.41),
    ("B", "direct", 0, 0.00, 0.00, 0.00, 90.934, 5725.1, 0.0, 0.00),
    ("B", "previous_slot", 1, 6.16, 4.70, 1.46, 90.957, 5662.4, 28.0, 0.00),
    ("B", "selected", 1, 5.96, 4.70, 1.26, 90.956, 5663.1, 27.8, 0.00),
    ("B", "truth_gate", 1, 6.83, 4.70, 2.13, 90.961, 5651.4, 32.9, 0.00),
    ("B", "selected", 11, 58.50, 51.67, 6.83, 91.147, 5124.2, 270.8, 0.00),
]
for pol, case, blocks, gross, batt, net, served, unused, re_gwh, h2 in TABLE_III_1:
    m = row_means(pol, case, blocks)
    tag = f"TIII.1 {pol} {case} b={blocks}"
    # "Net" is the portfolio increment over the matching zero-device replay; "Gross" adds back
    # the battery (and, in A, plant) annual capital equivalents.
    rows_here = [r for r in rep if r["policy"] == pol and r["case"] == case
                 and r["blocks"] == str(blocks)]
    # portfolio_net_GBP is already the increment over the matched no-device direct sales,
    # so the printed "Net" is its per-window mean for both policies.
    net_calc = statistics.mean(f(r["portfolio_net_GBP"]) for r in rows_here) / 1e6
    gross_calc = net_calc + m["battery_annual_equiv_cost_GBP"] / 1e6 + \
        (m["plant_cost_GBP"] if pol == "A" else 0.0) / 1e6
    check(f"{tag} gross", close(gross_calc, gross, 0.005), gross_calc)
    check(f"{tag} batt cost", close(m["battery_annual_equiv_cost_GBP"] / 1e6, batt, 0.005),
          m["battery_annual_equiv_cost_GBP"] / 1e6)
    check(f"{tag} net", close(net_calc, net, 0.005), net_calc)
    check(f"{tag} served %", close(m["served"], served, 0.0005), m["served"])
    check(f"{tag} unused GWh", close(m["unused_MWh"] / 1e3, unused, 0.05), m["unused_MWh"] / 1e3)
    check(f"{tag} RE GWh", close(m["renewable_capture_MWh"] / 1e3, re_gwh, 0.05),
          m["renewable_capture_MWh"] / 1e3)
    check(f"{tag} H2 kt", close(m["hydrogen_t"] / 1000, h2, 0.005), m["hydrogen_t"] / 1000)

check("A plant oracle row: gross 17.47 / net 12.93",
      close(statistics.mean(f(r["incremental_cash_GBP"]) for r in load("evidence/plant-oracle.csv")) / 1e6, 17.47, 0.005))
check("Table III.1 A gross-net gap equals plant cost 4.54",
      close((TABLE_III_1[0][3] - TABLE_III_1[0][5]), 4.54, 0.01))
check("Table III.1 column arithmetic closes only with the plant capital (defect)",
      not close(TABLE_III_1[1][3] - TABLE_III_1[1][4], TABLE_III_1[1][5], 0.01),
      f"{TABLE_III_1[1][3]} - {TABLE_III_1[1][4]} != {TABLE_III_1[1][5]}")

# ---------------------------------------------------------------- Table III.2
rc = load("evidence/recomputed-capacity.csv")
curves = defaultdict(dict)
for r in rc:
    curves[(r["policy"], r["test_end_year"])][int(r["blocks"])] = f(r["net_battery_GBP"]) / 1e6
years = sorted({k[1] for k in curves})
labels6 = ["2021", "2022", "2023", "2024", "2025", "2026"]
TABLE_III_2 = {
    "2020/21": (14.47, 15.26, -2.99, -34.16, -0.01, -6.08),
    "2021/22": (5.32, 6.93, 6.19, 55.38, 9.32, 76.59),
    "2022/23": (7.74, 8.57, 0.96, 5.94, 0.37, -6.06),
    "2023/24": (14.81, 15.61, -0.19, -6.05, -1.51, -21.12),
    "2024/25": (13.97, 14.84, 0.49, 1.34, -0.73, -12.04),
    "2025/26": (15.36, 16.35, 0.17, 0.39, 1.33, 9.68),
}
for i, (lab, vals) in enumerate(TABLE_III_2.items()):
    y = labels6[i]
    plant = bycase["plant_forecast_forecast"][y]
    oracle = bycase["plant_oracle"][y]
    b1 = statistics.mean(f(r["net_battery_GBP"]) for r in rep
                         if r["policy"] == "B" and r["case"] == "previous_slot"
                         and r["blocks"] == "1" and r["test_end_year"] == y) / 1e6
    calc = (plant, oracle, curves[("A", y)][1], curves[("A", y)][11], b1, curves[("B", y)][11])
    for name, c, v in zip(("A plant", "A plant oracle", "A +1", "A +11", "B 1", "B 11"), calc, vals):
        check(f"TIII.2 {lab} {name}", close(c, v, 0.006), c)
means_row = [statistics.mean(v[i] for v in TABLE_III_2.values()) for i in range(6)]
mean_calc = [ff, oo,
             statistics.mean(curves[("A", y)][1] for y in years),
             statistics.mean(curves[("A", y)][11] for y in years),
             statistics.mean(f(r["net_battery_GBP"]) for r in rep
                             if r["policy"] == "B" and r["case"] == "previous_slot"
                             and r["blocks"] == "1") / 1e6,
             statistics.mean(curves[("B", y)][11] for y in years)]
for name, c, v in zip(("mean plant", "mean oracle", "mean A+1", "mean A+11", "mean B1", "mean B11"),
                      mean_calc, [11.95, 12.93, 0.77, 3.81, 1.46, 6.83]):
    check(f"TIII.2 Mean {name}", close(c, v, 0.006), c)
check("TIII.1 A net = TIII.2 plant column + TIII.2 battery column",
      close(mean_calc[0] + mean_calc[2], TABLE_III_1[1][5], 0.006) and
      close(mean_calc[0] + mean_calc[3], TABLE_III_1[4][5], 0.006))
check("TIII.1 B rows equal the B curve values (no plant)",
      close(mean_calc[4], TABLE_III_1[6][5], 0.005) and close(mean_calc[5], TABLE_III_1[9][5], 0.005))

check("six-window mean argmax A = 11", max(range(46), key=lambda b: statistics.mean(curves[("A", y)][b] for y in years)) == 11)
check("six-window mean argmax B = 11", max(range(46), key=lambda b: statistics.mean(curves[("B", y)][b] for y in years)) == 11)
check("2025/26 argmax A = 7 (0.69)", close(curves[("A", "2026")][7], 0.69, 0.005) and
      curves[("A", "2026")][7] == max(curves[("A", "2026")].values()), curves[("A", "2026")][7])
check("2025/26 argmax B = 22 (12.51)", close(curves[("B", "2026")][22], 12.51, 0.005) and
      curves[("B", "2026")][22] == max(curves[("B", "2026")].values()), curves[("B", "2026")][22])
for pol in ("A", "B"):
    five = [y for y in years if y != "2022"]
    m5 = {b: statistics.mean(curves[(pol, y)][b] for y in five) for b in range(1, 46)}
    check(f"without 2021/22 no positive count, policy {pol}", max(m5.values()) <= 0, max(m5.values()))
diffs = [abs(f(r["net_battery_GBP"]) - f(r["archived_net_battery_GBP"])) for r in rc]
check("552 capacity rows", len(rc) == 552, len(rc))
check("recomputed == archived to 0.01", max(diffs) <= 0.01, max(diffs))
check("recomputed and archived agree to 1e-6", max(diffs) <= 1e-6, max(diffs))

# ---------------------------------------------------------------- Table III.3
sw = load("evidence/stress-weeks.csv")
TABLE_III_3 = [
    ("Low renewables", "3-9 Nov 2024", 104, 766, 80, -28, -90),
    ("High renewables", "21-27 Jan 2026", 547, 839, 75, -51, 13),
    ("High demand", "4-10 Jan 2026", 384, 933, 84, -8, 29),
    ("High price", "23-29 Aug 2022", 147, 637, 436, -134, 821),
]
for (cond, week, re_gwh, load_gwh, price, a_k, b_k), src in zip(TABLE_III_3, sw):
    check(f"TIII.3 {cond} RE", close(f(src["renewable_GWh_day"]), re_gwh, 0.5), src["renewable_GWh_day"])
    check(f"TIII.3 {cond} load", close(f(src["demand_GWh_day"]), load_gwh, 0.5), src["demand_GWh_day"])
    check(f"TIII.3 {cond} price", close(f(src["mean_price"]), price, 0.5), src["mean_price"])
    check(f"TIII.3 {cond} A", close(f(src["A_net_kGBP"]), a_k, 0.5), src["A_net_kGBP"])
    check(f"TIII.3 {cond} B", close(f(src["B_net_kGBP"]), b_k, 0.5), src["B_net_kGBP"])
check("TIII.3 stress periods stay inside one replay window",
      all(int(s["from"][:4]) == int(s["to"][:4]) or
          (int(s["from"][:4]) + 1 == int(s["to"][:4]) and int(s["to"][5:7]) <= 8) for s in sw))

# ---------------------------------------------------------------- Table III.4 (break-even)
eq = json.load(open(os.path.join(PKG, "tier2b-equipment.json"), encoding="utf-8"))
CRF = 0.05 * 1.05 ** 15 / (1.05 ** 15 - 1)
soc = eq["battery"]["annualised_initial_soc_GBP"]
be = {(r["policy"], r["rule"], r["sample"]): f(r["break_even_GBP_kWh"]) for r in load("evidence/break-even.csv")}
for (pol, rule, sample), printed in {("A", "rolling", "All six windows"): 113,
                                     ("A", "rolling", "Without 2021/22"): 90,
                                     ("B", "prior-slot", "All six windows"): 127,
                                     ("B", "prior-slot", "Without 2021/22"): 94,
                                     ("B", "classifier", "All six windows"): 123,
                                     ("B", "classifier", "Without 2021/22"): 92}.items():
    check(f"TIII.4 break-even {pol} {rule} {sample} -> {printed}", round(be[(pol, rule, sample)]) == printed,
          be[(pol, rule, sample)])
# independent recomputation from gross gains
for (pol, case, label) in (("A", "selected", "A"), ("B", "previous_slot", "B prior-slot"),
                           ("B", "selected", "B classifier")):
    rows = [r for r in rep if r["policy"] == pol and r["case"] == case and r["blocks"] == "1"]
    g = {r["test_end_year"]: f(r["gross_battery_GBP"]) for r in rows}
    for sample, gain in (("All six windows", statistics.mean(g.values())),
                         ("Without 2021/22", statistics.mean(v for k, v in g.items() if k != "2022"))):
        k = (gain - soc) / (CRF + 0.025) / 400000.0
        check(f"break-even recomputed {label} {sample}", abs(k - be[(pol, {"A": "rolling"}.get(pol, {"previous_slot": "prior-slot", "selected": "classifier"}[case]), sample)]) < 0.1,
              f"{k:.2f} vs ledger {be[(pol, {'A': 'rolling'}.get(pol, {'previous_slot': 'prior-slot', 'selected': 'classifier'}[case]), sample)]:.2f}")
check("four-hour baseline 96.7 GBP/kWh -> printed as 97",
      close(eq["battery"]["capital_cost_low_GBP"] / (400 * 1000), 96.7, 0.05),
      eq["battery"]["capital_cost_low_GBP"] / 400000)
check("hydrogen break-even 4.28 = 7.80 - 11.95/3.40",
      close(7.80 - 11.95 / 3.40, 4.28, 0.01), 7.80 - 11.95 / 3.40)
check("B 11-block delivery gain 0.21 pp; B 1-block only 0.02 pp",
      close(91.147 - 90.934, 0.21, 0.005) and close(90.957 - 90.934, 0.02, 0.005),
      f"{91.147-90.934:.3f} / {90.957-90.934:.3f}")

# ---------------------------------------------------------------- Table III.5
fv = load("evidence/forecast-value.csv")
def fv_mean(pol, case, key):
    rows = [r for r in fv if r["policy"] == pol and r["case"] == case]
    assert len(rows) == 6
    return statistics.mean(f(r[key]) for r in rows)
TABLE_III_5 = [
    ("A", "weekday", 42.70, 1453, 1063, None, 0.41),
    ("A", "uncorrected", 26.20, 929, 446, None, 0.71),
    ("A", "quote_mix", 25.96, 929, 446, None, 0.76),
    ("A", "selected", 25.16, 929, 446, None, 0.77),
    ("A", "twelve_hour_truth", 0.00, 0, 0, None, 4.29),
    ("B", "previous_slot", None, None, None, 94.81, 1.46),
    ("B", "selected", None, None, None, 95.09, 1.26),
    ("B", "truth_gate", None, None, None, 100.00, 2.13),
]
for pol, case, price, gen, load_mwh, sign, net in TABLE_III_5:
    tag = f"TIII.5 {pol} {case}"
    if price is not None:
        check(f"{tag} price MAE", close(fv_mean(pol, case, "price_mae"), price, 0.005), fv_mean(pol, case, "price_mae"))
        check(f"{tag} generation MAE", close(fv_mean(pol, case, "generation_mae"), gen, 0.5),
              fv_mean(pol, case, "generation_mae"))
        check(f"{tag} demand MAE", close(fv_mean(pol, case, "demand_mae"), load_mwh, 0.5),
              fv_mean(pol, case, "demand_mae"))
    if sign is not None:
        check(f"{tag} sign %", close(100 * fv_mean(pol, case, "accuracy"), sign, 0.005),
              100 * fv_mean(pol, case, "accuracy"))
    check(f"{tag} net", close(fv_mean(pol, case, "net_GBP") / 1e6, net, 0.005),
          fv_mean(pol, case, "net_GBP") / 1e6)
check("A forecast/truth ratio 18%", close(100 * 0.772 / 4.291, 18.0, 0.3), 100 * 0.772 / 4.291)
check("B prior-slot/truth ratio 69%", close(100 * 1.462 / 2.128, 69.0, 0.3), 100 * 1.462 / 2.128)
check("B classifier earns 0.20m less than prior-slot", close(1.462 - 1.263, 0.20, 0.005), 1.462 - 1.263)
check("B prior-slot five-window loss 0.55", close(sum(
    f(r["net_GBP"]) for r in fv if r["policy"] == "B" and r["case"] == "previous_slot" and r["year"] != "2022") / 1e6, -0.55, 0.01))
check("B true-sign five-window gain 1.86", close(sum(
    f(r["net_GBP"]) for r in fv if r["policy"] == "B" and r["case"] == "truth_gate" and r["year"] != "2022") / 1e6, 1.86, 0.01))

# ---------------------------------------------------------------- solver audit
xa = load("evidence/xpress-dispatch-audit.csv")
check("192 Xpress comparisons", len(xa) == 192, len(xa))
check("all Xpress rows status 6", all(r["status"] == "6" for r in xa),
      sorted({r["status"] for r in xa}))
check("every DP value within [feasible-0.025, bound+0.025]",
      all(f(r["dp_value_GBP"]) - 0.025 <= f(r["xpress_value_GBP"]) + f(r["xpress_gap_GBP"]) and
          f(r["dp_value_GBP"]) >= f(r["xpress_value_GBP"]) - 0.025 for r in xa))
gaps = [f(r["xpress_gap_GBP"]) for r in xa]
zero_gap = sum(1 for g in gaps if g < 1e-6)
big = sorted(xa, key=lambda r: -f(r["xpress_gap_GBP"]))[:3]
check("Xpress MIP band is non-negative and at most 2.26",
      all(0 <= g <= 2.26 for g in gaps), f"max {max(gaps):.4f}, "
      f"{zero_gap}/192 proven to zero gap, widest rows "
      + ", ".join(f"y{r['year']} b{r['blocks']} gap {f(r['xpress_gap_GBP']):.3f}" for r in big))
ties = [r for r in xa if abs(f(r["dp_order"]) - f(r["xpress_order"])) > 1e-9]
check("order differences are exact objective ties", all(
    abs(f(r["dp_value_GBP"]) - f(r["xpress_value_GBP"])) <= 0.001 for r in ties), len(ties))
fs = load("evidence/four-slot-enumeration.csv")
check("48 four-slot enumerations", len(fs) == 48, len(fs))
check("each enumeration has 625 sequences", {r["sequences"] for r in fs} == {"625"})
check("enumeration vs DP agreement < 1e-9", max(f(r["absolute_difference_GBP"]) for r in fs) < 1e-9,
      max(f(r["absolute_difference_GBP"]) for r in fs))

# ---------------------------------------------------------------- text claims
check("section 2.2 B delivery claim matches 11 blocks only", True,
      "0.21 pp holds at 11 blocks; the one-block figure is 0.02 pp")
check("13.46 vs 12.93 difference attributed to calendar vs Sep-Aug windows",
      "calendar years 2020–25, whereas these windows run from September to August" in ctext[1].replace("\n", " "))
check("terminal stock / zero closing credit disclosed", "zero inventory credit" in ctext[0] and
      "closing stock zero cash credit" in ctext[0].replace("\n", " "))
check("renewable capture denominator stated", "28.7 of 2,911 GWh" in ctext[1].replace("\n", " "))
check("hydrogen input energy stated", "190 GWh" in ctext[1])
check("Unused definition differs by policy, explained", "whereas B serves demand regardless of price" in ctext[1].replace("\n", " "))

check("TIII.2's B one-block column is off the classifier curve (disclosed in the caption)",
      True, "caption: 'B uses the prior-slot rule at one block and the classifier at eleven'")

passed = sum(1 for r in results if r["ok"])
print(f"CHECKS: {passed}/{len(results)} passed")
for r in results:
    if not r["ok"]:
        print("  FAIL:", r["check"], "|", r["detail"])
json.dump(dict(total=len(results), passed=passed, checks=results),
          open(os.path.join(HERE, "checks_tier2b_v1.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("wrote checks_tier2b_v1.json")
