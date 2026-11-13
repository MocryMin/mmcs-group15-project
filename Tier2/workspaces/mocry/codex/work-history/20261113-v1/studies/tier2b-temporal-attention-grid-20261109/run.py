"""Three isolated target workers for the attention versus plain lookback experiment."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch

import data as dataset
import fit_core
from fit_core import dump,sha,score
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
SEED=17


def export_case(work,row,x,data,mean,scale):
    j=TARGETS.index(row["target"]);cp=torch.load(work/row["checkpoint"],weights_only=True)
    model=Predictor(row["family"],j);model.load_state_dict(cp["state_dict"]);model.eval()
    predictions={};metrics=[];profiles={}
    for part,d in data.items():
        xx=torch.from_numpy(windows(x,d["origins"],row["lookback"]))
        with torch.inference_mode():p,w=model(xx,return_attention=True)
        pred=p.numpy().ravel().astype(float)*scale[j]+mean[j];weights=w.numpy().astype(float)
        assert weights.shape==(len(d["origins"]),row["lookback"])
        assert np.isfinite(weights).all() and (weights>=0).all() and np.allclose(weights.sum(axis=1),1.,atol=1e-6)
        predictions[part]=pred
        metrics.append({"target":row["target"],"family":row["family"],"lookback":row["lookback"],"seed":SEED,"split":part,
            "best_step":row["best_step"],"epochs":row["epochs"],**score(pred,d["truth"][:,j],scale[j])})
        entropy=-(weights*np.log(np.maximum(weights,1e-30))).sum(axis=1)
        profiles[part]={"mean_weight_by_lag_1_to_L":weights.mean(axis=0)[::-1].tolist(),
            "mean_lag_to_target_days":float((weights*np.arange(row["lookback"],0,-1)).sum(axis=1).mean()),
            "normalised_entropy":float((entropy/np.log(row["lookback"])).mean()),"effective_positions_mean":float(np.exp(entropy).mean()),
            "recent_mass":{str(k):float(weights[:,-min(k,row["lookback"]):].sum(axis=1).mean()) for k in dataset.LOOKBACKS}}
    np.savez_compressed(work/"predictions"/(row["run"]+".npz"),**predictions)
    dump(work/"attention_profiles"/(row["run"]+".json"),profiles)
    return metrics


def worker(target):
    work=ROOT/"jobs"/target;work.mkdir(parents=True,exist_ok=True)
    for folder in ("inputs","results","checkpoints","step_logs","predictions","attention_profiles"):(work/folder).mkdir(exist_ok=True)
    for name in ("inputs/model_daily.csv","inputs/SOURCE_MANIFEST.json","REFERENCE_CONFIGS.json"):
        shutil.copy2(ROOT/name,work/name)
    dataset.ROOT=work;fit_core.ROOT=work
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    f,x,data,mean,scale=dataset.prepare();configs=json.loads((work/"REFERENCE_CONFIGS.json").read_text());rows=[];metrics=[]
    for family in ("RNN","LSTM"):
        for length in dataset.LOOKBACKS:
            config={"lookback":length,"lr":float(configs[target+"|"+family]["lr"])}
            row=fit_core.fit(target,family,config,SEED,x,data,mean,scale)
            metrics.extend(export_case(work,row,x,data,mean,scale));rows.append(row)
            pd.DataFrame(rows).to_csv(work/"results/training_runs.csv",index=False)
            pd.DataFrame(metrics).to_csv(work/"results/GRID_METRICS.csv",index=False)
            print("PROGRESS",target,len(rows),"/14",flush=True)
    dump(work/"COMPLETE.json",{"target":target,"runs":rows,"metrics":metrics,"input_sha256":sha(work/"inputs/model_daily.csv"),
        "config_sha256":sha(work/"REFERENCE_CONFIGS.json"),"mean":mean.tolist(),"std":scale.tolist()})


def main():
    f,x,data,mean,scale=dataset.prepare()
    for folder in ("results","checkpoints","step_logs","predictions","attention_profiles","execution_logs"):(ROOT/folder).mkdir(exist_ok=True)
    baseline_files=[p for p in (ROOT/"baseline").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    dump(ROOT/"BASELINE_MANIFEST.json",{p.relative_to(ROOT).as_posix():sha(p) for p in baseline_files})
    protocol={"architecture":"Unidirectional recurrent encoder plus last-query scaled dot-product temporal attention; concatenated last state and attention context; persistence residual",
        "Q_K_V":"Identity projections; Q is last hidden state, K=V are all observed hidden states; no independent projection matrices",
        "parameters":{"RNN_attention":5441,"LSTM_attention":5441,"plain_RNN":5373,"plain_LSTM":5409},
        "attention_complexity":"Single query over L positions; O(LH) attention, no L by L self-attention matrix",
        "lookbacks_days":dataset.LOOKBACKS,"seed":17,"expected_new_fits":42,"periods":dataset.PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},
        "training":"Same target/family learning rate as plain grid; AdamW; batch64; 18 steps/epoch; max120 epochs; 15 complete epochs patience; val min_delta1e-5",
        "logging":"Every optimiser update: full train, validation and test eval MSE; flush every row; identical eval mode",
        "selection":"Checkpoint and seven-window selection use validation only; test never used for selection",
        "target_weights":"Independent target networks, same historical G/D/p and calendar inputs; no parameter sharing",
        "context":"2021 only provides historical input; 2022-2024 fits labels and scalers; 2026 September tail excluded",
        "test_status":"Monitored development holdout, previously viewed; not a blind test",
        "baseline":"Frozen previous plain seed17 grid; matched input/target dates/scalers/lookbacks/rates; small head parameter increase explicitly counted",
        "source_hashes":{n:sha(ROOT/n) for n in ("run.py","data.py","fit_core.py","model.py","REFERENCE_CONFIGS.json")},
        "baseline_manifest_sha256":sha(ROOT/"BASELINE_MANIFEST.json"),"input_sha256":sha(ROOT/"inputs/model_daily.csv"),
        "device":"CPU, independent target processes, two threads each","torch":torch.__version__,"data_vintage_audited":False,"MPC_evaluated":False}
    dump(ROOT/"PROTOCOL.json",protocol);print("PROTOCOL",json.dumps(protocol),flush=True)
    began=time.monotonic();jobs=[]
    for target in TARGETS:
        work=ROOT/"jobs"/target;work.mkdir(parents=True,exist_ok=True)
        log=(work/"worker.log").open("w",encoding="utf-8")
        process=subprocess.Popen([sys.executable,"-u",str(Path(__file__)),"worker",target],stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        jobs.append((target,process,log));print("STARTED",target,process.pid,flush=True)
    rows=[];metrics=[]
    for target,process,log in jobs:
        code=process.wait();log.close();assert code==0,(target,code)
        work=ROOT/"jobs"/target;complete=json.loads((work/"COMPLETE.json").read_text(encoding="utf-8"))
        assert len(complete["runs"])==14 and complete["input_sha256"]==protocol["input_sha256"]
        assert complete["config_sha256"]==sha(ROOT/"REFERENCE_CONFIGS.json")
        assert np.array_equal(complete["mean"],mean) and np.array_equal(complete["std"],scale)
        for row in complete["runs"]:
            for key in ("checkpoint","step_log"):
                path=Path(row[key].replace("\\","/"));shutil.copy2(work/path,ROOT/path);row[key]=path.as_posix()
            for folder,suffix in (("predictions",".npz"),("attention_profiles",".json")):
                path=Path(folder)/(row["run"]+suffix);shutil.copy2(work/path,ROOT/path)
            rows.append(row)
        metrics.extend(complete["metrics"])
        for name in ("worker.log","COMPLETE.json"):shutil.copy2(work/name,ROOT/"execution_logs"/(target+"_"+name))
        print("TARGET_COMPLETE",target,flush=True)
    runs=pd.DataFrame(rows);runs.to_csv(ROOT/"results/training_runs.csv",index=False)
    pd.DataFrame(metrics).to_csv(ROOT/"results/GRID_METRICS.csv",index=False)
    selection={}
    for target in TARGETS:
        for family in ("RNN","LSTM"):
            c=runs.loc[runs.target.eq(target)&runs.family.eq(family)].sort_values(["best_validation_loss","lookback"]).iloc[0]
            selection[target+"|"+family]={"target":target,"family":family,"lookback":int(c.lookback),"seed":17,
                "best_validation_loss":float(c.best_validation_loss),"best_step":int(c.best_step),"run":c.run}
    dump(ROOT/"results/SELECTION_FROZEN.json",selection)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"runs":rows,"metrics":metrics,"selected":selection,
        "wall_seconds":time.monotonic()-began,"summed_training_seconds":float(runs.seconds.sum())})
    print("COMPLETE",json.dumps(selection),flush=True)


if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="worker":worker(sys.argv[2])
    else:main()
