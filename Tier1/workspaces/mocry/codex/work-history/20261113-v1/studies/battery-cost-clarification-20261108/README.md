# Battery cost clarification — 2026-11-08

Local supplementary calculation; no changes to the frozen v4.1 candidate or remote repository.

One fixed 1.5 MW / 3 MWh battery and zero electrolysers, with the same daily throughput, efficiency, demand and sales-policy constraints as v4.1. Input hashes verified by `run_study.prepare_inputs()`. GBP2020 throughout.

Solved the continuous fixed-capacity problem with SciPy HiGHS 1.18.1. With baseline direct sales q0, use lost sales l=q0-q, charge c and discharge r. Maximise 1000*sum(price*(r-l)) / represented_years, subject to -l+c <= G-q0; -l+r <= D-q0; sum(r)=eta^2*sum(c); nonnegative variables; l<=q0 for A and l=0 for B; c<=min(G,E_usable/eta); r<=min(D,E_usable*eta). This is the original fixed-one-battery, no-electrolyser pooled LP with direct sales eliminated.

Every schedule passed the original `measure()` physical/cash checks. Both 2023 policy values match the archived Xpress cases within GBP0.10. Full six-year sample pooling and six separately balanced annual replays are distinct scenarios; the latter has lower mean earnings. Neither has chronological SOC.

Operating contribution includes the change in direct electricity sales plus discharge receipts and excludes fixed maintenance and capital recovery. Gross discharge receipts alone overstate economic benefit when charging displaces direct sales.

Across the six-year common pool, A contributes GBP25,485.70/year and B GBP20,977.43/year before fixed costs. Fixed maintenance is GBP22,292.43/year and annualised capital/commissioning GBP74,063.49/year, using a 15-year battery life and 5% real discount rate. Thus B does not cover maintenance on this historical mean; A covers maintenance by only GBP3,193.27/year and does not support capital recovery. The annualised appraisal does not require the initial investment to repay within six data years.

If each year balances separately, the mean operating contribution is A GBP22,149.19/year and B GBP17,662.52/year. These diagnostic cases explain the cost split; they do not replace the published joint investment results or demonstrate physically chronological battery performance.

Sources: sibling tier1-candidate-20261107-v4.1-academic inputs, run_study.py, results/study.json and results/extension.json. Detailed values: RESULTS.json.
