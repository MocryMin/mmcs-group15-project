"""Screen hydrogen inventory and backup supply for the 156 complete Tier 2B weeks."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def production(halfhour, audit, weekly):
    if sha256(halfhour.read_bytes()).hexdigest() != audit["input_sha256"]["inputs/halfhour.csv.gz"]:
        raise ValueError("Expected the backtest's frozen half-hour input")
    frame = pd.read_csv(halfhour)
    frame = frame[frame.date.between(weekly.week_start_utc.iloc[0], weekly.week_end_utc.iloc[-1])]
    starts = pd.to_datetime(frame.utc.iloc[::336], utc=True)
    assert starts.tolist() == pd.to_datetime(weekly.week_start_utc, utc=True).tolist()
    equip = audit["equipment"]
    surplus = (frame.background_MW + frame.farm_flat_MW - frame.demand_MW).clip(lower=0).to_numpy() * 0.5
    nameplate = audit["designs"]["pre_test"]["B"] * equip["module_mw"] * 0.5
    available = np.where(surplus >= equip["minimum_mwh"], surplus.clip(max=nameplate), 0)
    volume = available.reshape(-1, 336).sum(axis=1) / equip["mwh_per_kg"] / 1000
    np.testing.assert_allclose(np.minimum(volume, 70), weekly.b_greedy_delivery_t, atol=1e-6, rtol=0)
    return volume


def max_floor_supply_only(volume, tank):
    """Every block's demand must fit its generation plus its opening inventory."""
    prefix = np.r_[0, np.cumsum(volume)]
    start, end = np.triu_indices(len(volume) + 1, k=1)
    initial = np.where(start == 0, 0, tank)
    bounds = (prefix[end] - prefix[start] + initial) / (end - start)
    return min(70, max(0, float(bounds.min())))


def replay(volume, floor, tank):
    """Meet the floor, save any surplus that fits, and sell remaining volume to the cap."""
    stock = 0.0
    rows = []
    for index, supply in enumerate(volume):
        available = supply + stock
        backup = max(floor - available, 0)
        reserve = tank if index < len(volume) - 1 else 0
        stock_next = min(reserve, max(available - floor, 0))
        delivered = max(floor, min(70.0, available - stock_next))
        curtailed = available + backup - delivered - stock_next
        assert abs(curtailed) < 1e-7 or curtailed > 0
        assert floor <= delivered <= 70 and 0 <= stock_next <= tank
        rows.append((backup, delivered, stock_next))
        stock = stock_next
    assert stock == 0
    return np.array(rows)


def verify_backup_lp(volume, results):
    """Verify purchase volumes against a full-horizon linear programme."""
    from scipy.optimize import linprog
    from scipy.sparse import diags, eye, hstack

    weeks = len(volume)
    identity = eye(weeks, format="csr")
    stock_flow = diags(np.ones(weeks - 1), -1, shape=(weeks, weeks)) - identity
    # Columns are site production, purchases, deliveries and closing inventory.
    balance = hstack((identity, identity, -identity, stock_flow), format="csr")
    cost = np.r_[np.zeros(weeks), np.ones(weeks), np.zeros(2 * weeks)]
    for case in results.itertuples(index=False):
        bounds = (
            [(0, capacity) for capacity in volume]
            + [(0, case.floor_t)] * weeks
            + [(case.floor_t, 70)] * weeks
            + [(0, case.tank_t)] * (weeks - 1)
            + [(0, 0)]
        )
        solution = linprog(cost, A_eq=balance, b_eq=np.zeros(weeks), bounds=bounds, method="highs")
        if not solution.success:
            raise RuntimeError(f"Linear programme failed for {case}: {solution.message}")
        np.testing.assert_allclose(solution.fun, case.backup_total_t, atol=1e-6, rtol=0)
    print(f"Independent linear programme verified {len(results)} backup scenarios.")


