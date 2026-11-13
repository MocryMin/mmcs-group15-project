"""Validate exact plateau boundaries, unchanged data/model and CUDA gradients."""
from pathlib import Path
import gc
import json
import inspect
import numpy as np
import torch
from torch import nn
import data as dataset
from model import Predictor,COUNTS
from fit_core import configure,seed_all,tensors,dump,sha
from policy import POLICIES,PlateauController,hyperparameters

ROOT=Path(__file__).resolve().parent


def main():
    configure();f,x,data,mean,scale=dataset.prepare();checks={};replays=[]
    for name in ("model.py","data.py","scalers.json","splits.csv"):
        checks["unchanged_"+name]=(ROOT/name).read_bytes()==(ROOT/"reference"/name).read_bytes()
    checks["frozen_input"]=sha(ROOT/"inputs/model_daily.csv")=="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"
    for policy in POLICIES:
        c=PlateauController(policy)
        for epoch in range(1,31):c.after_epoch(epoch,epoch*18,False,.12)
        expected=[] if policy=="fixed" else [5,10,15]
        checks[policy+"_trigger_boundary"]=[e["epoch"] for e in c.events]==expected
        checks[policy+"_last_stage"]=c.stage==(0 if policy=="fixed" else 3)
        c=PlateauController(policy)
        for epoch in range(1,9):c.after_epoch(epoch,epoch*18,epoch==3,.12)
        checks[policy+"_improvement_resets_counter"]=(not c.events) if policy=="fixed" else [e["epoch"] for e in c.events]==[8]
    checks["controller_has_no_test_argument"]=not any("test" in k for k in inspect.signature(PlateauController.after_epoch).parameters)
    checks["combined_effective_decay_increases"]=hyperparameters("combined",3)["lr"]*hyperparameters("combined",3)["weight_decay"]>hyperparameters("combined",0)["lr"]*hyperparameters("combined",0)["weight_decay"]
    configs=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    for family in ("RNN","LSTM"):
        seed_all(17);m=Predictor(family,"large");checks[family+"_count"]=sum(p.numel() for p in m.parameters())==COUNTS[family]["large"]
        dd=tensors(x,data,configs[family]["lookback"],"cpu");xx,yy=dd["train"][0][:8],dd["train"][1][:8];m.eval()
        with torch.inference_mode():checks[family+"_initial_persistence"]=torch.equal(m(xx),xx[:,-1,:3])
        with torch.no_grad():m.head.weight.copy_(torch.linspace(-.03,.03,m.head.weight.numel()).reshape_as(m.head.weight))
        with torch.inference_mode():cpu=m(xx).numpy()
        m.to("cuda")
        with torch.inference_mode():gpu=m(xx.to("cuda")).cpu().numpy()
        diff=float(np.abs(cpu-gpu).max());checks[family+"_cpu_cuda"]=diff<2e-5
        m.train();loss=nn.functional.mse_loss(m(xx.to("cuda")),yy.to("cuda"));loss.backward()
        checks[family+"_finite_nonzero_gradient"]=all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters()) and float(m.core.weight_ih_l0.grad.abs().sum())>0
        m.eval()
        with torch.inference_mode():before=m(xx.to("cuda")).cpu().numpy();m.dropout.p=.4;after=m(xx.to("cuda")).cpu().numpy()
        checks[family+"_eval_loss_unaffected_by_dropout_setting"]=np.array_equal(before,after)
        replays.append({"family":family,"cpu_cuda_max_difference":diff})
        del m,dd;gc.collect();torch.cuda.empty_cache()
    record={"checks":{k:bool(v) for k,v in checks.items()},"all_passed":bool(all(checks.values())),"cpu_cuda":replays,"torch":str(torch.__version__),"GPU":torch.cuda.get_device_name(0)}
    dump(ROOT/"PREFLIGHT.json",record);assert record["all_passed"],record;print(json.dumps(record),flush=True)


if __name__=="__main__":main()
