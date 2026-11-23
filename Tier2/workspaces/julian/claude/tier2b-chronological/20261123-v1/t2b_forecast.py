"""
Daily forecasts for the rolling operation in Tier 2B.

Every forecast for day t+h uses only what is known at the end of day t.  Three quantities are forecast, in the
units of the cleaned daily table: wind-farm output (MW), the national supply gap (demand minus generation, MW)
and the electricity price (GBP/MWh, 2023 prices).  Unsold and saleable farm energy follow from the first two.

Methods
  perfect   the realised value (upper bound, not available in practice)
  persist   tomorrow and every later day equal today
  ar        ridge regression per horizon on recent values, the same weekday last week and calendar terms,
            re-estimated at the start of every month on all earlier data
  neso      as 'ar', but the one-day-ahead model also sees the NESO day-ahead demand and wind forecasts issued
            that day (course Q&A, 16 November: start from the published forecasts and re-solve every day).
            The NESO figures are on a different level from the course demand series, so they enter through a
            regression that is re-estimated every month: this is the calibration step.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

TARGETS = ("farm_MW", "gap_MW", "price")
NESO_COLS = ("neso_demand", "neso_wind", "neso_wind_lf")
FARM_MW = 1125.0


def load_frame(root: Path, start="2020-01-01", end="2025-12-31") -> pd.DataFrame:
    df = pd.read_csv(root / "inputs" / "clean_daily.csv", parse_dates=["date"]).set_index("date").loc[start:end].copy()
    df["gap_MW"] = df["demand_MW"] - df["gen_MW"]
    nd = pd.read_csv(root / "inputs" / "neso_demand.csv", parse_dates=["date"]).set_index("date")
    nw = pd.read_csv(root / "inputs" / "neso_wind.csv", parse_dates=["date"]).set_index("date")
    # a row dated t holds the forecast for day t+1 that was issued on day t
    df["neso_demand"] = nd["neso_demand_mean"].reindex(df.index)
    df["neso_wind"] = nw["neso_wind_mean"].reindex(df.index)
    df["neso_wind_lf"] = (nw["neso_wind_mean"] / nw["neso_wind_capacity"]).reindex(df.index)
    df["neso_wind_stale"] = nw["missing_forecast"].reindex(df.index)
    return df


def _features(y: np.ndarray, dates: pd.DatetimeIndex, h: int, extra: np.ndarray | None = None) -> np.ndarray:
    s = pd.Series(y)
    target = dates + pd.Timedelta(days=h)
    ang = 2 * np.pi * target.dayofyear.to_numpy() / 365.25
    wd = target.dayofweek.to_numpy()
    cols = [y, s.shift(1).to_numpy(), s.shift(2).to_numpy(), s.rolling(7).mean().to_numpy(),
            s.shift(max(7 - h, 0)).to_numpy(), np.sin(ang), np.cos(ang), np.sin(2 * ang), np.cos(2 * ang)]
    cols += [(wd == k).astype(float) for k in range(6)]
    X = np.column_stack(cols)
    if extra is not None: X = np.column_stack([X, extra])
    return X


def _ridge_fit(X, y, alpha=10.0):
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    Z = (X - mu) / sd
    beta = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return mu, sd, beta, y.mean()


def _ridge_predict(model, X):
    mu, sd, beta, b0 = model
    return ((X - mu) / sd) @ beta + b0


def make_forecasts(df: pd.DataFrame, H: int = 7, method: str = "ar") -> dict:
    """Returns {target: array (T, H)}; element [t, h-1] is the forecast for day t+h made at the end of day t.
    Regression models are re-estimated at the start of every month on all data whose outcome is already known.
    Where no model can be estimated yet the forecast falls back to persistence."""
    T, dates = len(df), df.index
    months = sorted(set(zip(dates.year, dates.month)))
    neso = df[list(NESO_COLS)].to_numpy(float)
    out = {}
    for tgt in TARGETS:
        y = df[tgt].to_numpy(float)
        F = np.repeat(y[:, None], H, axis=1)                               # persistence
        if method == "perfect":
            for h in range(1, H + 1):
                F[:T - h, h - 1] = y[h:]
        elif method in ("ar", "neso"):
            for h in range(1, H + 1):
                yt = np.full(T, np.nan); yt[:T - h] = y[h:]
                target_date = dates + pd.Timedelta(days=h)
                variants = [_features(y, dates, h)]
                if method == "neso" and h == 1: variants.append(_features(y, dates, h, neso))   # preferred when usable
                for X in variants:
                    ok = np.isfinite(X).all(1)
                    for yy, mm in months:
                        known = ok & np.isfinite(yt) & (target_date < pd.Timestamp(yy, mm, 1))
                        rows = ok & (dates.year == yy) & (dates.month == mm)
                        if known.sum() >= 300 and rows.any():
                            F[rows, h - 1] = _ridge_predict(_ridge_fit(X[known], yt[known]), X[rows])
        elif method != "persist":
            raise ValueError(method)
        if tgt == "farm_MW": F = np.clip(F, 0.0, FARM_MW)
        out[tgt] = F
    return out


def expected_energy(df: pd.DataFrame, F: dict, K: int = 200, seed: int = 0):
    """Expected unsold and saleable energy (MWh/day) around a point forecast.

    Unsold energy is max(farm output - supply gap, 0) on most days, so putting point forecasts into that formula
    understates it: the days that matter are the ones where the forecast is wrong in the favourable direction.
    Here the forecast errors observed over the previous 365 days (same horizon) are added to the point forecast
    and the formula is averaged over them.  Only errors already known on the day of the forecast are used."""
    T, H = F["price"].shape
    dates, idx = df.index, np.arange(len(df))
    yW, yG = df["farm_MW"].to_numpy(float), df["gap_MW"].to_numpy(float)
    S, Q = to_energy(F["farm_MW"], F["gap_MW"], F["price"])
    rng = np.random.default_rng(seed)
    for h in range(1, H + 1):
        eW, eG = np.full(T, np.nan), np.full(T, np.nan)
        eW[:T - h] = yW[h:] - F["farm_MW"][:T - h, h - 1]
        eG[:T - h] = yG[h:] - F["gap_MW"][:T - h, h - 1]
        for yy, mm in sorted(set(zip(dates.year, dates.month))):
            i0 = int(dates.searchsorted(pd.Timestamp(yy, mm, 1)))
            pool = np.flatnonzero((idx + h < i0) & (idx >= i0 - 365 - h) & np.isfinite(eW))
            rows = np.flatnonzero((dates.year == yy) & (dates.month == mm))
            if len(pool) < 60: continue
            pick = rng.choice(pool, size=min(K, len(pool)), replace=False)
            W = np.clip(F["farm_MW"][rows, h - 1][:, None] + eW[pick][None, :], 0.0, FARM_MW)
            G = F["gap_MW"][rows, h - 1][:, None] + eG[pick][None, :]
            s, q = to_energy(W, G, F["price"][rows, h - 1][:, None])
            S[rows, h - 1], Q[rows, h - 1] = s.mean(1), q.mean(1)
    return S, Q


def to_energy(farm, gap, price, boundary="farm"):
    """Unsold energy S and saleable energy Q0 (MWh/day) from farm output, supply gap and price (farm boundary)."""
    head = np.maximum(gap, 0.0)
    q0 = np.where(price >= 0, np.minimum(farm, head), 0.0)
    return 24.0 * (farm - q0), 24.0 * q0


def skill_table(df: pd.DataFrame, forecasts: dict, start, end) -> pd.DataFrame:
    """Mean absolute error by method, target and horizon over [start, end] (target dates)."""
    rows = []
    T, dates = len(df), df.index
    for method, F in forecasts.items():
        for tgt in TARGETS:
            y = df[tgt].to_numpy(float)
            for h in range(1, F[tgt].shape[1] + 1):
                tdate = dates[h:]
                m = (tdate >= pd.Timestamp(start)) & (tdate <= pd.Timestamp(end))
                err = F[tgt][:T - h, h - 1][m] - y[h:][m]
                rows.append(dict(method=method, target=tgt, horizon_days=h, mae=float(np.mean(np.abs(err))),
                                 bias=float(np.mean(err)), mean_level=float(np.mean(np.abs(y[h:][m])))))
    return pd.DataFrame(rows)


def calibration_table(df: pd.DataFrame) -> pd.DataFrame:
    """NESO day-ahead demand forecast against next-day demand in the course data, by year:
    as published, after a fixed scale estimated on the first year, and after a regression re-estimated yearly."""
    d = df[["demand_MW", "neso_demand"]].copy()
    d["actual_next"] = d["demand_MW"].shift(-1)
    d = d.dropna()
    rows, years = [], sorted(d.index.year.unique())
    first = d[d.index.year == years[0]]
    scale0 = float((first["actual_next"] / first["neso_demand"]).mean())
    for yr in years[1:]:
        past, cur = d[d.index.year < yr], d[d.index.year == yr]
        b = np.polyfit(past["neso_demand"], past["actual_next"], 1)
        rows.append(dict(year=yr, days=len(cur),
                         mae_as_published=float(np.abs(cur["neso_demand"] - cur["actual_next"]).mean()),
                         mae_fixed_scale=float(np.abs(scale0 * cur["neso_demand"] - cur["actual_next"]).mean()),
                         mae_recalibrated_yearly=float(np.abs(np.polyval(b, cur["neso_demand"]) - cur["actual_next"]).mean()),
                         mae_persistence=float(np.abs(cur["demand_MW"] - cur["actual_next"]).mean()),
                         bias_as_published=float((cur["neso_demand"] - cur["actual_next"]).mean()),
                         bias_recalibrated_yearly=float((np.polyval(b, cur["neso_demand"]) - cur["actual_next"]).mean())))
    return pd.DataFrame(rows)
