import json

p = "Tier1/workspaces/mocry/cleveruser/firstpass/R4-finance-data/audit_results.json"
d = json.load(open(p, encoding="utf-8"))
for f, r in d["files"].items():
    print("==", f)
    for c, st in r["value_stats"].items():
        print("  ", c, "n=%s min=%s max=%s mean=%.4f med=%s neg=%s zero=%s rz6=%s"
              % (st["n"], st["min"], st["max"], st["mean"], st["median"],
                 st["n_negative"], st["n_zero"], st.get("n_robust_z_gt6")))
        print("     lowest:", [(x["date"], round(x["value"], 3)) for x in st["lowest_5"]])
        print("     highest:", [(x["date"], round(x["value"], 3)) for x in st["highest_5"]])
        if st.get("n_robust_z_gt6"):
            print("     rz6 dates:", st.get("robust_z_gt6_dates")[:10])
cs = d["checks"]["common_date_system"]
print("\nsystem:", json.dumps({k: cs[k] for k in
      ["n_dates", "generation_MWh_total", "demand_MWh_total", "mean_generation_MW",
       "mean_demand_MW", "days_generation_gt_demand", "days_generation_lt_demand",
       "max_surplus_day", "max_deficit_day", "negative_price_days_on_intersection"]}, indent=1))
print("price identity:", d["checks"]["price_column_identity"])
print("fuel:", {k: d["checks"]["fuel_vs_total"][k] for k in
      ["common_dates", "dates_summing_exactly", "dates_with_nonzero_difference",
       "max_abs_difference_MW", "fuel_rows_per_date", "duplicate_date_psrType_pairs"]})
print("psr:", d["checks"]["fuel_vs_total"]["psrType_row_counts"])
