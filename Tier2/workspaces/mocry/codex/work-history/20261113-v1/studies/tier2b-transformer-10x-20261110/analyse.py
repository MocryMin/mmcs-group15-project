"""Replay every new checkpoint and compare fixed configurations across three seeds."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import data as dataset
from model import Predictor,TARGETS
from fit_core import configure,tensors,normalised_prediction,score,sha,dump

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
SEEDS=[17,29,43]
PARTS=["train","validation","test"]
ZH={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}


def audit(result,runs,metrics,data,x,mean,scale):
    p=result["protocol"];ref=json.loads((ROOT/"REFERENCE.json").read_text())
    archive=ROOT/"reference"/ref["archive"]
    assert sha(archive)==ref["sha256"]
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read("MANIFEST.json"))
        assert all(hashlib.sha256(z.read(n)).hexdigest()==v["sha256"] for n,v in manifest.items())
        assert (ROOT/"fit_core.py").read_bytes()==z.read("fit_core.py").replace(b'"Transformer":5407',b'"Transformer":54005')
        assert (ROOT/"data.py").read_bytes()==z.read("data.py")
        expected=z.read("model.py").decode().replace("24","72").replace("dim_feedforward=54","dim_feedforward=220").replace("Parameter-matched one-layer Transformer and frozen recurrent reference architectures.","Width-scaled one-layer Transformer; all other architecture choices retained.")
        assert (ROOT/"model.py").read_bytes()==expected.encode("utf-8")
        for name in ("scalers.json","splits.csv"):
            assert (ROOT/name).read_bytes()==z.read(name)
    assert all(sha(ROOT/n)==s for n,s in p["source_hashes"].items())
    assert sha(ROOT/"inputs/model_daily.csv")==p["input_sha256"]
    expected={(t,s) for t in TARGETS for s in SEEDS}
    assert len(runs)==9 and set(zip(runs.target,runs.seed))==expected
    assert len(metrics)==27 and metrics.groupby(["target","seed"]).size().eq(3).all()
    assert sum(q.numel() for q in Predictor("Transformer",0).parameters())==54005
    max_prediction=0.;max_loss=0.;max_log_loss=0.;histories={};diagnostics=[];cpu_cuda=[]
    for r in runs.itertuples():
        c=p["configs"][r.target];j=TARGETS.index(r.target)
        assert r.lookback==c["lookback"] and r.lr==c["lr"] and r.device=="cuda" and r.parameters==54005
        value=json.loads((ROOT/"case_results"/(r.run+".json")).read_text())
        assert all(value["signature"][n]==sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","inputs/model_daily.csv"))
        assert value["signature"]["torch"]==p["torch"]
        h=pd.read_csv(ROOT/r.step_log.replace("\\","/"));histories[r.run]=h
        assert np.array_equal(h.global_step,np.arange(r.steps+1)) and r.steps==r.epochs*18
        assert len(h)==r.steps+1 and np.isfinite(h[[v+"_eval_loss" for v in PARTS]]).all().all()
        best=float("inf");chosen=0;stale=0
        for line in h.itertuples():
            improved=line.validation_eval_loss<best-1e-5
            assert bool(line.checkpoint_improved)==improved
            if improved:best=line.validation_eval_loss;chosen=line.global_step
            assert abs(line.best_validation_so_far-best)<1e-12
            if line.global_step:
                assert line.epoch==(line.global_step-1)//18+1 and line.batch_index==(line.global_step-1)%18+1
                assert line.batch_size_actual==(8 if line.batch_index==18 else 64)
                assert line.samples_seen==(line.epoch-1)*1096+min(64*line.batch_index,1096)
        assert chosen==r.best_step and abs(best-r.best_validation_loss)<1e-12
        for epoch,g in h.loc[h.epoch.gt(0)].groupby("epoch"):
            assert len(g)==18
            stale=0 if g.checkpoint_improved.any() else stale+1
            assert stale<15 or epoch==r.epochs
        assert r.epochs==120 or stale==15
        cp=torch.load(ROOT/r.checkpoint.replace("\\","/"),weights_only=True)
        assert cp["best_step"]==chosen and cp["seed"]==r.seed and cp["parameters"]==54005 and cp["target_index"]==j
        assert np.array_equal(cp["mean"],mean) and np.array_equal(cp["std"],scale)
        model=Predictor("Transformer",j).to("cuda");model.load_state_dict(cp["state_dict"])
        dd=tensors(x,data,j,r.lookback,"cuda");saved=np.load(ROOT/"predictions"/(r.run+".npz"))
        for part,(xx,yy) in dd.items():
            norm=normalised_prediction(model,xx,r.eval_batch).cpu().numpy().ravel().astype(float)
            replay=norm*scale[j]+mean[j];pred=saved[part]
            assert len(pred)==len(data[part]["origins"])
            max_prediction=max(max_prediction,float(np.max(np.abs((replay-pred)/scale[j]))))
            s=score(pred,data[part]["truth"][:,j],scale[j]);m=metrics.loc[metrics.target.eq(r.target)&metrics.seed.eq(r.seed)&metrics.split.eq(part)].iloc[0]
            for k,v in s.items():max_loss=max(max_loss,abs(v-m[k])/max(1.,abs(v)))
            max_log_loss=max(max_log_loss,abs(s["loss"]-h.iloc[chosen][part+"_eval_loss"]))
            initial=float(np.mean(((data[part]["truth"][:,j]-(x[data[part]["origins"],j].astype(float)*scale[j]+mean[j]))/scale[j])**2))
            assert abs(initial-h.iloc[0][part+"_eval_loss"])<1e-7
        if r.seed==17:
            batch=dd["test"][0][:8];gpu=normalised_prediction(model,batch,8).cpu().numpy();model.to("cpu")
            cpu=normalised_prediction(model,batch.cpu(),8).numpy()
            diff=float(np.abs(cpu-gpu).max());assert diff<2e-5
            cpu_cuda.append({"run":r.run,"max_normalised_difference":diff})
        last=h.iloc[-1];point=h.iloc[chosen]
        diagnostics.append({"target":r.target,"seed":r.seed,"best_step":chosen,"steps":r.steps,
            **{part+"_selected":float(point[part+"_eval_loss"]) for part in PARTS},
            **{part+"_end_minus_selected":float(last[part+"_eval_loss"]-point[part+"_eval_loss"]) for part in PARTS}})
    assert max_prediction<2e-5 and max_loss<1e-10 and max_log_loss<2e-8
    pd.concat(histories.values(),ignore_index=True).to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False)
    record={"all_passed":True,"new_fits":9,"reference_release_verified_files":len(manifest),"reference_archive_sha256":ref["sha256"],
        "only_model_width_and_count_changed":True,"identical_input_features_splits_scalers_training_code":True,"all_steps_full_three_sets":True,
        "validation_only_checkpoints_and_stopping":True,"max_normalised_replay_prediction_difference":max_prediction,
        "max_relative_metric_difference":max_loss,"max_prediction_loss_vs_log_difference":max_log_loss,"selected_cpu_cuda_checks":cpu_cuda,
        "optimizer_steps":int(runs.steps.sum()),"evaluation_rows":sum(len(v) for v in histories.values()),"monitored_test_not_blind":True,"MPC_evaluated":False}
    dump(R/"AUDIT.json",record)
    return histories,record


def summarise(metrics):
    old=pd.read_csv(ROOT/"reference/results/CONFIRMATION_METRICS.csv")
    old["model"]=old.family.replace({"Transformer":"TF-5k"})
    new=metrics.copy();new["model"]="TF-54k"
    all_metrics=pd.concat([old,new],ignore_index=True)
    rows=[]
    for (t,m,p),g in all_metrics.groupby(["target","model","split"],sort=False):
        assert len(g)==3 and set(g.seed)==set(SEEDS)
        rows.append({"target":t,"model":m,"split":p,"lookback":int(g.lookback.iloc[0]),"lr":float(g.lr.iloc[0]),"seeds":3,
            **{k+"_mean":g[k].mean() for k in ("loss","MSE","RMSE","MAE")},**{k+"_sd":g[k].std(ddof=1) for k in ("loss","MSE","RMSE","MAE")}})
    summary=pd.DataFrame(rows);summary.to_csv(R/"SUMMARY.csv",index=False)
    all_metrics.to_csv(R/"COMBINED_METRICS.csv",index=False)
    changes=[]
    for t in TARGETS:
        for p in PARTS:
            large=all_metrics.loc[all_metrics.target.eq(t)&all_metrics.model.eq("TF-54k")&all_metrics.split.eq(p)].sort_values("seed")
            small=all_metrics.loc[all_metrics.target.eq(t)&all_metrics.model.eq("TF-5k")&all_metrics.split.eq(p)].sort_values("seed")
            vals=100*(large.loss.to_numpy()/small.loss.to_numpy()-1)
            changes.append({"target":t,"split":p,"small_mean":small.loss.mean(),"large_mean":large.loss.mean(),
                "mean_loss_change_pct":100*(large.loss.mean()/small.loss.mean()-1),"seed17_change_pct":vals[0],"seed29_change_pct":vals[1],"seed43_change_pct":vals[2],
                "large_better_seeds":int((vals<0).sum()),"small_seed_sd":small.loss.std(ddof=1),"large_seed_sd":large.loss.std(ddof=1),
                "small_min":small.loss.min(),"small_max":small.loss.max(),"large_min":large.loss.min(),"large_max":large.loss.max()})
    changes=pd.DataFrame(changes);changes.to_csv(R/"LARGE_VS_SMALL.csv",index=False)
    return all_metrics,summary,changes


def plot(all_metrics,runs,histories):
    folder=ROOT/"figures";folder.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(3,3,figsize=(13.5,10),layout="constrained")
    for i,t in enumerate(TARGETS):
        for k,p in enumerate(PARTS):
            ax=axes[i,k]
            for j,(model,color,marker) in enumerate((("TF-5k","#245c91","o"),("TF-54k","#a47736","s"))):
                vals=all_metrics.loc[all_metrics.target.eq(t)&all_metrics.model.eq(model)&all_metrics.split.eq(p)].sort_values("seed").loss.to_numpy()
                ax.scatter(j+np.array([-.09,0,.09]),vals,color=color,marker=marker,s=30,zorder=4)
                ax.errorbar([j],[vals.mean()],yerr=[vals.std(ddof=1)],fmt="_",color="black",capsize=4,markersize=20)
            ax.set_xticks([0,1],["5,407","54,005"]);ax.set(title=EN[t]+" / "+p.capitalize(),ylabel="Train-standardised MSE",xlabel="Trainable parameters")
            ax.grid(axis="y",alpha=.15)
    fig.suptitle("Transformer width scaling: frozen data, windows and optimiser\nPoints left to right: seeds 17 / 29 / 43; black interval: mean ± seed SD (not CI)",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("size_comparison."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    old_runs=pd.read_csv(ROOT/"reference/results/training_runs.csv");configs=json.loads((ROOT/"CONFIGS_FROZEN.json").read_text())
    ref=json.loads((ROOT/"REFERENCE.json").read_text());z=zipfile.ZipFile(ROOT/"reference"/ref["archive"])
    fig,axes=plt.subplots(3,2,figsize=(13,10),layout="constrained")
    for i,t in enumerate(TARGETS):
        c=configs[t]
        small=old_runs.loc[old_runs.target.eq(t)&old_runs.family.eq("Transformer")&old_runs.lookback.eq(c["lookback"])&old_runs.lr.eq(c["lr"])]
        for k,group in enumerate((small,runs.loc[runs.target.eq(t)])):
            r=next(group.sort_values("best_validation_loss").iloc[[1]].itertuples());ax=axes[i,k]
            h=pd.read_csv(io.BytesIO(z.read(r.step_log.replace("\\","/")))) if k==0 else histories[r.run]
            for p,color in zip(PARTS,("#245c91","#bb7625","#38844d")):
                ax.plot(h.global_step,h[p+"_eval_loss"],lw=.85,color=color,label=p)
            ax.axvline(r.best_step,color="black",ls=":",lw=.8,label="Val checkpoint")
            ax.set(title=f"{EN[t]} / {5407 if k==0 else 54005:,} parameters; seed {r.seed}\nL={r.lookback}; selected step {r.best_step}",xlabel="Optimiser step",ylabel="Train-standardised MSE")
            ax.grid(alpha=.15)
    z.close();handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False)
    fig.suptitle("Full train / validation / test evaluation after every step\nMedian-validation seed shown for each budget; no smoothing",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("step_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def report(summary,changes,audit,runs):
    def row(t,m,p):return summary.loc[summary.target.eq(t)&summary.model.eq(m)&summary.split.eq(p)].iloc[0]
    def cell(r):return f"{r.loss_mean:.6f} ± {r.loss_sd:.6f}"
    lines=["# Transformer 扩至约10倍参数：固定配置的三种子比较","",
        "本轮只扩大模型宽度：5,407 → 54,005参数（9.988倍）。单层编码器、3个注意力头保持不变，隐藏维度24 → 72、前馈层54 → 220；固定相对滞后正弦位置编码、pre-LayerNorm、GELU、dropout0.1和最后token的persistence residual输出均沿用。","",
        "固定配置下，供给平均test loss变化+0.15%，需求−1.14%，电价+0.99%；没有出现普遍的测试收益。供给种子波动增加，需求及电价种子波动缩小。保留小模型作为默认候选更有依据，当前不因更低val loss直接把电价模型替换成大模型。","",
        "供给和需求仍输入7天，电价输入182天；三个目标分别训练，均为次日预测，学习率均为0.001。窗口和学习率来自上一轮小模型的val选择，本轮不重新搜索。seeds为17、29、43，共9次新训练；小模型、RNN和LSTM对照从上一轮已核验的不可变release读取，不重新筛选。","",
        "## 固定数据和训练过程","",
        "Train目标2022-01-01—2024-12-31，共1096；val目标2025-01-01—2025-08-31，共243；test目标2025-09-01—2026-08-31，共365。2021年只提供历史。输入仍是三条已观察的标准化供给/需求/电价和5个日历特征，共8维；三个模型之间无参数共享。冻结修复数据、目标日期和仅train拟合的scaler均与旧release逐字节/哈希核对一致。","",
        "Transformer在RTX5090 Laptop GPU上以float32/math SDPA运行，AMP/TF32关闭，确定性算法开启。AdamW、weight decay0.0001、clip norm1、batch64，每epoch18step，最多120epoch；连续15个完整epoch无val改善则停止，改善阈值0.00001。每次更新后完整评估train/val/test并即时记录，仅val选checkpoint/早停。所有这些训练算术代码与上一轮完全一致，只改参数量校验常数。","",
        "Loss是每个样本平均的标准化MSE，三个分区均除以同一个train标准差的平方。±为三个种子的样本标准差，不是置信区间；下表来自各seed自己的val最优checkpoint，不是三模型集成。","",
        "## Train / Val / Test及种子波动","",
        "|目标|模型|参数量|窗口/天|Train loss|Val loss|Test loss|","|---|---|---:|---:|---:|---:|---:|"]
    for t in TARGETS:
        for m,count in (("RNN",5373),("LSTM",5409),("TF-5k",5407),("TF-54k",54005)):
            rr=row(t,m,"test")
            lines.append(f"|{ZH[t]}|{m}|{count:,}|{int(rr.lookback)}|{cell(row(t,m,'train'))}|{cell(row(t,m,'validation'))}|{cell(rr)}|")
    lines.extend(["","![全部分区的三种子比较](figures/size_comparison.png)","","## 扩大模型相对小Transformer的变化","",
        "负百分比表示大模型更好，均值变化为100×(大模型三个seed的平均MSE/小模型平均MSE−1)。相同seed仅是实验标识，网络维度变化后初始化及dropout随机数消费不同，不构成相同随机扰动或独立数据重采样。","",
        "|目标|分区|平均MSE变化|Seed17|Seed29|Seed43|大模型更好次数|","|---|---|---:|---:|---:|---:|---:|"])
    for r in changes.itertuples():
        lines.append(f"|{ZH[r.target]}|{r.split}|{r.mean_loss_change_pct:+.2f}%|{r.seed17_change_pct:+.2f}%|{r.seed29_change_pct:+.2f}%|{r.seed43_change_pct:+.2f}%|{r.large_better_seeds}/3|")
    lines.extend(["","## 训练轨迹","","![逐step完整评估](figures/step_losses.png)","",
        "每种参数预算展示val误差居中的seed，没有按test挑图，曲线不平滑。每个seed的完整轨迹见step_logs及results/ALL_STEP_LOSSES.csv；旧模型日志包含在reference中的原始release。训练末尾相对val最优点的三集变化见OVERFIT_DIAGNOSTICS.csv。最佳点后train下降而val上升，说明继续拟合训练集没有对应的验证收益；不能仅凭两个年份上的loss差值全部归因于过拟合，年份分布也不同。","",
        "## 结果判断","",
        *[f"{ZH[t]}：扩大后的平均test MSE相对小Transformer变化{changes.loc[changes.target.eq(t)&changes.split.eq('test')].iloc[0].mean_loss_change_pct:+.2f}%，三个对应seed中有{int(changes.loc[changes.target.eq(t)&changes.split.eq('test')].iloc[0].large_better_seeds)}次更好。test种子标准差由{row(t,'TF-5k','test').loss_sd:.6f}变为{row(t,'TF-54k','test').loss_sd:.6f}。" for t in TARGETS],"",
        "电价的三种子平均train loss下降25.82%、val loss下降6.44%，但test loss增加0.99%。三个seed的val均改善，test却仅一个改善；因此验证集上的进步没有在这一测试年份上延续。这个现象与训练期之外的泛化受限相容，但不能单独区分训练过拟合、验证选择影响和年份分布变化。","",
        "供给/需求在各自val最优checkpoint处的train平均loss几乎未变；checkpoint出现时刻不同，早停会使模型尚未达到最低train loss就被选中，不能从所选点的train loss断言模型容量没有增加或训练失效。9次新训练继续到末尾时train均下降、val均上升，早停仍有作用。","",
        "本轮回答的是固定窗口、学习率和训练预算下扩宽模型的效果，不代表大模型重新调参后的最好能力。三个seed只衡量训练随机性；test已被此前多轮监测，不是新的盲测。数据修复的历史发布版本未审计，未增加外部特征、未运行MPC、未上传或修改正式报告。","",
        "## 核验与复现","",
        f"9次新拟合、{audit['optimizer_steps']:,}次权重更新；含step0共{audit['evaluation_rows']:,}行完整三集评估。冻结旧release全部文件、数据/划分/scaler、模型宽度差异和未变训练代码、逐step样本覆盖、val选点与早停、9个checkpoint重放、原始单位预测及MSE/MAE/RMSE独立复算全部通过。最大标准化预测重放差{audit['max_normalised_replay_prediction_difference']:.3g}，预测复算loss与日志最大差{audit['max_prediction_loss_vs_log_difference']:.3g}。","",
        "- results/SUMMARY.csv：四类候选的各分区均值和种子标准差。","- results/LARGE_VS_SMALL.csv：逐种子/均值变化及三种子范围。","- results/ALL_METRICS.csv、training_runs.csv、ALL_STEP_LOSSES.csv：新模型全部指标和逐step日志。","- checkpoints/、predictions/：9个val最优权重及三分区原始单位预测。","- CONFIGS_FROZEN.json、PROTOCOL.json、PREFLIGHT.json、REFERENCE.json：固定配置、训练协议及GPU和引用核验。","",
        "新环境安装requirements.txt后，依次运行python preflight.py、python run.py、python analyse.py。代码默认CUDAGPU；包内reference已包含冻结原release，无需访问远程仓库。bootstrap.py是一次性的本地来源准备记录，不是正常复现的必要步骤。"])
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    configure("cuda");result=json.loads((R/"RESULTS.json").read_text())
    f,x,data,mean,scale=dataset.prepare(False)
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"ALL_METRICS.csv")
    histories,record=audit(result,runs,metrics,data,x,mean,scale)
    combined,summary,changes=summarise(metrics)
    plot(combined,runs,histories);report(summary,changes,record,runs)
    print("SUMMARY",summary[["target","model","split","loss_mean","loss_sd"]].to_string(index=False))
    print("CHANGE",changes.to_string(index=False));print("AUDIT",json.dumps(record))


if __name__=="__main__":main()
