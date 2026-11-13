"""Generate academic tables and vector diagrams from the frozen calculation archive."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "report"


def fmt(value, digits=2):
    if value < -.5 * 10**(-digits):
        return r"\minus{" + f"{-value:.{digits}f}" + "}"
    return f"{max(value, 0):.{digits}f}"


def tab(name, caption, label, columns, headers, rows):
    natural = "Y" not in columns
    opening = (r"\begin{tabular}{@{}" + columns + "@{}}" if natural else
               r"\begin{tabularx}{\linewidth}{@{}" + columns + "@{}}")
    text = [r"\begin{table}[H]", r"\centering\small", r"\caption{"+caption+"}",
            r"\label{"+label+"}", opening,
            r"\toprule", " & ".join(headers)+r" \\", r"\midrule"]
    text += [" & ".join(row)+r" \\" for row in rows]
    text += [r"\bottomrule", r"\end{tabular}" if natural else r"\end{tabularx}", r"\end{table}"]
    (OUT / "generated" / name).write_text("\n".join(text)+"\n", encoding="utf-8")


def architecture():
    fig, ax = plt.subplots(figsize=(7.2, 2.60))
    ax.set(xlim=(-.05, 10.05), ylim=(-.50, 3.1))
    ax.axis("off")

    def box(x, y, text, width=1.72, height=.78):
        ax.add_patch(Rectangle((x, y), width, height, facecolor="white", edgecolor="black", lw=.65))
        ax.text(x+width/2, y+height/2, text, ha="center", va="center", fontsize=7.6)

    def arrow(start, end, path="arc3", dashed=False):
        if path != "arc3":
            middle = .27 if start[1] == end[1] else (start[1] + end[1]) / 2
            ax.plot([start[0],start[0],end[0]], [start[1],middle,middle],color="black",lw=.65)
            start = (end[0],middle)
            path = "arc3"
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8,
                                     linewidth=.65, color="black", connectionstyle=path,
                                     linestyle="--" if dashed else "-"))

    xs=[0,2.06,4.12,6.18,8.24]
    texts=["Course series\nUpstream records\nEquipment research",
           "Repair and alignment\nQuality flags\nDaily energy / price",
           "Tier 1 appraisal\nKnown historical paths\nInvestment sensitivities",
           "Capacity selection\nTraining years only\nFixed before test",
           "Evaluation\nRealised annual gain\nSurplus and lost sales"]
    for x,text in zip(xs,texts):
        box(x,2.08,text)
    for i in (0,1):
        arrow((xs[i]+1.72,2.47),(xs[i+1],2.47))
    arrow((5.84,2.47),(6.18,2.47),dashed=True)
    ax.text(6.01,2.98,"same formulation",fontsize=6.7,ha="center")
    for x,text in zip(xs[:4],["Dated history\nTraining / validation\nObserved test days",
                             "Multi-step prediction\nGeneration, demand\nElectricity price",
                             "Rolling optimisation\nCurrent observations\nFuture predictions",
                             "Execute one day\nSell / store / hydrogen\nUpdate battery stock"]):
        box(x,.57,text,height=.84)
    for i in range(3):
        arrow((xs[i]+1.72,.99),(xs[i+1],.99))
    arrow((2.92,2.08),(.86,1.41),"angle,angleA=-90,angleB=90,rad=0")
    arrow((7.04,2.08),(4.98,1.41),"angle,angleA=-90,angleB=90,rad=0")
    arrow((7.9,.99),(9.1,2.08),"angle,angleA=0,angleB=-90,rad=0")
    arrow((7.04,.57),(4.98,.57),"angle,angleA=-90,angleB=-90,rad=0")
    ax.text(6.01,.08,"Stock feedback to next solve",fontsize=7.3,ha="center")
    ax.plot([7.90,9.98,9.98,.86],[.78,.78,-.15,-.15],color="black",lw=.65)
    arrow((.86,-.15),(.86,.57))
    ax.text(4.5,-.37,"Observe the next day; append its data to the available history",fontsize=7.3,ha="center")
    fig.subplots_adjust(left=.005,right=.995,bottom=.01,top=.99)
    fig.savefig(OUT / "figures/model_architecture.pdf",bbox_inches="tight",pad_inches=.02)
    plt.close(fig)


def frontier(primary):
    grid = pd.read_csv(ROOT / "results/contract_grid.csv")
    fig, axes = plt.subplots(1,2,figsize=(7.0,2.4),sharey=True)
    for ax, policy in zip(axes, "AB"):
        panel = grid[grid.policy == policy]
        sizes = panel.pivot(index="price",columns="offtake_t_day",values="modules")
        gains = panel.pivot(index="price",columns="offtake_t_day",values="gain")
        x,y=sizes.columns.to_numpy(), sizes.index.to_numpy()
        ax.imshow(sizes.to_numpy(), origin="lower", interpolation="nearest",
                  extent=(x.min()-.25,x.max()+.25,y.min()-.125,y.max()+.125),
                  aspect="auto",cmap="Greys",vmin=0,vmax=5)
        levels=[level for level in (2,5,10,20,30) if gains.to_numpy().max()>level]
        curves=ax.contour(x,y,gains,levels=levels,colors="black",linewidths=.5)
        ax.clabel(curves,inline=True,fmt="%g",fontsize=7)
        for modules in (1,2,3,4):
            points=np.argwhere(sizes.to_numpy()==modules)
            if len(points):
                row,col=points[len(points)//2]
                ax.text(x[col],y[row],f"{20*modules} MW",fontsize=7.0,ha="center",
                        bbox=dict(facecolor="white",edgecolor="none",pad=1.1,alpha=.9))
        ax.scatter(10,7.7990270551508845,marker="x",s=34,color="black",linewidths=1)
        ax.scatter(10,primary["summary"]["hydrogen_crossings"][f"{policy}_2023"],
                   marker="o",s=29,facecolor="white",edgecolor="black",linewidth=.8)
        ax.set(xlim=(0,30),ylim=(0,16),xlabel="Buyer limit (t/day)",title=f"Policy {policy}")
        ax.set_yticks([0,4,8,12,16])
        ax.text(3,2,"No build",fontsize=7.1)
    axes[0].set_ylabel("Hydrogen netback (2020 £/kg)")
    fig.subplots_adjust(left=.09,right=.99,bottom=.19,top=.90,wspace=.12)
    fig.savefig(OUT/"figures/contract_frontier.pdf",bbox_inches="tight",pad_inches=.025)
    plt.close(fig)


def run():
    (OUT/"generated").mkdir(exist_ok=True)
    (OUT/"figures").mkdir(exist_ok=True)
    primary=json.loads((ROOT/"results/study.json").read_text(encoding="utf-8"))
    extra=json.loads((ROOT/"results/extension.json").read_text(encoding="utf-8"))
    c,s=primary["cases"],primary["summary"]
    a=c["A_joint"]
    years=pd.read_csv(ROOT/"results/annual_replay.csv")
    complete=years[years.full_year]
    cash=s["cashflow_20MW"]["A_2023"]
    values={
        "Capital":f'{a["capex"]:.1f}',"MeanA":f'{complete.A_gain.mean():.2f}',
        "MeanB":f'{complete.B_gain.mean():.2f}',"Netback":f'{a["price_H2"]:.2f}',
        "RefGain":f'{a["net"]:.2f}',"SimpleLoss":f'{abs(c["A_simple20_2023"]["net"]):.2f}',
        "Hinput":f'{a["h2_GWh"]:.1f}',"Capture":f'{a["capture_GWh"]:.2f}',
        "Displaced":f'{a["displacement_GWh"]:.1f}',"Surplus":f'{s["surplus_GWh"]:.1f}',
        "CaptureShare":f'{100*a["capture_GWh"]/a["h2_GWh"]:.1f}',
        "SurplusShare":f'{100*a["capture_GWh"]/s["surplus_GWh"]:.2f}',
        "PhysicalCap":f'{extra["physical_cap_GWh"]:.2f}',
        "BreakA":f'{s["hydrogen_crossings"]["A_2023"]:.2f}',
        "BreakB":f'{s["hydrogen_crossings"]["B_2023"]:.2f}',
        "OfftakeBreak":f'{extra["offtake_break_even_kg_day"]/1000:.2f}',
        "FortyGain":f'{extra["cases"]["A_fixed40_2023"]["net"]:.2f}',
        "ExpansionGain":f'{extra["cases"]["A_offtake50_2023"]["net"]:.2f}',
        "ExpansionCapital":f'{extra["cases"]["A_offtake50_2023"]["capex"]:.1f}',
        "BatteryBound":f'{extra["battery_bounds"]["A"]["free_charge_revenue_ceiling"]*1000:.1f}',
        "BatteryCost":f'{extra["battery_bounds"]["A"]["annual_cost"]*1000:.1f}',
        "PoolValue":f'{1000*(c["A_battery1_pool"]["direct_change"]+c["A_battery1_pool"]["discharge_value"]):.1f}',
        "StockValue":f'{1000*(c["A_battery1_stock"]["direct_change"]+c["A_battery1_stock"]["discharge_value"]):.1f}',
        "NPV":f'{cash["npv"]:.1f}',"Payback":f'{cash["simple_payback"]:.2f}',
        "DiscountedPayback":f'{cash["discounted_payback"]:.2f}',
    }
    (OUT/"generated/numbers.tex").write_text("\n".join(
        "\\newcommand{\\"+k+"}{"+v+"}" for k,v in values.items())+"\n",encoding="utf-8")
    (ROOT/"results/report_values_v4.json").write_text(json.dumps(values,indent=2)+"\n",encoding="utf-8")
    lines=[r"\begin{table}[H]",r"\centering\small",
           r"\caption{Investment and operating results: capacities in MW, hydrogen in t/year, "
           r"gains in \gbp m/year against each policy's zero investment. "
           r"Panel (b) capture is identical in A and B.}",
           r"\label{tab:annual}",r"\textit{(a) 2023: asset-set optimisation and fixed-capacity comparison}\par\vspace{2pt}",
           r"\begin{tabular}{@{}l r r r r r r@{}}",r"\toprule",
           r" & \multicolumn{3}{c}{Policy A} & \multicolumn{3}{c}{Policy B} \\",
           r"\cmidrule(lr){2-4}\cmidrule(l){5-7}",
           r"Allowed investment & Battery & Electrolyser & Gain & Battery & Electrolyser & Gain \\",r"\midrule"]
    for title,key in [("No investment","zero"),("Battery only","battery"),
                      ("Electrolyser only","hydrogen"),("Joint choice","joint"),("Fixed 20 MW","fixed20_2023")]:
        row=[title]
        for policy in "AB":
            item=c[f"{policy}_{key}"]
            row.extend([fmt(item["battery_MW"],0),fmt(item["h2_MW"],0),fmt(item["net"])])
        lines.append(" & ".join(row)+r" \\")
    lines += [r"\bottomrule",r"\end{tabular}",r"\par\vspace{5pt}",
              r"\textit{(b) Fixed 20 MW on every complete year}\par\vspace{2pt}",
              r"\begin{tabular}{@{}l r r r r r r r@{}}",r"\toprule",
              r"Year & \shortstack{Surplus\\days} & \shortstack{Surplus\\(GWh)} & \shortstack{Capture\\(GWh)} & "
              r"H$_2$ A & H$_2$ B & Gain A & Gain B \\",r"\midrule"]
    annual_outputs=[]
    for item in complete.itertuples():
        year=int(item.year)
        h_a,h_b=c[f"A_fixed20_{year}"]["h2_tonnes"],c[f"B_fixed20_{year}"]["h2_tonnes"]
        annual_outputs.append((h_a,h_b))
        row=[str(year),str(int(item.surplus_days)),fmt(item.surplus_GWh,0),fmt(item.A_capture_GWh,1),
             fmt(h_a,0),fmt(h_b,0),fmt(item.A_gain),fmt(item.B_gain)]
        lines.append(" & ".join(row)+r" \\")
    row=["Mean","--",fmt(complete.surplus_GWh.mean(),0),fmt(complete.A_capture_GWh.mean(),1),
         fmt(np.mean([a for a,b in annual_outputs]),0),fmt(np.mean([b for a,b in annual_outputs]),0),
         fmt(complete.A_gain.mean()),fmt(complete.B_gain.mean())]
    lines += [" & ".join(row)+r" \\",r"\bottomrule",r"\end{tabular}",r"\end{table}"]
    (OUT/"generated/annual.tex").write_text("\n".join(lines)+"\n",encoding="utf-8")
    e=extra["cases"]
    scenarios=[(r"Recover half of lost sales",c["A_service_50"],None),
               (r"Retain 99.99\% of sales",e["A_floor_0.9999"],None),
               (r"Fixed 40 MW",e["A_fixed40_2023"],e["B_fixed40_2023"]),
               (r"50 t/day, free capacity",e["A_offtake50_2023"],e["B_offtake50_2023"]),
               (r"Capital +25\%, rate 8\%",c["A_fixed20_cost_stress"],c["B_fixed20_cost_stress"]),
               (r"2025 downside",c["A_fixed20_downside"],c["B_fixed20_downside"])]
    rows=[]
    for title,a_case,b_case in scenarios:
        rows.append([title,fmt(a_case["h2_MW"],0),fmt(b_case["h2_MW"],0) if b_case else "--",
                     fmt(a_case["price_H2"]),fmt(a_case["offtake_kg_day"]/1000,0),
                     fmt(a_case["capex"],1),fmt(a_case["displacement_GWh"],1),
                     fmt(a_case["net"]),fmt(b_case["net"]) if b_case else "--"])
    tab("comparisons.tex",r"Sensitivity and operating comparisons (2023 unless marked). "
        r"Electrolyser capacities $H_A,H_B$: MW; $v$: \gbp/kg; $L$ reported in t/day; capital: \gbp m; lost sales: GWh/year; "
        r"gain: \gbp m/year. Capacity is optimised for sales floors/50 t, otherwise fixed; "
        r"dashes mark A-only constraints.",
        "tab:comparisons","l r r r r r r r r",
        ["Comparison",r"$H_A$",r"$H_B$",r"$v$",r"$L$",r"\shortstack{Capital\\A}",
         r"\shortstack{Lost\\sales A}","Gain A","Gain B"],rows)
    plt.rcParams.update({"font.family":"serif","font.size":9,"pdf.fonttype":42,
                         "axes.spines.top":False,"axes.spines.right":False})
    architecture()
    frontier(primary)
    print("Generated academic tables, parameter macros and two vector diagrams.")


if __name__=="__main__":
    run()
