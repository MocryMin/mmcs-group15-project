"""Audit exported forecasts, create readable results and scientific figures."""
from pathlib import Path
import hashlib
import json
import platform
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import torch

import run_experiment as experiment

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"


def main():
    result=json.loads((R/"RESULTS.json").read_text(encoding="utf-8"))
    protocol=result["protocol"]
    frame=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date")
    scalers=json.loads((ROOT/"scalers.json").read_text())
    mean=np.array([scalers["mean"][s] for s in experiment.TARGETS])
    scale=np.array([scalers["std"][s] for s in experiment.TARGETS])
    checks={}
    checks["source_hashes"]=all(hashlib.sha256((ROOT/"inputs"/name).read_bytes()).hexdigest()==m["sha256"] for name,m in protocol["input_hashes"].items())
    source=frame.loc["2020":"2022",experiment.TARGETS].to_numpy()
    checks["train_only_mean_std"]=bool(np.allclose(mean,source.mean(0)) and np.allclose(scale,source.std(0)))
    splits=pd.read_csv(ROOT/"splits.csv",parse_dates=["origin","input_start_56","first_target","last_target"])
    checks["origins_before_all_targets"]=bool((splits.origin<splits.first_target).all())
    checks["input_history_ends_at_origin"]=bool(((splits.origin-splits.input_start_56).dt.days==55).all())
    checks["targets_within_designated_split"]=all(bool(((g.first_target>=pd.Timestamp(experiment.SPLITS[s][0]))&(g.last_target<=pd.Timestamp(experiment.SPLITS[s][1]))).all()) for s,g in splits.groupby("split"))
    checks["partial_2026_not_evaluated"]=bool((splits.last_target<pd.Timestamp("2026-01-01")).all())
    runs=pd.read_csv(R/"training_runs.csv")
    checks["same_parameter_budget"]=bool(set(runs.loc[runs.family.eq("RNN"),"parameters"])=={6101} and set(runs.loc[runs.family.eq("LSTM"),"parameters"])=={6069})
    checks["grid_all_24_runs"]=bool(len(runs)==24 and runs.groupby(["family","lookback","lr"]).size().eq(3).all())
    grid=pd.read_csv(R/"validation_grid.csv")
    checks["selection_uses_validation_only"]=all(np.isclose(float(grid.loc[grid.family.eq(f),"mean"].min()),float(v["mean"]),rtol=0,atol=1e-12) for f,v in result["selected"].items())
    worst_metric_difference=0.
    predictions={}
    for split in ("validation","test"):
        z=np.load(R/(split+"_predictions.npz"))
        predictions[split]={k:z[k] for k in z.files}
        for name,record in result["metrics"][split].items():
            for j,target in enumerate(experiment.TARGETS):
                error=z[name][:,:,j]-z["truth"][:,:,j]
                observed=record["targets"][target]
                worst_metric_difference=max(worst_metric_difference,abs(np.abs(error).mean()-observed["MAE"]),abs(np.sqrt(np.mean(error**2))-observed["RMSE"]))
        dates=frame.index.to_numpy()
        naive=np.stack([np.stack([frame[experiment.TARGETS].to_numpy()[t+k-7] for k in range(1,8)]) for t in z["origins"]])
        checks[split+"_seasonal_naive_uses_only_past"]=bool(np.allclose(naive,z["SeasonalNaive"]))
        checks[split+"_physical_prediction_bounds"]=all(bool((z[k][:,:,:2]>=0).all()) for k in result["metrics"][split])
    checks["independent_metric_recalculation"]=worst_metric_difference<1e-8
    # Evaluate the selected checkpoints on training examples, without re-fitting.
    xnorm=(frame[experiment.TARGETS].to_numpy()-mean)/scale
    day=frame.index.dayofweek.to_numpy()
    phase=(frame.index.dayofyear.to_numpy()-1)/np.where(frame.index.is_leap_year,366,365)
    x=np.column_stack([xnorm,np.sin(2*np.pi*day/7),np.cos(2*np.pi*day/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),day>=5]).astype(np.float32)
    train_origins=frame.index.get_indexer(splits.loc[splits.split.eq("train"),"origin"])
    traintruth=np.stack([frame[experiment.TARGETS].to_numpy()[t+1:t+8] for t in train_origins])
    trainstrict=np.stack([frame.strict_no_imputation.to_numpy()[t+1:t+8] for t in train_origins])
    trainmetrics={}
    for family,choice in result["selected"].items():
        for seed in experiment.SEEDS:
            run=runs.loc[runs.family.eq(family)&runs.lookback.eq(choice["lookback"])&runs.lr.eq(choice["lr"])&runs.seed.eq(seed)].iloc[0]
            cp=torch.load(ROOT/run.checkpoint,weights_only=True)
            model=experiment.Forecaster(family);model.load_state_dict(cp["state_dict"]);model.eval()
            assert sum(p.numel() for p in model.parameters())==int(run.parameters)
            xx=torch.from_numpy(experiment.windows(x,train_origins,int(choice["lookback"])))
            with torch.no_grad(): p=experiment.denormalise(model(xx).numpy(),mean,scale)
            trainmetrics[f"{family}_seed{seed}"]=experiment.metrics(p,traintruth,trainstrict,mean,scale)
    experiment.dump(R/"training_selected_metrics.json",trainmetrics)

    summaries=[]
    for split in ("validation","test"):
        for family in ("RNN","LSTM"):
            for target in experiment.TARGETS:
                for horizon in (1,3,7):
                    vals=[result["metrics"][split][f"{family}_seed{s}"]["targets"][target]["horizons"][str(horizon)] for s in experiment.SEEDS]
                    summaries.append(dict(split=split,model=family,target=target,horizon=horizon,
                        MAE_mean=float(np.mean([v["MAE"] for v in vals])),MAE_seed_sd=float(np.std([v["MAE"] for v in vals],ddof=1)),
                        RMSE_mean=float(np.mean([v["RMSE"] for v in vals])),RMSE_seed_sd=float(np.std([v["RMSE"] for v in vals],ddof=1))))
        for name in ("Persistence","SeasonalNaive","Ridge"):
            for target in experiment.TARGETS:
                for horizon in (1,3,7):
                    m=result["metrics"][split][name]["targets"][target]["horizons"][str(horizon)]
                    summaries.append(dict(split=split,model=name,target=target,horizon=horizon,
                                          MAE_mean=m["MAE"],MAE_seed_sd=0.,RMSE_mean=m["RMSE"],RMSE_seed_sd=0.))
    summary=pd.DataFrame(summaries)
    summary.to_csv(R/"MODEL_COMPARISON.csv",index=False)
    yearly=[]
    for year in (2024,2025):
        z=predictions["test"]
        origin_dates=frame.index[z["origins"]]
        years=np.stack([(origin_dates+pd.Timedelta(days=k)).year for k in range(1,8)],axis=1)
        mask=years==year
        for name in result["metrics"]["test"]:
            e=z[name][:,:,2]-z["truth"][:,:,2]
            yearly.append(dict(year=year,model=name,price_MAE=float(np.abs(e[mask]).mean()),price_RMSE=float(np.sqrt(np.mean(e[mask]**2))),count=int(mask.sum())))
    pd.DataFrame(yearly).to_csv(R/"test_price_by_target_year.csv",index=False)
    audit=dict(checks=checks,all_passed=all(checks.values()),worst_metric_difference=worst_metric_difference,
               data_vintage_audit=False,data_vintage_note=protocol["limitations"][0])
    experiment.dump(R/"AUDIT.json",audit)
    assert audit["all_passed"],audit

    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    figures=ROOT/"figures";figures.mkdir(exist_ok=True)
    colors={"Persistence":"#777777","SeasonalNaive":"#969696","Ridge":"#39735b","RNN":"#b66b22","LSTM":"#245c91"}
    fig,axes=plt.subplots(1,3,figsize=(13,3.9),layout="constrained")
    for j,(ax,target) in enumerate(zip(axes,experiment.TARGETS)):
        for name in ("Persistence","SeasonalNaive","Ridge","RNN","LSTM"):
            if name in ("RNN","LSTM"):
                a=np.array([[result["metrics"]["test"][f"{name}_seed{s}"]["targets"][target]["horizons"][str(k)]["MAE"] for k in range(1,8)] for s in experiment.SEEDS])
                avg=a.mean(0);sd=a.std(0,ddof=1)
                ax.fill_between(range(1,8),avg-sd,avg+sd,color=colors[name],alpha=.12)
            else:
                avg=np.array([result["metrics"]["test"][name]["targets"][target]["horizons"][str(k)]["MAE"] for k in range(1,8)])
            ax.plot(range(1,8),avg,label=name,color=colors[name],linestyle="--" if "Naive" in name or name=="Persistence" else "-",marker="o",markersize=3)
        ax.set(title=["Total available generation","Market demand","Market index price"][j],xlabel="Forecast lead (days)",ylabel="MAE ("+ ("GBP/MWh" if j==2 else "MW daily mean")+")",xticks=range(1,8));ax.grid(alpha=.18)
    handles,labels=axes[-1].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=5,frameon=False)
    fig.suptitle("Held-out 2024–2025: forecast error by lead time\nNeural curves: mean of 3 seeds; shading: seed standard deviation",fontsize=11)
    fig.savefig(figures/"test_mae_by_horizon.png",dpi=180);fig.savefig(figures/"test_mae_by_horizon.svg");plt.close(fig)
    daily=pd.read_csv(R/"test_one_day_predictions.csv",parse_dates=["target_date"]).set_index("target_date")
    fig,axes=plt.subplots(3,1,figsize=(12.5,7),layout="constrained")
    for ax,(start,end) in zip(axes,[("2024-01-01","2024-03-31"),("2024-09-01","2024-11-30"),("2025-06-01","2025-08-31")]):
        d=daily.loc[start:end];ax.plot(d.index,d.price_GBP_MWh_actual,color="black",lw=1.2,label="Actual")
        for family in ("RNN","LSTM"):
            ax.plot(d.index,d["price_GBP_MWh_"+family+"_ensemble"],label=family+" (3-seed mean)",color=colors[family],lw=1.,alpha=.85)
        ax.set(ylabel="GBP/MWh",title=start+" to "+end);ax.grid(alpha=.18)
    axes[0].legend(ncol=3,frameon=False);fig.suptitle("One-day-ahead market-price predictions: fixed diagnostic periods",fontsize=12)
    fig.savefig(figures/"price_prediction_examples.png",dpi=180);fig.savefig(figures/"price_prediction_examples.svg");plt.close(fig)

    def row(split,model,target,h):
        return summary.loc[summary.split.eq(split)&summary.model.eq(model)&summary.target.eq(target)&summary.horizon.eq(h)].iloc[0]
    lines=["# RNN 与 LSTM 预测试验：2026-11-09","",
        "本轮只比较预测，不计算 MPC 收益；不包含 attention、Transformer 或外部特征。",
        "","## 数据与划分","",
        "使用冻结的修复数据。总供给为课程总发电加独立风场；供给和需求均预测每日平均功率（MW），电价为名义英镑/MWh。保留负电价，不使用事后全月 CPI 构造预测输入。",
        "","| 分区 | 目标日期范围 | 原始日数 | 完整七日预测样本数 |","|---|---|---:|---:|"]
    for split,title in (("train","训练"),("validation","验证"),("test","测试")):
        a,b=experiment.SPLITS[split];days=len(frame.loc[a:b]);n=protocol["splits"][split]["samples"]
        lines.append(f"| {title} | {a}–{b} | {days:,} | {n:,} |")
    lines += ["","预测起点为当天输入已知之后，目标为未来第 1–7 日；目标日期不跨分区。各次预测可使用截至当日已经观测到的历史，包括前一分区的过去数据。所有配置使用共同的预测起点集合。2026 年部分年未用于选型或测试。",
        "","## 模型与验证选型","",
        "单层传统 tanh RNN：64 隐藏单元、6,101 参数；单层 LSTM：32 隐藏单元、6,069 参数。两者有相同的残差预测头：以当天值为起点，预测未来变化；输入为三条标准化序列和五个日历特征。没有 attention。",
        "","两种模型均比较 28/56 日窗口及 0.001/0.003 学习率，每配置使用 17、29、43 三个随机种子，共 24 次训练。AdamW、batch 64、weight decay 0.0001、梯度裁剪 1；最多 120 epoch，验证集连续 15 epoch 无实质改善则停止。以三变量、七跨度等权标准化验证 MSE 的种子均值选配置。验证集还用于早停，不作为独立最终结论。",
        "","| 模型 | 选中窗口 | 学习率 | 验证标准化 MSE：三种子均值 |","|---|---:|---:|---:|"]
    for family,c in result["selected"].items(): lines.append(f"| {family} | {int(c['lookback'])} | {c['lr']:g} | {c['mean']:.5f} |")
    lines += [f"| Ridge 基准 | 56 | alpha={result['ridge']['selected']['alpha']:g} | {result['ridge']['selected']['validation_standardised_mse']:.5f} |",
        "","## 独立测试结果","",
        "神经模型列为三个随机种子的指标均值 ± 种子标准差，非置信区间；基准模型为单一确定性结果。MAE/RMSE 使用原始单位。主表没有把三模型集成误差当成单模型结果；集成预测另存于导出文件及示例图。",
        "","| 模型 | 电价 1 日 MAE（£/MWh） | 电价 1 日 RMSE（£/MWh） | 电价 7 日 MAE（£/MWh） | 供给 1 日 MAE（MW） | 需求 1 日 MAE（MW） |","|---|---:|---:|---:|---:|---:|"]
    for name in ("Persistence","SeasonalNaive","Ridge","RNN","LSTM"):
        cells=[]
        for target,h,metric in (("price_GBP_MWh",1,"MAE"),("price_GBP_MWh",1,"RMSE"),("price_GBP_MWh",7,"MAE"),("generation_MW",1,"MAE"),("demand_MW",1,"MAE")):
            v=row("test",name,target,h);avg=v[metric+"_mean"];sd=v[metric+"_seed_sd"]
            cells.append(f"{avg:,.2f}"+(f" ± {sd:,.2f}" if name in ("RNN","LSTM") else ""))
        lines.append("| "+name+" | "+" | ".join(cells)+" |")
    lines += ["","![测试误差](figures/test_mae_by_horizon.png)","",
        "完整各跨度 MAE/RMSE 见 [MODEL_COMPARISON.csv](results/MODEL_COMPARISON.csv)；原始预测及逐种子指标见 results。另提供仅在 strict_no_imputation 为真的目标日上的误差，但同一输入窗口内仍可能含修复估计值。",
        "","## 本轮发现","",
        "在两个神经模型之间，普通 RNN 的三变量综合验证/测试标准化 MSE 更低，且供给和需求的预测误差较低。LSTM 的次日电价 MAE 略低于 RNN，但次日持续值基准的 MAE 仍略低于两者。RNN 的次日电价 RMSE 与第七日电价 MAE 优于本轮 LSTM；较低 MAE 和较低 RMSE 的赢家并不完全一致。",
        "","当前结果支持将传统 RNN 留作后续控制实验候选，没有证据因模型名称更复杂便优先选用 LSTM。Ridge 在供给和需求的一日预测上更好，也应保留。正式接入 MPC 后还要评价实际收益，预测误差排序不自动等于调度收益排序。",
        "","## 解释边界","",
        "这是一个固定修复历史数据集上的回顾性预测试验。模型训练/标准化/调参按时间隔离，原始数据修复中的来源发布延迟、后验校准和插值没有重建为逐日版本；不能宣称完成了真实实时数据可得性的审计。",
        "","日均数据和八维基础输入限定了本轮结论。结果不证明某一架构在所有配置、外部天气或官方预测特征下都更好。最终测试结果已经查看，后续模型迭代若反复使用这一测试结果选型，应把它标为已使用的比较期或建立新的最终检验，不能继续宣称它完全未参与研究。",
        "","## 复现与文件","",
        "运行 run_experiment.py 完成训练与预测；运行 analyse_results.py 独立复算指标、检查划分并生成本说明和图表。训练按 CPU 两线程执行。run.log 保留原始训练日志，末尾的首次导出异常来自把 0/1 质量标签当成 true/false 读取；修正后使用同一组权重完成评估，记录在 evaluation.log。修正前后全部预测值的最大差为 0，没有重新选型。",
        "","主要文件：PROTOCOL.json（协议）、splits.csv、scalers.json、inputs/MANIFEST.json、results/validation_grid.csv、results/training_runs.csv、results/RESULTS.json、results/AUDIT.json、checkpoints。",
        "","环境：Python "+platform.python_version()+"；PyTorch "+torch.__version__+"；NumPy "+np.__version__+"；pandas "+pd.__version__+"；SciPy "+scipy.__version__+"；Matplotlib "+matplotlib.__version__+"。环境文件夹 .venv 不属于交付包。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    requirements=["--extra-index-url https://download.pytorch.org/whl/cpu",f"torch=={torch.__version__}",f"numpy=={np.__version__}",f"pandas=={pd.__version__}",f"scipy=={scipy.__version__}",f"matplotlib=={matplotlib.__version__}"]
    (ROOT/"requirements.txt").write_text("\n".join(requirements)+"\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit,ensure_ascii=False))
    print(summary.loc[summary.split.eq("test")&summary.target.eq("price_GBP_MWh")].to_string(index=False))


if __name__=="__main__":
    torch.set_num_threads(2)
    main()
