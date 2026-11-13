"""Next-day-only RNN/LSTM comparison against the identical-value forecast."""
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import copy
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/"tier1-candidate-20261107-v4.1-academic"/"inputs"
TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]
WINDOWS=[28,56]
LRS=[0.001,0.003]
SEEDS=[17,29,43]
PERIODS={"train":("2020-01-01","2022-12-31"),"validation":("2023-01-01","2023-12-31")}


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    folder=ROOT/"inputs";folder.mkdir(exist_ok=True)
    # A self-contained derived snapshot is sufficient to reproduce the experiment.
    if (folder/"model_daily.csv").exists():
        frame=pd.read_csv(folder/"model_daily.csv",parse_dates=["date"]).set_index("date")
        manifest=json.loads((folder/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        assert digest(folder/"model_daily.csv")==manifest["derived_sha256"]
    else:
        names=["daily_generation_total.csv","wind_farm_generation.csv","daily_demand.csv","daily_market_index_price.csv","date_quality.csv"]
        known=json.loads((SOURCE/"MANIFEST.json").read_text(encoding="utf-8"))
        manifest={"sources":{}}
        for name in names:
            assert digest(SOURCE/name)==known[name]["sha256"]
            manifest["sources"][name]={"sha256":digest(SOURCE/name),"source":str(SOURCE/name)}
        def read(name,date="date"):
            d=pd.read_csv(SOURCE/name)
            d.index=pd.to_datetime(d.pop(date),utc=True).dt.tz_localize(None)
            assert d.index.is_unique
            return d.sort_index()
        total=read(names[0]).total_MW;wind=read(names[1]).wind_farm_MW
        demand=read(names[2],"startTime").demand;price=read(names[3])["avg_price_£_per_MWh"]
        q=read(names[4]).strict_no_imputation.astype(str).str.lower().isin(["1","true"])
        assert all(s.index.equals(total.index) for s in (wind,demand,price,q))
        frame=pd.DataFrame(dict(generation_MW=total+wind,demand_MW=demand,price_GBP_MWh=price,
            source_total_MW=total,wind_farm_MW=wind,strict_no_imputation=q)).loc["2020":"2023"]
        frame.to_csv(folder/"model_daily.csv",index_label="date")
        manifest["derived_sha256"]=digest(folder/"model_daily.csv")
        dump(folder/"SOURCE_MANIFEST.json",manifest)
    assert frame.index.equals(pd.date_range("2020-01-01","2023-12-31"))
    assert np.isfinite(frame[TARGETS]).all().all()
    frame["strict_no_imputation"]=frame.strict_no_imputation.astype(str).str.lower().isin(["1","true"])
    train=frame.loc["2020":"2022",TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy()
    normal=(frame[TARGETS].to_numpy()-mean)/scale
    weekday=frame.index.dayofweek.to_numpy()
    season=(frame.index.dayofyear.to_numpy()-1)/np.where(frame.index.is_leap_year,366,365)
    calendar=np.column_stack([np.sin(2*np.pi*weekday/7),np.cos(2*np.pi*weekday/7),
                               np.sin(2*np.pi*season),np.cos(2*np.pi*season),weekday>=5])
    x=np.column_stack([normal,calendar]).astype(np.float32)
    sets={};rows=[]
    for split,(start,end) in PERIODS.items():
        origins=np.array([t for t in range(max(WINDOWS)-1,len(frame)-1) if pd.Timestamp(start)<=frame.index[t+1]<=pd.Timestamp(end)])
        sets[split]={"origins":origins,"truth":frame[TARGETS].to_numpy()[origins+1],
            "y":normal[origins+1].astype(np.float32),"strict":frame.strict_no_imputation.to_numpy()[origins+1]}
        for t in origins:rows.append(dict(split=split,origin=str(frame.index[t].date()),
            history_start_56=str(frame.index[t-55].date()),target_date=str(frame.index[t+1].date())))
    pd.DataFrame(rows).to_csv(ROOT/"splits.csv",index=False)
    scaler={"targets":TARGETS,"mean":mean.tolist(),"std":scale.tolist(),"fit_start":"2020-01-01","fit_end":"2022-12-31","ddof":0}
    dump(ROOT/"scalers.json",scaler)
    return frame,x,sets,mean,scale


def inputs(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins])


class Predictor(nn.Module):
    def __init__(self,family):
        super().__init__()
        # Re-match parameter counts after shrinking the readout from 21 to 3 outputs.
        hidden=68 if family=="RNN" else 32
        self.core=nn.RNN(8,hidden,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,hidden,batch_first=True)
        self.drop=nn.Dropout(0.1);self.head=nn.Linear(hidden,3)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def forward(self,x):
        h,_=self.core(x)
        return x[:,-1,:3]+self.head(self.drop(h[:,-1]))


def metrics(pred,truth,scale,strict):
    error=np.asarray(pred,dtype=float)-truth
    mse=(error**2).mean(0);norm=mse/scale**2
    return {"loss":float(norm.mean()),"targets":{name:{"MSE":float(mse[j]),"RMSE":float(np.sqrt(mse[j])),
        "MAE":float(np.abs(error[:,j]).mean()),"standardised_MSE":float(norm[j]),
        "strict_target_MSE":float(np.mean(error[strict,j]**2)) if strict.any() else None}
        for j,name in enumerate(TARGETS)}}


def fit(family,length,lr,seed,x,data,mean,scale):
    tag=f"{family}_L{length}_lr{lr:g}_s{seed}"
    print("START",tag,flush=True)
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=Predictor(family)
    count=sum(p.numel() for p in model.parameters())
    assert count==(5511 if family=="RNN" else 5475)
    tensors={s:(torch.from_numpy(inputs(x,d["origins"],length)),torch.from_numpy(d["y"])) for s,d in data.items()}
    optimizer=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    rng=torch.Generator().manual_seed(seed+1000)
    history=[];best=float("inf");best_state=None;best_epoch=0;stale=0
    start=time.monotonic()
    for epoch in range(121):
        online=None
        if epoch:
            model.train();total=0.
            tx,ty=tensors["train"]
            for ids in torch.randperm(len(tx),generator=rng).split(64):
                optimizer.zero_grad(set_to_none=True)
                loss=nn.functional.mse_loss(model(tx[ids]),ty[ids]);assert torch.isfinite(loss)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                total+=loss.item()*len(ids)
            online=total/len(tx)
        # Both reported losses use eval mode, identical MSE, and no dropout/decay term.
        model.eval();evaluated={}
        with torch.no_grad():
            for split,(xx,yy) in tensors.items():evaluated[split]=nn.functional.mse_loss(model(xx),yy).item()
        history.append({"run":tag,"epoch":epoch,"train_eval_loss":evaluated["train"],"validation_eval_loss":evaluated["validation"],"online_training_loss":online})
        if evaluated["validation"]<best-1e-5:
            best=evaluated["validation"];best_epoch=epoch;best_state=copy.deepcopy(model.state_dict());stale=0
        else:stale+=1
        if epoch and epoch%30==0:print(f"EPOCH {tag} {epoch} train={evaluated['train']:.5f} val={evaluated['validation']:.5f}",flush=True)
        if stale>=15:break
    assert best_state is not None
    model.load_state_dict(best_state);model.eval()
    checkpoint=ROOT/"checkpoints"/(tag+".pt")
    torch.save({"state_dict":best_state,"family":family,"lookback":length,"lr":lr,"seed":seed,"horizon":1,
        "mean":mean.tolist(),"std":scale.tolist(),"best_epoch":best_epoch},checkpoint)
    scores={}
    with torch.no_grad():
        for split,(xx,_) in tensors.items():
            p=model(xx).numpy().astype(float)*scale+mean
            scores[split]=metrics(p,data[split]["truth"],scale,data[split]["strict"])
    row={"run":tag,"family":family,"lookback":length,"lr":lr,"seed":seed,"parameters":count,"best_epoch":best_epoch,
        "epochs":epoch,"train_loss":scores["train"]["loss"],"validation_loss":scores["validation"]["loss"],
        "seconds":time.monotonic()-start,"checkpoint":str(checkpoint.relative_to(ROOT))}
    print("DONE",json.dumps(row),flush=True)
    return row,history


def run():
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    (ROOT/"results").mkdir(exist_ok=True);(ROOT/"checkpoints").mkdir(exist_ok=True)
    frame,x,data,mean,scale=prepare()
    protocol={"forecast_horizon":1,"targets":TARGETS,"loss":"Mean next-day squared error over three variables standardised with training mean/std; no other horizon in loss",
        "reported_train_validation_loss":"Both evaluated on the complete respective sample set in model.eval(), without dropout, and without adding a weight penalty. AdamW decay affects fitting only.",
        "periods":PERIODS,"sample_counts":{s:len(d["origins"]) for s,d in data.items()},"lookbacks":WINDOWS,"learning_rates":LRS,"seeds":SEEDS,
        "validation_selection":"Mean next-day validation loss across three seeds; best-validation checkpoint per seed; initial persistence checkpoint eligible",
        "training":{"max_epochs":120,"early_stopping_patience":15,"optimizer":"AdamW","batch_size":64,"weight_decay":1e-4,"gradient_clip":1.,"dropout":0.1},
        "architectures":{"RNN":"one-layer tanh RNN, hidden 68, residual linear next-day output, 5511 parameters","LSTM":"one-layer LSTM, hidden 32, identical residual readout, 5475 parameters"},
        "inputs":"three target-series histories and weekday sin/cos, annual sin/cos, weekend; total generation includes independent farm",
        "price_units":"nominal GBP/MWh; no monthly CPI feature","test_evaluated_this_experiment":False,"Ridge_fitted":False,
        "source_data":"Frozen reconstructed dataset; data-vintage causal audit not performed",
        "script_sha256":digest(Path(__file__)),"torch":torch.__version__,"python":sys.version,"device":"CPU, two threads"}
    dump(ROOT/"PROTOCOL.json",protocol)
    print("SPLITS",protocol["sample_counts"],flush=True)
    rows=[];hist=[]
    for family,length,lr,seed in itertools.product(("RNN","LSTM"),WINDOWS,LRS,SEEDS):
        row,h=fit(family,length,lr,seed,x,data,mean,scale);rows.append(row);hist.extend(h)
        pd.DataFrame(rows).to_csv(ROOT/"results/training_runs.csv",index=False)
        pd.DataFrame(hist).to_csv(ROOT/"results/training_history.csv",index=False)
    runs=pd.DataFrame(rows)
    grid=runs.groupby(["family","lookback","lr"]).validation_loss.agg(["mean","std"]).reset_index()
    grid.to_csv(ROOT/"results/validation_grid.csv",index=False)
    selected={f:grid.loc[grid.family.eq(f)].sort_values(["mean","lookback","lr"]).iloc[0].to_dict() for f in ("RNN","LSTM")}
    dump(ROOT/"results/SELECTION_FROZEN.json",selected)
    result={"protocol":protocol,"selected":selected,"metrics":{},"training_seconds":float(runs.seconds.sum())}
    comparison=[];prediction_files={}
    for split,d in data.items():
        baseline=frame[TARGETS].to_numpy()[d["origins"]]
        scores={"Persistence":metrics(baseline,d["truth"],scale,d["strict"])}
        pred={"truth":d["truth"],"origins":d["origins"],"strict":d["strict"],"Persistence":baseline}
        for f,choice in selected.items():
            for seed in SEEDS:
                row=runs.loc[runs.family.eq(f)&runs.lookback.eq(choice["lookback"])&runs.lr.eq(choice["lr"])&runs.seed.eq(seed)].iloc[0]
                cp=torch.load(ROOT/row.checkpoint,weights_only=True)
                model=Predictor(f);model.load_state_dict(cp["state_dict"]);model.eval()
                xx=torch.from_numpy(inputs(x,d["origins"],int(choice["lookback"])))
                with torch.no_grad():p=model(xx).numpy().astype(float)*scale+mean
                name=f+"_seed"+str(seed);pred[name]=p;scores[name]=metrics(p,d["truth"],scale,d["strict"])
            pred[f+"_ensemble"]=np.mean([pred[f+"_seed"+str(s)] for s in SEEDS],axis=0)
            scores[f+"_ensemble"]=metrics(pred[f+"_ensemble"],d["truth"],scale,d["strict"])
        result["metrics"][split]=scores
        np.savez_compressed(ROOT/"results"/(split+"_predictions.npz"),**pred)
        for name in ("Persistence","RNN","LSTM"):
            vals=[scores[name+"_seed"+str(s)] for s in SEEDS] if name!="Persistence" else [scores[name]]
            losses=[v["loss"] for v in vals]
            comparison.append({"split":split,"model":name,"loss_mean":float(np.mean(losses)),"loss_seed_sd":float(np.std(losses,ddof=1)) if len(losses)>1 else 0.,
                "skill_vs_persistence":float(1-np.mean(losses)/scores["Persistence"]["loss"])})
        daily=pd.DataFrame({"origin":frame.index[d["origins"]],"target_date":frame.index[d["origins"]+1]})
        for j,target in enumerate(TARGETS):
            daily[target+"_actual"]=d["truth"][:,j]
            for name in ("Persistence","RNN_ensemble","LSTM_ensemble"):daily[target+"_"+name]=pred[name][:,j]
        daily.to_csv(ROOT/"results"/(split+"_predictions.csv"),index=False)
    table=pd.DataFrame(comparison);table.to_csv(ROOT/"results/LOSS_COMPARISON.csv",index=False)
    dump(ROOT/"results/RESULTS.json",result)
    print("SELECTED",json.dumps(selected),flush=True)
    print(table.to_string(index=False),flush=True)


if __name__=="__main__":run()
