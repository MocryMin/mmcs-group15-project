"""Replay neighboring verified investments to strengthen difficult B incumbents."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import json

from run import CASES, ROOT
from sweep import check, data_costs, make_model, solve, stress, unpack


def replay(task):
    target, source = task
    gap, price = target["gap_std_multiplier"], target["price_std_multiplier"]
    g, d, p = stress(gap, price)
    config, groups, plants = data_costs()
    counts = source["counts"]
    h_counts = source["electrolyser_counts"]
    cap = sum(b["usable"] * b["eta"] * counts.get(b["id"], 0) for group in groups for b in group)
    reference = target["no_battery_annual_profit_GBP"] / 1e6
    bad = set()
    for _ in range(5):
        model, cols, h, b, modes = make_model(g, d, p, "B", config, groups, plants, True,
                                              reference, bad, True, fixed=counts, size_limit=cap)
        for name, index in h.items():
            model.lo[index] = model.hi[index] = h_counts.get(name, 0)
            model.integer[index] = 0
        for index in b.values():
            model.integer[index] = 0
        x, _, _, status = solve(model, 28, 1)
        flow, hc, bc, _ = unpack(x, cols, h, b, modes)
        _, added, priority, profit = check(flow, hc | bc, g, d, p, "B", config, groups, plants)
        if not added and priority < 1e-7:
            return {
                "gap": gap, "price": price, "source_price": source["price_std_multiplier"],
                "annual_profit_GBP": profit * 1e6, "status": status,
                **{key: source[key] for key in ("counts", "battery_MW", "battery_MWh", "battery_annual_cost_GBP",
                                               "electrolyser_counts", "electrolyser_MW")}
            }
        if not added - bad:
            break
        bad.update(added)
    raise RuntimeError(f"No verified replay for {gap}, {price} from {source['price_std_multiplier']}")


def compute():
    b = [json.loads(path.read_text(encoding="utf-8")) for path in CASES.glob("B_joint_*.json")]
    wide = [r for r in b if r["objective_upper_GBP"] - r["objective_lower_GBP"] > 20]
    tasks = []
    for target in wide:
        neighbors = [r for r in b if r["gap_std_multiplier"] == target["gap_std_multiplier"]
                     and r["decision"] == "positive" and r["battery_MWh"] > 0]
        neighbors.sort(key=lambda r: abs(r["price_std_multiplier"] - target["price_std_multiplier"]))
        tasks.extend((target, r) for r in neighbors[:2])
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = {pool.submit(replay, task): task for task in tasks}
        for future in as_completed(results):
            target, source = results[future]
            try:
                row = future.result()
            except (AssertionError, RuntimeError) as error:
                print(f"Replay {target['gap_std_multiplier']}, {target['price_std_multiplier']} "
                      f"from {source['price_std_multiplier']} failed: {error}", flush=True)
                continue
            print(f"Replay {row['gap']}, {row['price']} from {row['source_price']}: "
                  f"{row['annual_profit_GBP'] - target['no_battery_annual_profit_GBP']:,.2f} GBP/y", flush=True)
            name = f"{row['gap']:.10g}_{row['price']:.8g}_{row['source_price']:.8g}.json"
            (ROOT / "replays" / name).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")


def merge(prices=None):
    for path in (ROOT / "replays").glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if prices is not None and value["price"] not in prices:
            continue
        case = CASES / f"B_joint_{value['price']:.8g}_gap{value['gap']:.10g}.json"
        row = json.loads(case.read_text(encoding="utf-8"))
        increase = value["annual_profit_GBP"] - row["no_battery_annual_profit_GBP"]
        if increase <= row["objective_lower_GBP"] + .02:
            continue
        assert increase <= row["objective_upper_GBP"] + .05
        for key in ("counts", "battery_MW", "battery_MWh", "battery_annual_cost_GBP",
                    "electrolyser_counts", "electrolyser_MW"):
            row[key] = value[key]
        row["objective_lower_GBP"] = increase
        row["incumbent_replayed_from_price_std_multiplier"] = value["source_price"]
        row["decision"] = "positive" if increase > row["zero_upper_minus_feasible_GBP"] + .5 else "unresolved"
        case.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys
    (ROOT / "replays").mkdir(exist_ok=True)
    merge() if "--merge" in sys.argv else compute()
