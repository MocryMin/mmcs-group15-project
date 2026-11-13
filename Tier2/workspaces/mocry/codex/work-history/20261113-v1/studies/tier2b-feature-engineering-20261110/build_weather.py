"""Join valid-day forecasts onto their preceding forecast-origin day."""
import json
import numpy as np,pandas as pd
from features import ROOT
from build_features import save

index=pd.date_range('2021-01-01','2026-09-17')
src=ROOT/'research/gfs_temperature_day2.json'
if src.exists():
    raw=json.loads(src.read_text());frame=pd.DataFrame(index=index);values=[];missing=[]
    for k,loc in enumerate(raw['locations']):
        d=pd.DataFrame(loc['days']);d['date']=pd.to_datetime(d.date)-pd.Timedelta(days=1);d=d.set_index('date').reindex(index)
        v=d['mean'];missing.append(v.isna());v=v.ffill();values.append(v)
        frame['temp_forecast48h_location'+str(k)]=v
    avg=pd.concat(values,axis=1).mean(axis=1)
    frame['cold_index15']=np.maximum(15-avg,0);frame['warm_index22']=np.maximum(avg-22,0)
    frame['temperature_change']=avg.diff();frame['any_missing_forecast']=pd.concat(missing,axis=1).any(axis=1).astype(float)
    frame=frame.fillna(0)
    save('weather_temp',frame,{'source_url':raw['url'],'model':'GFS seamless','lead_hours_before_valid_time':48,'origin_date':'valid day minus one day','availability':'Every hourly forecast has 48h lead, so even last target-day hour was predicted at least24h before end of origin; not target-day realised weather. API docs describe lead, exact publication files not independently recovered.','aggregation':'Daily mean only if24 forecasts exist, otherwise previous daily forecast carried forward, with missingness flag. Initial no-forecast context zero, outside histories used by frozen windows.','locations':'London, Birmingham, Manchester, Glasgow; each separate proxy, not exact national area weights.','mechanism':'Heating/cooling demand and weather-driven price/supply; cold threshold15C and warm22C are uncalibrated feature basis choices.'})
    print('built weather_temp',frame.shape)

src=ROOT/'research/jma_wind_day2.json'
if src.exists():
    raw=json.loads(src.read_text());frame=pd.DataFrame(index=index)
    for k,loc in enumerate(raw['locations']):
        d=pd.DataFrame(loc['days']);d['date']=pd.to_datetime(d.date)-pd.Timedelta(days=1);d=d.set_index('date').reindex(index)
        assert d.n.eq(24).all()
        frame['wind_forecast48h_location'+str(k)]=d.wind_mean
        frame['wind_cubic_forecast48h_location'+str(k)]=d.wind_cubic_mean
    save('weather_wind',frame,{'source_url':raw['url'],'model':'JMA GSM','lead_hours_before_valid_time':48,'origin_date':'valid day minus one day','availability':'Fixed48h forecasts; every target-day hour predicted at least24h before end of origin. Not realised target-day weather.','aggregation':'24-hour mean wind speed km/h and mean cube of hourly wind speed m/s; all24 values required and present.','locations':'Aberdeen proxy, North Sea proxy, west Wales proxy, actual grid coordinates recorded upstream.','mechanism':'Regional wind predictability; cube of speed is a potential index, without claiming a specific hub-height correction, turbine power curve or farm geography.'})
    print('built weather_wind',frame.shape)

src=ROOT/'research/jma_solar_proxy_day2.json'
if src.exists():
    raw=json.loads(src.read_text());frame=pd.DataFrame(index=index)
    for k,loc in enumerate(raw['locations']):
        d=pd.DataFrame(loc['days']);d['date']=pd.to_datetime(d.date)-pd.Timedelta(days=1);d=d.set_index('date').reindex(index)
        assert d.n.eq(24).all()
        frame['cloud_forecast48h_location'+str(k)]=d.cloud_mean
        frame['daylight_clear_proxy_location'+str(k)]=d.daylight_cloud_index
    frame['clear_sky_seasonal_index']=d.clear_sky_index
    save('weather_solar',frame,{'source_url':raw['url'],'model':'JMA GSM','lead_hours_before_valid_time':48,'origin_date':'valid day minus one day','availability':'48h forecast cloud cover plus deterministic solar geometry, all known before origin cutoff.','aggregation':'All24 hours required and present; mean cloud and mean positive-cosine-solar-elevation times1-cloud_fraction. This is a heuristic feature, not measured irradiance or calibrated PV production.','locations':'London, Manchester, Edinburgh proxy grids','mechanism':'Seasonal daylight modulated by forecast clouds captures weather-driven solar supply beyond day-of-year harmonics.'})
    print('built weather_solar',frame.shape)
