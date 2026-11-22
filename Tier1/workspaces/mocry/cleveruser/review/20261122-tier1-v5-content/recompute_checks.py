"""Independent arithmetic checks on Tier 1 report v5 (doc 7b8a9fa5...).

Only the report's own printed values are used; no author code is available in the
published v5 directory, so these checks test internal consistency and stated
identities, not the underlying optimisation.

Run: python -X utf8 recompute_checks.py
Writes checks.json next to this file and prints a pass/fail table.
"""

import json
import math
from datetime import date

OUT = "checks.json"

def annuity(rate, years):
    return rate / (1 - (1 + rate) ** -years)

def days_between(a, b):
    return (b - a).days + 1

checks = []

def add(name, computed, stated, ok, note=""):
    checks.append(dict(name=name, computed=computed, stated=stated, ok=ok, note=note))

# ---- calendar -------------------------------------------------------------
d_all = days_between(date(2020, 1, 1), date(2026, 9, 17))
d_t1 = days_between(date(2020, 1, 1), date(2025, 12, 31))
add("calendar days 2020-01-01..2026-09-17", d_all, 2452, d_all == 2452)
add("Tier 1 days 2020-2025", d_t1, 2192, d_t1 == 2192)
add("Tier 1 half-hours", d_t1 * 48, 105216, d_t1 * 48 == 105216)

# ---- equipment ------------------------------------------------------------
mod_mw = 90 * 55.9 / 1000          # 90 kg/h, 55.9 kWh/kg -> MW input
add("module input MW", round(mod_mw, 6), 5.031, abs(mod_mw - 5.031) < 5e-4)

mw_a = 845 * mod_mw
mw_b = 362 * mod_mw
add("845 modules MW", round(mw_a, 4), 4251.195, abs(mw_a - 4251.195) < 0.05)
add("362 modules MW", round(mw_b, 4), 1821.222, abs(mw_b - 1821.222) < 0.05)

K_elec = 1.46                      # £m per MW (2020)
K_bat = 38.690                     # £m per 100 MW / 400 MWh block
cap_a = mw_a * K_elec + K_bat
cap_b = mw_b * K_elec + K_bat
add("capital A £bn", round(cap_a / 1000, 3), 6.247, abs(cap_a / 1000 - 6.247) < 0.005)
add("capital B £bn", round(cap_b / 1000, 3), 2.698, abs(cap_b / 1000 - 2.698) < 0.005)

# ---- annual costs ---------------------------------------------------------
a_bat = K_bat * annuity(0.05, 15) + 0.025 * K_bat
add("battery annual cost £m", round(a_bat, 4), 4.695, abs(a_bat - 4.695) < 0.02)
# electrolyser 0.757 £m per module is an input; no independent build-up published in body.

payback_a = (K_bat + 80 * 78.13 / 1e6) / (7.586 - 0.025 * K_bat)
payback_b = (K_bat + 80 * 78.13 / 1e6) / (5.659 - 0.025 * K_bat)
add("payback A yr", round(payback_a, 2), 5.8, abs(payback_a - 5.8) < 0.1)
add("payback B yr", round(payback_b, 2), 8.2, abs(payback_b - 8.2) < 0.1)

ann15 = annuity(0.05, 15)
be_a_capital = 7.586 / (ann15 + 0.025)
be_b_capital = 5.659 / (ann15 + 0.025)
add("break-even A £/kWh", round(be_a_capital * 2.5, 1), 156, abs(be_a_capital * 2.5 - 156) < 2)
add("break-even B £/kWh", round(be_b_capital * 2.5, 1), 117, abs(be_b_capital * 2.5 - 117) < 2)

four_a = 7.586 - K_bat * (ann15 + 0.04)
four_b = 5.659 - K_bat * (ann15 + 0.04)
add("4% maintenance A £m/yr", round(four_a, 3), 2.311, abs(four_a - 2.311) < 0.01)
add("4% maintenance B £m/yr", round(four_b, 3), 0.383, abs(four_b - 0.383) < 0.01)

# ---- gains -----------------------------------------------------------------
add("battery full-foresight gain A", round(1692.85 - 1689.96, 2), 2.89, abs((1692.85 - 1689.96) - 2.89) < 0.01)
add("battery full-foresight gain B", round(119.34 - 118.38, 2), 0.96, abs((119.34 - 118.38) - 0.964) < 0.01)
add("battery simple-rule loss A", round(1687.36 - 1689.96, 3), -2.605, abs((1687.36 - 1689.96) + 2.605) < 0.01)
add("battery simple-rule loss B", round(117.44 - 118.38, 3), -0.938, abs((117.44 - 118.38) + 0.938) < 0.02)
add("net after annual cost A", round(7.586 - 4.695, 3), 2.891, abs((7.586 - 4.695) - 2.891) < 0.01)
add("net after annual cost B", round(5.659 - 4.695, 3), 0.964, abs((5.659 - 4.695) - 0.964) < 0.01)

