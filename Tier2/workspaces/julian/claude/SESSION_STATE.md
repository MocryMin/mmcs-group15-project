# julian-claude Tier 2 session state

Updated 2026-11-22T20:45Z · agent `julian-claude` · member `julian` (Julian)

## Work
- `tier2-models/20261116-v1/README.md`: one runnable daily model for each Tier 2 route, on the Tier 1 v6 inputs and conventions (2020 pounds, 5% real, hydrogen netback GBP 7.80/kg, 10 t/day offtake). Built to compare the two routes before the group settled on the half-hour Tier 2B work. Personal research draft, not a group decision.
- The documents are in English (`README.md`, `RESULTS_2A.md`, `RESULTS_2B.md`) and in Chinese (the same names with `_ZH`). The two versions carry the same numbers.

## Main findings
- 2A (new generation): offshore wind is never chosen; onshore wind enters first, solar after onshore saturates. With a GBP 500m budget: 352 MW onshore wind plus a 23.3 MW electrolyser, no battery, +GBP 44.1m/yr under policy A and +GBP 34.2m/yr under B. New generation does not change the electrolyser or battery choice.
- 2B (daily operation under limited information): a hydrogen buffer tank never pays at researched costs. A settlement window in the offtake contract does create a link between days, but under policy A every causal operating rule earns less than the plain daily contract (GBP 13.08m/yr against at most GBP 12.95m/yr), because forecast skill is gone after about two days. Under policy B a greedy rule is already optimal.

## Open
- Solved with HiGHS through SciPy. The Xpress branch in `common.LP` has never been run; `python tier2a.py --solver xpress --check` needs a licensed machine.
- Daily data cannot see within-day price spreads, so these models say nothing about the 100 MW / 400 MWh battery used in the group's Tier 2B work.
- The forecaster in `tier2b.py` is a plain ridge regression and can be swapped for the released ensembles.
- No message has been sent to other agents about this work. No public file was added or changed.
