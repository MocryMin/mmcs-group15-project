# mocry-claude session state

Updated 2026-11-25T01:10Z · agent `mocry-claude` · member `mocry` (Ran Min)

## Setup
- Registered at `0bcd9bc` (event `652234e533c744628b3b7158f9b2d47e`).
- Works in the owner's local clone through a sandboxed shell with no GitHub network access; the owner pushes with his own Git.
- No Xpress in the sandbox.

## Read through
- Repository up to `024edd1`, all Tier1 messages up to `14fecd9ec87a4305aefc33af457ead67`, the Tier2 bootstrap message.

## Sent
- `c5f0b466d6674241a518a507f3220597` → mocry-codex (notice/action): four onboarding observations (no decision record, three unanswered CU requests, 8% surplus-capture framing risk with 13.92 = 29 × 0.48 GWh, rubric text not archived) and an offer to prepare a Tier 2A/2B comparison for the owner.

## Reviews
- `review/20261106-tier1-candidates/REVIEW.md`: independent comparison of Codex `d906c03` (technical-report-latex/20261105-v2) and CU `665bade` (report/20261105-v1). Verdict: Codex skeleton + CU presentation layer; as-is ≈70 vs ≈68; merged 76–80. New finding: 2023 is the lowest-surplus year (29 surplus days vs 154 in 2022); under B a fixed 20 MW averages +£2.12m/yr over 2020–25.
- Not yet sent to either agent; waiting for the owner's choice of base.

- `review/20261110-v4.1-academic/REVIEW.md`: review of Codex v4.1 academic candidate (request `1bff0d2d1ba0416fa541b818d5c2012f`). No numerical errors; adopt as Tier 1 base after three P0 fixes (page-count confirmation, a decision-form conclusion, the brief's £9.50/kg benchmark). Unofficial estimate ≈72 (A3), 76–79 after fixes. Reply `9446a4d0764142889e162cf3fb692581`.

- `review/20261122-tier1-independent-standard/STANDARD.md` (commit `9d86960`, written before opening v5) and `review/20261122-tier1-v5-content/REVIEW.md`: content review of Codex v5 (`98b316f`). Unofficial ≈68 (range 64–72) vs ≈72 for v4.1. Main issues: common configuration at UK-scale electrolysis (845/362 modules) while recommending site scale; HAR1-based netback applied to diverted grid power that cannot meet the LCHS threshold; positive battery only under four non-brief assumptions; £9.5/kg still unreported.
- Reported to Codex: `tools/collab.py` tree() loads all blob contents and is killed at 8 GB after the 3 GB archive; proposed a blob-id-based fix.

- `review/20261123-tier1-v6-content/REVIEW.md`: re-review of v6 (`2f02e3e`) against the unchanged standard. All tables reproduce from the evidence ZIP. Unofficial ≈72 (v5 ≈68). Remaining P0: electrolyser minimum-run rule (B cannot complete a 4-day run: longest surplus stretch 56 h, recomputed from v7 inputs) and the Tier 2B hand-off uses 45/9 blocks instead of the recommended one block. (Correction in the v6.1 review: the Q&A transcript was in the v6 evidence ZIP under course-sources; I had missed it.)

- `review/20261123-tier1-v6.1-content/REVIEW.md`: re-review of v6.1 (`589b9d5`), reply to request `78956f30d3694d8fad4ea5b9805e3285`. Unofficial ≈74 (range 71–77). Both v6 P0s closed in wording. Q&A transcript read line by line (lines 86, 92–128: teachers reject hourly switching; minimum load via long-term contract). Main P1: make the operating-limits plan primary (A 6 modules / 30.2 MW; B 50.3 MW only with a minimum-load contract), give A's four-day finance, report Tier 2B by window (A −31.55/−14.70/+25.57, B −3.62/+2.50/+8.87 £m), run the one-block matched replay, full Xpress licence, use the four spare body pages, add method literature.


- `review/20261124-tier1-v6.2-content/REVIEW.md`: re-review of v6.2 (`2d8a0d8`), reply to request `98f4331f96ab4bc4a00094864bbc2403`. Unofficial ≈75 (range 72–78). One P0: the main case uses the 12.5% product floor although the brief says "Assume … between 20% and 100%" and Q&A lines 119/125 say 20% or higher (A 7 modules → 6 at 20%). P1: abstract and the only body figure feature the non-recommended 45/6 portfolio; hydrogen price and eligibility (38.4% from surplus vs 24.9% needed) dropped from the body; B one-block six-window evidence (+7.57 total, −1.24 excl. 2021/22) not reported; A Tier 2B handover still flexible with an unexplained 7 blocks; A main result has no Xpress; body still 6 pages.

- `review/20261124-v6.5-acceptance/REVIEW.md`: acceptance review of the project report v6.5 (`3b0318e`/`044f446`), reply to request `8fffc2dd58cb49d0bb43d4dfa77f69f1`. Accepted as submission candidate, no blockers; unofficial ≈78 (range 75–81). The v6.2 P0 (20% floor) is resolved: both floors are in Table II.3/II.7. Recommended, not blocking: lead with 6 modules / 30.2 MW, since it is optimal at 20% and feasible at 12.5% (the 7th module adds ≤ £0.22m/yr); add the eligibility sentence (34.1% from surplus vs 25.5% needed at 20%); reword Verification so Xpress comes first; cite the one-block Table III.1 results in §5.5.

- `review/20261124-v7-content/REVIEW.md`: review of project report v7 (`1bb26de`/`2dfb603`), reply to request `2a8e5658a479411b8ba10a747cd8a43f`. No blockers; unofficial ≈79 (range 76–82). All v6.5 acceptance items adopted; full-licence Xpress resizing closes T1-14; renewable capture added (Table C.3). M1: the recommended 6-module plant gets only 14.8% of its input from renewable surplus (28.1/190.4 GWh, 1.2% of the 2,432 GWh/yr renewable surplus), below the 25.5% two-rate break-even, so the §5.5 "34% all-fuel surplus" sentence overstates eligibility. M2: Table II.6 is still at 12.5%/7 modules. M3: Table C.1 needs a best-alternative upper bound column to separate certified counts (margin £7,030/yr) from the dispatch gap (£2,600/yr).

- `review/20261125-v7.1-recheck/REVIEW.md`: recheck of v7.1 (`311c6cd`), reply to request `23f4acc1607549389f3e274281f7b198`. Passed, no blockers; unofficial ≈80 (range 77–83). v7 M1–M3 all resolved and verified: 25.4% break-even share, 14.8% renewable gives −£1.93m/yr, Table II.6 at 20%, other-count bound column. Optional P2s: at £9.50 even 20% picks 7 modules (say so in §5.5); abstract should state the support condition and ~1% renewable capture; add the £7,030 margin in §5.1.

## Open
- Waiting for a Codex reply on the 2A/2B comparison offer.
- Tier 2 route is the owner's decision; nothing here chooses it.
