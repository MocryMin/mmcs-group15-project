"""Fit aligned classical forecasts; select only on per-target validation MSE."""
import argparse
import itertools
import json
import time
import warnings
import numpy as np
import pandas as pd
from common import ROOT, Data, TARGETS, dump, save_method, sha
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
import joblib

D=Data()
FIT_LOG=[]
SELECT=[]
START=time.time()


def specs(family,j):
    transforms=['raw','asinh'] if j==2 else ['raw']
    grid={'Ridge':[.1,1.,10.,100.,1000.], 'Lasso':[.0001,.001,.01,.03,.1], 'HGB':[2,4], 'CalendarAR':[0]}[family]
    return [dict(family=family,parameter=p,transform=t) for p,t in itertools.product(grid,transforms)]


def label_indices(origin,window=None):
    labels=np.arange(D.index.get_loc('2022-01-01'),origin+1)
    if window:labels=labels[labels>=origin-window+1]
    assert len(labels)>0 and labels.max()<=origin
    return labels


def fit(spec,j,labels,tag):
    y=D.z[labels,j]
    state={'spec':spec,'target':j,'labels_first':str(D.index[labels[0]].date()),'labels_last':str(D.index[labels[-1]].date()),'n':len(labels)}
    if spec['family']=='CalendarAR':
        b=np.linalg.lstsq(D.cal[labels],y,rcond=1e-10)[0]
        residual=D.z[:,j]-D.cal@b
        avg=pd.Series(residual).rolling(7).mean().to_numpy()
        origins=labels-1
        phi=np.linalg.lstsq(np.column_stack([residual[origins],avg[origins]]),residual[labels],rcond=1e-10)[0]
        state.update(b=b,phi=phi)
    else:
        if spec['transform']=='asinh':
            median=float(np.median(y));spread=max(1.4826*float(np.median(np.abs(y-median))),1e-6)
            y=np.arcsinh((y-median)/spread);state.update(median=median,spread=spread)
        xs=StandardScaler().fit(D.engineered[labels-1]);X=xs.transform(D.engineered[labels-1])
        p=spec['parameter'];family=spec['family']
        if family=='Ridge':model=Ridge(alpha=p,solver='svd')
        elif family=='Lasso':model=Lasso(alpha=p,max_iter=30000,tol=1e-5,selection='cyclic')
        else:model=HistGradientBoostingRegressor(max_iter=300,learning_rate=.05,max_depth=p,min_samples_leaf=20,l2_regularization=1.,early_stopping=False,random_state=17)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',ConvergenceWarning);model.fit(X,y)
        convergence=[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]
        state.update(xs=xs,model=model,convergence_warnings=convergence)
        if convergence:raise RuntimeError('Unconverged '+tag+': '+str(convergence))
    train_pred=predict(state,labels-1)
    FIT_LOG.append({'tag':tag,'target':TARGETS[j],**spec,'label_start':state['labels_first'],'label_end':state['labels_last'],'n':len(labels),'fit_train_loss':float(np.mean(((train_pred-D.y[labels,j])/D.scale[j])**2))})
    return state


def predict(state,origins):
    j=state['target'];spec=state['spec']
    if spec['family']=='CalendarAR':
        r=D.z[:,j]-D.cal@state['b'];avg=pd.Series(r).rolling(7).mean().to_numpy()
        z=D.cal[origins+1]@state['b']+np.column_stack([r[origins],avg[origins]])@state['phi']
    else:
        z=state['model'].predict(state['xs'].transform(D.engineered[origins]))
        if spec['transform']=='asinh':z=state['median']+state['spread']*np.sinh(z)
    result=z*D.scale[j]+D.mean[j]
    assert np.isfinite(result).all()
    return result


def val_loss(pred,j):return float(np.mean(((pred-D.y[D.origins['validation']+1,j])/D.scale[j])**2))


