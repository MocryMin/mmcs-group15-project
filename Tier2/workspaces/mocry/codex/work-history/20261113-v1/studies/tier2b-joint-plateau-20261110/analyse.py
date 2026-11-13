"""Audit every plateau event, replay checkpoints, and select policies by val only."""
from pathlib import Path
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
from model import Predictor,TARGETS,COUNTS
from policy import POLICIES,LR_LEVELS,WD_LEVELS,DROPOUT_LEVELS
from fit_core import configure,tensors,predict,score,dump,sha,PARTS

ROOT=Path(__file__).resolve().parent
R=ROOT/"results"
ZH={"fixed":"固定策略","lr_only":"仅降LR","reg_only":"仅增强正则","combined":"LR＋正则"}
EN={"fixed":"Fixed","lr_only":"LR only","reg_only":"Reg only","combined":"LR + reg"}
COLORS={"train":"#245c91","validation":"#bb7625","test":"#38844d"}


def expected_params(policy,stage):
    return {"learning_rate":LR_LEVELS[stage] if policy in ("lr_only","combined") else LR_LEVELS[0],
        "weight_decay":WD_LEVELS[stage] if policy in ("reg_only","combined") else WD_LEVELS[0],
        "dropout":DROPOUT_LEVELS[stage] if policy in ("reg_only","combined") else DROPOUT_LEVELS[0]}


