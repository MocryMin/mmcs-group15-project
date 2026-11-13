"""Reproduce the GB market-index series and identify extreme windows."""

import csv
import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parent / "data-repair-20261104-v2/evidence/mid.json.gz"
V6 = ROOT.parent / "tier1-multiproduct-20261110-v6"
API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index"
QUERIES = [
    ("2016-11-01", "2016-11-08"), ("2016-11-08", "2016-11-15"), ("2016-11-15", "2016-11-22"),
    ("2016-11-22", "2016-11-29"), ("2016-11-29", "2016-12-01"),
    ("2018-02-22", "2018-03-01"), ("2018-03-01", "2018-03-08"), ("2018-03-08", "2018-03-11"),
    ("2021-09-07", "2021-09-10"), ("2022-08-26", "2022-08-27"), ("2022-09-23", "2022-09-24"),
]
RANGES = [("2016-11-01", "2016-12-01"), ("2018-02-22", "2018-03-11"), ("2020-01-01", "2026-09-18")]


def read_sources():
    with gzip.open(ARCHIVE, "rt", encoding="utf-8") as stream:
        archive = json.load(stream)["days"]
    providers = {(stamp, name): tuple(values) for day in archive.values()
                 for stamp, records in day.items() for name, values in records.items()}
    checked = {}
    manifest = []
    for start, end in QUERIES:
        file = ROOT / "source" / f"mid-{start}.json"
        payload = file.read_bytes()
        document = json.loads(payload)
        assert document["metadata"]["datasets"] == ["MID"]
        rows = document["data"]
        for row in rows:
            stamp = row["startTime"]
            if not start <= stamp[:10] < end:
                continue
            key = (stamp, row["dataProvider"])
            value = (row["price"], row["volume"])
            if start >= "2020-01-01":
                assert providers[key] == value
                checked[start] = checked.get(start, 0) + 1
            else:
                assert key not in providers
                providers[key] = value
        manifest.append(dict(
            file=str(file.relative_to(ROOT)), record_count=len(rows),
            sha256=hashlib.sha256(payload).hexdigest(),
            url=API + "?" + urlencode({"from": start + "T00:00:00Z", "to": end + "T00:00:00Z", "format": "json"})))
    assert checked == {"2021-09-07": 288, "2022-08-26": 96, "2022-09-23": 86}
    return providers, checked, manifest


def cpi_series():
    path = V6 / "inputs/CPI.csv"
    result = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            try:
                month = pd.to_datetime(row[0], format="%Y %b").strftime("%Y-%m")
                result[month] = float(row[1])
            except (ValueError, IndexError):
                continue
    return result


def prices(providers):
    raw = pd.DataFrame(((ts, name, price, volume) for (ts, name), (price, volume) in providers.items()),
                       columns=["utc", "provider", "nominal", "volume"])
    raw.utc = pd.to_datetime(raw.utc, utc=True)
    assert (raw.volume >= 0).all()
    active = raw[raw.volume.gt(0)].copy()
    active["price_x_volume"] = active.nominal * active.volume
    grouped = active.groupby("utc").agg(volume=("volume", "sum"), pv=("price_x_volume", "sum"),
                                         active_providers=("provider", "size"))
    timeline = pd.date_range(*RANGES[0], freq="30min", tz="UTC", inclusive="left")
    for bounds in RANGES[1:]:
        timeline = timeline.append(pd.date_range(*bounds, freq="30min", tz="UTC", inclusive="left"))
    assert grouped.index.difference(timeline).empty
    half = grouped.reindex(timeline).rename_axis("utc")
    half["mid_GBP_per_MWh"] = half.pv / half.volume
    half["volume"] = half.volume.fillna(0)
    half["active_providers"] = half.active_providers.fillna(0).astype(int)
    half["mid_GBP2020_per_MWh"] = half.mid_GBP_per_MWh * (108.7 / half.index.strftime("%Y-%m").map(cpi_series()))
    half = half.drop(columns="pv")
    half["date_utc"] = half.index.tz_localize(None).normalize()
    daily = half.groupby("date_utc").agg(
        observed_halfhours=("mid_GBP_per_MWh", "count"), daily_GBP_per_MWh=("mid_GBP_per_MWh", "mean"),
        daily_GBP2020_per_MWh=("mid_GBP2020_per_MWh", "mean"), min_30m_GBP_per_MWh=("mid_GBP_per_MWh", "min"),
        max_30m_GBP_per_MWh=("mid_GBP_per_MWh", "max"),
        min_30m_GBP2020_per_MWh=("mid_GBP2020_per_MWh", "min"),
        max_30m_GBP2020_per_MWh=("mid_GBP2020_per_MWh", "max"))
    daily["complete_utc_day"] = daily.observed_halfhours.eq(48)
    daily["spread_30m_GBP2020_per_MWh"] = daily.max_30m_GBP2020_per_MWh - daily.min_30m_GBP2020_per_MWh
    return half, daily


