"""Run independent target grids in isolated processes; combine after validation-only selection."""
from pathlib import Path
import json
import os
import shutil
import signal
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch

import fit_core
import run_grid as exp
from fit_core import dump,sha,score
from model import TARGETS

ROOT=Path(__file__).resolve().parent


def worker(target):
    work=ROOT/"parallel_jobs"/target;work.mkdir(parents=True,exist_ok=True)
    for folder in ("inputs","results","checkpoints","step_logs","predictions"):(work/folder).mkdir(exist_ok=True)
    for name in ("inputs/model_daily.csv","inputs/SOURCE_MANIFEST.json","REFERENCE_CONFIGS.json"):
        shutil.copy2(ROOT/name,work/name)
    exp.ROOT=work;fit_core.ROOT=work
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    f,x,data,mean,scale=exp.prepare();exp.previous_equivalence(f,x,data,mean,scale)
    configs=json.loads((work/"REFERENCE_CONFIGS.json").read_text())
    old=pd.read_csv(exp.PREVIOUS/"results/training_runs.csv");rows=[];metrics=[]
    for family in ("RNN","LSTM"):
        lr=float(configs[target+"|"+family]["lr"])
        for length in exp.LOOKBACKS:
            match=old.loc[old.target.eq(target)&old.family.eq(family)&old.lookback.eq(length)&old.lr.eq(lr)&old.seed.eq(17)]
            if length==56 and len(match)==1:
                row=match.iloc[0].to_dict()
                for key in ("seed","lookback","parameters","best_epoch","best_step","epochs","steps"):row[key]=int(row[key])
                for key in ("checkpoint","step_log"):
                    path=Path(str(row[key]).replace("\\","/"));shutil.copy2(exp.PREVIOUS/path,work/path);row[key]=path.as_posix()
                row["original_training_seconds"]=float(row["seconds"]);row["seconds"]=0.;row["reused_previous"]=True
                print("REUSE",row["run"],flush=True)
            else:
                row=fit_core.fit(target,family,{"lookback":length,"lr":lr},17,x,data,mean,scale)
                row["reused_previous"]=False;row["original_training_seconds"]=None
            metrics.extend(exp.export_case(row,f,x,data,mean,scale));rows.append(row)
            pd.DataFrame(rows).to_csv(work/"results/training_runs.csv",index=False)
            pd.DataFrame(metrics).to_csv(work/"results/GRID_METRICS.csv",index=False)
            print("PROGRESS",target,len(rows),"/14",flush=True)
    dump(work/"COMPLETE.json",{"target":target,"runs":rows,"metrics":metrics,"input_sha256":sha(work/"inputs/model_daily.csv")})


