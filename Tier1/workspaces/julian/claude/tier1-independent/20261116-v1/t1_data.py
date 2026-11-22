"""Independent Tier 1 - data preparation from the five supplied CSVs only.

Usage:  python t1_data.py [RAW_DIR]      (default: ./raw, else the nearest parent folder with the five CSVs)
Writes: data/clean_daily.csv and data/data_quality_log.txt

Every adjustment is flagged in the output so that it can be switched off in a sensitivity run.
All power columns are daily averages in MW; daily energy in MWh = 24 x MW.

Adjustments (evidence for each is printed to the log):
  D1  demand   every 7th day (the last day of each weekly download window in get_data.py) holds a
               single early-morning reading, not a daily value -> replaced by the mean of its neighbours.
  P1  price    same weekly-window fault -> replaced by the mean of its neighbours.
  P2  price    get_data.py averages the Market Index Price over all rows, including the rows of a data
               provider that reports zero price and zero volume, which halves the average -> multiplied by 2.
  P3  price    30 missing days -> linear interpolation.
  G1  generation  30 missing days, 107 days with no thermal/nuclear/hydro at all, 18 days with a partial
               record -> the non-wind/solar part is imputed from demand and wind+solar by regression;
               wind+solar on the 30 fully missing days is imputed from the client's farm output.
  R1  prices are converted to 2023 pounds with the ONS CPI annual index (2015 = 100).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
START, END = "2020-01-01", "2026-09-17"
FARM_CAPACITY_MW = 75 * 15            # farm_generator.py: 75 turbines x 15 MW
# ONS Consumer Prices Index, all items, annual average, 2015 = 100 (series D7BT). 2026 is held at 2025.
CPI = {2020: 108.7, 2021: 111.6, 2022: 121.7, 2023: 130.5, 2024: 133.9, 2025: 138.4, 2026: 138.4}
BASE_YEAR = 2023                       # the hydrogen benchmark (HAR1 strike price) is quoted in 2023 prices


RAW_FILES = ("daily_demand.csv", "daily_generation_by_fuel.csv", "daily_generation_total.csv",
             "daily_market_index_price.csv", "wind_farm_generation.csv")


def raw_dir() -> Path:
    """RAW_DIR argument, else ./raw, else the nearest parent folder holding the five supplied CSVs
    (in the group repository that is the repository root)."""
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        return Path(sys.argv[1])
    for d in (ROOT / "raw", *ROOT.parents):
        if all((d / name).exists() for name in RAW_FILES):
            return d
    raise SystemExit("Supplied CSVs not found. Pass their folder: python t1_data.py RAW_DIR")


def build(raw: Path, verbose=True) -> pd.DataFrame:
    log = []
    def note(s=""):
        log.append(s)
        if verbose:
            print(s)
    idx = pd.date_range(START, END, freq="D")
    pos = np.arange(len(idx)) % 7                       # position inside the 7-day download window
    window_end = pos == 6

    dem = pd.read_csv(raw / "daily_demand.csv")
    dem.index = pd.to_datetime(dem["startTime"], utc=True).dt.tz_localize(None).dt.normalize()
    dem = dem["demand"].astype(float).reindex(idx)
    price = pd.read_csv(raw / "daily_market_index_price.csv", parse_dates=["date"]).set_index("date").iloc[:, 0].reindex(idx)
    farm = pd.read_csv(raw / "wind_farm_generation.csv", parse_dates=["date"]).set_index("date")["wind_farm_MW"].reindex(idx)
    fuel = pd.read_csv(raw / "daily_generation_by_fuel.csv", parse_dates=["date"]).pivot_table(
        index="date", columns="psrType", values="MW", aggfunc="sum").reindex(idx)
    out = pd.DataFrame(index=idx); out.index.name = "date"
    out["farm_MW"] = farm
    assert farm.notna().all()

    # ---- D1 / P1: weekly-window fault
    note("== D1/P1  last day of each 7-day download window ==")
    for name, s in (("demand", dem), ("price", price)):
        nb = (s.shift(1) + s.shift(-1)) / 2
        ratio = (s / nb)
        by = ratio.groupby(pos).median().round(3)
        note(f"{name}: median ratio to the mean of the two neighbouring days, by position in window: {by.to_dict()}")
    note(f"position 6 falls on a {idx[6].day_name()} throughout; {int(window_end.sum())} days affected in each series")
    out["demand_raw"] = dem
    d = dem.copy()
    d[window_end | (d < 10000)] = np.nan
    out["demand_fixed"] = d.isna()
    out["demand_MW"] = d.interpolate("time").bfill().ffill()
    note(f"demand: {int(out.demand_fixed.sum())} values replaced (window ends, 1 missing day and the 636 MW outlier are all window-end days)")

    out["price_raw"] = price
    p = price.copy(); p[window_end] = np.nan
    out["price_fixed"] = p.isna()
    p = p.interpolate("time").bfill().ffill()
    note("\n== P2/P3  price level ==")
    note(f"price: {int(price.isna().sum())} missing days and {int(window_end.sum())} window-end days replaced by interpolation")
    yr_mean = (price.groupby(idx.year).mean()).round(1)
    note(f"raw annual means GBP/MWh: {yr_mean.to_dict()}")
    note("published GB day-ahead averages: 2024 = 72.58 (Montel), 74.0 (Electricity Maps); 2025 = 81.2 (Electricity Maps)")
    note(f"ratio of the raw file to those figures: 2024 = {yr_mean[2024] / 72.58:.2f}, 2025 = {yr_mean[2025] / 81.2:.2f}  -> x2 correction applied")
    out["price_nominal"] = 2.0 * p
    out["price_as_supplied"] = p                       # for the 'no correction' sensitivity
    defl = np.array([CPI[BASE_YEAR] / CPI[y] for y in idx.year])
    out["price"] = out["price_nominal"] * defl          # GBP(2023) per MWh
    out["price_as_supplied_real"] = out["price_as_supplied"] * defl

    # ---- G1: generation
    note("\n== G1  national generation ==")
    res = fuel[["Wind Offshore", "Wind Onshore", "Solar"]].sum(axis=1, min_count=1)
    total = fuel.sum(axis=1, min_count=1)
    firm = total - res
    nuc = fuel["Nuclear"]
    missing = total.isna()
    zero = (firm <= 0) & ~missing
    cover = total / out["demand_MW"]
    x = cover / cover.where(firm > 0).rolling(31, center=True, min_periods=8).median()
    y = nuc / nuc.where(nuc > 0).rolling(11, center=True, min_periods=4).median()
    partial = ~missing & ~zero & (y < 0.75) & (x < 0.85)
    bad = missing | zero | partial
    note(f"missing days {int(missing.sum())}; days with zero non-wind/solar output {int(zero.sum())}; partial records {int(partial.sum())} "
         f"(nuclear below 75% of its 11-day median and generation/demand below 85% of its 31-day median)")
    quarters = pd.get_dummies(pd.PeriodIndex(idx, freq="Q").astype(str)).astype(float).values
    # wind+solar on fully missing days, from the client's farm (same weather system)
    Xr = np.column_stack([quarters, farm.values, farm.values ** 2 / 1000])
    br, *_ = np.linalg.lstsq(Xr[~missing.values], res.values[~missing.values], rcond=None)
    res_hat = np.maximum(Xr @ br, 0)
    err = (res.values - res_hat)[~missing.values]
    note(f"wind+solar ~ farm output: R2 {1 - err.var() / res.values[~missing.values].var():.2f}, MAE {np.abs(err).mean():,.0f} MW (used on {int(missing.sum())} days)")
    res_f = res.where(~missing, res_hat)
    Xf = np.column_stack([quarters, out["demand_MW"].values, res_f.values])
    ok = ~bad.values
    bf, *_ = np.linalg.lstsq(Xf[ok], firm.values[ok], rcond=None)
    firm_hat = np.maximum(Xf @ bf, 0)
    err = (firm.values - firm_hat)[ok]
    note(f"non-wind/solar ~ demand + wind+solar + quarter: R2 {1 - err.var() / firm.values[ok].var():.2f}, MAE {np.abs(err).mean():,.0f} MW, "
         f"coefficients demand {bf[-2]:.2f}, wind+solar {bf[-1]:.2f} (used on {int(bad.sum())} days)")
    out["gen_imputed"] = bad
    out["gen_missing"] = missing
    out["res_MW"] = res_f
    out["gen_MW"] = (firm.where(~bad, firm_hat) + res_f)
    out["gen_raw_total_MW"] = total
    out["imputation_mae_MW"] = float(np.abs(err).mean())

    out["any_adjusted"] = out.demand_fixed | out.price_fixed | out.gen_imputed
    note(f"\nclean table: {len(out)} days; {int(out.gen_imputed.sum())} with imputed generation, {int(out.demand_fixed.sum())} with replaced demand, "
         f"{int(out.price_fixed.sum())} with replaced price; {int((~out.any_adjusted).sum())} days untouched except for the price level correction")
    (ROOT / "data").mkdir(exist_ok=True)
    out.round(4).to_csv(ROOT / "data" / "clean_daily.csv")
    (ROOT / "data" / "data_quality_log.txt").write_text("\n".join(log), encoding="utf-8")
    return out


def load(start="2020-01-01", end="2025-12-31") -> pd.DataFrame:
    f = ROOT / "data" / "clean_daily.csv"
    if not f.exists():
        build(raw_dir(), verbose=False)
    return pd.read_csv(f, parse_dates=["date"]).set_index("date").loc[start:end]


if __name__ == "__main__":
    df = build(raw_dir())
    w = df.loc["2020":"2025"]
    head = (w.demand_MW - w.gen_MW).clip(lower=0)
    q0 = np.minimum(w.farm_MW, head); s = w.farm_MW - q0
    print(f"\n2020-2025: national generation above demand on {(w.gen_MW > w.demand_MW).mean():.1%} of days; "
          f"farm output {w.farm_MW.mean() * 8.766:,.0f} GWh/yr, of which unused {s.mean() * 8.766:,.0f} GWh/yr ({s.sum() / w.farm_MW.sum():.1%})")
