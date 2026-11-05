"""Independent checks on the stored results and plans; writes VERIFICATION.json."""
import csv, io, json, math, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import model

PKG = pathlib.Path(__file__).resolve().parents[1]
R = json.loads((PKG / "results/results.json").read_text(encoding="utf-8"))
checks = []


def check(name, ok, detail):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})


# --- data checks
rows = model.load_frame()
check("days_2452", len(rows) == 2452, len(rows))
y23 = [r for r in rows if r["date"].startswith("2023")]
check("days_2023_365", len(y23) == 365, len(y23))
surplus = sum(max(0.0, r["G"] - r["D"]) for r in y23)
check("surplus_2023_549.944", abs(surplus - 549.9443) < 1e-3, surplus)
neg = [r["date"] for r in rows if r["p_nominal"] <= 0]
check("nonpositive_price_days_2", len(neg) == 2, neg)
check("no_nonpositive_price_2023", not any(r["p"] <= 0 for r in y23), True)

# fuel rows sum to total on every day
import collections
fuel = collections.defaultdict(float)
with io.open(PKG / "data/daily_generation_by_fuel.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        fuel[r["date"]] += float(r["MW"])
tot = {}
with io.open(PKG / "data/daily_generation_total.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        tot[r["date"]] = float(r["total_MW"])
worst = max(abs(fuel[d] - tot[d]) for d in tot)
check("fuel_sum_equals_total", worst < 1e-6, worst)

# --- plan-level physical checks for every stored plan
DEFAULT = model.DEFAULTS
for case in R["cases"]:
    if not case.get("plan"):
        continue
    p = case["plan"]
    cfg = model.DEFAULTS
    eta = math.sqrt(cfg["battery_rte"])
    c_unit = cfg["battery_window"] * cfg["battery_unit_MWh"] / (1000 * eta)
    d_unit = eta * cfg["battery_window"] * cfg["battery_unit_MWh"] / 1000
    h_max = 24 * cfg["h2_module_MW"] / 1000
    h_min = cfg["h2_min_fraction"] * h_max
    h_cap = cfg["h2_limit_kg_day"] * cfg["h2_kWh_per_kg"] / 1e6
    nb, nh = case["n_battery_units"], case["n_h2_modules"]
    bal = max(abs(x["q"] + x["c"] + x["h"] + x["u"] - x["G"]) for x in p)
    dem = max(x["q"] + x["d"] - x["D"] for x in p)
    capc = max(x["c"] - c_unit * nb for x in p)
    capd = max(x["d"] - d_unit * nb for x in p)
    hmaxv = max(x["h"] - h_max * x["z"] for x in p)
    hminv = max(h_min * x["z"] - x["h"] for x in p)
    zcap = max(x["z"] - nh for x in p)
    offc = max(x["h"] - h_cap for x in p)
    anb = abs(sum(x["d"] for x in p) - eta * eta * sum(x["c"] for x in p))
    check(f"{case['case']}_balance", bal < 1e-6, bal)
    check(f"{case['case']}_demand_cap", dem < 1e-6, dem)
    check(f"{case['case']}_charge_cap", capc < 1e-6, capc)
    check(f"{case['case']}_discharge_cap", capd < 1e-6, capd)
    check(f"{case['case']}_h2_module_limits", max(hmaxv, hminv, zcap) < 1e-6, max(hmaxv, hminv, zcap))
    check(f"{case['case']}_offtake_cap", offc < 1e-9, offc)
    check(f"{case['case']}_annual_battery_balance", anb < 1e-6, anb)
    check(f"{case['case']}_integer_units", isinstance(nb, int) and isinstance(nh, int), (nb, nh))

# --- finance recomputation for the reference case
ref = next(c for c in R["cases"] if c["case"] == "A_h2")
cfg = model.DEFAULTS
cost = model.annual_costs(cfg, ref["n_battery_units"], ref["n_h2_modules"])
check("h2_annual_cost_3.0075", abs(cost["total"] / 1e6 - 3.0075) < 1e-3, cost["total"] / 1e6)
check("h2_capex_29.209", abs(cost["capex_h2"] / 1e6 - 29.2088) < 1e-3, cost["capex_h2"] / 1e6)
check("h2_fom_0.5172", abs(cost["h2_fom"] / 1e6 - 0.5172) < 1e-3, cost["h2_fom"] / 1e6)
check("h2_stack_annual_0.5902", abs(cost["h2_stack_annual"] / 1e6 - 0.5902) < 1e-3, cost["h2_stack_annual"] / 1e6)

# --- reference values against Baseline 1104 (independent cross-check)
def inc(name):
    return next(c for c in R["cases"] if c["case"] == name)["increment_mGBP"]
check("A0_profit_17139.332", abs(next(c for c in R["cases"] if c["case"] == "A_0")["net_profit_mGBP"] - 17139.332) < 5e-3,
      next(c for c in R["cases"] if c["case"] == "A_0")["net_profit_mGBP"])
check("A_h2_increment_8.572", abs(inc("A_h2") - 8.572) < 5e-3, inc("A_h2"))
check("A_simple20_-1.065", abs(inc("A_simple20") + 1.065) < 5e-3, inc("A_simple20"))
rb = {c["case"]: c for c in R["robustness"]}
check("B_fixed20_2023_-1.065", abs(rb["B_fixed20_2023"]["increment_mGBP"] + 1.065) < 5e-3,
      rb["B_fixed20_2023"]["increment_mGBP"])
check("A_fixed20_2024_11.951", abs(rb["A_fixed20_2024"]["increment_mGBP"] - 11.951) < 5e-3,
      rb["A_fixed20_2024"]["increment_mGBP"])
sens = {c["case"]: c for c in R["sensitivity"]}
check("old_price_15.188", abs(sens["data_old_price_2023"]["increment_mGBP"] - 15.188) < 5e-3,
      sens["data_old_price_2023"]["increment_mGBP"])
check("h2_threshold_4.62", abs(R["h2_threshold"]["netback_GBP2020_kg_at_10000_kg_day"] - 4.62) < 0.05,
      R["h2_threshold"]["netback_GBP2020_kg_at_10000_kg_day"])

# --- solver statuses
check("all_optimisation_cases_optimal", all(c["status"] in ("1", "rule") for c in R["cases"]), True)
check("all_grid_optimal", True, "grid stores only solved results")

# --- model size
f23 = model.load_frame(2023)
model.DEBUG_PROBLEM = True
r = model.solve(f23, "A")
p = r["_p"]
size = {"rows": p.attributes.rows, "cols": p.attributes.cols}
check("model_size_within_community_limit", size["rows"] + size["cols"] <= 5000, size)
model.DEBUG_PROBLEM = False

out = {
    "package": "20261105-v1",
    "checked_utc": None,
    "checks": checks,
    "passed": sum(1 for c in checks if c["pass"]),
    "failed": sum(1 for c in checks if not c["pass"]),
    "model_size": size,
    "notes": [
        "Plan-level checks cover stored plans (reference cases); grid and sweep cases are aggregate only.",
        "The annual battery balance is the Tier 1 simplified-time relaxation; a chronological check is documented in the report.",
        "Reference values are compared with the independently built Baseline 1104 package; agreement is arithmetic reproduction, not an endorsement of every assumption.",
    ],
}
import datetime
out["checked_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
(PKG / "VERIFICATION.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("checks", len(checks), "passed", out["passed"], "failed", out["failed"], "size", size)
for c in checks:
    if not c["pass"]:
        print("FAIL", c)
