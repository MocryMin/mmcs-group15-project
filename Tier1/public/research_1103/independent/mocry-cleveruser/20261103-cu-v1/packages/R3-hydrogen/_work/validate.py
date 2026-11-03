import json, re, os, math

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(base, '..'))

p = json.load(open(os.path.join(root, 'parameters.json'), encoding='utf-8'))
s = json.load(open(os.path.join(root, 'sources.json'), encoding='utf-8'))

ids = [c['id'] for c in p['claims']]
assert len(ids) == len(set(ids)), "duplicate claim ids"
src_ids = {x['id'] for x in s['sources']}
missing = set()
for c in p['claims']:
    ref = c.get('source_ref') or ''
    for tok in re.findall(r'S\d+', ref):
        if tok not in src_ids:
            missing.add((c['id'], tok))
print("claims:", len(ids), "| sources:", len(src_ids), "| dangling source refs:", sorted(missing))
print("gaps covered:", sorted({c['gap_id'] for c in p['claims']}))

# --- arithmetic verification of every headline conversion in REPORT.md ---
checks = []
def chk(name, got, want, tol=0.01):
    ok = abs(got - want) <= tol * max(1.0, abs(want))
    checks.append((ok, name, round(got, 4), want))

chk("241 GBP/MWh x 39.4 kWh/kg", 241 * 39.4 / 1000, 9.4954)
chk("175 GBP/MWh x 39.4 kWh/kg", 175 * 39.4 / 1000, 6.895)
chk("implied GBP/MWh of electricity", 9.50 / 55.9 * 1000, 169.95)
chk("kg/h per MW_e", 1000 / 55.9, 17.889)
chk("POSEIDON kWh/kg check", 20000 / 360, 55.56, 0.01)
chk("ALPHA50 kWh/kg check", 50000 / 900, 55.56, 0.01)
chk("NEPTUNE II kWh/kg check", 2000 / 35, 57.14, 0.01)
chk("BEIS 2020 medium kWh/kg", 1.397 * 39.4, 55.04)
chk("BEIS 2020 medium GBP/kW_e", 1158.63 / 1.397, 829.37)
chk("BEIS low pair GBP/kW_e", 953.59 / 1.2319, 774.09)
chk("BEIS high pair GBP/kW_e", 1887.51 / 1.6256, 1161.12)
chk("BEIS 2025 medium GBP/kW_e", 730.29 / 1.3208, 552.90)
chk("BEIS fixed opex GBP/kW_e/yr", 36.72 / 1.397, 26.29)
chk("BEIS variable opex GBP/kg", 0.0039 * 39.4, 0.15366)
chk("ALPHA50 EUR per MW", 50e6 / 50, 1.0e6, 0.001)
chk("HAR1 private capital per MW", 413 / 125, 3.304)
chk("HAR1 incl grant per MW", (413 + 90) / 125, 4.024)
chk("overstatement if 39.4 used as input", 55.9 / 39.4, 1.4193)
chk("reconversion round trip at 60%", 39.4 * 0.60 / 55.9, 0.4229)

# indicative break-even cross-check quoted in REPORT 2.9
capex = 1.5e6
crf = 0.1 / (1 - 1.1 ** -30)
kg_per_mw_yr = 17.889 * 8760 * 0.98
capex_per_kg = capex * crf / kg_per_mw_yr
fixed_per_kg = 26300 / kg_per_mw_yr
stack_pv = sum(0.6 * capex / 1.1 ** y for y in (11, 22))
stack_per_kg = stack_pv * crf / kg_per_mw_yr
var_per_kg = 0.15366
non_elec = capex_per_kg + fixed_per_kg + stack_per_kg + var_per_kg
breakeven = (9.50 - non_elec) / 55.9 * 1000
chk("non-electric cost GBP/kg", non_elec, 1.65, 0.05)
chk("break-even electricity GBP/MWh", breakeven, 140.4, 0.02)
chk("LCOH at 100 GBP/MWh", non_elec + 100 * 55.9 / 1000, 7.24, 0.02)

bad = [c for c in checks if not c[0]]
for ok, name, got, want in checks:
    print(("PASS " if ok else "FAIL "), f"{name:42s} got={got} want={want}")
print("\nFAILURES:", len(bad))
assert not bad
print("ALL JSON AND ARITHMETIC CHECKS PASSED")
