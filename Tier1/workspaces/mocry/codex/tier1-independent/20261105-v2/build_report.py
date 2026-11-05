"""Build the four-page report and editable Markdown from the same result records."""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "report"
FIG = OUT / "figures"
RESULT = ROOT.parent / "20261105-v1" / "results"
STUDY = json.loads((RESULT / "study.json").read_text(encoding="utf-8"))
S, C = STUDY["summary"], STUDY["cases"]
CHECK = json.loads((ROOT / "crosscheck.json").read_text(encoding="utf-8"))
INK = "#172838"
TEAL = "#12675f"
GRAY = "#526273"
RULE = "#d8e2e7"
PALE = "#edf6f4"
WIDTH = A4[0] - 90


def figures():
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.labelcolor": INK, "xtick.color": GRAY,
                         "ytick.color": GRAY, "text.color": INK, "savefig.facecolor": "white"})
    f = pd.read_csv(RESULT / "schedules/A_joint.csv")
    surplus = np.maximum(f.g - f.demand, 0)
    positive = np.sort(surplus[surplus > 1e-9])[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 2.22), layout="constrained")
    rank = np.arange(1, len(positive) + 1)
    ax.plot(rank, positive, color=TEAL, linewidth=2.2, marker="o", markersize=3)
    ax.axhline(.48, color="#9b4c2d", linestyle="--", linewidth=1.4, label="One 20 MW module: 0.48 GWh/day")
    ax.set(yscale="log", ylim=(.32, 110), xlim=(1, len(rank)), xlabel="Positive-surplus days, ranked",
           ylabel="Daily surplus (GWh)", xticks=[1, 5, 10, 15, 20, 25, 29], yticks=[.5, 1, 5, 10, 50, 100])
    ax.set_yticklabels(["0.5", "1", "5", "10", "50", "100"])
    ax.grid(axis="y", alpha=.19)
    ax.legend(loc="upper right", frameon=False, fontsize=8.6)
    fig.savefig(FIG / "surplus.png", dpi=220)
    plt.close(fig)

    grid = pd.read_csv(RESULT / "contract_grid.csv")
    palette = ["#e8edf0", "#93cec3", "#509a92", "#28696e", "#173f56"]
    cmap = ListedColormap(palette)
    norm = BoundaryNorm(np.arange(-.5, 5.5), cmap.N)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.82), sharex=True, sharey=True)
    fig.subplots_adjust(left=.102, right=.99, top=.86, bottom=.25, wspace=.16)
    for policy, ax, title in zip(("A", "B"), axes, ("A  Economic allocation", "B  Supply priority")):
        cells = grid[grid.policy == policy].pivot(index="price", columns="offtake_t_day", values="modules")
        ax.pcolormesh(cells.columns, cells.index, cells.to_numpy(), cmap=cmap, norm=norm, shading="nearest")
        ax.scatter([10], [C["A_joint"]["price_H2"]], s=54, marker="D", facecolor="#ffcb79", edgecolor=INK, linewidth=.9, zorder=4)
        ax.set(title=title, xlim=(0, 30), ylim=(0, 16), xticks=[0, 5, 10, 15, 20, 25, 30], yticks=[0, 4, 8, 12, 16],
               xlabel="Daily offtake limit (t)")
        ax.title.set_fontsize(10)
    axes[0].set_ylabel("Hydrogen netback (£2020/kg)")
    handles = [Patch(color=palette[k], label=f"{20*k} MW") for k in range(5)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.55, .005), frameon=False,
               ncol=5, fontsize=8.5)
    fig.savefig(FIG / "contract_map.png", dpi=240)
    plt.close(fig)


