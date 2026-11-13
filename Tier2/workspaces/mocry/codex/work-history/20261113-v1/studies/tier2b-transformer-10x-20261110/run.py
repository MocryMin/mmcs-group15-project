"""Nine width-scaled fits: no window, feature, split or learning-rate search."""
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG",":4096:8")
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import torch
import data as dataset
from model import TARGETS,Predictor
from fit_core import configure,fit,sha,dump

ROOT=Path(__file__).resolve().parent
SEEDS=[17,29,43]


def main():
    configure("cuda")
    (ROOT/"results").mkdir(exist_ok=True)
    assert json.loads((ROOT/"PREFLIGHT.json").read_text())["all_passed"]
    f,x,data,mean,scale=dataset.prepare()
    configs=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    previous=json.loads((ROOT/"reference/PROTOCOL.json").read_text())
    for name in ("scalers.json","splits.csv"):
        assert (ROOT/name).read_bytes()==(ROOT/"reference"/name).read_bytes(),name
    assert sha(ROOT/"inputs/model_daily.csv")==previous["input_sha256"]
    assert np.isfinite(x).all()
    assert sum(p.numel() for p in Predictor("Transformer",0).parameters())==54005
    protocol={"experiment":"10x Transformer width scaling, frozen previous configuration", "parameters":54005,"previous_parameters":5407,"ratio":54005/5407,
        "architecture":{"layers":1,"d_model":72,"heads":3,"ffn":220,"activation":"GELU","pre_LN":True,"dropout":.1,"fixed_relative_lag_positions":True,"persistence_residual_output":True},
        "training":previous["training"],"precision":previous["precision"],"logging":previous["logging"],"evaluation_chunks":previous["evaluation_chunks"],
        "periods":dataset.PERIODS,"samples":{p:len(d["origins"]) for p,d in data.items()},"features":8,"horizon":1,"separate_targets":True,
        "configs":configs,"seeds":SEEDS,"expected_fits":9,"selection":"Original small-model val-selected window/lr frozen; each new checkpoint selected only by val",
        "device":"cuda","gpu":torch.cuda.get_device_name(0),"torch":str(torch.__version__),"cuda":torch.version.cuda,
        "input_sha256":sha(ROOT/"inputs/model_daily.csv"),"source_hashes":{n:sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","run.py","CONFIGS_FROZEN.json")},
        "test_is_monitored_not_blind":True,"external_features":False,"MPC_evaluated":False,"data_vintage_audited":False,"new_hyperparameter_search":False}
    dump(ROOT/"PROTOCOL.json",protocol)
    values=[];began=time.monotonic()
    for target in TARGETS:
        c=configs[target]
        for seed in SEEDS:
            values.append(fit(target,"Transformer",c["lookback"],c["lr"],seed,x,data,mean,scale,"cuda","10x_frozen_configuration"))
            pd.DataFrame([v["row"] for v in values]).to_csv(ROOT/"results/training_runs.csv",index=False)
            pd.DataFrame([m for v in values for m in v["metrics"]]).to_csv(ROOT/"results/ALL_METRICS.csv",index=False)
            print("PROGRESS",len(values),"/9",flush=True)
    dump(ROOT/"results/RESULTS.json",{"protocol":protocol,"values":values,"wall_seconds":time.monotonic()-began})
    print("COMPLETE",len(values),"fits",time.monotonic()-began,flush=True)


if __name__=="__main__":main()
