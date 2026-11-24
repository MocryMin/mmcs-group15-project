# v6.5 verification of the Tier 1 report candidate

Verifier: `mocry-cleveruser`. Date: 2026-11-24.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261124-v6.5/report.pdf`
sha256 `4ffabb3aa479de3ed94e51ec6845e73ecfe155cb8fc4f9c24deba2cc5c36520c`, 195,997 bytes, 15 PDF pages
(cover/abstract i, contents ii, body 1–6, R1, A1–A6). Published at `3b0318e`; the checksum file was relabelled in
`044f446` ("Align v6.5 evidence checksum with Git line endings"); the review requests were sent at `3a4f8ec`.
Sources: `report-source.zip` sha256 `746c1162…96d9` (10 files, 8 LaTeX + 2 figure PDFs);
`display-table-evidence.json` sha256 `faf94771…482b` (new machine-readable table values);
`tier1-site-evidence-v6.3.zip` sha256 `202bb3de…997a` (34 entries, `MANIFEST.json` with 33 payload hashes).
All four digests agree with `SHA256SUMS.txt`, and the working-tree bytes are the published bytes — the `044f446`
line-ending commit did **not** change any artefact, so no CRLF reconstruction was needed.
Baselines: the pinned v6.2 archive `tier1-site-evidence-v6.2.zip` (`3a1a9377…bd3e`, 132 entries; still the source of
the 12.5% sizing certificates and the half-hour panel), the pinned v6 archive `tier1-site-evidence-v6.zip`
(190 files; two-hour and flexible-switching studies), and Julian's study at commit `c3902fe`,
`Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1`.
Standard: `../20261122-tier1-independent-standard/STANDARD.md`, `ADDENDUM_1_OFFICIAL_RUBRIC.md`,
`ADDENDUM_2_PAGE_RULE.md` (10 pages means body pages).
Machine checks: `v6.5_checks.py` → `checks_v6.5.json`, **199 checks, 2 failures**; both failures are the P2 bookkeeping
items P2-2 and P2-3 below, not headline numbers.
Independence: I read `mocry-codex`'s request (`2830fe8d…0b37`) and then the artefacts. No other agent's v6.5 review
was consulted, and every number below was recomputed from the archives, the LaTeX source or Julian's commit.

## Verdict

v6.5 closes the two structural gaps I recorded against v6.2 and does not regress any printed number. The 12.5% and 20%
load floors are now sized, financed and compared on one basis; A's four-day chronological replay, which v6.2 listed as
"yet to be evaluated", exists and reproduces from a 552-row ledger; the Xpress role is wider (stand-alone A at both
floors, the 45/6 schedule, the B subproblems, 192 sampled Tier 2B windows) and its boundary is stated honestly.
Every value in Tables I.2, II.3, II.4, II.5, II.6, II.7, III.1, B.1, C.1–C.3 reproduces from the shipped archives or
from Julian's commit; the two failures in the check set are a £0.01m rounding and one stale bound field.

One compliance item is retained, narrowed: the headline recommendation still rests on the product's 12.5% floor where
the brief instructs 20%–100%, and the report never states why that departure is admissible. Score **84** (range 81–87;
v6.2: 81).

## Disposition of my v6.2 items

| v6.2 item | v6.5 status | Evidence |
|:--|:--|:--|
| **P1-1** main case uses 12.5% where the brief says 20% | **Mitigated, narrowed P1.** Both floors appear in Tables II.3 and II.7, §5.5 quantifies the trade-off (£0.22m/yr for £7.35m), the abstract links 12.5% to "confirmation of operating limits from the supplier" and prints the 30.2 MW brief-floor plant. What is still missing is a sentence saying why a floor below the brief's assumption may be used at all. | pp. 4–5; `A-7-finance.json`; `A-zero-finance.json` |
| **P1-2** A's capacity search is HiGHS, not Xpress | **Downgraded to P2.** Xpress now re-solves stand-alone A at both floors (7 fixed-boundary chunks each, 3,840 and 3,520 rows+columns ≤ the 5,000 licence cap) and reproduces the HiGHS value to £0.0000001m; the joint capacity MILP is still HiGHS, and the licence limit is named in §4.2 and Table C.1. | `A-seven-module-xpress.json`, `A-zero-verification.json`, Table C.1 |
| A four-day chronological replay absent | **Closed.** Table III.1 A columns, the 552-row `six-fold-capacity-replay.csv`, and §III.2's rule statement agree cell by cell. | Table III.1; `tier2b-commitment-125-20261124/` |
| Figure I.1 did not count spells by minimum duration | **Closed.** 2,891 spells at 0.5 h, monotone counts, longest 56 h at both floors, 96 h rule drawn and labelled. | `surplus-spell-counts.csv`, `surplus-spells.json`, p. 1 render |
| Figure II.1 panel B bar above the top tick and mean label over the bars | **Closed.** B axis now −31…90 with −25…75 ticks, the 2022 bar sits inside the frame, the mean is an unlabelled dashed line. | p. 4 render; `annual-net.pdf` |
| §5.4 "Battery ." spacing | **Withdrawn — my v6.2 item was wrong.** The source is `\textbf{Battery.}`; the gap is a text-extraction artefact, and the rendered page reads "Battery. Defer purchase…". | `sections/tier1.tex`; p. 5 render |
| "With 2.5% upkeep, both increments are negative" easy to misread | **Closed for wording, new rounding slip.** Now "the increments fall to annual losses of £0.24m and £2.60m" — the A value should be £0.23m (P2-2). | p. 5; `fixed_pair.csv`; `reference_day_A_integer.json` |
| One battery's six windows not printed | **Closed.** Table III.1 carries 1-block columns for both policies. | Table III.1; `selected-six-fold-net-GBP.csv` |
| "No starts in the last three days" not in (II.8) | **Closed.** §4.2 states `m_d = 0 for d > N_D − 3` and the reason. | p. 3 |
| Cover carries no named authors | **Unchanged.** Still "Group 15" only. | p. i |
| 1,559 t/day broad-market row carries no file | **Unchanged.** Still author-reported in Appendix A.2. | p. A2 |

## P0 — none

No headline is wrong, no scale mismatch, no misleading claim. The page gate holds: six body pages against the owner's
ten, and the model stays in the body (§4). Every headline is recomputable from the shipped artefacts.

## P1 — one narrowed compliance item

### P1-1 The recommendation still leads with the product floor, not the brief's floor

- **What the sources say.** Brief p. 3: "Assume that the electrolyser can operate between 20% and 100% of installed
  capacity", repeated in the parameter table ("4 MW and 20 MW"). Q&A transcript (archive [20],
  `course-sources/Project Q and A transcript.txt`) line 119: "whether it's 20% or something higher"; line 125:
  "you have to operate it at at least the 20%".
- **What v6.5 does.** Table II.2 prints the ITM NEPTUNE V band 12.5–100%; §II.3 states "We test minimum loads of 12.5%
  for NEPTUNE V and 20% from the brief"; Table II.3 carries both four-day rows; Table II.7 carries the full finance
  pair; §5.5 states the trade-off; the abstract says the brief's 20% "reduces the plant to 30.2 MW".
- **What is still missing.** No sentence argues that a floor below the brief's assumption is admissible, or names the
  30.2 MW plant as the brief-compliant recommendation. The deviation is also not paid for in economics: the seven-module
  plant gains £0.22m/yr (£13.68m vs £13.46m) for £7.35m more capital, so payback is *worse* (2.85 vs 2.56 y), NPV is
  only 1.6% higher (£210.28m vs £206.91m) and the break-even receipt is lower at 20% (£3.85 vs £3.82/kg).
- **Assessment.** Not a numerical error and not a blocker for the numbers; a compliance and emphasis choice. A marker
  checking the brief's assumption will see the 20% column and the abstract sentence, so the exposure is moderate rather
  than fatal. The fix is one sentence plus one reordering: recommend the 30.2 MW/20% plant, present 12.5% as a
  supplier-conditional option worth £0.22m/yr, and state that the condition is a written confirmation of the sustained
  minimum load from ITM.

## P2 — clarity, traceability and bookkeeping

1. **Figure I.1 left axis drops the per-half-hour basis.** The plotted series is mean surplus *per half-hour slot*
   (`surplus = max(G−D,0)` in MWh, mean ÷ 1000), so the winter peak of 1.5 is 1.5 GWh per half-hour ≈ 3 GW, but the axis
   reads "Mean surplus (GWh)". The archived `prepare_evidence.py` labels it "GWh/half-hour" — and also labels the right
   panel "Consecutive hours" / "Spells at least this long", which is **not** what the shipped figure says ("Duration
   threshold x (hours)" / "Number of surplus periods lasting at least x hours"). The script also writes to
   `project-report-20261124-v6.3/report/figures`, which is not in the bundle, so "run `prepare_evidence.py` for
   exhibits" does not reproduce the shipped figure exactly. Values are right; the unit label and the exhibit source are
   one revision apart.
2. **£0.24m should be £0.23m.** §5.4: 2.5% of the brief block capital is 0.025 × £51.247m = £1.281m; the A increment is
   £1.0505m, so the loss is £0.2307m, printed as £0.24m. B is exact (−£1.318m − £1.281m = −£2.599m → −£2.60m).
3. **The 20% capacity certificate contradicts itself on the bound.** `A-capacity-certificate.json` has
   `upper_mGBP` 118.820805 and `global_upper_mGBP` 118.819823, i.e. the winner's own local upper bound exceeds the
   reported global upper bound — impossible if both come from the same grid. The 12.5% certificate is consistent
   (118.900889 ≤ 118.900891). The printed "£118.819824m global upper bound" is also a 1e-6 over-round of 118.8198235.
   The conclusion is unaffected (the best alternative upper is 118.811176, £7,031 below the feasible 118.818207), but
   one field is stale and should be regenerated.
4. **Table II.3's 20% joint "Served 90.16%" has no source field.** The cell uses the shared `\TwentyCoverage` macro and
   the 20% certificate has no `served_pct`; the 12.5% row is backed by `main-schedule-summary.json`. Either print an
   independently computed value or add the field.
5. **Table III.1 omits the count its own text highlights.** §III.3 says "the sum is highest at 11 blocks for each policy"
   (A Σ £22.99m, B Σ £40.97m from `capacity-summary.csv`), but the table prints 1/7/45 and 1/9/22. A reader cannot verify
   the sentence from the table; add an 11 column or drop the claim.
6. **Author names.** Still only "Group 15" on the cover.
7. **Broad-market row.** The 1,559 t/day case on p. A2 remains author-reported: no file in any of the three archives.
8. **Basis change is not marked.** Tier 2B A moved from the flexible-switching basis of the v6.2 draft (Σ £28.31m) to
   the matched four-day committed basis (Σ £20.40m; 45 blocks −£139.86m vs −£21.26m). The new numbers are internally
   consistent and §III.2 describes the rule, but a reader who saw the earlier draft has no note that the basis changed.

## Visual notes

Pages rendered and inspected: 1 (cover/abstract), 3 (Fig. I.1, Tables I.1–I.2), 6 (Table II.3, Fig. II.1, Table II.4),
7 (Tables II.5–II.7, §5.5), 8 (Table III.1), 14 (Table C.1). Text was read for all 15 pages.

- Figure I.1: log axis 10⁰–10³, "Longest: 56 h" marker on the last point, dashed 96 h rule inside the frame, legend
  above the axes without collisions. Only the left y-unit is wrong (P2-1).
- Figure II.1: A −100…400, B −25…75 with the 2022 bar above the 75 tick but inside the frame; unlabelled dashed mean
  line; both panels titled; caption carries counts, scenario and the different scales.
- Tables II.3 and III.1: both fit the text block with no overfull rows; the six numeric columns of Table III.1 align and
  negative signs render as minus.
- "Battery." renders with no gap; the v6.2 "Battery ." sighting was an extraction artefact (P2 withdrawn above).
- Page breaks: body pages 1–6, Chapter III starts cleanly at the top of body page 6, R1 then A1–A6 as labelled.

## Numbers that were checked (selection of the 199)

| Item | Recomputed | Source |
|:--|:--|:--|
| Table II.3 12.5% pair | 0/7 £13.68m 89.61%; 45/6 £118.90m 90.16%; flexible 45/6 £119.04m | `A-7-finance.json`, `main-schedule-summary.json`, `site_portfolios.csv` |
| Table II.3 20% pair | 0/6 £13.46m 89.61%; 45/6 £118.82m | `A-zero-finance.json`, `A-capacity-certificate.json` |
| 20% dual bounds | feasible 118.818207, global upper 118.819823, best alternative 118.811176, certified, no rivals left | same certificate |
| 12.5% dual bounds | feasible 118.898893, upper 118.900891, 46/6 upper 118.890634 | v6.2 certificate |
| Table II.7 12.5% | 7 modules, 35.217 MW, £51.432m, £13.679m, 9.811, 2.847 y, £210.283m, £3.8198/kg | `A-7-finance.json` + display table |
| Table II.7 20% | 6 modules, 30.186 MW, £44.085m, £13.460m, 8.666, 2.560 y, £206.907m, £3.8478/kg | `A-zero-finance.json` + display table |
| Payback identities | 7·7.34747/(18.97497−0.91077)=2.8472; 6·7.34747/(17.99883−0.78066)=2.5604 | finance files, Xpress replays |
| NPV | 13.6792 × 15.37246 = 210.28; 13.4596 × 15.37246 = 206.91 | same |
| 20% side effects | 3,406.4 t/yr, 125.39 GWh diverted, −0.0495 pp coverage, 154 starts, 0 loss years | `A-zero-finance.json` |
| Table II.4 | 118.90 / 6.07; 39.12 / −13.07; 19.53 / −12.85; 65.10 / −8.01 | display table; `main-schedule-summary.json` |
| Table III.1 | 36 cells + 12 totals/excl rows match the 552-row ledger to the penny | `selected-six-fold-net-GBP.csv`, `six-fold-capacity-replay.csv` |
| T2B peaks | reference window 7 blocks (A +£0.695m), 22 blocks (B +£12.510m); six-window 11/11 (A £22.99m, B £40.97m); ex-2021/22 negative at every positive count | `capacity-summary.csv` |
| B invariance | B 9-block column identical to v6.2 (−4.20, 65.31, −3.95, −16.83, −9.45, 8.57) | v6.2 `comparison.csv` |
| T2B Xpress audit | 192 draws (6 windows × 4 counts × 8 samples), max |Xpress − DP| = £0.037, bound assertion holds in every row, 190 optimal + 2 status-4 with gaps ≤ £286.85 | `continuous-xpress-audit.csv` |
| Fig. I.1 | 2,891 spells, longest 56 h at 12.5% and 20%, no spell ≥ 96 h, threshold 0.125 × 5.031 MW = 0.629 MW = 0.3144 MWh per half-hour | `surplus-spell-counts.csv`, `surplus-spells.json` |
| Surplus totals | 24.75% of half-hours, 5,164.7 / 2,276.2 GWh/yr, 2,192 days | `surplus-spells.json` |
| Xpress chunks | A 12.5%: 7 chunks, 960+2,880; A 20%: 7 chunks, 960+2,560; chunk sums equal horizon values within £0.05 | `A-seven-module-xpress.json`, `A-zero-verification.json` |
| Solver baselines | 13,155 cols / 24,113 rows, 0.5 s; 551 blocks, 4.3 s, gap £5.1; 16.8 s, gap £0.17; £4/yr gain | `reference_day_*.json`, `site_A_xpress.json`, `B_n9_h10.json` |
| Strict B | 9 blocks £6.070m, 8 blocks £6.070m (−£639/yr), 561 = 536 + 25, gap £0.167, hydrogen bound £0.326m vs £0.757m, 116 days | `B-battery-certificate.json`, `B-hydrogen-bound.json` |
| Table II.5 / B.1 | 12.46/2.18, 13.42/14.47/3.78/2.46, ±1.05/−1.32, £213/£130 per kWh; 14.10/5.48, 13.18/−8.14, 13.16/−8.32, 13.46/0, 13.68/0 | `fixed_pair.csv`, `reference_day_*.json`, Julian `operating_rules.csv`, `main_table.csv` |
| Table C.2 / C.3 | eight window pairs; twelve contract rows; two-rate 11 modules £6.06m at £6.58/kg; NPV 8% £144m/£42m; +20% capex £3.91/£5.30; B 41.6% | `fixed_block_windows.csv`, `contract_sizing.csv`, `electrolyser_finance.csv` |

## Author-reported, not independently re-run

- The optimisation itself: I read the saved schedules, certificates, ledgers and audit tables; I did not re-solve the
  MIPs, the dynamic programmes or the Xpress subproblems.
- The 20% stand-alone optimum is **six** modules: `run_a.py --zero` writes `A-zero-sizing.json`, but that file is not in
  the bundle, so the sweep that rules out five and seven is missing. The value is corroborated by Julian's independent
  `main_table.csv` (A, electrolysis only, 20% floor: 6 modules, £13.46m, £44.08m, 2.56 y) and by the certificate's
  `certified_fleet: 6`.
- Completeness of A's count screen over the full (blocks, modules) grid; the 17 retained relaxations are not re-solved.
- Tier 2B forecast training, the classifier refits and the dependency on the frozen fold inputs, which the README names
  but the bundle does not contain.
- The EHO consumption totals and the 1,559 t/day broad-market row.

## Score

Scored on the same descriptor convention as v6.1 and v6.2 (seven dimensions, presentation ×2).

| Descriptor (weight) | Anchor | Fraction | Basis |
|:--|:--|--:|:--|
| Understanding & Depth (1) | A3+/A2− | 0.82 | Commitment, both load floors, licence-capped solvers and the B exclusion bound are understood; the brief's floor is still not the recommendation |
| Originality (1) | A2− | 0.86 | Own dual-bound certificates at two floors, revenue-bound exclusion for B, fixed-boundary Xpress decomposition, matched replay |
| Amount of Work (1) | A2− | 0.89 | 552-row replay, 192 window audits, 48 enumerations, 20% re-run and finance, figure data, three pinned archives |
| Logic of Argument (1) | A3+/A2− | 0.82 | Chain is coherent end to end; the headline still opens on the non-brief floor and one sentence rests on an untabulated count |
| Background & References (1) | A3+ | 0.82 | [23]–[25] pin the archives; sources unchanged from v6.2 |
| Validity of Results (1) | A2− | 0.88 | 197 of 199 checks pass; dual bounds, cross-solver equality, per-window reconciliation, held-out data errors |
| Presentation (2) | A3+/A2− | 0.83 | Figure I.1 labels and Table II.7 layout improved; unit slip, missing 11 column, no authors, one £0.01m slip |

Weighted: (0.82 + 0.86 + 0.89 + 0.82 + 0.82 + 0.88 + 2 × 0.83) / 8 = **84** (v6.2: 81; range 81–87).

The gain is real rather than cosmetic: v6.2's two P1s are now one narrowed P1 and one disclosed P2, and the work
volume and validation both grew. What holds it out of the mid-80s is the emphasis on the product floor and four small
traceability defects, all cheap to fix.

## What would change the score

- **Upward (86–87).** Lead with the 30.2 MW/20% plant and demote 12.5% to a supplier-conditional option (one paragraph,
  no new numbers); add the 11-block column or drop the six-window claim; fix Figure I.1's unit; correct £0.24m to
  £0.23m; regenerate the 20% certificate so `upper_mGBP ≤ global_upper_mGBP`; add author names; ship
  `A-zero-sizing.json`; note that Tier 2B A moved to the committed basis.
- **Downward.** If a marker treats the brief's 20% as binding, the A recommendation must be re-sized — the compliant
  plant already exists in Table II.7 (£44.08m, 2.56 y, £206.91m), so the cost of compliance is presentation, not
  modelling. Nothing in Tier 2B or the B conclusion depends on the floor.
- **No numeric regression.** Every carried baseline (site portfolios, two-hour references, contract table, window
  sensitivities, electrolyser finance, Xpress replays, B certificates, Julian's 20% rows) is re-asserted in
  `checks_v6.5.json` and passes; the only unverified carry-overs are the author-reported items above.
