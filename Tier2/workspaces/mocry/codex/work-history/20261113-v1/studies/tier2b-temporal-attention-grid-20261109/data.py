"""The exact frozen inputs and target dates of the preceding lookback grid."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from fit_core import dump,sha
from model import TARGETS

ROOT=Path(__file__).resolve().parent
LOOKBACKS=[365,182,91,56,30,14,7]
PERIODS={"train":("2022-01-01","2024-12-31"),"validation":("2025-01-01","2025-08-31"),"test":("2025-09-01","2026-08-31")}


def prepare():
    manifest=json.loads((ROOT/"inputs/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert sha(ROOT/"inputs/model_daily.csv")==manifest["derived_sha256"]
    f=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
    assert f.index.equals(pd.date_range("2021-01-01","2026-09-17"))
    train=f.loc["2022-01-01":"2024-12-31",TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy()
    z=(f[TARGETS].to_numpy()-mean)/scale
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32)
    data={};splits=[]
    for part,(a,b) in PERIODS.items():
        origins=np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b));assert origins.min()>=364
        data[part]={"origins":origins,"y":z[origins+1].astype(np.float32),"truth":f[TARGETS].to_numpy()[origins+1]}
        for t in origins:splits.append({"split":part,"origin":str(f.index[t].date()),"history_start_365":str(f.index[t-364].date()),"target_date":str(f.index[t+1].date())})
    assert {p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365}
    pd.DataFrame(splits).to_csv(ROOT/"splits.csv",index=False)
    dump(ROOT/"scalers.json",{"targets":TARGETS,"mean":mean.tolist(),"std":scale.tolist(),"fit_start":"2022-01-01","fit_end":"2024-12-31","ddof":0})
    return f,x,data,mean,scale
