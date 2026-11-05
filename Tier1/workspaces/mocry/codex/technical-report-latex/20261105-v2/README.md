# MMCS technical report candidate · LaTeX v2

5 November 2026 · Ran Min / mocry-codex · Tier 1 review candidate

[Template preview](output/pdf/report-template.pdf) · [Four-page Tier 1 sample](output/pdf/tier1-example.pdf) · [Complete LaTeX sources](mmcs-technical-report-latex.zip)

The template is a group-report starting point. It budgets ten physical pages, including references, while the course counting rule is being clarified. The worked example fills the common front matter and Tier 1. The group report will add its selected Tier 2 extension and the combined recommendation. Both use the same A4, 11 pt layout.

## Contents and build

- `report-template.tex` loads the editable placeholders in `sections/tier1-template.tex`. To start from the example, replace that input with `sections/tier1.tex` and bring across the relevant bibliography entries.
- `tier1-example.tex` compiles the four-page worked example. Its section-boundary page breaks apply only to the example. The group template reflows the same material naturally.
- `report-style.tex` defines the common typography, equations, tables and cross-references. The two vector figures are included.

From this directory or the unpacked source ZIP, run:

```text
tectonic report-template.tex
tectonic tier1-example.tex
```

To redraw the figures, run `python make_figures.py --results <Tier 1 v1 results directory>` with matplotlib, NumPy and pandas. Compilation uses the included figures and needs no Python or solver.

## Evidence and changes since v1

- **Input treatment.** The report now records the full-day repairs for generation, demand and price endpoints, the price aggregation correction and the strict-quality check. The equipment assumptions show how the brief's EUR 288,000/MWh and GBP 9.50/kg anchors relate to the real-price model. The hydrogen value is rebased from the explicitly dated 2012 support price, rather than assigning an assumed price year to the GBP 9.50/kg figure.
- **Value and energy capture.** The opening states the policy and offtake conditions for the result. The figure and model separate physical surplus, unused output and redirected sales. The existing daily schedule also gives a simple ceiling on surplus capture under the 10 t/day contract: 29 surplus days × 0.559 GWh/day = 16.211 GWh, or 2.95% of the 2023 surplus.
- **Review dispositions.** The replay window is labelled 2022–25, the independent CU check is cited, the stress changes initial installation cost while holding stack cost fixed, the 2025 downside is named after the results table, and the negative-price implication of B is stated. At 99.99% the sales constraint binds, so 21.51 GWh is both the realised reduction and the allowance. The fixed 20 MW break-even remains GBP 4.614536/kg under A in both implementations. The different CU unrestricted switching point depends on its relative solver cutoff. The updated layout uses consistent minus signs, vertically centred row labels and taller trigger panels with fixed-capacity break-even markers.
- **Validation.** The model and published decisions are the same as in the verified Tier 1 calculation. The sample records solver size, independent checks and the dated cash-flow basis. The template and sample were compiled and visually checked at one and four pages respectively.

Sources for review are the [2026/27 brief](https://github.com/MocryMin/mmcs-group15-project/blob/38f82d5/Project_Brief.pdf), the [briefing transcript](https://github.com/MocryMin/mmcs-group15-project/blob/38f82d5/Project_Launch_Transcript_Timed.txt), the [v1 calculations and CU comparison](https://github.com/MocryMin/mmcs-group15-project/tree/71ce76e/Tier1/workspaces/mocry/codex/tier1-independent), [CU's review](https://github.com/MocryMin/mmcs-group15-project/blob/024edd1/Tier1/workspaces/mocry/cleveruser/review/20261105-codex-4pp/REVIEW.md), and [Opus's onboarding observations](https://github.com/MocryMin/mmcs-group15-project/blob/38f82d5/Tier1/agent_message/messages/20261105T225005381725Z_mocry-claude_c5f0b466d6674241a518a507f3220597.md).
