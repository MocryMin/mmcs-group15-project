"""External professional forecasts, explicitly separated from first-party predictors."""
import json
import pandas as pd,numpy as np
from features import ROOT
from build_features import save

index=pd.date_range('2021-01-01','2026-09-17')
for name,filename,columns in [
 ('neso_demand','neso_demand_day_ahead.json',['mean','min','max','n']),
 ('neso_wind','neso_wind_day_ahead.json',['mean','capacity','n'])]:
    src=ROOT/'research'/filename
    if not src.exists():continue
    data=json.loads(src.read_text());raw=pd.DataFrame(data['records']);valid=pd.to_datetime(raw.date,utc=True)
    issues=pd.to_datetime(raw.latest_issue,utc=True)
    assert (issues<valid).all()
    raw['date']=pd.to_datetime(raw.date)-pd.Timedelta(days=1);raw=raw.set_index('date').reindex(index)
    missing=raw['mean'].isna();out=raw[columns].astype(float).ffill().fillna(0);out.columns=[name+'_'+c for c in out]
    out['missing_forecast']=missing.astype(float)
    # Explicitly track stale forecasts rather than silently treating carry-forward as fresh data.
    elapsed=0;ages=[]
    for m in missing:
        elapsed=elapsed+1 if m else 0;ages.append(elapsed)
    out['forecast_stale_days']=ages
    note={'source_url':data['url'],'availability':'Only forecast timestamps strictly before valid UTC day00 survive; origin is prior UTC day. All retained latest_issue timestamps independently asserted before cutoff.','aggregation':'Latest available issue per cardinal point (demand) or UTC halfhour (wind), then mean/min/max or wind mean. These are forecast covariates, not realised daily targets.','not_a_scratch_forecast':'This experiment imports NESO professional forecasts; report independently of self-built weather/history predictors.','missing_days':int(missing.sum()),'max_stale_days':int(max(ages)),'imputation':'Past forecast carried forward with missingness and age flags. Never interpolation from future.','future_or_bad_issue_rejected':data['future_or_bad_issue_rejected']}
    if name=='neso_wind':note['important_limitation']='UTC boundary excludes BST tail halfhours not yet published at origin; n is retained. Current archive has a long unavailable tail after2026-04-23 under this strict timestamp rule.'
    save(name,out,note);print('built',name,out.shape,'missing',missing.sum(),'maxstale',max(ages))
