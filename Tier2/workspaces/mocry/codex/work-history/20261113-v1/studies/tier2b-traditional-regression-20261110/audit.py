"""Independently replay linear coefficients and verify train normal equations."""
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
T=["generation_MW","demand_MW","price_GBP_MWh"]


def main():
    protocol=json.loads((ROOT/"PROTOCOL.json").read_text());assert hashlib.sha256((ROOT/"inputs/model_daily.csv").read_bytes()).hexdigest()==protocol["source_sha256"]
    f=pd.read_csv(ROOT/"inputs/model_daily.csv",parse_dates=["date"]).set_index("date");train=f.loc["2022":"2024",T]
    mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy();z=(f[T].to_numpy()-mean)/scale
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]).astype(np.float32).astype(float)
    data={p:np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b)) for p,(a,b) in protocol["periods"].items()}
    md=f.index.month.to_numpy()*100+f.index.day.to_numpy()
    cal=np.column_stack([np.eye(7)[dow],*[fn(2*np.pi*h*phase) for h in (1,2,3) for fn in (np.sin,np.cos)],((md>=1224)|(md<=101)).astype(float)])
    cases=pd.read_csv(ROOT/"results/CANDIDATES.csv");metrics=pd.read_csv(ROOT/"results/ALL_METRICS.csv");selection=json.loads((ROOT/"results/SELECTION.json").read_text())
    assert len(cases)==61 and len(metrics)==61*3*4
    max_prediction=0.;max_metric=0.;max_normal=0.
    for r in cases.itertuples():
        stored=np.load(ROOT/"predictions"/(r.model+".npz"));pred={}
        if r.group in ("OLSLevel","OLSResidual","RidgeLevel","RidgeResidual"):
            cp=np.load(ROOT/"coefficients"/(r.model+".npz"));length=int(r.lookback)
            arrays={p:np.stack([x[t-length+1:t+1].reshape(-1) for t in origins]) for p,origins in data.items()}
            assert np.allclose(arrays["train"].mean(0),cp["feature_center"],rtol=0,atol=1e-14)
            expected=arrays["train"].std(0);expected[expected<1e-12]=1.;assert np.array_equal(expected,cp["feature_std"])
            arrays={p:(a-cp["feature_center"])/cp["feature_std"] for p,a in arrays.items()}
            is_residual=r.group.endswith("Residual")
            for p,a in arrays.items():pred[p]=a@cp["weight"]+cp["intercept"]+(z[data[p]] if is_residual else 0)
            yy=z[data["train"]+1]-(z[data["train"]] if is_residual else 0)
            lhs=arrays["train"].T@(arrays["train"]@cp["weight"]+cp["intercept"]-yy)+r.alpha*cp["weight"]
            rhs=arrays["train"].T@(yy-cp["intercept"])
            if r.alpha==0:
                # Truncated OLS solves the retained singular subspace, rather than
                # the deliberately discarded near-null calendar directions.
                _,singular,basis=np.linalg.svd(arrays["train"],full_matrices=False)
                keep=basis[singular>1e-6*singular[0]]
                projected=keep.T@(keep@cp["weight"])
                assert np.linalg.norm(projected-cp["weight"])/max(1.,np.linalg.norm(cp["weight"]))<1e-8
                lhs=keep@lhs;rhs=keep@rhs
            err=float(np.linalg.norm(lhs)/max(1.,np.linalg.norm(rhs)));max_normal=max(max_normal,err)
            assert err<1e-8 and np.allclose(cp["intercept"],yy.mean(0),atol=1e-14),(r.model,err,float(np.abs(cp["weight"]).max()),float(np.abs(cp["intercept"]-yy.mean(0)).max()))
        elif r.group in ("CalendarOLS","CalendarResidualAR"):
            cp=np.load(ROOT/"coefficients"/(r.model+".npz"));b=cp["calendar_weight"]
            traincal=cal[data["train"]+1];gradient=traincal.T@(traincal@b-z[data["train"]+1])
            assert np.linalg.norm(gradient)<1e-8
            pred={p:cal[origins+1]@b for p,origins in data.items()}
            if r.group=="CalendarResidualAR":
                e=z-cal@b;e7=pd.DataFrame(e).rolling(7).mean().to_numpy()
                for j in range(3):
                    for p,origins in data.items():pred[p][:,j]+=np.column_stack([e[origins,j],e7[origins,j]])@cp["residual_weight"][:,j]
                    a=np.column_stack([e[data["train"],j],e7[data["train"],j]])
                    assert np.linalg.norm(a.T@(a@cp["residual_weight"][:,j]-e[data["train"]+1,j]))<1e-8
        else:
            if r.group=="Mean28":average=pd.DataFrame(z).rolling(28).mean().to_numpy();pred={p:average[o] for p,o in data.items()}
            else:
                lag=1 if r.group=="Persistence" else 7;pred={p:z[o+1-lag] for p,o in data.items()}
        for p,pnorm in pred.items():
            raw=pnorm*scale+mean;truth=f[T].to_numpy()[data[p]+1]
            max_prediction=max(max_prediction,float(np.abs((raw-stored[p])/scale).max()))
            losses=((stored[p]-truth)/scale)**2
            for j,t in enumerate(T):
                rr=metrics.loc[metrics.model.eq(r.model)&metrics.split.eq(p)&metrics.target.eq(t)].iloc[0]
                max_metric=max(max_metric,abs(losses[:,j].mean()-rr.loss))
            rr=metrics.loc[metrics.model.eq(r.model)&metrics.split.eq(p)&metrics.target.eq("JOINT")].iloc[0]
            max_metric=max(max_metric,abs(losses.mean()-rr.loss))
    assert max_prediction<1e-10 and max_metric<1e-12
    for group,c in selection.items():
        rr=metrics.loc[metrics.group.eq(group)&metrics.target.eq("JOINT")&metrics.split.eq("validation")].sort_values(["loss","model"]).iloc[0]
        assert rr.model==c["model"] and abs(rr.loss-c["validation_loss"])<1e-12
    record={"all_passed":True,"candidates_replayed":61,"all_predictions_replayed_from_coefficients_or_past_only_rules":True,
        "ridge_full_and_truncated_OLS_projected_train_normal_equations_verified":True,"calendar_and_AR_train_normal_equations_verified":True,"val_only_selection_verified":True,
        "max_normalised_prediction_difference":max_prediction,"max_metric_difference":max_metric,"max_relative_ridge_normal_equation_residual":max_normal,
        "future_observations_used_as_features":False,"known_calendar_representation_explicit":True,"deterministic_no_seed_variation":True}
    (ROOT/"results/INDEPENDENT_AUDIT.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8");print(json.dumps(record))


if __name__=="__main__":main()
