"""Joint training with validation-plateau LR/regularisation ablations."""
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
from model import Predictor,TARGETS,COUNTS,WIDTHS,windows
from policy import PlateauController,hyperparameters,MAX_EPOCHS,EARLY_STOP_EPOCHS,MIN_DELTA

ROOT=Path(__file__).resolve().parent
PARTS=["train","validation","test"]
EVAL_BATCH=2048


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def configure():
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    assert torch.cuda.is_available();torch.cuda.set_per_process_memory_fraction(.25,0)


def seed_all(seed):random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)


def tensors(x,data,length,device="cuda"):
    return {part:(torch.from_numpy(windows(x,d["origins"],length)).to(device),torch.from_numpy(d["y"]).to(device)) for part,d in data.items()}


def predict(model,xx,eval_batch=EVAL_BATCH):
    model.eval()
    with torch.inference_mode():return torch.cat([model(batch) for batch in xx.split(eval_batch)],0)


def evaluate(model,data):
    result={}
    for part,(xx,yy) in data.items():
        error=(predict(model,xx)-yy).double();per=error.square().mean(0)
        result[part+"_eval_loss"]=float(per.mean().item())
        for j,target in enumerate(TARGETS):result[part+"_"+target+"_loss"]=float(per[j].item())
    return result


def score(pred,truth,scale):
    e=np.asarray(pred,dtype=float)-np.asarray(truth,dtype=float)
    metrics=[{"target":"JOINT","loss":float(np.mean((e/scale)**2))}]
    for j,t in enumerate(TARGETS):metrics.append({"target":t,"loss":float(np.mean((e[:,j]/scale[j])**2)),"MSE":float(np.mean(e[:,j]**2)),"RMSE":float(np.sqrt(np.mean(e[:,j]**2))),"MAE":float(np.mean(np.abs(e[:,j])))})
    return metrics


