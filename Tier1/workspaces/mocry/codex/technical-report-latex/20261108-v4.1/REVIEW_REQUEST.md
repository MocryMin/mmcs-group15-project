# Review request: v4.1 academic candidate

Ran Min explicitly requests an Opus review of the latest report and complete package.

## Material

Read `report.pdf` in this directory and the source/data/code in the accompanying ZIP. The latest ToC includes the subsection level. `VERSION.json` pins the PDF and ZIP hashes. The full original brief and four-page report marking descriptors are inside `references/` in the ZIP. The rubric PDF retains its internal 25/26 title although it was retrieved from the current course.

## Fixed owner framework

Use the owner's current academic framework: Abstract/Contents separately numbered, then common background/data/notation (2 body pages), Tier 1 (at most 4), and Tier 2B (at most 4); Tier 1 plus Tier 2 at most 8 body pages. References are separated under the owner's instruction. Chapters are centred Roman numerals and sections Arabic numerals. Do not restore the earlier KPI cards/marketing decision box. The owner prioritises sequential explanation, definition-before-use, evidence and information density.

## Requested checks

1. Read sequentially: identify any noun/model quantity, assumption, data value or comparison whose meaning is not available when first needed; cite the exact page/paragraph.
2. Check the mathematical formulation, units, domains, policy A/B, cost and zero-investment comparison against the Python implementation and stored schedules.
3. Assess Table II.3's portfolio/yearly panels and Table II.4's sensitivities, including fixed vs optimised capacity, production units, policy-specific counterfactuals and real sales lost. Flag missing comparisons that would materially weaken the result discussion.
4. Inspect layout and all tables/figures. Prioritise usable information and legible hierarchy, rather than decorative presentation. Confirm page budget and referenced items.
5. Review the written assumptions/source traceability, including the brief's hydrogen benchmark and the separately rebased support-value scenario; distinguish a genuine numerical error from an explicitly chosen scenario.
6. Assess against the supplied report descriptors (first six dimensions weight 1, Presentation weight 2). Any numerical score is an internal estimate, not an official grade.

Chapter III is a method/evaluation specification. No predictive experiment result or control performance has been completed. Review its coherence and major design gaps; do not score its placeholders as an implemented Tier 2B result or import the obsolete 2 November prototype's numbers.

Please return severity-ranked findings with page/equation/table references and concrete fixes, plus a recommendation on this Tier 1 candidate. Work in your own `Tier1/workspaces/mocry/claude/` review folder and reply through a new message. Keep the Codex candidate intact during the review. There is no newly imposed review deadline.
