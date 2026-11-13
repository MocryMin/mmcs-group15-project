"""Measure reconstruction error on held-out complete observations."""
import gzip
import json
import statistics
from datetime import date, timedelta
from pathlib import Path

from repair_data import error_stats, parse_neso, stamp_minutes

HERE = Path(__file__).resolve().parent


def main():
    def source(name):
        with gzip.open(HERE / "evidence" / (name + ".json.gz"), "rt", encoding="utf-8") as stream:
            return json.load(stream)
    neso = parse_neso(source("neso"))
    vd = source("demand")["days"]
    original, predicted = [], []
    for day, records in sorted(vd.items()):
        if day[-2:] != "15" or len(records) != 288 or any(v < 10000 for v in records.values()):
            continue
        grid = sorted((stamp_minutes(t), v) for t, v in records.items())
        good = grid[17:]
        diffs = [v - neso[day][t - t % 30][0] for t, v in good[:48]
                 if neso[day][t - t % 30][0] >= 10000]
        if len(diffs) < 12:
            continue
        offset = statistics.median(diffs)
        replaced = [neso[day][t - t % 30][0] + offset for t, v in grid[:17]]
        original.append(statistics.mean(v for t, v in grid))
        predicted.append((sum(replaced) + sum(v for t, v in good)) / 288)

    daily = {}
    for day, periods in source("mid")["days"].items():
        points = []
        for providers in periods.values():
            active = [(p, v) for p, v in providers.values() if v > 0]
            if active:
                points.append(sum(p * v for p, v in active) / sum(v for p, v in active))
        if len(points) == 48:
            daily[day] = statistics.mean(points)
    actual_price, estimated_price = [], []
    for day, value in sorted(daily.items()):
        if day[-2:] != "15":
            continue
        peers = []
        for delta in (7, -7, 14, -14, 21, -21):
            other = (date.fromisoformat(day) + timedelta(days=delta)).isoformat()
            if other in daily:
                peers.append(daily[other])
            if len(peers) == 4:
                break
        if len(peers) == 4:
            actual_price.append(value)
            estimated_price.append(statistics.mean(peers))
    result = {
        "demand_17_missing_midnight_slots": error_stats(original, predicted),
        "whole_day_price_estimation_GBP_MWh": error_stats(actual_price, estimated_price),
        "caveat": "Holdout tests use normal complete days on the 15th of each month. Errors are empirical, not guaranteed bounds. Wind and solar holdout statistics are in REPAIR_AUDIT.json."
    }
    (HERE / "IMPUTATION_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
