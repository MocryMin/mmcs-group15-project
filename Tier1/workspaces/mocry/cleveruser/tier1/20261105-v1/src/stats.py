import csv, io, json, math, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import model

PKG = pathlib.Path(__file__).resolve().parent.parent
rows = model.load_frame(2023)
G = sum(r["G"] for r in rows); D = sum(r["D"] for r in rows)
S = sum(max(0.0, r["G"] - r["D"]) for r in rows)
R = sum(r["renewable"] for r in rows)
days = [r for r in rows if r["G"] > r["D"]]
surplus_sorted = sorted((r["G"] - r["D"] for r in days), reverse=True)
print("G", round(G, 1), "D", round(D, 1), "deficit", round(D - G, 1), "surplus", round(S, 1),
      "coverage", round(G / D, 6))
print("renewable share", round(R / G, 4), "other share", round(1 - R / G, 4))
print("surplus days", len(days), "max surplus", round(surplus_sorted[0], 2), "median surplus", round(surplus_sorted[len(surplus_sorted)//2], 2))
p = sorted(r["p"] for r in rows)
print("price min/median/mean/max", round(p[0], 2), round(p[182], 2), round(sum(p)/len(p), 2), round(p[-1], 2))
# renewable share on surplus days
Rd = sum(r["renewable"] for r in days); Gd = sum(r["G"] for r in days)
print("surplus-day renewable share", round(Rd / Gd, 4))
# timing
f = rows
t0 = time.perf_counter()
r = model.solve(f, "A", fixed=(0, 1))
t1 = time.perf_counter()
print("solve seconds fixed20", round(t1 - t0, 4))
t0 = time.perf_counter()
r = model.solve(f, "A")
t1 = time.perf_counter()
print("solve seconds free", round(t1 - t0, 4), "modules", r["n_h2_modules"])
# value per battery unit at zero capex, FOM 0
cfg = dict(model.DEFAULTS, battery_cost_GBP2020_MWh=0.0, battery_FOM_GBP2020_MWyr=0.0, max_h2_modules=0)
base = model.base_profit(f, "A")
for fix in [(50, 0), (100, 0), (200, 0)]:
    rr = model.solve(f, "A", cfg, fixed=fix)
    print("battery units", fix[0], "value mGBP", round(rr["net_profit_GBP2020_year"] - base, 3),
          "per unit kGBP", round((rr["net_profit_GBP2020_year"] - base) * 1000 / fix[0], 2))