def draw(maximum, results, output):
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False})
    fig, (left, right) = plt.subplots(1, 2, figsize=(10.65, 4.45), facecolor="white")
    fig.subplots_adjust(left=0.082, right=0.975, top=0.748, bottom=0.21, wspace=0.32)
    fig.text(0.082, 0.964, "How can Policy B meet a weekly delivery floor?", fontsize=19.5,
             color="#162831", weight="bold", va="top")
    fig.text(0.082, 0.868, "156 complete weeks, 2023–2025  |  12 modules  |  Flexible half-hour switching",
             color="#425768", fontsize=10.5, va="top")
    for axis in (left, right):
        axis.tick_params(length=0, pad=6, labelcolor="#425768")
        axis.spines["bottom"].set_color("#BDD0D8")
        axis.set_axisbelow(True)
        axis.grid(axis="y", color="#DEE7EB", linewidth=0.8)
    left.set_title("Storage alone", loc="left", color="#162831", weight="bold", fontsize=13)
    left.plot(maximum["tank_t"], maximum["max_floor_t"], color="#077A77", lw=2.5)
    ceiling = maximum["max_floor_t"].max()
    left.axhline(ceiling, color="#7B8A94", lw=1.1, ls=(0, (4, 3)))
    left.text(66, ceiling + 0.17, f"Ceiling {ceiling:.2f} t/week", color="#077A77", ha="right", fontsize=9.2)
    left.set_xlim(0, 70)
    left.set_ylim(0, 4.45)
    left.set_xlabel("Usable hydrogen buffer (t)", color="#425768")
    left.set_ylabel("Maximum weekly floor (t)", color="#425768")

    bars = results.query("floor_t == 10 and tank_t in [0, 20, 70]").sort_values("tank_t")
    right.set_title("Backup needed for a 10 t/week floor", loc="left", color="#162831", weight="bold", fontsize=13)
    series = right.bar(["No buffer", "20 t buffer", "70 t buffer"], bars["backup_total_t"],
                       color=["#BB5F36", "#A87657", "#826956"], width=0.56)
    right.bar_label(series, fmt="%.1f", padding=4, fontsize=10, color="#162831")
    right.set_ylim(0, 320)
    right.set_yticks([0, 100, 200, 300])
    right.set_ylabel("Backup over the replay (t)", color="#425768")
    fig.text(0.082, 0.064, "Indicative screen with lossless storage, zero opening and closing inventory, and weekly settlement.",
             fontsize=9, color="#425768")
    fig.text(0.082, 0.029, "The floor is measured in this replay. Backup on any shortfall week requires a firm supply arrangement.",
             fontsize=9, color="#425768")
    for suffix in ("png", "pdf"):
        fig.savefig(output / f"delivery-options-en.{suffix}", dpi=200, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weekly", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--halfhour", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lp", action="store_true", help="Verify each backup volume with a linear programme")
    args = parser.parse_args()

    weekly = pd.read_csv(args.weekly)
    audit = json.loads(args.audit.read_text())
    volume = production(args.halfhour, audit, weekly)
    assert len(volume) == 156
    starts = pd.to_datetime(weekly.week_start_utc)
    days = pd.date_range(starts.iloc[0], weekly.week_end_utc.iloc[-1])
    years = sum(1 / (366 if day.is_leap_year else 365) for day in days)
    equip = audit["equipment"]
    fixed = audit["designs"]["pre_test"]["B"] * equip["annual_gbp"]
    floor_curve = pd.DataFrame(
        (dict(tank_t=tank, max_floor_t=max_floor_supply_only(volume, tank)) for tank in np.linspace(0, 70, 141))
    )
    results = []
    for floor in (0, 3, 10, 35, 70):
        for tank in (0, 20, 30, 70):
            series = replay(volume, floor, tank)
            backup, delivered, stock = series.T
            backup_premium = 5.0
            own_sales_value = (delivered.sum() - backup.sum()) * 1000 * equip["netback"]
            net_before_tank = (own_sales_value - backup.sum() * 1000 * backup_premium) / years - fixed
            results.append(dict(floor_t=floor, tank_t=tank, max_no_backup_floor_t=max_floor_supply_only(volume, tank),
                                total_delivered_t=delivered.sum(), backup_total_t=backup.sum(),
                                max_weekly_backup_t=backup.max(), max_stored_t=stock.max(),
                                net_gbp_per_year_before_tank_at_5_gbp_backup_premium=net_before_tank))
    results = pd.DataFrame(results)
    if args.verify_lp:
        verify_backup_lp(volume, results)
    args.output.mkdir(parents=True, exist_ok=True)
    floor_curve.to_csv(args.output / "storage_floor_curve.csv", index=False, float_format="%.9f")
    results.to_csv(args.output / "delivery_options.csv", index=False, float_format="%.9f")
    draw(floor_curve, results, args.output)


if __name__ == "__main__":
    main()
