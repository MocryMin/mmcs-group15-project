"""Replay checkpoints, audit every-step logs, plot all three split losses."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

import run_monitored as exp
from model import Predictor,TARGETS,windows

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
PARTS=("train","validation","test")
LABELS={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}
ENGLISH={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
COLORS={"train":"#245c91","validation":"#bd7625","test":"#38804b"}


def main():
    torch.set_num_threads(2)
    result=json.loads((R/"RESULTS.json").read_text(encoding="utf-8"))
    protocol=result["protocol"]
    frame,x,data,mean,scale=exp.prepare()
    runs=pd.read_csv(R/"training_runs.csv")
    comparison=pd.read_csv(R/"LOSS_COMPARISON.csv")
    splits=pd.read_csv(ROOT/"splits.csv",parse_dates=["origin","history_start_56","target_date"])
    configs=json.loads((ROOT/"REFERENCE_CONFIGS.json").read_text())
    histories={row.run:pd.read_csv(ROOT/row.step_log.replace("\\","/")) for row in runs.itertuples()}
    history=pd.concat(histories.values(),ignore_index=True)
    history.to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    dates={p:set(splits.loc[splits.split.eq(p),"target_date"]) for p in PARTS}
    checks={
        "18_fresh_fits":len(runs)==18 and runs.groupby(["target","family"]).size().eq(3).all(),
        "all_source_code_hashes_match":all(exp.sha(ROOT/name)==v for name,v in protocol["source_hashes"].items()),
        "all_target_dates_disjoint":all(not dates[a]&dates[b] for a,b in (("train","validation"),("train","test"),("validation","test"))),
        "next_day_labels_only":((splits.target_date-splits.origin).dt.days==1).all(),
        "exact_requested_boundaries":all(min(dates[p])==pd.Timestamp(a) and max(dates[p])==pd.Timestamp(b) for p,(a,b) in exp.PERIODS.items()),
        "train_only_scaler":np.allclose(mean,frame.loc["2022":"2024",TARGETS].mean()) and np.allclose(scale,frame.loc["2022":"2024",TARGETS].std(ddof=0)),
        "exact_sample_counts":{p:len(z) for p,z in dates.items()}=={"train":1096,"validation":243,"test":365},
        "pre2022_history_context_only":splits.target_date.min()==pd.Timestamp("2022-01-01") and splits.history_start_56.min()==pd.Timestamp("2021-11-06"),
        "no_september2026_targets":splits.target_date.max()==pd.Timestamp("2026-08-31"),
    }
    completeness=selection=layout=stop=initial=heads=baseline=True
    max_loss_diff=max_prediction_diff=max_checkpoint_log_diff=0.
    for row in runs.itertuples():
        h=histories[row.run]
        completeness &= np.array_equal(h.global_step.to_numpy(),np.arange(row.steps+1))
        completeness &= h[[p+"_eval_loss" for p in PARTS]].notna().all().all()
        completeness &= np.isfinite(h[[p+"_eval_loss" for p in PARTS]].to_numpy()).all()
        completeness &= len(h)==row.steps+1 and row.steps==18*row.epochs
        batches=h.iloc[1:]
        layout &= np.array_equal(batches.batch_index.to_numpy(),np.tile(np.arange(1,19),row.epochs))
        layout &= np.array_equal(batches.batch_size_actual.to_numpy(),np.tile([64]*17+[8],row.epochs))
        layout &= np.array_equal(batches.epoch.to_numpy(),np.repeat(np.arange(1,row.epochs+1),18))
        seen=np.repeat(np.arange(row.epochs)*1096,18)+np.tile(np.cumsum([64]*17+[8]),row.epochs)
        layout &= np.array_equal(batches.samples_seen.to_numpy(),seen)
        best=float("inf");best_step=0;best_epoch=0
        for z in h.itertuples():
            improved=z.validation_eval_loss<best-1e-5
            selection &= bool(z.checkpoint_improved)==improved
            if improved:best=z.validation_eval_loss;best_step=z.global_step;best_epoch=z.epoch
            selection &= np.isclose(z.best_validation_so_far,best,atol=1e-12,rtol=0)
        selection &= best_step==row.best_step and best_epoch==row.best_epoch
        stop &= row.epochs==120 or row.epochs-best_epoch==15
        selected=h.loc[h.global_step.eq(row.best_step)].iloc[0]
        for p,col in (("train","best_train_loss"),("validation","best_validation_loss"),("test","test_loss_at_val_checkpoint")):
            max_checkpoint_log_diff=max(max_checkpoint_log_diff,abs(float(selected[p+"_eval_loss"])-getattr(row,col)))
        cp=torch.load(ROOT/row.checkpoint.replace("\\","/"),weights_only=True)
        selection &= cp["best_step"]==row.best_step and cp["best_epoch"]==row.best_epoch
        m=Predictor(row.family,TARGETS.index(row.target));m.load_state_dict(cp["state_dict"]);m.eval()
        heads &= m.head.out_features==1 and cp["target"]==row.target and cp["target_index"]==TARGETS.index(row.target)
        expected=5373 if row.family=="RNN" else 5409
        heads &= sum(p.numel() for p in m.parameters())==expected==row.parameters
        j=TARGETS.index(row.target)
        for p in PARTS:
            exported=np.load(R/(p+"_predictions.npz"))
            xx=torch.from_numpy(windows(x,data[p]["origins"],row.lookback))
            with torch.inference_mode():pred=m(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
            saved=exported[row.target+"|"+row.family+"_seed"+str(row.seed)]
            max_prediction_diff=max(max_prediction_diff,float(np.max(np.abs(pred-saved))))
            computed=float(np.mean(((saved-exported["truth"][:,j])/scale[j])**2))
            reported=result["metrics"][p][row.target][row.family+"_seed"+str(row.seed)]["loss"]
            max_loss_diff=max(max_loss_diff,abs(computed-reported),abs(computed-float(selected[p+"_eval_loss"])))
            base=result["metrics"][p][row.target]["Persistence"]["loss"]
            initial &= np.isclose(h.iloc[0][p+"_eval_loss"],base,atol=1e-6,rtol=0)
            baseline &= np.allclose(exported[row.target+"|Persistence"],frame[TARGETS].to_numpy()[data[p]["origins"],j])
    checks.update(full_three_set_eval_at_every_step=completeness,all_batches_and_sample_counts_correct=layout,
        checkpoint_replayed_from_validation_only=selection,early_stop_15_complete_epochs=stop,
        epoch_zero_persistence=initial,independent_scalar_heads=heads,persistence_uses_today=baseline,
        checkpoint_log_matches=max_checkpoint_log_diff<1e-12,checkpoint_prediction_replay=max_prediction_diff<1e-6,
        independent_loss_recalculation=max_loss_diff<1e-6)
    checks={k:bool(v) for k,v in checks.items()}
    audit={"checks":checks,"all_passed":all(checks.values()),"evaluation_rows":len(history),
        "optimizer_steps":int(runs.steps.sum()),"full_set_metric_values":3*len(history),
        "max_prediction_difference":max_prediction_diff,"max_normalised_loss_difference":max_loss_diff,
        "max_checkpoint_log_difference":max_checkpoint_log_diff,"test_is_monitored_not_blind":True,"data_vintage_audited":False}
    exp.dump(R/"AUDIT.json",audit)
    assert audit["all_passed"],audit
    diagnostics=[]
    for (target,family),g in runs.groupby(["target","family"],sort=False):
        d={"target":target,"family":family,"lookback":int(g.lookback.iloc[0]),"lr":float(g.lr.iloc[0]),
            "best_epoch_min":int(g.best_epoch.min()),"best_epoch_max":int(g.best_epoch.max()),
            "best_step_min":int(g.best_step.min()),"best_step_max":int(g.best_step.max()),
            "stopped_epoch_min":int(g.epochs.min()),"stopped_epoch_max":int(g.epochs.max())}
        for p,bestcol in (("train","best_train_loss"),("validation","best_validation_loss"),("test","test_loss_at_val_checkpoint")):
            d["selected_"+p]=float(g[bestcol].mean())
            d["final_"+p]=float(g["last_"+p+"_loss"].mean())
            d[p+"_change_after_selected_pct"]=float(100*(d["final_"+p]/d["selected_"+p]-1))
        d["train_falls_val_rises"]=d["final_train"]<d["selected_train"] and d["final_validation"]>d["selected_validation"]
        diagnostics.append(d)
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False)
    # Annual target difficulty is descriptive only; it never selects models.
    yearly=[]
    for p,z in data.items():
        target_dates=frame.index[z["origins"]+1]
        for yr in sorted(set(target_dates.year)):
            mask=target_dates.year==yr
            for j,target in enumerate(TARGETS):
                truth=z["truth"][mask,j];pred=frame[target].to_numpy()[z["origins"][mask]]
                yearly.append({"split":p,"year":int(yr),"target":target,"samples":int(mask.sum()),**exp.score(pred,truth,scale[j])})
    pd.DataFrame(yearly).to_csv(R/"YEARLY_PERSISTENCE_DIFFICULTY.csv",index=False)
    figures=ROOT/"figures";figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})

    def draw(ax,row,relative=False,detail=False):
        h=histories[row.run];best=h.loc[h.global_step.eq(row.best_step)].iloc[0]
        for p in PARTS:
            base=result["metrics"][p][row.target]["Persistence"]["loss"]
            denom=base if relative else 1.
            ax.plot(h.global_step,h[p+"_eval_loss"]/denom,color=COLORS[p],lw=.9,label=p.capitalize())
            if not relative:ax.axhline(base,color=COLORS[p],ls="--",lw=.8,alpha=.6,label=p.capitalize()+" copy-today")
        if relative:ax.axhline(1.,color="#777777",ls="--",lw=.9,label="Own-split copy-today")
        denom=result["metrics"]["validation"][row.target]["Persistence"]["loss"] if relative else 1.
        ax.scatter([row.best_step],[best.validation_eval_loss/denom],color="black",s=22,zorder=5,label="Val-selected checkpoint")
        ax.axvline(row.best_step,color="#444444",ls=":",lw=.7,alpha=.65)
        ax.set(title=f"{ENGLISH[row.target]} / {row.family}, seed {row.seed}, L={row.lookback}\nSelected step {row.best_step} (epoch {row.best_epoch}); stopped epoch {row.epochs}",
            xlabel="Optimiser step",ylabel="MSE / own-split persistence MSE" if relative else "Train-standardised MSE")
        ax.grid(alpha=.15)
        if detail:
            sec=ax.secondary_xaxis("top",functions=(lambda v:v/18,lambda v:v*18));sec.set_xlabel("Epoch equivalents")
    for relative in (False,True):
        fig,axes=plt.subplots(3,2,figsize=(13,11),layout="constrained")
        for j,target in enumerate(TARGETS):
            for k,family in enumerate(("RNN","LSTM")):
                g=runs.loc[runs.target.eq(target)&runs.family.eq(family)].sort_values("best_validation_loss")
                draw(axes[j,k],next(g.iloc[[1]].itertuples()),relative)
        handles,labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False,fontsize=9)
        fig.suptitle("Next-day forecasting: full train / validation / test evaluation after EVERY update\nOne median-validation seed per model; raw step values, no smoothing",fontsize=12)
        stem="relative_step_losses" if relative else "step_losses"
        fig.savefig(figures/(stem+".png"),dpi=180,bbox_inches="tight",pad_inches=.12);fig.savefig(figures/(stem+".svg"),bbox_inches="tight",pad_inches=.12);plt.close(fig)
    for (target,family),g in runs.groupby(["target","family"],sort=False):
        fig,axes=plt.subplots(1,3,figsize=(15.5,4.7),layout="constrained")
        for ax,row in zip(axes,g.itertuples()):draw(ax,row,True,True)
        handles,labels=axes[0].get_legend_handles_labels()
        fig.legend(handles,labels,loc="outside lower center",ncol=5,frameon=False,fontsize=9)
        fig.savefig(figures/(target+"_"+family+"_all_seeds.png"),dpi=170);plt.close(fig)

    def entry(t,p,m):return comparison.loc[comparison.target.eq(t)&comparison.split.eq(p)&comparison.model.eq(m)].iloc[0]
    def cell(row):return f"{row.loss_mean:.6f}"+(f" ± {row.loss_seed_sd:.6f}" if row.model!="Persistence" else "")
    lines=["# 独立次日 RNN/LSTM：三段时间划分与逐 step 轨迹","",
        "供给、需求、电价分别训练独立网络，各自预测下一天。每个 optimizer step 更新参数后，完整评估 train、val、test；所有 loss 均逐行保存并立即刷新文件。输入仍为三条历史序列及日历特征，每个模型只输出一个目标，不共享权重。","",
        "## 日期与样本","","日期按预测目标日划分，边界互不重叠。用户原述的 2025 年 9 月作为 test 起点；test 取完整一年，末端多出的 17 天未纳入。","",
        "| 分区 | 目标日期 | 样本数 | 用途 |","|---|---|---:|---|",
        "| Train | 2022-01-01—2024-12-31 | 1,096 | 梯度更新；拟合标准化参数 |",
        "| Val | 2025-01-01—2025-08-31 | 243 | 逐 step 选择 checkpoint；提前停止 |",
        "| Test | 2025-09-01—2026-08-31 | 365 | 逐 step 监测；不参与选择 |","",
        "2021-11-06—12-31 仅供训练最开始的历史输入窗口使用，不作为训练标签。预测某天时可用到前一天为止的真实历史；跨分区窗口保留过去可观察的信息，不把未来目标输入网络。冻结数据中供给为课程总发电加独立风场，单位为日均 MW；电价为名义 £/MWh。","",
        "## 训练安排与记录粒度","",
        "每个 epoch 将 1,096 个训练窗口重新打乱分批，但不改变单个窗口内部时间顺序。batch size 为 64；每 epoch 共 18 step，即 17×64 + 8。最多 120 epoch、2,160 step/fit。AdamW、weight decay 0.0001、梯度范数截断 1、dropout 0.1。","",
        "step 0 是未训练模型的初始评估，预测与照抄今天一致。每次更新后切到 eval 模式，用同一组权重评估三个完整分区，再恢复 train 模式继续更新。train_batch_loss 单独记录，不能与无 dropout 的完整 train_eval_loss 混用。","",
        "每个 step 都可成为最佳 checkpoint：只看 val MSE，改善阈值为 0.00001。连续 15 个完整 epoch 没有新的 val 改善才提前停止，不是连续 15 step。test 曲线不参与梯度、checkpoint、早停或本轮配置选择。","",
        "沿用上一轮已选出的六组窗口和学习率，从零初始化重新训练，三个随机种子 17、29、43，共 18 fits。本轮没有重新调参。RNN 为单层 tanh、68 隐藏单元、5,373 参数；LSTM 为单层、32 隐藏单元、5,409 参数。","",
        "| 目标 | 模型 | 输入窗口/天 | 学习率 | 最佳 step 范围 | 实际停止 epoch 范围 |","|---|---|---:|---:|---:|---:|"]
    for d in diagnostics:lines.append(f"| {LABELS[d['target']]} | {d['family']} | {d['lookback']} | {d['lr']:g} | {d['best_step_min']}—{d['best_step_max']} | {d['stopped_epoch_min']}—{d['stopped_epoch_max']} |")
    lines += ["","## 最佳验证 checkpoint 的三个分区 loss","",
        "loss 为单目标标准化均方误差（MSE），是每个样本误差的平均值，不是求和。标准差只由 2022–2024 年拟合，三个分区使用同一标准差：","",
        "$$","L_S=\\frac{1}{|S|}\\sum_{t\\in S}\\left(\\frac{\\hat y_t-y_t}{s_{\\mathrm{train}}}\\right)^2.","$$","",
        "下表为每个种子各自 val 最优 checkpoint 的指标，± 为三个种子的标准差，不是置信区间或集成模型。Test 使用同一个 val 所选 checkpoint，没有另外挑 test 最优点。","",
        "| 目标 | 模型 | Train loss | Val loss | Test loss | Test 相对照抄误差降幅 |","|---|---|---:|---:|---:|---:|"]
    for target in TARGETS:
        for family in ("Persistence","RNN","LSTM"):
            a,b,c=(entry(target,p,family) for p in PARTS)
            lines.append(f"| {LABELS[target]} | {family} | {cell(a)} | {cell(b)} | {cell(c)} | {100*c.skill_vs_persistence:.2f}% |")
    lines += ["","![每次更新后的完整三分区 loss](figures/step_losses.png)","",
        "图中展示每个目标、家族内按 val 排序居中的种子，未根据 test 选择。每个点是一整套分区的平均误差；没有平滑，也没有只取 epoch 末尾。黑点为实际保存的 val checkpoint。全部种子的曲线另存 figures，各 step 原始记录见 results/ALL_STEP_LOSSES.csv。","",
        "## 相对照抄与过拟合","",
        "不同年份的波动强弱不同，直接比较跨分区 loss 高低不足以判断过拟合。以下曲线分别除以各分区自己的照抄 loss；1 表示等于照抄，低于 1 表示预测改善。过拟合主要观察固定 val 在后续训练中的变化，并与持续下降的 train 对照。","",
        "![各分区相对照抄误差](figures/relative_step_losses.png)","",
        "| 目标 | 模型 | 所选 train | 最后 train | 所选 val | 最后 val | Val 后续变化 | Test 后续变化 |","|---|---|---:|---:|---:|---:|---:|---:|"]
    for d in diagnostics:
        lines.append(f"| {LABELS[d['target']]} | {d['family']} | {d['selected_train']:.6f} | {d['final_train']:.6f} | {d['selected_validation']:.6f} | {d['final_validation']:.6f} | {d['validation_change_after_selected_pct']:+.2f}% | {d['test_change_after_selected_pct']:+.2f}% |")
    patterns=sum(d["train_falls_val_rises"] for d in diagnostics)
    lines += ["",f"六组配置中，{patterns} 组的种子平均呈现所选 checkpoint 后 train 继续下降、val 上升。Test 轨迹用于查看这种变化是否延续至后一时段；没有因为某个 test 点较好而换 checkpoint。由于选择的是逐 step 最低 val，后续 val 回升本身还包含选点效应，应结合整段曲线判断其持续程度。","",
        "## 原始单位指标","","供给和需求的 MSE 单位为 MW²，RMSE 为 MW；电价 MSE 单位为 (£/MWh)²，RMSE 为 £/MWh。","",
        "| 目标 | 模型 | Train MSE | Val MSE | Test MSE | Test RMSE | Test MAE |","|---|---|---:|---:|---:|---:|---:|"]
    for target in TARGETS:
        for family in ("Persistence","RNN","LSTM"):
            a,b,c=(entry(target,p,family) for p in PARTS)
            lines.append(f"| {LABELS[target]} | {family} | {a.MSE_mean:,.3f} | {b.MSE_mean:,.3f} | {c.MSE_mean:,.3f} | {c.RMSE_mean:,.3f} | {c.MAE_mean:,.3f} |")
    winners=[]
    for target in TARGETS:
        candidates=comparison.loc[comparison.target.eq(target)&comparison.split.eq("validation")&comparison.model.isin(["RNN","LSTM"])].sort_values("loss_mean")
        chosen=candidates.iloc[0].model
        winners.append(f"{LABELS[target]}：{chosen}")
    lines += ["","若只按本轮平均 val loss 比较两个家族，排序为："+"；".join(winners)+"。电价的 val 均值仅差约 0.000285，小于两个家族各自的种子波动；不能据此宣称 LSTM 稳定优胜。Test 上，供给 LSTM 较好，需求两者接近，电价 RNN 较好。这个 test 排序只用于报告，没有据此改选配置或重跑训练。","",
        "电价 RNN 的 test RMSE 为 20.38 £/MWh、MAE 为 15.14 £/MWh，照抄分别为 23.63 和 16.67。Test 电价 loss 低于 train/val，与 test 本身较容易预测一致：照抄 loss 也从 train 的 0.147014、val 的 0.134970 降到 test 的 0.087454。不同年份的标准化参数保持一致，差异不是样本数量或分区分别缩放造成的。新实验的训练期标准差与旧实验不同，应避免直接用两轮归一化 loss 的绝对值评价进步。预测改善对 MPC 收益的影响尚未评估。","",
        "## 审计、文件和复现","",
        f"完成 {len(runs)} 次拟合，累计 {audit['optimizer_steps']:,} 次权重更新；含各模型 step 0 共 {audit['evaluation_rows']:,} 行完整评估，三分区共 {audit['full_set_metric_values']:,} 个平均 loss 数值。每行三项齐全且 finite；step 连续、批次大小、样本计数、15 epoch 早停、仅 val 选点、初始照抄、单输出目标映射、训练期 scaler、冻结代码/输入及 checkpoint 重放检查全部通过。最大标准化 loss 复算差 {max_loss_diff:.3g}。详见 results/AUDIT.json。","",
        "- run_monitored.py：训练、逐 step 完整评估、checkpoint 与指标导出。",
        "- summarise_monitored.py：读取所有日志，重放 18 个 checkpoint、复算指标、绘图。",
        "- step_logs/：18 份独立 CSV，训练时每行刷新；results/ALL_STEP_LOSSES.csv 为合并记录。",
        "- results/LOSS_COMPARISON.csv：各目标、各分区的平均 loss、原始 MSE/RMSE/MAE、种子标准差。",
        "- checkpoints/：18 份最佳 val 权重；inputs/、splits.csv、scalers.json、REFERENCE_CONFIGS.json、PROTOCOL.json：数据和配置。","",
        "复现：安装 requirements.txt 后，先运行 python run_monitored.py，再运行 python summarise_monitored.py。训练过程会更新本文件夹中的结果；如需保留本次产物，请在新副本中复现。","",
        "本轮 test 是按用户要求逐 step 查看损失的留出集，不是全程不可见的盲测集；旧实验也曾查看过部分 2025 年数据。它未参与本轮模型配置、梯度、checkpoint 或早停，但未来若依据这条曲线继续改模型，就不能再把同一段称为全新独立测试。当前输入为事后修复历史，尚未审计逐日发布版本；本轮没有新增外部特征、Ridge、MPC 收益、合同罚则或远程上传。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cpu\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit))
    print(comparison[["target","split","model","loss_mean","loss_seed_sd","skill_vs_persistence"]].to_string(index=False))
    print(pd.DataFrame(diagnostics).to_string(index=False))


if __name__=="__main__":main()
