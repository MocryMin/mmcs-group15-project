"""Validate the completed cuts and render the investment boundary."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FixedLocator, NullFormatter
import pandas as pd

from envelope import GAP_POINTS, ROOT, economics, max_gap_factor


def collect():
    gaps = [*GAP_POINTS, max_gap_factor()]
    cases = [
        json.loads((ROOT / "cases" / f"{policy}_{gap:.10g}.json").read_text(encoding="utf-8"))
        for policy in "AB" for gap in gaps
    ]
    cuts = pd.DataFrame(case["boundary"] for case in cases)
    points = pd.DataFrame(point for case in cases for point in case["points"])
    assert len(cuts) == 2 * len(gaps)
    assert not points.duplicated(["policy", "gap_std_multiplier", "price_std_multiplier"]).any()
    assert (points["net_lower_GBP_year"] <= points["net_upper_GBP_year"]).all()
    assert ((points["net_upper_GBP_year"] - points["net_lower_GBP_year"]) < 401).all()
    for case in cases:
        cut = case["boundary"]
        if cut["entry_certified"]:
            tested = {p["price_std_multiplier"]: p for p in case["points"]}
            assert tested[cut["price_entry_upper"]]["net_lower_GBP_year"] > 0
            assert cut["price_entry_upper"] - cut["price_entry_lower"] <= .125
            if cut["price_entry_lower"] != cut["price_entry_upper"]:
                assert tested[cut["price_entry_lower"]]["net_upper_GBP_year"] <= 0
    return cuts, points


def plot(cuts):
    font_manager.fontManager.addfont("C:/Windows/Fonts/Deng.ttf")
    matplotlib.rcParams.update({
        "font.family": font_manager.FontProperties(fname="C:/Windows/Fonts/Deng.ttf").get_name(),
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.unicode_minus": False,
        "svg.fonttype": "path",
    })
    fig, (wide, near) = plt.subplots(1, 2, figsize=(12.3, 5.2), sharey=True,
                                   gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(left=.075, right=.98, top=.77, bottom=.21, wspace=.26)
    fig.text(.075, .935, "洞穴压缩空气储能的投资门槛", fontsize=21, color="#172b39")
    fig.text(.075, .869, "50 MW / 1.5 GWh，年化购置与固定维护 £852 万，按 2020 年不变价",
             fontsize=11, color="#465761")
    styles = {"A": ("#196b94", "o", "A  经济调度"), "B": ("#b45c21", "s", "B  供电优先")}
    for ax, cap, heading in ((wide, max_gap_factor(), "全部测试范围"), (near, 2, "接近历史供需波动")):
        selected = cuts[cuts["gap_std_multiplier"] <= cap]
        ax.set_title(heading, loc="left", pad=12, fontsize=13)
        for policy, (color, marker, label) in styles.items():
            group = selected[selected["policy"] == policy]
            lo = group["price_entry_lower"].where(group["entry_certified"])
            hi = group["price_entry_upper"].where(group["entry_certified"])
            x = group["gap_std_multiplier"]
            ax.plot(x, (lo+hi)/2, color=color, marker=marker, ms=4.3, lw=1.6, label=label)
            ax.vlines(x, lo, hi, color=color, lw=1.6)
        ax.axhline(1, color="#8d9498", linewidth=.9, linestyle="--", zorder=0)
        ax.scatter([1], [1], s=35, marker="D", facecolor="#fff", edgecolor="#333", zorder=6,
                   clip_on=False, label="历史波动")
        ax.grid(axis="y", color="#dce2e5", lw=.65)
        ax.set_axisbelow(True)
        ax.set_xlabel("供需差标准差倍率", labelpad=8)
    wide.set_ylabel("电价标准差倍率", labelpad=9)
    wide.set_xscale("log")
    wide.set_xlim(.94, max_gap_factor() * 1.08)
    wide.xaxis.set_major_locator(FixedLocator([1, 2, 4, 8, 16, max_gap_factor()]))
    wide.set_xticklabels(["1", "2", "4", "8", "16", "28.24"])
    wide.xaxis.set_minor_formatter(NullFormatter())
    wide.tick_params(axis="x", which="minor", bottom=False)
    near.set_xlim(.975, 2.04)
    near.set_xticks([1, 1.1, 1.25, 1.5, 2], ["1", "1.1", "1.25", "1.5", "2"])
    for ax in (wide, near):
        ax.set_ylim(bottom=0)
    handles, labels = wide.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(.979, .95),
               frameon=False, ncol=1, fontsize=10)
    fig.text(.075, .06, "每个标记对应一个单独求解的供需差倍率。连线连接相邻测试点。1 倍为历史标准差。",
             fontsize=10, color="#465761")
    fig.savefig(ROOT / "entry-envelope.png", dpi=180, facecolor="white")
    plt.close(fig)


def main():
    cuts, points = collect()
    cuts.to_csv(ROOT / "entry-envelope.csv", index=False)
    points.to_csv(ROOT / "scenario-points.csv", index=False)
    (ROOT / "economics.json").write_text(json.dumps(economics(), indent=2)+"\n", encoding="utf-8")
    plot(cuts)
    print(cuts[["policy", "gap_std_multiplier", "price_entry_lower", "price_entry_upper",
                "entry_certified", "historical_price_gross_GBP_year"]].to_string(index=False))
    print(f"{len(points)} sampled points")


if __name__ == "__main__":
    main()
