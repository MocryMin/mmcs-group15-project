"""Inspect original course inputs and build a date-aligned, unchanged-unit table."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / 'materials' / 'sync-20261030'

def prepare():
    frames = {}
    audit = {'originals': {}, 'adjustments': []}
    for name in ['daily_generation_by_fuel', 'daily_generation_total',
                 'daily_demand', 'wind_farm_generation', 'daily_market_index_price']:
        path = DATA / (name + '.csv')
        df = pd.read_csv(path)
        date_col = 'startTime' if name == 'daily_demand' else 'date'
        df['date'] = pd.to_datetime(df[date_col], utc=True).dt.tz_localize(None)
        key = ['date', 'psrType'] if name == 'daily_generation_by_fuel' else ['date']
        dates = pd.DatetimeIndex(df.date.unique()).sort_values()
        missing = pd.date_range(dates.min(), dates.max()).difference(dates)
        audit['originals'][name] = {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'rows': len(df), 'dates': len(dates), 'duplicate_keys': int(df.duplicated(key).sum()),
            'nulls': df.isna().sum().to_dict(), 'first': str(dates.min().date()),
            'last': str(dates.max().date()), 'missing_dates': [str(x.date()) for x in missing],
            'numeric_summary': df.select_dtypes('number').describe().to_dict()}
        assert not df.duplicated(key).any(), name
        frames[name] = df
    fuel = frames['daily_generation_by_fuel'].pivot(index='date', columns='psrType', values='MW')
    total = frames['daily_generation_total'].set_index('date')['total_MW']
    audit['fuel_types'] = list(fuel.columns)
    audit['max_fuel_total_difference_MW'] = float((fuel.sum(axis=1)-total).abs().max())
    df = pd.DataFrame({'generation_MW': total,
        'demand_MW': frames['daily_demand'].set_index('date')['demand'],
        'wind_MW': frames['wind_farm_generation'].set_index('date')['wind_farm_MW'],
        'price_MWh': frames['daily_market_index_price'].set_index('date')['avg_price_£_per_MWh'],
        'price_MWday': frames['daily_market_index_price'].set_index('date')['avg_price_£_per_MW_day']})
    audit['price_conversion_max_error'] = float((df.price_MWday-24*df.price_MWh).abs().max())
    audit['union_dates'] = len(df)
    audit['excluded_dates'] = [str(d.date()) for d in df.index[df.isna().any(axis=1)]]
    aligned = df.dropna().copy()
    audit['aligned_dates'] = len(aligned)
    audit['negative_price_days'] = int((aligned.price_MWh < 0).sum())
    audit['adjustments'] = ['Parse UTC dates to daily keys; join by date, not row number.',
        'Use complete-case date intersection for cross-series audit; no zero filling.',
        'Keep price in GBP/MWh; treat generation/demand as daily-average MW provisionally.']
    yearly = []
    for year,g in aligned.groupby(aligned.index.year):
        surplus=(g.generation_MW-g.demand_MW).clip(lower=0)
        residual=(g.demand_MW-g.generation_MW).clip(lower=0)
        yearly.append({'year': int(year), 'days':len(g),
            'calendar_days':len(pd.date_range(f'{year}-01-01', f'{year}-12-31')),
            'system_surplus_days':int((surplus>0).sum()),
            'system_surplus_MWh':float(24*surplus.sum()),
            'wind_MWh':float(24*g.wind_MW.sum()),
            'wind_max_MW':float(g.wind_MW.max()),
            'mean_price_MWh':float(g.price_MWh.mean()),
            'wind_spill_if_extra_MWh':float(24*(g.wind_MW-residual).clip(lower=0).sum()),
            'wind_spill_if_in_total_MWh':float(24*np.minimum(g.wind_MW,surplus).sum())})
    audit['yearly']=yearly
    aligned.to_csv(HERE/'aligned_data.csv',index_label='date')
    (HERE/'data_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=int)+'\n',encoding='utf-8')
    return aligned,audit

if __name__=='__main__':
    _,a=prepare()
    print(json.dumps({k:v for k,v in a.items() if k!='originals'},ensure_ascii=False,indent=2))