def fixed_models():
    for family in ['Ridge','Lasso','HGB']:
        predictions={p:np.empty((len(o),3)) for p,o in D.origins.items()};choices=[]
        for j in range(3):
            candidates=[]
            for spec in specs(family,j):
                tag=f'fixed_{family}_{j}_{len(candidates)}'
                state=fit(spec,j,D.origins['train']+1,tag)
                vp=predict(state,D.origins['validation']);loss=val_loss(vp,j)
                candidates.append((loss,json.dumps(spec,sort_keys=True),state))
                SELECT.append({'regime':'fixed','family':family,'target':TARGETS[j],**spec,'validation_loss':loss})
            loss,_,chosen=min(candidates,key=lambda x:(x[0],x[1]));choices.append({**chosen['spec'],'target':TARGETS[j],'validation_loss':loss})
            joblib.dump(chosen,ROOT/'models'/f'T_fixed_Engineered{family}_{j}.joblib')
            for p,o in D.origins.items():predictions[p][:,j]=predict(chosen,o)
        save_method('T_fixed_Engineered'+family,{'label':{'Ridge':'特征岭回归','Lasso':'LASSO','HGB':'梯度提升树'}[family],'category':'traditional','regime':'fixed','selection':'per-target validation MSE','selected':choices,'features':D.feature_names,'transform_fit':'training labels only'}, {'det':predictions})
        print(f'fixed {family} done {time.time()-START:.1f}s',flush=True)
    ensemble('T_fixed_EqualEnsemble',['T_fixed_EngineeredRidge','T_fixed_EngineeredLasso','T_fixed_EngineeredHGB'],'fixed')


def level_weekday(alpha,j,adaptive):
    y=D.y[:,j];dow=D.index.dayofweek.to_numpy();forecast=np.full(len(y),np.nan);level=None
    train=D.origins['train']+1
    fixed_profile=np.array([y[train[dow[train]==k]].mean() for k in range(7)])
    fixed_base=float(y[train].mean())
    for t in range(364,len(y)-1):
        if adaptive:
            profile=np.array([y[t-364:t][dow[t-364:t]==k].mean() for k in range(7)]);base=y[t-364:t].mean()
        else:profile=fixed_profile.copy();base=fixed_base
        if j==2:
            assert abs(base)>1e-8
            profile=profile/base
            assert np.min(np.abs(profile))>1e-8
            deseason=y[t]/profile[dow[t]]
        else:
            profile=profile-base;deseason=y[t]-profile[dow[t]]
        level=deseason if level is None else alpha*deseason+(1-alpha)*level
        forecast[t]=level*profile[dow[t+1]] if j==2 else level+profile[dow[t+1]]
    return forecast


def rules():
    # The forecast origin is t; matching target weekday observations are t-6,t-13,... .
    pred={p:np.stack([D.y[o-6-7*k] for k in range(52)]).mean(axis=0) for p,o in D.origins.items()}
    save_method('T_rule_Weekday52',{'label':'52周同星期均值','category':'traditional','regime':'past_only_rule','window_days':364}, {'det':pred})
    for adaptive in [False,True]:
        choices=[];pred={p:np.empty((len(o),3)) for p,o in D.origins.items()}
        for j in range(3):
            candidates=[]
            for a in [.05,.1,.2,.3,.5,.8]:
                allp=level_weekday(a,j,adaptive);loss=val_loss(allp[D.origins['validation']],j)
                candidates.append((loss,a,allp));SELECT.append({'regime':'adaptive_profile' if adaptive else 'fixed_profile','family':'LevelWeekday','target':TARGETS[j],'alpha':a,'validation_loss':loss})
            loss,a,allp=min(candidates,key=lambda x:(x[0],x[1]));choices.append({'target':TARGETS[j],'alpha':a,'validation_loss':loss})
            for p,o in D.origins.items():pred[p][:,j]=allp[o]
        save_method('T_state_LevelWeekday'+('Adaptive' if adaptive else 'Fixed'),{'label':'水平＋星期模式（'+('动态' if adaptive else '固定')+'）','category':'traditional','regime':'online_state' if adaptive else 'fixed_state','selected':choices,'profile':'previous 364 observations, excluding origin' if adaptive else '2022-2024 training labels','level_update':'actual observations through origin; no refitting alpha','price_profile':'multiplicative; other targets additive'}, {'det':pred})