def audit(result,runs,metrics,x,data,mean,scale):
    p=result["protocol"];ref=json.loads((ROOT/"REFERENCE.json").read_text());archive=ROOT/"reference"/ref["archive"]
    assert sha(archive)==ref["sha256"]
    z=zipfile.ZipFile(archive);manifest=json.loads(z.read("MANIFEST.json"))
    import hashlib
    assert all(hashlib.sha256(z.read(n)).hexdigest()==v["sha256"] for n,v in manifest.items())
    for n in ("model.py","data.py","scalers.json","splits.csv"):assert (ROOT/n).read_bytes()==z.read(n)
    assert sha(ROOT/"inputs/model_daily.csv")==p["input_sha256"]=="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"
    assert all(sha(ROOT/n)==v for n,v in p["source_hashes"].items()) and all(sha(ROOT/n)==v for n,v in p["reference_hashes"].items())
    expected={(f,policy,s) for f in ("RNN","LSTM") for policy in POLICIES for s in (17,29,43)}
    assert len(runs)==24 and set(zip(runs.family,runs.policy,runs.seed))==expected
    assert len(metrics)==288 and metrics.groupby(["family","policy","seed","split"]).size().eq(4).all()
    histories={};max_prediction=0.;max_score=0.;max_log=0.;events_rows=[];diagnostics=[];cpu_cuda=[]
    for r in runs.itertuples():
        assert r.lookback==p["configs"][r.family]["lookback"] and r.parameters==COUNTS[r.family]["large"] and r.device=="cuda"
        cache=json.loads((ROOT/"case_results"/(r.run+".json")).read_text())
        assert all(cache["signature"][n]==sha(ROOT/n) for n in ("model.py","fit_core.py","policy.py","data.py","inputs/model_daily.csv","CONFIGS_FROZEN.json"))
        cp=torch.load(ROOT/r.checkpoint.replace("\\","/"),weights_only=True)
        assert cp["policy"]==r.policy and cp["seed"]==r.seed and cp["parameters"]==r.parameters and cp["targets"]==TARGETS
        assert np.array_equal(cp["mean"],mean) and np.array_equal(cp["std"],scale)
        h=pd.read_csv(ROOT/r.step_log.replace("\\","/"));histories[r.run]=h
        assert np.array_equal(h.global_step,np.arange(r.steps+1)) and r.steps==r.epochs*18
        best=float("inf");chosen=0
        for line in h.itertuples():
            improved=line.validation_eval_loss<best-1e-5;assert bool(line.checkpoint_improved)==improved
            if improved:best=line.validation_eval_loss;chosen=line.global_step
            assert abs(line.best_validation_so_far-best)<1e-12
            if line.global_step:
                assert line.epoch==(line.global_step-1)//18+1 and line.batch_index==(line.global_step-1)%18+1
                assert line.batch_size_actual==(8 if line.batch_index==18 else 64)
                assert line.samples_seen==(line.epoch-1)*1096+min(64*line.batch_index,1096)
        assert chosen==r.best_step==cp["best_step"] and cp["stage"]==r.best_stage
        stage=0;plateau=0;early=0;events=json.loads((ROOT/"events"/(r.run+".json")).read_text());event_index=0
        for epoch,g in h.groupby("epoch",sort=True):
            params=expected_params(r.policy,stage)
            assert g.stage.eq(stage).all()
            for name,value in params.items():assert np.allclose(g[name],value,rtol=0,atol=1e-15)
            assert np.allclose(g.lr_times_wd,g.learning_rate*g.weight_decay,atol=1e-18)
            if epoch==0:continue
            assert len(g)==18
            good=bool(g.checkpoint_improved.any());early=0 if good else early+1;plateau=0 if good else plateau+1
            if r.policy!="fixed" and stage<3 and plateau>=5:
                e=events[event_index];event_index+=1
                assert e["epoch"]==epoch and e["global_step"]==epoch*18 and e["from_stage"]==stage and e["to_stage"]==stage+1 and e["no_improvement_complete_epochs"]==5
                assert abs(e["best_joint_validation"]-g.best_validation_so_far.iloc[-1])<1e-12
                before=params;stage+=1;after=expected_params(r.policy,stage)
                for event_name,key in (("lr","learning_rate"),("weight_decay","weight_decay"),("dropout","dropout")):
                    assert e["before"][event_name]==before[key] and e["after"][event_name]==after[key]
                plateau=0;events_rows.append({"run":r.run,"family":r.family,"policy":r.policy,"seed":r.seed,**e})
            assert early<30 or epoch==r.epochs
        assert event_index==len(events)==r.events_count and (r.epochs==120 or early==30)
        for part in PARTS:
            cc=[part+"_"+t+"_loss" for t in TARGETS]
            assert np.isfinite(h[[part+"_eval_loss",*cc]]).all().all()
            assert np.allclose(h[cc].mean(1),h[part+"_eval_loss"],rtol=0,atol=1e-12)
        for k in ("learning_rate","weight_decay","dropout"):assert abs(cp[k]-h.iloc[chosen][k])<1e-15
        model=Predictor(r.family,"large").to("cuda");model.load_state_dict(cp["state_dict"]);model.dropout.p=cp["dropout"]
        dd=tensors(x,data,r.lookback);saved=np.load(ROOT/"predictions"/(r.run+".npz"))
        for part,(xx,yy) in dd.items():
            raw=predict(model,xx).cpu().numpy().astype(float)*scale+mean
            assert raw.shape==saved[part].shape==(len(data[part]["origins"]),3)
            max_prediction=max(max_prediction,float(np.abs((raw-saved[part])/scale).max()))
            for m in score(saved[part],data[part]["truth"],scale):
                sr=metrics.loc[metrics.family.eq(r.family)&metrics.policy.eq(r.policy)&metrics.seed.eq(r.seed)&metrics.split.eq(part)&metrics.target.eq(m["target"])].iloc[0]
                for k in ("loss","MSE","RMSE","MAE"):
                    if k in m:max_score=max(max_score,abs(m[k]-sr[k])/max(1,abs(m[k])))
                col=part+"_eval_loss" if m["target"]=="JOINT" else part+"_"+m["target"]+"_loss"
                max_log=max(max_log,abs(m["loss"]-h.iloc[chosen][col]))
        if r.seed==17:
            xx=dd["test"][0][:8];gpu=predict(model,xx,8).cpu().numpy();model.to("cpu");cpu=predict(model,xx.cpu(),8).numpy()
            diff=float(np.abs(cpu-gpu).max());assert diff<2e-5;cpu_cuda.append({"family":r.family,"policy":r.policy,"max_normalised_difference":diff})
        diagnostics.append({"run":r.run,"family":r.family,"policy":r.policy,"seed":r.seed,"best_stage":r.best_stage,"best_step":r.best_step,
            **{part+"_last_minus_selected":h.iloc[-1][part+"_eval_loss"]-h.iloc[chosen][part+"_eval_loss"] for part in PARTS}})
    losscols=[p+"_eval_loss" for p in PARTS]+[p+"_"+t+"_loss" for p in PARTS for t in TARGETS]+["train_batch_loss"]
    prefixes=[];old_runs=pd.read_csv(io.BytesIO(z.read("results/training_runs.csv")))
    for family in ("RNN","LSTM"):
        for seed in (17,29,43):
            fixed=runs.loc[runs.family.eq(family)&runs.policy.eq("fixed")&runs.seed.eq(seed)].iloc[0];h0=histories[fixed.run]
            old=old_runs.loc[old_runs.family.eq(family)&old_runs.budget.eq("large")&old_runs.seed.eq(seed)].iloc[0]
            ho=pd.read_csv(io.BytesIO(z.read(old.step_log.replace("\\","/"))))
            difference=float(np.nanmax(np.abs(h0.iloc[:len(ho)][losscols].to_numpy()-ho[losscols].to_numpy())))
            assert difference<1e-12;prefixes.append({"family":family,"seed":seed,"comparison":"old15 vs new30 prefix","max_loss_difference":difference})
            for policy in POLICIES[1:]:
                rr=runs.loc[runs.family.eq(family)&runs.policy.eq(policy)&runs.seed.eq(seed)].iloc[0];hh=histories[rr.run]
                events=json.loads((ROOT/"events"/(rr.run+".json")).read_text());end=events[0]["global_step"]+1 if events else len(hh)
                diff=float(np.nanmax(np.abs(h0.iloc[:end][losscols].to_numpy()-hh.iloc[:end][losscols].to_numpy())))
                assert diff<1e-12;prefixes.append({"family":family,"seed":seed,"comparison":policy+" before first intervention","steps":end-1,"max_loss_difference":diff})
    z.close();assert max_prediction<2e-5 and max_score<1e-10 and max_log<3e-8
    pd.concat(histories.values(),ignore_index=True).to_csv(R/"ALL_STEP_LOSSES.csv",index=False)
    pd.DataFrame(diagnostics).to_csv(R/"OVERFIT_DIAGNOSTICS.csv",index=False);dump(R/"PLATEAU_EVENTS.json",events_rows)
    record={"all_passed":True,"fits":24,"policies":4,"seeds":[17,29,43],"reference_manifest_files_verified":len(manifest),"all_events_reconstructed_from_val_only":True,
        "matched_30_epoch_patience":True,"no_schedule_reset_of_early_stop_clock":True,"every_step_full_joint_and_components":True,"checkpoint_parameters_match_log":True,
        "max_normalised_replay_prediction_difference":max_prediction,"max_relative_metric_difference":max_score,"max_metric_vs_logged_loss_difference":max_log,
        "initial_trajectory_comparisons":prefixes,"cpu_cuda_replay":cpu_cuda,"optimizer_updates":int(runs.steps.sum()),"evaluation_rows":sum(len(h) for h in histories.values()),
        "test_is_monitored_not_blind":True,"MPC_evaluated":False}
    dump(R/"AUDIT.json",record);return histories,record


