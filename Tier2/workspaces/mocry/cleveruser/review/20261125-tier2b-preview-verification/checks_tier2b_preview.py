# -*- coding: utf-8 -*-
"""Independent recomputation of every headline quantity in the Tier 2B preview.

Reads the published PDF and the published evidence zip directly (no extraction step):
    Tier2/workspaces/mocry/codex/technical-report/20261125-preview/
Writes checks_tier2b_preview.json next to this file and prints a summary.

Author: mocry-cleveruser. Evidence, not authority: a pass means the printed number
equals the value recomputed from the author's own shipped tables.
"""
import csv, hashlib, io, json, os, sys, zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.abspath(os.path.join(HERE, "..", "..", "..", "codex", "technical-report", "20261125-preview"))

CHECKS = []


def add(cid, groups, printed, computed, tol, note=""):
    ok = computed is not None and abs(printed - computed) <= tol
    CHECKS.append({"id": cid, "group": groups, "printed": printed,
                   "computed": None if computed is None else round(computed, 6),
                   "tol": tol, "ok": ok, "note": note})
    return ok


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    pdf = os.path.join(PREV, "tier2b-report-preview.pdf")
    zpath = os.path.join(PREV, "tier2b-report-preview-source-and-evidence.zip")
    sums = io.open(os.path.join(PREV, "SHA256SUMS.txt"), encoding="utf-8").read().split()
    for cid, printed, actual in (("artifact.pdf.sha256", sums[0], sha256(pdf)),
                                 ("artifact.zip.sha256", sums[2], sha256(zpath))):
        CHECKS.append({"id": cid, "group": "artifact", "printed": printed, "computed": actual,
                       "tol": 0, "note": "", "ok": printed == actual})

    z = zipfile.ZipFile(zpath)

    def rows(name):
        with z.open("evidence/" + name) as fh:
            return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8")))

    def f(x):
        return float(x)

    rep = rows("replays.csv")
    cap = rows("six-fold-capacity-replay.csv")
    fv = rows("forecast-value.csv")
    stress = rows("stress-weeks.csv")
    be = rows("break-even.csv")
    daily = rows("daily-operation.csv")
    audit = rows("xpress-dispatch-audit.csv")
    oracle = rows("plant-oracle.csv")

    def mean_of(rs, col, scale=1.0):
        return sum(f(r[col]) for r in rs) / len(rs) / scale

    # ---- Table III.1: mean outcomes over six windows -------------------------
    t1 = {
        ("A", "forecast_plant", 0): dict(net=11.95, cost=0.00, gross=16.49, served=89.980,
                                        unused=7962.0, re=28.7, h2=3.40),
        ("A", "reactive", 1): dict(net=11.50, cost=4.70, gross=20.74, served=89.995,
                                   unused=7919.5, re=48.5, h2=3.40),
        ("A", "selected", 1): dict(net=12.72, cost=4.70, gross=21.96, served=89.989,
                                   unused=7927.1, re=44.7, h2=3.40),
        ("A", "twelve_hour_truth", 1): dict(net=16.24, cost=4.70, gross=25.48, served=89.998,
                                            unused=7901.2, re=56.9, h2=3.40),
        ("A", "selected", 11): dict(net=15.75, cost=51.67, gross=71.96, served=90.061,
                                    unused=7625.4, re=182.1, h2=3.41),
        ("B", "direct", 0): dict(net=0.00, cost=0.00, gross=0.00, served=90.934,
                                 unused=5725.1, re=0.0, h2=0.00),
        ("B", "previous_slot", 1): dict(net=1.46, cost=4.70, gross=6.16, served=90.957,
                                        unused=5662.4, re=28.0, h2=0.00),
        ("B", "selected", 1): dict(net=1.26, cost=4.70, gross=5.96, served=90.956,
                                   unused=5663.1, re=27.8, h2=0.00),
        ("B", "truth_gate", 1): dict(net=2.13, cost=4.70, gross=6.83, served=90.961,
                                     unused=5651.4, re=32.9, h2=0.00),
        ("B", "selected", 9): dict(net=6.57, cost=42.28, gross=48.85, served=91.112,
                                   unused=5222.4, re=226.3, h2=0.00),
    }
    for key, p in t1.items():
        rs = [r for r in rep if (r["policy"], r["case"], int(r["blocks"])) == key]
        tag = "III.1 %s %s %d" % (key[0], key[1], key[2])
        n = len(rs)
        add(tag + " rows=6", "III.1", 6, n, 0)
        add(tag + " net", "III.1", p["net"], mean_of(rs, "portfolio_net_GBP", 1e6), 0.006)
        add(tag + " cost", "III.1", p["cost"], mean_of(rs, "battery_annual_equiv_cost_GBP", 1e6), 0.006)
        add(tag + " gross=net+plant+batt", "III.1", p["gross"],
            sum(f(r["portfolio_net_GBP"]) + f(r["plant_cost_GBP"]) + f(r["battery_annual_equiv_cost_GBP"])
                for r in rs) / n / 1e6, 0.006)
        add(tag + " served_pp", "III.1", p["served"],
            100 * sum(f(r["delivered_MWh"]) for r in rs) / sum(f(r["demand_MWh"]) for r in rs), 0.0005)
        add(tag + " unused", "III.1", p["unused"], mean_of(rs, "unused_MWh", 1e3), 0.05)
        add(tag + " RE", "III.1", p["re"], mean_of(rs, "renewable_capture_MWh", 1e3), 0.05)
        add(tag + " H2", "III.1", p["h2"], mean_of(rs, "hydrogen_t", 1e3), 0.005)
    # plant oracle row lives in plant-oracle.csv
    add("III.1 A plant_oracle net", "III.1", 51.40, mean_of(oracle, "portfolio_net_GBP", 1e6), 0.006)
    add("III.1 A plant_oracle rows=6", "III.1", 6, len(oracle), 0)
    add("III.1 A plant_oracle gross", "III.1", 55.94,
        mean_of(oracle, "portfolio_net_GBP", 1e6) + mean_of(oracle, "plant_cost_GBP", 1e6), 0.006)
    add("III.1 A plant_oracle oracle_gap<1", "III.1", 0.0,
        max(abs(f(r["oracle_gap_GBP"])) for r in oracle), 1.0)

    # ---- Table III.2: six windows -------------------------------------------
    grid = defaultdict(dict)
    for r in cap:
        grid[(r["policy"], int(r["blocks"]))][int(r["test_end_year"])] = f(r["net_battery_GBP"])
    add("III.2 capacity grid rows", "III.2", 552, len(cap), 0)
    add("III.2 capacity grid = 46x6x2", "III.2", 552, 46 * 6 * 2, 0)
    plant = {int(r["test_end_year"]): f(r["portfolio_net_GBP"]) for r in rep
             if r["policy"] == "A" and r["case"] == "forecast_plant" and int(r["blocks"]) == 0}
    orac = {int(r["test_end_year"]): f(r["portfolio_net_GBP"]) for r in oracle}
    printed_t2 = {
        "A plant": {2021: 14.47, 2022: 5.32, 2023: 7.74, 2024: 14.81, 2025: 13.97, 2026: 15.36},
        "A oracle": {2021: 27.57, 2022: 27.32, 2023: 54.73, 2024: 80.72, 2025: 49.71, 2026: 68.34},
        "A +1": {2021: -2.99, 2022: 6.19, 2023: 0.96, 2024: -0.19, 2025: 0.49, 2026: 0.17},
        "A +11": {2021: -34.16, 2022: 55.38, 2023: 5.94, 2024: -6.05, 2025: 1.34, 2026: 0.39},
        "B 1": {2021: -0.11, 2022: 8.81, 2023: 0.03, 2024: -1.60, 2025: -0.83, 2026: 1.27},
        "B 11": {2021: -6.08, 2022: 76.59, 2023: -6.06, 2024: -21.12, 2025: -12.04, 2026: 9.68},
    }
    for label, series in printed_t2.items():
        for y, v in series.items():
            if label == "A plant":
                comp = plant[y] / 1e6
            elif label == "A oracle":
                comp = orac[y] / 1e6
            else:
                pol, b = label.split()
                comp = grid[(pol, int(b))][y] / 1e6
            add("III.2 %s %d" % (label, y), "III.2", v, comp, 0.006)
    add("III.2 A plant mean", "III.2", 11.95, sum(plant.values()) / 6 / 1e6, 0.006)
    add("III.2 A oracle mean", "III.2", 51.40, sum(orac.values()) / 6 / 1e6, 0.006)
    for pol, b, printed in (("A", 1, 0.77), ("A", 11, 3.81), ("B", 1, 1.26), ("B", 11, 6.83)):
        add("III.2 mean %s +%d" % (pol, b), "III.2", printed,
            sum(grid[(pol, b)].values()) / 6 / 1e6, 0.006)

    # ---- capacity-selection claims -----------------------------------------
    def series(pol):
        return sorted((b, sum(d.values()) / 6 / 1e6) for (p, b), d in grid.items()
                      if p == pol and len(d) == 6)

    for pol in ("A", "B"):
        s = series(pol)
        best = max(s, key=lambda kv: kv[1])
        add("%s six-window argmax blocks" % pol, "selection", 11, best[0], 0)
        ref = sorted(((b, grid[(pol, b)].get(2026)) for b in range(46)
                      if grid.get((pol, b), {}).get(2026) is not None), key=lambda kv: kv[1])
        add("%s reference-window argmax blocks" % pol, "selection", 7 if pol == "A" else 22, ref[-1][0], 0)
        add("%s reference-window peak value" % pol, "selection", 0.69 if pol == "A" else 12.51,
            ref[-1][1] / 1e6, 0.006)
        no = {}
        for b in range(46):
            d = grid.get((pol, b), {})
            if len(d) == 6:
                no[b] = (sum(v for y, v in d.items() if y != 2022) / 5) / 1e6
        add("%s all positive counts < 0 excluding 2021/22" % pol, "selection", -1.0,
            -1.0 if max(v for b, v in no.items() if b >= 1) < 0 else 1.0, 0,
            note="(-1 = every positive count has a negative five-window mean)")
    add("A single-block portfolio mean", "selection", 12.72,
        sum(plant.values()) / 6 / 1e6 + sum(grid[("A", 1)].values()) / 6 / 1e6, 0.006)
    worst = min(plant[y] + grid[("A", 1)][y] for y in plant)
    add("A single-block lowest portfolio window", "selection", 8.70, worst / 1e6, 0.006)
    add("A single-block shock-year gain", "selection", 6.19, grid[("A", 1)][2022] / 1e6, 0.006)
    add("A single-block loss elsewhere", "selection", -1.55,
        sum(v for y, v in grid[("A", 1)].items() if y != 2022) / 1e6, 0.006)

    # ---- Table III.5: forecast value --------------------------------------
    fv_group = defaultdict(list)
    for r in fv:
        fv_group[(r["policy"], r["case"])].append(r)
    printed_t5 = {
        ("A", "weekday"): dict(price=42.70, gen=1453, load=1063, net=0.41),
        ("A", "uncorrected"): dict(price=26.20, gen=929, load=446, net=0.71),
        ("A", "quote_mix"): dict(price=25.96, gen=929, load=446, net=0.76),
        ("A", "selected"): dict(price=25.16, gen=929, load=446, net=0.77),
        ("A", "twelve_hour_truth"): dict(price=0.00, gen=0, load=0, net=4.29),
        ("B", "previous_slot"): dict(sign=94.81, net=1.46),
        ("B", "selected"): dict(sign=95.09, net=1.26),
        ("B", "truth_gate"): dict(sign=100.00, net=2.13),
    }
    for key, p in printed_t5.items():
        rs = fv_group[key]
        tag = "III.5 %s %s" % key
        add(tag + " rows=6", "III.5", 6, len(rs), 0)
        if "price" in p:
            add(tag + " price", "III.5", p["price"], mean_of(rs, "price_mae"), 0.006)
            add(tag + " gen", "III.5", p["gen"], mean_of(rs, "generation_mae"), 0.51)
            add(tag + " load", "III.5", p["load"], mean_of(rs, "demand_mae"), 0.51)
        if "sign" in p:
            add(tag + " sign_pct", "III.5", p["sign"], 100 * mean_of(rs, "accuracy"), 0.006)
        add(tag + " net", "III.5", p["net"], mean_of(rs, "net_GBP", 1e6), 0.006)
    pre = {int(r["year"]): f(r["net_GBP"]) for r in fv_group[("B", "previous_slot")]}
    sel = {int(r["year"]): f(r["net_GBP"]) for r in fv_group[("B", "selected")]}
    add("B simple rule beats classifier in all six one-block replays", "III.5", 6,
        sum(1 for y in pre if pre[y] > sel[y]), 0)
    add("B simple-minus-classifier gap", "III.5", 0.20,
        mean_of(fv_group[("B", "previous_slot")], "net_GBP", 1e6) -
        mean_of(fv_group[("B", "selected")], "net_GBP", 1e6), 0.006)

    # ---- Table III.3: stress weeks ----------------------------------------
    printed_t3 = [
        ("Low renewable output", 104, 766, 80, -28, -90),
        ("High renewable output", 547, 839, 75, -51, 10),
        ("High demand", 384, 933, 84, -8, 20),
        ("High price", 147, 637, 436, -134, 773),
    ]
    for cond, re_g, load_g, price, a_k, b_k in printed_t3:
        rs = [r for r in stress if r["condition"] == cond]
        tag = "III.3 %s" % cond
        add(tag + " rows=1", "III.3", 1, len(rs), 0)
        r = rs[0]
        add(tag + " RE", "III.3", re_g, f(r["renewable_GWh_day"]), 0.51)
        add(tag + " load", "III.3", load_g, f(r["demand_GWh_day"]), 0.51)
        add(tag + " price", "III.3", price, f(r["mean_price"]), 0.51)
        add(tag + " A_k", "III.3", a_k, f(r["A_net_kGBP"]), 0.51)
        add(tag + " B_k", "III.3", b_k, f(r["B_net_kGBP"]), 0.51)

    # ---- Table III.4: decision boundaries ---------------------------------
    for pol, sample, printed in (("A", "All six windows", 113), ("A", "Without 2021/22", 90),
                                 ("B", "All six windows", 123), ("B", "Without 2021/22", 92)):
        rs = [r for r in be if r["policy"] == pol and r["sample"] == sample][0]
        add("III.4 break-even %s %s" % (pol, sample), "III.4", printed,
            f(rs["break_even_GBP_kWh"]), 0.51)
    base_per_block = f([r for r in rep if r["policy"] == "A" and int(r["blocks"]) == 1][0]
                       ["battery_annual_equiv_cost_GBP"])
    rs = [r for r in be if r["policy"] == "A" and r["sample"] == "All six windows"][0]
    implied_kwh = f(rs["break_even_GBPm_year"]) * 1e6 / f(rs["break_even_GBP_kWh"])
    add("III.4 base cost £97/kWh implied by the same conversion", "III.4", 97,
        base_per_block / implied_kwh, 0.51)
    add("III.4 per-block annual cost £4.695m", "III.4", 4.70, base_per_block / 1e6, 0.006)
    h2 = [f(r["hydrogen_t"]) for r in rep if r["policy"] == "A" and r["case"] == "forecast_plant"
          and int(r["blocks"]) == 0]
    h2_mean = sum(h2) / len(h2)
    add("III.4 hydrogen break-even £4.28/kg", "III.4", 4.28,
        7.80 - (sum(plant.values()) / 6) / (h2_mean * 1000), 0.006)

    # ---- mechanics and internal consistency -------------------------------
    ch = sum(f(r["a_charge_MWh"]) for r in daily)
    dis = sum(f(r["a_discharge_MWh"]) for r in daily)
    chb = sum(f(r["b_charge_MWh"]) for r in daily)
    disb = sum(f(r["b_discharge_MWh"]) for r in daily)
    add("A round-trip discharge/charge = 0.90", "mechanics", 0.90, dis / ch, 0.002)
    add("B round-trip discharge/charge = 0.90", "mechanics", 0.90, disb / chb, 0.002)
    add("A cycles per block-day (informational)", "mechanics", 0.8414,
        (ch / 400.0) / len(daily), 0.0001, note="printed nowhere; cap is 1/day")
    CHECKS.append({"id": "A cycles/day <= 1", "group": "mechanics", "printed": 1.0,
                   "computed": round((ch / 400.0) / len(daily), 4), "tol": 0, "note": "",
                   "ok": (ch / 400.0) / len(daily) <= 1.0 + 1e-9})
    add("daily net sum = six-window table sum (A, 1 block)", "mechanics",
        sum(grid[("A", 1)].values()) / 1e6, sum(f(r["a_net_GBP"]) for r in daily) / 1e6, 0.006)
    add("daily rows = six 365/366-day windows", "mechanics", 2191, len(daily), 0)

    # ---- audit (informational) -------------------------------------------
    mism = sum(1 for r in audit if f(r["dp_order"]) != f(r["xpress_order"]))
    nonopt = sum(1 for r in audit if r["status"] != "6")
    add("audit sampled solutions", "audit", 192, len(audit), 0)
    print("AUDIT: %d rows, %d order mismatches, %d rows status != 6, max |gap| %.2f"
          % (len(audit), mism, nonopt, max(abs(f(r["xpress_gap_GBP"])) for r in audit)))

    passed = sum(1 for c in CHECKS if c["ok"])
    failed = [c for c in CHECKS if not c["ok"]]
    print("CHECKS: %d total, %d passed, %d failed" % (len(CHECKS), passed, len(failed)))
    for c in failed:
        print("  FAIL", c)
    by_group = defaultdict(lambda: [0, 0])
    for c in CHECKS:
        by_group[c["group"]][0] += 1
        by_group[c["group"]][1] += 1 if c["ok"] else 0
    for g in sorted(by_group):
        print("  %-10s %d/%d" % (g, by_group[g][1], by_group[g][0]))
    with io.open(os.path.join(HERE, "checks_tier2b_preview.json"), "w", encoding="utf-8") as fh:
        json.dump({"target_pdf_sha256": sums[0], "checks": CHECKS,
                   "summary": {g: {"passed": v[1], "total": v[0]} for g, v in by_group.items()},
                   "audit": {"rows": len(audit), "order_mismatches": mism,
                             "status_not_6": nonopt,
                             "max_abs_gap_gbp": max(abs(f(r["xpress_gap_GBP"])) for r in audit)}},
                  fh, indent=1)


if __name__ == "__main__":
    main()