def rolling_forecast(spec,j,split,window,save_states=False,method=None):
    origins=D.origins[split];out=np.empty(len(origins));rows=[]
    for block,start in enumerate(range(0,len(origins),28)):
        current=origins[start:start+28];origin=int(current[0]);labels=label_indices(origin,window)
        assert D.index[labels[-1]]<=D.index[current[0]]<D.index[current[0]+1]
        tag=f'rolling_{window}_{split}_{spec["family"]}_{spec["parameter"]}_{spec["transform"]}_{j}_{block}'
        state=fit(spec,j,labels,tag);out[start:start+len(current)]=predict(state,current)
        row={'method':method,'target':TARGETS[j],'split':split,'block':block,'label_start':state['labels_first'],'label_end':state['labels_last'],'n':len(labels),'first_origin':str(D.index[current[0]].date()),'last_origin':str(D.index[current[-1]].date()),'first_target':str(D.index[current[0]+1].date()),'last_target':str(D.index[current[-1]+1].date()),'spec':json.dumps(spec,sort_keys=True)}
        if save_states:
            path=ROOT/'models'/f'{method}_{j}_{split}_{block}.joblib';joblib.dump(state,path);row['model_file']=path.relative_to(ROOT).as_posix();row['model_sha256']=sha(path)
        rows.append(row)
    return out,rows


def rolling_models():
    history=[]
    for family,window in [('Ridge',None),('Ridge',730),('Lasso',730),('HGB',None),('CalendarAR',None),('CalendarAR',730)]:
        regime='expanding' if window is None else 'rolling730';mid='T_'+regime+'_'+family
        pred={p:np.empty((len(D.origins[p]),3)) for p in ['validation','test']};chosen=[]
        for j in range(3):
            candidates=[]
            for spec in specs(family,j):
                vp,_=rolling_forecast(spec,j,'validation',window);loss=val_loss(vp,j)
                candidates.append((loss,json.dumps(spec,sort_keys=True),spec))
                SELECT.append({'regime':regime,'family':family,'target':TARGETS[j],**spec,'validation_loss':loss})
            loss,_,spec=min(candidates,key=lambda x:(x[0],x[1]));chosen.append({**spec,'target':TARGETS[j],'validation_loss':loss})
            for p in ['validation','test']:
                pred[p][:,j],rows=rolling_forecast(spec,j,p,window,True,mid);history+=rows
        save_method(mid,{'label':{'Ridge':'特征岭回归','Lasso':'LASSO','HGB':'梯度提升树','CalendarAR':'日历＋残差 AR'}[family]+('（扩展）' if window is None else '（滚动730）'),'category':'traditional','regime':regime,'selection':'per-target rolling validation MSE','selected':chosen,'refit_every_origin_days':28,'training_boundary':'label date <= first forecast origin of each block','train_score':'not comparable: varying model, per-refit in FIT_HISTORY.csv'}, {'det':pred})
        print(f'{mid} done {time.time()-START:.1f}s',flush=True)
    pd.DataFrame(history).to_csv(ROOT/'results/ROLLING_BOUNDARIES.csv',index=False)
    ensemble('T_online_EqualEnsemble',['T_expanding_Ridge','T_rolling730_Lasso','T_expanding_HGB'],'rolling_ensemble')


def ensemble(mid,members,regime):
    arrays=[np.load(ROOT/'predictions'/(m+'.npz')) for m in members]
    keys=set.intersection(*[set(a.files) for a in arrays])
    pred={k.split('__')[1]:np.mean([a[k] for a in arrays],axis=0) for k in keys}
    save_method(mid,{'label':'等权集成'+('（滚动）' if regime=='rolling_ensemble' else ''),'category':'traditional','regime':regime,'members':members,'weights':[1/3]*3,'selection':'members target-specific validation selected; equal weights fixed'}, {'det':pred})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--part',choices=['all','fixed','rolling'],default='all');args=parser.parse_args()
    with threadpool_limits(limits=2):
        if args.part in ['all','fixed']:rules();fixed_models()
        if args.part in ['all','rolling']:rolling_models()
    pd.DataFrame(SELECT).to_csv(ROOT/f'results/SELECTION_{args.part}.csv',index=False)
    pd.DataFrame(FIT_LOG).to_csv(ROOT/f'results/FIT_HISTORY_{args.part}.csv',index=False)
    dump(ROOT/f'results/RUN_{args.part}.json',{'seconds':time.time()-START,'fits':len(FIT_LOG),'selection_candidates':len(SELECT),'code_sha256':sha(__file__),'input_sha256':sha(ROOT/'inputs/model_daily.csv')})
    print('finished',args.part,len(FIT_LOG),time.time()-START,flush=True)
