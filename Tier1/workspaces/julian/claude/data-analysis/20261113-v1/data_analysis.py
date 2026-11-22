"""
MMCS project - data cleaning and exploratory analysis.

Usage:  python data_analysis.py [DATA_DIR] [OUT_DIR]
        DATA_DIR holds the five supplied CSVs (default: this folder or the nearest parent
                 folder that has them; in the group repository that is the repository root)
        OUT_DIR  receives clean_daily.csv, summary.txt and the figures (default: ./results)

All power columns are DAILY AVERAGE MW. Energy in MWh = MW * 24.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def _find_data() -> Path:
    for d in (HERE, *HERE.parents):
        if (d / "daily_demand.csv").exists() and (d / "wind_farm_generation.csv").exists():
            return d
    raise SystemExit("Supplied CSVs not found. Pass their folder: python data_analysis.py DATA_DIR [OUT_DIR]")


DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_data()
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "results"
OUT.mkdir(parents=True, exist_ok=True)

START, END = "2020-01-01", "2026-09-17"
FARM_CAPACITY_MW = 75 * 15          # from farm_generator.py (75 turbines x 15 MW)
RENEWABLES = ["Wind Offshore", "Wind Onshore", "Solar",
              "Hydro Run-of-river and poundage"]

# ---------------------------------------------------------------- style
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "ytick.major.size": 0, "lines.linewidth": 2, "figure.dpi": 110,
    "legend.frameon": False,
})


def save(fig, name):
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 1. load
dem = pd.read_csv(DATA / "daily_demand.csv")
dem["date"] = pd.to_datetime(dem["startTime"]).dt.tz_localize(None).dt.normalize()
dem = dem.set_index("date")["demand"].rename("demand_MW")

fuel = pd.read_csv(DATA / "daily_generation_by_fuel.csv", parse_dates=["date"])
fuel = fuel.pivot_table(index="date", columns="psrType", values="MW", aggfunc="sum")

tot = pd.read_csv(DATA / "daily_generation_total.csv", parse_dates=["date"]).set_index("date")["total_MW"]
price = pd.read_csv(DATA / "daily_market_index_price.csv", parse_dates=["date"]).set_index("date").iloc[:, 0].rename("price_GBP_MWh")
farm = pd.read_csv(DATA / "wind_farm_generation.csv", parse_dates=["date"]).set_index("date")["wind_farm_MW"]

log = []
def note(s):
    print(s); log.append(s)

note("== RAW DATA ==")
idx = pd.date_range(START, END, freq="D")
for name, s in [("demand", dem), ("generation by fuel", fuel), ("generation total", tot),
                ("price", price), ("wind farm", farm)]:
    note(f"{name:20s} rows={len(s):5d}  {s.index.min().date()} -> {s.index.max().date()}  "
         f"missing days={len(idx.difference(s.index))}")
note(f"total_MW equals sum of fuels on every common day: "
     f"{bool((tot - fuel.sum(axis=1).reindex(tot.index)).abs().max() < 1e-6)}")

# ---------------------------------------------------------------- 2. clean
df = pd.DataFrame(index=idx)
df.index.name = "date"
df = df.join(dem).join(price).join(farm).join(fuel)
df["total_MW"] = df[fuel.columns].sum(axis=1, min_count=1)

note("\n== CLEANING ==")
# demand: one missing day and one obvious recording error
bad_dem = df["demand_MW"] < 10000
note(f"demand: {int(df['demand_MW'].isna().sum())} missing day, {int(bad_dem.sum())} outlier "
     f"({', '.join(f'{d.date()}={int(v)} MW' for d, v in df.loc[bad_dem, 'demand_MW'].items())}) -> linear interpolation")
df["demand_imputed"] = df["demand_MW"].isna() | bad_dem
df.loc[bad_dem, "demand_MW"] = np.nan
df["demand_MW"] = df["demand_MW"].interpolate("time")

# price: missing days -> linear interpolation (gaps are at most a few days)
df["price_imputed"] = df["price_GBP_MWh"].isna()
gap = df["price_imputed"].groupby((~df["price_imputed"]).cumsum()).sum().max()
note(f"price: {int(df['price_imputed'].sum())} missing days (longest gap {int(gap)} days) -> linear interpolation")
df["price_GBP_MWh"] = df["price_GBP_MWh"].interpolate("time")

# generation: (a) days absent from the file, (b) days where the non-weather-dependent fleet
# (gas, nuclear, biomass, hydro, other) is reported as zero / near zero while wind and solar are present.
# Rule: non-wind/solar output is zero, OR total < 70% of demand while nuclear (a steady baseload source)
# is below 70% of its 61-day median. These are reporting gaps, not real system states -> flag, do not use total_MW on these days.
df["gen_missing"] = df["Wind Onshore"].isna()
firm = df["total_MW"] - df[["Wind Offshore", "Wind Onshore", "Solar"]].sum(axis=1)
nuc_ref = df["Nuclear"].where(df["Nuclear"] > 0).rolling(61, center=True, min_periods=10).median()
partial = (df["total_MW"] < 0.7 * df["demand_MW"]) & (df["Nuclear"] < 0.7 * nuc_ref)   # only part of the day reported
df["gen_incomplete"] = (~df["gen_missing"]) & ((firm <= 0) | partial)
df["gen_valid"] = ~(df["gen_missing"] | df["gen_incomplete"])
note(f"generation: {int(df['gen_missing'].sum())} days absent; {int(df['gen_incomplete'].sum())} days where "
     f"gas/nuclear/biomass/hydro are reported as (near) zero -> flagged gen_incomplete, total_MW not usable")
inc = df.index[df["gen_incomplete"]]
blocks = pd.Series(inc).groupby((pd.Series(inc).diff().dt.days > 3).cumsum()).agg(["min", "max", "count"])
for _, b in blocks.iterrows():
    note(f"    incomplete block {b['min'].date()} -> {b['max'].date()} ({b['count']} days)")
note(f"    'Fossil Oil' is zero on every day; 'Fossil Hard coal' is zero from "
     f"{df.index[(df['Fossil Hard coal'] > 0)].max().date()} onward (coal closure, real)")
note(f"wind farm: no gaps; {int((df['wind_farm_MW'] == 0).sum())} zero-output days, "
     f"{int((df['wind_farm_MW'] >= FARM_CAPACITY_MW - 0.1).sum())} days at rated {FARM_CAPACITY_MW} MW")

df["renewables_MW"] = df[RENEWABLES].sum(axis=1, min_count=1)
df["wind_national_MW"] = df[["Wind Offshore", "Wind Onshore"]].sum(axis=1, min_count=1)
df["farm_cf"] = df["wind_farm_MW"] / FARM_CAPACITY_MW
df.round(3).to_csv(OUT / "clean_daily.csv")
note(f"clean table: {len(df)} days x {df.shape[1]} columns -> clean_daily.csv "
     f"({int(df['gen_valid'].sum())} days with valid system generation)")

v = df[df["gen_valid"]]          # days with a trustworthy system total
yr = df.index.year

# ---------------------------------------------------------------- 3. numbers
note("\n== KEY NUMBERS ==")
note(f"demand         mean {df.demand_MW.mean():,.0f} MW   min {df.demand_MW.min():,.0f}   max {df.demand_MW.max():,.0f}")
note(f"wind farm      mean {df.wind_farm_MW.mean():,.0f} MW   capacity factor {df.farm_cf.mean():.1%}   "
     f"annual energy {df.wind_farm_MW.mean() * 8760 / 1e3:,.0f} GWh")
note(f"price          mean {df.price_GBP_MWh.mean():.1f}  median {df.price_GBP_MWh.median():.1f}  "
     f"max {df.price_GBP_MWh.max():.0f}  days<0: {int((df.price_GBP_MWh < 0).sum())}  days<20: {int((df.price_GBP_MWh < 20).sum())}")
capture = (df.wind_farm_MW * df.price_GBP_MWh).sum() / df.wind_farm_MW.sum()
note(f"wind farm capture price {capture:.1f} GBP/MWh = {capture / df.price_GBP_MWh.mean():.1%} of the time-average price")
note(f"wind farm merchant revenue ~ {(df.wind_farm_MW * 24 * df.price_GBP_MWh).groupby(yr).sum().loc[2021:2025].mean() / 1e6:,.0f} m GBP/yr (2021-25 mean)")
note(f"farm share of national demand: {df.wind_farm_MW.mean() / df.demand_MW.mean():.2%}")
note(f"valid days: system generation > demand on {int((v.total_MW > v.demand_MW).sum())} of {len(v)} days "
     f"({(v.total_MW > v.demand_MW).mean():.1%}); renewables > demand on {int((v.renewables_MW > v.demand_MW).sum())} days")
note(f"renewable share of demand: mean {(v.renewables_MW / v.demand_MW).mean():.1%}, max {(v.renewables_MW / v.demand_MW).max():.1%}")

annual = pd.DataFrame({
    "demand_MW": df.demand_MW.groupby(yr).mean(),
    "total_gen_MW(valid)": v.total_MW.groupby(v.index.year).mean(),
    "renew_share_of_demand": (v.renewables_MW.groupby(v.index.year).mean() / v.demand_MW.groupby(v.index.year).mean()),
    "farm_MW": df.wind_farm_MW.groupby(yr).mean(),
    "farm_CF": df.farm_cf.groupby(yr).mean(),
    "price": df.price_GBP_MWh.groupby(yr).mean(),
    "price_std": df.price_GBP_MWh.groupby(yr).std(),
}).round(3)
note("\nAnnual means (2026 = Jan-Sep only):\n" + annual.to_string())

corr = df[["demand_MW", "wind_farm_MW", "wind_national_MW", "Solar", "price_GBP_MWh"]].corr().round(2)
note("\nCorrelation (daily):\n" + corr.to_string())
note(f"\nwind farm autocorrelation: lag1 {df.wind_farm_MW.autocorr(1):.2f}, lag2 {df.wind_farm_MW.autocorr(2):.2f}, "
     f"lag7 {df.wind_farm_MW.autocorr(7):.2f}")
wk = df.demand_MW.groupby(df.index.dayofweek).mean()
note(f"demand weekday effect: weekend is {1 - wk[[5, 6]].mean() / wk[:5].mean():.1%} below weekdays")


def spells(mask):
    grp = (mask != mask.shift()).cumsum()
    return mask.groupby(grp).agg(["first", "size"]).query("first")["size"]

low, high = spells(df.farm_cf < 0.10), spells(df.farm_cf > 0.70)
note(f"\nlow-wind spells (farm CF<10%): {int((df.farm_cf < 0.10).sum())} days in {len(low)} spells, "
     f"mean {low.mean():.1f} d, longest {low.max()} d, spells >=3 d: {int((low >= 3).sum())}")
note(f"high-wind spells (farm CF>70%): {int((df.farm_cf > 0.70).sum())} days in {len(high)} spells, "
     f"mean {high.mean():.1f} d, longest {high.max()} d, spells >=3 d: {int((high >= 3).sum())}")

# surplus under the 'scaled demand' definition: client demand = k * national demand,
# k chosen so that the farm's mean output covers a given fraction r of the client's mean demand.
note("\n'Surplus' when the client's demand is national demand scaled so that the farm covers a share r of it on average:")
rows = []
for r in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
    k = df.wind_farm_MW.mean() / (r * df.demand_MW.mean())
    d = k * df.demand_MW
    sur, sho = (df.wind_farm_MW - d).clip(lower=0), (d - df.wind_farm_MW).clip(lower=0)
    rows.append({"r": r, "client_mean_demand_MW": d.mean(), "surplus_days_%": (sur > 0).mean() * 100,
                 "surplus_GWh_per_yr": sur.mean() * 8.76, "surplus_%_of_farm_output": sur.sum() / df.wind_farm_MW.sum() * 100,
                 "shortfall_GWh_per_yr": sho.mean() * 8.76, "p95_surplus_MW": sur.quantile(0.95), "max_surplus_MW": sur.max(),
                 "longest_surplus_spell_d": spells(sur > 0).max()})
surplus_tab = pd.DataFrame(rows).set_index("r").round(1)
note(surplus_tab.to_string())
(OUT / "summary.txt").write_text("\n".join(log), encoding="utf-8")

# ---------------------------------------------------------------- 4. figures
# Fig 1 - overview (small multiples, shared time axis)
fig, axs = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
tv = df.total_MW.where(df.gen_valid)
panels = [("Demand (GW)", df.demand_MW / 1e3, BLUE), ("System generation, valid days only (GW)", tv / 1e3, AQUA),
          ("Client wind farm output (MW)", df.wind_farm_MW, VIOLET), ("Market index price (£/MWh)", df.price_GBP_MWh, ORANGE)]
for ax, (ttl, s, c) in zip(axs, panels):
    ax.plot(s.index, s, color=c, lw=0.6, alpha=0.35)
    ax.plot(s.index, s.rolling(30, center=True, min_periods=10).mean(), color=c, lw=2)
    ax.set_title(ttl); ax.set_ylim(bottom=min(0, s.min()))
axs[0].text(1, 1.04, "thin: daily   bold: 30-day mean", transform=axs[0].transAxes, ha="right", color=MUTED, fontsize=9)
save(fig, "fig1_overview.png")

# Fig 2 - generation mix by year (valid days)
groups = {"Gas": ["Fossil Gas"], "Nuclear": ["Nuclear"], "Wind offshore": ["Wind Offshore"], "Wind onshore": ["Wind Onshore"],
          "Solar": ["Solar"], "Biomass": ["Biomass"], "Other": ["Fossil Hard coal", "Fossil Oil", "Hydro Pumped Storage",
                                                               "Hydro Run-of-river and poundage", "Other"]}
gcol = {"Gas": ORANGE, "Nuclear": VIOLET, "Wind offshore": BLUE, "Wind onshore": AQUA, "Solar": YELLOW, "Biomass": GREEN, "Other": MUTED}
mix = pd.DataFrame({g: v[c].sum(axis=1).groupby(v.index.year).mean() for g, c in groups.items()}) / 1e3
fig, ax = plt.subplots(figsize=(9, 5))
bottom = np.zeros(len(mix))
for g in mix.columns:
    ax.bar(mix.index.astype(str), mix[g], bottom=bottom, color=gcol[g], width=0.62, edgecolor=SURFACE, linewidth=2, label=g)
    for x, (b, h) in enumerate(zip(bottom, mix[g])):
        if h > 1.6:
            ax.text(x, b + h / 2, f"{h:.1f}", ha="center", va="center", fontsize=8.5, color=INK if g == "Solar" else "white")
    bottom += mix[g].values
ax.plot(mix.index.astype(str), v.demand_MW.groupby(v.index.year).mean() / 1e3, color=INK, lw=0, marker="_", ms=34, mew=2)
ax.plot([], [], color=INK, lw=2, label="Mean demand")
ax.set_title("Average generation by technology (GW, days with complete data; 2026 = Jan–Sep)")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.07), fontsize=9)
save(fig, "fig2_generation_mix.png")

# Fig 3 - seasonality (small multiples)
mth = df.index.month
labels = list("JFMAMJJASOND")
fig, axs = plt.subplots(1, 4, figsize=(13, 3.4))
for ax, (ttl, s, c) in zip(axs, [("Demand (GW)", df.demand_MW / 1e3, BLUE), ("Wind farm capacity factor", df.farm_cf, VIOLET),
                                 ("National solar (GW)", df.Solar / 1e3, YELLOW), ("Price (£/MWh), median", df.price_GBP_MWh, ORANGE)]):
    m = s.groupby(mth).median() if "median" in ttl else s.groupby(mth).mean()
    ax.bar(range(1, 13), m.reindex(range(1, 13)), color=c, width=0.7)
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(labels)
    ax.set_title(ttl)
fig.suptitle("Monthly profile, 2020–2026", x=0.01, ha="left", fontweight="bold", y=1.04)
save(fig, "fig3_seasonality.png")

# Fig 4 - wind farm: distribution and duration curve
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
axs[0].hist(df.farm_cf, bins=np.linspace(0, 1, 21), color=VIOLET, edgecolor=SURFACE, linewidth=1.5)
axs[0].axvline(df.farm_cf.mean(), color=INK, lw=1.2, ls="--")
axs[0].text(df.farm_cf.mean() + 0.015, axs[0].get_ylim()[1] * 0.93, f"mean {df.farm_cf.mean():.0%}", color=INK2)
axs[0].set_title("Wind farm daily capacity factor (days)"); axs[0].set_xlabel("capacity factor")
dur = df.wind_farm_MW.sort_values(ascending=False).values
axs[1].plot(np.arange(len(dur)) / len(dur) * 100, dur, color=VIOLET)
axs[1].set_title("Wind farm duration curve (MW)"); axs[1].set_xlabel("% of days output is exceeded")
axs[1].set_ylim(0); axs[1].set_xlim(0, 100)
save(fig, "fig4_wind_farm_profile.png")

# Fig 5 - price vs national wind output
q = pd.qcut(v.wind_national_MW / v.demand_MW, 10)
pm = v.price_GBP_MWh.groupby(q, observed=True).median()
fq = pd.qcut(df.farm_cf, 5)
fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
axs[0].bar([f"{i.left:.0%}–{i.right:.0%}" for i in pm.index], pm, color=ORANGE, width=0.7)
axs[0].set_title("Median price by national wind share of demand (£/MWh)")
axs[0].tick_params(axis="x", labelrotation=45, labelsize=8); axs[0].set_xlabel("wind as share of demand (deciles)")
fm = df.price_GBP_MWh.groupby(fq, observed=True).median()
axs[1].bar([f"{max(i.left, 0):.0%}–{i.right:.0%}" for i in fm.index], fm, color=ORANGE, width=0.6)
axs[1].set_title("Median price by client wind farm capacity factor"); axs[1].set_xlabel("farm capacity factor (quintiles)")
save(fig, "fig5_price_vs_wind.png")

# Fig 6 - spell lengths
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, s, ttl, c in [(axs[0], low, "Low-wind spells (farm CF < 10%)", RED), (axs[1], high, "High-wind spells (farm CF > 70%)", BLUE)]:
    cnt = s.clip(upper=7).value_counts().reindex(range(1, 8), fill_value=0)
    ax.bar([str(i) if i < 7 else "7+" for i in cnt.index], cnt, color=c, width=0.65)
    for x, h in enumerate(cnt):
        ax.text(x, h + 2, str(h), ha="center", fontsize=9, color=INK2)
    ax.set_title(f"{ttl}: number of spells"); ax.set_xlabel("consecutive days")
save(fig, "fig6_wind_spells.png")

# Fig 7 - how the 'surplus' depends on the demand-scaling assumption
rs = np.linspace(0.4, 2.5, 43)
share, days = [], []
for r in rs:
    d = df.wind_farm_MW.mean() / (r * df.demand_MW.mean()) * df.demand_MW
    sur = (df.wind_farm_MW - d).clip(lower=0)
    share.append(sur.sum() / df.wind_farm_MW.sum() * 100); days.append((sur > 0).mean() * 100)
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
axs[0].plot(rs, share, color=BLUE); axs[0].set_title("Surplus as % of wind farm output")
axs[1].plot(rs, days, color=BLUE); axs[1].set_title("% of days with a surplus")
for ax in axs:
    ax.set_xlabel("farm mean output ÷ client mean demand"); ax.set_ylim(0); ax.axvline(1, color=AXIS, lw=1, ls="--")
save(fig, "fig7_surplus_vs_scaling.png")
print("\nDone ->", OUT)
