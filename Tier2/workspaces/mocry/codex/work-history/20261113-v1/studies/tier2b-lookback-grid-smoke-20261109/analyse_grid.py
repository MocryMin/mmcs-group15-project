"""Audit all lookback cases, replay checkpoints and compare validation-selected windows."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import run_grid as exp
from fit_core import dump,sha,score
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
if not exp.PREVIOUS.exists():exp.PREVIOUS=ROOT/"reference_previous"
R=ROOT/"results"
PARTS=("train","validation","test")
ZH={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
COLORS={"train":"#245c91","validation":"#ba7426","test":"#38804b"}


def audit_all(result,f,x,data,mean,scale,runs,metrics,baselines,selection,histories):
    expected={(t,m,l) for t in TARGETS for m in ("RNN","LSTM") for l in exp.LOOKBACKS}
    observed=set(zip(runs.target,runs.family,runs.lookback))
    checks={"complete_42_case_grid":len(runs)==42 and observed==expected,
        "complete_126_case_split_metrics":len(metrics)==126 and metrics.groupby(["target","family","lookback"]).size().eq(3).all(),
        "fixed_seed":runs.seed.eq(17).all(),"fixed_training_dates":{p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365},
        "three_identical_previous_cases_reused":runs.reused_previous.sum()==3,
        "frozen_code_and_config_hashes":all(sha(ROOT/n)==v for n,v in result["protocol"]["source_hashes"].items()),
        "frozen_input_hash":sha(ROOT/"inputs/model_daily.csv")==json.loads((ROOT/"inputs/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))["derived_sha256"],
        "train_only_scaling":np.array_equal(mean,f.loc["2022":"2024",TARGETS].mean().to_numpy()) and np.array_equal(scale,f.loc["2022":"2024",TARGETS].std(ddof=0).to_numpy()),
        "2021_used_as_history_only":min(f.index[d["origins"]+1].min() for d in data.values())==pd.Timestamp("2022-01-01"),
        "365_day_context_available":f.index[0]==pd.Timestamp("2021-01-01") and min(d["origins"].min() for d in data.values())>=364,
        "test_excluded_from_grid_selection":all(selection[t+"|"+m]["run"]==runs.loc[runs.target.eq(t)&runs.family.eq(m)].sort_values(["best_validation_loss","lookback"]).iloc[0].run for t in TARGETS for m in ("RNN","LSTM"))}
    if (ROOT/"EXECUTION.json").exists():
        execution=json.loads((ROOT/"EXECUTION.json").read_text(encoding="utf-8"))
        checks["parallel_execution_code_hash"]=sha(ROOT/"grid_jobs.py")==execution["worker_source_sha256"]
        checks["parallel_targets_completed"]=execution.get("all_targets_complete",False)
    traces=layout=selected=stopping=reused=initial=heads=True
    max_loss_diff=max_pred_diff=0.
    for row in runs.itertuples():
        h=histories[row.run];j=TARGETS.index(row.target)
        traces &= np.array_equal(h.global_step,np.arange(row.steps+1)) and len(h)==row.steps+1
        traces &= np.isfinite(h[[p+"_eval_loss" for p in PARTS]].to_numpy()).all()
        layout &= row.steps==row.epochs*18 and np.array_equal(h.iloc[1:].batch_size_actual,np.tile([64]*17+[8],row.epochs))
        layout &= np.array_equal(h.iloc[1:].epoch,np.repeat(np.arange(1,row.epochs+1),18))
        layout &= np.array_equal(h.iloc[1:].batch_index,np.tile(np.arange(1,19),row.epochs))
        expected_seen=np.repeat(np.arange(row.epochs)*1096,18)+np.tile(np.cumsum([64]*17+[8]),row.epochs)
        layout &= np.array_equal(h.iloc[1:].samples_seen,expected_seen)
        best=float("inf");beststep=0;bestepoch=0
        for z in h.itertuples():
            improved=z.validation_eval_loss<best-1e-5
            selected &= bool(z.checkpoint_improved)==improved
            if improved:best=z.validation_eval_loss;beststep=z.global_step;bestepoch=z.epoch
            selected &= np.isclose(best,z.best_validation_so_far,atol=1e-12,rtol=0)
        selected &= beststep==row.best_step and bestepoch==row.best_epoch
        stopping &= row.epochs==120 or row.epochs-bestepoch==15
        cp_path=ROOT/row.checkpoint.replace("\\","/")
        cp=torch.load(cp_path,weights_only=True);m=Predictor(row.family,j);m.load_state_dict(cp["state_dict"]);m.eval()
        heads &= m.head.out_features==1 and cp["target_index"]==j and cp["best_step"]==row.best_step
        heads &= cp["lookback"]==row.lookback and row.parameters==(5373 if row.family=="RNN" else 5409)
        if row.reused_previous:
            reused &= sha(cp_path)==sha(exp.PREVIOUS/row.checkpoint.replace("\\","/"))
            reused &= sha(ROOT/row.step_log.replace("\\","/"))==sha(exp.PREVIOUS/row.step_log.replace("\\","/"))
        exported=np.load(ROOT/"predictions"/(row.run+".npz"));at=h.loc[h.global_step.eq(row.best_step)].iloc[0]
        for part,d in data.items():
            xx=torch.from_numpy(windows(x,d["origins"],row.lookback))
            heads &= xx.shape[1]==row.lookback and xx.shape[2]==8
            with torch.inference_mode():pred=m(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
            max_pred_diff=max(max_pred_diff,float(np.max(np.abs(pred-exported[part]))))
            loss=score(exported[part],d["truth"][:,j],scale[j])["loss"]
            metric=metrics.loc[metrics.target.eq(row.target)&metrics.family.eq(row.family)&metrics.lookback.eq(row.lookback)&metrics.split.eq(part)].iloc[0]
            max_loss_diff=max(max_loss_diff,abs(loss-metric.loss),abs(loss-at[part+"_eval_loss"]))
            base=baselines.loc[baselines.target.eq(row.target)&baselines.split.eq(part)].iloc[0].loss
            initial &= np.isclose(h.iloc[0][part+"_eval_loss"],base,atol=1e-6,rtol=0)
    checks.update(every_step_full_three_sets=traces,batch_layout_and_counts=layout,validation_only_checkpoint_reconstructed=selected,
        early_stopping_15_full_epochs=stopping,reused_weights_and_logs_identical=reused,initial_persistence=initial,
        independent_scalar_heads_and_constant_parameter_counts=heads,all_checkpoint_predictions_replay=max_pred_diff<1e-6,
        all_three_losses_independently_recalculate=max_loss_diff<1e-6)
    checks={k:bool(v) for k,v in checks.items()};rows=sum(len(h) for h in histories.values())
    audit={"checks":checks,"all_passed":all(checks.values()),"cases":42,"fresh_fits":39,"reused_fits":3,
        "optimizer_steps_including_reused":int(runs.steps.sum()),"fresh_optimizer_steps":int(runs.loc[~runs.reused_previous,"steps"].sum()),
        "evaluation_rows":rows,"full_split_losses":rows*3,"max_prediction_difference":max_pred_diff,"max_loss_difference":max_loss_diff,
        "single_seed_smoke_not_stability_estimate":True,"test_is_monitored_not_blind":True,"data_vintage_audited":False}
    dump(R/"AUDIT.json",audit);assert audit["all_passed"],audit
    return audit


def plot_all(runs,metrics,baselines,selection,histories):
    figures=ROOT/"figures";figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    ticks=sorted(exp.LOOKBACKS)
    ordered=[(t,m) for t in TARGETS for m in ("RNN","LSTM")]
    values=np.array([[metrics.loc[metrics.target.eq(t)&metrics.family.eq(m)&metrics.lookback.eq(l)&metrics.split.eq("validation")].iloc[0].loss for l in exp.LOOKBACKS] for t,m in ordered])
    ratios=values/values.min(axis=1,keepdims=True);vmax=max(1.01,float(ratios.max()))
    fig,ax=plt.subplots(figsize=(12.8,5.2),layout="constrained")
    im=ax.imshow(ratios,cmap="Greys",vmin=1.,vmax=vmax,aspect="auto")
    for i,(t,m) in enumerate(ordered):
        for k,l in enumerate(exp.LOOKBACKS):
            color="white" if (ratios[i,k]-1)/(vmax-1)>.55 else "black"
            ax.text(k,i,f"{values[i,k]:.6f}",ha="center",va="center",color=color,fontsize=11)
            if selection[t+"|"+m]["lookback"]==l:ax.add_patch(Rectangle((k-.48,i-.47),.96,.94,fill=False,edgecolor="#087caa",lw=2.1))
    ax.set_xticks(np.arange(7),labels=["365 days\n1 year","182 days\nhalf year","91 days\n3 months","56 days","30 days","14 days","7 days"])
    ax.set_yticks(np.arange(6),labels=[EN[t]+" / "+m for t,m in ordered])
    ax.set_title("Validation MSE across input-history windows — seed 17\nCell: standardised MSE; shade: ratio to row minimum; outline: validation-selected window",pad=13)
    ax.tick_params(length=0);fig.colorbar(im,ax=ax,pad=.025,label="Val MSE / minimum within same row")
    for ext in ("png","svg"):fig.savefig(figures/("validation_grid_heatmap."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(15,10.8),layout="constrained")
    for j,t in enumerate(TARGETS):
        for k,p in enumerate(PARTS):
            ax=axes[j,k]
            for family,color,marker in (("RNN","#245c91","o"),("LSTM","#ba7426","s")):
                g=metrics.loc[metrics.target.eq(t)&metrics.family.eq(family)&metrics.split.eq(p)].sort_values("lookback")
                ax.plot(g.lookback,g.loss,color=color,marker=marker,ms=4,lw=1.1,label=family)
                chosen=selection[t+"|"+family]["lookback"];r=g.loc[g.lookback.eq(chosen)].iloc[0]
                ax.scatter([chosen],[r.loss],s=95,facecolors="none",edgecolors=color,linewidths=1.4,zorder=5)
            base=baselines.loc[baselines.target.eq(t)&baselines.split.eq(p)].iloc[0].loss
            ax.set_xscale("log",base=2);ax.set_xticks(ticks,labels=[str(v) for v in ticks])
            ax.set(title=f"{EN[t]} / {p.capitalize()}\nCopy-today MSE: {base:.6f}",xlabel="History length (days; log spacing)",ylabel="Train-standardised MSE")
            ax.grid(alpha=.15)
    fig.suptitle("Input-history smoke grid: fixed dates, architecture and learning rate; seed 17\nAll points use their own validation-selected checkpoint; rings mark validation-selected window",fontsize=12)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=3,frameon=False)
    for ext in ("png","svg"):fig.savefig(figures/("lookback_grid."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    for relative in (False,True):
        fig,axes=plt.subplots(3,2,figsize=(13,11),layout="constrained")
        for j,t in enumerate(TARGETS):
            for k,family in enumerate(("RNN","LSTM")):
                chosen=selection[t+"|"+family];row=runs.loc[runs.run.eq(chosen["run"])].iloc[0];h=histories[row.run];ax=axes[j,k]
                for part in PARTS:
                    base=baselines.loc[baselines.target.eq(t)&baselines.split.eq(part)].iloc[0].loss
                    denom=base if relative else 1.
                    ax.plot(h.global_step,h[part+"_eval_loss"]/denom,color=COLORS[part],lw=.9,label=part.capitalize())
                    if not relative:ax.axhline(base,color=COLORS[part],ls="--",alpha=.55,lw=.8,label=part.capitalize()+" copy-today")
                if relative:ax.axhline(1.,color="#777777",ls="--",lw=.9,label="Own-split copy-today")
                best=h.loc[h.global_step.eq(row.best_step)].iloc[0]
                denom=baselines.loc[baselines.target.eq(t)&baselines.split.eq("validation")].iloc[0].loss if relative else 1.
                ax.scatter([row.best_step],[best.validation_eval_loss/denom],color="black",s=22,zorder=5,label="Val-selected checkpoint")
                ax.axvline(row.best_step,color="#444444",ls=":",lw=.7,alpha=.6)
                ax.set(title=f"{EN[t]} / {family}, L={row.lookback}, seed 17\nSelected step {row.best_step}; stopped epoch {row.epochs}",xlabel="Optimiser step",
                    ylabel="MSE / own-split persistence MSE" if relative else "Train-standardised MSE")
                ax.grid(alpha=.15)
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False,fontsize=9)
        fig.suptitle("Every-step full-set loss trajectories of validation-selected input windows\nWindow and checkpoint chosen by validation only; no smoothing",fontsize=12)
        stem="selected_relative_step_losses" if relative else "selected_step_losses"
        for ext in ("png","svg"):fig.savefig(figures/(stem+"."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
        plt.close(fig)


def main():
    torch.set_num_threads(2)
    result=json.loads((R/"RESULTS.json").read_text(encoding="utf-8"));selection=result["selected"]
    f,x,data,mean,scale=exp.prepare();exp.previous_equivalence(f,x,data,mean,scale)
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"GRID_METRICS.csv");baselines=pd.read_csv(R/"PERSISTENCE.csv")
    histories={row.run:pd.read_csv(ROOT/row.step_log.replace("\\","/")) for row in runs.itertuples()}
    history=pd.concat(histories.values(),ignore_index=True);history.to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    audit=audit_all(result,f,x,data,mean,scale,runs,metrics,baselines,selection,histories)
    selected=[]
    for key,c in selection.items():
        run=runs.loc[runs.run.eq(c["run"])].iloc[0];h=histories[run.run]
        rec={**c,"lr":float(run.lr),"epochs":int(run.epochs),"best_epoch":int(run.best_epoch)}
        for part in PARTS:
            s=metrics.loc[metrics.target.eq(c["target"])&metrics.family.eq(c["family"])&metrics.lookback.eq(c["lookback"])&metrics.split.eq(part)].iloc[0]
            b=baselines.loc[baselines.target.eq(c["target"])&baselines.split.eq(part)].iloc[0]
            for name in ("loss","MSE","RMSE","MAE"):rec[part+"_"+name]=float(s[name])
            rec[part+"_skill"]=float(1-s.loss/b.loss)
            rec["final_"+part+"_loss"]=float(h.iloc[-1][part+"_eval_loss"])
        selected.append(rec)
    pd.DataFrame(selected).to_csv(R/"SELECTED_SUMMARY.csv",index=False)
    rankings=runs.sort_values(["target","family","best_validation_loss","lookback"]).copy()
    rankings["validation_rank"]=rankings.groupby(["target","family"]).cumcount()+1
    rankings.to_csv(R/"VALIDATION_RANKING.csv",index=False)
    plot_all(runs,metrics,baselines,selection,histories)
    write_report(result,runs,metrics,baselines,selected,audit)
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cpu\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit),flush=True)
    print(pd.DataFrame(selected).to_string(index=False),flush=True)


def write_report(result,runs,metrics,baselines,selected,audit):
    lines=["# 输入历史长度 grid smoke：独立次日 RNN/LSTM","",
        "按照用户指定的七种历史长度，分别测试供给、需求、电价的独立 RNN 与 LSTM。每个目标/模型有七个窗口，共 42 个配置。固定随机种子 17，本轮用于筛选窗口，不估计跨种子的稳定性。","",
        "## 控制变量与数据划分","",
        "窗口分别为 365、182、91、56、30、14、7 天。年、半年、三个月按固定天数解释，没有按日历月改变窗口长度。所有窗口均预测下一天，使用完全相同的训练、验证、测试目标日期。","",
        "| 分区 | 目标日期 | 样本数 |","|---|---|---:|",
        "| Train | 2022-01-01—2024-12-31 | 1,096 |",
        "| Val | 2025-01-01—2025-08-31 | 243 |",
        "| Test | 2025-09-01—2026-08-31 | 365 |","",
        "补入 2021-01-01—12-31 作为历史输入，保证 365 天窗口也不减少训练目标日。2021 年不作为训练标签，不参与 scaler 拟合。三个分区共用 2022–2024 年拟合的均值和标准差。供给为课程总发电加独立风场，日均 MW；电价为名义 £/MWh。","",
        "每个模型输入窗口内的供给、需求、电价历史及五个日历特征，独立输出自己的次日目标，不共享参数。RNN 为单层 tanh，68 隐藏单元、5,373 参数；LSTM 为单层，32 隐藏单元、5,409 参数。增加窗口不增加网络参数。","",
        "| 目标 | RNN 学习率 | LSTM 学习率 |","|---|---:|---:|"]
    for t in TARGETS:
        a=runs.loc[runs.target.eq(t)&runs.family.eq("RNN")].iloc[0].lr
        b=runs.loc[runs.target.eq(t)&runs.family.eq("LSTM")].iloc[0].lr
        lines.append(f"| {ZH[t]} | {a:g} | {b:g} |")
    lines += ["","学习率沿用此前每目标/家族的配置，不随窗口重新调参。其余保持 batch size 64、18 step/epoch、AdamW、weight decay 0.0001、dropout 0.1、梯度范数截断 1、最多 120 epoch、连续 15 个完整 epoch 无 val 改善早停。","",
        "每次权重更新后完整评估 train、val、test，写入并刷新 CSV。checkpoint 只根据 val MSE 选择，改善阈值 0.00001；窗口排序同样只用最佳 val。测试曲线只记录和报告。三个已有的 56 天、seed 17 实验，经逐元素验证三个分区的 float32 输入、标签及 scaler 完全相同后，直接复用原 checkpoint 和完整日志；其余 39 个配置从头训练。","",
        "三个目标使用独立进程计算，每进程两线程；完整日志、权重和预测汇总后统一重放核验。执行记录保留在 EXECUTION.json 与 execution_logs/，不影响训练和选点规则。","",
        "## 七种窗口的 Val loss","",
        "loss 为单目标标准化 MSE，即每个样本的平均误差平方除以训练期方差。以下每个数字对应该窗口自己的 val 最优 checkpoint；加粗为该目标/家族中按 val 选中的窗口。","",
        "| 目标 | 模型 | 365 天 | 182 天 | 91 天 | 56 天 | 30 天 | 14 天 | 7 天 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for t in TARGETS:
        for family in ("RNN","LSTM"):
            c=result["selected"][t+"|"+family];values=[]
            for length in exp.LOOKBACKS:
                v=metrics.loc[metrics.target.eq(t)&metrics.family.eq(family)&metrics.lookback.eq(length)&metrics.split.eq("validation")].iloc[0].loss
                values.append(("**" if length==c["lookback"] else "")+f"{v:.6f}"+("**" if length==c["lookback"] else ""))
            lines.append("| "+ZH[t]+" | "+family+" | "+" | ".join(values)+" |")
    lines += ["","![七种窗口的验证误差](figures/validation_grid_heatmap.png)","",
        "![各窗口的完整三分区比较](figures/lookback_grid.png)","",
        "图中的空心圈标出 val 所选窗口在三个分区的位置。Test 面板没有另选最低点；横轴按天数对数间距显示。","",
        "## 每个目标/模型的 Val 所选窗口","",
        "以下均为单种子结果，不是三种子均值。Test 相对改善为 1 − 模型 MSE / 同分区照抄今天 MSE。","",
        "| 目标 | 模型 | 窗口/天 | Train loss | Val loss | Test loss | Test 相对照抄改善 | 最佳 step | 停止 epoch |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in selected:
        lines.append(f"| {ZH[c['target']]} | {c['family']} | {c['lookback']} | {c['train_loss']:.6f} | {c['validation_loss']:.6f} | {c['test_loss']:.6f} | {100*c['test_skill']:.2f}% | {c['best_step']} | {c['epochs']} |")
    lines += ["","![所选窗口的逐 step loss](figures/selected_step_losses.png)","",
        "![所选窗口相对照抄的逐 step loss](figures/selected_relative_step_losses.png)","",
        "## 相对上一轮窗口的变化","",
        "只比较同一 seed 17、同一学习率的 val 最优 checkpoint。上一轮窗口不一定在本轮候选中：28 天替换为本轮要求的 30 天，因此这里列明原窗口。此表仅供追踪窗口搜索的增益，不用 Test 选择窗口。","",
        "| 目标 | 模型 | 原窗口/天 | 原 Val loss | 本轮所选/天 | 本轮 Val loss | Val 相对变化 | Test 相对变化 |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    previous=pd.read_csv(exp.PREVIOUS/"results/training_runs.csv")
    for c in selected:
        old=previous.loc[previous.target.eq(c["target"])&previous.family.eq(c["family"])&previous.seed.eq(17)].iloc[0]
        delta=100*(c["validation_loss"]/old.best_validation_loss-1)
        test_delta=100*(c["test_loss"]/old.test_loss_at_val_checkpoint-1)
        lines.append(f"| {ZH[c['target']]} | {c['family']} | {int(old.lookback)} | {old.best_validation_loss:.6f} | {c['lookback']} | {c['validation_loss']:.6f} | {delta:+.2f}% | {test_delta:+.2f}% |")
    lines += ["","## 原始单位的 Test 误差","",
        "供给、需求的 RMSE/MAE 为 MW；电价为 £/MWh。","",
        "| 目标 | 方法 | 窗口/天 | Test MSE | Test RMSE | Test MAE |","|---|---|---:|---:|---:|---:|"]
    for t in TARGETS:
        b=baselines.loc[baselines.target.eq(t)&baselines.split.eq("test")].iloc[0]
        lines.append(f"| {ZH[t]} | 照抄今天 | 1 | {b.MSE:,.3f} | {b.RMSE:,.3f} | {b.MAE:,.3f} |")
        for c in (z for z in selected if z["target"]==t):
            lines.append(f"| {ZH[t]} | {c['family']} | {c['lookback']} | {c['test_MSE']:,.3f} | {c['test_RMSE']:,.3f} | {c['test_MAE']:,.3f} |")
    lines += ["","## 全部配置的 Train / Val / Test loss","",
        "| 目标 | 模型 | 窗口/天 | Train | Val | Test | 最佳 epoch | 停止 epoch |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for t in TARGETS:
        for family in ("RNN","LSTM"):
            for length in exp.LOOKBACKS:
                row=runs.loc[runs.target.eq(t)&runs.family.eq(family)&runs.lookback.eq(length)].iloc[0]
                g=metrics.loc[metrics.target.eq(t)&metrics.family.eq(family)&metrics.lookback.eq(length)].set_index("split")
                lines.append(f"| {ZH[t]} | {family} | {length} | {g.loc['train','loss']:.6f} | {g.loc['validation','loss']:.6f} | {g.loc['test','loss']:.6f} | {int(row.best_epoch)} | {int(row.epochs)} |")
    longest=metrics.loc[metrics.lookback.eq(365)&metrics.split.eq("validation")].set_index(["target","family"])
    shortest=metrics.loc[metrics.lookback.eq(7)&metrics.split.eq("validation")].set_index(["target","family"])
    nlong=sum(float(longest.loc[(t,m),"loss"])<float(shortest.loc[(t,m),"loss"]) for t in TARGETS for m in ("RNN","LSTM"))
    test_improved=sum(c["test_loss"]<previous.loc[previous.target.eq(c["target"])&previous.family.eq(c["family"])&previous.seed.eq(17)].iloc[0].test_loss_at_val_checkpoint for c in selected)
    lines += ["","## 解释与下一步","",
        "六组按 val 选出的窗口均为 7–30 天，没有半年或一年窗口胜出。供给两组相对原窗口的 val 改善都不足 0.04%，基本持平。需求 RNN 的 7 天和电价 LSTM 的 14 天分别降低 val 约 2.58% 和 2.51%，是这轮较明显的验证集变化。","",
        f"相对原来同一 seed 17 的配置，六组中只有 {test_improved} 组的 test MSE 下降。需求 RNN 的 7 天 val 更低，test 却增加约 0.28%；电价 LSTM 的 14 天 val 更低，test 增加约 2.46%。窗口搜索降低 val 最小值，不保证外推到后一年的误差也下降。本轮结果适合作为多种子复核的候选，不能仅凭这一次排序认定换窗口已经提高泛化表现。表中正的 Test 变化表示误差增加。","",
        f"365 天窗口的 val loss 在六组中有 {nlong} 组低于 7 天窗口。应结合全部七个点判断长历史是否带来稳定趋势；单次最小值仅作为候选。延长输入意味着模型可以看到更远的过去，不等于已经证明网络有效利用了全年规律。窗口、网络家族和学习率之间仍可能有交互，本轮固定学习率，未进行联合搜索。","",
        "所选窗口需要多种子复核，特别是差距小的情况。本轮 test 沿用用户要求的逐 step 监测方式，已在前几轮查看，不是新的盲测；后续若据这些 test 结果改模型，应将它视为开发过程中反复查看的数据。所有 checkpoint、早停和本轮窗口选择均只用 val。预测对 MPC 经济收益的影响本轮尚未计算。","",
        "## 文件、复现与审计","",
        f"42 个配置（39 次新拟合、3 次严格等价复用）；累计 {audit['optimizer_steps_including_reused']:,} 次更新记录，其中本轮新训练 {audit['fresh_optimizer_steps']:,} 次。含初始 step 0 共 {audit['evaluation_rows']:,} 行评估、{audit['full_split_losses']:,} 个完整分区平均 loss。代码与数据哈希、固定日期与 scaler、逐 step 完整性、批次计数、仅 val 选点、早停、复用原件哈希及全部 42 个 checkpoint 重放均通过。预测重放最大差 {audit['max_prediction_difference']:.3g}，标准化 loss 独立复算最大差 {audit['max_loss_difference']:.3g}。","",
        "- results/GRID_METRICS.csv：全部配置的三分区 MSE/RMSE/MAE。",
        "- results/VALIDATION_RANKING.csv、SELECTION_FROZEN.json：按 val 排序和冻结的窗口选择。",
        "- results/SELECTED_SUMMARY.csv：所选六组的完整指标；PERSISTENCE.csv 为照抄基准。",
        "- step_logs/ 与 results/ALL_STEP_LOSSES.csv：每 step 完整 train/val/test 日志。",
        "- checkpoints/、predictions/：42 个最佳 val 权重和三分区预测。",
        "- inputs/、splits.csv、scalers.json、PROTOCOL.json、REUSE_EQUIVALENCE.json：数据、边界、配置与复用验证。","",
        "安装 requirements.txt 后，在副本中运行 python reproduce.py，可使用包内 reference_previous 复用三组严格等价的实验并从头完成其余训练和分析。若只检查已有产物，运行 python analyse_grid.py；原文件夹不在时自动使用包内参考文件。完整数据、所有 checkpoint、日志和预测已随本包保存。事后修复历史的逐日发布版本尚未审计。实验保留在本地，未修改正式候选报告或上传仓库。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
