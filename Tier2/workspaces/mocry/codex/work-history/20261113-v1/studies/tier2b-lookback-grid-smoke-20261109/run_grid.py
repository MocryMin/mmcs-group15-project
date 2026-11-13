"""Controlled lookback smoke grid with fixed target dates and validation selection."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
from pathlib import Path
import json
import shutil
import sys
import time

import numpy as np
import pandas as pd
import torch

from fit_core import fit,dump,sha,score
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/"tier1-candidate-20261107-v4.1-academic/inputs"
PREVIOUS=ROOT.parent/"tier2b-independent-newsplit-20261109"
LOOKBACKS=[365,182,91,56,30,14,7]
PERIODS={"train":("2022-01-01","2024-12-31"),"validation":("2025-01-01","2025-08-31"),"test":("2025-09-01","2026-08-31")}
SEED=17


def prepare():
    inputs=ROOT/"inputs";inputs.mkdir(exist_ok=True)
    if (inputs/"model_daily.csv").exists():
        manifest=json.loads((inputs/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        assert sha(inputs/"model_daily.csv")==manifest["derived_sha256"]
        f=pd.read_csv(inputs/"model_daily.csv",parse_dates=["date"]).set_index("date")
    else:
        frozen=json.loads((SOURCE/"MANIFEST.json").read_text(encoding="utf-8"));manifest={"sources":{}}
        def read(name,date="date"):
            assert sha(SOURCE/name)==frozen[name]["sha256"]
            manifest["sources"][name]={"sha256":sha(SOURCE/name),"source":str(SOURCE/name)}
            d=pd.read_csv(SOURCE/name);d.index=pd.to_datetime(d.pop(date),utc=True).dt.tz_localize(None)
            assert d.index.is_unique
            return d.sort_index()
        total=read("daily_generation_total.csv").total_MW;wind=read("wind_farm_generation.csv").wind_farm_MW
        demand=read("daily_demand.csv","startTime").demand
        price=read("daily_market_index_price.csv")["avg_price_£_per_MWh"]
        strict=read("date_quality.csv").strict_no_imputation.astype(str).str.lower().isin(["1","true"])
        assert all(z.index.equals(total.index) for z in (wind,demand,price,strict))
        f=pd.DataFrame({"generation_MW":total+wind,"demand_MW":demand,"price_GBP_MWh":price,
            "source_total_MW":total,"wind_farm_MW":wind,"strict_no_imputation":strict}).loc["2021-01-01":"2026-09-17"]
        f.to_csv(inputs/"model_daily.csv",index_label="date")
        manifest["derived_sha256"]=sha(inputs/"model_daily.csv");dump(inputs/"SOURCE_MANIFEST.json",manifest)
        f=pd.read_csv(inputs/"model_daily.csv",parse_dates=["date"]).set_index("date")
    assert f.index.equals(pd.date_range("2021-01-01","2026-09-17"))
    train=f.loc["2022-01-01":"2024-12-31",TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy()
    z=(f[TARGETS].to_numpy()-mean)/scale
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32)
    data={};splits=[]
    for part,(a,b) in PERIODS.items():
        origins=np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b))
        assert origins.min()>=364
        data[part]={"origins":origins,"y":z[origins+1].astype(np.float32),"truth":f[TARGETS].to_numpy()[origins+1]}
        for t in origins:splits.append({"split":part,"origin":str(f.index[t].date()),"history_start_365":str(f.index[t-364].date()),"target_date":str(f.index[t+1].date())})
    assert {p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365}
    pd.DataFrame(splits).to_csv(ROOT/"splits.csv",index=False)
    dump(ROOT/"scalers.json",{"targets":TARGETS,"mean":mean.tolist(),"std":scale.tolist(),"fit_start":"2022-01-01","fit_end":"2024-12-31","ddof":0})
    return f,x,data,mean,scale


def previous_equivalence(f,x,data,mean,scale):
    previous=pd.read_csv(PREVIOUS/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
    scaler=json.loads((PREVIOUS/"scalers.json").read_text())
    assert np.array_equal(mean,np.array(scaler["mean"])) and np.array_equal(scale,np.array(scaler["std"]))
    z=(previous[TARGETS].to_numpy()-mean)/scale
    dow=previous.index.dayofweek.to_numpy();phase=(previous.index.dayofyear.to_numpy()-1)/np.where(previous.index.is_leap_year,366,365)
    px=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32)
    for p,(a,b) in PERIODS.items():
        origins=np.flatnonzero((previous.index[1:]>=a)&(previous.index[1:]<=b))
        assert np.array_equal(windows(px,origins,56),windows(x,data[p]["origins"],56))
        assert np.array_equal(previous[TARGETS].to_numpy()[origins+1],data[p]["truth"])
    dump(ROOT/"REUSE_EQUIVALENCE.json",{"all_three_sets_exact_float32_input_and_label_match":True,"scalers_exact_match":True,
        "lookback":56,"seed":17,"source":str(PREVIOUS),"reuse_only_same_target_family_learning_rate_window_seed":True})


def export_case(row,f,x,data,mean,scale):
    j=TARGETS.index(row["target"])
    cp=torch.load(ROOT/row["checkpoint"],weights_only=True)
    model=Predictor(row["family"],j);model.load_state_dict(cp["state_dict"]);model.eval()
    predictions={};metrics=[]
    for part,d in data.items():
        xx=torch.from_numpy(windows(x,d["origins"],row["lookback"]))
        with torch.inference_mode():pred=model(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
        predictions[part]=pred
        metrics.append({"target":row["target"],"family":row["family"],"lookback":row["lookback"],"seed":SEED,"split":part,
            "best_step":row["best_step"],"epochs":row["epochs"],**score(pred,d["truth"][:,j],scale[j])})
    np.savez_compressed(ROOT/"predictions"/(row["run"]+".npz"),**predictions)
    return metrics


def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    for name in ("results","checkpoints","step_logs","predictions"):(ROOT/name).mkdir(exist_ok=True)
    f,x,data,mean,scale=prepare()
    cfg=ROOT/"REFERENCE_CONFIGS.json"
    if not cfg.exists():shutil.copy2(PREVIOUS/"REFERENCE_CONFIGS.json",cfg)
    configs=json.loads(cfg.read_text());old=pd.read_csv(PREVIOUS/"results/training_runs.csv")
    previous_equivalence(f,x,data,mean,scale)
    protocol={"lookbacks_days":LOOKBACKS,"labels":{"365":"one year","182":"half year","91":"three months","56":"56 days","30":"30 days","14":"14 days","7":"7 days"},
        "month_interpretation":"Fixed day counts; not variable calendar-month windows","seed":SEED,"purpose":"Single-seed controlled lookback smoke grid",
        "expected_cases":42,"periods":PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},
        "context_only":"2021-01-01 through 2021-12-31; no 2021 training labels","identical_target_dates_for_every_window":True,
        "batch_size":64,"steps_per_epoch":18,"max_epochs":120,"patience_epochs":15,"checkpoint_min_delta":1e-5,
        "learning_rates":"Fixed previous target/family learning rate; only input lookback changes",
        "architecture":"Independent scalar targets; RNN hidden68/5373 parameters, LSTM hidden32/5409; 8 shared-observation input features; no weight sharing",
        "evaluation":"Full train, val and test eval after every optimiser step; checkpoint/early stop and grid selection use validation only",
        "previous_reuse":"Only three identical L56 seed17 cases after exact input/label/scaler checks; original complete logs and weights retained",
        "test_status":"Monitored held-out test, previously inspected; not blind; no test-driven selection",
        "source_hashes":{n:sha(ROOT/n) for n in ("run_grid.py","fit_core.py","model.py","REFERENCE_CONFIGS.json")},
        "data_vintage_audited":False,"MPC_evaluated":False,"python":sys.version,"torch":torch.__version__}
    dump(ROOT/"PROTOCOL.json",protocol)
    print("PROTOCOL",json.dumps(protocol,ensure_ascii=False),flush=True)
    rows=[];metrics=[];began=time.monotonic()
    # Target/family ordering helps compare each complete seven-window grid.
    for target in TARGETS:
        for family in ("RNN","LSTM"):
            lr=float(configs[target+"|"+family]["lr"])
            for length in LOOKBACKS:
                match=old.loc[old.target.eq(target)&old.family.eq(family)&old.lookback.eq(length)&old.lr.eq(lr)&old.seed.eq(SEED)]
                if length==56 and len(match)==1:
                    row=match.iloc[0].to_dict()
                    for key in ("seed","lookback","parameters","best_epoch","best_step","epochs","steps"):row[key]=int(row[key])
                    for key in ("checkpoint","step_log"):
                        path=Path(str(row[key]).replace("\\","/"));shutil.copy2(PREVIOUS/path,ROOT/path)
                        row[key]=path.as_posix()
                    row["original_training_seconds"]=float(row["seconds"]);row["seconds"]=0.;row["reused_previous"]=True
                    print("REUSE",row["run"],flush=True)
                else:
                    row=fit(target,family,{"lookback":length,"lr":lr},SEED,x,data,mean,scale)
                    row["reused_previous"]=False;row["original_training_seconds"]=None
                metrics.extend(export_case(row,f,x,data,mean,scale));rows.append(row)
                pd.DataFrame(rows).to_csv(ROOT/"results/training_runs.csv",index=False)
                pd.DataFrame(metrics).to_csv(ROOT/"results/GRID_METRICS.csv",index=False)
                print("PROGRESS",len(rows),"/42",flush=True)
    baseline=[]
    for part,d in data.items():
        for j,target in enumerate(TARGETS):
            baseline.append({"target":target,"split":part,**score(f[TARGETS].to_numpy()[d["origins"],j],d["truth"][:,j],scale[j])})
    pd.DataFrame(baseline).to_csv(ROOT/"results/PERSISTENCE.csv",index=False)
    selection={}
    for target in TARGETS:
        for family in ("RNN","LSTM"):
            g=pd.DataFrame(rows);g=g.loc[g.target.eq(target)&g.family.eq(family)].sort_values(["best_validation_loss","lookback"])
            c=g.iloc[0]
            selection[target+"|"+family]={"target":target,"family":family,"lookback":int(c.lookback),"seed":SEED,
                "best_validation_loss":float(c.best_validation_loss),"best_step":int(c.best_step),"run":c.run}
    dump(ROOT/"results/SELECTION_FROZEN.json",selection)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"runs":rows,"metrics":metrics,"baselines":baseline,"selected":selection,
        "wall_seconds":time.monotonic()-began,"new_training_seconds":sum(row["seconds"] for row in rows)})
    print("COMPLETE",json.dumps(selection),flush=True)


if __name__=="__main__":main()
