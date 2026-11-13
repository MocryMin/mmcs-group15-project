"""Audit all fits and compare three-seed forecasts without test-driven selection."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import data as dataset
from model import Predictor,TARGETS
from fit_core import configure,COUNTS,dump,sha,tensors,normalised_prediction,score,eval_batch_for

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
PARTS=("train","validation","test")
SEEDS=[17,29,43]
ZH={"generation_MW":"供给","demand_MW":"需求","price_GBP_MWh":"电价"}
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
COLORS={"train":"#245c91","validation":"#bb7625","test":"#38844d"}


def identify_confirmation(result,runs):
    keep=runs.family.ne("Transformer")
    for target,c in result["selection"].items():
        keep |= runs.target.eq(target)&runs.family.eq("Transformer")&runs.lookback.eq(c["lookback"])&runs.lr.eq(c["lr"])
    chosen=runs.loc[keep].copy()
    assert len(chosen)==27 and chosen.groupby(["target","family"]).size().eq(3).all()
    return chosen


def audit_all(result,f,x,data,mean,scale,runs,metrics,histories):
    protocol=result["protocol"];configs=json.loads((ROOT/"BASELINE_CONFIGS.json").read_text())
    expected={(t,"Transformer",l,lr,17) for t in TARGETS for l in dataset.LOOKBACKS for lr in [.001,.003]}
    expected|={(t,"Transformer",c["lookback"],c["lr"],seed) for t,c in result["selection"].items() for seed in (29,43)}
    expected|={(t,m,c["lookback"],c["lr"],seed) for key,c in configs.items() for t,m in [(c["target"],c["family"])] for seed in SEEDS}
    observed=set(zip(runs.target,runs.family,runs.lookback,runs.lr,runs.seed))
    refs=json.loads((ROOT/"REFERENCE_MANIFEST.json").read_text())
    scalers=json.loads((ROOT/"reference_plain/scalers.json").read_text())
    split=pd.read_csv(ROOT/"splits.csv",parse_dates=["target_date","origin","history_start_365"])
    dates={p:set(split.loc[split.split.eq(p),"target_date"]) for p in PARTS}
    screen=runs.loc[runs.family.eq("Transformer")&runs.seed.eq(17)]
    recovery=json.loads((ROOT/"METADATA_RECOVERY.json").read_text())
    original=(ROOT/"fit_core_initial_metadata.txt").read_text(encoding="utf-8")
    checks={"66_unique_fits":len(runs)==66 and observed==expected,
        "198_complete_case_split_metrics":len(metrics)==198 and metrics.groupby(["target","family","lookback","lr","seed"]).size().eq(3).all(),
        "42_single_seed_screen":len(screen)==42,
        "frozen_sources":all(sha(ROOT/n)==v for n,v in protocol["source_hashes"].items()),
        "frozen_reference_files":all(sha(ROOT/n)==v for n,v in refs.items()),
        "frozen_input":sha(ROOT/"inputs/model_daily.csv")==protocol["input_sha256"],
        "same_train_only_scalers":np.array_equal(mean,scalers["mean"]) and np.array_equal(scale,scalers["std"]),
        "split_dates_disjoint":all(not dates[a]&dates[b] for a,b in (("train","validation"),("train","test"),("validation","test"))),
        "next_day_only":((split.target_date-split.origin).dt.days==1).all(),
        "sample_counts":{p:len(d["origins"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365},
        "pre2022_history_not_labels":split.target_date.min()==pd.Timestamp("2022-01-01") and split.history_start_365.min()==pd.Timestamp("2021-01-01"),
        "no_post_august2026_targets":split.target_date.max()==pd.Timestamp("2026-08-31"),
        "validation_only_screen_selection":all(c["screen_run"]==screen.loc[screen.target.eq(t)].sort_values(["best_validation_loss","lookback","lr"]).iloc[0].run for t,c in result["selection"].items()),
        "metadata_recovery_numeric_training_unchanged":recovery["all_passed"] and original.replace('"device":device,"torch":torch.__version__,','"device":device,"torch":str(torch.__version__),')==(ROOT/"fit_core.py").read_text(encoding="utf-8"),
        "cuda_and_parameter_preflight":json.loads((ROOT/"PREFLIGHT_BENCHMARK.json").read_text())["all_passed"]}
    complete=layout=selection=stopping=initial=parameters=full_predictions=signatures=True
    recovered_weights_ok=True
    recovered_hashes={r["run"]:r["state_sha256_before_after"] for r in recovery["fits"]}
    max_prediction_diff=max_loss_diff=max_native_log_diff=0.
    confirmation=identify_confirmation(result,runs)
    cross_backend=[]
    for row in runs.itertuples():
        h=histories[row.run]
        complete &= len(h)==row.steps+1 and np.array_equal(h.global_step,np.arange(row.steps+1))
        complete &= np.isfinite(h[[p+"_eval_loss" for p in PARTS]].to_numpy()).all()
        layout &= row.steps==18*row.epochs and np.array_equal(h.iloc[1:].batch_size_actual,np.tile([64]*17+[8],row.epochs))
        layout &= np.array_equal(h.iloc[1:].batch_index,np.tile(np.arange(1,19),row.epochs))
        layout &= np.array_equal(h.iloc[1:].epoch,np.repeat(np.arange(1,row.epochs+1),18))
        seen=np.repeat(np.arange(row.epochs)*1096,18)+np.tile(np.cumsum([64]*17+[8]),row.epochs)
        layout &= np.array_equal(h.iloc[1:].samples_seen,seen)
        best=float("inf");beststep=bestepoch=0
        for z in h.itertuples():
            improved=z.validation_eval_loss<best-1e-5
            selection &= bool(z.checkpoint_improved)==improved
            if improved:best=z.validation_eval_loss;beststep=z.global_step;bestepoch=z.epoch
            selection &= np.isclose(z.best_validation_so_far,best,atol=1e-12,rtol=0)
        selection &= beststep==row.best_step and bestepoch==row.best_epoch
        stopping &= row.epochs==120 or row.epochs-bestepoch==15
        at=h.loc[h.global_step.eq(row.best_step)].iloc[0]
        cp=torch.load(ROOT/row.checkpoint.replace("\\","/"),weights_only=True)
        if row.run in recovered_hashes:
            digest=hashlib.sha256()
            for key,value in sorted(cp["state_dict"].items()):
                digest.update(key.encode());digest.update(str(value.dtype).encode());digest.update(str(tuple(value.shape)).encode());digest.update(value.contiguous().cpu().numpy().tobytes())
            recovered_weights_ok &= digest.hexdigest()==recovered_hashes[row.run]
        device=row.device if row.device!="cuda" or torch.cuda.is_available() else "cpu"
        j=TARGETS.index(row.target);model=Predictor(row.family,j).to(device);model.load_state_dict(cp["state_dict"])
        parameters &= sum(p.numel() for p in model.parameters())==COUNTS[row.family]==row.parameters==cp["parameters"]
        parameters &= row.eval_batch==eval_batch_for(row.family,row.lookback) and cp["target_index"]==j
        parameters &= isinstance(cp["torch"],str) and type(cp["torch"]) is str
        d=tensors(x,data,j,row.lookback,device)
        with np.load(ROOT/"predictions"/(row.run+".npz")) as exported:
            for part,(xx,yy) in d.items():
                prediction=normalised_prediction(model,xx,row.eval_batch).cpu().numpy().ravel().astype(float)*scale[j]+mean[j]
                saved=exported[part];full_predictions &= len(saved)==len(data[part]["origins"])
                max_prediction_diff=max(max_prediction_diff,float(np.max(np.abs(prediction-saved))/scale[j]))
                calculated=score(saved,data[part]["truth"][:,j],scale[j])
                record=metrics.loc[metrics.target.eq(row.target)&metrics.family.eq(row.family)&metrics.lookback.eq(row.lookback)&metrics.lr.eq(row.lr)&metrics.seed.eq(row.seed)&metrics.split.eq(part)].iloc[0]
                max_loss_diff=max(max_loss_diff,abs(calculated["loss"]-record.loss))
                max_native_log_diff=max(max_native_log_diff,abs(calculated["loss"]-at[part+"_eval_loss"]))
                base=f[TARGETS].to_numpy()[data[part]["origins"],j]
                initial &= np.isclose(h.iloc[0][part+"_eval_loss"],score(base,data[part]["truth"][:,j],scale[j])["loss"],atol=1e-6,rtol=0)
        case=json.loads((ROOT/"case_results"/(row.run+".json")).read_text())
        signatures &= all(sha(ROOT/n)==v for n,v in case["signature"].items() if n!="torch")
        signatures &= case["signature"]["torch"]==str(torch.__version__)
        if row.family=="Transformer" and row.seed==17 and row.run in set(confirmation.run) and device=="cuda":
            xx=d["validation"][0];native=normalised_prediction(model,xx,row.eval_batch).cpu().numpy()
            cpu_model=Predictor(row.family,j);cpu_model.load_state_dict(cp["state_dict"])
            cpu=normalised_prediction(cpu_model,xx.cpu(),row.eval_batch).numpy()
            difference=float(np.max(np.abs(native-cpu)))
            cross_backend.append({"run":row.run,"max_normalised_prediction_difference":difference})
        del model,d
    checks.update(all_steps_full_three_sets=complete,correct_batches_and_samples_seen=layout,validation_only_checkpoints=selection,
        full_epoch_early_stopping=stopping,correct_parameter_counts_and_metadata=parameters,all_predictions_cover_complete_splits=full_predictions,
        initial_persistence=initial,case_signatures_unchanged=signatures,checkpoint_replay=max_prediction_diff<2e-5,
        independent_metric_calculation=max_loss_diff<1e-7,full_log_loss_recalculation=max_native_log_diff<1e-6,
        selected_transformer_cpu_cuda_match=all(r["max_normalised_prediction_difference"]<2e-5 for r in cross_backend))
    checks["recovered_checkpoints_numeric_weights_unchanged"]=recovered_weights_ok
    checks={k:bool(v) for k,v in checks.items()};n=sum(len(h) for h in histories.values())
    audit={"checks":checks,"all_passed":all(checks.values()),"optimizer_steps":int(runs.steps.sum()),"evaluation_rows":n,"full_split_losses":3*n,
        "max_normalised_checkpoint_prediction_difference":max_prediction_diff,"max_independent_loss_difference":max_loss_diff,
        "max_raw_prediction_loss_vs_log_difference":max_native_log_diff,"selected_cpu_cuda_replay":cross_backend,"cross_backend_check_performed":bool(cross_backend),
        "test_is_monitored_not_blind":True,"data_vintage_audited":False}
    dump(R/"AUDIT.json",audit);assert audit["all_passed"],audit
    return audit,confirmation


def summarise(result,runs,metrics,confirmation):
    keys=["target","family","lookback","lr","seed"]
    chosen=metrics.merge(confirmation[keys],on=keys,validate="many_to_one")
    assert len(chosen)==81
    chosen.to_csv(R/"CONFIRMATION_METRICS.csv",index=False)
    rows=[]
    for (target,family,part),g in chosen.groupby(["target","family","split"],sort=False):
        rec={"target":target,"family":family,"split":part,"lookback":int(g.lookback.iloc[0]),"lr":float(g.lr.iloc[0]),"seeds":len(g)}
        for key in ("loss","MSE","RMSE","MAE"):
            rec[key+"_mean"]=float(g[key].mean());rec[key+"_seed_sd"]=float(g[key].std(ddof=1))
        rows.append(rec)
    summary=pd.DataFrame(rows);summary.to_csv(R/"THREE_SEED_SUMMARY.csv",index=False)
    winners={};comparisons=[];paired=[]
    for target in TARGETS:
        available=summary.loc[summary.target.eq(target)&summary.split.eq("validation")&summary.family.isin(["RNN","LSTM"])].sort_values(["loss_mean","family"])
        winner=available.iloc[0].family;winners[target]=winner
        for family in ("RNN","LSTM"):
            deltas=[];tf_values=[];base_values=[]
            for seed in SEEDS:
                tf=chosen.loc[chosen.target.eq(target)&chosen.family.eq("Transformer")&chosen.seed.eq(seed)&chosen.split.eq("test")].iloc[0]
                base=chosen.loc[chosen.target.eq(target)&chosen.family.eq(family)&chosen.seed.eq(seed)&chosen.split.eq("test")].iloc[0]
                delta=100*(tf.loss/base.loss-1);deltas.append(delta);tf_values.append(float(tf.loss));base_values.append(float(base.loss))
                paired.append({"target":target,"baseline_family":family,"seed":seed,"transformer_test_loss":float(tf.loss),"baseline_test_loss":float(base.loss),"test_change_pct":float(delta)})
            base=summary.loc[summary.target.eq(target)&summary.family.eq(family)&summary.split.eq("test")].iloc[0]
            tf=summary.loc[summary.target.eq(target)&summary.family.eq("Transformer")&summary.split.eq("test")].iloc[0]
            comparisons.append({"target":target,"baseline_family":family,"baseline_chosen_by_mean_val":family==winner,
                "transformer_mean_test_loss":float(tf.loss_mean),"baseline_mean_test_loss":float(base.loss_mean),"mean_loss_ratio_change_pct":float(100*(tf.loss_mean/base.loss_mean-1)),
                "paired_delta_mean_pct":float(np.mean(deltas)),"paired_delta_seed_sd_pct":float(np.std(deltas,ddof=1)),
                "seeds_transformer_better":sum(d<0 for d in deltas),"seed17_delta_pct":deltas[0],"seed29_delta_pct":deltas[1],"seed43_delta_pct":deltas[2],
                "transformer_all_runs_better_than_all_baseline_runs":max(tf_values)<min(base_values),
                "transformer_all_runs_worse_than_all_baseline_runs":min(tf_values)>max(base_values),
                "transformer_test_loss_min":min(tf_values),"transformer_test_loss_max":max(tf_values),"baseline_test_loss_min":min(base_values),"baseline_test_loss_max":max(base_values)})
    pd.DataFrame(paired).to_csv(R/"PAIRED_SEED_TEST_COMPARISON.csv",index=False)
    comparisons=pd.DataFrame(comparisons);comparisons.to_csv(R/"TRANSFORMER_VS_RECURRENT.csv",index=False)
    dump(R/"RECURRENT_FAMILY_SELECTED_BY_VALIDATION.json",winners)
    diagnostics=[]
    for (target,family),g in confirmation.groupby(["target","family"],sort=False):
        rec={"target":target,"family":family,"best_step_min":int(g.best_step.min()),"best_step_max":int(g.best_step.max()),
            "stop_epoch_min":int(g.epochs.min()),"stop_epoch_max":int(g.epochs.max())}
        for part,column in (("train","best_train_loss"),("validation","best_validation_loss"),("test","test_loss_at_val_checkpoint")):
            rec["selected_"+part]=float(g[column].mean());rec["final_"+part]=float(g["last_"+part+"_loss"].mean())
        diagnostics.append(rec)
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False)
    return chosen,summary,comparisons,winners


def main():
    configure("cuda" if torch.cuda.is_available() else "cpu")
    result=json.loads((R/"RESULTS.json").read_text());f,x,data,mean,scale=dataset.prepare()
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"ALL_METRICS.csv")
    histories={r.run:pd.read_csv(ROOT/r.step_log.replace("\\","/")) for r in runs.itertuples()}
    pd.concat(histories.values(),ignore_index=True).to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    audit,confirmation=audit_all(result,f,x,data,mean,scale,runs,metrics,histories)
    chosen,summary,comparisons,winners=summarise(result,runs,metrics,confirmation)
    plot_all(result,runs,metrics,confirmation,chosen,summary,comparisons,histories)
    write_report(result,runs,metrics,confirmation,chosen,summary,comparisons,winners,audit)
    (ROOT/"requirements.txt").write_text(f"--extra-index-url https://download.pytorch.org/whl/cu130\ntorch=={torch.__version__}\nnumpy=={np.__version__}\npandas=={pd.__version__}\nmatplotlib=={matplotlib.__version__}\n",encoding="utf-8")
    print("AUDIT",json.dumps(audit),flush=True)
    print(summary[["target","family","split","loss_mean","loss_seed_sd"]].to_string(index=False),flush=True)
    print(comparisons.to_string(index=False),flush=True)


def plot_all(result,runs,metrics,confirmation,chosen,summary,comparisons,histories):
    folder=ROOT/"figures";folder.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    screen=metrics.loc[metrics.family.eq("Transformer")&metrics.seed.eq(17)&metrics.split.eq("validation")]
    fig,axes=plt.subplots(1,2,figsize=(13,4.5),layout="constrained")
    for ax,lr in zip(axes,[.001,.003]):
        values=np.array([[screen.loc[screen.target.eq(t)&screen.lookback.eq(l)&screen.lr.eq(lr)].iloc[0].loss for l in dataset.LOOKBACKS] for t in TARGETS])
        ratios=values/np.array([screen.loc[screen.target.eq(t),"loss"].min() for t in TARGETS])[:,None]
        vmax=max(1.05,float(ratios.max()));im=ax.imshow(ratios,cmap="Greys",vmin=1.,vmax=vmax,aspect="auto")
        for i,t in enumerate(TARGETS):
            c=result["selection"][t]
            for j,l in enumerate(dataset.LOOKBACKS):
                ax.text(j,i,f"{values[i,j]:.5f}",ha="center",va="center",color="white" if (ratios[i,j]-1)/(vmax-1)>.55 else "black",fontsize=9)
                if c["lookback"]==l and c["lr"]==lr:ax.add_patch(Rectangle((j-.47,i-.45),.94,.9,fill=False,edgecolor="#087caa",lw=2))
        ax.set_xticks(np.arange(7),labels=[str(v) for v in dataset.LOOKBACKS]);ax.set_yticks(np.arange(3),labels=[EN[t] for t in TARGETS])
        ax.set(title=f"Learning rate {lr:g}",xlabel="History length (days)");ax.tick_params(length=0)
        fig.colorbar(im,ax=ax,shrink=.8,label="Val MSE / target minimum")
    fig.suptitle("Transformer screening: seed 17; 42 configurations\nCell: validation MSE; outline: configuration frozen before seeds 29 and 43",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("screening_grid."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(11.8,10),layout="constrained")
    families=["RNN","LSTM","Transformer"]
    markers=["o","s","^"]
    colours=["#245c91","#a47736","#367a55"]
    for i,t in enumerate(TARGETS):
        for k,part in enumerate(("validation","test")):
            ax=axes[i,k]
            for j,(m,marker,color) in enumerate(zip(families,markers,colours)):
                g=chosen.loc[chosen.target.eq(t)&chosen.family.eq(m)&chosen.split.eq(part)].sort_values("seed")
                vals=g.loss.to_numpy();ax.scatter(np.array([j-.09,j,j+.09]),vals,color=color,marker=marker,s=28,label=m,zorder=4)
                ax.errorbar([j],[vals.mean()],yerr=[vals.std(ddof=1)],fmt="_",color="black",capsize=5,markersize=22,lw=1.2,zorder=5)
            ax.set_xticks(np.arange(3),families);ax.set(title=f"{EN[t]} / {part.capitalize()}",ylabel="Train-standardised MSE")
            ax.grid(axis="y",alpha=.15)
    fig.suptitle("Three-seed confirmation of frozen configurations\nThree symbols per model: seeds 17 / 29 / 43; black interval: mean ± sample SD",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("three_seed_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(15.5,11),layout="constrained")
    simple=pd.read_csv(R/"SIMPLE_BASELINES.csv")
    for i,t in enumerate(TARGETS):
        for j,m in enumerate(families):
            group=confirmation.loc[confirmation.target.eq(t)&confirmation.family.eq(m)].sort_values("best_validation_loss")
            row=next(group.iloc[[1]].itertuples());h=histories[row.run];ax=axes[i,j]
            for part in PARTS:
                b=simple.loc[simple.target.eq(t)&simple.family.eq("Persistence")&simple.split.eq(part)].iloc[0].loss
                ax.plot(h.global_step,h[part+"_eval_loss"]/b,color=COLORS[part],lw=.9,label=part)
            valbase=simple.loc[simple.target.eq(t)&simple.family.eq("Persistence")&simple.split.eq("validation")].iloc[0].loss
            ax.scatter([row.best_step],[row.best_validation_loss/valbase],color="black",s=20,zorder=4,label="Val checkpoint")
            ax.axvline(row.best_step,color="#555555",ls=":",lw=.7,alpha=.5)
            ax.axhline(1.,color="#777777",ls="--",lw=.8,label="Copy-today")
            ax.set(title=f"{EN[t]} / {m}, L={row.lookback}\nseed {row.seed}, selected step {row.best_step}",xlabel="Optimiser step",ylabel="MSE / own-split persistence")
            ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=5,frameon=False,fontsize=9)
    fig.suptitle("Every-step full train / validation / test losses\nOne median-validation seed per frozen configuration; no smoothing",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("selected_step_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13.6,4.6),layout="constrained")
    for ax,t in zip(axes,TARGETS):
        g=comparisons.loc[comparisons.target.eq(t)]
        for j,row in enumerate(g.itertuples()):
            vals=[row.seed17_delta_pct,row.seed29_delta_pct,row.seed43_delta_pct]
            ax.scatter([j-.09,j,j+.09],vals,color="#245c91",s=30,zorder=3)
            ax.axhline(0,color="#777777",lw=.8)
            ax.errorbar([j],[np.mean(vals)],yerr=[np.std(vals,ddof=1)],fmt="_",color="black",capsize=5,markersize=20)
        ax.set_xticks([0,1],["vs "+v for v in g.baseline_family]);ax.set(title=EN[t],ylabel="Test MSE change (%)\nNegative favours Transformer")
        ax.grid(axis="y",alpha=.15)
    fig.suptitle("Transformer test differences by random seed\nIdentical data; configurations chosen with validation only; intervals are seed SD, not confidence intervals",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("paired_seed_differences."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def write_report(result,runs,metrics,confirmation,chosen,summary,comparisons,winners,audit):
    def row(t,m,p):return summary.loc[summary.target.eq(t)&summary.family.eq(m)&summary.split.eq(p)].iloc[0]
    def cell(r,field="loss"):return f"{r[field+'_mean']:.6f} ± {r[field+'_seed_sd']:.6f}"
    simple=pd.read_csv(R/"SIMPLE_BASELINES.csv")
    lines=["# 约 5.4k 参数 Transformer：次日预测与三种子复核","",
        "本轮使用小型 Transformer 编码器预测次日供给、需求或电价，每个目标单独训练。重点是将架构变化与训练随机性分开观察：先用 seed 17 初筛七个窗口、两个学习率，再固定每个目标的配置，补齐 seeds 29、43。普通 RNN/LSTM 的原候选配置也在本轮软件环境重新训练三个种子。","",
        "完成日期：2026-11-10；实验目录中的20261109保留启动日期。","",
        "## 结果判断","",
        "同等参数预算下，没有出现三个目标普遍明显优于循环模型的结果。供给和需求的Transformer平均test MSE相对LSTM分别降低1.71%、2.17%，但三种子的误差范围均与LSTM重叠。供给三次对应seed都改善，其中两次仅约0.4%；需求两次改善、一次略差。因此这两项属于小幅改善的候选证据，不能仅凭均值称为稳定的明显优势。","",
        "电价Transformer相对LSTM的平均test MSE降低8.99%，但相对RNN增加4.70%，三个对应seed中只有一个优于RNN。Transformer电价的seed标准差为0.003749，RNN为0.001095；其较低val误差没有转化为本段test中最好的平均表现。应保留RNN这个更强的电价对照，而不是只报告相对LSTM的提升。","",
        "供给相对RNN的改善较一致：平均test MSE降低4.93%，且三个Transformer结果均低于三个RNN结果。不过，较强的LSTM已经缩小了这个差距。整体上，Transformer值得保留为供给/需求候选，但本轮不足以支持把全部预测器统一替换为Transformer。上一轮注意力只测一个seed，不能由本轮直接断定其提升全部来自噪声。","",
        "## 网络结构与参数预算","",
        "每个历史日有 8 个特征：三条标准化历史序列，以及星期/年内相位的正余弦和周末标志。输入先投影到 24 维，再加固定正弦位置编码，经过一层 Transformer encoder，最后一个 token 接线性头预测次日相对当日的变化。","",
        "| 部件 | 配置 | 可训练参数 |","|---|---|---:|",
        "| 输入投影 | 8 → 24 | 216 |",
        "| 多头自注意力 | 3 heads，每 head 8 维 | 2,400 |",
        "| 前馈网络 | 24 → 54 → 24，GELU | 2,670 |",
        "| 两个 LayerNorm | pre-LayerNorm | 96 |",
        "| 输出头 | 24 → 1 | 25 |",
        "| 固定位置编码 | 按相对滞后天数编码 | 0 |",
        "| 合计 | 一层编码器 | **5,407** |","",
        "同轮普通 RNN 为 5,373 参数，LSTM 为 5,409 参数。Transformer 没有预训练、没有可学习的 365×24 位置嵌入，也没有新增输入信息。各模型输出头初始化为零，因此 step 0 都等于照抄今天。","",
        "相对位置零始终对应最后已知日，不随窗口长度改变。窗口内的 token 全部是预测时已知的历史，允许它们相互做双向自注意力；次日目标没有放入窗口。设标准化目标为 $z_t$、最后 token 输出为 $h_t$，预测为 $\\widehat z_{t+1}=z_t+w^\\top h_t+b$。",
        "",
        "编码器按 [PyTorch TransformerEncoderLayer 官方结构](https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html) 实现；上述参数数由实际模型逐项统计。","",
        "## 数据与选择过程","",
        "| 分区 | 预测目标日期 | 样本数 |","|---|---|---:|",
        "| Train | 2022-01-01—2024-12-31 | 1,096 |",
        "| Val | 2025-01-01—2025-08-31 | 243 |",
        "| Test | 2025-09-01—2026-08-31 | 365 |","",
        "使用冻结的修复数据：总供给为课程总发电加独立风场，单位为日均 MW；电价为名义 £/MWh。2021 年只提供历史输入，所有窗口共享相同目标日期；均值和标准差只由 2022–2024 年拟合。保留原来三序列加日历的输入，没有加入天气、燃料、外部预测或其他新特征。","",
        "Transformer 初筛窗口为 365、182、91、56、30、14、7 天，学习率为 0.001、0.003。每个目标有 14 个 seed17 配置，共 42 次拟合。仅按该目标最佳 val MSE 选窗口/学习率，选择文件先冻结，再从零训练选定配置的 seeds29、43；这六次补充训练与原 seed17 共形成九个确认模型。","",
        "RNN/LSTM 不在本轮重新搜索窗口或学习率，使用上一轮已按 val 选出的六组配置，每组三个种子，共十八次新拟合。因此，本轮 Transformer 搜索预算与固定的循环模型对照不同，结果比较的是这些实际候选，不单独证明架构优劣。全部唯一拟合为 42 + 6 + 18 = 66 次。","",
        "每个 seed 的 checkpoint 仍只按 val 选择；test 不用于选择窗口、学习率、checkpoint 或停止时刻。Test 已在前几轮反复监测，不是新的盲测。三种子主要检验训练随机性，不覆盖未来年份和数据来源的不确定性。","",
        "## 训练与硬件","",
        "所有模型统一使用本轮 PyTorch 2.14.1+cu130 环境，避免将旧 CPU 版与新 GPU 版的差异混入直接对照。Transformer 在 RTX 5090 Laptop GPU 上训练，RNN/LSTM 三目标在 CPU 独立进程中并行，每进程两线程。模型均为 float32，关闭 AMP、TF32，使用确定性算法；Transformer 用 math SDPA。","",
        "AdamW、weight decay 0.0001、梯度范数截断 1、dropout 0.1；batch size64，每 epoch18 step（17×64+8），最多120 epoch、连续15个完整 epoch 无新 val 改善则停止。没有 warmup 或学习率调度。checkpoint 可在任意 step 保存，改善阈值为0.00001。","",
        "每次更新后完整评估 train、val、test，关闭 dropout，逐行刷新日志。长窗口评估分块以控制显存，短窗口使用较大块降低调用开销；所有样本都计入均值，不是抽样。Transformer 的分块上限随 $L^{-2}$ 调整，范围64–2048；训练 batch 始终64。","",
        "初始测量一年窗口的一次更新加完整三集评估：CPU约2.67秒、GPU约0.11秒；重复测量约2.35/0.16秒。测量受到当时其他GPU负载影响，详见两份 PREFLIGHT_BENCHMARK 文件。GPU进程内存上限设为总显存25%，这不是预先占满该显存。短序列的循环模型在CPU上的吞吐也有竞争力。","",
        "初始导出曾将版本号保存为 TorchVersion 对象，安全读取因此报错。只修改了将版本号转为普通字符串这一项元数据；四次已完成训练由完整日志和checkpoint恢复，数值权重哈希及对应 loss 均验证不变，没有重训或更改选择。原错误日志和 METADATA_RECOVERY.json 保留。","",
        "## Transformer 初筛结果","",
        "以下配置只由 seed17 的 val 决定，不用 test 排序。","",
        "| 目标 | 窗口/天 | 学习率 | 初筛最佳 Val loss |","|---|---:|---:|---:|"]
    for t,c in result["selection"].items():lines.append(f"| {ZH[t]} | {c['lookback']} | {c['lr']:g} | {c['best_validation_loss']:.6f} |")
    lines += ["","![七窗口两学习率初筛](figures/screening_grid.png)","",
        "## 三种子 Train / Val / Test loss","",
        "Loss 为相应目标的每样本平均标准化 MSE。± 是三个随机种子的样本标准差，不是置信区间；结果来自各 seed 自己的 val 最优 checkpoint，不是模型集成。每个窗口没有都训练三个种子，三种子复核仅针对冻结配置。","",
        "| 目标 | 模型 | 窗口/天 | 学习率 | Train loss | Val loss | Test loss |","|---|---|---:|---:|---:|---:|---:|"]
    for t in TARGETS:
        for m in ("RNN","LSTM","Transformer"):
            a,b,c=(row(t,m,p) for p in PARTS)
            lines.append(f"| {ZH[t]} | {m} | {a.lookback} | {a.lr:g} | {cell(a)} | {cell(b)} | {cell(c)} |")
    lines += ["","![三个种子的误差分布](figures/three_seed_losses.png)","",
        "每组从左到右为 seeds17、29、43，黑线为均值±样本标准差。小幅均值变化应与这些重复结果共同判断，不用最好的一次代表整个模型。","",
        "## 相对 RNN/LSTM 的逐种子 Test 变化","",
        "百分比为100×（Transformer test MSE / 对照test MSE − 1），负值有利于Transformer。均值比的变化和三个种子的百分比均值不一定相同，表中分别列出。对应seed只是重复实验的标识，不构成三次独立数据重采样。","",
        "| 目标 | 对照 | 平均MSE比变化 | Seed17 | Seed29 | Seed43 | Transformer较好次数 |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for c in comparisons.itertuples():
        lines.append(f"| {ZH[c.target]} | {c.baseline_family} | {c.mean_loss_ratio_change_pct:+.2f}% | {c.seed17_delta_pct:+.2f}% | {c.seed29_delta_pct:+.2f}% | {c.seed43_delta_pct:+.2f}% | {c.seeds_transformer_better}/3 |")
    lines += ["","![逐种子差异](figures/paired_seed_differences.png)","",
        "若需要用一个循环模型作参照，仅依据三种子平均 val 选择，其结果为："+"；".join(ZH[t]+"="+m for t,m in winners.items())+"。表格仍完整保留对另一个家族的结果，不用 test 挑一个更弱的对照。","",
        "## 简单基准与原始单位","",
        "Persistence 为明天照抄今天，Seasonal7 为明天照抄上周同一天。两者在同一目标日期上计算。供给和需求 RMSE/MAE 单位为MW，电价为£/MWh。","",
        "| 目标 | 方法 | Test标准化MSE | Test RMSE | Test MAE |","|---|---|---:|---:|---:|"]
    for t in TARGETS:
        for name in ("Persistence","Seasonal7"):
            c=simple.loc[simple.target.eq(t)&simple.family.eq(name)&simple.split.eq("test")].iloc[0]
            lines.append(f"| {ZH[t]} | {name} | {c.loss:.6f} | {c.RMSE:,.3f} | {c.MAE:,.3f} |")
        for m in ("RNN","LSTM","Transformer"):
            c=row(t,m,"test")
            lines.append(f"| {ZH[t]} | {m} | {cell(c)} | {c.RMSE_mean:,.3f} ± {c.RMSE_seed_sd:,.3f} | {c.MAE_mean:,.3f} ± {c.MAE_seed_sd:,.3f} |")
    lines += ["","## 训练轨迹与边界","",
        "![完整逐step轨迹](figures/selected_step_losses.png)","",
        "每个模型/目标展示按val排序居中的种子，未按test挑选。各分区loss除以本分区照抄今天的MSE后显示，1是照抄水平；横轴为每次optimizer更新，未平滑。完整三种子和初筛的日志均随包保存。","",
        "三种子复核比单次最优值更能反映训练随机性，但仍然使用同一训练/验证/测试年份，且Transformer配置先由seed17筛选；小差异不应表述为统计显著。是否值得用于最终MPC，还需要在相同资产、信息和运营规则下比较控制收益。本轮没有运行MPC，也没有加入外部特征或修改正式报告。","",
        "## 核验、文件和复现","",
        f"66 次唯一拟合，确认阶段27个模型；累计 {audit['optimizer_steps']:,} 次权重更新，含 step0 共 {audit['evaluation_rows']:,} 行完整评估、{audit['full_split_losses']:,} 个分区loss。源文件/输入/基准哈希、固定划分/训练期scaler、参数量、每step全量覆盖、批次计数、val选点/选窗及早停检查通过。checkpoint重放最大标准化预测差 {audit['max_normalised_checkpoint_prediction_difference']:.3g}，独立loss复算最大差 {audit['max_independent_loss_difference']:.3g}；所选Transformer的CPU/GPU预测也在记录的容差内一致。","",
        "- model.py、fit_core.py、data.py、run.py：模型、统一训练/全量评估、划分和运行协调。",
        "- results/SELECTION_FROZEN.json、CONFIRMATION_METRICS.csv、THREE_SEED_SUMMARY.csv：配置、每个种子和均值/标准差。",
        "- results/TRANSFORMER_VS_RECURRENT.csv、PAIRED_SEED_TEST_COMPARISON.csv：平均与逐seed差值。",
        "- results/ALL_METRICS.csv、ALL_STEP_LOSSES.csv、OVERFIT_DIAGNOSTICS.csv：全部初筛/复核和训练轨迹。",
        "- checkpoints/、predictions/、case_results/：66个最佳val权重、三分区预测和完整案例缓存。",
        "- PREFLIGHT_BENCHMARK*.json、EVALUATION_CHUNK_TIMING.json、PROTOCOL.json、results/AUDIT.json：环境、速度和核验。",
        "- METADATA_RECOVERY.json、execution_logs/、fit_core_initial_metadata.txt：历史元数据修复证据；recover_metadata.py为一次性历史恢复脚本，不用于正常复现。","",
        "安装requirements.txt后，在新副本依次运行 python preflight_benchmark.py、python run.py、python analyse.py。训练默认需要可用CUDA GPU；checkpoint以CPU张量保存，分析脚本在无GPU时也可用CPU重放。完整数据随包提供，原CPU实验未改写。修复历史的逐日发布版本仍未审计；test已多轮监测，不是新的盲测。","",
        "本轮只通过匿名隔离Playwright MCP核对了官方PyTorch安装索引和编码器文档；未查学校平台或邮箱，未上传小组仓库或提交作业。"]
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
