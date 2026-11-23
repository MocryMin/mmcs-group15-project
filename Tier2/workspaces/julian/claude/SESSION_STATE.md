# julian-claude Tier 2 session state

Updated 2026-11-23T00:40Z · agent `julian-claude` · member `julian` (Julian)

## Work
- `tier2b-chronological/20261123-v1/README.md` (new): independent Tier 2B on the conventions of the independent Tier 1 (the client owns the wind farm, brief parameters, daily data 2020-2025, 2023 pounds, hydrogen GBP 9.5/kg). A chronological mixed-integer programme with a minimum run and minimum load for the electrolyser, a battery state of charge carried from day to day, and an operation re-planned every day on forecasts that include the NESO day-ahead demand and wind forecasts. Personal research draft, not a group decision.
- `tier2-models/20261116-v1/README.md`: one runnable daily model for each Tier 2 route, on the Tier 1 v6 inputs and conventions (2020 pounds, 5% real, hydrogen netback GBP 7.80/kg, 10 t/day offtake). Built to compare the two routes before the group settled on the half-hour Tier 2B work.
- Every results document is in English (`README.md`, `RESULTS*.md`) and in Chinese (the same names with `_ZH`). The two versions carry the same numbers.

## Main findings of `tier2b-chronological/20261123-v1`
- With a five-day minimum run and unsold energy only, the 40 MW plant of Tier 1 runs on 7% of days and loses GBP 6.1m/yr; no size is viable. Unsold energy sufficient for one module comes in short stretches (23 of five days or more in six years).
- If other electricity may hold minimum load, 40 MW earns GBP 4.5m/yr and the best size is 340 MW at GBP 17.3m/yr (payback 8.4 years, three loss-making years of six, about half of the hydrogen from electricity that had a buyer).
- With diversion allowed, the best size is 660 MW at GBP 127.8m/yr (payback 5.2 years); the minimum run costs under 1%.
- No battery is chosen under any rule: GBP 2,100-14,200 per MWh per year of value against GBP 27,400 of cost.
- Operation: at GBP 9.5/kg never switching off earns 94-96% of full foresight in 2022-2025, and plans built on more accurate forecasts did not earn more. At GBP 6/kg it earns 76-77% and daily re-planning recovers 7-10 points.
- The strategy changes with the hydrogen price (no plant below about GBP 6-8/kg), demand growth of 10%, 20% less national wind and solar, and an offtake cap.
- It agrees with the two half-hour site-scale studies under `../codex/` where they overlap (surplus-only with a multi-day minimum run is not operable; the minimum run is cheap once diversion is allowed). Section 7 of `RESULTS.md` compares them.

## Main findings of `tier2-models/20261116-v1`
- 2A (new generation): offshore wind is never chosen; onshore wind enters first, solar after onshore saturates. With a GBP 500m budget: 352 MW onshore wind plus a 23.3 MW electrolyser, no battery, +GBP 44.1m/yr under policy A and +GBP 34.2m/yr under B. New generation does not change the electrolyser or battery choice.
- 2B (daily operation under limited information): a hydrogen buffer tank never pays at researched costs. A settlement window in the offtake contract does create a link between days, but under policy A every causal operating rule earns less than the plain daily contract (GBP 13.08m/yr against at most GBP 12.95m/yr), because forecast skill is gone after about two days. Under policy B a greedy rule is already optimal.

## Open
- Solved with HiGHS through SciPy. No Xpress branch has been run: `python t2b_run.py --solver xpress --check` and `python tier2a.py --solver xpress --check` need a licensed machine.
- Daily data cannot see within-day price spreads or how continuous the surplus is within a day; the half-hour work takes precedence where results differ.
- The farm boundary used in `tier2b-chronological` (only the wind farm belongs to the client) is an interpretation that has not been confirmed with the course staff.
- `tier2b-chronological` prices grid imports at the wholesale price and values all hydrogen at one price; both are tested in its sensitivity table.
- No message has been sent to other agents about this work. No public file was added or changed. Files under `../codex/` belong to `julian-codex` and were not touched.
