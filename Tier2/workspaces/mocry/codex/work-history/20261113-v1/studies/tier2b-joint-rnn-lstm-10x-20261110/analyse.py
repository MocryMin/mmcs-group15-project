"""Audit joint checkpoints and show aggregate and component three-seed losses."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import data as dataset
from model import TARGETS,COUNTS,WIDTHS,Predictor
from fit_core import configure,tensors,predict,score,sha,dump,PARTS

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
ZH={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价","JOINT":"综合"}
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
SEEDS=[17,29,43]


def audit(result,runs,metrics,x,data,mean,scale):
    protocol=result["protocol"];config=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    old=json.loads((ROOT/"reference/results/SELECTION_FROZEN.json").read_text())
    assert all(config[m]["lookback"]==old[m]["lookback"] and config[m]["lr"]==old[m]["lr"] for m in config)
    assert all(sha(ROOT/n)==v for n,v in protocol["source_hashes"].items())
    assert sha(ROOT/"inputs/model_daily.csv")==protocol["source_input_sha256"]=="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"
    for name in ("scalers.json","splits.csv"):assert (ROOT/name).read_bytes()==(ROOT/"reference"/name).read_bytes()
    assert len(runs)==12 and set(zip(runs.family,runs.budget,runs.seed))=={(f,b,s) for f in ("RNN","LSTM") for b in ("small","large") for s in SEEDS}
    assert len(metrics)==144 and metrics.groupby(["family","budget","seed","split"]).size().eq(4).all()
    reference_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/"reference").rglob("*") if p.is_file()}
    dump(ROOT/"REFERENCE_MANIFEST.json",reference_hashes)
    histories={};max_replay=0.;max_metric=0.;max_log=0.;max_component_identity=0.;cpu_cuda=[];diagnostics=[]
    for r in runs.itertuples():
        assert r.lookback==config[r.family]["lookback"] and r.lr==config[r.family]["lr"]
        assert r.parameters==COUNTS[r.family][r.budget] and r.device=="cuda" and r.eval_batch==2048
        cp=torch.load(ROOT/r.checkpoint.replace("\\","/"),weights_only=True)
        assert cp["parameters"]==r.parameters and cp["hidden"]==WIDTHS[r.family][r.budget] and cp["horizon"]==1 and cp["features"]==8 and cp["targets"]==TARGETS
        assert cp["seed"]==r.seed and cp["family"]==r.family and cp["budget"]==r.budget
        assert np.array_equal(cp["mean"],mean) and np.array_equal(cp["std"],scale)
        cache=json.loads((ROOT/"case_results"/(r.run+".json")).read_text())
        assert cache["signature"]["torch"]==protocol["torch"]
        assert all(cache["signature"][n]==sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","inputs/model_daily.csv","CONFIGS_FROZEN.json"))
        h=pd.read_csv(ROOT/r.step_log.replace("\\","/"));histories[r.run]=h
        assert len(h)==r.steps+1 and np.array_equal(h.global_step,np.arange(r.steps+1)) and r.steps==r.epochs*18
        for part in PARTS:
            cols=[part+"_"+t+"_loss" for t in TARGETS]
            assert np.isfinite(h[[part+"_eval_loss",*cols]]).all().all()
            diff=float(np.max(np.abs(h[cols].mean(1)-h[part+"_eval_loss"])))
            max_component_identity=max(max_component_identity,diff);assert diff<1e-12
        best=float("inf");chosen=0
        for line in h.itertuples():
            improved=line.validation_eval_loss<best-1e-5;assert bool(line.checkpoint_improved)==improved
            if improved:best=line.validation_eval_loss;chosen=line.global_step
            assert abs(line.best_validation_so_far-best)<1e-12
            if line.global_step:
                assert line.epoch==(line.global_step-1)//18+1 and line.batch_index==(line.global_step-1)%18+1
                assert line.batch_size_actual==(8 if line.batch_index==18 else 64)
                assert line.samples_seen==(line.epoch-1)*1096+min(64*line.batch_index,1096)
        assert chosen==r.best_step==cp["best_step"] and abs(best-r.best_validation_loss)<1e-12
        stale=0
        for epoch,g in h.loc[h.epoch.gt(0)].groupby("epoch"):
            assert len(g)==18;stale=0 if g.checkpoint_improved.any() else stale+1
            assert stale<15 or epoch==r.epochs
        assert r.epochs==120 or stale==15
        model=Predictor(r.family,r.budget).to("cuda");assert sum(p.numel() for p in model.parameters())==r.parameters
        model.load_state_dict(cp["state_dict"]);dd=tensors(x,data,r.lookback);saved=np.load(ROOT/"predictions"/(r.run+".npz"))
        for part,(xx,yy) in dd.items():
            raw=predict(model,xx).cpu().numpy().astype(float)*scale+mean
            assert raw.shape==saved[part].shape==(len(data[part]["origins"]),3)
            max_replay=max(max_replay,float(np.max(np.abs((raw-saved[part])/scale))))
            mm=score(saved[part],data[part]["truth"],scale)
            for m in mm:
                stored=metrics.loc[metrics.family.eq(r.family)&metrics.budget.eq(r.budget)&metrics.seed.eq(r.seed)&metrics.split.eq(part)&metrics.target.eq(m["target"])].iloc[0]
                for key in ("loss","MSE","RMSE","MAE"):
                    if key in m:max_metric=max(max_metric,abs(m[key]-stored[key])/max(1.,abs(m[key])))
                name=part+"_eval_loss" if m["target"]=="JOINT" else part+"_"+m["target"]+"_loss"
                max_log=max(max_log,abs(m["loss"]-h.iloc[chosen][name]))
            baseline=(x[data[part]["origins"],:3].astype(float)*scale+mean)
            persistence=score(baseline,data[part]["truth"],scale)
            assert abs(persistence[0]["loss"]-h.iloc[0][part+"_eval_loss"])<1e-7
        if r.seed==17:
            xx=dd["test"][0][:8];gpu=predict(model,xx,8).cpu().numpy();model.to("cpu");cpu=predict(model,xx.cpu(),8).numpy()
            difference=float(np.abs(cpu-gpu).max());assert difference<2e-5
            cpu_cuda.append({"family":r.family,"budget":r.budget,"max_normalised_prediction_difference":difference})
        diagnostics.append({"run":r.run,"family":r.family,"budget":r.budget,"seed":r.seed,"selected_step":chosen,"steps":r.steps,
            **{part+"_selected":h.iloc[chosen][part+"_eval_loss"] for part in PARTS},
            **{part+"_last_minus_selected":h.iloc[-1][part+"_eval_loss"]-h.iloc[chosen][part+"_eval_loss"] for part in PARTS}})
    assert max_replay<2e-5 and max_metric<1e-10 and max_log<3e-8
    pd.concat(histories.values(),ignore_index=True).to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False)
    record={"all_passed":True,"unique_fits":12,"joint_outputs":3,"new_small_controls":True,"same_current_data_splits_scalers_features":True,"frozen_previous_joint_windows_lr":True,
        "parameter_counts_and_formulas_verified":True,"one_joint_val_checkpoint_for_all_targets":True,"validation_only_selection_and_stopping":True,"every_step_full_three_sets_and_components":True,
        "optimizer_updates":int(runs.steps.sum()),"evaluation_rows":sum(len(h) for h in histories.values()),"max_normalised_replay_prediction_difference":max_replay,
        "max_relative_metric_difference":max_metric,"max_prediction_vs_log_loss_difference":max_log,"max_joint_vs_mean_components_difference":max_component_identity,
        "cpu_cuda_replay":cpu_cuda,"test_is_monitored_not_blind":True,"MPC_evaluated":False}
    dump(R/"AUDIT.json",record);return histories,record


def summarise(metrics):
    rows=[]
    for (f,b,t,p),g in metrics.groupby(["family","budget","target","split"],sort=False):
        assert len(g)==3 and set(g.seed)==set(SEEDS)
        rows.append({"family":f,"budget":b,"target":t,"split":p,"parameters":int(g.parameters.iloc[0]),"lookback":int(g.lookback.iloc[0]),"seeds":3,
            "loss_mean":g.loss.mean(),"loss_sd":g.loss.std(ddof=1),
            **({k+"_mean":g[k].mean() for k in ("MSE","RMSE","MAE")} if t!="JOINT" else {})})
    summary=pd.DataFrame(rows);summary.to_csv(R/"SUMMARY.csv",index=False)
    changes=[]
    for family in ("RNN","LSTM"):
        for target in ["JOINT",*TARGETS]:
            for part in PARTS:
                s=metrics.loc[metrics.family.eq(family)&metrics.budget.eq("small")&metrics.target.eq(target)&metrics.split.eq(part)].sort_values("seed")
                l=metrics.loc[metrics.family.eq(family)&metrics.budget.eq("large")&metrics.target.eq(target)&metrics.split.eq(part)].sort_values("seed")
                delta=100*(l.loss.to_numpy()/s.loss.to_numpy()-1)
                changes.append({"family":family,"target":target,"split":part,"small_mean":s.loss.mean(),"large_mean":l.loss.mean(),"mean_loss_change_pct":100*(l.loss.mean()/s.loss.mean()-1),
                    "seed17_pct":delta[0],"seed29_pct":delta[1],"seed43_pct":delta[2],"large_better_seeds":int((delta<0).sum()),"small_seed_sd":s.loss.std(ddof=1),"large_seed_sd":l.loss.std(ddof=1)})
    changes=pd.DataFrame(changes);changes.to_csv(R/"LARGE_VS_SMALL.csv",index=False)
    return summary,changes


def plot(metrics,runs,histories):
    folder=ROOT/"figures";folder.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    def distribution(ax,family,target,part):
        for j,(budget,color,marker) in enumerate((("small","#245c91","o"),("large","#a47736","s"))):
            v=metrics.loc[metrics.family.eq(family)&metrics.budget.eq(budget)&metrics.target.eq(target)&metrics.split.eq(part)].sort_values("seed").loss.to_numpy()
            ax.scatter(j+np.array([-.08,0,.08]),v,color=color,marker=marker,s=30,zorder=4)
            ax.errorbar([j],[v.mean()],yerr=[v.std(ddof=1)],fmt="_",color="black",capsize=5,markersize=20)
        ax.set_xticks([0,1],[f"{COUNTS[family]['small']:,}",f"{COUNTS[family]['large']:,}"]);ax.set(xlabel="Trainable parameters",ylabel="Train-standardised MSE");ax.grid(axis="y",alpha=.15)
    fig,axes=plt.subplots(2,3,figsize=(13,7.6),layout="constrained")
    for i,family in enumerate(("RNN","LSTM")):
        for k,part in enumerate(PARTS):distribution(axes[i,k],family,"JOINT",part);axes[i,k].set_title(family+" / "+part.capitalize())
    fig.suptitle("Joint next-day prediction: equal mean of generation, demand and price losses\nFrozen RNN28 / LSTM56; three points: seeds 17,29,43; black interval: mean ± seed SD (not CI)",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("joint_seed_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(10.5,10),layout="constrained")
    for i,target in enumerate(TARGETS):
        for k,family in enumerate(("RNN","LSTM")):distribution(axes[i,k],family,target,"test");axes[i,k].set_title(EN[target]+" / "+family+" / Test")
    fig.suptitle("Component test losses at the SAME joint-validation-selected checkpoint\nMean ± seed SD; no target-specific checkpoint selection",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("target_test_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12.5,8),layout="constrained")
    for i,family in enumerate(("RNN","LSTM")):
        for k,budget in enumerate(("small","large")):
            r=next(runs.loc[runs.family.eq(family)&runs.budget.eq(budget)].sort_values("best_validation_loss").iloc[[1]].itertuples());h=histories[r.run];ax=axes[i,k]
            for part,color in zip(PARTS,("#245c91","#bb7625","#38844d")):ax.plot(h.global_step,h[part+"_eval_loss"],color=color,lw=.9,label=part)
            ax.axvline(r.best_step,color="black",ls=":",lw=.8,label="Joint-val checkpoint")
            ax.set(title=f"{family}, {r.parameters:,} parameters, seed {r.seed}\nL={r.lookback}; selected step {r.best_step}",xlabel="Optimiser step",ylabel="Joint standardised MSE");ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False)
    fig.suptitle("Every-step full train / validation / test evaluation\nMedian-validation seed per configuration; no smoothing",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("joint_step_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def report(summary,changes,record,runs):
    def row(f,b,t,p):return summary.loc[summary.family.eq(f)&summary.budget.eq(b)&summary.target.eq(t)&summary.split.eq(p)].iloc[0]
    def cell(r):return f"{r.loss_mean:.6f} ± {r.loss_sd:.6f}"
    lines=["# 联合次日RNN / LSTM扩大约10倍：三种子比较","",
        "一个模型读取过去L天×8维特征，同时输出次日供给、需求、电价三个数，三者共享循环编码器。这里只扩大隐藏宽度，输出跨度仍是一天。RNN从hidden68/5511参数扩至hidden228/54951参数；LSTM从hidden32/5475参数扩至hidden112/54995参数，分别为9.971倍和10.045倍。","",
        "当前结果：大RNN综合test loss变化+0.22%，大LSTM变化−1.18%。两者均未显示明显的整体测试收益；RNN电价三个seed均变差，LSTM电价三个seed均改善，但LSTM综合结果的种子波动增加。以下同时披露综合与分项结果，不把几个不同方向的变化压成单一结论。","",
        "## 窗口、数据与训练","",
        "沿用之前联合次日实验按val选出的RNN28天、LSTM56天，学习率均0.003。这是两个联合模型各自的单一窗口；独立模型smoke得到的六个按目标区分的窗口不直接套入联合结构。本轮没有重新搜索窗口/学习率。","",
        "当前train目标2022-01-01—2024-12-31共1096日，val目标2025-01-01—2025-08-31共243日，test目标2025-09-01—2026-08-31共365日。输入与当前Transformer实验相同：冻结修复的三条历史序列，星期sin/cos、年内sin/cos、周末标志，共8维；2021年仅作为历史，scaler只fit train。总供给包含独立风场，电价为名义GBP/MWh。","",
        "旧联合模型是在2020–22训练、2023验证，不能拿其loss直接对照当前年份。因此本轮在相同当前划分、相同GPU软件环境从零重训小模型对照；两家族×两预算×seeds17/29/43，共12次新拟合。","",
        "RTX5090 Laptop GPU，PyTorch2.14.1+cu130；float32、AMP/TF32关闭，确定性CUDA/cuDNN，单层循环网络+输出dropout0.1+线性三输出，预测值为当天观测加模型预测变化；输出头零初始化，step0等于照抄当天。AdamW、weight decay0.0001、梯度范数截断1、batch64，每epoch18step，最多120epoch，15个完整epoch无val改善则早停，改善阈值0.00001。","",
        "每个step完整评估train、val、test，同时记录综合loss与三个分项loss。仅综合val选择一个checkpoint/早停，三个目标在同一checkpoint上评价，不为每个目标另挑最优时刻。","",
        "设训练期标准差为$s_j$，综合loss为 $\\frac{1}{3N}\\sum_{i=1}^{N}\\sum_{j=1}^{3}((\\widehat y_{ij}-y_{ij})/s_j)^2$。下表为各seed自己综合val最优点的结果，±是三个seed的样本标准差，不是置信区间或集成误差。","",
        "## 综合Train / Val / Test","","|模型|参数量|窗口/天|Train loss|Val loss|Test loss|","|---|---:|---:|---:|---:|---:|"]
    for f in ("RNN","LSTM"):
        for b in ("small","large"):
            r=row(f,b,"JOINT","test");lines.append(f"|{f} {b}|{COUNTS[f][b]:,}|{int(r.lookback)}|{cell(row(f,b,'JOINT','train'))}|{cell(row(f,b,'JOINT','validation'))}|{cell(r)}|")
    lines.extend(["","![综合三种子误差](figures/joint_seed_losses.png)","","## 三个输出的分项loss","",
        "每行仍使用该seed的同一综合val最优checkpoint。分项采用相同训练期标准差，三个分项平均即上表综合loss。","",
        "|目标|模型|参数量|Train loss|Val loss|Test loss|","|---|---|---:|---:|---:|---:|"])
    for t in TARGETS:
        for f in ("RNN","LSTM"):
            for b in ("small","large"):
                lines.append(f"|{ZH[t]}|{f} {b}|{COUNTS[f][b]:,}|{cell(row(f,b,t,'train'))}|{cell(row(f,b,t,'validation'))}|{cell(row(f,b,t,'test'))}|")
    lines.extend(["","![三个目标的test误差](figures/target_test_losses.png)","","## 扩大模型的变化","",
        "负值表示大模型更好；均值变化是大模型三seed的平均MSE/小模型平均MSE−1。相同seed不代表网络扩宽后仍具有相同随机初始化扰动，也不是数据重采样。","",
        "|模型|目标|分区|平均loss变化|Seed17|Seed29|Seed43|大模型更好次数|","|---|---|---|---:|---:|---:|---:|---:|"])
    for r in changes.itertuples():
        if r.target=="JOINT" or r.split=="test":lines.append(f"|{r.family}|{ZH[r.target]}|{r.split}|{r.mean_loss_change_pct:+.2f}%|{r.seed17_pct:+.2f}%|{r.seed29_pct:+.2f}%|{r.seed43_pct:+.2f}%|{r.large_better_seeds}/3|")
    lines.extend(["","## 结果判断","",
        "大RNN相对小RNN：供给test均值降低1.16%，需求增加0.15%，电价增加4.31%，综合增加0.22%。电价三个对应seed均变差；综合test SD虽从0.001666缩至0.000220，但只是结果更集中，不能据此称为误差更低。综合val均值也没有改善。","",
        "大LSTM相对小LSTM：供给test增加0.19%，需求降低2.59%，电价降低2.40%，综合降低1.18%。电价三个对应seed均改善，综合则只有两个改善，其中seed29降低约3.98%，另外两个分别约+0.64%和−0.17%；综合均值收益较依赖seed29。综合test SD从0.000920增至0.002742，应同时保留这项波动。","",
        "在当前冻结窗口、学习率和训练预算下，没有证据支持仅扩大联合模型就能带来稳健的整体增益。LSTM的电价改善方向较一致，可保留为候选结果；这不等于最终选择已完成，也不代表大模型重新调参后的最好能力。小模型与大模型均使用相同当前年份，旧联合实验的2023验证loss不参与数值对照。","",
        "## 训练轨迹与解释","","![逐step完整三集曲线](figures/joint_step_losses.png)","",
        "图中选每个配置综合val排序居中的seed，未用test挑选，曲线未平滑。其余种子与所有分项轨迹完整保存在step_logs和ALL_STEP_LOSSES.csv；OVERFIT_DIAGNOSTICS.csv保留训练末尾相对所选点的变化。","",
        "![两个大模型的全部三个种子](figures/large_all_seed_joint_steps.png)","",
        "上图展示两个大模型的全部三个种子，不隐藏初期尖峰，子图y轴按各自数值范围显示。下图将综合loss拆为三个输出的loss；每个家族仍使用综合val居中的同一个seed，各输出共享同一条checkpoint竖线。","",
        "![大模型各输出的逐step loss](figures/large_component_step_losses.png)","",
        "所选点的train loss不等于训练能达到的最低train loss，扩大模型改变了训练路径和早停时刻，因此该点train loss不一定更低。训练/验证年份的分布也不同，不能把跨分区差值全部解释成过拟合。","",
        "大LSTM在所选点之后继续训练，三个seed的train均明显下降而val/test均上升，支持保留早停；大RNN轨迹更抖，两个seed在结束时连train loss也高于所选点，不能把其无收益全部解释为训练拟合更强而导致的过拟合。这里只观察到固定设置下的优化路径变化，未进一步测试其他学习率或调度。","",
        "## 核验与文件","",
        f"{record['unique_fits']}次拟合，{record['optimizer_updates']:,}次更新，含step0共{record['evaluation_rows']:,}行全量评估，每行含综合和三个分项的三集loss。数据/scaler/划分、参数公式、窗口冻结、训练覆盖、单一综合val选点/早停、12个checkpoint和原始单位预测独立复算全部通过。最大标准化重放预测差{record['max_normalised_replay_prediction_difference']:.3g}，预测与日志loss最大差{record['max_prediction_vs_log_loss_difference']:.3g}。","",
        "- SUMMARY.csv：各家族/预算/分区/目标的三种子均值与SD。","- LARGE_VS_SMALL.csv：完整平均及逐seed变化。","- SIMPLE_BASELINES.csv：相同目标日期上的照抄当天/上周同日基准。","- checkpoints/、predictions/、step_logs/：12组权重、原始单位预测、每step综合和分项loss。","- CONFIGS_FROZEN.json、PROTOCOL.json、PREFLIGHT.json、AUDIT.json：配置、完整协议、GPU预检和核验。","",
        "安装requirements.txt后按preflight.py、run.py、analyse.py的顺序复现。只在本地运行，不修改旧实验；未新增外部特征，未做MPC或数据发布版本审计，test已被多轮监测并非盲测。"])
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    configure();result=json.loads((R/"RESULTS.json").read_text());f,x,data,mean,scale=dataset.prepare(False)
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"ALL_METRICS.csv")
    histories,record=audit(result,runs,metrics,x,data,mean,scale)
    summary,changes=summarise(metrics);plot(metrics,runs,histories)
    import generate_replays
    generate_replays.main();report(summary,changes,record,runs)
    print("JOINT",summary.loc[summary.target.eq("JOINT"),["family","budget","split","loss_mean","loss_sd"]].to_string(index=False))
    print("TEST",changes.loc[changes.split.eq("test")].to_string(index=False));print("AUDIT",json.dumps(record))


if __name__=="__main__":main()
