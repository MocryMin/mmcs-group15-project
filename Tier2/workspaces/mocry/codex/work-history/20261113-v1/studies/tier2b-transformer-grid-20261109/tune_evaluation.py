"""Time full evaluation chunk sizes without changing samples, model selection or objectives."""
from pathlib import Path
import gc
import time
import json
import numpy as np
import torch
import data as dataset
from model import Predictor
from fit_core import configure,seed_all,tensors,evaluate,dump

ROOT=Path(__file__).resolve().parent


def main():
    configure("cuda");f,x,data,mean,scale=dataset.prepare(False);rows=[]
    for length,batches in ((365,[64,128,256,512]),(56,[64,2048]),(7,[64,2048])):
        seed_all(17);model=Predictor("Transformer",0).to("cuda")
        with torch.no_grad():model.head.weight.copy_(torch.linspace(-.03,.03,24,device="cuda").reshape(1,24))
        d=tensors(x,data,0,length,"cuda");reference=None
        for batch in batches:
            evaluate(model,d,batch);torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
            for _ in range(3):losses=evaluate(model,d,batch)
            torch.cuda.synchronize();seconds=(time.perf_counter()-start)/3
            if reference is None:reference=losses
            delta=max(abs(losses[p]-reference[p]) for p in losses)
            assert delta<1e-6
            row={"lookback":length,"eval_batch":batch,"seconds_full_three_sets":seconds,"max_loss_difference":delta,"peak_allocated_MiB":torch.cuda.max_memory_allocated()/1024**2}
            rows.append(row);print(json.dumps(row),flush=True)
        del model,d;gc.collect();torch.cuda.empty_cache()
    dump(ROOT/"EVALUATION_CHUNK_TIMING.json",{"timings":rows,"full_three_set_samples_unchanged":True,"no_model_selection":True})


if __name__=="__main__":main()
