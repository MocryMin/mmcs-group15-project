"""Independent reconstruction of per-target losses and overfitting diagnostics."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

import run_independent as experiment

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
LABELS={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}


def main():
    result=json.loads((R/"RESULTS.json").read_text(encoding="utf-8"))
    frame=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
    split=pd.read_csv(ROOT/"splits.csv",parse_dates=["origin","history_start_56","target_date"])
    scalers=json.loads((ROOT/"scalers.json").read_text())
    mean=np.array(scalers["mean"]);scale=np.array(scalers["std"])
    runs=pd.read_csv(R/"training_runs.csv");history=pd.read_csv(R/"training_history.csv");grid=pd.read_csv(R/"validation_grid.csv")
    comparison=pd.read_csv(R/"LOSS_COMPARISON.csv")
    source=json.loads((ROOT/"inputs/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    checks={"next_day_only":bool(((split.target_date-split.origin).dt.days==1).all()),
        "train_validation_disjoint":not bool(set(split.loc[split.split.eq("train"),"target_date"])&set(split.loc[split.split.eq("validation"),"target_date"])),
        "no_post_2023_evaluation":frame.index.max()==pd.Timestamp("2023-12-31"),
        "frozen_input_hash":hashlib.sha256((ROOT/"inputs/model_daily.csv").read_bytes()).hexdigest()==source["derived_sha256"],
        "train_only_scaling":np.allclose(mean,frame.loc["2020":"2022",experiment.TARGETS].mean().to_numpy()) and np.allclose(scale,frame.loc["2020":"2022",experiment.TARGETS].std(ddof=0).to_numpy()),
        "72_fits":len(runs)==72 and runs.groupby(["target","family","lookback","lr"]).size().eq(3).all(),
        "six_separate_selections":len(result["selected"])==6,
        "matched_per_model_parameters":runs.loc[runs.family.eq("RNN"),"parameters"].eq(5373).all() and runs.loc[runs.family.eq("LSTM"),"parameters"].eq(5409).all(),
        "selection_validation_only":all(np.isclose(grid.loc[grid.target.eq(c["target"])&grid.family.eq(c["family"]),"mean"].min(),c["mean"],atol=1e-12,rtol=0) for c in result["selected"].values())}
    normal=(frame[experiment.TARGETS].to_numpy()-mean)/scale
    weekday=frame.index.dayofweek.to_numpy();season=(frame.index.dayofyear.to_numpy()-1)/np.where(frame.index.is_leap_year,366,365)
    x=np.column_stack([normal,np.sin(2*np.pi*weekday/7),np.cos(2*np.pi*weekday/7),np.sin(2*np.pi*season),np.cos(2*np.pi*season),weekday>=5]).astype(np.float32)
    loss_diff=0.;prediction_diff=0.;head_ok=True;initial_ok=True;baseline_ok=True
    for part in ("train","validation"):
        z=np.load(R/(part+"_predictions.npz"))
        for j,target in enumerate(experiment.TARGETS):
            baseline=z[target+"|Persistence"]
            baseline_ok &= np.allclose(baseline,frame[experiment.TARGETS].to_numpy()[z["origins"],j])
            base_loss=result["metrics"][part][target]["Persistence"]["loss"]
            for family in ("RNN","LSTM"):
                choice=result["selected"][target+"|"+family]
                xx=torch.from_numpy(experiment.windows(x,z["origins"],int(choice["lookback"])))
                starts=history.loc[history.run.str.startswith(target+"_"+family+"_")&history.epoch.eq(0),part+"_eval_loss"]
                initial_ok &= np.allclose(starts,base_loss,atol=2e-7,rtol=0)
                for seed in experiment.SEEDS:
                    row=runs.loc[runs.target.eq(target)&runs.family.eq(family)&runs.lookback.eq(choice["lookback"])&runs.lr.eq(choice["lr"])&runs.seed.eq(seed)].iloc[0]
                    cp=torch.load(ROOT/row.checkpoint,weights_only=True)
                    model=experiment.Predictor(family,j);model.load_state_dict(cp["state_dict"]);model.eval()
                    head_ok &= model.head.out_features==1 and cp["target_index"]==j and cp["target"]==target
                    with torch.no_grad():p=model(xx).numpy().ravel().astype(float)*scale[j]+mean[j]
                    prediction_diff=max(prediction_diff,float(np.max(np.abs(p-z[target+"|"+family+"_seed"+str(seed)]))))
            for name,record in result["metrics"][part][target].items():
                p=z[target+"|"+name]
                independent=float(np.mean(((p-z["truth"][:,j])/scale[j])**2))
                loss_diff=max(loss_diff,abs(independent-record["loss"]))
    checks.update(single_output_target_heads=bool(head_ok),epoch_zero_matches_baseline=bool(initial_ok),
                  persistence_correct=bool(baseline_ok),checkpoint_replay=prediction_diff<1e-6,independent_loss_recalculation=loss_diff<1e-7)
    checks={k:bool(v) for k,v in checks.items()}
    audit={"checks":checks,"all_passed":all(checks.values()),"max_loss_difference":float(loss_diff),"max_prediction_difference":float(prediction_diff),
           "data_vintage_audited":False,"test_used":False}
    experiment.dump(R/"AUDIT.json",audit);assert audit["all_passed"],audit
    diagnostics=[];joint=[]
    previous=pd.read_csv(ROOT.parent/"tier2b-nextday-rnn-lstm-20261109/results/TARGET_LOSSES.csv")
    for key,c in result["selected"].items():
        group=runs.loc[runs.target.eq(c["target"])&runs.family.eq(c["family"])&runs.lookback.eq(c["lookback"])&runs.lr.eq(c["lr"])]
        diagnostics.append({"target":c["target"],"family":c["family"],"lookback":int(c["lookback"]),"lr":c["lr"],
            "best_train_mean":float(group.train_loss.mean()),"best_validation_mean":float(group.validation_loss.mean()),
            "last_train_mean":float(group.last_train_loss.mean()),"last_validation_mean":float(group.last_validation_loss.mean()),
            "validation_rise_after_best_pct":float(100*(group.last_validation_loss.mean()/group.validation_loss.mean()-1)),
            "training_loss_falls_after_best":bool(group.last_train_loss.mean()<group.train_loss.mean()),
            "best_epoch_min":int(group.best_epoch.min()),"best_epoch_max":int(group.best_epoch.max())})
        old=previous.loc[previous.target.eq(c["target"])&previous.model.eq(c["family"])&previous.split.eq("validation")&previous.metric.eq("standardised_MSE")].iloc[0]
        new=comparison.loc[comparison.target.eq(c["target"])&comparison.model.eq(c["family"])&comparison.split.eq("validation")].iloc[0]
        joint.append({"target":c["target"],"family":c["family"],"joint_validation_loss":float(old["mean"]),"independent_validation_loss":float(new.loss_mean),
            "independent_change_pct":float(100*(new.loss_mean/old["mean"]-1)),"caveat":"Independent setup has about 3x total parameter budget for the three tasks"})
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False)
    pd.DataFrame(joint).to_csv(R/"JOINT_VS_INDEPENDENT.csv",index=False)

    figures=ROOT/"figures";figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    for relative in (False,True):
        fig,axes=plt.subplots(3,2,figsize=(12.5,9.8),layout="constrained")
        for j,target in enumerate(experiment.TARGETS):
            for k,family in enumerate(("RNN","LSTM")):
                ax=axes[j,k];choice=result["selected"][target+"|"+family]
                group=runs.loc[runs.target.eq(target)&runs.family.eq(family)&runs.lookback.eq(choice["lookback"])&runs.lr.eq(choice["lr"])].sort_values("validation_loss")
                representative=group.iloc[1];h=history.loc[history.run.eq(representative.run)]
                trainbase=result["metrics"]["train"][target]["Persistence"]["loss"]
                valbase=result["metrics"]["validation"][target]["Persistence"]["loss"]
                at=trainbase if relative else 1.;av=valbase if relative else 1.
                ax.plot(h.epoch,h.train_eval_loss/at,color="#245c91",label="Training (eval mode)")
                ax.plot(h.epoch,h.validation_eval_loss/av,color="#b66b22",label="Validation")
                if relative:ax.axhline(1.,ls="--",color="#777777",label="Copy-today baseline")
                else:
                    ax.axhline(trainbase,ls="--",color="#245c91",alpha=.5,label="Copy-today: training")
                    ax.axhline(valbase,ls="--",color="#b66b22",alpha=.5,label="Copy-today: validation")
                best=h.loc[h.epoch.eq(representative.best_epoch)].iloc[0]
                ax.scatter([best.epoch],[best.validation_eval_loss/av],color="black",s=25,zorder=5,label="Selected checkpoint")
                ax.set(title=f"{['Generation','Demand','Price'][j]} — {family}, L={int(choice['lookback'])}, seed={int(representative.seed)}",xlabel="Epoch",
                    ylabel="MSE / own-split persistence MSE" if relative else "Single-target standardised MSE")
                ax.grid(alpha=.15)
        handles,labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,labels,loc="outside lower center",ncol=3,frameon=False)
        fig.suptitle("Independent next-day models: training and validation\nEach panel uses the median-validation seed of its selected configuration",fontsize=12)
        stem="relative_train_validation_loss" if relative else "train_validation_loss"
        fig.savefig(figures/(stem+".png"),dpi=180);fig.savefig(figures/(stem+".svg"));plt.close(fig)

    def entry(target,part,name):
        return comparison.loc[comparison.target.eq(target)&comparison.split.eq(part)&comparison.model.eq(name)].iloc[0]
    lines=["# 独立单目标 RNN/LSTM：次日预测与过拟合检查","",
        "供给、需求、电价分别训练独立网络；每个目标分别有 RNN 与 LSTM，不共享参数，loss 只包含自己的次日 MSE。输入仍保留三条历史序列与五个日历特征，因此本轮是独立目标训练，不是纯单变量输入试验。",
        "","训练目标日期 2020–2022 年，1,040 个预测样本；验证目标日期 2023 年，365 个样本。本轮未使用 2024 年后的目标。训练期标准化参数用于两个分区。总供给含独立风场，电价为名义 £/MWh。",
        "","## 配置","",
        "RNN 为单层 tanh、68 隐藏单元、每模型 5,373 参数；LSTM 为单层、32 隐藏单元、每模型 5,409 参数。输出为相对当日值的次日变化。每目标×每家族分别比较两个窗口、两个学习率、三个随机种子，共 72 次训练。",
        "","train/val loss 均由同一检查点在 eval 模式下计算，不包含 dropout 或额外权重惩罚。每个分区的照抄基准在相同预测起点上计算。验证集参与早停和选配置，不是新的独立测试集。",
        "","| 目标 | 模型 | 窗口 | 学习率 |","|---|---|---:|---:|"]
    for c in result["selected"].values():lines.append(f"| {LABELS[c['target']]} | {c['family']} | {int(c['lookback'])} | {c['lr']:g} |")
    lines += ["","## 每个目标的 train / val loss","",
        "loss 为相应目标用训练期标准差归一化后的 MSE，三个目标不再合并。± 是随机种子标准差，非置信区间。结果是各种子最佳验证检查点的指标均值，不是三模型集成。",
        "","| 目标 | 模型 | Train loss | Val loss | 相对照抄的验证误差降幅 |","|---|---|---:|---:|---:|"]
    for target in experiment.TARGETS:
        for family in ("Persistence","RNN","LSTM"):
            a=entry(target,"train",family);b=entry(target,"validation",family)
            def cell(row):return f"{row.loss_mean:.6f}"+(f" ± {row.loss_seed_sd:.6f}" if family!="Persistence" else "")
            lines.append(f"| {LABELS[target]} | {family} | {cell(a)} | {cell(b)} | {100*b.skill_vs_persistence:.2f}% |")
    lines += ["","![训练验证曲线](figures/train_validation_loss.png)","",
        "## 过拟合诊断","",
        "每一组均保留了完整 epoch 曲线。下表比较验证最优检查点和早停前最后一个 epoch，检查后续训练是否仍降低 train loss、同时抬高 val loss。",
        "","| 目标 | 模型 | 最优处 train | 最优处 val | 最后 train | 最后 val | val 回升 |","|---|---|---:|---:|---:|---:|---:|"]
    for d in diagnostics:lines.append(f"| {LABELS[d['target']]} | {d['family']} | {d['best_train_mean']:.6f} | {d['best_validation_mean']:.6f} | {d['last_train_mean']:.6f} | {d['last_validation_mean']:.6f} | {d['validation_rise_after_best_pct']:.2f}% |")
    lines += ["","所选六组配置的种子平均均出现：最佳验证点之后 train loss 继续降低，而 val loss 回升。这符合继续训练后过拟合的典型形态，支持保留验证早停检查点。电价最明显：RNN 平均 val loss 从 0.038269 回升到 0.048951，LSTM 从 0.039742 回升到 0.046954，最后都高于照抄基准 0.044562。",
        "","不同年份的基础波动不同，不能仅凭 train loss 大于或小于 val loss 判断过拟合。特别是电价，应同时看曲线和各分区照抄基准。下图将每个分区 loss 除以本分区照抄 loss，辅助比较相对预测能力。",
        "","![相对照抄曲线](figures/relative_train_validation_loss.png)","",
        "## 原始单位 MSE","","供给和需求单位为 MW²；电价为 (£/MWh)²。","",
        "| 目标 | 模型 | Train MSE | Val MSE | Val RMSE |","|---|---|---:|---:|---:|"]
    for target in experiment.TARGETS:
        for family in ("Persistence","RNN","LSTM"):
            a=entry(target,"train",family);b=entry(target,"validation",family)
            lines.append(f"| {LABELS[target]} | {family} | {a.MSE_mean:,.3f} | {b.MSE_mean:,.3f} | {b.RMSE_mean:,.3f} |")
    lines += ["","## 与此前联合训练的参考对照","",
        "只作开发集参考：三个独立模型的总参数量约为一个联合模型的三倍，因此不能把差异完全解释成消除了任务干扰。两组使用相同输入、目标日期及每家族调参范围。",
        "","| 目标 | 模型 | 联合 val loss | 独立 val loss | 独立相对变化 |","|---|---|---:|---:|---:|"]
    for d in joint:lines.append(f"| {LABELS[d['target']]} | {d['family']} | {d['joint_validation_loss']:.6f} | {d['independent_validation_loss']:.6f} | {d['independent_change_pct']:.2f}% |")
    lines += ["","## 文件与边界","",
        "run_independent.py 训练与导出；summarise_independent.py 重放检查点、独立复算 loss 和绘图。PROTOCOL.json、splits.csv、scalers.json 固定协议；results/LOSS_COMPARISON.csv 和 OVERFIT_DIAGNOSTICS.csv 保存详细结果，checkpoints 包含全部模型。",
        "","数据为当前冻结的事后修复历史，尚未重建逐日发布版本；没有新增外部特征、Ridge、合同罚则或 MPC 收益计算。此前联合模型与七日试验均保留，未覆盖或上传。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cpu\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit))
    print(comparison[["target","split","model","loss_mean","loss_seed_sd","skill_vs_persistence"]].to_string(index=False))
    print(pd.DataFrame(diagnostics).to_string(index=False))


if __name__=="__main__":
    torch.set_num_threads(2)
    main()
