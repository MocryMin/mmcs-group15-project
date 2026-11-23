# julian-claude Tier 1 session state

Updated 2026-11-23T10:42Z · agent `julian-claude` · member `julian` (Julian)

## Work
- `tier1-main-results/20261123-v1/REVISION.md` (new): the Tier 1 main results at the recommended scale with the electrolyser's operating limits in the main case, on the group's half-hour conventions (v7 record, 2020 pounds, GBP 7.80/kg, NEPTUNE V, 10 t/day buyer). Written as proposed replacement text and tables for report v5. Personal work, not a group decision.
- `tier1-independent/20261116-v1/README.md`: an independent Tier 1 built from the brief, the course scripts and the five supplied CSVs. Farm boundary (only the client's own unsold wind output counts as surplus), brief parameters (two-hour battery, 20 MW electrolyser modules, hydrogen at GBP 9.5/kg), daily data, four solution methods cross-checked, and a step-by-step bridge to the repository's Tier 1 v6 result. Personal research draft, not a group decision.
- `data-analysis/20261113-v1/README.md`: first exploratory pass over the raw CSVs, made before reading the repository. Partly superseded; its README lists what not to quote.
- Each study has its documents in English (`README.md`, `RESULTS.md`, `COMPARISON.md`, `REVISION.md`) and in Chinese (the same names with `_ZH`). The two versions carry the same numbers.

## Main findings of `tier1-main-results/20261123-v1`
- Main operating rule: 20% minimum load, starts and stops at UTC midnight, at least four days online after a start.
- Policy A: the best plant falls from eight modules (40.2 MW, +GBP 14.10m/yr) to six (30.2 MW, +GBP 13.46m/yr, payback 2.6 years). A five-day run gives the same size and GBP 13.45m.
- Policy B: no electrolyser can run at any size. Generation left after demand covers one module's minimum load for at most 56 hours at a stretch, and for only 14 whole UTC days in six years.
- B with a minimum-load reserve (online modules may draw their minimum load ahead of demand): ten modules (50.3 MW), +GBP 8.11m/yr, payback 5.1 years, demand served down by 0.02 percentage points. This changes the policy definition and is for the group to decide.
- One 100 MW / 400 MWh battery block beside the site-scale plant: +GBP 5.64m/yr (A) and +GBP 1.64m/yr (B) with full foresight; +GBP 1.66m and +GBP 1.64m with the simple rule.
- 33 automated checks pass. Independent code reproduces all eight entries of v5 Table C.1, the UK-wide rows of v5 Table II.3, v5's simple-rule battery results, and the A results of `../codex/electrolyser-sensitivity/20261122-v1` to six decimals.

## Main findings of `tier1-independent/20261116-v1`
- Battery: zero under all four methods with the brief's two-hour battery. Gross value with perfect foresight is about GBP 2,900–3,200 per MWh-year against an annual cost of GBP 27,381 per MWh.
- Electrolyser, surplus only: 40 MW, +GBP 0.71m/yr, payback 9.75 years, negative in 2021, 2023 and 2024. Break-even for the first module: hydrogen at GBP 8.72/kg.
- Electrolyser, diversion allowed: 600 MW, +GBP 118.4m/yr, which needs 46,623 t/yr of hydrogen sold. With a 10 t/day offtake limit: 20 MW, +GBP 9.7m/yr.
- The gap to v6 (740 MW under policy B) is explained mainly by the system boundary (740 to 267 MW) and by cost and discount-rate assumptions (267 to 60 MW), not by method or data.
- All money is in 2023 pounds at an 8% real discount rate. The repository uses 2020 pounds at 5%.

## Open
- `tier1-main-results` was written against report v5. Report v6 (published 23 November, 02:09 UTC) already makes the 10 t/day site the main case, and its one-block battery figures (GBP 5.63m and 1.64m a year, break-even GBP 213 and 130 per kWh) agree with section 2.6 here. Section 1 of `REVISION.md` is therefore superseded by v6. Section 2 (operating rule) still applies: v6 keeps half-hour switching and a 12.5% minimum in its main case.
- Not yet done for v6: the GBP 2.50/kg, GBP 9.50/kg and two-rate rows of v6 Table II.4 under the main operating rule, and replacement wording keyed to v6's sections.
- `tier1-main-results` was solved with HiGHS through SciPy and has not been run in Xpress. Starts and stops are at UTC midnight only; start-up energy and a cost per start are not modelled.
- `tier1-independent` was solved with HiGHS through SciPy. The Xpress branches in `t1_model.py` have never been run; `python t1_run.py --check --solver xpress` needs a licensed machine.
- The farm boundary is an interpretation that has not been confirmed with the course staff.
- `tier1-independent` was written before report v5 (22 November). v5's half-hour results were not reproduced here. The README maps this work to the gaps the two v5 reviews raised (GBP 9.5/kg case, supplied daily data with brief parameters, investment metrics at the recommended scale).
- No message has been sent to other agents about this work. No public file was added or changed.
