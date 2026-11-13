"""Import frozen neural predictions and reselect old linear candidates by target val."""
from pathlib import Path
import shutil
import json
import numpy as np
import pandas as pd
from common import ROOT,Data,TARGETS,INPUT_HASH,sha,dump,save_method,score

BASE=ROOT.parent


def main():
    for folder in ("inputs","reference","methods","predictions","results","models","cache"):(ROOT/folder).mkdir(exist_ok=True)
    source=BASE/"tier2b-joint-plateau-20261110"
    for name in ("inputs/model_daily.csv",):
        p=ROOT/name
        if p.exists():assert p.read_bytes()==(source/name).read_bytes()
        else:shutil.copy2(source/name,p)
    for name in ("scalers.json","splits.csv"):
        p=ROOT/"reference"/name
        if not p.exists():shutil.copy2(source/name,p)
    data=Data();imports=[]
    def verified(path,source_folder):
        manifest=json.loads((source_folder/"MANIFEST.json").read_text());rel=path.relative_to(source_folder).as_posix()
        assert sha(path)==manifest[rel]["sha256"],path
        imports.append({"folder":source_folder.name,"path":rel,"sha256":sha(path)})
        return np.load(path)
    small=BASE/"tier2b-transformer-grid-20261109";runs=pd.read_csv(small/"results/training_runs.csv");confirmed=pd.read_csv(small/"results/CONFIRMATION_METRICS.csv")
    for family,label in (("RNN","独立 RNN"),("LSTM","独立 LSTM"),("Transformer","独立 Transformer 5k")):
        pred={};configs={};total=0
        for seed in (17,29,43):
            columns={p:[] for p in data.origins}
            for target in TARGETS:
                c=confirmed.loc[confirmed.family.eq(family)&confirmed.target.eq(target)&confirmed.seed.eq(seed)].iloc[0]
                r=runs.loc[runs.family.eq(family)&runs.target.eq(target)&runs.seed.eq(seed)&runs.lookback.eq(c.lookback)&runs.lr.eq(c.lr)].iloc[0]
                z=verified(small/"predictions"/(r.run+".npz"),small)
                for p in columns:columns[p].append(z[p])
                configs[target]={"lookback":int(r.lookback),"lr":r.lr,"parameters_per_target":int(r.parameters)}
            pred[str(seed)]={p:np.column_stack(v) for p,v in columns.items()}
        total=sum(c["parameters_per_target"] for c in configs.values())
        save_method("N_sep_"+family,{"label":label,"category":"neural","regime":"fixed","selection":"Previously frozen independent target validation selection; per-seed target val checkpoints","target_configs":configs,"parameters_total":total,"uncertainty":"sample SD of three training seeds"},pred)
    big=BASE/"tier2b-transformer-10x-20261110";br=pd.read_csv(big/"results/training_runs.csv");pred={};configs={}
    for seed in (17,29,43):
        cols={p:[] for p in data.origins}
        for target in TARGETS:
            r=br.loc[br.seed.eq(seed)&br.target.eq(target)].iloc[0];z=verified(big/"predictions"/(r.run+".npz"),big)
            for p in cols:cols[p].append(z[p])
            configs[target]={"lookback":int(r.lookback),"lr":r.lr,"parameters_per_target":int(r.parameters)}
        pred[str(seed)]={p:np.column_stack(v) for p,v in cols.items()}
    save_method("N_sep_Transformer10x",{"label":"独立 Transformer 54k","category":"neural","regime":"fixed","selection":"Previous frozen target configurations and per-seed target val checkpoints","target_configs":configs,"parameters_total":162015,"uncertainty":"sample SD of three training seeds"},pred)
    joint=BASE/"tier2b-joint-rnn-lstm-10x-20261110";jr=pd.read_csv(joint/"results/training_runs.csv")
    for family in ("RNN","LSTM"):
        for budget in ("small","large"):
            group=jr.loc[jr.family.eq(family)&jr.budget.eq(budget)];pred={}
            for r in group.itertuples():z=verified(joint/"predictions"/(r.run+".npz"),joint);pred[str(r.seed)]={p:z[p] for p in data.origins}
            save_method("N_joint_"+family+"_"+budget+"15",{"label":f"联合 {family} {'5k' if budget=='small' else '55k'} P15","category":"neural","regime":"fixed","selection":"One joint-val checkpoint per seed, patience15","parameters_total":int(group.parameters.iloc[0]),"lookback":int(group.lookback.iloc[0]),"uncertainty":"sample SD of three training seeds"},pred)
    pr=pd.read_csv(source/"results/training_runs.csv")
    labels={"fixed":"固定","lr_only":"降LR","reg_only":"增强正则","combined":"LR+正则"}
    for family in ("RNN","LSTM"):
        for policy in labels:
            group=pr.loc[pr.family.eq(family)&pr.policy.eq(policy)];pred={}
            for r in group.itertuples():z=verified(source/"predictions"/(r.run+".npz"),source);pred[str(r.seed)]={p:z[p] for p in data.origins}
            save_method("N_joint_"+family+"_"+policy+"30",{"label":f"联合 {family} 55k {labels[policy]} P30","category":"neural","regime":"fixed","selection":"One joint-val checkpoint per seed; prior predeclared plateau policy; patience30","parameters_total":int(group.parameters.iloc[0]),"lookback":int(group.lookback.iloc[0]),"uncertainty":"sample SD of three training seeds"},pred)
    linear=BASE/"tier2b-traditional-regression-20261110";cases=pd.read_csv(linear/"results/CANDIDATES.csv");selections=[]
    group_labels={"Persistence":"持续值","Seasonal7":"七日季节朴素","Mean28":"28日均值","OLSLevel":"OLS 水平","OLSResidual":"OLS 变化","RidgeLevel":"岭回归 水平","RidgeResidual":"岭回归 变化","CalendarOLS":"日历回归","CalendarResidualAR":"日历回归+残差AR"}
    for group,rows in cases.groupby("group",sort=False):
        loaded={}
        for r in rows.itertuples():loaded[r.model]=verified(linear/"predictions"/(r.model+".npz"),linear)
        output={p:np.empty((len(o),3)) for p,o in data.origins.items()};config={};params=0
        for j,target in enumerate(TARGETS):
            ranking=[(score(z["validation"][:,j],data.y[data.origins["validation"]+1,j],data.scale[j])["loss"],name) for name,z in loaded.items()]
            val,name=min(ranking);r=rows.loc[rows.model.eq(name)].iloc[0]
            for p in output:output[p][:,j]=loaded[name][p][:,j]
            config[target]={"candidate":name,"validation_loss":val};params+=int(r.parameters)//3
            selections.append({"family":group,"target":target,"candidate":name,"validation_loss":val})
        save_method("T_fixed_"+group,{"label":group_labels[group],"category":"traditional","regime":"fixed" if group not in ("Persistence","Seasonal7","Mean28") else "past_only_rule","selection":"Each target selects its own configuration solely by target validation MSE","target_configs":config,"parameters_total":params,"uncertainty":"deterministic; no training seed SD"},{"det":output})
    pd.DataFrame(selections).to_csv(ROOT/"results/IMPORTED_LINEAR_SELECTIONS.csv",index=False)
    dump(ROOT/"reference/IMPORT_MANIFEST.json",imports)
    print("Prepared 16 frozen neural variants and 9 target-selected traditional families; verified",len(imports),"prediction sources.")


if __name__=="__main__":main()