def fit(family,policy,length,seed,x,data,mean,scale):
    for folder in ("step_logs","checkpoints","predictions","case_results","events"):(ROOT/folder).mkdir(exist_ok=True)
    tag=f"{family}_{policy}_joint_L{length}_s{seed}";cached=ROOT/"case_results"/(tag+".json")
    signature={n:sha(ROOT/n) for n in ("model.py","fit_core.py","policy.py","data.py","inputs/model_daily.csv","CONFIGS_FROZEN.json")};signature["torch"]=str(torch.__version__)
    if cached.exists():
        value=json.loads(cached.read_text());assert value["signature"]==signature;print("REUSE",tag,flush=True);return value
    seed_all(seed);model=Predictor(family,"large").to("cuda");count=sum(q.numel() for q in model.parameters());assert count==COUNTS[family]["large"]
    d=tensors(x,data,length);params=hyperparameters(policy,0)
    opt=torch.optim.AdamW(model.parameters(),lr=params["lr"],weight_decay=params["weight_decay"],foreach=False)
    controller=PlateauController(policy);generator=torch.Generator().manual_seed(seed+1000)
    checkpoint=ROOT/"checkpoints"/(tag+".pt");log=ROOT/"step_logs"/(tag+".csv")
    lossfields=[p+"_eval_loss" for p in PARTS]+[p+"_"+t+"_loss" for p in PARTS for t in TARGETS]
    fields=["run","family","policy","seed","epoch","batch_index","global_step","batch_size_actual","samples_seen","train_batch_loss",
        "stage","learning_rate","weight_decay","dropout","lr_times_wd",*lossfields,"best_validation_so_far","checkpoint_improved","elapsed_seconds"]
    best=float("inf");bestrow=None;step=0;began=time.monotonic();stale=0
    handle=log.open("w",newline="",encoding="utf-8");writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
    def record(epoch,batch_index,batch_size,seen,batch_loss):
        nonlocal best,bestrow
        losses=evaluate(model,d);improved=losses["validation_eval_loss"]<best-MIN_DELTA
        actual={"learning_rate":opt.param_groups[0]["lr"],"weight_decay":opt.param_groups[0]["weight_decay"],"dropout":model.dropout.p}
        row={"run":tag,"family":family,"policy":policy,"seed":seed,"epoch":epoch,"batch_index":batch_index,"global_step":step,
            "batch_size_actual":batch_size,"samples_seen":seen,"train_batch_loss":batch_loss,"stage":controller.stage,**actual,
            "lr_times_wd":actual["learning_rate"]*actual["weight_decay"],**losses,
            "best_validation_so_far":losses["validation_eval_loss"] if improved else best,"checkpoint_improved":improved,"elapsed_seconds":time.monotonic()-began}
        if improved:
            best=losses["validation_eval_loss"];bestrow=row.copy()
            torch.save({"state_dict":{k:v.detach().cpu().clone() for k,v in model.state_dict().items()},"family":family,"budget":"large","policy":policy,"lookback":length,"seed":seed,
                "parameters":count,"hidden":WIDTHS[family]["large"],"targets":TARGETS,"horizon":1,"features":8,"mean":mean.tolist(),"std":scale.tolist(),"stage":controller.stage,**actual,
                "best_epoch":epoch,"best_step":step,"best_validation_loss":best,"torch":str(torch.__version__),"device":"cuda"},checkpoint)
        writer.writerow(row);handle.flush();return row,improved
    try:
        first,_=record(0,0,0,0,None);print("START",tag,count,"initial",first["validation_eval_loss"],flush=True)
        tx,ty=d["train"];n=len(tx)
        for epoch in range(1,MAX_EPOCHS+1):
            improved_epoch=False;seen=(epoch-1)*n
            for batch_index,ids in enumerate(torch.randperm(n,generator=generator).split(64),1):
                ids=ids.to("cuda");model.train();opt.zero_grad(set_to_none=True)
                p=model(tx[ids]);assert p.shape==ty[ids].shape==(len(ids),3)
                loss=nn.functional.mse_loss(p,ty[ids]);assert torch.isfinite(loss)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.,foreach=False);opt.step()
                step+=1;seen+=len(ids);last,improved=record(epoch,batch_index,len(ids),seen,float(loss.item()));improved_epoch|=improved
                if step%400==0:print("STEP",tag,step,"stage",controller.stage,"val",last["validation_eval_loss"],"best",best,flush=True)
            stale=0 if improved_epoch else stale+1
            event=controller.after_epoch(epoch,step,improved_epoch,best)
            if event:
                params=event["after"]
                for group in opt.param_groups:group["lr"]=params["lr"];group["weight_decay"]=params["weight_decay"]
                model.dropout.p=params["dropout"]
                dump(ROOT/"events"/(tag+".json"),controller.events)
                print("PLATEAU",tag,json.dumps(event),flush=True)
            if stale>=EARLY_STOP_EPOCHS:break
        cp=torch.load(checkpoint,weights_only=True);model.load_state_dict(cp["state_dict"]);model.dropout.p=cp["dropout"]
        metrics=[];exported={}
        for part,(xx,yy) in d.items():
            pred=predict(model,xx).cpu().numpy().astype(float)*scale+mean;exported[part]=pred
            metrics.extend({"family":family,"policy":policy,"parameters":count,"lookback":length,"seed":seed,"split":part,**m} for m in score(pred,data[part]["truth"],scale))
        np.savez_compressed(ROOT/"predictions"/(tag+".npz"),**exported)
        row={"run":tag,"family":family,"policy":policy,"parameters":count,"lookback":length,"seed":seed,"best_epoch":bestrow["epoch"],"best_step":bestrow["global_step"],
            "best_stage":bestrow["stage"],"best_lr":bestrow["learning_rate"],"best_weight_decay":bestrow["weight_decay"],"best_dropout":bestrow["dropout"],
            "epochs":epoch,"steps":step,"events_count":len(controller.events),"best_train_loss":bestrow["train_eval_loss"],"best_validation_loss":bestrow["validation_eval_loss"],"test_loss_at_val_checkpoint":bestrow["test_eval_loss"],
            "last_train_loss":last["train_eval_loss"],"last_validation_loss":last["validation_eval_loss"],"last_test_loss":last["test_eval_loss"],"device":"cuda","eval_batch":EVAL_BATCH,"seconds":time.monotonic()-began,
            "checkpoint":str(checkpoint.relative_to(ROOT)),"step_log":str(log.relative_to(ROOT))}
        value={"row":row,"metrics":metrics,"signature":signature,"events":controller.events};dump(ROOT/"events"/(tag+".json"),controller.events);dump(cached,value)
        print("DONE",json.dumps(row),flush=True);return value
    finally:handle.close()
