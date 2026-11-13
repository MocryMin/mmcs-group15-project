"""Three temporal splits, full-set loss after every optimiser update, val selection."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")

import copy
import csv
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def fit(target,family,config,seed,x,data,mean,scale):
    j=TARGETS.index(target);length=int(config["lookback"]);lr=float(config["lr"])
    tag=f"{target}_{family}_L{length}_lr{lr:g}_s{seed}"
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=Predictor(family,j)
    count=sum(p.numel() for p in model.parameters());assert count==5441
    tensors={p:(torch.from_numpy(windows(x,d["origins"],length)),torch.from_numpy(d["y"][:,j:j+1])) for p,d in data.items()}
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    generator=torch.Generator().manual_seed(seed+1000)
    best=float("inf");best_state=None;best_row=None;step=0;stale_epochs=0;began=time.monotonic()
    checkpoint=ROOT/"checkpoints"/(tag+".pt");log=ROOT/"step_logs"/(tag+".csv")
    fields=["run","target","family","seed","epoch","batch_index","global_step","batch_size_actual","samples_seen",
            "train_batch_loss","train_eval_loss","validation_eval_loss","test_eval_loss","best_validation_so_far","checkpoint_improved","elapsed_seconds"]
    handle=log.open("w",newline="",encoding="utf-8");writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
    def evaluate(epoch,batch_index,batch_size,samples_seen,batch_loss):
        nonlocal best,best_state,best_row
        model.eval();losses={}
        with torch.inference_mode():
            for part,(xx,yy) in tensors.items():losses[part]=nn.functional.mse_loss(model(xx),yy).item()
        # Test is logged, but never appears in checkpoint/early-stopping decisions.
        improved=losses["validation"]<best-1e-5
        row={"run":tag,"target":target,"family":family,"seed":seed,"epoch":epoch,"batch_index":batch_index,
            "global_step":step,"batch_size_actual":batch_size,"samples_seen":samples_seen,"train_batch_loss":batch_loss,
            "train_eval_loss":losses["train"],"validation_eval_loss":losses["validation"],"test_eval_loss":losses["test"],
            "best_validation_so_far":losses["validation"] if improved else best,"checkpoint_improved":improved,"elapsed_seconds":time.monotonic()-began}
        if improved:
            best=losses["validation"];best_state=copy.deepcopy(model.state_dict());best_row=row.copy()
            torch.save({"state_dict":best_state,"target":target,"target_index":j,"family":family,"lookback":length,"lr":lr,"seed":seed,
                "mean":mean.tolist(),"std":scale.tolist(),"best_epoch":epoch,"best_step":step,"best_validation_loss":best,"architecture":"temporal_scaled_dot_product_attention"},checkpoint)
        writer.writerow(row);handle.flush()
        return row,improved
    try:
        first,_=evaluate(0,0,0,0,None)
        print("START",tag,"initial",first["train_eval_loss"],first["validation_eval_loss"],first["test_eval_loss"],flush=True)
        train_x,train_y=tensors["train"];n=len(train_x)
        for epoch in range(1,121):
            improved_epoch=False;samples_seen=(epoch-1)*n
            for batch_index,ids in enumerate(torch.randperm(n,generator=generator).split(64),1):
                model.train();opt.zero_grad(set_to_none=True)
                prediction=model(train_x[ids]);assert prediction.shape==train_y[ids].shape
                batch_loss=nn.functional.mse_loss(prediction,train_y[ids]);assert torch.isfinite(batch_loss)
                batch_loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
                step+=1;samples_seen+=len(ids)
                last,improved=evaluate(epoch,batch_index,len(ids),samples_seen,float(batch_loss.item()))
                improved_epoch|=improved
                if step%200==0:print(f"STEP {tag} {step} E{epoch} train={last['train_eval_loss']:.5f} val={last['validation_eval_loss']:.5f} test={last['test_eval_loss']:.5f} bestVal={best:.5f}",flush=True)
            stale_epochs=0 if improved_epoch else stale_epochs+1
            if stale_epochs>=15:break
        assert best_state is not None and best_row is not None
        row={"run":tag,"target":target,"family":family,"seed":seed,"lookback":length,"lr":lr,"parameters":count,
            "best_epoch":best_row["epoch"],"best_step":best_row["global_step"],"epochs":epoch,"steps":step,
            "best_train_loss":best_row["train_eval_loss"],"best_validation_loss":best_row["validation_eval_loss"],"test_loss_at_val_checkpoint":best_row["test_eval_loss"],
            "last_train_loss":last["train_eval_loss"],"last_validation_loss":last["validation_eval_loss"],"last_test_loss":last["test_eval_loss"],
            "seconds":time.monotonic()-began,"step_log":str(log.relative_to(ROOT)),"checkpoint":str(checkpoint.relative_to(ROOT))}
        print("DONE",json.dumps(row),flush=True)
        return row
    finally:handle.close()


def score(pred,truth,sd):
    e=np.asarray(pred,dtype=float).ravel()-truth
    return {"loss":float(np.mean((e/sd)**2)),"MSE":float(np.mean(e**2)),"RMSE":float(np.sqrt(np.mean(e**2))),"MAE":float(np.abs(e).mean())}


