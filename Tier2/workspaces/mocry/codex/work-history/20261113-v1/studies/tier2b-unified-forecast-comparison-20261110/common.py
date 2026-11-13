"""Shared next-day data, units, selection score and prediction storage."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("OPENBLAS_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
from pathlib import Path
import json
import hashlib
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/".deps"))
TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]
PERIODS={"train":("2022-01-01","2024-12-31"),"validation":("2025-01-01","2025-08-31"),"test":("2025-09-01","2026-08-31")}
INPUT_HASH="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def calendar(index):
    dow=index.dayofweek.to_numpy();phase=(index.dayofyear.to_numpy()-1)/np.where(index.is_leap_year,366,365);md=index.month.to_numpy()*100+index.day.to_numpy()
    return np.column_stack([np.eye(7)[dow],*[fn(2*np.pi*h*phase) for h in (1,2,3) for fn in (np.sin,np.cos)],((md>=1224)|(md<=101)).astype(float)])


class Data:
    def __init__(self):
        assert sha(ROOT/"inputs/model_daily.csv")==INPUT_HASH
        self.f=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
        assert self.f.index.equals(pd.date_range("2021-01-01","2026-09-17"))
        self.index=self.f.index;self.y=self.f[TARGETS].to_numpy();train=self.f.loc["2022":"2024",TARGETS]
        self.mean=train.mean().to_numpy();self.scale=train.std(ddof=0).to_numpy();self.z=(self.y-self.mean)/self.scale
        reference=json.loads((ROOT/"reference/scalers.json").read_text());assert np.array_equal(self.mean,reference["mean"]) and np.array_equal(self.scale,reference["std"])
        self.origins={p:np.flatnonzero((self.index[1:]>=a)&(self.index[1:]<=b)) for p,(a,b) in PERIODS.items()}
        old=pd.read_csv(ROOT/"reference/splits.csv")
        for p,o in self.origins.items():assert np.array_equal(self.index[o+1].strftime("%Y-%m-%d"),old.loc[old.split.eq(p),"target_date"].to_numpy())
        assert {p:len(o) for p,o in self.origins.items()}=={"train":1096,"validation":243,"test":365}
        self.cal=calendar(self.index)
        columns=[];names=[]
        for j,t in enumerate(TARGETS):
            v=pd.Series(self.z[:,j])
            for lag in [0,1,2,3,4,5,6,13]:columns.append(v.shift(lag).to_numpy());names.append(t+"_lag"+str(lag))
            for k in [7,28]:columns.append(v.rolling(k).mean().to_numpy());names.append(t+"_mean"+str(k))
        future_cal=calendar(self.index+pd.Timedelta(days=1))
        self.engineered=np.column_stack([*columns,future_cal]);self.feature_names=names+["target_calendar_"+str(i) for i in range(14)]
        assert self.engineered.shape[1]==44
        assert all(np.isfinite(self.engineered[o]).all() for o in self.origins.values())


def score(pred,truth,sd):
    error=np.asarray(pred,float)-np.asarray(truth,float)
    return {"n":len(error),"loss":float(np.mean((error/sd)**2)),"MSE":float(np.mean(error**2)),"RMSE":float(np.sqrt(np.mean(error**2))),"MAE":float(np.mean(np.abs(error)))}


def save_method(method_id,meta,predictions):
    """predictions: seed string -> split -> N x 3 RAW MW/MW/nominal GBP matrices."""
    folder=ROOT/"predictions";folder.mkdir(exist_ok=True)
    arrays={seed+"__"+p:np.asarray(v,float) for seed,d in predictions.items() for p,v in d.items()}
    assert all(np.isfinite(v).all() and v.ndim==2 and v.shape[1]==3 for v in arrays.values())
    np.savez_compressed(folder/(method_id+".npz"),**arrays)
    dump(ROOT/"methods"/(method_id+".json"),{"id":method_id,**meta,"prediction_file":"predictions/"+method_id+".npz","prediction_sha256":sha(folder/(method_id+".npz")),"seeds":list(predictions)})


def methods():return [json.loads(p.read_text()) for p in sorted((ROOT/"methods").glob("*.json"))]
