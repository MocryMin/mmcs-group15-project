"""Replay attention models, audit losses and compare the frozen plain-model grid."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import TwoSlopeNorm

import data as dataset
from fit_core import dump,sha,score
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
PARTS=("train","validation","test")
ZH={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
COLORS={"train":"#245c91","validation":"#b97828","test":"#39844e"}


def audit_all(result,f,x,data,mean,scale,runs,metrics,persistence,histories):
    expected={(t,m,l) for t in TARGETS for m in ("RNN","LSTM") for l in dataset.LOOKBACKS}
    baseline_manifest=json.loads((ROOT/"BASELINE_MANIFEST.json").read_text())
    baseline_scaler=json.loads((ROOT/"baseline/scalers.json").read_text())
    checks={"42_complete_cases":len(runs)==42 and set(zip(runs.target,runs.family,runs.lookback))==expected,
        "126_case_split_metrics":len(metrics)==126 and metrics.groupby(["target","family","lookback"]).size().eq(3).all(),
        "source_code_config_unchanged":all(sha(ROOT/n)==v for n,v in result["protocol"]["source_hashes"].items()),
        "frozen_baseline_files":all(sha(ROOT/n)==v for n,v in baseline_manifest.items()),
        "frozen_input":sha(ROOT/"inputs/model_daily.csv")==result["protocol"]["input_sha256"],
        "same_train_only_scalers_as_plain":np.array_equal(mean,baseline_scaler["mean"]) and np.array_equal(scale,baseline_scaler["std"]),
        "preflight_attention_math_and_gradients":json.loads((ROOT/"PREFLIGHT.json").read_text())["all_passed"],
        "fixed_seed_and_parameters":runs.seed.eq(17).all() and runs.parameters.eq(5441).all(),
        "fixed_samples":{p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365},
        "validation_only_grid_selection":all(c["run"]==runs.loc[runs.target.eq(c["target"])&runs.family.eq(c["family"])].sort_values(["best_validation_loss","lookback"]).iloc[0].run for c in result["selected"].values())}
    complete=layout=chosen=stopping=heads=initial=weights_ok=True
    max_pred_diff=max_loss_diff=max_profile_diff=0.
    for row in runs.itertuples():
        h=histories[row.run];j=TARGETS.index(row.target)
        complete &= np.array_equal(h.global_step,np.arange(row.steps+1)) and np.isfinite(h[[p+"_eval_loss" for p in PARTS]].to_numpy()).all()
        layout &= row.steps==18*row.epochs and np.array_equal(h.iloc[1:].batch_size_actual,np.tile([64]*17+[8],row.epochs))
        layout &= np.array_equal(h.iloc[1:].batch_index,np.tile(np.arange(1,19),row.epochs))
        layout &= np.array_equal(h.iloc[1:].epoch,np.repeat(np.arange(1,row.epochs+1),18))
        seen=np.repeat(np.arange(row.epochs)*1096,18)+np.tile(np.cumsum([64]*17+[8]),row.epochs)
        layout &= np.array_equal(h.iloc[1:].samples_seen,seen)
        best=float("inf");beststep=0;bestepoch=0
        for z in h.itertuples():
            improved=z.validation_eval_loss<best-1e-5
            chosen &= bool(z.checkpoint_improved)==improved
            if improved:best=z.validation_eval_loss;beststep=z.global_step;bestepoch=z.epoch
            chosen &= np.isclose(z.best_validation_so_far,best,atol=1e-12,rtol=0)
        chosen &= beststep==row.best_step and bestepoch==row.best_epoch
        stopping &= row.epochs==120 or row.epochs-bestepoch==15
        cp=torch.load(ROOT/row.checkpoint,weights_only=True);model=Predictor(row.family,j);model.load_state_dict(cp["state_dict"]);model.eval()
        heads &= cp["architecture"]=="temporal_scaled_dot_product_attention" and cp["lookback"]==row.lookback
        heads &= model.head.out_features==1 and cp["target_index"]==j and cp["best_step"]==row.best_step
        z=np.load(ROOT/"predictions"/(row.run+".npz"));profiles=json.loads((ROOT/"attention_profiles"/(row.run+".json")).read_text())
        at=h.loc[h.global_step.eq(row.best_step)].iloc[0]
        for part,d in data.items():
            xx=torch.from_numpy(windows(x,d["origins"],row.lookback))
            with torch.inference_mode():p,w=model(xx,return_attention=True)
            pred=p.numpy().ravel().astype(float)*scale[j]+mean[j];weights=w.numpy()
            heads &= xx.shape[1]==row.lookback and weights.shape==(len(d["origins"]),row.lookback)
            weights_ok &= np.isfinite(weights).all() and (weights>=0).all() and np.allclose(weights.sum(axis=1),1.,atol=1e-6)
            max_pred_diff=max(max_pred_diff,float(np.max(np.abs(pred-z[part]))))
            max_profile_diff=max(max_profile_diff,float(np.max(np.abs(weights.astype(float).mean(axis=0)[::-1]-profiles[part]["mean_weight_by_lag_1_to_L"]))))
            value=score(z[part],d["truth"][:,j],scale[j])["loss"]
            stored=metrics.loc[metrics.target.eq(row.target)&metrics.family.eq(row.family)&metrics.lookback.eq(row.lookback)&metrics.split.eq(part)].iloc[0].loss
            max_loss_diff=max(max_loss_diff,abs(value-stored),abs(value-at[part+"_eval_loss"]))
            b=persistence.loc[persistence.target.eq(row.target)&persistence.split.eq(part)].iloc[0].loss
            initial &= np.isclose(h.iloc[0][part+"_eval_loss"],b,atol=1e-6,rtol=0)
    checks.update(every_step_full_three_sets=complete,all_batch_counts=layout,validation_only_checkpoints=chosen,
        early_stop_15_full_epochs=stopping,single_target_heads_and_real_window_shapes=heads,epoch_zero_persistence=initial,
        attention_weights_normalised=weights_ok,checkpoint_replay=max_pred_diff<1e-6,
        independent_losses=max_loss_diff<1e-6,attention_profiles_replay=max_profile_diff<1e-6)
    checks={k:bool(v) for k,v in checks.items()};n=sum(len(h) for h in histories.values())
    audit={"checks":checks,"all_passed":all(checks.values()),"optimizer_steps":int(runs.steps.sum()),"evaluation_rows":n,"full_split_losses":3*n,
        "max_prediction_difference":max_pred_diff,"max_normalised_loss_difference":max_loss_diff,"max_profile_difference":max_profile_diff,
        "test_is_monitored_not_blind":True,"data_vintage_audited":False}
    dump(R/"AUDIT.json",audit);assert audit["all_passed"],audit
    return audit


def compare_all(result,metrics,runs,persistence):
    plain=pd.read_csv(ROOT/"baseline/results/GRID_METRICS.csv")
    effect=metrics.merge(plain,on=["target","family","lookback","split","seed"],suffixes=("_attention","_plain"),validate="one_to_one")
    assert len(effect)==126
    effect["loss_change_pct"]=100*(effect.loss_attention/effect.loss_plain-1)
    effect.to_csv(R/"MATCHED_WINDOW_COMPARISON.csv",index=False)
    plain_selected=json.loads((ROOT/"baseline/results/SELECTION_FROZEN.json").read_text())
    selected=[]
    for key,c in result["selected"].items():
        pc=plain_selected[key];row=runs.loc[runs.run.eq(c["run"])].iloc[0]
        rec={**c,"plain_lookback":pc["lookback"],"lr":float(row.lr),"epochs":int(row.epochs),"best_epoch":int(row.best_epoch)}
        for part in PARTS:
            a=metrics.loc[metrics.target.eq(c["target"])&metrics.family.eq(c["family"])&metrics.lookback.eq(c["lookback"])&metrics.split.eq(part)].iloc[0]
            b=plain.loc[plain.target.eq(c["target"])&plain.family.eq(c["family"])&plain.lookback.eq(pc["lookback"])&plain.split.eq(part)].iloc[0]
            base=persistence.loc[persistence.target.eq(c["target"])&persistence.split.eq(part)].iloc[0]
            for metric in ("loss","MSE","RMSE","MAE"):rec[part+"_"+metric]=float(a[metric]);rec["plain_"+part+"_"+metric]=float(b[metric])
            rec[part+"_change_pct"]=float(100*(a.loss/b.loss-1));rec[part+"_persistence_skill"]=float(1-a.loss/base.loss)
        selected.append(rec)
    pd.DataFrame(selected).to_csv(R/"SELECTED_COMPARISON.csv",index=False)
    return plain,effect,selected


def readout_diagnostics(selected,x,data,mean,scale):
    (ROOT/"selected_attention").mkdir(exist_ok=True);rows=[];summary=[]
    for c in selected:
        cp=torch.load(ROOT/"checkpoints"/(c["run"]+".pt"),weights_only=True);j=TARGETS.index(c["target"])
        model=Predictor(c["family"],j);model.load_state_dict(cp["state_dict"]);model.eval();saved={}
        profiles=json.loads((ROOT/"attention_profiles"/(c["run"]+".json")).read_text())
        for part,d in data.items():
            xx=torch.from_numpy(windows(x,d["origins"],c["lookback"]))
            for mode in ("attention","uniform","last_only"):
                with torch.inference_mode():p,w=model(xx,return_attention=True,mode=mode)
                pred=p.numpy().ravel().astype(float)*scale[j]+mean[j]
                record={"target":c["target"],"family":c["family"],"lookback":c["lookback"],"split":part,"readout_mode":mode,**score(pred,d["truth"][:,j],scale[j])}
                record["change_vs_attention_pct"]=100*(record["loss"]/c[part+"_loss"]-1);rows.append(record)
                if mode=="attention" and part!="train":
                    saved[part+"_weights"]=w.numpy();saved[part+"_origins"]=d["origins"]
            summary.append({"target":c["target"],"family":c["family"],"lookback":c["lookback"],"split":part,
                **{k:v for k,v in profiles[part].items() if k not in ("mean_weight_by_lag_1_to_L","recent_mass")},
                **{"mass_recent_"+k:val for k,val in profiles[part]["recent_mass"].items()}})
        saved["lag_to_target_days"]=np.arange(c["lookback"],0,-1)
        np.savez_compressed(ROOT/"selected_attention"/(c["run"]+".npz"),**saved)
    diagnostics=pd.DataFrame(rows);diagnostics.to_csv(R/"READOUT_DIAGNOSTICS.csv",index=False)
    pd.DataFrame(summary).to_csv(R/"ATTENTION_SUMMARY.csv",index=False)
    return diagnostics


def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    result=json.loads((R/"RESULTS.json").read_text());f,x,data,mean,scale=dataset.prepare()
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"GRID_METRICS.csv");persistence=pd.read_csv(ROOT/"baseline/results/PERSISTENCE.csv")
    histories={row.run:pd.read_csv(ROOT/row.step_log) for row in runs.itertuples()}
    pd.concat(histories.values(),ignore_index=True).to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    audit=audit_all(result,f,x,data,mean,scale,runs,metrics,persistence,histories)
    profiles=[]
    for row in runs.itertuples():
        p=json.loads((ROOT/"attention_profiles"/(row.run+".json")).read_text())
        for part,values in p.items():
            profiles.append({"target":row.target,"family":row.family,"lookback":row.lookback,"split":part,
                **{k:v for k,v in values.items() if k not in ("mean_weight_by_lag_1_to_L","recent_mass")},
                **{"mass_recent_"+k:v for k,v in values["recent_mass"].items()}})
    pd.DataFrame(profiles).to_csv(R/"ALL_ATTENTION_SUMMARY.csv",index=False)
    plain,effect,selected=compare_all(result,metrics,runs,persistence)
    diagnostics=readout_diagnostics(selected,x,data,mean,scale)
    plot_all(metrics,plain,effect,selected,histories,persistence)
    write_report(result,runs,metrics,plain,effect,selected,diagnostics,audit)
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cpu\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit),flush=True)
    print(pd.DataFrame(selected).to_string(index=False),flush=True)


def plot_all(metrics,plain,effect,selected,histories,persistence):
    folder=ROOT/"figures";folder.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    ordered=[(t,m) for t in TARGETS for m in ("RNN","LSTM")]
    bound=max(1.,float(effect.loc[effect.split.isin(["validation","test"]),"loss_change_pct"].abs().max()))
    norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
    fig,axes=plt.subplots(2,1,figsize=(13.5,10.2),layout="constrained")
    for ax,part in zip(axes,("validation","test")):
        values=np.array([[effect.loc[effect.target.eq(t)&effect.family.eq(m)&effect.lookback.eq(l)&effect.split.eq(part)].iloc[0].loss_change_pct for l in dataset.LOOKBACKS] for t,m in ordered])
        im=ax.imshow(values,cmap="RdBu_r",norm=norm,aspect="auto")
        for i,(t,m) in enumerate(ordered):
            chosen=next(c for c in selected if c["target"]==t and c["family"]==m)["lookback"]
            for k,l in enumerate(dataset.LOOKBACKS):
                ax.text(k,i,f"{values[i,k]:+.1f}%",ha="center",va="center",color="white" if abs(values[i,k])>.55*bound else "black",fontsize=11)
                if l==chosen:ax.add_patch(Rectangle((k-.48,i-.47),.96,.94,fill=False,edgecolor="black",lw=2))
        ax.set_xticks(np.arange(7),labels=[str(l) for l in dataset.LOOKBACKS]);ax.set_xlabel("History length (days)")
        ax.set_yticks(np.arange(6),labels=[EN[t]+" / "+m for t,m in ordered]);ax.set_title(part.capitalize());ax.tick_params(length=0)
    fig.suptitle("Attention versus plain encoder at the SAME history length — seed 17\nMSE change: negative is better; each model uses its own val checkpoint; boxes mark attention-selected windows",fontsize=12)
    fig.colorbar(im,ax=axes,shrink=.85,pad=.015,label="100 × (attention MSE / plain MSE − 1)")
    for ext in ("png","svg"):fig.savefig(folder/("matched_window_effect."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(13,11),layout="constrained")
    for j,t in enumerate(TARGETS):
        for k,m in enumerate(("RNN","LSTM")):
            c=next(c for c in selected if c["target"]==t and c["family"]==m);h=histories[c["run"]];ax=axes[j,k]
            for part in PARTS:
                base=persistence.loc[persistence.target.eq(t)&persistence.split.eq(part)].iloc[0].loss
                ax.plot(h.global_step,h[part+"_eval_loss"]/base,color=COLORS[part],lw=.9,label="Attention "+part)
                if part!="train":
                    p=plain.loc[plain.target.eq(t)&plain.family.eq(m)&plain.lookback.eq(c["lookback"])&plain.split.eq(part)].iloc[0]
                    ax.axhline(p.loss/base,color=COLORS[part],ls="--",lw=.9,alpha=.75,label="Plain same-window "+part)
            ax.axhline(1.,color="#777777",ls=":",lw=.8,label="Own-split copy-today")
            base=persistence.loc[persistence.target.eq(t)&persistence.split.eq("validation")].iloc[0].loss
            ax.scatter([c["best_step"]],[c["validation_loss"]/base],color="black",s=22,zorder=5,label="Val-selected checkpoint")
            ax.axvline(c["best_step"],color="#555555",ls=":",lw=.7,alpha=.5)
            ax.set(title=f"{EN[t]} / {m}+attention, L={c['lookback']}\nSelected step {c['best_step']}; stopped epoch {c['epochs']}",xlabel="Optimiser step",ylabel="MSE / own-split persistence MSE")
            ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=3,frameon=False,fontsize=9)
    fig.suptitle("Full train / validation / test loss after every update\nAttention-selected windows; dashed lines are the plain same-window checkpoint metrics",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("selected_step_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12.5,9.5),layout="constrained")
    for j,t in enumerate(TARGETS):
        for k,m in enumerate(("RNN","LSTM")):
            c=next(c for c in selected if c["target"]==t and c["family"]==m);ax=axes[j,k]
            p=json.loads((ROOT/"attention_profiles"/(c["run"]+".json")).read_text())
            for part in ("validation","test"):
                values=np.array(p[part]["mean_weight_by_lag_1_to_L"])*c["lookback"]
                ax.plot(np.arange(1,c["lookback"]+1),values,color=COLORS[part],label=part,lw=1.1)
            ax.axhline(1.,color="#777777",ls="--",lw=.8,label="Uniform pooling")
            if c["lookback"]>=56:ax.set_xscale("log",base=2)
            ticks=[v for v in [1,7,14,30,56,91,182,365] if v<=c["lookback"]]
            ax.set_xticks(ticks,labels=[str(v) for v in ticks]);ax.set(title=f"{EN[t]} / {m}+attention, L={c['lookback']}",xlabel="Hidden-state lag to forecast target (days)",ylabel="Mean attention / uniform weight")
            ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=3,frameon=False)
    fig.suptitle("Where the selected temporal readout places weight\nWeights describe recurrent hidden-state positions, not causal importance of raw daily observations",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("selected_attention_profiles."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def write_report(result,runs,metrics,plain,effect,selected,diagnostics,audit):
    valwins=int((effect.loc[effect.split.eq("validation"),"loss_change_pct"]<0).sum())
    testwins=int((effect.loc[effect.split.eq("test"),"loss_change_pct"]<0).sum())
    selected_valwins=sum(c["validation_change_pct"]<0 for c in selected)
    selected_testwins=sum(c["test_change_pct"]<0 for c in selected)
    lines=["# RNN/LSTM 加入时间注意力：七窗口对照","",
        f"供给、需求、电价分别训练独立的 RNN+attention 和 LSTM+attention，固定 seed 17，七个历史窗口，共 42 次新拟合。与冻结的普通模型比较：相同窗口下，val MSE 在 {valwins}/42 个配置中降低，test 在 {testwins}/42 个配置中降低。两种架构各自按 val 选窗口后，六组中 {selected_valwins} 组 val 更低，{selected_testwins} 组 test 更低。以下均为单种子实验，42 个窗口配置不是 42 个独立随机重复。","",
        "## 机制与参数量","",
        "普通模型用最后一个循环隐藏状态输出预测。本轮保留这个通道，同时让最后状态查询窗口内各天的隐藏状态，得到加权上下文，再一起输出次日变化。模型输入仍为历史供给、需求、电价和日历特征；循环层及隐藏维度不变。","",
        "设窗口为第 $t-L+1$ 天至第 $t$ 天，编码器输出为 $h_i\\in\\mathbb R^H$。最后状态 $h_t$ 是 query（查询向量），各位置状态是 key/value（用于打分和汇总的向量）：","",
        "$$","s_i=\\frac{h_i^\\top h_t}{\\sqrt H},\\qquad \\alpha_i=\\frac{\\exp(s_i)}{\\sum_{j=t-L+1}^{t}\\exp(s_j)},\\qquad r_t=\\sum_{i=t-L+1}^{t}\\alpha_i h_i.","$$","",
        "以训练期标准化后的目标 $z_t$ 为持续值基准，输出层的权重和偏置分别为 $w$、$b$：","",
        "$$","\\widehat z_{t+1}=z_t+w^\\top[h_t;r_t]+b.","$$","",
        "采用单查询 scaled dot-product attention（缩放点积注意力），没有单独的 Q/K/V 投影矩阵；打分依赖循环层学到的表示，梯度可沿加权汇总直接传到较早位置。注意力权重随输入变化，整个模型端到端训练。注意力计算为 $O(LH)$，没有 $L\\times L$ 的自注意力矩阵。","",
        "| 家族 | 隐藏维度 | 普通模型参数 | 加注意力后参数 | 增加 |","|---|---:|---:|---:|---:|",
        "| RNN | 68 | 5,373 | 5,441 | 68（1.27%） |",
        "| LSTM | 32 | 5,409 | 5,441 | 32（0.59%） |","",
        "增加的参数来自输出层新增的上下文通道。两个模型的规模仍约为 5.4k。初始循环层权重与对应普通模型在同一种子下逐元素一致；输出层初始化为零，所以 step 0 都等于照抄今天。","",
        "## 数据、训练和选择规则","",
        "| 分区 | 预测目标日期 | 样本数 |","|---|---|---:|",
        "| Train | 2022-01-01—2024-12-31 | 1,096 |",
        "| Val | 2025-01-01—2025-08-31 | 243 |",
        "| Test | 2025-09-01—2026-08-31 | 365 |","",
        "窗口为 365、182、91、56、30、14、7 天。2021 年仅提供历史输入，所有窗口训练目标日期一致；scaler 只拟合 2022–2024 年。冻结输入和普通模型完全相同，总供给包含独立风场，电价为名义 £/MWh。","",
        "固定上一轮目标/家族的学习率：供给 RNN/LSTM 0.003/0.003，需求 0.001/0.003，电价 0.001/0.003。每模型独立训练，batch64、18 step/epoch；AdamW、weight decay 0.0001、dropout 0.1、梯度范数截断 1。最多 120 epoch，连续 15 个完整 epoch 无 val 改善则停止。","",
        "每次更新后关闭 dropout，完整评估 train、val、test 并刷新 CSV。checkpoint 只用 val MSE，最小改善阈值 0.00001；各家族的窗口也只按 val 选择。Test 只记录和报告。本轮 test 已在多轮开发中监测，不是新的盲测。三个目标在独立 CPU 进程计算，每进程两线程。","",
        "## 相同窗口下的注意力增量","",
        "下图比较相同目标、模型家族和历史长度，双方各自使用 val 最优 checkpoint。数值为 100 ×（注意力 MSE / 普通模型 MSE − 1）：负值表示注意力误差更低。方框仅标出注意力架构按 val 选中的窗口，在 test 面板沿用同一选择。","",
        "![相同窗口的注意力增量](figures/matched_window_effect.png)","",
        "## 双方各自选窗口后的比较","",
        "以下按各自七窗口搜索的 val 最优结果比较。Loss 是单目标、每样本平均的标准化 MSE；三个分区使用相同训练期标准差。","",
        "| 目标 | 家族 | 普通窗口 | 注意力窗口 | 普通 Val | 注意力 Val | Val 变化 | 普通 Test | 注意力 Test | Test 变化 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for c in selected:
        lines.append(f"| {ZH[c['target']]} | {c['family']} | {c['plain_lookback']} | {c['lookback']} | {c['plain_validation_loss']:.6f} | {c['validation_loss']:.6f} | {c['validation_change_pct']:+.2f}% | {c['plain_test_loss']:.6f} | {c['test_loss']:.6f} | {c['test_change_pct']:+.2f}% |")
    lines += ["","| 目标 | 家族 | 注意力 Train | 注意力 Val | 注意力 Test | Test 相对照抄改善 | 最佳 step | 停止 epoch |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for c in selected:
        lines.append(f"| {ZH[c['target']]} | {c['family']} | {c['train_loss']:.6f} | {c['validation_loss']:.6f} | {c['test_loss']:.6f} | {100*c['test_persistence_skill']:.2f}% | {c['best_step']} | {c['epochs']} |")
    long_chosen=sum(c["lookback"]>=91 for c in selected)
    lines += ["",f"六组注意力模型中，{long_chosen} 组选中至少 91 天的窗口。注意力是否改善泛化，需要同时查看相同窗口的配对结果和各自选窗口后的 test；增加早期状态的读取通道不自动保证长历史有益。","",
        "本轮的主要变化集中在电价。双方各自按 val 选窗后，电价 RNN 的 val/test MSE 分别下降约 1.87%/0.61%，电价 LSTM 下降约 3.13%/2.60%；供给两组的 test 反而增加。需求 LSTM 的 test 仅下降约 0.015%，可视为基本持平。它们是本轮单种子的观察，不能据此把六组都替换为注意力模型。","",
        "![所选注意力模型逐 step 轨迹](figures/selected_step_losses.png)","",
        "曲线为完整分区的逐 step 平均 loss，分别除以该分区照抄今天的 MSE；1 表示照抄水平。虚线给出普通模型在相同窗口下的 val 最优 checkpoint 的 val/test 水平，不是普通模型的完整训练曲线。","",
        "## 注意力读取方式诊断","",
        "对已训练、已按 val 选定的 checkpoint 保持所有参数不变，只在推理时将动态权重替换为均匀权重，或只读取最后一个状态。它检验当前权重对聚合方式的依赖，没有重新训练，不能把它当成另一种架构的公平训练结果。也未用这些诊断重新选择模型。","",
        "| 目标 | 家族 | 窗口 | 均匀读取 Val 变化 | 均匀读取 Test 变化 | 仅末状态 Val 变化 | 仅末状态 Test 变化 |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for c in selected:
        g=diagnostics.loc[diagnostics.target.eq(c["target"])&diagnostics.family.eq(c["family"])]
        vals=[g.loc[g.split.eq(p)&g.readout_mode.eq(mode)].iloc[0].change_vs_attention_pct for mode in ("uniform","last_only") for p in ("validation","test")]
        lines.append(f"| {ZH[c['target']]} | {c['family']} | {c['lookback']} | "+" | ".join(f"{v:+.2f}%" for v in vals)+" |")
    lines += ["","正值表示替换读取方式后误差增加；负值表示该固定 checkpoint 在替换后误差反而下降。","",
        "所选电价 LSTM 改用均匀权重后 test MSE 仅增加约 0.10%，说明这个已训练模型的预测对细致权重分配并不敏感。相对地，需求 RNN 改用均匀权重后 test MSE 增加约 5.85%，表明它对动态分配更敏感，尽管它仍未超过普通 RNN。注意力参与预测与注意力提高泛化表现是两个需要分别检验的问题。","",
        "![注意力分配](figures/selected_attention_profiles.png)","",
        "横轴是隐藏状态位置距预测目标日的天数，1 表示最后已知日。纵轴为该位置平均权重除以均匀权重；1 表示等于均匀分配。循环隐藏状态本身包含其此前的信息，因此这张图不能直接解释为原始某一天的因果贡献。逐样本 val/test 权重保存在 selected_attention/。","",
        "## 全部窗口的三分区误差","",
        "| 目标 | 家族 | 历史/天 | Train | Val | Test | 同窗 Val 变化 | 同窗 Test 变化 |","|---|---|---:|---:|---:|---:|---:|---:|"]
    for t in TARGETS:
        for m in ("RNN","LSTM"):
            for length in dataset.LOOKBACKS:
                g=metrics.loc[metrics.target.eq(t)&metrics.family.eq(m)&metrics.lookback.eq(length)].set_index("split")
                d=effect.loc[effect.target.eq(t)&effect.family.eq(m)&effect.lookback.eq(length)].set_index("split")
                lines.append(f"| {ZH[t]} | {m} | {length} | {g.loc['train','loss']:.6f} | {g.loc['validation','loss']:.6f} | {g.loc['test','loss']:.6f} | {d.loc['validation','loss_change_pct']:+.2f}% | {d.loc['test','loss_change_pct']:+.2f}% |")
    lines += ["","## 原始单位的所选模型 Test 指标","",
        "供给、需求的 RMSE/MAE 为 MW；电价为 £/MWh。","",
        "| 目标 | 家族 | 窗口 | Test MSE | Test RMSE | Test MAE |","|---|---|---:|---:|---:|---:|"]
    for c in selected:lines.append(f"| {ZH[c['target']]} | {c['family']}+attention | {c['lookback']} | {c['test_MSE']:,.3f} | {c['test_RMSE']:,.3f} | {c['test_MAE']:,.3f} |")
    lines += ["","## 审计与复现","",
        f"完成 42 次新拟合、{audit['optimizer_steps']:,} 次权重更新。含 step 0 共 {audit['evaluation_rows']:,} 行完整评估、{audit['full_split_losses']:,} 个分区平均 loss。注意力打分经独立 NumPy 复算，初始循环层与普通模型一致、早期位置梯度、权重和/非负性、冻结数据与基准、同一 scaler、真实窗口形状、逐 step 日志、val 选点/选窗及早停检查通过。全部 42 个 checkpoint 重放最大预测差 {audit['max_prediction_difference']:.3g}，标准化 loss 最大复算差 {audit['max_normalised_loss_difference']:.3g}。","",
        "- model.py：循环编码器、时间注意力和输出；preflight.py：计算、梯度和初始状态检查。",
        "- run.py、fit_core.py、data.py：三目标进程、训练和逐 step 评估、冻结数据划分。",
        "- results/MATCHED_WINDOW_COMPARISON.csv：同窗口配对；SELECTED_COMPARISON.csv：各自选窗后的比较。",
        "- results/GRID_METRICS.csv、ALL_STEP_LOSSES.csv：全部模型指标与逐 step 三集 loss。",
        "- results/READOUT_DIAGNOSTICS.csv、ATTENTION_SUMMARY.csv、ALL_ATTENTION_SUMMARY.csv：读取方式、所选模型和全部配置的权重摘要。",
        "- checkpoints/、predictions/、attention_profiles/、selected_attention/：权重、预测、平均和逐样本注意力。",
        "- baseline/：冻结的普通模型数据；BASELINE_MANIFEST.json、PROTOCOL.json、PREFLIGHT.json、results/AUDIT.json：证据与核验。","",
        "安装 requirements.txt 后，在新副本运行 python preflight.py、python run.py、python analyse.py。已有产物可直接运行分析脚本。训练时 test 可见且已多轮使用，本轮只做探索性单种子对照；尚未审计历史数据的逐日发布版本，未增加外部数据、MPC 收益、上传或修改正式候选报告。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
