"""Audit next-day losses and plot training/validation comparisons."""
from pathlib import Path
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

import run_nextday as experiment

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"


def main():
    result=json.loads((R/"RESULTS.json").read_text(encoding="utf-8"))
    frame=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
    split=pd.read_csv(ROOT/"splits.csv",parse_dates=["origin","history_start_56","target_date"])
    scaler=json.loads((ROOT/"scalers.json").read_text())
    mean=np.array(scaler["mean"]);scale=np.array(scaler["std"])
    runs=pd.read_csv(R/"training_runs.csv")
    grid=pd.read_csv(R/"validation_grid.csv")
    history=pd.read_csv(R/"training_history.csv")
    checks={"next_day_target":bool(((split.target_date-split.origin).dt.days==1).all()),
        "no_post_2023_data":bool(frame.index.max()==pd.Timestamp("2023-12-31") and split.target_date.max()==pd.Timestamp("2023-12-31")),
        "target_split_disjoint":not bool(set(split.loc[split.split.eq("train"),"target_date"])&set(split.loc[split.split.eq("validation"),"target_date"])),
        "train_scaler":bool(np.allclose(mean,frame.loc["2020":"2022",experiment.TARGETS].mean().to_numpy()) and np.allclose(scale,frame.loc["2020":"2022",experiment.TARGETS].std(ddof=0).to_numpy())),
        "24_runs":len(runs)==24,
        "near_parameter_match":bool(runs.loc[runs.family.eq("RNN"),"parameters"].eq(5511).all() and runs.loc[runs.family.eq("LSTM"),"parameters"].eq(5475).all()),
        "selection_from_validation":all(np.isclose(grid.loc[grid.family.eq(f),"mean"].min(),c["mean"],atol=1e-12,rtol=0) for f,c in result["selected"].items())}
    manifest=json.loads((ROOT/"inputs/SOURCE_MANIFEST.json").read_text())
    checks["frozen_derived_input_hash"]=hashlib.sha256((ROOT/"inputs/model_daily.csv").read_bytes()).hexdigest()==manifest["derived_sha256"]
    normal=(frame[experiment.TARGETS].to_numpy()-mean)/scale
    dow=frame.index.dayofweek.to_numpy();phase=(frame.index.dayofyear.to_numpy()-1)/np.where(frame.index.is_leap_year,366,365)
    x=np.column_stack([normal,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32)
    metric_difference=0.;checkpoint_difference=0.;target_rows=[]
    for part in ("train","validation"):
        z=np.load(R/(part+"_predictions.npz"))
        checks[part+"_persistence_is_today"]=bool(np.allclose(z["Persistence"],frame[experiment.TARGETS].to_numpy()[z["origins"]]))
        base=result["metrics"][part]["Persistence"]["loss"]
        initial=history.loc[history.epoch.eq(0),part+"_eval_loss"]
        checks[part+"_initial_network_equals_baseline"]=bool(np.allclose(initial,base,atol=2e-7,rtol=0))
        for name,record in result["metrics"][part].items():
            diff=(z[name]-z["truth"])/scale
            recomputed=float(np.mean(diff**2));metric_difference=max(metric_difference,abs(recomputed-record["loss"]))
            for j,target in enumerate(experiment.TARGETS):
                metric_difference=max(metric_difference,abs(np.mean((z[name][:,j]-z["truth"][:,j])**2)-record["targets"][target]["MSE"]))
        for f,c in result["selected"].items():
            xx=torch.from_numpy(experiment.inputs(x,z["origins"],int(c["lookback"])))
            for seed in experiment.SEEDS:
                row=runs.loc[runs.family.eq(f)&runs.lookback.eq(c["lookback"])&runs.lr.eq(c["lr"])&runs.seed.eq(seed)].iloc[0]
                cp=torch.load(ROOT/row.checkpoint,weights_only=True)
                model=experiment.Predictor(f);model.load_state_dict(cp["state_dict"]);model.eval()
                with torch.no_grad():p=model(xx).numpy().astype(float)*scale+mean
                checkpoint_difference=max(checkpoint_difference,float(np.max(np.abs(p-z[f+"_seed"+str(seed)]))))
        for name in ("Persistence","RNN","LSTM"):
            vals=[result["metrics"][part][name+"_seed"+str(s)] for s in experiment.SEEDS] if name!="Persistence" else [result["metrics"][part][name]]
            for target in experiment.TARGETS:
                for key in ("MSE","RMSE","MAE","standardised_MSE"):
                    numbers=[v["targets"][target][key] for v in vals]
                    target_rows.append(dict(split=part,model=name,target=target,metric=key,mean=float(np.mean(numbers)),seed_sd=float(np.std(numbers,ddof=1)) if len(numbers)>1 else 0.))
    checks["losses_independently_recomputed"]=metric_difference<1e-7
    checks["checkpoint_replay"]=checkpoint_difference<1e-6
    checks={k:bool(v) for k,v in checks.items()}
    audit={"checks":checks,"all_passed":all(checks.values()),"metric_max_difference":float(metric_difference),"checkpoint_max_difference":float(checkpoint_difference),
        "data_vintage_audited":False,"test_used_in_this_round":False}
    experiment.dump(R/"AUDIT.json",audit);assert audit["all_passed"],audit
    targets=pd.DataFrame(target_rows);targets.to_csv(R/"TARGET_LOSSES.csv",index=False)
    comparison=pd.read_csv(R/"LOSS_COMPARISON.csv")
    figures=ROOT/"figures";figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout="constrained")
    for ax,f in zip(axes,("RNN","LSTM")):
        c=result["selected"][f]
        candidates=runs.loc[runs.family.eq(f)&runs.lookback.eq(c["lookback"])&runs.lr.eq(c["lr"])].sort_values("validation_loss")
        representative=candidates.iloc[1]
        h=history.loc[history.run.eq(representative.run)]
        ax.plot(h.epoch,h.train_eval_loss,label="Training MSE (eval mode)",color="#245c91")
        ax.plot(h.epoch,h.validation_eval_loss,label="Validation MSE",color="#b66b22")
        ax.axhline(result["metrics"]["train"]["Persistence"]["loss"],ls="--",color="#245c91",alpha=.55,label="Copy-today: training")
        ax.axhline(result["metrics"]["validation"]["Persistence"]["loss"],ls="--",color="#b66b22",alpha=.55,label="Copy-today: validation")
        best=h.loc[h.epoch.eq(representative.best_epoch)].iloc[0]
        ax.scatter([best.epoch],[best.validation_eval_loss],s=35,color="black",zorder=5,label="Selected checkpoint")
        ax.set(title=f"{f}: {int(c['lookback'])}-day history, lr={c['lr']:g}, seed={int(representative.seed)}",xlabel="Epoch",ylabel="Next-day standardised MSE")
        ax.grid(alpha=.16)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=3,frameon=False)
    fig.suptitle("One-day-only training objective and evaluation\nRepresentative seed: median validation loss of the selected configuration",fontsize=11)
    fig.savefig(figures/"train_validation_loss.png",dpi=180);fig.savefig(figures/"train_validation_loss.svg");plt.close(fig)
    price=targets.loc[targets.target.eq("price_GBP_MWh")&targets.metric.eq("MSE")]
    lines=["# 次日 RNN/LSTM：训练、验证与照抄基准","",
        "只训练 RNN 和 LSTM；不拟合 Ridge。本轮每个样本只预测次日的总供给、需求、电价三个值。目标中没有未来第 2–7 天。2024 年以后的数据未在本轮评估。",
        "","## 数据与目标","",
        "训练目标日期 2020–2022 年，验证目标日期 2023 年。共 1,040 个训练样本和 365 个验证样本，均有完整历史窗口。输入保持三条序列与五个日历特征；总供给包含独立风场，电价单位为名义 £/MWh。",
        "","损失是三个目标使用训练集均值/标准差标准化后的次日 MSE 等权均值。两个分区使用同一套训练期标准差。AdamW 的 weight decay 为训练规则的一部分，不另加进展示的 MSE。展示 train loss 和 val loss 时均关闭 dropout，使用同一模型权重和完全相同的计算公式。",
        "","照抄基准为次日预测等于当日观测。它不训练，但在完全相同的预测起点和目标上计算同样的 MSE。神经模型以当日值加预测变化作读出；初始零读出等于照抄基准，并在 epoch 0 验证。",
        "","## 配置与选型","",
        "单层 tanh RNN 隐藏宽度 68，5,511 参数；单层 LSTM 宽度 32，5,475 参数。缩短输出跨度后重新匹配参数规模。每种模型比较 28/56 日窗口、0.001/0.003 学习率和三个随机种子，共 24 次拟合。验证平均 loss 决定配置，每个种子保存最低验证 loss 检查点。",
        "","| 模型 | 选中窗口 | 学习率 |","|---|---:|---:|"]
    for f,c in result["selected"].items():lines.append(f"| {f} | {int(c['lookback'])} | {c['lr']:g} |")
    lines += ["","## 综合 loss","","以下为三个种子的指标均值 ± 种子标准差，不是统计置信区间；展示的是各自最佳验证检查点的训练/验证 loss，没有将集成预测当成单模型。",
        "","| 模型 | Train loss | Val loss | 相对照抄基准的验证 MSE 降幅 |","|---|---:|---:|---:|"]
    for name in ("Persistence","RNN","LSTM"):
        a=comparison.loc[comparison.model.eq(name)&comparison.split.eq("train")].iloc[0]
        b=comparison.loc[comparison.model.eq(name)&comparison.split.eq("validation")].iloc[0]
        def cell(row):return f"{row.loss_mean:.6f}"+(f" ± {row.loss_seed_sd:.6f}" if name!="Persistence" else "")
        lines.append(f"| {name} | {cell(a)} | {cell(b)} | {100*b.skill_vs_persistence:.2f}% |")
    lines += ["","![训练与验证曲线](figures/train_validation_loss.png)","",
        "## 各变量的标准化 MSE","","| 变量 | 分区 | 照抄 | RNN | LSTM |","|---|---|---:|---:|---:|"]
    for target in experiment.TARGETS:
        for part in ("train","validation"):
            d=targets.loc[targets.target.eq(target)&targets.split.eq(part)&targets.metric.eq("standardised_MSE")].set_index("model")
            lines.append(f"| {target} | {part} | {d.loc['Persistence','mean']:.6f} | {d.loc['RNN','mean']:.6f} | {d.loc['LSTM','mean']:.6f} |")
    lines += ["","## 电价的原始单位 MSE","","MSE 单位为 (£/MWh)²，开平方得到 RMSE。","","| 模型 | 训练电价 MSE | 验证电价 MSE |","|---|---:|---:|"]
    for name in ("Persistence","RNN","LSTM"):
        d=price.loc[price.model.eq(name)].set_index("split")
        lines.append(f"| {name} | {d.loc['train','mean']:.3f} | {d.loc['validation','mean']:.3f} |")
    lines += ["","## 解释与复现","",
        "这些是用于早停和选型的验证结果，不是新的独立测试结果。不同年份的波动水平不同，train/val 的高低同时受行情影响，应结合各分区照抄基准判断。当前数据是事后修复历史，尚未完成逐日发布版本审计；没有新增外部特征或合同罚则，也没有计算 MPC 收益。",
        "","run_nextday.py 完成数据划分、训练和导出；summarise_nextday.py 独立复算 loss、重放检查点并生成图表。本轮使用前一试验的隔离 PyTorch 环境，依赖见 requirements.txt。原七日试验未改动。",
        "","Ridge 即岭回归，是带 L2 正则化的线性预测模型；拟合它可以调用线性方程求解方法。RNN/LSTM 则通过 AdamW 拟合。Xpress 是后续能源调度求解器。这些角色不同。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cpu\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit))
    print(comparison.to_string(index=False))
    print(price.to_string(index=False))


if __name__=="__main__":
    torch.set_num_threads(2)
    main()
