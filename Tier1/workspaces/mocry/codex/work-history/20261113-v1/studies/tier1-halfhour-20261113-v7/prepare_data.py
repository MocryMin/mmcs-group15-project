"""Reconstruct intraday shapes from frozen evidence; retain v6 daily totals."""
from pathlib import Path
import sys, json, gzip, hashlib, statistics
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT/'source_data' if (ROOT/'source_data').exists() else ROOT.parent
OLD = PROJECT / 'tier1-multiproduct-20261110-v6'
REPAIR = PROJECT / 'data-repair-20261104-v2'
sys.path.insert(0, str(REPAIR))
import repair_data as rd

def read_json(p):
    with (gzip.open(p, 'rt', encoding='utf-8') if p.suffix == '.gz' else p.open(encoding='utf-8')) as f:
        return json.load(f)

def build():
    (ROOT/'inputs').mkdir(exist_ok=True)
    days = pd.date_range('2020-01-01', '2025-12-31').strftime('%Y-%m-%d').tolist()
    source = {k:read_json(REPAIR/'evidence'/f'{k}.json.gz') for k in ('agpt','fuelhh','neso','demand')}
    audit = read_json(REPAIR/'REPAIR_AUDIT.json')
    neso = rd.parse_neso(source['neso'])
    fuel_daily = pd.read_csv(OLD/'inputs/daily_generation_by_fuel.csv').pivot(index='date',columns='psrType',values='MW')
    demand_daily = pd.read_csv(OLD/'inputs/daily_demand.csv').set_index('startTime')['demand']
    demand_daily.index = demand_daily.index.str[:10]
    wind_daily = pd.read_csv(OLD/'inputs/wind_farm_generation.csv').set_index('date')['wind_farm_MW']
    # Reuse the exact real-price column already used in the daily optimisation.
    v6 = pd.read_csv(OLD/'results/A_comparable_main_schedule.csv').set_index('date')
    prices = pd.read_csv(PROJECT/'gb-price-stress-20261112/halfhour-market-index.csv')
    prices['utc'] = pd.to_datetime(prices.utc,utc=True)
    price_series = prices.set_index('utc').mid_GBP2020_per_MWh
    demand_replacements = {r['date']:{int(v[0]):v[2] for v in r['replaced_intervals']}
                           for r in audit['demand_reconstructions']}
    output=[]; quality=[]
    for day in days:
        start=rd.daily_start(day); targets=list(range(start,start+1440,30))
        agpt={rd.stamp_minutes(t):v for t,v in source['agpt']['days'].get(day,{}).items()}
        bad={t for t,v in agpt.items() if all(x==0 for x in v[:8])}
        fh={rd.stamp_minutes(t):v for t,v in source['fuelhh']['days'][day].items()}
        bad_fh={start+x for x in audit['fuelhh_filled_intervals_minutes_UTC'].get(day,[])}
        fuel_shapes=[]; methods=[]
        for i,name in enumerate(rd.FUELS):
            valid={t:v[i] for t,v in agpt.items() if rd.finite(v[i]) and (i>=8 or t not in bad)}
            if len(valid)>=42:
                shape=np.array([max(0,rd.interpolate(valid,t)) for t in targets])
                method='AGPT_observed' if len(valid)==48 else 'AGPT_short_interpolation'
            elif i<8:
                keys=[['BIOMASS'],['CCGT','OCGT'],['COAL'],['OIL'],['PS'],['NPSHYD'],['NUCLEAR'],['OTHER']][i]
                valid={t:max(0,sum(v[k] for k in keys)) for t,v in fh.items()
                       if t not in bad_fh and all(rd.finite(v.get(k)) for k in keys)}
                shape=np.array([rd.interpolate(valid,t) for t in targets])
                method='FUELHH_shape_transfer'
            elif i==8:
                shape=np.array([max(0,neso[day][t][2]) for t in targets])
                method='NESO_solar_shape_transfer'
            else:
                valid={t:max(0,v['WIND']) for t,v in fh.items() if rd.finite(v.get('WIND')) and t not in bad_fh}
                shape=np.array([rd.interpolate(valid,t)+max(0,neso[day][t][3]) for t in targets])
                method='FUELHH_NESO_wind_shape_transfer'
            mean=float(fuel_daily.loc[day,name])
            if shape.mean()<=0 and mean>0:
                shape=np.ones(48);method='flat_no_shape_available'
            shape=shape*(mean/shape.mean()) if shape.mean()>0 else np.zeros(48)
            fuel_shapes.append(shape); methods.append(method)
        generation=np.sum(fuel_shapes,axis=0)
        raw_d={rd.stamp_minutes(t):v for t,v in source['demand']['days'].get(day,{}).items()}
        replacements=demand_replacements.get(day,{})
        d5=np.array([replacements[t-start] if t-start in replacements else raw_d[t]
                     for t in range(start,start+1440,5)])
        demand=d5.reshape(48,6).mean(axis=1)
        demand*=float(demand_daily.loc[day])/demand.mean()
        stamps=pd.date_range(day, periods=48, freq='30min',tz='UTC')
        price=price_series.reindex(stamps).to_numpy(); observed=np.isfinite(price)
        if observed.sum()>=24:
            # Short missing price intervals use surrounding observed timestamps.
            union=price_series.index.union(stamps).sort_values()
            price=price_series.reindex(union).interpolate(method='time').reindex(stamps).to_numpy()
            pm='MID_observed' if observed.all() else 'MID_short_interpolation'
        else:
            peers=[]
            for delta in (7,-7,14,-14,21,-21,28,-28):
                ps=price_series.reindex(stamps+pd.Timedelta(days=delta))
                if ps.notna().sum()>=42:
                    peers.append(ps.interpolate(limit_direction='both').to_numpy())
                if len(peers)==4:break
            assert peers,day
            price=np.mean(peers,axis=0); pm='same_weekday_shape_estimate'
        # Anchor price shape to v6's mean, retaining its prior missing-day estimate.
        price=price+float(v6.loc[day,'price'])-price.mean()
        wind=float(wind_daily.loc[day])
        wind_shape=np.sum(fuel_shapes[-2:],axis=0)
        wind_proxy=wind_shape/wind_shape.mean()*wind if wind_shape.mean()>0 else np.repeat(wind,48)
        output.extend(zip(stamps.astype(str),np.repeat(day,48),generation,np.repeat(wind,48),wind_proxy,
                          demand,price,observed.astype(int)))
        quality.append(dict(date=day,generation_methods='|'.join(methods),
                            generation_native=all(m=='AGPT_observed' for m in methods),
                            demand_native=not replacements,price_native=bool(observed.all()),
                            price_observed_slots=int(observed.sum()),price_method=pm,
                            independent_wind_method='daily_mean_flat; GB_wind_profile_sensitivity'))
    columns=['utc','date','background_MW','farm_flat_MW','farm_proxy_MW','demand_MW','price','price_observed']
    df=pd.DataFrame(output,columns=columns)
    df.to_csv(ROOT/'inputs/halfhour.csv.gz',index=False,compression='gzip',float_format='%.12g')
    q=pd.DataFrame(quality);q.to_csv(ROOT/'inputs/day_quality.csv',index=False)
    mean=df.groupby('date')[['background_MW','farm_flat_MW','demand_MW','price']].mean()
    checks=dict(days=len(days),periods=len(df),price_full_days=int(q.price_native.sum()),
                generation_full_days=int(q.generation_native.sum()),demand_full_days=int(q.demand_native.sum()),
                all_three_full_days=int((q.price_native&q.generation_native&q.demand_native).sum()),
                daily_generation_error_GWh=float(abs((mean.background_MW+mean.farm_flat_MW)*.024-v6.generation).max()),
                daily_demand_error_GWh=float(abs(mean.demand_MW*.024-v6.demand).max()),
                daily_price_error=float(abs(mean.price-v6.price).max()),
                note='Observed/reconstructed shapes anchored to v6 daily means. Farm intraday profiles are assumptions, not observations.')
    assert checks['daily_generation_error_GWh']<1e-8 and checks['daily_demand_error_GWh']<1e-8 and checks['daily_price_error']<1e-8
    paths=[OLD/'configuration.json',OLD/'results/A_comparable_main_schedule.csv',
           OLD/'inputs/daily_generation_by_fuel.csv',OLD/'inputs/daily_demand.csv',OLD/'inputs/wind_farm_generation.csv',
           REPAIR/'REPAIR_AUDIT.json',PROJECT/'gb-price-stress-20261112/halfhour-market-index.csv']
    paths += [REPAIR/'evidence'/f'{k}.json.gz' for k in source]
    manifest={str(p.relative_to(PROJECT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths}
    (ROOT/'inputs/source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (ROOT/'inputs/data_validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    config=read_json(OLD/'configuration.json');config['version']='v7-halfhour-20261113';config['dt_hours']=.5
    config['preserved']=[v for v in config['preserved'] if 'chronological daily' not in v and 'one net charge' not in v]
    config['operating_clock']={
        'time_zone':'UTC','hours_per_period':0.5,'periods_per_day':48,
        'battery':'Stock every half hour; direction exclusivity per type per half hour; multiple intraday cycles allowed.',
        'electrolyser':'Minimum online load per half hour; constant nominal kWh/kg; no minute-scale startup/ramp model.',
        'offtake':'Sum all 48 half-hour hydrogen quantities against the original DAILY cap.',
        'B':'Generation first; battery output next, limited by both opening usable stock and half-hour power.',
        'self_discharge':'Half-hour retention = (1 - daily self-discharge)^(1/48). Main case remains zero.'}
    (ROOT/'configuration.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2),flush=True)

if __name__=='__main__':build()