def fonts():
    font_dir = Path("C:/Windows/Fonts")
    for name, filename in (("Report", "arial.ttf"), ("ReportBold", "arialbd.ttf"),
                           ("ReportItalic", "ariali.ttf"), ("ReportBoldItalic", "arialbi.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily("Report", normal="Report", bold="ReportBold", italic="ReportItalic", boldItalic="ReportBoldItalic")


def report():
    fonts()
    story, md = [], []
    col = colors.HexColor
    regular = ParagraphStyle("body", fontName="Report", fontSize=10.2, leading=14.0, textColor=col(INK), spaceAfter=6)
    small = ParagraphStyle("small", parent=regular, fontSize=8.5, leading=11, textColor=col(GRAY), spaceAfter=5)
    heading = ParagraphStyle("heading", fontName="ReportBold", fontSize=15, leading=18, textColor=col(INK), spaceAfter=9)
    title = ParagraphStyle("title", parent=heading, fontSize=24, leading=28, spaceAfter=7)
    section = ParagraphStyle("section", parent=heading, fontSize=10.8, leading=13.5, textColor=col(TEAL), spaceBefore=6, spaceAfter=4)
    eq = ParagraphStyle("equation", parent=regular, leftIndent=12, fontSize=10.1, leading=13, spaceAfter=3)
    table_style = ParagraphStyle("cell", parent=regular, fontSize=9.2, leading=11.3, spaceAfter=0)
    right_cell = ParagraphStyle("right cell", parent=table_style, alignment=TA_RIGHT)
    table_head = ParagraphStyle("table head", parent=table_style, textColor=colors.white, fontName="ReportBold")
    band = ParagraphStyle("band", parent=regular, fontSize=10.6, leading=14.4, spaceAfter=0)

    def plain(value):
        return re.sub(r"</?i>", "*", re.sub(r"</?b>", "**", str(value))).replace("<br/>", " ").replace("&amp;", "&")

    def p(s, style=regular):
        story.append(Paragraph(s, style))
        md.extend([plain(s), ""])

    def head(s, level=2, style=heading):
        story.append(Paragraph(s, style))
        md.extend(["#" * level + " " + plain(s), ""])

    def callout(s):
        box = Table([[Paragraph(s, band)]], colWidths=[WIDTH])
        box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col(PALE)),
                                 ("LINEBEFORE", (0, 0), (0, 0), 2.4, col(TEAL)),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                 ("TOPPADDING", (0, 0), (-1, -1), 8),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        story.extend([box, Spacer(1, 7)])
        md.extend(["> " + plain(s), ""])

    def table(headers, rows, widths, numeric=()):
        body = [[Paragraph(str(x), table_head) for x in headers]]
        body += [[Paragraph(str(x), right_cell if j in numeric else table_style) for j, x in enumerate(row)] for row in rows]
        t = Table(body, colWidths=[WIDTH * x for x in widths], hAlign="LEFT", repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), col(INK)),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, col("#f2f6f8")]),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                               ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("LINEBELOW", (0, -1), (-1, -1), .55, col(RULE))]))
        story.extend([t, Spacer(1, 7)])
        md.extend(["| " + " | ".join(headers) + " |", "| " + " | ".join("---:" if j in numeric else "---" for j in range(len(headers))) + " |"])
        md.extend("| " + " | ".join(plain(x) for x in row) + " |" for row in rows)
        md.append("")

    def image(name, height, caption):
        story.append(Image(str(FIG / name), width=WIDTH, height=height))
        p(caption, small)
        md.extend([f"![{plain(caption)}](figures/{name})", ""])

    def page():
        story.append(PageBreak())

    a, z = C["A_joint"], C["A_zero"]
    s = S["cashflow_20MW"]["A_2023"]
    head("Tier 1. Investment in flexibility", 1, title)
    p("MMCS final project  |  Group 15  |  Technical report section", small)
    callout(f"<b>2023 investment decision.</b> With economic dispatch and a buyer taking up to 10 t/day at £7.799/kg, add 20 MW of electrolysis and no battery for an annual gain of £{a['net']:.2f}m. Under daily electricity priority, add neither. Verify the buyer's terms and the operator's freedom to redirect electricity before committing capital.")
    head("1. System boundary and opportunity")
    p("We use the brief's constructed system [1]. Daily supply combines reported generation and the separately provided simulated wind farm. Demand limits total electricity sales. Existing generation is fixed, electricity imports are excluded, and unused energy has zero value. The objective is incremental project value against the same policy's zero-investment schedule. A wind-farm-only boundary is tested in Section 4.")
    p(f"Repaired input v2 contains {S['days']:,} aligned days from January 2020 to September 2026 [2]. Fuel components reconcile to reported generation. Daily mean MW is multiplied by 24 h. Prices use the repaired £/MWh series, deflated by monthly CPI. The price repair excludes zero-volume records that previously depressed the wholesale series. Design uses all {S['design_days']} days of 2023.")
    image("surplus.png", WIDTH * 2.22 / 7.2,
          f"<b>Figure 1.</b> 2023 surplus duration. Only {S['surplus_days']} days have a positive physical surplus. Their total is {S['surplus_GWh']:.2f} GWh and their median is {S['median_surplus_day_GWh']:.2f} GWh. All {365-S['surplus_days']} other days have zero surplus and are omitted from this logarithmic plot.")
    head("Reference assumptions in 2020 pounds", 3, section)
    table(["Input", "Assumption used"], [
        ("Battery", "1.5 MW / 3 MWh modules, 20-80% state of charge, 90% round-trip efficiency, £256k/MWh installed, £14.9k/MW-year fixed costs, 15-year life."),
        ("Electrolyser", "20 MW modules, 20-100% online loading, 55.9 kWh/kg. £29.21m per module, £0.52m/year fixed costs, £9.79m stack proxy in years 11 and 22, 30-year life."),
        ("Economics", "5% real discount rate. £7.799/kg netback with a 10 t/day offtake limit is a policy-supported reference scenario. Market terms and access to support remain investment conditions.")], [.22, .78])
    p("Installed electrolyser cost uses the converted midpoint of the IEA benchmark. Fixed operating and stack costs use separate UK legacy proxies. The underlying cost ranges and conversion assumptions are documented in [3].", small)

    page()
    head("2. Investment model and matched comparison")
    p("Choose integer battery and electrolyser counts <i>b</i> and <i>n</i>. For day <i>t</i>, let <i>q</i>, <i>c</i>, <i>r</i> and <i>h</i> denote direct sale, charge, discharge and electrolysis input in MWh. Supply is <i>G</i> and demand is <i>D</i>. <i>z</i> counts online electrolyser modules and <i>L</i> caps daily hydrogen sales in kg. The core mixed-integer linear program is implemented in Python/FICO Xpress.")
    p("Maximise Σ<sub>t</sub>[p<sub>t</sub>(q<sub>t</sub> + r<sub>t</sub>) + vh<sub>t</sub>/0.0559] − a<sub>B</sub>b − a<sub>H</sub>n.", eq)
    p("q<sub>t</sub> + c<sub>t</sub> + h<sub>t</sub> ≤ G<sub>t</sub> &nbsp;&nbsp; and &nbsp;&nbsp; q<sub>t</sub> + r<sub>t</sub> ≤ D<sub>t</sub>.", eq)
    p("96z<sub>t</sub> ≤ h<sub>t</sub> ≤ 480z<sub>t</sub>, &nbsp; z<sub>t</sub> integer, &nbsp; 0 ≤ z<sub>t</sub> ≤ n, &nbsp; h<sub>t</sub>/0.0559 ≤ L.", eq)
    p("c<sub>t</sub> ≤ 1.8b/η, &nbsp; r<sub>t</sub> ≤ 1.8bη, &nbsp; Σr<sub>t</sub> = 0.90Σc<sub>t</sub>, &nbsp; η = √0.90.", eq)
    p("In the annual objective, <i>p</i> is £/MWh, <i>v</i> is £/kg, and <i>a</i><sub>B</sub>, <i>a</i><sub>H</sub> are annualised costs per module. Policy <b>A</b> allows economic allocation. Policy <b>B</b> fixes direct sales to min(G, D), including on negative-price days. Flows are nonnegative. The Tier 1 annual pool relaxes the ordering of storage transfers. Fixed battery schedules are checked with chronological stock and empty initial and terminal usable inventory.")
    rows = []
    for label, key in (("No investment", "zero"), ("Battery only", "battery"), ("Hydrogen only", "hydrogen"), ("Joint choice", "joint"), ("Fixed reference module", "fixed20_2023")):
        rows.append([label, *[v for policy in ("A", "B") for v in (f"{C[f'{policy}_{key}']['battery_MW']:g} / {C[f'{policy}_{key}']['h2_MW']:g}", f"{C[f'{policy}_{key}']['net']:+.2f}")]])
    table(["2023 portfolio", "A BESS/H<sub>2</sub> MW", "A Δ £m/yr", "B BESS/H<sub>2</sub> MW", "B Δ £m/yr"], rows, [.30, .19, .16, .19, .16], (1, 2, 3, 4))
    p("<b>Table 1.</b> BESS denotes battery energy storage system. Gains use the policy-matched zero-investment reference and equivalent annual costs, in 2020 pounds.", small)
    p(f"The same 20 MW module run by a simple sale-first rule loses £{abs(C['A_simple20_2023']['net']):.2f}m/year in 2023. Optimising its use in A improves the result by £{a['net']-C['A_simple20_2023']['net']:.2f}m/year. Both use the same day data and capital cost. With no battery, this improvement comes from how today's power is allocated.")
    head("Battery economics and physical check", 3, section)
    bound = S["battery_bounds"]["A_2023"]
    p(f"Without a sales floor, removing a battery leaves direct sales and hydrogen feasible and deletes only its discharge revenue. At full discharge every positive-price day, even free charging yields at most £{1000*bound['free_charge_revenue_ceiling']:.1f}k per module in 2023, below its £{1000*bound['annual_cost']:.1f}k annual cost. This rules out storage in A and B in 2023-25 under the daily throughput assumption.")
    p(f"Forcing one module in A earns £{CHECK['battery']['gross_pool_GBP']/1000:.1f}k in extra operating revenue after charging in the annual pool, or £{CHECK['battery']['gross_stock_GBP']/1000:.1f}k with chronological stock. The stock result falls below even the lower fixed-cost assumption of £11.1k/year per module. These daily cases leave intraday and ancillary services for separate analysis.")

    page()
    head("3. What changes the investment decision?")
    p(f"In A, the selected electrolyser consumes {a['h2_GWh']:.2f} GWh and produces {a['h2_tonnes']:,.0f} t of hydrogen. Relative to no investment, {a['unused_reduction_GWh']:.2f} GWh comes from reduced unused electricity and {a['displacement_GWh']:.2f} GWh from displaced direct sales. Only {a['capture_GWh']/a['h2_GWh']:.1%} of the input can be assigned to physical surplus under a surplus-first convention, capturing {a['capture_GWh']/S['surplus_GWh']:.2%} of annual surplus.")
    p(f"Daily fuel totals allow {a['renewable_capture_low_GWh']:.0f}-{a['renewable_capture_high_GWh']:.2f} GWh of the captured surplus to come from wind and solar, depending on allocation. Including biomass and run-of-river hydro leaves that interval unchanged. Verifying the renewable share requires tracing the source of the electricity used.")
    image("contract_map.png", WIDTH * 2.82 / 7.2,
          "<b>Figure 2.</b> 2023 investment trigger map. Each cell selects the number of 20 MW modules with greatest annual gain, including zero. Gold diamonds mark the reference netback and offtake limit. Positive-price sellable electricity carries its full opportunity cost.")
    x = S["hydrogen_crossings"]
    next_size = CHECK["size_cases"]["A_10000"][2]
    expansion = CHECK["size_cases"]["A_50000"][-1]
    p(f"At 10 t/day, the break-even netback for 20 MW is £{x['A_2023']:.2f}/kg in A and £{x['B_2023']:.2f}/kg in B. In A a second module can sell more hydrogen, yet cuts gain to £{next_size['gain']:.2f}m/year. At 50 t/day, A selects {expansion['MW']} MW and gains £{expansion['gain']:.2f}m/year on £{expansion['capital']:.2f}m of initial capital. Expansion depends on securing the larger contract.")
    head("Price of retaining electricity sales", 3, section)
    base = CHECK["sales_base_GWh"]
    service_rows = [
        [f"{100*(1-r['displacement_GWh']/base):.4f}%", f"{r['displacement_GWh']:.2f}",
         f"{r['h2_MW']:g}", f"{r['net']:+.2f}"]
        for r in (a, C["A_service_50"])
    ]
    service_rows.extend(
        [f"{r['floor_pct']:.4f}%", f"{r['sales_given_up']:.2f}", f"{r['h2_MW']:g}", f"{r['gain']:+.2f}"]
        for r in CHECK["floors"]
    )
    table(["Minimum sales retained", "Sales given up (GWh)", "H<sub>2</sub> MW", "Δ £m/year"], service_rows, [.40, .26, .13, .21], (1, 2, 3))
    p(f"<b>Table 2.</b> Retention is relative to the {base/1000:.1f} TWh sold without investment. Retaining half of the 157.92 GWh diverted by free dispatch preserves £5.19m/year. These annual floors let the operator choose which days to preserve sales. Policy B gives electricity priority each day.", small)

    page()
    head("4. Robustness and investment recommendation")
    p("A fixed 20 MW module is evaluated on each historical year at identical cost and offtake assumptions. The site boundary assigns background generation first to demand, makes only residual demand available to the wind farm and restricts device input to its wind output. These are matched incremental comparisons within each boundary.")
    yearly = [[str(y), f"{C[f'A_fixed20_{y}']['net']:+.2f}", f"{C[f'B_fixed20_{y}']['net']:+.2f}"] for y in (2022, 2023, 2024, 2025)]
    yearly += [["2025, £4/kg and 5 t/day", f"{C['A_fixed20_downside']['net']:+.2f}", f"{C['B_fixed20_downside']['net']:+.2f}"],
               ["2023, wind site boundary", f"{C['A_site_fixed20_2023']['net']:+.2f}", f"{C['B_site_fixed20_2023']['net']:+.2f}"]]
    table(["Fixed 20 MW replay", "A Δ £m/year", "B Δ £m/year"], yearly, [.58, .21, .21], (1, 2))
    p(f"B's 2025 break-even netback falls to £{x['B_2025']:.2f}/kg at 10 t/day as surplus opportunities increase. The 2025 contract downside reverses both investment cases. A's 2023 gain remains £{C['A_fixed20_cost_stress']['net']:.2f}m/year at 25% higher installed cost and an 8% real discount rate. Reoptimising the {S['strict_design_days']} strict-quality days retains the 2023 capacity choices. Fixed-capacity replays assess performance on known historical conditions.")
    head("Cash flow of the 2023 economic case", 3, section)
    table(["Annual component", "£2020m/year"], [
        ["Hydrogen netback receipts", f"+{a['hydrogen_value']:.2f}"],
        ["Foregone direct electricity receipts", f"{a['direct_change']:.2f}"],
        ["Fixed operating cost", f"−{S['hydrogen_fixed_opex']:.2f}"],
        ["Equivalent cost of initial capital and stack renewals", f"−{a['annual_cost']-S['hydrogen_fixed_opex']:.2f}"],
        ["Equivalent incremental gain", f"+{a['net']:.2f}"]], [.74, .26], (1,))
    p(f"Against £29.21m paid upfront, £{s['annual_operating_cash']:.2f}m annual operating cash flow gives simple payback in {s['simple_payback']:.2f} years, or {s['discounted_payback']:.2f} years at 5% real discount. Repeating 2023 operating cash flow for 30 years, with stack renewals in years 11 and 22 and zero terminal value, gives £{s['npv']:.2f}m net present value.")
    callout("<b>Client action.</b> Retain the current assets while verifying delivered hydrogen netback, daily acceptance and electricity sales obligations. Consider one 20 MW module if the agreed terms clear the corresponding contract boundary and the site can supply it. Evaluate a battery only when an additional paid service or a different throughput and cost basis can bridge the quantified revenue gap.")
    p(f"<b>Validation.</b> {S['checks']['xpress_schedules']} optimal Xpress schedules and two rule schedules reconcile flows and cash within 0.001 MWh for the physical checks. Eight trigger cells, the two sizing cases and the sales floors were checked with Xpress. An independent implementation agrees on all {len(CHECK['comparable_cases'])} matched capacities and gains to the precision of its published table.", small)
    p("<b>Sources.</b> [1] MMCS 2026/27 Project Brief, pp. 2-3, 5-6, and project briefing. [2] Course datasets, repaired release 20261104-v2 and its audit, with ONS monthly CPI D7BT. [3] Danish Energy Agency storage catalogue, IEA <i>Global Hydrogen Review 2025</i>, BEIS <i>Hydrogen Production Costs 2021</i> and DESNZ HAR1 results, as transcribed and converted in the project R2-R4 parameter research.", small)

    def footer(canvas, doc):
        canvas.setStrokeColor(col(RULE))
        canvas.line(45, 37, A4[0]-45, 37)
        canvas.setFont("Report", 8)
        canvas.setFillColor(col(GRAY))
        canvas.drawString(45, 23, "MMCS 2026/27  |  Group 15  |  Tier 1")
        canvas.drawRightString(A4[0]-45, 23, str(doc.page))

    document = SimpleDocTemplate(str(OUT / "Tier1_Report.pdf"), pagesize=A4, leftMargin=39, rightMargin=39,
                                 topMargin=41, bottomMargin=49, title="Tier 1. Investment in flexibility",
                                 author="MMCS Group 15", pageCompression=1)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    (OUT / "Tier1_Report.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    figures()
    report()
