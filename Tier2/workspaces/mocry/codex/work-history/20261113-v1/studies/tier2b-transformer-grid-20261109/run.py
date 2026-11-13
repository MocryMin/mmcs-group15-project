"""GPU Transformer screen and three-seed confirmation, with fresh CPU recurrent controls."""
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG",":4096:8")
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
from pathlib import Path
import json
import subprocess
import sys
import time
import numpy as np
import pandas as pd
import torch
import data as dataset
from fit_core import fit,configure,dump,sha,score
from model import TARGETS

ROOT=Path(__file__).resolve().parent
SEEDS=[17,29,43]
RATES=[.001,.003]


def write_tables(values):
    rows=[v["row"] for v in values];metrics=[m for v in values for m in v["metrics"]]
    pd.DataFrame(rows).to_csv(ROOT/"results/training_runs.csv",index=False)
    pd.DataFrame(metrics).to_csv(ROOT/"results/ALL_METRICS.csv",index=False)


def baseline_worker(target):
    configure("cpu");f,x,data,mean,scale=dataset.prepare(False)
    configs=json.loads((ROOT/"BASELINE_CONFIGS.json").read_text());values=[]
    work=ROOT/"baseline_jobs"/target;work.mkdir(parents=True,exist_ok=True)
    for family in ("RNN","LSTM"):
        c=configs[target+"|"+family]
        for seed in SEEDS:
            values.append(fit(target,family,c["lookback"],c["lr"],seed,x,data,mean,scale,"cpu","baseline_confirmation"))
            pd.DataFrame([v["row"] for v in values]).to_csv(work/"progress.csv",index=False)
    dump(work/"COMPLETE.json",{"target":target,"values":values})


