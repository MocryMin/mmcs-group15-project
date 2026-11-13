"""Recompute every score from raw predictions under one evaluation protocol."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,Data,TARGETS,methods,score,sha,dump

D=Data();rows=[]
for m in methods():
    path=ROOT/m['prediction_file'];assert sha(path)==m['prediction_sha256']
    z=np.load(path)
    for key in z.files:
        seed,p=key.split('__');pred=z[key];truth=D.y[D.origins[p]+1]
        assert pred.shape==truth.shape
        for j,target in enumerate(TARGETS):
            rows.append({'method':m['id'],'label':m['label'],'category':m['category'],'regime':m['regime'],'seed':seed,'split':p,'target':target,**score(pred[:,j],truth[:,j],D.scale[j])})
        rows.append({'method':m['id'],'label':m['label'],'category':m['category'],'regime':m['regime'],'seed':seed,'split':p,'target':'JOINT','n':len(pred),'loss':float(np.mean(((pred-truth)/D.scale)**2))})
full=pd.DataFrame(rows);full.to_csv(ROOT/'results/ALL_METRICS.csv',index=False)
summary=[]
keys=['method','label','category','regime','split','target']
for key,g in full.groupby(keys,sort=False):
    row=dict(zip(keys,key));row.update(n=int(g.n.iloc[0]),seeds=len(g))
    for metric in ['loss','MSE','RMSE','MAE']:
        row[metric+'_mean']=float(g[metric].mean()) if g[metric].notna().any() else np.nan
        row[metric+'_sd']=float(g[metric].std(ddof=1)) if len(g)>1 and g[metric].notna().any() else np.nan
    summary.append(row)
s=pd.DataFrame(summary)
base=s.loc[s.method.eq('T_fixed_Persistence')].set_index(['split','target']).loss_mean
s['improvement_vs_persistence_pct']=[100*(1-r.loss_mean/base.loc[r.split,r.target]) for r in s.itertuples()]
s.to_csv(ROOT/'results/SUMMARY.csv',index=False)

# All members in this candidate pool are selected by validation scores, never test.
fixedreg=['fixed','fixed_state','past_only_rule']
choices=[]
for target in [*TARGETS,'JOINT']:
    for category,regimes in [('traditional',fixedreg),('neural',['fixed']),('rolling',['expanding','rolling730','rolling_ensemble','online_state'])]:
        pool=s.loc[s.target.eq(target)&s.split.eq('validation')&s.regime.isin(regimes)]
        if category!='rolling':pool=pool.loc[pool.category.eq(category)]
        best=pool.sort_values(['loss_mean','method']).iloc[0]
        for p in ['train','validation','test']:
            score_row=s.loc[s.method.eq(best.method)&s.target.eq(target)&s.split.eq(p)]
            if score_row.empty:continue
            row=score_row.iloc[0].to_dict();row['pool']=category;choices.append(row)
pd.DataFrame(choices).to_csv(ROOT/'results/VALIDATION_SELECTED_COMPARISON.csv',index=False)

# Human-readable wide loss tables retain train/validation/test and NN seed SD.
def cell(m,t,p,metric='loss'):
    r=s.loc[s.method.eq(m)&s.target.eq(t)&s.split.eq(p)]
    if r.empty:return '—'
    r=r.iloc[0];v=r[metric+'_mean'];sd=r[metric+'_sd']
    return f'{v:.6f}'+(f' ± {sd:.6f}' if np.isfinite(sd) else '')
lines=['# 全部方法的统一次日误差','', '各表数值为样本平均标准化 MSE；神经网络为三个种子的分数均值 ± 样本标准差。滚动重拟合没有可比的单一 train 分数，逐次拟合分数见 FIT_HISTORY_all.csv。','']
for target in TARGETS:
    lines+=['## '+target,'','| 方法 | 更新方式 | Train loss | Val loss | Test loss | Test MAE | Test RMSE |','|---|---|---:|---:|---:|---:|---:|']
    for m in methods():
        lines.append('| '+' | '.join([m['label'],m['regime'],*[cell(m['id'],target,p) for p in ['train','validation','test']],cell(m['id'],target,'test','MAE'),cell(m['id'],target,'test','RMSE')])+' |')
    lines+=['']
(ROOT/'results/COMPLETE_TABLES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
out=ROOT/'figures';out.mkdir(exist_ok=True)
labels={
 'T_fixed_Persistence':'Persistence','T_fixed_Seasonal7':'Seasonal naive (7d)','T_fixed_Mean28':'Mean (28d)','T_rule_Weekday52':'Weekday mean (52wk)',
 'T_fixed_OLSLevel':'OLS level','T_fixed_OLSResidual':'OLS residual','T_fixed_RidgeLevel':'Ridge level','T_fixed_RidgeResidual':'Ridge residual',
 'T_fixed_CalendarOLS':'Calendar OLS','T_fixed_CalendarResidualAR':'Calendar + residual AR',
 'T_fixed_EngineeredRidge':'Engineered Ridge','T_fixed_EngineeredLasso':'LASSO','T_fixed_EngineeredHGB':'Gradient boosting','T_fixed_EqualEnsemble':'Equal ensemble',
 'T_state_LevelWeekdayFixed':'Level + weekday (fixed)', 'T_state_LevelWeekdayAdaptive':'Level + weekday (adaptive)',
 'N_sep_RNN':'Independent RNN (5k each)','N_sep_LSTM':'Independent LSTM (5k each)','N_sep_Transformer':'Independent Transformer (5k each)',
 'N_sep_Transformer10x':'Independent Transformer (54k each)',
 'N_joint_RNN_small15':'Joint RNN 5k P15','N_joint_RNN_large15':'Joint RNN 55k P15','N_joint_LSTM_small15':'Joint LSTM 5k P15','N_joint_LSTM_large15':'Joint LSTM 55k P15',
 'N_joint_RNN_fixed30':'Joint RNN 55k fixed P30','N_joint_LSTM_fixed30':'Joint LSTM 55k fixed P30',
 'T_expanding_Ridge':'Ridge expanding','T_rolling730_Ridge':'Ridge rolling 730d','T_rolling730_Lasso':'LASSO rolling 730d','T_expanding_HGB':'Boosting expanding',
 'T_expanding_CalendarAR':'Calendar AR expanding','T_rolling730_CalendarAR':'Calendar AR rolling 730d','T_online_EqualEnsemble':'Equal ensemble online'}
main=[m for m in labels if m not in ['T_state_LevelWeekdayAdaptive'] and not m.startswith(('T_expanding','T_rolling','T_online'))]
fig,axes=plt.subplots(1,3,figsize=(15.5,11.5),sharey=True)
for j,(target,ax) in enumerate(zip(TARGETS,axes)):
    for y,mid in enumerate(main):
        r=s.loc[s.method.eq(mid)&s.target.eq(target)&s.split.eq('test')].iloc[0]
        ref=base.loc['test',target];value=r.loss_mean/ref
        ax.errorbar(value,y,xerr=r.loss_sd/ref if np.isfinite(r.loss_sd) else None,fmt='o',markersize=4,color='#b3542f' if mid.startswith('N_') else '#245578',capsize=2)
    ax.axvline(1,color='.5',ls='--',lw=1);ax.grid(axis='x',alpha=.2);ax.set_title(['Generation (MW)','Demand (MW)','Price (GBP/MWh)'][j]);ax.set_xlabel('Test MSE / persistence MSE')
    ax.set_xlim(left=0)
axes[0].set_yticks(range(len(main)),[labels[m] for m in main]);axes[0].invert_yaxis()
fig.suptitle('Same next-day targets, 2025-09 to 2026-08 | frozen coefficients\nBlue: classical; orange: neural mean score +/- SD of 3 seeds',fontsize=12)
fig.tight_layout(rect=(0,0,1,.95));fig.savefig(out/'fixed_comparison.png',dpi=180);fig.savefig(out/'fixed_comparison.svg');plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(15.5,5.2))
for target,ax in zip(TARGETS,axes):
    pool=pd.DataFrame(choices);g=pool.loc[pool.target.eq(target)]
    mids=list(dict.fromkeys(g.method))
    for x,mid in enumerate(mids):
        for offset,p,c in [(-.18,'train','#8c9dac'),(0.,'validation','#d6a54d'),(.18,'test','#245578')]:
            r=s.loc[s.method.eq(mid)&s.target.eq(target)&s.split.eq(p)]
            if not r.empty:
                r=r.iloc[0];ax.errorbar(x+offset,r.loss_mean,yerr=r.loss_sd if np.isfinite(r.loss_sd) else None,fmt='o',color=c,label=p if x==0 else None,capsize=3)
    ax.set_xticks(range(len(mids)),[labels.get(m,m.replace('N_joint_','')) for m in mids],rotation=25,ha='right');ax.grid(axis='y',alpha=.2)
    ax.set_title(target);ax.set_ylabel('Mean standardized squared error')
axes[0].legend();fig.suptitle('Configurations selected by validation MSE within each pool\nOnline models update on observed labels; they are a separate protocol')
fig.tight_layout(rect=(0,0,1,.9));fig.savefig(out/'selected_losses.png',dpi=180);plt.close(fig)
dump(ROOT/'results/COUNTS.json',{'methods':len(methods()),'neural_configurations':len([m for m in methods() if m['category']=='neural']),'classical_configurations':len([m for m in methods() if m['category']=='traditional']),'raw_metric_rows':len(full),'summary_rows':len(s),'input_hash':sha(ROOT/'inputs/model_daily.csv')})
print(pd.DataFrame(choices).loc[lambda x:x.split.eq('test'),['target','pool','method','loss_mean','loss_sd','MAE_mean','RMSE_mean','improvement_vs_persistence_pct']].to_string(index=False))