def coordinate(original_pids):
    began=time.monotonic();jobs=[]
    for target in ("demand_MW","price_GBP_MWh"):
        work=ROOT/"parallel_jobs"/target;work.mkdir(parents=True,exist_ok=True)
        log=(work/"worker.log").open("w",encoding="utf-8")
        process=subprocess.Popen([sys.executable,"-u",str(Path(__file__)),"worker",target],stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        jobs.append((target,process,log))
    print("STARTED",[(t,p.pid) for t,p,_ in jobs],flush=True)
    execution={"reason":"Parallelise independent target grids, preserving all training/evaluation settings",
        "original_generation_processes":original_pids,"targets":{"generation_MW":"initial sequential runner","demand_MW":"isolated process","price_GBP_MWh":"isolated process"},
        "threads_per_process":2,"worker_source_sha256":sha(Path(__file__)),"interrupted_partial_cases_used":False}
    dump(ROOT/"EXECUTION.json",execution)
    while True:
        try:
            initial=pd.read_csv(ROOT/"results/training_runs.csv")
            generation=initial.loc[initial.target.eq("generation_MW")]
            if len(generation)==14:break
        except (FileNotFoundError,pd.errors.EmptyDataError,pd.errors.ParserError):pass
        for t,p,_ in jobs:
            if p.poll() not in (None,0):raise RuntimeError(f"{t} process failed: {p.returncode}")
        time.sleep(1)
    # All generation fits and exports are complete. Discard any partially started demand fit.
    gen_metrics=pd.read_csv(ROOT/"results/GRID_METRICS.csv")
    gen_metrics=gen_metrics.loc[gen_metrics.target.eq("generation_MW")]
    generation.to_csv(ROOT/"results/generation_completed.csv",index=False)
    gen_metrics.to_csv(ROOT/"results/generation_metrics_completed.csv",index=False)
    for pid in original_pids:
        try:os.kill(pid,signal.SIGTERM)
        except (ProcessLookupError,OSError):pass
    execution["generation_complete_cases"]=14
    execution["initial_runner_stopped_after_generation"]=True
    execution["discarded_partial_case_note"]="Initial runner may have started the next target; its incomplete output is replaced by the isolated complete case."
    dump(ROOT/"EXECUTION.json",execution);print("GENERATION_COMPLETE",flush=True)
    for target,process,log in jobs:
        code=process.wait();log.close();assert code==0,(target,code)
        print("TARGET_COMPLETE",target,flush=True)
    rows=generation.to_dict("records");metrics=gen_metrics.to_dict("records")
    for target,_,_ in jobs:
        work=ROOT/"parallel_jobs"/target
        complete=json.loads((work/"COMPLETE.json").read_text(encoding="utf-8"))
        assert complete["input_sha256"]==sha(ROOT/"inputs/model_daily.csv")
        assert len(complete["runs"])==14
        for row in complete["runs"]:
            for key in ("checkpoint","step_log"):
                path=Path(row[key].replace("\\","/"));shutil.copy2(work/path,ROOT/path);row[key]=path.as_posix()
            name="predictions/"+row["run"]+".npz";shutil.copy2(work/name,ROOT/name)
            rows.append(row)
        metrics.extend(complete["metrics"])
    for row in rows:
        for key in ("seed","lookback","parameters","best_epoch","best_step","epochs","steps"):row[key]=int(row[key])
        if pd.isna(row.get("original_training_seconds")):row["original_training_seconds"]=None
        row["reused_previous"]=bool(row["reused_previous"])
    runs=pd.DataFrame(rows);assert len(runs)==42
    runs.to_csv(ROOT/"results/training_runs.csv",index=False);pd.DataFrame(metrics).to_csv(ROOT/"results/GRID_METRICS.csv",index=False)
    f,x,data,mean,scale=exp.prepare();baseline=[]
    for part,d in data.items():
        for j,target in enumerate(TARGETS):baseline.append({"target":target,"split":part,**score(f[TARGETS].to_numpy()[d["origins"],j],d["truth"][:,j],scale[j])})
    pd.DataFrame(baseline).to_csv(ROOT/"results/PERSISTENCE.csv",index=False)
    selection={}
    for target in TARGETS:
        for family in ("RNN","LSTM"):
            c=runs.loc[runs.target.eq(target)&runs.family.eq(family)].sort_values(["best_validation_loss","lookback"]).iloc[0]
            selection[target+"|"+family]={"target":target,"family":family,"lookback":int(c.lookback),"seed":17,
                "best_validation_loss":float(c.best_validation_loss),"best_step":int(c.best_step),"run":c.run}
    dump(ROOT/"results/SELECTION_FROZEN.json",selection)
    dump(ROOT/"results/RESULTS.json",{"protocol":json.loads((ROOT/"PROTOCOL.json").read_text(encoding="utf-8")),"runs":rows,"metrics":metrics,
        "baselines":baseline,"selected":selection,"coordinator_wall_seconds":time.monotonic()-began,"new_training_seconds":float(runs.seconds.sum())})
    execution["all_targets_complete"]=True;execution["coordinator_wall_seconds"]=time.monotonic()-began
    dump(ROOT/"EXECUTION.json",execution);print("COMPLETE",json.dumps(selection),flush=True)


if __name__=="__main__":
    if sys.argv[1]=="worker":worker(sys.argv[2])
    else:coordinate([int(v) for v in sys.argv[2:]])