# ---- unit conversions ------------------------------------------------------
L_usd = 62.15
M_usd = 111.32
H_usd = 160.49
for label, usd, stated in (("low", L_usd, 96.72), ("mid", M_usd, 173.25), ("high", H_usd, 249.77)):
    implied = stated * 400000 / usd / 1e6   # £m per block * 1e6 / (USD m) -> GBP/USD-ish factor
    add(f"conversion factor implied by Lazard {label} total", round(implied, 4), 0.635, False,
        "report states 0.635 in Appendix B.4/B.2")
add("low capital from 0.635", round(L_usd * 0.635, 2), 38.690, "mismatch", "0.635 * 62.15 != 38.69")
add("mid capital from 0.635", round(M_usd * 0.635, 2), 69.30, "mismatch", "stated 173.25 £/kWh = 69.30 £m")
add("electrolyser 2,300 $/kW at 0.635", round(2.3 * 0.635, 3), 1.46, abs(2.3 * 0.635 - 1.46) < 0.01)

# ---- hydrogen prices -------------------------------------------------------
add("brief £9.5 basis", round(241 * 39.4 / 1000, 4), 9.50, abs(241 * 39.4 / 1000 - 9.4954) < 0.01)
add("HAR1 2012-price deflation", round(175 * 39.4 / 1000 * (108.7 / 96.1), 3), 7.799, abs(175 * 0.0394 * 108.7 / 96.1 - 7.799) < 0.01)
add("£/kg to £/MWh at 55.9 kWh/kg", round(7.80 * 1000 / 55.9, 2), 139.53, abs(7.8 * 1000 / 55.9 - 139.5) < 0.5)

# ---- energy attribution ----------------------------------------------------
add("A unused delta Table II.3", 8647 - 4142, 4505, "text states 4,536", "Table II.3 gives 4,505; text says 4,536")
add("B unused delta Table II.3", 5165 - 2353, 2812, "text states 2,857", "Table II.3 gives 2,812; text says 2,857")
add("A take-up vs less-unused (text)", 4221, 4536, "inconsistent by 315 GWh", "same sentence, A: take-up 4,221 vs less unused 4,536")
add("B take-up vs less-unused (text)", 2857, 2857, "coincident", "B: 2,857 used twice")

# ---- Table C.1 implied opportunity cost -----------------------------------
rows = [(4, 7.80, 15.093, 5.66, 20.124, 2.21),
        (10, 5.00, 35.217, 4.96, 35.217, 1.19),
        (10, 7.80, 40.248, 14.10, 55.341, 5.48),
        (10, 10.00, 40.248, 21.79, 60.372, 9.49)]
for lim, gbp, mwa, ga, mwb, gb in rows:
    kg = lim * 365 * 1000
    kwh = kg * 55.9
    rev = kg / 1000 * gbp / 1e6
    cost_a = mwa / mod_mw * 0.757
    cost_b = mwb / mod_mw * 0.757
    opp_a = rev - cost_a - ga
    opp_b = rev - cost_b - ga
    add(f"implied opportunity cost A {lim}t {gbp}£/kg (£/MWh)",
        round(opp_a * 1e6 / (kwh / 1000), 1), None, "info", "revenue - equipment charge - stated gain")
    add(f"implied opportunity cost B {lim}t {gbp}£/kg (£/MWh)",
        round(opp_b * 1e6 / (kwh / 1000), 1), None, "info", "same for B")

# ---- 827 vs 845 ------------------------------------------------------------
add("module count mismatch", 827, 845, False, "Appendix B.3.1 says 827-module A plan; body uses 845")

failures = [c for c in checks if c["ok"] is False]
info = [c for c in checks if c["ok"] == "info"]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(dict(source_sha256="7b8a9fa573796be5ad80bc0844d8d8cf88efb7a68a07a9cf0b1451db46cc4e72",
                   checks=checks), f, indent=2)
print(f"checks={len(checks)} failures={len(failures)} info={len(info)} -> {OUT}")
for c in failures:
    print(f"FAIL {c['name']}: computed={c['computed']} stated={c['stated']} {c['note']}")
