"""Read-only reproducible audit of the five supplied MMCS daily CSVs."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[4] / 'materials' / 'sync-20261030'
OUT = Path(__file__).resolve().parent
names = ['daily_generation_by_fuel.csv', 'daily_generation_total.csv', 'daily_demand.csv',
         'wind_farm_generation.csv', 'daily_market_index_price.csv']
raw, rows, inventory = {}, {}, {}
for name in names:
    data = (BASE / name).read_bytes()
    raw[name] = hashlib.sha256(data).hexdigest()
    with (BASE / name).open(encoding='utf-8-sig', newline='') as stream:
        rows[name] = list(csv.DictReader(stream))
    key = 'startTime' if name == 'daily_demand.csv' else 'date'
    dates = [r[key][:10] for r in rows[name]]
    inventory[name] = dict(rows=len(dates), distinct_dates=len(set(dates)), first=min(dates),
                           last=max(dates), sha256=raw[name])

fuel = defaultdict(dict)
fuel_duplicates = []
for r in rows[names[0]]:
    if r['psrType'] in fuel[r['date']]:
        fuel_duplicates.append([r['date'], r['psrType']])
    fuel[r['date']][r['psrType']] = float(r['MW'])

mapping = {}
duplicates = {}
for name, column in [(names[1], 'total_MW'), (names[2], 'demand'), (names[3], 'wind_farm_MW'),
                     (names[4], 'avg_price_£_per_MWh')]:
    key = 'startTime' if name == names[2] else 'date'
    counts = Counter(r[key][:10] for r in rows[name])
    duplicates[name] = [d for d, n in counts.items() if n > 1]
    mapping[name] = {r[key][:10]: float(r[column]) for r in rows[name]}

sets = [set(fuel)] + [set(x) for x in mapping.values()]
common = sorted(set.intersection(*sets))
union = sorted(set.union(*sets))
segments = []
for day in common:
    if not segments or date.fromisoformat(day) != date.fromisoformat(segments[-1][-1]) + timedelta(days=1):
        segments.append([])
    segments[-1].append(day)

year_stats = {}
for year in sorted({d[:4] for d in common}):
    ds = [d for d in common if d.startswith(year)]
    expected = (date(int(year)+1, 1, 1)-date(int(year), 1, 1)).days
    year_stats[year] = dict(common_dates=len(ds), calendar_days=expected,
                           negative_price_days=sum(mapping[names[4]][d] < 0 for d in ds))

price_ratio_error = max(abs(float(r['avg_price_£_per_MW_day']) - 24*float(r['avg_price_£_per_MWh'])) for r in rows[names[4]])
reconciliation = max(abs(sum(fuel[d].values())-mapping[names[1]][d]) for d in set(fuel)&set(mapping[names[1]]))
prices = mapping[names[4]]
demand = mapping[names[2]]
result = {
    'source': 'Five unchanged course-supplied CSVs; own calculation, no external unit provenance inferred',
    'inventory': inventory,
    'fuel_types': sorted(set.union(*(set(v) for v in fuel.values()))),
    'fuel_date_pair_duplicates': fuel_duplicates,
    'other_date_duplicates': duplicates,
    'date_intersection_count': len(common), 'union_count': len(union),
    'intersection_excluded_dates': sorted(set(union)-set(common)),
    'continuous_segments': [{'start':s[0], 'end':s[-1], 'days':len(s)} for s in segments],
    'year_stats': year_stats,
    'maximum_total_vs_fuel_sum_error_MW': reconciliation,
    'maximum_price_MWday_vs_24MWh_error': price_ratio_error,
    'negative_price_dates': sorted(d for d in prices if prices[d]<0),
    'price_min': min(prices.items(), key=lambda x:x[1]),
    'price_max': max(prices.items(), key=lambda x:x[1]),
    'demand_min': min(demand.items(), key=lambda x:x[1]),
    'demand_max': max(demand.items(), key=lambda x:x[1]),
    'demand_2022_08_02_neighbours': {d:demand.get(d) for d in ['2022-08-01','2022-08-02','2022-08-03']},
    'scope_cautions': ['No anomaly automatically deleted', '24x price identity is a unit consistency check, not proof demand is daily-average MW', 'Temporal gaps cannot be ignored in SOC transitions', 'Fuel-category reconciliation does not prove inclusion of the separately simulated facility'],
}
for name in names:
    assert hashlib.sha256((BASE/name).read_bytes()).hexdigest() == raw[name]
(OUT/'data_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:result[k] for k in ['date_intersection_count','union_count','year_stats','maximum_total_vs_fuel_sum_error_MW','maximum_price_MWday_vs_24MWh_error','demand_2022_08_02_neighbours']}, ensure_ascii=True))
