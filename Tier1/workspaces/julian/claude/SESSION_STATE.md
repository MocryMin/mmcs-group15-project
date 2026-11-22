# julian-claude Tier 1 session state

Updated 2026-11-22T20:45Z · agent `julian-claude` · member `julian` (Julian)

## Work
- `tier1-independent/20261116-v1/README.md`: an independent Tier 1 built from the brief, the course scripts and the five supplied CSVs. Farm boundary (only the client's own unsold wind output counts as surplus), brief parameters (two-hour battery, 20 MW electrolyser modules, hydrogen at GBP 9.5/kg), daily data, four solution methods cross-checked, and a step-by-step bridge to the repository's Tier 1 v6 result. Personal research draft, not a group decision.
- `data-analysis/20261113-v1/README.md`: first exploratory pass over the raw CSVs, made before reading the repository. Partly superseded; its README lists what not to quote.
- Each study has its documents in English (`README.md`, `RESULTS.md`, `COMPARISON.md`) and in Chinese (the same names with `_ZH`). The two versions carry the same numbers.

## Main findings
- Battery: zero under all four methods with the brief's two-hour battery. Gross value with perfect foresight is about GBP 2,900–3,200 per MWh-year against an annual cost of GBP 27,381 per MWh.
- Electrolyser, surplus only: 40 MW, +GBP 0.71m/yr, payback 9.75 years, negative in 2021, 2023 and 2024. Break-even for the first module: hydrogen at GBP 8.72/kg.
- Electrolyser, diversion allowed: 600 MW, +GBP 118.4m/yr, which needs 46,623 t/yr of hydrogen sold. With a 10 t/day offtake limit: 20 MW, +GBP 9.7m/yr.
- The gap to v6 (740 MW under policy B) is explained mainly by the system boundary (740 to 267 MW) and by cost and discount-rate assumptions (267 to 60 MW), not by method or data.
- All money is in 2023 pounds at an 8% real discount rate. The repository uses 2020 pounds at 5%.

## Open
- Solved with HiGHS through SciPy. The Xpress branches in `t1_model.py` have never been run; `python t1_run.py --check --solver xpress` needs a licensed machine.
- The farm boundary is an interpretation that has not been confirmed with the course staff.
- Written before report v5 (22 November). v5's half-hour results were not reproduced here. The README maps this work to the gaps the two v5 reviews raised (GBP 9.5/kg case, supplied daily data with brief parameters, investment metrics at the recommended scale).
- No message has been sent to other agents about this work. No public file was added or changed.
