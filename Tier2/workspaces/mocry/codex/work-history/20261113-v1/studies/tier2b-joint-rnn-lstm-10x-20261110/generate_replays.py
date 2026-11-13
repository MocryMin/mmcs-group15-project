"""Replay saved step logs; no training, smoothing or test-based selection."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from model import TARGETS

ROOT=Path(__file__).resolve().parent
EN={"generation_MW":"Generation","demand_MW":"Demand","price_GBP_MWh":"Price"}
COLORS={"train":"#245c91","validation":"#bb7625","test":"#38844d"}


def main():
    runs=pd.read_csv(ROOT/"results/training_runs.csv")
    assert len(runs)==12
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    folder=ROOT/"figures"
    fig,axes=plt.subplots(2,3,figsize=(14,8.2),layout="constrained")
    for i,family in enumerate(("RNN","LSTM")):
        for k,seed in enumerate((17,29,43)):
            r=next(runs.loc[runs.family.eq(family)&runs.budget.eq("large")&runs.seed.eq(seed)].itertuples())
            h=pd.read_csv(ROOT/r.step_log.replace("\\","/"));ax=axes[i,k]
            for part,color in COLORS.items():ax.plot(h.global_step,h[part+"_eval_loss"],color=color,lw=.85,label=part)
            ax.axvline(r.best_step,color="black",ls=":",lw=.8,label="Joint-val checkpoint")
            ax.set(title=f"{family}, {r.parameters:,} parameters, seed {seed}\nL={r.lookback}; selected step {r.best_step}",xlabel="Optimiser step",ylabel="Joint standardised MSE");ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False)
    fig.suptitle("Large joint models: EVERY seed's recorded train / validation / test loss\nFull-split evaluation after every update; no smoothing",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("large_all_seed_joint_steps."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12.8,11),layout="constrained")
    for k,family in enumerate(("RNN","LSTM")):
        group=runs.loc[runs.family.eq(family)&runs.budget.eq("large")].sort_values("best_validation_loss")
        r=next(group.iloc[[1]].itertuples());h=pd.read_csv(ROOT/r.step_log.replace("\\","/"))
        for i,target in enumerate(TARGETS):
            ax=axes[i,k]
            for part,color in COLORS.items():ax.plot(h.global_step,h[part+"_"+target+"_loss"],color=color,lw=.9,label=part)
            ax.axvline(r.best_step,color="black",ls=":",lw=.8,label="Joint-val checkpoint")
            ax.set(title=f"{EN[target]} / {family}, seed {r.seed}\nL={r.lookback}; SHARED selected step {r.best_step}",xlabel="Optimiser step",ylabel="Component standardised MSE");ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False)
    fig.suptitle("Large joint models: generation, demand and price loss trajectories\nMedian-JOINT-validation seed per family; every component shares that same checkpoint",fontsize=12)
    for ext in ("png","svg"):fig.savefig(folder/("large_component_step_losses."+ext),dpi=180,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)
    print("Generated all-seed joint and per-target component replays from unchanged logs.")


if __name__=="__main__":main()
