"""Check size, chronology and CPU/CUDA equivalence; time the actual per-step workload."""
from pathlib import Path
import gc
import json
import time
import numpy as np
import torch
from torch import nn
import data as dataset
from fit_core import configure,seed_all,tensors,evaluate,dump,COUNTS,eval_batch_for
from model import Predictor

ROOT=Path(__file__).resolve().parent


def main():
    configure("cuda");f,x,data,mean,scale=dataset.prepare()
    checks={"cuda_available":torch.cuda.is_available(),"same_scalers_as_plain":False}
    reference=json.loads((ROOT/"reference_plain/scalers.json").read_text())
    checks["same_scalers_as_plain"]=np.array_equal(mean,reference["mean"]) and np.array_equal(scale,reference["std"])
    seed_all(17);model=Predictor("Transformer",0)
    checks["5407_transformer_parameters"]=sum(p.numel() for p in model.parameters())==5407
    checks["fixed_position_not_trainable"]=not model.position.requires_grad and "position" not in dict(model.named_parameters())
    checks["latest_position_zero_for_any_length"]=torch.equal(model.position[:7].flip(0)[-1],model.position[:365].flip(0)[-1])
    d=tensors(x,data,0,56,"cpu");batch=d["train"][0][:5]
    model.eval()
    with torch.inference_mode():p=model(batch)
    checks["initial_persistence"]=torch.equal(p,batch[:,-1,0:1])
    with torch.no_grad():model.head.weight.copy_(torch.linspace(-.03,.03,24).reshape(1,24));model.head.bias.fill_(.01)
    with torch.inference_mode():cpu=model(batch).numpy()
    model=model.to("cuda").eval()
    with torch.inference_mode():gpu=model(batch.to("cuda")).cpu().numpy()
    discrepancy=float(np.max(np.abs(cpu-gpu)));checks["nontrivial_cpu_cuda_prediction_match"]=discrepancy<2e-5
    model.train();loss=nn.functional.mse_loss(model(batch.to("cuda")),d["train"][1][:5].to("cuda"));loss.backward()
    checks["finite_cuda_backward"]=all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    del model,d;gc.collect();torch.cuda.empty_cache()
    timings=[]
    for family,length in (("Transformer",7),("Transformer",56),("Transformer",365),("RNN",30),("LSTM",14)):
        for device in ("cpu","cuda"):
            seed_all(17);model=Predictor(family,0).to(device);d=tensors(x,data,0,length,device)
            assert sum(p.numel() for p in model.parameters())==COUNTS[family]
            opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=1e-4,foreach=False)
            eval_batch=eval_batch_for(family,length)
            def update():
                model.train();opt.zero_grad(set_to_none=True)
                loss=nn.functional.mse_loss(model(d["train"][0][:64]),d["train"][1][:64]);loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(),1.,foreach=False);opt.step();evaluate(model,d,eval_batch)
            for _ in range(2):update()
            if device=="cuda":torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
            start=time.perf_counter()
            for _ in range(3):update()
            if device=="cuda":torch.cuda.synchronize()
            seconds=(time.perf_counter()-start)/3
            row={"family":family,"lookback":length,"device":device,"eval_batch":eval_batch,"seconds_per_update_and_full_three_set_eval":seconds,
                "peak_cuda_allocated_MiB":float(torch.cuda.max_memory_allocated()/1024**2) if device=="cuda" else None}
            timings.append(row);print("TIMING",json.dumps(row),flush=True)
            del model,d,opt;gc.collect();torch.cuda.empty_cache()
    checks={k:bool(v) for k,v in checks.items()}
    result={"checks":checks,"all_passed":all(checks.values()),"torch":torch.__version__,"cuda_build":torch.version.cuda,
        "gpu":torch.cuda.get_device_name(0),"capability":torch.cuda.get_device_capability(0),"cpu_cuda_max_normalised_prediction_difference":discrepancy,
        "timings":timings,"timing_protocol":"2 warmups, mean of3 complete updates plus full three-split eval; GPU synchronised; float32/math SDPA/TF32 off",
        "memory_fraction_cap":.25}
    dump(ROOT/"PREFLIGHT_BENCHMARK.json",result);assert result["all_passed"],result
    print("PREFLIGHT",json.dumps(result),flush=True)


if __name__=="__main__":main()
