"""Common deterministic float32 training and full-split per-update evaluation."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG",":4096:8")
from pathlib import Path
import csv
import hashlib
import json
import random
import time
import numpy as np
import torch
from torch import nn
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
COUNTS={"Transformer":5407,"RNN":5373,"LSTM":5409}


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(device):
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    if device=="cuda":
        assert torch.cuda.is_available();torch.cuda.set_per_process_memory_fraction(.25,0)


def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)


def eval_batch_for(family,length):
    if family!="Transformer":return 2048
    budget=max(64,int(64*(365/length)**2))
    return min(2048,2**(budget.bit_length()-1))


def tensors(x,data,j,length,device):
    return {p:(torch.from_numpy(windows(x,d["origins"],length)).to(device),torch.from_numpy(d["y"][:,j:j+1]).to(device)) for p,d in data.items()}


def normalised_prediction(model,xx,eval_batch=64):
    model.eval()
    with torch.inference_mode():return torch.cat([model(batch) for batch in xx.split(eval_batch)],dim=0)


def evaluate(model,data,eval_batch=64):
    losses={}
    for part,(xx,yy) in data.items():
        p=normalised_prediction(model,xx,eval_batch)
        losses[part]=float(((p-yy).double().square().mean()).item())
    return losses


def fit(target,family,length,lr,seed,x,data,mean,scale,device,stage):
    for folder in ("checkpoints","step_logs","predictions","case_results"):(ROOT/folder).mkdir(exist_ok=True)
    tag=f"{target}_{family}_L{length}_lr{lr:g}_s{seed}"
    cached=ROOT/"case_results"/(tag+".json")
    signature={n:sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","inputs/model_daily.csv")}
    signature["torch"]=torch.__version__
    if cached.exists():
        value=json.loads(cached.read_text());assert value["row"]["device"]==device and value["signature"]==signature
        print("REUSE_COMPLETE",tag,flush=True);return value
    seed_all(seed);j=TARGETS.index(target);model=Predictor(family,j).to(device)
    count=sum(p.numel() for p in model.parameters());assert count==COUNTS[family]
    eval_batch=eval_batch_for(family,length)
    d=tensors(x,data,j,length,device)
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4,foreach=False)
    generator=torch.Generator().manual_seed(seed+1000)
    checkpoint=ROOT/"checkpoints"/(tag+".pt");log=ROOT/"step_logs"/(tag+".csv")
    fields=["run","target","family","seed","epoch","batch_index","global_step","batch_size_actual","samples_seen",
        "train_batch_loss","train_eval_loss","validation_eval_loss","test_eval_loss","best_validation_so_far","checkpoint_improved","elapsed_seconds"]
    best=float("inf");bestrow=None;step=0;stale=0;began=time.monotonic()
    handle=log.open("w",newline="",encoding="utf-8");writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
    def record(epoch,batch_index,batch_size,samples_seen,batch_loss):
        nonlocal best,bestrow
        losses=evaluate(model,d,eval_batch);improved=losses["validation"]<best-1e-5
        row={"run":tag,"target":target,"family":family,"seed":seed,"epoch":epoch,"batch_index":batch_index,"global_step":step,
            "batch_size_actual":batch_size,"samples_seen":samples_seen,"train_batch_loss":batch_loss,
            "train_eval_loss":losses["train"],"validation_eval_loss":losses["validation"],"test_eval_loss":losses["test"],
            "best_validation_so_far":losses["validation"] if improved else best,"checkpoint_improved":improved,"elapsed_seconds":time.monotonic()-began}
        if improved:
            best=losses["validation"];bestrow=row.copy()
            torch.save({"state_dict":{k:v.detach().cpu().clone() for k,v in model.state_dict().items()},"target":target,"target_index":j,
                "family":family,"lookback":length,"lr":lr,"seed":seed,"parameters":count,"device":device,"torch":str(torch.__version__),
                "mean":mean.tolist(),"std":scale.tolist(),"best_epoch":epoch,"best_step":step,"best_validation_loss":best},checkpoint)
        writer.writerow(row);handle.flush();return row,improved
    try:
        first,_=record(0,0,0,0,None);print("START",tag,device,"initial",first["validation_eval_loss"],flush=True)
        tx,ty=d["train"];n=len(tx)
        for epoch in range(1,121):
            improved_epoch=False;seen=(epoch-1)*n
            for batch_index,ids in enumerate(torch.randperm(n,generator=generator).split(64),1):
                ids=ids.to(device);model.train();opt.zero_grad(set_to_none=True)
                p=model(tx[ids]);assert p.shape==ty[ids].shape
                loss=nn.functional.mse_loss(p,ty[ids]);assert torch.isfinite(loss)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.,foreach=False);opt.step()
                step+=1;seen+=len(ids)
                last,improved=record(epoch,batch_index,len(ids),seen,float(loss.item()));improved_epoch|=improved
                if step%200==0:print("STEP",tag,step,"E",epoch,"train",last["train_eval_loss"],"val",last["validation_eval_loss"],"best",best,flush=True)
            stale=0 if improved_epoch else stale+1
            if stale>=15:break
        assert bestrow is not None
        row={"run":tag,"target":target,"family":family,"lookback":length,"lr":lr,"seed":seed,"stage":stage,"device":device,"eval_batch":eval_batch,"parameters":count,
            "best_epoch":bestrow["epoch"],"best_step":bestrow["global_step"],"epochs":epoch,"steps":step,
            "best_train_loss":bestrow["train_eval_loss"],"best_validation_loss":bestrow["validation_eval_loss"],"test_loss_at_val_checkpoint":bestrow["test_eval_loss"],
            "last_train_loss":last["train_eval_loss"],"last_validation_loss":last["validation_eval_loss"],"last_test_loss":last["test_eval_loss"],
            "seconds":time.monotonic()-began,"checkpoint":str(checkpoint.relative_to(ROOT)),"step_log":str(log.relative_to(ROOT))}
        cp=torch.load(checkpoint,weights_only=True);model.load_state_dict(cp["state_dict"]);metrics=[];exported={}
        for part,(xx,yy) in d.items():
            p=normalised_prediction(model,xx,eval_batch).cpu().numpy().ravel().astype(float)*scale[j]+mean[j]
            exported[part]=p;metrics.append({"target":target,"family":family,"lookback":length,"lr":lr,"seed":seed,"stage":stage,"split":part,**score(p,data[part]["truth"][:,j],scale[j])})
        np.savez_compressed(ROOT/"predictions"/(tag+".npz"),**exported)
        value={"row":row,"metrics":metrics,"signature":signature};dump(cached,value);print("DONE",json.dumps(row),flush=True)
        return value
    finally:handle.close()


def score(pred,truth,sd):
    error=np.asarray(pred,dtype=float).ravel()-truth
    return {"loss":float(np.mean((error/sd)**2)),"MSE":float(np.mean(error**2)),"RMSE":float(np.sqrt(np.mean(error**2))),"MAE":float(np.abs(error).mean())}
