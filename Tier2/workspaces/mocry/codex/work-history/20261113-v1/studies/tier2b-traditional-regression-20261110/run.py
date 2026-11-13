"""Deterministic fixed-train linear baselines on the exact current neural split."""
import os
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("OPENBLAS_NUM_THREADS","2")
os.environ.setdefault("MKL_NUM_THREADS","2")
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]
PERIODS={"train":("2022-01-01","2024-12-31"),"validation":("2025-01-01","2025-08-31"),"test":("2025-09-01","2026-08-31")}
EXPECTED="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def score(pred,truth,scale):
    e=(pred-truth)/scale
    return [{"target":"JOINT","loss":float(np.mean(e**2))}]+[{"target":t,"loss":float(np.mean(e[:,j]**2)),"RMSE":float(np.sqrt(np.mean((pred[:,j]-truth[:,j])**2))),"MAE":float(np.mean(np.abs(pred[:,j]-truth[:,j])))} for j,t in enumerate(TARGETS)]


def main():
    for p in ("inputs","results","predictions","coefficients","reference"):(ROOT/p).mkdir(exist_ok=True)
    source=ROOT.parent/"tier2b-joint-plateau-20261110/inputs/model_daily.csv";dest=ROOT/"inputs/model_daily.csv"
    if not dest.exists():dest.write_bytes(source.read_bytes())
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==EXPECTED
    f=pd.read_csv(dest,parse_dates=["date"]).set_index("date");train=f.loc["2022":"2024",TARGETS]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy();z=(f[TARGETS].to_numpy()-mean)/scale
    neural=ROOT.parent/"tier2b-joint-plateau-20261110"
    for name in ("scalers.json","splits.csv"):
        if not (ROOT/"reference"/name).exists():(ROOT/"reference"/name).write_bytes((neural/name).read_bytes())
    scaler=json.loads((ROOT/"reference/scalers.json").read_text());assert np.array_equal(mean,scaler["mean"]) and np.array_equal(scale,scaler["std"])
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32).astype(float)
    data={}
    for part,(a,b) in PERIODS.items():
        origin=np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b));target=origin+1
        data[part]={"origin":origin,"target":target,"truth":f[TARGETS].to_numpy()[target],"ynorm":z[target],"today":z[origin]}
    assert {p:len(d["origin"]) for p,d in data.items()}=={"train":1096,"validation":243,"test":365}
    oldsplit=pd.read_csv(ROOT/"reference/splits.csv")
    for p,d in data.items():assert np.array_equal(f.index[d["target"]].strftime("%Y-%m-%d"),oldsplit.loc[oldsplit.split.eq(p),"target_date"].to_numpy())
    metrics=[];cases=[];maximum_roundtrip=0.
    def save(name,group,parameters,pred,meta,coeff=None):
        nonlocal maximum_roundtrip
        raw={p:np.asarray(v,float)*scale+mean for p,v in pred.items()}
        for p,v in raw.items():
            maximum_roundtrip=max(maximum_roundtrip,float(np.max(np.abs((v-mean)/scale-pred[p]))))
            metrics.extend({"model":name,"group":group,"parameters":parameters,"split":p,**m} for m in score(v,data[p]["truth"],scale))
        np.savez_compressed(ROOT/"predictions"/(name+".npz"),**raw)
        if coeff is not None:np.savez_compressed(ROOT/"coefficients"/(name+".npz"),**coeff)
        cases.append({"model":name,"group":group,"parameters":parameters,**meta})
    for name,lag in (("Persistence",1),("Seasonal7",7)):
        save(name,name,0,{p:z[d["target"]-lag] for p,d in data.items()},{"trained":False})
    ma28=pd.DataFrame(z).rolling(28).mean().to_numpy()
    save("Mean28","Mean28",0,{p:ma28[d["origin"]] for p,d in data.items()},{"trained":False})
    for length in (7,14,28,56):
        arrays={p:np.stack([x[t-length+1:t+1].reshape(-1) for t in d["origin"]]) for p,d in data.items()}
        center=arrays["train"].mean(0);sd=arrays["train"].std(0);sd[sd<1e-12]=1.
        xx={p:(a-center)/sd for p,a in arrays.items()};u,s,vt=np.linalg.svd(xx["train"],full_matrices=False)
        # Float32 calendar histories contain nearly duplicated lag columns.
        # Drop roundoff-sized singular directions instead of fitting million-size OLS coefficients.
        tolerance=1e-6*s[0]
        for residual in (False,True):
            yy=data["train"]["ynorm"]-(data["train"]["today"] if residual else 0)
            intercept=yy.mean(0);uy=u.T@(yy-intercept)
            for alpha in (0.,.01,.1,1.,10.,100.,1000.):
                factor=np.divide(1.,s,out=np.zeros_like(s),where=s>tolerance) if alpha==0 else s/(s*s+alpha)
                weight=vt.T@(factor[:,None]*uy)
                pred={p:a@weight+intercept+(data[p]["today"] if residual else 0) for p,a in xx.items()}
                group=("OLS" if alpha==0 else "Ridge")+("Residual" if residual else "Level")
                name=f"{group}_L{length}_a{alpha:g}"
                save(name,group,weight.size+intercept.size,pred,{"lookback":length,"alpha":alpha,"residual_to_persistence":residual,"OLS_rank_cutoff":1e-6 if alpha==0 else None,"feature_representation":"Same Lx8 flattened neural input; train-fitted lag-column scaling"},
                    {"weight":weight,"intercept":intercept,"feature_center":center,"feature_std":sd,"target_mean":mean,"target_std":scale})
    md=f.index.month.to_numpy()*100+f.index.day.to_numpy()
    cal=np.column_stack([np.eye(7)[dow],*[fn(2*np.pi*h*phase) for h in (1,2,3) for fn in (np.sin,np.cos)],((md>=1224)|(md<=101)).astype(float)])
    target=data["train"]["target"];b=np.linalg.lstsq(cal[target],z[target],rcond=None)[0]
    save("CalendarOLS","CalendarOLS",b.size,{p:cal[d["target"]]@b for p,d in data.items()},{"calendar_columns":14,"feature_representation":"Known target-day weekday dummies, three annual harmonics, Christmas-period flag; no external holiday data"},{"calendar_weight":b,"target_mean":mean,"target_std":scale})
    residual=z-cal@b;e7=pd.DataFrame(residual).rolling(7).mean().to_numpy();phi=np.zeros((2,3));pred={p:cal[d["target"]]@b for p,d in data.items()}
    for j in range(3):
        a=np.column_stack([residual[data["train"]["origin"],j],e7[data["train"]["origin"],j]])
        phi[:,j]=np.linalg.lstsq(a,residual[target,j],rcond=None)[0]
        for p,d in data.items():pred[p][:,j]+=np.column_stack([residual[d["origin"],j],e7[d["origin"],j]])@phi[:,j]
    save("CalendarResidualAR","CalendarResidualAR",b.size+phi.size,pred,{"calendar_columns":14,"residual_terms":["last observed residual","trailing7 residual mean"],"feature_representation":"Known calendar plus observed past residuals; fixed training coefficients"},{"calendar_weight":b,"residual_weight":phi,"target_mean":mean,"target_std":scale})
    m=pd.DataFrame(metrics);c=pd.DataFrame(cases);m.to_csv(ROOT/"results/ALL_METRICS.csv",index=False);c.to_csv(ROOT/"results/CANDIDATES.csv",index=False)
    val=m.loc[m.target.eq("JOINT")&m.split.eq("validation")];selected=val.sort_values(["loss","model"]).groupby("group",sort=False).head(1)
    choices={r.group:{"model":r.model,"validation_loss":r.loss,"criterion":"Joint validation MSE only"} for r in selected.itertuples()};dump(ROOT/"results/SELECTION.json",choices)
    chosen=m.loc[m.model.isin(selected.model)].copy();chosen.to_csv(ROOT/"results/SELECTED_METRICS.csv",index=False)
    audit={"all_passed":bool(maximum_roundtrip<1e-12),"candidates":len(cases),"input_hash":EXPECTED,"same_target_dates_scalers_and_base_history_features":True,"causal_history_features":True,
        "fit_coefficients_only_train":True,"val_only_model_selection":True,"test_is_monitored_not_blind":True,"linear_models_are_deterministic":True,"neural_context_not_random_repetitions":False,
        "max_normalisation_roundtrip_error":maximum_roundtrip,"calendar_extra_representation_explicit":True,"bank_holidays_added":False,"rolling_refit":False}
    assert audit["all_passed"] and len(cases)==61
    for name in selected.model:
        saved=np.load(ROOT/"predictions"/(name+".npz"))
        for p in PERIODS:
            for metric in score(saved[p],data[p]["truth"],scale):
                rr=m.loc[m.model.eq(name)&m.split.eq(p)&m.target.eq(metric["target"])].iloc[0]
                assert abs(rr.loss-metric["loss"])<1e-12
    dump(ROOT/"results/AUDIT.json",audit);dump(ROOT/"PROTOCOL.json",{"periods":PERIODS,"source_sha256":EXPECTED,"lookbacks":[7,14,28,56],"alpha_grid":[0,.01,.1,1,10,100,1000],"OLS_relative_rank_cutoff":1e-6,"OLS_precision_reason":"Near-dependent calendar lag columns inherited from float32 features; cutoff chosen from precision audit, not test loss","seeds":"not applicable: deterministic closed-form fit","refit":"train2022–24 once; actual past observations remain available as history","external_data":False,"source_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    lines=["# 同划分传统回归基线试算","","与当前神经实验使用相同冻结数据、train2022–24、val2025Jan–Aug、test2025Sep–2026Aug及训练期标准化。所有回归系数只用train拟合，val选型；不进行滚动重训。本轮只预测次日。","",
        "OLS/岭回归读取与神经模型相同的L×8历史，展开为线性特征；分别比较直接预测水平和相对当天的残差。窗口7/14/28/56、alpha0/0.01/0.1/1/10/100/1000；alpha0用SVD截断最小范数OLS。日历回归是另一种已知日期的表示：星期哑变量、三阶年周期和圣诞期；残差AR使用最后已观察残差及其过去7日均值，没有新增天气/能源数据或银行假日表。","",
        "这些方法是确定性拟合，没有随机初始化、epoch或可解释的三种子训练波动。每组只按综合val MSE选一个配置，三个输出共同评价。","","|方法组|Val选中的配置|Train loss|Val loss|Test loss|","|---|---|---:|---:|---:|"]
    for r in selected.itertuples():
        g=chosen.loc[chosen.model.eq(r.model)&chosen.target.eq("JOINT")].set_index("split")
        lines.append(f"|{r.group}|{r.model}|{g.loc['train','loss']:.6f}|{g.loc['validation','loss']:.6f}|{g.loc['test','loss']:.6f}|")
    lines.extend(["","基线与神经模型的信息来源相同，但特征表示、容量与选型预算不同，不将差异单独归因于是否神经网络。Fable的研究采用2024–25测试、2020年不变价、额外发电分量特征和滚动重估；其数值不与本表直接比较。这里还没有执行修正后的多步/滚动回测、LASSO或MPC。","","输入/划分/scaler、训练期拟合与val选择、保存预测和指标复算已核验。所有候选指标、选型、权重和原始单位预测保留于results、coefficients、predictions；未上传或修改正式报告。"])
    (ROOT/"REPORT_ZH.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(selected[["group","model","loss"]].to_string(index=False));print(chosen.loc[chosen.target.eq("JOINT"),["group","split","loss"]].to_string(index=False));print("AUDIT",json.dumps(audit))


if __name__=="__main__":main()
