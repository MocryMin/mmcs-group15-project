"""Fit three seeds for each joint RNN/LSTM budget on the current frozen split."""
from pathlib import Path
import json
import time
import pandas as pd
import torch
import data as dataset
from model import TARGETS,COUNTS,WIDTHS
from fit_core import configure,fit,dump,sha,score

ROOT=Path(__file__).resolve().parent
SEEDS=[17,29,43]


def main():
    configure();assert json.loads((ROOT/"PREFLIGHT.json").read_text())["all_passed"]
    (ROOT/"results").mkdir(exist_ok=True)
    f,x,data,mean,scale=dataset.prepare();configs=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    for name in ("scalers.json","splits.csv"):assert (ROOT/name).read_bytes()==(ROOT/"reference"/name).read_bytes()
    protocol={"joint_three_target_next_day":True,"horizon":1,"features":8,"targets":TARGETS,"separate_target_models":False,
        "parameters":COUNTS,"hidden_widths":WIDTHS,"configs":configs,"seeds":SEEDS,"expected_fits":12,
        "periods":dataset.PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},"source_input_sha256":sha(ROOT/"inputs/model_daily.csv"),
        "architecture":"One shared recurrent layer + dropout0.1 + linear3 output, residual-to-last-day three-series readout; zero-initialised output head",
        "loss":"Equal mean over samples and the three train-standardised next-day variables; same joint validation loss selects the sole checkpoint for all targets",
        "selection":"Previous joint next-day val-selected RNN28/LSTM56 lr0.003 frozen; no new window/lr search; each seed checkpoint/early-stop uses only joint val",
        "training":{"batch":64,"steps_per_epoch":18,"epochs_max":120,"patience_full_epochs":15,"min_delta":1e-5,"optimizer":"AdamW","weight_decay":1e-4,"gradient_clip":1.,"dropout":.1},
        "logging":"Full train/val/test joint and all three component losses after every optimiser step; eval dropout disabled; immediate flush",
        "precision":"float32; AMP/TF32 off; deterministic CUDA/cuDNN; CUBLAS_WORKSPACE_CONFIG=:4096:8","device":"cuda","GPU":torch.cuda.get_device_name(0),"torch":str(torch.__version__),"cuda":torch.version.cuda,
        "new_small_controls":True,"old_joint_periods_differ":True,"test_is_monitored_not_blind":True,"data_vintage_audited":False,"external_features_added":False,"MPC_evaluated":False,
        "source_hashes":{n:sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","run.py","CONFIGS_FROZEN.json")}}
    dump(ROOT/"PROTOCOL.json",protocol);values=[];began=time.monotonic()
    for family in ("RNN","LSTM"):
        c=configs[family]
        for budget in ("small","large"):
            for seed in SEEDS:
                values.append(fit(family,budget,c["lookback"],c["lr"],seed,x,data,mean,scale))
                pd.DataFrame([v["row"] for v in values]).to_csv(ROOT/"results/training_runs.csv",index=False)
                pd.DataFrame([m for v in values for m in v["metrics"]]).to_csv(ROOT/"results/ALL_METRICS.csv",index=False)
                print("PROGRESS",len(values),"/12",flush=True)
    simple=[]
    for part,d in data.items():
        for name,lag in (("Persistence",1),("Seasonal7",7)):
            pred=f[TARGETS].to_numpy()[d["origins"]+1-lag]
            simple.extend({"family":name,"budget":"none","seed":None,"split":part,**m} for m in score(pred,d["truth"],scale))
    pd.DataFrame(simple).to_csv(ROOT/"results/SIMPLE_BASELINES.csv",index=False)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"values":values,"simple_baselines":simple,"wall_seconds":time.monotonic()-began})
    print("COMPLETE",len(values),"fits",time.monotonic()-began,flush=True)


if __name__=="__main__":main()