def window_stats(daily, half):
    frozen = daily.v6_daily_GBP2020_per_MWh.dropna()
    rolling = {n: frozen.rolling(n).std(ddof=0).dropna() for n in (30, 90, 365)}
    end90 = rolling[90].idxmax()
    cases = [
        ("November 2016", "2016-11-01", "2016-11-30"),
        ("February–March 2018 cold spell", "2018-02-22", "2018-03-10"),
        ("September 2021", "2021-09-01", "2021-09-30"),
        ("August 2022", "2022-08-01", "2022-08-31"),
        ("Most volatile 90 days, 2020–2025", str((end90-pd.Timedelta(days=89)).date()), str(end90.date())),
        ("Whole v6 history", "2020-01-01", "2025-12-31"),
    ]
    results = []
    for name, start, end in cases:
        rows = daily.loc[start:end]
        complete = rows.loc[rows.complete_utc_day, "daily_GBP2020_per_MWh"]
        use_v6 = name.startswith("Most volatile") or name.startswith("Whole v6")
        q = rows.v6_daily_GBP2020_per_MWh if use_v6 else complete
        periods = half.loc[start:end, "mid_GBP2020_per_MWh"].dropna()
        results.append(dict(
            window=name, start=start, end=end, days=len(rows), complete_days=len(complete),
            daily_statistics_days=q.count(),
            daily_statistics_basis="v6 repaired series" if use_v6 else "complete 48-period days only",
            days_with_daily_value=rows.daily_GBP2020_per_MWh.count(),
            daily_mean_GBP2020_MWh=q.mean(), daily_sd_GBP2020_MWh=q.std(ddof=0),
            daily_min_GBP2020_MWh=q.min(), daily_max_GBP2020_MWh=q.max(),
            daily_max_date=str(q.idxmax().date()),
            halfhour_min_GBP2020_MWh=periods.min(), halfhour_min_utc=str(periods.idxmin()),
            halfhour_max_GBP2020_MWh=periods.max(), halfhour_max_utc=str(periods.idxmax())))
    rolling_stats = {str(n): {"max_sd_GBP2020_MWh": float(series.max()), "ending_utc_day": str(series.idxmax().date())}
                     for n, series in rolling.items()}
    return pd.DataFrame(results), rolling_stats


def draw(half, daily, rolling):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import matplotlib.dates as mdates

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), layout="constrained")
    for day, name, color in [("2021-09-09", "9 Sep 2021", "#225881"), ("2022-08-26", "26 Aug 2022", "#aa5227")]:
        day_price = half.loc[day, "mid_GBP2020_per_MWh"]
        hour = day_price.index.hour + day_price.index.minute / 60
        axes[0].step(np.r_[hour, 24], np.r_[day_price, day_price.iloc[-1]], where="post",
                     label=name, color=color, lw=1.45)
        axes[0].axhline(day_price.mean(), color=color, alpha=.5, linestyle="--", linewidth=.9)
    axes[0].legend(frameon=False)
    axes[0].set(title="Half-hour prices on two high-price days", xlabel="Hour of day (UTC)",
                ylabel="Market index price (£2020/MWh)", xlim=(0, 24), xticks=[0, 6, 12, 18, 24])

    end = pd.Timestamp(rolling["90"]["ending_utc_day"])
    start = end - pd.Timedelta(days=89)
    series = daily.loc[start:end, "v6_daily_GBP2020_per_MWh"]
    axes[1].plot(series.index, series, color="#aa5227", lw=1.55)
    axes[1].set(title="Most volatile 90-day window in v6", xlabel="2022",
                ylabel="Daily market index price (£2020/MWh)")
    axes[1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    for ax in axes:
        ax.grid(axis="y", color="#d9dfe3", linewidth=.55)
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(ROOT / "gb-price-episodes.png", dpi=185)
    plt.close(fig)


def main():
    providers, checked, manifest = read_sources()
    half, daily = prices(providers)
    frozen = pd.read_csv(V6 / "results/A_comparable_main_schedule.csv", index_col="date", parse_dates=True)
    daily["v6_daily_GBP2020_per_MWh"] = frozen.price
    exact = daily.loc[frozen.index]
    matched = exact.loc[exact.complete_utc_day, "daily_GBP2020_per_MWh"]
    error = matched.to_numpy() - frozen.price.loc[matched.index].to_numpy()
    assert np.max(np.abs(error)) < 1e-4
    stats, rolling = window_stats(daily, half)
    half.to_csv(ROOT / "halfhour-market-index.csv", float_format="%.8f")
    daily.to_csv(ROOT / "daily-market-index.csv", float_format="%.8f")
    stats.to_csv(ROOT / "episode-summary.csv", index=False, float_format="%.8f")
    test = dict(
        archive_days=int(len(daily)), halfhour_slots=len(half), positive_volume_halfhours=int(half.active_providers.gt(0).sum()),
        redownloaded_provider_records_matching=checked,
        v6_dates=len(frozen), complete_v6_raw_days_reproduced=len(matched),
        v6_raw_days_without_active_record=int(exact.observed_halfhours.eq(0).sum()),
        v6_raw_days_with_incomplete_coverage=int((~exact.complete_utc_day).sum()),
        max_v6_error_GBP2020_MWh=float(np.max(np.abs(error))), max_rolling_sd=rolling,
        largest_daily_within_day_spreads_v6=daily.loc[frozen.index, "spread_30m_GBP2020_per_MWh"]
        .nlargest(5).rename(index=lambda t: str(t.date())).to_dict())
    (ROOT / "verification.json").write_text(json.dumps(test, indent=2) + "\n", encoding="utf-8")
    (ROOT / "source-manifest.json").write_text(json.dumps({
        "retrieved_on_Europe_London": "2026-11-12", "Elexon": manifest,
        "local_raw": str(ARCHIVE.relative_to(ROOT.parent)),
        "local_cpi": str((V6 / "inputs/CPI.csv").relative_to(ROOT.parent)),
        "CPI_series": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23",
        "currency_conversion": "108.7 / corresponding monthly ONS CPI",
    }, indent=2) + "\n", encoding="utf-8")
    draw(half, daily, rolling)
    print(stats.to_string(index=False))
    print(json.dumps(test, indent=2))


if __name__ == "__main__":
    main()