def summarise(metrics):
    rows=[]
    for (f,p,t,split),g in metrics.groupby(["family","policy","target","split"],sort=False):
        assert len(g)==3
        rows.append({"family":f,"policy":p,"target":t,"split":split,"loss_mean":g.loss.mean(),"loss_sd":g.loss.std(ddof=1)})
    summary=pd.DataFrame(rows);summary.to_csv(R/"SUMMARY.csv",index=False);changes=[]
    for (f,p,t,part),g in metrics.loc[metrics.policy.ne("fixed")].groupby(["family","policy","target","split"],sort=False):
        b=metrics.loc[metrics.family.eq(f)&metrics.policy.eq("fixed")&metrics.target.eq(t)&metrics.split.eq(part)].sort_values("seed");g=g.sort_values("seed")
        d=100*(g.loss.to_numpy()/b.loss.to_numpy()-1)
        changes.append({"family":f,"policy":p,"target":t,"split":part,"change_pct":100*(g.loss.mean()/b.loss.mean()-1),"seed17_pct":d[0],"seed29_pct":d[1],"seed43_pct":d[2],"better_seeds":int((d<0).sum())})
    change=pd.DataFrame(changes);change.to_csv(R/"VERSUS_MATCHED_FIXED.csv",index=False)
    selection={}
    for family in ("RNN","LSTM"):
        rr=summary.loc[summary.family.eq(family)&summary.target.eq("JOINT")&summary.split.eq("validation")].sort_values(["loss_mean","policy"]).iloc[0]
        selection[family]={"policy":rr.policy,"mean_joint_validation_loss":rr.loss_mean,"criterion":"Mean joint validation only; test not used"}
    dump(R/"SELECTION_BY_VALIDATION.json",selection);return summary,change,selection


