"""Resumable capacity grid; complete three-split evaluation after every update."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2');os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import argparse,csv,json,random,time,hashlib
from pathlib import Path
import numpy as np,pandas as pd,torch
from torch import nn
from features import load,ROOT,TARGETS
from model import Predictor

def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def signature():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['features.py','model.py','fit.py','BASELINE_FROZEN.json','inputs/model_daily.csv']}
def evaluate(model,tensors,chunk):
    model.eval();out={}
    with torch.inference_mode():
        for p,(x,y) in tensors.items():
            prediction=torch.cat([model(b) for b in x.split(chunk)]);out[p]=float((prediction-y).double().square().mean())
    return out

def fit(target,family,budget,groups,seed,device):
    tag=target+'_'+family+'_'+str(budget)+'_'+('base' if not groups else '+'.join(groups))+'_s'+str(seed);cached=ROOT/'case_results'/(tag+'.json');sig=signature()
    if cached.exists():
        value=json.loads(cached.read_text());assert value['signature']==sig;return value
    if (ROOT/'STOP_REQUESTED').exists():raise InterruptedError('Stop requested before next fit')
    f,x,data,mean,scale,names=load(groups);j=TARGETS.index(target);cfg=json.loads((ROOT/'BASELINE_FROZEN.json').read_text());length=cfg['windows_days'][family][j];lr=cfg['learning_rates'][family][j]
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=Predictor(family,j,x.shape[1],budget).to(device);count=sum(p.numel() for p in model.parameters());assert abs(count-budget)/budget<.12
    tensors={p:(torch.tensor(np.stack([x[t-length+1:t+1] for t in d['origins']]),device=device),torch.tensor(d['y'][:,j:j+1],device=device)) for p,d in data.items()}
    chunk=2048 if family!='Transformer' else (128 if length>=91 else 2048)
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=.0001,foreach=False);generator=torch.Generator().manual_seed(seed+1000)
    checkpoint=ROOT/'models'/(tag+'.pt');log=ROOT/'step_logs'/(tag+'.csv');began=time.monotonic();best=float('inf');step=0;stale=0
    fields=['run','target','family','budget','parameters','features','groups','seed','epoch','step','batch_loss','train_loss','validation_loss','test_loss','best_validation','improved','seconds']
    handle=log.open('w',newline='',encoding='utf-8');writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
    bestrow=None
    def record(epoch,batch_loss):
        nonlocal best,bestrow
        scores=evaluate(model,tensors,chunk);improved=scores['validation']<best-1e-5
        row={'run':tag,'target':target,'family':family,'budget':budget,'parameters':count,'features':x.shape[1],'groups':'+'.join(groups),'seed':seed,'epoch':epoch,'step':step,'batch_loss':batch_loss,'train_loss':scores['train'],'validation_loss':scores['validation'],'test_loss':scores['test'],'best_validation':min(best,scores['validation']) if improved else best,'improved':improved,'seconds':time.monotonic()-began}
        if improved:
            best=scores['validation'];bestrow=row.copy();torch.save({'state_dict':{k:v.detach().cpu().clone() for k,v in model.state_dict().items()},'family':family,'target':target,'j':j,'budget':budget,'inputs':x.shape[1],'spec':model.spec,'groups':groups,'features':names,'seed':seed,'epoch':epoch,'step':step,'validation_loss':best,'mean':mean.tolist(),'scale':scale.tolist()},checkpoint)
        writer.writerow(row);handle.flush();return improved,row
    try:
        _,last=record(0,None);tx,ty=tensors['train'];print('START',tag,device,count,x.shape[1],flush=True)
        for epoch in range(1,cfg['max_epochs']+1):
            improved_epoch=False
            for ids in torch.randperm(len(tx),generator=generator).split(cfg['batch_size']):
                ids=ids.to(device);model.train();opt.zero_grad(set_to_none=True);pred=model(tx[ids]);loss=nn.functional.mse_loss(pred,ty[ids]);assert torch.isfinite(loss)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.,foreach=False);opt.step();step+=1;improved,last=record(epoch,float(loss.detach()));improved_epoch|=improved
            stale=0 if improved_epoch else stale+1
            if stale>=cfg['patience_epochs']:break
        state=torch.load(checkpoint,weights_only=True);model.load_state_dict(state['state_dict']);model.eval();metrics=[];predictions={}
        with torch.inference_mode():
            for p,(xx,yy) in tensors.items():
                raw=torch.cat([model(b) for b in xx.split(chunk)]).cpu().numpy().ravel().astype(float)*scale[j]+mean[j];predictions[p]=raw;err=raw-data[p]['truth'][:,j]
                metrics.append({'split':p,'n':len(err),'loss':float(np.mean((err/scale[j])**2)),'MSE':float(np.mean(err**2)),'MAE':float(np.mean(abs(err))),'RMSE':float(np.sqrt(np.mean(err**2)))})
        np.savez_compressed(ROOT/'predictions'/(tag+'.npz'),**predictions)
        value={'row':{**bestrow,'epochs_ran':epoch,'updates':step,'wall_seconds':time.monotonic()-began,'device':device,'lookback':length,'lr':lr,'checkpoint':checkpoint.relative_to(ROOT).as_posix()},'metrics':metrics,'signature':sig};dump(cached,value);print('DONE',tag,bestrow['validation_loss'],bestrow['test_loss'],time.monotonic()-began,flush=True)
        return value
    finally:handle.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--families',default='Transformer');p.add_argument('--targets',default=','.join(TARGETS));p.add_argument('--budgets',default='2000,5000,10000');p.add_argument('--groups',default='');p.add_argument('--seeds',default='17,29,43');p.add_argument('--device',default='cuda');args=p.parse_args()
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    if args.device=='cuda':torch.cuda.set_per_process_memory_fraction(.80,0)
    for target in args.targets.split(','):
        for family in args.families.split(','):
            for budget in map(int,args.budgets.split(',')):
                for seed in map(int,args.seeds.split(',')):fit(target,family,budget,[g for g in args.groups.split(',') if g],seed,args.device)
