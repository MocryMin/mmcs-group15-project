"""Verify the published generation repair against the course inputs and audit."""

import csv
import hashlib
import io
import json
from pathlib import Path


def csv_bytes(header, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    release = Path(__file__).resolve().parent
    root = release.parents[4]
    audit = json.loads((release / "generation_repair_audit.json").read_text(encoding="utf-8"))
    fuel_name = "daily_generation_by_fuel.csv"
    total_name = "daily_generation_total.csv"
    fuel_order = audit["original"]["fuel_columns_in_audit_order"]
    fuel_index = {fuel: index for index, fuel in enumerate(fuel_order)}
    patches = {row["d"]: row for row in audit["patches"]}
    require(len(patches) == len(audit["patches"]) == 107, "Unexpected patch dates")

    for filename in (fuel_name, total_name):
        digest = hashlib.sha256((root / filename).read_bytes()).hexdigest()
        require(digest == audit["original"]["sha256"][filename], f"Unexpected course input {filename}")

    fuel_rows = []
    old_totals = {}
    repaired_totals = {}
    observed_keys = set()
    with (root / fuel_name).open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            date, fuel, value = row["date"], row["psrType"], int(row["MW"])
            require((date, fuel) not in observed_keys, f"Duplicate record for {date} {fuel}")
            observed_keys.add((date, fuel))
            patch = patches.get(date)
            replacement = value
            if patch:
                index = fuel_index[fuel]
                require(patch["original"][index] == value, f"Patch source mismatch for {date} {fuel}")
                replacement = patch["repair"][index]
            fuel_rows.append((date, fuel, replacement))
            old_totals[date] = old_totals.get(date, 0) + value
            repaired_totals[date] = repaired_totals.get(date, 0) + replacement

    require(patches.keys() <= repaired_totals.keys(), "Patch refers to an absent date")
    require(len(fuel_rows) == len(repaired_totals) * len(fuel_order), "Incomplete fuel categories")
    total_rows = []
    with (root / total_name).open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            date, value = row["date"], int(row["total_MW"])
            require(old_totals[date] == value, f"Course total differs from fuel sum for {date}")
            total_rows.append((date, repaired_totals[date]))

    require(len(total_rows) == len(repaired_totals) == 2422, "Unexpected date count")
    require(len({date for date, _ in total_rows}) == len(total_rows), "Duplicate total date")
    changed_dates = {date for date, value in total_rows if value != old_totals[date]}
    require(changed_dates == patches.keys(), "Changed dates do not match the patch")
    expected = {
        fuel_name: csv_bytes(("date", "psrType", "MW"), fuel_rows),
        total_name: csv_bytes(("date", "total_MW"), total_rows),
    }
    for filename, data in expected.items():
        require((release / filename).read_bytes() == data, f"Reconstruction differs for {filename}")
        digest = hashlib.sha256(data).hexdigest()
        require(digest == audit["output_verification"]["sha256"][filename], f"Hash differs for {filename}")
    print(f"Verified {len(fuel_rows):,} fuel rows, {len(total_rows):,} totals and {len(changed_dates)} repaired dates.")


if __name__ == "__main__":
    main()
