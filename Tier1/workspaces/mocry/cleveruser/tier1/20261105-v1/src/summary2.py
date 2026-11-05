import json, pathlib
R = json.loads((pathlib.Path(__file__).resolve().parents[1] / "results/results.json").read_text(encoding="utf-8"))
print("thresholds:", json.dumps(R["battery_threshold"], indent=1))
print("h2:", json.dumps(R["h2_threshold"], indent=1))
print("robustness 2024:", [c for c in R["robustness"] if "2024" in c["case"]])
print("frontier:")
for r in R["supply_frontier"]:
    print(" ", r)
print("low FOM sweep:")
for r in R["battery_sweep"]:
    if r["fom"] == "table":
        print(" ", r)
print("primary sweep A:")
for r in R["battery_sweep"]:
    if r["fom"] == "primary" and r["policy"] == "A":
        print(" ", r["cost_GBP2020_MWh"], r["n_units"], r["increment_mGBP"])
