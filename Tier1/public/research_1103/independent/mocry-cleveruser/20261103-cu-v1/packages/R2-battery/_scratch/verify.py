import json, math, os, sys

base = os.path.join('Tier1', 'workspaces', 'mocry', 'cleveruser', 'firstpass', 'R2-battery')

for name in ('parameters.json', 'sources.json'):
    p = os.path.join(base, name)
    with open(p, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    print('OK parse', name, 'bytes', os.path.getsize(p))

with open(os.path.join(base, 'parameters.json'), 'r', encoding='utf-8') as f:
    params = json.load(f)
ids = [c['id'] for c in params['claims']]
print('claims', len(ids), 'unique', len(set(ids)))

with open(os.path.join(base, 'sources.json'), 'r', encoding='utf-8') as f:
    src = json.load(f)
print('sources', len(src['sources']), 'not_obtained', len(src['sources_not_obtained']))

# arithmetic checks
energy_side = 0.077 + 0.023 + 0.081 + 0.010 + 0.037
power_side = (0.069 + 0.017) / 2.0
subtotal = energy_side + power_side
total = subtotal * 1.10
print('DEA energy_side', round(energy_side, 4), 'power_side', round(power_side, 4))
print('DEA subtotal', round(subtotal, 4), 'total', round(total, 4))
print('vs brief 0.288 -> pct diff', round((total - 0.288) / 0.288 * 100, 2))
assert abs(total - 0.298) < 0.002, total

# 2023 variant
t2023 = (0.084 + 0.025 + 0.081 + 0.010 + 0.037) + power_side
t2023 *= 1.10
print('DEA 2023-variant total', round(t2023, 4))
assert 0.30 < t2023 < 0.315

# Lazard
low = 113 + 26 / 2 + 29
high = 244 + 70 / 2 + 122
print('Lazard sum-of-lines USD/kWh', low, high)
print('Lazard reported total USD/kWh', 34e6 / 200000, 88e6 / 200000)
assert (low, high) == (155, 401)
assert (34e6 / 200000, 88e6 / 200000) == (170, 440)

# Tesla duration
print('Tesla duration h', 3854 / 1927)
assert abs(3854 / 1927 - 2.0) < 1e-9

# efficiency split
print('eta per direction', round(math.sqrt(0.90), 5))
assert abs(math.sqrt(0.90) - 0.94868) < 1e-5

# usable window
print('usable MWh per MWh nameplate', 0.6, 'hours at 0.5 MW/MWh', 0.6 / 0.5)

# cycle budget
print('20y x 350 cycles', 20 * 350, 'vs LFP', 2400)
assert 20 * 350 == 7000

# refurb
print('refurb MEUR2020/MWh', round(0.30 * 0.069 / 2, 5))

print('ALL CHECKS PASSED')
