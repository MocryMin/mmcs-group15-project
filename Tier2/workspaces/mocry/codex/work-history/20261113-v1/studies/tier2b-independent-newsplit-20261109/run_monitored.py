"""Three temporal splits, full-set loss after every optimiser update, val selection."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")

import copy
import csv
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/"tier1-candidate-20261107-v4.1-academic"/"inputs"
PREVIOUS=ROOT.parent/"tier2b-nextday-independent-20261109"
PERIODS={"train":("2022-01-01","2024-12-31"),"validation":("2025-01-01","2025-08-31"),"test":("2025-09-01","2026-08-31")}
SEEDS=[17,29,43]


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    inputs=ROOT/"inputs";inputs.mkdir(exist_ok=True)
    if (inputs/"model_daily.csv").exists():
        manifest=json.loads((inputs/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        assert sha(inputs/"model_daily.csv")==manifest["derived_sha256"]
        f=pd.read_csv(inputs/"model_daily.csv",parse_dates=["date"]).set_index("date")
    else:
        names=["daily_generation_total.csv","wind_farm_generation.csv","daily_demand.csv","daily_market_index_price.csv","date_quality.csv"]
        frozen=json.loads((SOURCE/"MANIFEST.json").read_text(encoding="utf-8"));manifest={"sources":{}}
        def read(name,date="date"):
            assert sha(SOURCE/name)==frozen[name]["sha256"]
            manifest["sources"][name]={"sha256":sha(SOURCE/name),"source":str(SOURCE/name)}
            d=pd.read_csv(SOURCE/name);d.index=pd.to_datetime(d.pop(date),utc=True).dt.tz_localize(None)
            assert d.index.is_unique
            return d.sort_index()
        total=read(names[0]).total_MW;wind=read(names[1]).wind_farm_MW
        demand=read(names[2],"startTime").demand;price=read(names[3])["avg_price_£_per_MWh"]
        strict=read(names[4]).strict_no_imputation.astype(str).str.lower().isin(["1","true"])
        assert all(s.index.equals(total.index) for s in (wind,demand,price,strict))
        f=pd.DataFrame({"generation_MW":total+wind,"demand_MW":demand,"price_GBP_MWh":price,
            "source_total_MW":total,"wind_farm_MW":wind,"strict_no_imputation":strict}).loc["2021-11-06":"2026-09-17"]
        f.to_csv(inputs/"model_daily.csv",index_label="date")
        manifest["derived_sha256"]=sha(inputs/"model_daily.csv");dump(inputs/"SOURCE_MANIFEST.json",manifest)
    assert f.index.equals(pd.date_range("2021-11-06","2026-09-17"))
    f["strict_no_imputation"]=f.strict_no_imputation.astype(str).str.lower().isin(["1","true"])
    train=f.loc[PERIODS["train"][0]:PERIODS["train"][1],TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy()
    y=(f[TARGETS].to_numpy()-mean)/scale
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([y,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32)
    data={};splits=[]
    for part,(a,b) in PERIODS.items():
        origins=np.array([t for t in range(55,len(f)-1) if pd.Timestamp(a)<=f.index[t+1]<=pd.Timestamp(b)])
        data[part]={"origins":origins,"y":y[origins+1].astype(np.float32),"truth":f[TARGETS].to_numpy()[origins+1],"strict":f.strict_no_imputation.to_numpy()[origins+1]}
        for t in origins:splits.append({"split":part,"origin":str(f.index[t].date()),"history_start_56":str(f.index[t-55].date()),"target_date":str(f.index[t+1].date())})
    assert {p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365}
    pd.DataFrame(splits).to_csv(ROOT/"splits.csv",index=False)
    dump(ROOT/"scalers.json",{"targets":TARGETS,"mean":mean.tolist(),"std":scale.tolist(),"fit_start":"2022-01-01","fit_end":"2024-12-31","ddof":0})
    return f,x,data,mean,scale


def fit(target,family,config,seed,x,data,mean,scale):
    j=TARGETS.index(target);length=int(config["lookback"]);lr=float(config["lr"])
    tag=f"{target}_{family}_L{length}_lr{lr:g}_s{seed}"
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=Predictor(family,j)
    count=sum(p.numel() for p in model.parameters());assert count==(5373 if family=="RNN" else 5409)
    tensors={p:(torch.from_numpy(windows(x,d["origins"],length)),torch.from_numpy(d["y"][:,j:j+1])) for p,d in data.items()}
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    generator=torch.Generator().manual_seed(seed+1000)
    best=float("inf");best_state=None;best_row=None;step=0;stale_epochs=0;began=time.monotonic()
    checkpoint=ROOT/"checkpoints"/(tag+".pt");log=ROOT/"step_logs"/(tag+".csv")
    fields=["run","target","family","seed","epoch","batch_index","global_step","batch_size_actual","samples_seen",
            "train_batch_loss","train_eval_loss","validation_eval_loss","test_eval_loss","best_validation_so_far","checkpoint_improved","elapsed_seconds"]
    handle=log.open("w",newline="",encoding="utf-8");writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
    def evaluate(epoch,batch_index,batch_size,samples_seen,batch_loss):
        nonlocal best,best_state,best_row
        model.eval();losses={}
        with torch.inference_mode():
            for part,(xx,yy) in tensors.items():losses[part]=nn.functional.mse_loss(model(xx),yy).item()
        # Test is logged, but never appears in checkpoint/early-stopping decisions.
        improved=losses["validation"]<best-1e-5
        row={"run":tag,"target":target,"family":family,"seed":seed,"epoch":epoch,"batch_index":batch_index,
            "global_step":step,"batch_size_actual":batch_size,"samples_seen":samples_seen,"train_batch_loss":batch_loss,
            "train_eval_loss":losses["train"],"validation_eval_loss":losses["validation"],"test_eval_loss":losses["test"],
            "best_validation_so_far":losses["validation"] if improved else best,"checkpoint_improved":improved,"elapsed_seconds":time.monotonic()-began}
        if improved:
            best=losses["validation"];best_state=copy.deepcopy(model.state_dict());best_row=row.copy()
            torch.save({"state_dict":best_state,"target":target,"target_index":j,"family":family,"lookback":length,"lr":lr,"seed":seed,
                "mean":mean.tolist(),"std":scale.tolist(),"best_epoch":epoch,"best_step":step,"best_validation_loss":best},checkpoint)
        writer.writerow(row);handle.flush()
        return row,improved
    try:
        first,_=evaluate(0,0,0,0,None)
        print("START",tag,"initial",first["train_eval_loss"],first["validation_eval_loss"],first["test_eval_loss"],flush=True)
        train_x,train_y=tensors["train"];n=len(train_x)
        for epoch in range(1,121):
            improved_epoch=False;samples_seen=(epoch-1)*n
            for batch_index,ids in enumerate(torch.randperm(n,generator=generator).split(64),1):
                model.train();opt.zero_grad(set_to_none=True)
                prediction=model(train_x[ids]);assert prediction.shape==train_y[ids].shape
                batch_loss=nn.functional.mse_loss(prediction,train_y[ids]);assert torch.isfinite(batch_loss)
                batch_loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
                step+=1;samples_seen+=len(ids)
                last,improved=evaluate(epoch,batch_index,len(ids),samples_seen,float(batch_loss.item()))
                improved_epoch|=improved
                if step%100==0:print(f"STEP {tag} {step} E{epoch} train={last['train_eval_loss']:.5f} val={last['validation_eval_loss']:.5f} test={last['test_eval_loss']:.5f} bestVal={best:.5f}",flush=True)
            stale_epochs=0 if improved_epoch else stale_epochs+1
            if stale_epochs>=15:break
        assert best_state is not None and best_row is not None
        row={"run":tag,"target":target,"family":family,"seed":seed,"lookback":length,"lr":lr,"parameters":count,
            "best_epoch":best_row["epoch"],"best_step":best_row["global_step"],"epochs":epoch,"steps":step,
            "best_train_loss":best_row["train_eval_loss"],"best_validation_loss":best_row["validation_eval_loss"],"test_loss_at_val_checkpoint":best_row["test_eval_loss"],
            "last_train_loss":last["train_eval_loss"],"last_validation_loss":last["validation_eval_loss"],"last_test_loss":last["test_eval_loss"],
            "seconds":time.monotonic()-began,"step_log":str(log.relative_to(ROOT)),"checkpoint":str(checkpoint.relative_to(ROOT))}
        print("DONE",json.dumps(row),flush=True)
        return row
    finally:handle.close()


def score(pred,truth,sd):
    e=np.asarray(pred,dtype=float).ravel()-truth
    return {"loss":float(np.mean((e/sd)**2)),"MSE":float(np.mean(e**2)),"RMSE":float(np.sqrt(np.mean(e**2))),"MAE":float(np.abs(e).mean())}


def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    for folder in ("results","checkpoints","step_logs"):(ROOT/folder).mkdir(exist_ok=True)
    f,x,data,mean,scale=prepare()
    frozen_path=ROOT/"REFERENCE_CONFIGS.json"
    if not frozen_path.exists():frozen_path.write_bytes((PREVIOUS/"results/SELECTION_FROZEN.json").read_bytes())
    configs=json.loads(frozen_path.read_text(encoding="utf-8"))
    protocol={"targets":TARGETS,"horizon":1,"independent_targets":True,"periods":PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},
        "context_only":"2021-11-06 through 2021-12-31; no pre-2022 target fitting","unused_tail":"2026-09-01 through 2026-09-17",
        "batch_size":64,"steps_per_epoch":18,"batch_layout":"17 batches of 64 and one batch of 8; each epoch shuffles origins only, never sequence order",
        "max_epochs":120,"max_steps_per_fit":2160,"epoch_zero":"Initial evaluation without optimiser update",
        "logging":"Every optimiser step: full train, validation and test MSE in eval mode; CSV flush after every row; batch training loss separately labelled",
        "checkpoint":"Minimum validation MSE at any step, min_delta=1e-5; no test comparison in selection",
        "early_stop":"At epoch end, stop after 15 complete consecutive epochs with no new validation minimum; not 15 steps",
        "configurations":"Reuse six previously selected lookback/lr configurations; reset all weights; no hyperparameter search in this round",
        "seeds":SEEDS,"expected_fits":18,"optimizer":"AdamW","weight_decay":1e-4,"clip_grad_norm":1.,"dropout":.1,
        "loss":"Single target next-day MSE standardised by training-2022-24 std; same scaler for all splits; no penalty in displayed MSE",
        "test_status":"Monitored held-out test, not a blind test; some 2025 dates were inspected in earlier experiments. Test does not influence gradient, checkpoint or early stopping.",
        "data_vintage":"Frozen post-hoc repaired data; publication/reconstruction vintage not audited","external_features":False,"MPC_evaluated":False,
        "price":"nominal GBP/MWh; no future monthly CPI","torch":torch.__version__,"python":sys.version,"device":"CPU two threads",
        "source_hashes":{"run_monitored.py":sha(Path(__file__)),"model.py":sha(ROOT/"model.py"),"REFERENCE_CONFIGS.json":sha(frozen_path)}}
    dump(ROOT/"PROTOCOL.json",protocol);print("PROTOCOL",json.dumps(protocol,ensure_ascii=False),flush=True)
    rows=[]
    for target in TARGETS:
        for family in ("RNN","LSTM"):
            for seed in SEEDS:
                rows.append(fit(target,family,configs[target+"|"+family],seed,x,data,mean,scale))
                pd.DataFrame(rows).to_csv(ROOT/"results/training_runs.csv",index=False)
    runs=pd.DataFrame(rows);result={"protocol":protocol,"runs":rows,"metrics":{},"runtime_seconds":float(runs.seconds.sum())};summary=[]
    for part,d in data.items():
        exported={"truth":d["truth"],"origins":d["origins"]};metrics={}
        for j,target in enumerate(TARGETS):
            base=f[TARGETS].to_numpy()[d["origins"],j]
            scores={"Persistence":score(base,d["truth"][:,j],scale[j])};exported[target+"|Persistence"]=base
            for family in ("RNN","LSTM"):
                config=configs[target+"|"+family];xx=torch.from_numpy(windows(x,d["origins"],int(config["lookback"])))
                for seed in SEEDS:
                    row=runs.loc[runs.target.eq(target)&runs.family.eq(family)&runs.seed.eq(seed)].iloc[0]
                    cp=torch.load(ROOT/row.checkpoint,weights_only=True);m=Predictor(family,j);m.load_state_dict(cp["state_dict"]);m.eval()
                    with torch.inference_mode():p=m(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
                    name=family+"_seed"+str(seed);scores[name]=score(p,d["truth"][:,j],scale[j]);exported[target+"|"+name]=p
            metrics[target]=scores
            for family in ("Persistence","RNN","LSTM"):
                vals=[scores[family+"_seed"+str(s)] for s in SEEDS] if family!="Persistence" else [scores[family]]
                fields={}
                for key in ("loss","MSE","RMSE","MAE"):
                    z=[v[key] for v in vals];fields[key+"_mean"]=float(np.mean(z));fields[key+"_seed_sd"]=float(np.std(z,ddof=1)) if len(z)>1 else 0.
                summary.append({"target":target,"split":part,"model":family,**fields,"skill_vs_persistence":float(1-fields["loss_mean"]/scores["Persistence"]["loss"])})
        result["metrics"][part]=metrics;np.savez_compressed(ROOT/"results"/(part+"_predictions.npz"),**exported)
    pd.DataFrame(summary).to_csv(ROOT/"results/LOSS_COMPARISON.csv",index=False);dump(ROOT/"results/RESULTS.json",result)
    print("COMPLETE",pd.DataFrame(summary)[["target","split","model","loss_mean","loss_seed_sd"]].to_string(index=False),flush=True)


if __name__=="__main__":main()
