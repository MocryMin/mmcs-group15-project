"""Independent next-day forecasts: separate target parameters, losses and selection."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")

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
PREVIOUS=ROOT.parent/"tier2b-nextday-rnn-lstm-20261109"
TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]
WINDOWS=[28,56]
LRS=[0.001,0.003]
SEEDS=[17,29,43]


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    inputs=ROOT/"inputs";inputs.mkdir(exist_ok=True)
    if not (inputs/"model_daily.csv").exists():
        prior=json.loads((PREVIOUS/"inputs/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        assert sha(PREVIOUS/"inputs/model_daily.csv")==prior["derived_sha256"]
        for name in ("model_daily.csv","SOURCE_MANIFEST.json"):
            (inputs/name).write_bytes((PREVIOUS/"inputs"/name).read_bytes())
    manifest=json.loads((inputs/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert sha(inputs/"model_daily.csv")==manifest["derived_sha256"]
    frame=pd.read_csv(inputs/"model_daily.csv",parse_dates=["date"]).set_index("date")
    assert frame.index.equals(pd.date_range("2020-01-01","2023-12-31"))
    frame["strict_no_imputation"]=frame.strict_no_imputation.astype(str).str.lower().isin(["1","true"])
    train=frame.loc["2020":"2022",TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy()
    y=(frame[TARGETS].to_numpy()-mean)/scale
    weekday=frame.index.dayofweek.to_numpy()
    season=(frame.index.dayofyear.to_numpy()-1)/np.where(frame.index.is_leap_year,366,365)
    x=np.column_stack([y,np.sin(2*np.pi*weekday/7),np.cos(2*np.pi*weekday/7),
                       np.sin(2*np.pi*season),np.cos(2*np.pi*season),weekday>=5]).astype(np.float32)
    data={};splits=[]
    for part,(start,end) in {"train":("2020-01-01","2022-12-31"),"validation":("2023-01-01","2023-12-31")}.items():
        origins=np.array([t for t in range(55,len(frame)-1) if pd.Timestamp(start)<=frame.index[t+1]<=pd.Timestamp(end)])
        data[part]={"origins":origins,"y":y[origins+1].astype(np.float32),"truth":frame[TARGETS].to_numpy()[origins+1],
                    "strict":frame.strict_no_imputation.to_numpy()[origins+1]}
        for t in origins:splits.append({"split":part,"origin":str(frame.index[t].date()),
            "history_start_56":str(frame.index[t-55].date()),"target_date":str(frame.index[t+1].date())})
    pd.DataFrame(splits).to_csv(ROOT/"splits.csv",index=False)
    dump(ROOT/"scalers.json",{"targets":TARGETS,"mean":mean.tolist(),"std":scale.tolist(),"fit_start":"2020-01-01","fit_end":"2022-12-31","ddof":0})
    return frame,x,data,mean,scale


def windows(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins])


class Predictor(nn.Module):
    def __init__(self,family,target_index):
        super().__init__();self.target_index=target_index
        hidden=68 if family=="RNN" else 32
        self.core=nn.RNN(8,hidden,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,hidden,batch_first=True)
        self.dropout=nn.Dropout(.1);self.head=nn.Linear(hidden,1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def forward(self,x):
        hidden,_=self.core(x)
        return x[:,-1,self.target_index:self.target_index+1]+self.head(self.dropout(hidden[:,-1]))


def fit(family,target,length,lr,seed,x,data,mean,scale):
    j=TARGETS.index(target);tag=f"{target}_{family}_L{length}_lr{lr:g}_s{seed}"
    print("START",tag,flush=True)
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=Predictor(family,j);nparams=sum(p.numel() for p in model.parameters())
    assert nparams==(5373 if family=="RNN" else 5409)
    arrays={part:(torch.from_numpy(windows(x,d["origins"],length)),torch.from_numpy(d["y"][:,j:j+1])) for part,d in data.items()}
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    rng=torch.Generator().manual_seed(seed+1000)
    best=float("inf");best_epoch=0;state=None;stale=0;history=[];began=time.monotonic()
    for epoch in range(121):
        online=None
        if epoch:
            model.train();total=0.;tx,ty=arrays["train"]
            for ids in torch.randperm(len(tx),generator=rng).split(64):
                opt.zero_grad(set_to_none=True)
                predicted=model(tx[ids]);assert predicted.shape==ty[ids].shape
                loss=nn.functional.mse_loss(predicted,ty[ids]);assert torch.isfinite(loss)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
                total+=loss.item()*len(ids)
            online=total/len(tx)
        model.eval();losses={}
        with torch.no_grad():
            for part,(xx,yy) in arrays.items():losses[part]=nn.functional.mse_loss(model(xx),yy).item()
        history.append({"run":tag,"epoch":epoch,"train_eval_loss":losses["train"],"validation_eval_loss":losses["validation"],"online_train_loss":online})
        if losses["validation"]<best-1e-5:
            best=losses["validation"];best_epoch=epoch;state=copy.deepcopy(model.state_dict());stale=0
        else:stale+=1
        if epoch and epoch%40==0:print(f"EPOCH {tag} {epoch} train={losses['train']:.5f} val={losses['validation']:.5f}",flush=True)
        if stale>=15:break
    assert state is not None
    model.load_state_dict(state);model.eval()
    with torch.no_grad():
        scores={part:nn.functional.mse_loss(model(xx),yy).item() for part,(xx,yy) in arrays.items()}
    checkpoint=ROOT/"checkpoints"/(tag+".pt")
    torch.save({"state_dict":state,"family":family,"target":target,"target_index":j,"lookback":length,"lr":lr,"seed":seed,
        "mean":mean.tolist(),"std":scale.tolist(),"best_epoch":best_epoch,"horizon":1},checkpoint)
    row={"run":tag,"target":target,"family":family,"lookback":length,"lr":lr,"seed":seed,"parameters":nparams,
        "best_epoch":best_epoch,"epochs":epoch,"train_loss":scores["train"],"validation_loss":scores["validation"],
        "last_train_loss":history[-1]["train_eval_loss"],"last_validation_loss":history[-1]["validation_eval_loss"],
        "seconds":time.monotonic()-began,"checkpoint":str(checkpoint.relative_to(ROOT))}
    print("DONE",json.dumps(row),flush=True)
    return row,history


def score(pred,truth,sd,strict):
    e=np.asarray(pred,dtype=float).reshape(-1)-truth
    return {"loss":float(np.mean((e/sd)**2)),"MSE":float(np.mean(e**2)),"RMSE":float(np.sqrt(np.mean(e**2))),
        "MAE":float(np.abs(e).mean()),"strict_target_loss":float(np.mean((e[strict]/sd)**2)) if strict.any() else None}


def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    (ROOT/"results").mkdir(exist_ok=True);(ROOT/"checkpoints").mkdir(exist_ok=True)
    frame,x,data,mean,scale=prepare()
    protocol={"mode":"independent target models, no shared weights or multi-task loss","horizon":1,"targets":TARGETS,
        "features":"All models retain the same three observed histories and five calendar features, but output one target only",
        "loss":"Single target next-day MSE standardised by that target's training std; train and val use identical eval-mode criterion",
        "periods":{"train":"2020-2022","validation":"2023"},"sample_counts":{p:len(d["origins"]) for p,d in data.items()},
        "lookbacks":WINDOWS,"learning_rates":LRS,"seeds":SEEDS,"expected_fits":72,
        "selection":"Per-target, per-family lowest three-seed mean validation loss; per-seed best validation checkpoint; epoch-zero persistence eligible",
        "architecture":{"RNN":"single tanh layer, hidden 68, 5373 parameters","LSTM":"single LSTM layer, hidden 32, 5409 parameters"},
        "training":{"optimizer":"AdamW","weight_decay":1e-4,"dropout":.1,"batch_size":64,"max_epochs":120,"patience":15,"clip_grad_norm":1.},
        "baseline":"target tomorrow equals target today, scored on identical origins",
        "test_evaluated":False,"external_features":False,"Ridge_fitted":False,"MPC_evaluated":False,
        "joint_comparison_caveat":"Three independent models use about three times the total parameters of one joint model; differences are not a capacity-controlled causal estimate of negative transfer.",
        "data_vintage":"Frozen repaired historical data, source publication/reconstruction vintages not audited",
        "source_script_sha256":sha(Path(__file__)),"torch":torch.__version__,"python":sys.version,"device":"CPU, two threads"}
    dump(ROOT/"PROTOCOL.json",protocol)
    print("SAMPLES",protocol["sample_counts"],flush=True)
    rows=[];hist=[]
    for target,family,length,lr,seed in itertools.product(TARGETS,("RNN","LSTM"),WINDOWS,LRS,SEEDS):
        row,h=fit(family,target,length,lr,seed,x,data,mean,scale);rows.append(row);hist.extend(h)
        pd.DataFrame(rows).to_csv(ROOT/"results/training_runs.csv",index=False)
        pd.DataFrame(hist).to_csv(ROOT/"results/training_history.csv",index=False)
    runs=pd.DataFrame(rows)
    grid=runs.groupby(["target","family","lookback","lr"]).validation_loss.agg(["mean","std"]).reset_index()
    grid.to_csv(ROOT/"results/validation_grid.csv",index=False)
    selected={}
    for target,family in itertools.product(TARGETS,("RNN","LSTM")):
        selected[target+"|"+family]=grid.loc[grid.target.eq(target)&grid.family.eq(family)].sort_values(["mean","lookback","lr"]).iloc[0].to_dict()
    dump(ROOT/"results/SELECTION_FROZEN.json",selected)
    result={"protocol":protocol,"selected":selected,"metrics":{},"training_seconds":float(runs.seconds.sum())}
    comparison=[]
    for part,d in data.items():
        predictions={"truth":d["truth"],"origins":d["origins"],"strict":d["strict"]};metrics={}
        csv=pd.DataFrame({"origin":frame.index[d["origins"]],"target_date":frame.index[d["origins"]+1]})
        for j,target in enumerate(TARGETS):
            truth=d["truth"][:,j];persistence=frame[TARGETS].to_numpy()[d["origins"],j]
            scores={"Persistence":score(persistence,truth,scale[j],d["strict"])}
            predictions[target+"|Persistence"]=persistence;csv[target+"|actual"]=truth;csv[target+"|Persistence"]=persistence
            for family in ("RNN","LSTM"):
                choice=selected[target+"|"+family]
                xx=torch.from_numpy(windows(x,d["origins"],int(choice["lookback"])))
                group=[]
                for seed in SEEDS:
                    row=runs.loc[runs.target.eq(target)&runs.family.eq(family)&runs.lookback.eq(choice["lookback"])&runs.lr.eq(choice["lr"])&runs.seed.eq(seed)].iloc[0]
                    cp=torch.load(ROOT/row.checkpoint,weights_only=True)
                    model=Predictor(family,j);model.load_state_dict(cp["state_dict"]);model.eval()
                    with torch.no_grad():p=model(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
                    name=family+"_seed"+str(seed)
                    scores[name]=score(p,truth,scale[j],d["strict"]);predictions[target+"|"+name]=p;group.append(p)
                predictions[target+"|"+family+"_ensemble"]=np.mean(group,axis=0)
                csv[target+"|"+family+"_ensemble"]=np.mean(group,axis=0)
            metrics[target]=scores
            for name in ("Persistence","RNN","LSTM"):
                vals=[scores[name+"_seed"+str(s)] for s in SEEDS] if name!="Persistence" else [scores[name]]
                stats={}
                for metric in ("loss","MSE","RMSE","MAE"):
                    numbers=[v[metric] for v in vals];stats[metric+"_mean"]=float(np.mean(numbers));stats[metric+"_seed_sd"]=float(np.std(numbers,ddof=1)) if len(numbers)>1 else 0.
                comparison.append({"target":target,"split":part,"model":name,**stats,"skill_vs_persistence":float(1-stats["loss_mean"]/scores["Persistence"]["loss"])})
        result["metrics"][part]=metrics
        np.savez_compressed(ROOT/"results"/(part+"_predictions.npz"),**predictions)
        csv.to_csv(ROOT/"results"/(part+"_predictions.csv"),index=False)
    table=pd.DataFrame(comparison);table.to_csv(ROOT/"results/LOSS_COMPARISON.csv",index=False)
    dump(ROOT/"results/RESULTS.json",result)
    print("SELECTED",json.dumps(selected),flush=True)
    print(table[["target","split","model","loss_mean","loss_seed_sd","skill_vs_persistence"]].to_string(index=False),flush=True)


if __name__=="__main__":main()
