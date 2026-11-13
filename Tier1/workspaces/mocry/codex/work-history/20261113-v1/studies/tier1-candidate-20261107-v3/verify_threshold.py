"""Recheck the disputed hydrogen threshold with free and fixed-capacity MILPs."""
import run_study as model


def run():
    data, econ = model.load_data().loc["2023"], model.economics()
    price = 4.618
    free = model.solve(data, econ, "A", netback=price)[0]
    fixed = model.solve(data, econ, "A", fixed=(0, 1), netback=price)[0]
    assert free["nh"] == 1 and abs(free["net"] - fixed["net"]) < 1e-9
    record = dict(exact_break_even_GBP_kg=model.crossing(data, econ, "A", 10000.),
                  probe_GBP_kg=price, free_modules=free["nh"],
                  free_gain_GBP_year=free["net"] * 1e6,
                  fixed_one_gain_GBP_year=fixed["net"] * 1e6, miprelcutoff=0,
                  interpretation="At GBP4.618/kg the build is profitable; peer CSV rounding cannot explain zero build here.")
    model.write_json(model.OUT / "threshold_reconciliation.json", record)
    print(record)


if __name__ == "__main__":
    run()
