"""Four predeclared training policies, two joint models, three seeds each."""
from pathlib import Path
import json
import time
import pandas as pd
import torch
import data as dataset
from model import COUNTS
from policy import POLICIES,LR_LEVELS,WD_LEVELS,DROPOUT_LEVELS,PLATEAU_EPOCHS,EARLY_STOP_EPOCHS,MAX_EPOCHS
from fit_core import configure,fit,dump,sha

ROOT=Path(__file__).resolve().parent
SEEDS=[17,29,43]


def main():
    configure();assert json.loads((ROOT/"PREFLIGHT.json").read_text())["all_passed"]
    (ROOT/"results").mkdir(exist_ok=True)
    f,x,data,mean,scale=dataset.prepare();config=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    for name in ("scalers.json","splits.csv"):assert (ROOT/name).read_bytes()==(ROOT/"reference"/name).read_bytes()
    protocol={"joint_next_day":True,"features":8,"outputs":3,"parameters":{m:COUNTS[m]["large"] for m in ("RNN","LSTM")},"configs":config,
        "policies":POLICIES,"seeds":SEEDS,"expected_fits":24,"periods":dataset.PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},
        "schedule":{"trigger":"5 complete epochs with no new global joint-val checkpoint; epoch improvement based on any step beating global joint-val best by1e-5",
            "plateau_epochs":PLATEAU_EPOCHS,"max_transitions":3,"lr_levels":LR_LEVELS,"weight_decay_levels":WD_LEVELS,"dropout_levels":DROPOUT_LEVELS,
            "lr_only":"LR changes; WD/dropout fixed","reg_only":"WD/dropout change; LR fixed","combined":"all three change","fixed":"all three fixed",
            "continuation":"Continue current weights and AdamW moments; no rewind, no optimiser restart; transition after completed epoch affects next update"},
        "training":{"max_epochs":MAX_EPOCHS,"early_stop_full_epochs":EARLY_STOP_EPOCHS,"batch":64,"steps_per_epoch":18,"checkpoint_min_delta":1e-5,"optimizer":"AdamW","clip_norm":1.},
        "old_control_patience":15,"matched_new_control_patience":30,"early_stop_clock_not_reset_by_schedule":True,
        "selection":"One joint-val checkpoint per seed; mean joint-val across seeds selects policy per family; test only monitored",
        "loss":"Equal mean of three targets standardised by train-only scales; train/val/test always eval mode without dropout or added penalty",
        "logging":"Every optimizer step: complete train/val/test joint+3 components, LR/WD/dropout/stage/effective LR*WD; separate event audit",
        "precision":"float32; AMP/TF32 off; deterministic CUDA/cuDNN; same initialisation/shuffle seeds as old study","torch":str(torch.__version__),"cuda":torch.version.cuda,"GPU":torch.cuda.get_device_name(0),
        "input_sha256":sha(ROOT/"inputs/model_daily.csv"),"source_hashes":{n:sha(ROOT/n) for n in ("model.py","policy.py","fit_core.py","data.py","run.py","CONFIGS_FROZEN.json")},
        "reference_hashes":{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/"reference").rglob("*") if p.is_file()},
        "test_is_monitored_not_blind":True,"new_window_or_lr_grid":False,"external_features_added":False,"data_vintage_audited":False,"MPC_evaluated":False}
    dump(ROOT/"PROTOCOL.json",protocol);values=[];began=time.monotonic()
    for family in ("RNN","LSTM"):
        for policy in POLICIES:
            for seed in SEEDS:
                values.append(fit(family,policy,config[family]["lookback"],seed,x,data,mean,scale))
                pd.DataFrame([v["row"] for v in values]).to_csv(ROOT/"results/training_runs.csv",index=False)
                pd.DataFrame([m for v in values for m in v["metrics"]]).to_csv(ROOT/"results/ALL_METRICS.csv",index=False)
                print("PROGRESS",len(values),"/24",flush=True)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"values":values,"wall_seconds":time.monotonic()-began})
    print("COMPLETE",len(values),"fits",time.monotonic()-began,flush=True)


if __name__=="__main__":main()
