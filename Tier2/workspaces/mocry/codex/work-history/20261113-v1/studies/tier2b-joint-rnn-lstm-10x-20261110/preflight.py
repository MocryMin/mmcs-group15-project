"""Check joint-output shapes, exact counts, persistence, gradients and CUDA replay."""
from pathlib import Path
import gc
import time
import json
import numpy as np
import torch
from torch import nn
import data as dataset
from model import Predictor,COUNTS,WIDTHS
from fit_core import configure,seed_all,tensors,evaluate,dump

ROOT=Path(__file__).resolve().parent


def main():
    configure();f,x,data,mean,scale=dataset.prepare()
    checks={"same_scalers":(ROOT/"scalers.json").read_bytes()==(ROOT/"reference/scalers.json").read_bytes(),"same_splits":(ROOT/"splits.csv").read_bytes()==(ROOT/"reference/splits.csv").read_bytes()}
    configs=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text());timings=[];differences=[]
    for family in ("RNN","LSTM"):
        length=configs[family]["lookback"]
        for budget in ("small","large"):
            seed_all(17);model=Predictor(family,budget);count=sum(p.numel() for p in model.parameters())
            checks[family+budget+"_count"]=count==COUNTS[family][budget]
            h=WIDTHS[family][budget];formula=h*h+13*h+3 if family=="RNN" else 4*h*h+43*h+3
            checks[family+budget+"_formula"]=formula==count
            dd=tensors(x,data,length,"cpu");xx=dd["train"][0][:5];yy=dd["train"][1][:5]
            model.eval()
            with torch.inference_mode():checks[family+budget+"_persistence_shape"]=model(xx).shape==(5,3) and torch.equal(model(xx),xx[:,-1,:3])
            with torch.no_grad():model.head.weight.copy_(torch.linspace(-.03,.03,model.head.weight.numel()).reshape_as(model.head.weight));model.head.bias.fill_(.01)
            with torch.inference_mode():cpu=model(xx).numpy()
            model.to("cuda")
            with torch.inference_mode():gpu=model(xx.to("cuda")).cpu().numpy()
            diff=float(np.abs(cpu-gpu).max());differences.append({"family":family,"budget":budget,"max_prediction_difference":diff})
            checks[family+budget+"_cpu_cuda"]=diff<2e-5
            model.train();loss=nn.functional.mse_loss(model(xx.to("cuda")),yy.to("cuda"));loss.backward()
            checks[family+budget+"_finite_nonzero_gradient"]=all(q.grad is None or torch.isfinite(q.grad).all() for q in model.parameters()) and float(model.core.weight_ih_l0.grad.abs().sum())>0
            del model,dd;gc.collect();torch.cuda.empty_cache()
            seed_all(17);model=Predictor(family,budget).to("cuda");dd=tensors(x,data,length)
            opt=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=1e-4,foreach=False)
            def update():
                model.train();opt.zero_grad(set_to_none=True)
                loss=nn.functional.mse_loss(model(dd["train"][0][:64]),dd["train"][1][:64]);loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.,foreach=False);opt.step();evaluate(model,dd)
            for _ in range(2):update()
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();began=time.perf_counter()
            for _ in range(3):update()
            torch.cuda.synchronize();row={"family":family,"budget":budget,"parameters":count,"lookback":length,"seconds_per_update_and_full_eval":(time.perf_counter()-began)/3,"peak_cuda_MiB":torch.cuda.max_memory_allocated()/1024**2}
            timings.append(row);print("BENCHMARK",json.dumps(row),flush=True)
            del model,dd,opt;gc.collect();torch.cuda.empty_cache()
    record={"checks":{k:bool(v) for k,v in checks.items()},"all_passed":bool(all(checks.values())),"timings":timings,"cpu_cuda":differences,"torch":str(torch.__version__),"gpu":torch.cuda.get_device_name(0)}
    dump(ROOT/"PREFLIGHT.json",record);assert record["all_passed"],record
    print("PREFLIGHT",json.dumps(record),flush=True)


if __name__=="__main__":main()