def main():
    configure("cuda");f,x,data,mean,scale=dataset.prepare()
    for folder in ("results","checkpoints","step_logs","predictions","case_results","execution_logs"):(ROOT/folder).mkdir(exist_ok=True)
    baseline_select=json.loads((ROOT/"reference_plain/results/SELECTION_FROZEN.json").read_text());old_runs=pd.read_csv(ROOT/"reference_plain/results/training_runs.csv")
    baseline_configs={}
    for key,c in baseline_select.items():
        r=old_runs.loc[old_runs.run.eq(c["run"])].iloc[0]
        baseline_configs[key]={"target":c["target"],"family":c["family"],"lookback":int(r.lookback),"lr":float(r.lr),"selected_from":"Previous seed17 seven-window grid; frozen before current training"}
    dump(ROOT/"BASELINE_CONFIGS.json",baseline_configs)
    reference_files={p.relative_to(ROOT).as_posix():sha(p) for name in ("reference_plain","reference_attention") for p in (ROOT/name).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    dump(ROOT/"REFERENCE_MANIFEST.json",reference_files)
    protocol={"architecture":"Single-layer Transformer encoder; d_model24, heads3, FFN54, GELU, pre-LayerNorm, fixed relative-lag sinusoidal positions, last-token residual-to-persistence readout",
        "parameters":{"Transformer":5407,"RNN":5373,"LSTM":5409},"input_features":8,"horizon":1,"separate_targets":True,
        "periods":dataset.PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},"lookbacks_days":dataset.LOOKBACKS,
        "screen":{"family":"Transformer","seed":17,"learning_rates":RATES,"cases":42,"selection":"minimum validation checkpoint MSE; tie-break shorter window then smaller learning rate"},
        "confirmation":{"seeds":SEEDS,"transformer_cases":9,"recurrent_cases":18,"screen_seed17_reused":True,"expected_unique_fits":66},
        "baseline_configuration":"Frozen six plain-model configurations from previous grid; all18 seeds retrained in the current torch environment",
        "selection":"Validation only for checkpoint, window and learning rate; test is only logged, never selects anything",
        "training":{"batch_size":64,"steps_per_epoch":18,"max_epochs":120,"patience_complete_epochs":15,"min_delta":1e-5,"optimizer":"AdamW","weight_decay":1e-4,"clip_norm":1.,"dropout":.1},
        "logging":"Full train, validation and test eval after every update; weighted all-sample mean from chunks; CSV flush every row",
        "evaluation_chunks":"Transformer largest power-of-two <=64*(365/L)^2, bounded64..2048; recurrent2048; no sample subsampling",
        "precision":"float32, math SDPA, AMP off, TF32 off, deterministic algorithms; CUBLAS_WORKSPACE_CONFIG=:4096:8",
        "device":{"Transformer":"cuda","RNN":"cpu","LSTM":"cpu","GPU":torch.cuda.get_device_name(0),"GPU_memory_fraction_cap":.25},
        "attention_boundary":"Bidirectional self-attention among observed historical tokens only; target day never in the window",
        "test_status":"Previously monitored holdout, not a new blind test; only validation chooses configurations",
        "data_vintage_audited":False,"external_features":False,"MPC_evaluated":False,"torch":torch.__version__,"cuda":torch.version.cuda,
        "source_hashes":{n:sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","run.py","BASELINE_CONFIGS.json","REFERENCE_MANIFEST.json")},
        "input_sha256":sha(ROOT/"inputs/model_daily.csv")}
    dump(ROOT/"PROTOCOL.json",protocol);print("PROTOCOL",json.dumps(protocol),flush=True)
    jobs=[]
    for target in TARGETS:
        work=ROOT/"baseline_jobs"/target;work.mkdir(parents=True,exist_ok=True);log=(work/"worker.log").open("w",encoding="utf-8")
        process=subprocess.Popen([sys.executable,"-u",str(Path(__file__)),"baseline",target],stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        jobs.append((target,process,log))
    began=time.monotonic();values=[]
    for target in TARGETS:
        for length in dataset.LOOKBACKS:
            for lr in RATES:
                values.append(fit(target,"Transformer",length,lr,17,x,data,mean,scale,"cuda","screen"))
                write_tables(values);print("SCREEN_PROGRESS",len(values),"/42",flush=True)
                for t,p,_ in jobs:
                    if p.poll() not in (None,0):raise RuntimeError(("baseline failed",t,p.returncode))
    screen=pd.DataFrame([v["row"] for v in values]);selection={}
    for target in TARGETS:
        c=screen.loc[screen.target.eq(target)].sort_values(["best_validation_loss","lookback","lr"]).iloc[0]
        selection[target]={"target":target,"family":"Transformer","lookback":int(c.lookback),"lr":float(c.lr),"selected_seed":17,"best_validation_loss":float(c.best_validation_loss),"screen_run":c.run}
    dump(ROOT/"results/SELECTION_FROZEN.json",selection);print("SELECTION_FROZEN",json.dumps(selection),flush=True)
    for target,c in selection.items():
        for seed in (29,43):
            values.append(fit(target,"Transformer",c["lookback"],c["lr"],seed,x,data,mean,scale,"cuda","confirmation"))
            write_tables(values)
    for target,p,log in jobs:
        code=p.wait();log.close();assert code==0,(target,code)
        work=ROOT/"baseline_jobs"/target;complete=json.loads((work/"COMPLETE.json").read_text());values.extend(complete["values"])
        (ROOT/"execution_logs"/(target+"_baseline.log")).write_bytes((work/"worker.log").read_bytes())
    assert len(values)==66;write_tables(values)
    simple=[]
    for part,d in data.items():
        for j,target in enumerate(TARGETS):
            for name,lag in (("Persistence",1),("Seasonal7",7)):
                pred=f[TARGETS].to_numpy()[d["origins"]+1-lag,j]
                simple.append({"target":target,"split":part,"family":name,**score(pred,d["truth"][:,j],scale[j])})
    pd.DataFrame(simple).to_csv(ROOT/"results/SIMPLE_BASELINES.csv",index=False)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"selection":selection,"values":values,"simple_baselines":simple,
        "wall_seconds":time.monotonic()-began,"summed_training_seconds":sum(v["row"]["seconds"] for v in values)})
    print("COMPLETE",len(values),"fits",time.monotonic()-began,flush=True)


if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="baseline":baseline_worker(sys.argv[2])
    else:main()
