"""Chronological, parameter-matched vanilla RNN/LSTM forecasting pilot."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import random
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "tier1-candidate-20261107-v4.1-academic" / "inputs"
FILES = ["daily_generation_total.csv", "daily_demand.csv", "wind_farm_generation.csv",
         "daily_market_index_price.csv", "date_quality.csv"]
TARGETS = ["generation_MW", "demand_MW", "price_GBP_MWh"]
H = 7
WINDOWS = [28, 56]
LRS = [0.001, 0.003]
SEEDS = [17, 29, 43]
MAX_EPOCHS = 120
PATIENCE = 15
SPLITS = {"train": ("2020-01-01", "2022-12-31"),
          "validation": ("2023-01-01", "2023-12-31"),
          "test": ("2024-01-01", "2025-12-31")}


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    folder = ROOT / "inputs"
    folder.mkdir(exist_ok=True)
    frozen = json.loads((SOURCE / "MANIFEST.json").read_text(encoding="utf-8"))
    manifest = {}
    for name in FILES:
        source = SOURCE / name
        assert sha(source) == frozen[name]["sha256"], name
        target = folder / name
        if target.exists():
            assert sha(target) == sha(source), name
        else:
            target.write_bytes(source.read_bytes())
        manifest[name] = dict(sha256=sha(target), source=str(source))
    dump(folder / "MANIFEST.json", manifest)

    def load(name, date="date"):
        f = pd.read_csv(folder / name)
        f.index = pd.to_datetime(f.pop(date), utc=True).dt.tz_localize(None)
        assert f.index.is_unique
        return f.sort_index()

    gen = load(FILES[0]).total_MW
    demand = load(FILES[1], "startTime").demand
    wind = load(FILES[2]).wind_farm_MW
    price = load(FILES[3])["avg_price_£_per_MWh"]
    quality = load(FILES[4]).strict_no_imputation.astype(str).str.lower().isin(["true", "1"])
    dates = pd.date_range("2020-01-01", "2026-09-17")
    assert all(s.index.equals(dates) for s in (gen, demand, wind, price, quality))
    frame = pd.DataFrame(dict(generation_MW=gen + wind, demand_MW=demand,
                              price_GBP_MWh=price, strict_no_imputation=quality), index=dates)
    assert np.isfinite(frame[TARGETS]).all().all()
    assert (frame[TARGETS[:2]] >= 0).all().all()
    frame.to_csv(folder / "model_daily.csv", index_label="date")
    train = frame.loc[SPLITS["train"][0]:SPLITS["train"][1], TARGETS]
    mean, scale = train.mean().to_numpy(), train.std(ddof=0).to_numpy()
    assert np.all(scale > 0)
    y = (frame[TARGETS].to_numpy() - mean) / scale
    day = frame.index.dayofweek.to_numpy()
    yearphase = (frame.index.dayofyear.to_numpy() - 1) / np.where(frame.index.is_leap_year, 366, 365)
    calendar = np.column_stack([np.sin(2*np.pi*day/7), np.cos(2*np.pi*day/7),
                                np.sin(2*np.pi*yearphase), np.cos(2*np.pi*yearphase), day >= 5])
    x = np.column_stack([y, calendar]).astype(np.float32)
    samples = {}
    rows = []
    for split, (start, end) in SPLITS.items():
        origins = np.array([t for t in range(max(WINDOWS)-1, len(frame)-H)
                            if frame.index[t+1] >= pd.Timestamp(start)
                            and frame.index[t+H] <= pd.Timestamp(end)])
        assert len(origins)
        samples[split] = dict(origins=origins,
                             y=np.stack([y[t+1:t+H+1] for t in origins]).astype(np.float32),
                             truth=np.stack([frame[TARGETS].to_numpy()[t+1:t+H+1] for t in origins]),
                             strict=np.stack([quality.to_numpy()[t+1:t+H+1] for t in origins]))
        for t in origins:
            rows.append(dict(split=split, origin=frame.index[t].date(),
                             input_start_56=frame.index[t-55].date(),
                             first_target=frame.index[t+1].date(), last_target=frame.index[t+H].date()))
    splits = pd.DataFrame(rows)
    splits.to_csv(ROOT / "splits.csv", index=False)
    target_sets = {}
    for split, group in splits.groupby("split"):
        target_sets[split] = set().union(*(set(pd.date_range(a,b))
                                         for a,b in zip(group.first_target, group.last_target)))
    assert all(not (target_sets[a] & target_sets[b]) for a,b in itertools.combinations(SPLITS,2))
    scalers = dict(mean=dict(zip(TARGETS,mean)), std=dict(zip(TARGETS,scale)),
                   fit_start=SPLITS["train"][0], fit_end=SPLITS["train"][1], ddof=0)
    dump(ROOT / "scalers.json", scalers)
    return frame, x, samples, mean, scale, manifest


class Forecaster(nn.Module):
    def __init__(self, family, features=8):
        super().__init__()
        hidden = 64 if family == "RNN" else 32
        self.core = nn.RNN(features, hidden, batch_first=True, nonlinearity="tanh") if family == "RNN" else nn.LSTM(features, hidden, batch_first=True)
        self.dropout = nn.Dropout(0.1)
        self.head = nn.Linear(hidden, H*3)
        nn.init.zeros_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    def forward(self, x):
        hidden, _ = self.core(x)
        change = self.head(self.dropout(hidden[:, -1])).reshape(-1,H,3)
        return x[:, -1, :3].unsqueeze(1) + change


def windows(x, origins, length):
    return np.stack([x[t-length+1:t+1] for t in origins]).astype(np.float32)


def clip_normal(pred, mean, scale):
    result = pred.clone()
    lower = torch.tensor((-mean[:2]/scale[:2]).astype(np.float32))
    result[:, :, :2] = torch.maximum(result[:, :, :2], lower)
    return result


def denormalise(pred, mean, scale):
    ans = np.asarray(pred, dtype=float) * scale + mean
    ans[:, :, :2] = np.maximum(ans[:, :, :2], 0)
    assert np.isfinite(ans).all()
    return ans


def fit(family, length, lr, seed, x, data, mean, scale):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    tag = f"{family}_L{length}_lr{lr:g}_s{seed}"
    print("START", tag, flush=True)
    model = Forecaster(family)
    count = sum(p.numel() for p in model.parameters())
    assert count == (6101 if family == "RNN" else 6069), count
    tx = torch.from_numpy(windows(x,data["train"]["origins"],length))
    ty = torch.from_numpy(data["train"]["y"])
    vx = torch.from_numpy(windows(x,data["validation"]["origins"],length))
    vy = torch.from_numpy(data["validation"]["y"])
    optimizer = torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    generator = torch.Generator().manual_seed(seed+1000)
    best = float("inf"); best_state = None; stale = 0; history = []; best_epoch=0
    started = time.monotonic()
    for epoch in range(1,MAX_EPOCHS+1):
        model.train(); total=0.
        for ids in torch.randperm(len(tx),generator=generator).split(64):
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.mse_loss(model(tx[ids]),ty[ids])
            assert torch.isfinite(loss)
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step(); total += loss.item()*len(ids)
        model.eval()
        with torch.no_grad():
            val = nn.functional.mse_loss(clip_normal(model(vx),mean,scale),vy).item()
        history.append(dict(run=tag,epoch=epoch,train_mse=total/len(tx),validation_mse=val))
        if val < best-1e-5:
            best=val;best_epoch=epoch;stale=0;best_state=copy.deepcopy(model.state_dict())
        else:
            stale+=1
        if epoch%30 == 0:
            print(f"EPOCH {tag} {epoch} val={val:.5f} best={best:.5f}",flush=True)
        if stale>=PATIENCE:
            break
    assert best_state is not None
    model.load_state_dict(best_state);model.eval()
    checkpoint = ROOT/"checkpoints"/(tag+".pt")
    checkpoint.parent.mkdir(exist_ok=True)
    torch.save(dict(state_dict=best_state,family=family,lookback=length,lr=lr,seed=seed,
                    horizon=H,features=8,targets=TARGETS,mean=mean.tolist(),scale=scale.tolist(),
                    nominal_price=True,best_epoch=best_epoch),checkpoint)
    row=dict(run=tag,family=family,lookback=length,lr=lr,seed=seed,parameters=count,
             best_epoch=best_epoch,epochs=epoch,validation_standardised_mse=best,
             seconds=time.monotonic()-started,checkpoint=str(checkpoint.relative_to(ROOT)))
    print("DONE",json.dumps(row),flush=True)
    return row,history


def metrics(pred, truth, strict, mean, scale):
    err=pred-truth
    ans=dict(standardised_mse=float(np.mean((err/scale)**2)),targets={})
    for j,name in enumerate(TARGETS):
        e=err[:,:,j]
        ans["targets"][name]=dict(MAE=float(np.abs(e).mean()),RMSE=float(np.sqrt((e*e).mean())),
            horizons={str(k+1):dict(MAE=float(np.abs(e[:,k]).mean()),RMSE=float(np.sqrt(np.mean(e[:,k]**2)))) for k in range(H)},
            strict_target_MAE=float(np.abs(e[strict]).mean()) if strict.any() else None,
            strict_target_RMSE=float(np.sqrt(np.mean(e[strict]**2))) if strict.any() else None,
            strict_target_count=int(strict.sum()))
    return ans


def baseline_predictions(frame, x, data, mean, scale):
    preds={s:{} for s in ("validation","test")}
    y=frame[TARGETS].to_numpy()
    for split in preds:
        ts=data[split]["origins"]
        preds[split]["Persistence"]=np.stack([np.repeat(y[t][None,:],H,axis=0) for t in ts])
        preds[split]["SeasonalNaive"]=np.stack([np.stack([y[t+k-7] for k in range(1,H+1)]) for t in ts])
    # A transparent linear baseline with exactly the same 56-day information window.
    arrays={s:windows(x,d["origins"],56).reshape(len(d["origins"]),-1).astype(float) for s,d in data.items()}
    center=arrays["train"].mean(axis=0)
    a=arrays["train"]-center
    origins=data["train"]["origins"]
    residual=data["train"]["y"]-x[origins,:3,None].transpose(0,2,1)
    b=residual.reshape(len(origins),-1).astype(float);bcenter=b.mean(axis=0);b-=bcenter
    matrix=a.T@a; cross=a.T@b
    rows=[]; ridge_candidates={}
    for alpha in (0.1,1.,10.,100.):
        w=cho_solve(cho_factor(matrix+alpha*np.eye(matrix.shape[0]),lower=True),cross)
        normal=((arrays["validation"]-center)@w+bcenter).reshape(-1,H,3)+x[data["validation"]["origins"],:3,None].transpose(0,2,1)
        p=denormalise(normal,mean,scale)
        score=float(np.mean(((p-data["validation"]["truth"])/scale)**2))
        rows.append(dict(alpha=alpha,validation_standardised_mse=score));ridge_candidates[alpha]=w
    best=min(rows,key=lambda row:row["validation_standardised_mse"])
    for split in preds:
        normal=((arrays[split]-center)@ridge_candidates[best["alpha"]]+bcenter).reshape(-1,H,3)+x[data[split]["origins"],:3,None].transpose(0,2,1)
        preds[split]["Ridge"]=denormalise(normal,mean,scale)
    np.savez_compressed(ROOT/"checkpoints"/"Ridge.npz",coef=ridge_candidates[best["alpha"]],feature_center=center,
                        target_center=bcenter,alpha=best["alpha"],mean=mean,scale=scale)
    return preds,dict(selected=best,candidates=rows,lookback=56)


def main():
    start=time.monotonic()
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"checkpoints").mkdir(exist_ok=True)
    frame,x,data,mean,scale,manifest=prepare()
    metadata=dict(horizon_days=H,lookbacks=WINDOWS,learning_rates=LRS,seeds=SEEDS,
        train_cutoff=SPLITS["train"][1],splits={s:dict(start=a,end=b,samples=len(data[s]["origins"]),
                first_origin=str(frame.index[data[s]["origins"][0]].date()),last_origin=str(frame.index[data[s]["origins"][-1]].date())) for s,(a,b) in SPLITS.items()},
        inputs=[*TARGETS,"weekday_sin","weekday_cos","year_sin","year_cos","weekend"],
        price_units="nominal GBP/MWh; no full-month CPI adjustment in forecast inputs",
        supply="daily_generation_total + independent wind_farm_generation; daily mean MW",
        validation_criterion="mean validation squared error after train-only target standardisation; equal target/horizon weights; average across three seeds",
        models="one-layer tanh RNN(64) vs one-layer LSTM(32), matched linear residual readout; 0.1 final-state dropout",
        training=dict(optimizer="AdamW",batch_size=64,weight_decay=1e-4,gradient_clip=1.,max_epochs=MAX_EPOCHS,early_stopping=PATIENCE),
        evaluation="Fixed weights after training; forecast origins roll daily with newly observed history. All forecast targets stay inside their split; no refit after validation.",
        limitations=["Frozen retrospectively repaired dataset. Source reconstruction/publication vintages were not re-created, so this is not an audited real-time data-vintage backtest.",
                     "Strict-target metrics exclude estimated/reconstructed target dates but retain the same calendar and input windows; they do not remove all reconstruction influence in inputs.",
                     "2026 partial year unused. No external data, fuel-disaggregated covariates or MPC profit experiment in this pilot."],
        software=dict(python=sys.version,torch=torch.__version__,numpy=np.__version__,pandas=pd.__version__,platform=platform.platform(),device="CPU",threads=2),
        input_hashes=manifest,script_sha256=sha(Path(__file__)))
    if "--evaluate-only" in sys.argv:
        training_protocol=json.loads((ROOT/"PROTOCOL_TRAINING.json").read_text(encoding="utf-8"))
        metadata["training_script_sha256"]=training_protocol["script_sha256"]
        metadata["evaluation_note"]="Only quality-label parsing changed after training; numeric input features, targets, models, validation selection and saved weights unchanged."
    dump(ROOT/"PROTOCOL.json",metadata)
    print("SPLITS",json.dumps(metadata["splits"]),flush=True)
    runs=[];hist=[]
    if "--evaluate-only" in sys.argv:
        runs=pd.read_csv(ROOT/"results"/"training_runs.csv").to_dict("records")
        assert len(runs)==24
    else:
        for family,length,lr,seed in itertools.product(("RNN","LSTM"),WINDOWS,LRS,SEEDS):
            row,history=fit(family,length,lr,seed,x,data,mean,scale)
            runs.append(row);hist.extend(history)
            pd.DataFrame(runs).to_csv(ROOT/"results"/"training_runs.csv",index=False)
            pd.DataFrame(hist).to_csv(ROOT/"results"/"training_history.csv",index=False)
    trial=pd.DataFrame(runs)
    groups=trial.groupby(["family","lookback","lr"]).validation_standardised_mse.agg(["mean","std"]).reset_index()
    groups.to_csv(ROOT/"results"/"validation_grid.csv",index=False)
    selected={family:groups.loc[groups.family.eq(family)].sort_values(["mean","lookback","lr"]).iloc[0].to_dict() for family in ("RNN","LSTM")}
    # Freeze selection before making any test prediction or reading a test metric.
    frozen=ROOT/"results"/"SELECTION_FROZEN.json"
    if "--evaluate-only" in sys.argv:
        old=json.loads(frozen.read_text(encoding="utf-8"))["selected"]
        assert all(selected[f]["lookback"]==old[f]["lookback"] and selected[f]["lr"]==old[f]["lr"] and np.isclose(selected[f]["mean"],old[f]["mean"],atol=1e-12,rtol=0) for f in selected)
    else:
        dump(frozen,dict(selected=selected,criterion=metadata["validation_criterion"],test_metrics_accessed=False))
    preds,ridge=baseline_predictions(frame,x,data,mean,scale)
    for family,choice in selected.items():
        chosen=trial.loc[trial.family.eq(family)&trial.lookback.eq(choice["lookback"])&trial.lr.eq(choice["lr"])]
        for _,row in chosen.iterrows():
            checkpoint=torch.load(ROOT/row.checkpoint,weights_only=True)
            model=Forecaster(family);model.load_state_dict(checkpoint["state_dict"]);model.eval()
            for split in preds:
                xx=torch.from_numpy(windows(x,data[split]["origins"],int(choice["lookback"])))
                with torch.no_grad(): normal=model(xx).numpy()
                preds[split][f"{family}_seed{int(row.seed)}"]=denormalise(normal,mean,scale)
        for split in preds:
            preds[split][family+"_ensemble"]=np.mean([preds[split][f"{family}_seed{s}"] for s in SEEDS],axis=0)
    result=dict(protocol=metadata,selected=selected,ridge=ridge,metrics={})
    equivalence={}
    for split,methods in preds.items():
        result["metrics"][split]={name:metrics(pred,data[split]["truth"],data[split]["strict"],mean,scale) for name,pred in methods.items()}
        existing=ROOT/"results"/(split+"_predictions.npz")
        if "--evaluate-only" in sys.argv:
            previous=np.load(existing)
            equivalence[split]=max(float(np.max(np.abs(previous[name]-pred))) for name,pred in methods.items())
            assert equivalence[split]<1e-6
        np.savez_compressed(existing,truth=data[split]["truth"],
                            origins=data[split]["origins"],strict=data[split]["strict"],**methods)
        items=[]
        for name,p in methods.items():
            for j,target in enumerate(TARGETS):
                v=result["metrics"][split][name]["targets"][target]
                for h in range(1,H+1):
                    items.append(dict(split=split,model=name,target=target,horizon=h,**v["horizons"][str(h)]))
        pd.DataFrame(items).to_csv(ROOT/"results"/(split+"_metrics.csv"),index=False)
        daily=pd.DataFrame(dict(origin=frame.index[data[split]["origins"]],target_date=frame.index[data[split]["origins"]+1],
                                 strict_target=data[split]["strict"][:,0]))
        for j,target in enumerate(TARGETS):
            daily[target+"_actual"]=data[split]["truth"][:,0,j]
            for name in ("Persistence","SeasonalNaive","Ridge","RNN_ensemble","LSTM_ensemble"):
                daily[target+"_"+name]=methods[name][:,0,j]
        daily.to_csv(ROOT/"results"/(split+"_one_day_predictions.csv"),index=False)
    result["training_seconds"]=sum(row["seconds"] for row in runs)
    result["runtime_seconds"]=time.monotonic()-start
    result["post_training_quality_fix_max_forecast_difference"]=equivalence
    dump(ROOT/"results"/"RESULTS.json",result)
    print("SELECTED",json.dumps(selected),flush=True)
    for split in ("validation","test"):
        print("PRICE",split,json.dumps({name:{k:value for k,value in vals["targets"]["price_GBP_MWh"].items() if k in ("MAE","RMSE")} for name,vals in result["metrics"][split].items()}),flush=True)
    print("COMPLETE",round(result["runtime_seconds"],2),flush=True)


if __name__ == "__main__":
    main()
