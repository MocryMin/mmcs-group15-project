"""Check the exact size increase, frozen split and both training workloads before fitting."""
from pathlib import Path
import gc
import json
import time
import numpy as np
import torch
from torch import nn
import data as dataset
from fit_core import configure,seed_all,tensors,evaluate,eval_batch_for,dump,sha
from model import Predictor

ROOT=Path(__file__).resolve().parent


def main():
    configure("cuda");f,x,data,mean,scale=dataset.prepare()
    reference=json.loads((ROOT/"reference/scalers.json").read_text())
    small=json.loads((ROOT/"reference/PROTOCOL.json").read_text())
    seed_all(17);m=Predictor("Transformer",0)
    checks={"54005_parameters":sum(p.numel() for p in m.parameters())==54005,"ratio_within_0_2_percent_of_10":abs(54005/5407-10)<.02,
        "exact_frozen_scalers":np.array_equal(mean,reference["mean"]) and np.array_equal(scale,reference["std"]),
        "exact_input_hash":sha(ROOT/"inputs/model_daily.csv")==small["input_sha256"],
        "exact_split_file":(ROOT/"splits.csv").read_bytes()==(ROOT/"reference/splits.csv").read_bytes(),
        "same_feature_count":x.shape[1]==8,"cuda_available":torch.cuda.is_available(),
        "fixed_position_not_parameter":"position" not in dict(m.named_parameters()) and not m.position.requires_grad,
        "latest_position_independent_of_length":torch.equal(m.position[:7].flip(0)[-1],m.position[:182].flip(0)[-1])}
    d=tensors(x,data,0,7,"cpu");xx=d["train"][0][:5]
    m.eval()
    with torch.inference_mode():checks["initial_persistence"]=torch.equal(m(xx),xx[:,-1,0:1])
    with torch.no_grad():m.head.weight.copy_(torch.linspace(-.03,.03,72).reshape(1,72));m.head.bias.fill_(.01)
    with torch.inference_mode():cpu=m(xx).numpy()
    m.to("cuda")
    with torch.inference_mode():gpu=m(xx.to("cuda")).cpu().numpy()
    difference=float(np.abs(cpu-gpu).max());checks["nontrivial_cpu_cuda_match"]=difference<2e-5
    m.train();loss=nn.functional.mse_loss(m(xx.to("cuda")),d["train"][1][:5].to("cuda"));loss.backward()
    checks["finite_nonzero_backward"]=all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters()) and float(m.encoder.linear1.weight.grad.abs().sum())>0
    del m,d;gc.collect();torch.cuda.empty_cache()
    timings=[]
    for length in (7,182):
        seed_all(17);m=Predictor("Transformer",0).to("cuda");d=tensors(x,data,0,length,"cuda")
        opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=1e-4,foreach=False);bs=eval_batch_for("Transformer",length)
        def update():
            m.train();opt.zero_grad(set_to_none=True)
            loss=nn.functional.mse_loss(m(d["train"][0][:64]),d["train"][1][:64]);loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(),1.,foreach=False);opt.step();evaluate(m,d,bs)
        for _ in range(2):update()
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
        for _ in range(3):update()
        torch.cuda.synchronize()
        row={"lookback":length,"eval_batch":bs,"seconds_per_update_and_full_eval":(time.perf_counter()-t)/3,"peak_cuda_allocated_MiB":torch.cuda.max_memory_allocated()/1024**2}
        timings.append(row);print("BENCHMARK",json.dumps(row),flush=True)
        del m,d,opt;gc.collect();torch.cuda.empty_cache()
    checks={k:bool(v) for k,v in checks.items()}
    result={"checks":checks,"all_passed":all(checks.values()),"cpu_cuda_max_difference":difference,"timings":timings,"torch":str(torch.__version__),"gpu":torch.cuda.get_device_name(0)}
    dump(ROOT/"PREFLIGHT.json",result);assert result["all_passed"],result
    print("PREFLIGHT",json.dumps(result),flush=True)


if __name__=="__main__":main()