def plot(metrics,runs,histories):
    folder=ROOT/"figures";folder.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout="constrained")
    for i,family in enumerate(("RNN","LSTM")):
        for k,part in enumerate(PARTS):
            ax=axes[i,k]
            for j,policy in enumerate(POLICIES):
                v=metrics.loc[metrics.family.eq(family)&metrics.policy.eq(policy)&metrics.target.eq("JOINT")&metrics.split.eq(part)].sort_values("seed").loss.to_numpy()
                ax.scatter(j+np.array([-.09,0,.09]),v,color="#245c91",s=25,zorder=4);ax.errorbar([j],[v.mean()],yerr=[v.std(ddof=1)],fmt="_",color="black",capsize=4,markersize=18)
            ax.set_xticks(range(4),[EN[v] for v in POLICIES],rotation=15);ax.set(title=family+" / "+part.capitalize(),ylabel="Joint standardised MSE");ax.grid(axis="y",alpha=.15)
    fig.suptitle("Plateau-policy ablation; all four arms share patience30 and max120 epochs\nPoints: seeds17/29/43; black interval: mean ± seed SD (not CI)",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("policy_joint_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(2,4,figsize=(16,8.5),layout="constrained")
    for i,family in enumerate(("RNN","LSTM")):
        for k,policy in enumerate(POLICIES):
            r=next(runs.loc[runs.family.eq(family)&runs.policy.eq(policy)&runs.seed.eq(17)].itertuples());h=histories[r.run];ax=axes[i,k]
            for part,color in COLORS.items():ax.plot(h.global_step,h[part+"_eval_loss"],color=color,lw=.8,label=part)
            events=json.loads((ROOT/"events"/(r.run+".json")).read_text())
            for j,e in enumerate(events):
                ax.axvline(e["global_step"],color="#888888",ls="--",lw=.7,label="Plateau change" if j==0 else None)
                ax.text(e["global_step"],.98,str(e["to_stage"]),transform=ax.get_xaxis_transform(),ha="left",va="top",fontsize=8,color="#555555")
            ax.axvline(r.best_step,color="black",ls=":",lw=1,label="Val checkpoint")
            ax.set(title=f"{family} / {EN[policy]} / seed17\nSelected stage {r.best_stage}, step {r.best_step}",xlabel="Optimiser step",ylabel="Joint standardised MSE");ax.grid(alpha=.15)
    handles,labels=axes[0,1].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=5,frameon=False)
    fig.suptitle("Recorded full-split losses: SAME seed17 across every policy\nNo smoothing; grey dashed lines are validation-only intervention times",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("policy_replays."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(12,10),layout="constrained")
    for k,family in enumerate(("RNN","LSTM")):
        r=next(runs.loc[runs.family.eq(family)&runs.policy.eq("combined")&runs.seed.eq(17)].itertuples());h=histories[r.run]
        for part,color in COLORS.items():axes[0,k].plot(h.global_step,h[part+"_eval_loss"],color=color,lw=.8,label=part)
        axes[0,k].axvline(r.best_step,color="black",ls=":",lw=.8,label="Val checkpoint");axes[0,k].set(title=family+" / Combined / seed17",ylabel="Joint MSE")
        for i,(col,label) in enumerate((("learning_rate","Learning rate"),("weight_decay","Weight decay"),("dropout","Output dropout")),1):
            axes[i,k].step(h.global_step,h[col],where="post",color="#245c91",lw=1.3);axes[i,k].set(ylabel=label,xlabel="Optimiser step")
            if i<3:axes[i,k].set_yscale("log")
        for ax in axes[:,k]:ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False)
    fig.suptitle("Combined policy: actual logged LR, WD and dropout used by each update",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("combined_schedules."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def report(summary,changes,selection,runs,record):
    def row(f,p,part,target="JOINT"):return summary.loc[summary.family.eq(f)&summary.policy.eq(p)&summary.split.eq(part)&summary.target.eq(target)].iloc[0]
    def cell(r):return f"{r.loss_mean:.6f} ± {r.loss_sd:.6f}"
    lines=["# 联合大模型：平台期学习率与正则化实验","",
        "RNN54951参数/28日窗口，LSTM54995参数/56日窗口，联合预测次日供给、需求、电价。输入8维、数据与train-only scaler完全沿用；train2022–24、val2025Jan–Aug、test2025Sep–2026Aug，样本1096/243/365。","",
        "本轮只按三种子平均综合val选策略，两家族均选fixed。调度后的test均值有约0.1%—1.5%的改善，但val未改善；不能据此反向用test选择。更平稳的训练轨迹值得保留，却没有转化为当前验证协议下的新胜出策略。","",
        "## 预先固定的四组策略","",
        "初始LR0.003、AdamW WD0.0001、输出dropout0.1。综合val连续5个完整epoch无新checkpoint改善时，最多进入3个新档位。训练从当前权重和AdamW动量继续，不回滚权重或重启优化器。","",
        "|档位|LR（lr_only/combined）|WD（reg_only/combined）|Dropout（reg_only/combined）|","|---:|---:|---:|---:|","|0|0.003|0.0001|0.1|","|1|0.001|0.001|0.2|","|2|0.0003|0.003|0.3|","|3|0.0001|0.01|0.4|","",
        "fixed三项均固定；lr_only只改LR；reg_only只改WD和dropout；combined三项同改。dropout仍只在输出头前，循环层结构不变。AdamW覆盖全部参数。综合loss不加入权重惩罚，三个分区评估均关闭dropout。日志额外记录LR×WD，以免只看名义WD忽略LR降低也会减小每次更新的直接衰减。","",
        "四组统一early-stop耐心30个完整epoch、最多120epoch。调度不重置这个全局早停时钟；最早3次调整发生于连续平台的第5/10/15个epoch，最后一档至少还有15个平台epoch可训练。旧实验耐心15，因此本轮fixed也从零重训，不将延长训练带来的变化直接归因于新策略。24次新GPU拟合（2家族×4策略×3种子），每step全量评估综合及三个分项。","",
        "## 综合loss：三种子均值与标准差","",
        "每个seed取单一综合val最优checkpoint。±是种子样本标准差，不是置信区间。","",
        "|模型|策略|Train|Val|Test|选中调整后checkpoint次数|","|---|---|---:|---:|---:|---:|"]
    for f in ("RNN","LSTM"):
        for p in POLICIES:
            count=int(runs.loc[runs.family.eq(f)&runs.policy.eq(p)].best_stage.gt(0).sum())
            lines.append(f"|{f}|{ZH[p]}|{cell(row(f,p,'train'))}|{cell(row(f,p,'validation'))}|{cell(row(f,p,'test'))}|{count}/3|")
    lines.extend(["","![四策略三集loss分布](figures/policy_joint_losses.png)","",
        "仅按三种子平均综合val选择策略："+"；".join(f+"="+ZH[s["policy"]] for f,s in selection.items())+"。test不参与选择。完整分项指标、逐seed变化和原始单位误差见结果文件，不从test反选一个看起来更好的策略。","",
        "## 逐step回放与实际参数变化","","![同一个seed17的四策略回放](figures/policy_replays.png)","",
        "蓝train、橙val、绿test；黑点线是选中checkpoint，灰虚线为调度动作，数字为新档位。统一展示seed17，没有按test挑图。","",
        "![实际学习率和正则化档位](figures/combined_schedules.png)","",
        "## 解释边界","",
        "RNN仅降LR相对同耐心fixed的test均值降低1.46%，结合正则降低1.17%，单加正则降低0.63%；三种策略的val均值均较差。LR下降后后段尖峰明显减少，额外增强正则没有在这个试验中显示出超过仅降LR的收益。","",
        "LSTM仅降LR与结合正则的所选结果完全相同，三个seed都选中stage0，即首次平台动作前的checkpoint。它们相对新fixed30的test均值低1.48%，主要因为seed29没有继续选择fixed后期的新val低点，而不是调度后训练出了更好的checkpoint。单加正则只有一个seed选到stage3，整体val仍未胜过fixed。","",
        "一个策略最终选择的checkpoint可能在首次调度之前；此时不能把该预测结果称为增强正则化或降LR之后训练出的提升。平台动作虽按规则执行，是否形成更优checkpoint需看best_stage。固定窗口和一套预先声明的分档只是探索，不能代表各方法调参后的最优能力。","",
        "当前val/test年份存在分布差异，val更低不保证test更低。Test已在之前多轮实验中监测，不是新的盲测；三种子只检查训练随机性，不是未来年份的置信区间。","",
        "## 核验与复现","",
        f"24checkpoint重放、参数/数据/划分/scaler/批次覆盖、每次平台动作、早停/选点和每step参数使用均通过。旧fixed15与新fixed30的共同前缀，以及每个新策略首次动作前与fixed的前缀逐值一致。共{record['optimizer_updates']:,}次更新、{record['evaluation_rows']:,}行全量评估。最大重放标准化预测差{record['max_normalised_replay_prediction_difference']:.3g}；最大指标/日志loss差{record['max_metric_vs_logged_loss_difference']:.3g}。","",
        "- SUMMARY.csv：三种子分区/目标均值与SD；VERSUS_MATCHED_FIXED.csv：逐seed和均值变化。","- SELECTION_BY_VALIDATION.json：只按val选出的策略；training_runs.csv记录每seed所选档位。","- ALL_STEP_LOSSES.csv、events/、PLATEAU_EVENTS.json：完整原始轨迹和调度动作。","- checkpoints/、predictions/：24组权重和三集原始单位预测。","",
        "requirements.txt与前轮相同。运行preflight.py、run.py、analyse.py可复现；bootstrap.py是一次性本地来源准备记录。旧release随reference保存。无外部特征、无MPC、未审计数据修复的历史发布版本，未上传或修改正式报告。"])
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    configure();result=json.loads((R/"RESULTS.json").read_text());f,x,data,mean,scale=dataset.prepare(False)
    runs=pd.read_csv(R/"training_runs.csv");metrics=pd.read_csv(R/"ALL_METRICS.csv")
    histories,record=audit(result,runs,metrics,x,data,mean,scale);summary,changes,selection=summarise(metrics)
    plot(metrics,runs,histories);report(summary,changes,selection,runs,record)
    print(summary.loc[summary.target.eq("JOINT")].to_string(index=False));print(changes.loc[changes.target.eq("JOINT")].to_string(index=False));print("SELECTION",json.dumps(selection));print("AUDIT",json.dumps(record))


if __name__=="__main__":main()
