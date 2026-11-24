# v6.2 verification of the Tier 1 report candidate

Verifier: `mocry-cleveruser`. Date: 2026-11-24.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261124-v6.2/report.pdf`
sha256 `4837c08d330d8bb938c9dd41831c4042d4bf457e3a8238e0b0c34a62bbd6f1ea`, 155,073 bytes, 15 PDF pages
(cover/abstract i, contents ii, body 1–6, R1, A1–A6). Published at `2d8a0d8`.
Sources: `report-source.zip` sha256 `20aacf7c…602a` (10 LaTeX files); `README.md` `a800a3f6…512e`;
`REVIEW_RESPONSE.md` `a6d24932…5453`. All five digests agree with `SHA256SUMS.txt`.
New evidence: `tier1-site-evidence-v6.2.zip` sha256 `3a1a9377…abd3e`, 132 entries,
`MANIFEST.json` with 131 payload hashes.
Baseline evidence: the pinned v6 archive `tier1-site-evidence-v6.zip` (`f4c0e6e5…b50440`, 190 files) and
Julian's study at commit `c3902fe`, `Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1`.
Standard: `../20261122-tier1-independent-standard/STANDARD.md` (unchanged; the page rule is
`ADDENDUM_2_PAGE_RULE.md`: 10 pages means body pages).
Machine checks: `v6.2_checks.py` → `checks_v6.2.json`, **188 checks, 0 failures**.
Independence: I ran the numbers and the archive reads first. `mocry-claude`'s v6.2 review
(`1ef6a9e`) was read as a lead only; its one structural point that survives is re-derived below
from the brief and the Q&A transcript, and I grade it differently.

## Verdict

v6.2 is the strongest Tier 1 candidate so far and the first version whose operating rule, capacity
certificate, financing and Tier 2B handover agree with each other. Every printed number I could
trace reproduces from the two archives or from Julian's commit; no arithmetic error was found and
no earlier v6/v6.1 number regressed.

Two P1 compliance/parameter items remain: the main case adopts the supplier's 12.5% load floor
although the brief instructs 20%–100%, and the brief asks for the Xpress optimiser for the main
modelling work while A's four-day capacity search is HiGHS. Both are disclosed in the report, both
are cheap to fix, and neither changes the B conclusion. Score **81** (range 78–84).

## Disposition of my v6.1 items

| v6.1 item | v6.2 status | Evidence |
|:--|:--|:--|
| Main-case operating rule unresolved (headline answered with half-hour switching) | **Closed.** Base case is midnight switching plus four-day runs; ABSTRACT, §II.3 and (II.8) state it; the half-hour case is a sensitivity. | Table II.3 rows 4–5; §5.3; Table B.1 |
| A's four-day case had no capital/NPV/payback | **Closed.** Seven-module plant carries capital £51.43m, payback 2.85 y, NPV £210.28m, break-even £3.82/kg, 118 GWh diverted. | `A-7-finance.json`; §5.4 |
| Tier 2B pooled sums hid window signs | **Closed.** Table III.1 gives six windows with totals and ex-2021/22 sums. | `a-stability.csv`, `comparison.csv` |
| Ref [9] still said "accompanying package" | **Closed.** [9] names `research/PARAMETER_BASIS.md` in `tier1-site-evidence-v6.zip`. | p.9 |
| Xpress "£4/year" direction inconsistent | **Closed.** "improves … by about £4/year" matches the replay delta. | Table C.1; `site_A_xpress.json` |
| Cover carries no named authors | **Unchanged.** Still "Group 15" only. | p.i |
| A four-day replay absent | **Disclosed open** in §III.3 and REVIEW_RESPONSE. | p.6, REVIEW_RESPONSE |
| New: "With 2.5% upkeep, both increments are negative" is easy to misread (present since v6.1, not weighed then) | **P2** below | p.5; §5.3; `reference_day_A_integer.json` |

## P0 — none

No headline number is wrong, no scale mismatch, page gate satisfied (six body pages against the
owner's ten), and every headline is recomputable from the published artefacts.

## P1 — material weaknesses (2)

### P1-1 The main case uses a 12.5% load floor where the brief says 20%

- **What the sources say.** Brief p.3: "Assume that the electrolyser can operate between 20% and
  100% of installed capacity"; the parameter table repeats it ("a 20 MW electrolyser would normally
  operate between 4 MW and 20 MW"). The Q&A transcript (archive [20], `course-sources/Project Q and
  A transcript.txt`) line 119: "set a minimum threshold … whether it's 20% or something higher";
  line 125: "if you have an electrolyzer, you have to operate it at at least the 20%".
- **What the report does.** §II.2 prints the brief's 20% floor (Table II.1) and the abstract prints
  "the product's 12.5% minimum load"; §II.3 attributes the 12.5–100% band to the supplier [14].
  The body never states that the brief's 20% is being replaced, nor why; the brief-consistent
  four-day case appears only in Appendix B.1 (row 5: six modules, £13.46m).
- **Why it matters.** The recommendation's size and capital follow from the departing parameter:
  7 modules / 35.2 MW / £51.43m / 2.85 y at 12.5%, versus Julian's 20% case of 6 modules /
  30.2 MW / £44.08m / 2.56 y / NPV ≈ £206.9m (verified from `main_table.csv`: 13.4596 × 15.3725).
  A reader applying the brief's floor would size a different plant.
- **Severity note.** I record P1, not P0: both bands are printed, so the value is not hidden, and
  the 20% case exists in the archive and in B.1. But a client specification is being replaced by a
  supplier datasheet without an argued departure, and the body recommendation does not carry the
  brief-consistent alternative.
- **Fix (cheap).** In §5.4 put the 20% six-module plant (30.2 MW, £44.08m, 2.56 y) as the
  brief-consistent case and the 12.5% seven-module plant as the "supplier-confirmed low-load"
  upside, with one sentence naming the departure; add Julians' 20% capital/payback to Table B.1.
  This is exactly the sensitivity Table B.1 already contains.

### P1-2 A's capacity search and commitment certificate are HiGHS, not Xpress

- **Source.** Brief p.1: "The main modelling work should be implemented in Python using the Xpress
  optimiser." REVIEW_RESPONSE lists "a full-licence Tier 1 Xpress rerun" as open.
- **What the report does.** §II.4 Verification states HiGHS gives A's feasible schedules and
  capacity bounds; Table C.1 records Xpress 9.9 for the 45/6 replay (551 blocks, gap £5.1/yr) and
  for B's 536 empty-stock subproblems. So Xpress is used, but not for the sizing decision.
- **Severity note.** P1, not P0: the numbers are dual-solver verified (feasible HiGHS schedules
  inside certified bounds), the split is disclosed, and the Community licence explains the
  decomposition. It is a submission-readiness item against a written course requirement.
- **Fix.** With the full licence, solve one A four-day model with Xpress — the zero-battery
  seven-module case and the 45/6 fixed portfolio are small enough to record `Xpress 9.9,
  status, rows/columns, gap` in Table C.1; then say in §II.4 which A runs are Xpress.

## P2 — clarity and traceability

1. **"With 2.5% upkeep, both increments are negative" (p.5) reads as contradicting the +£1.05m
   printed immediately before it.** The claim is true: the solved `brief-2h` product carries
   `fom_GBP = 0.0` (capital £51.247m, annual charge £4.938m), so +£1.05m and −£1.32m exclude upkeep;
   adding 2.5% of capital (£1.281m) gives −£0.24m and −£2.60m. Table II.4's caption "Gains are net
   of equipment costs" does not say the two-hour rows omit maintenance. Fix: print the
   maintenance-adjusted increments or say "before the brief-block's 2.5% upkeep; with it, −£0.24m
   and −£2.60m".
2. **Figure II.1.** Panel B's 2022 bar (£76.49m) rises above the last gridline (75) although the
   axis limit is 88, and the "Mean £6.07m/yr" annotation sits at 92% of the axes height and collides
   with that bar; panel A's label sits at the same relative height. Fix: put the mean label on the
   dashed line, set the top to 90/450, or annotate in the caption.
3. **"Battery ."** in §5.4 (space before the full stop) — typesetting slip.
4. **Cover has no named authors.** Carried from v6.1; "Group 15" is the only identifier.
5. **A's four-day chronological replay is absent.** Disclosed ("has yet to be evaluated"), and the
   recommendation is conditional, but the A handover in Table III.1 remains a flexible-switching,
   seven-block portfolio while Tier 1's A case is four-day. The B handover is exact.
6. **Broad-market (1,559 t/day) numbers are not in either archive.** "A power of 4,100, 900 and
   0 MW … gains £46.46m, £0.93m" and the B rows are author-reported; neither `tier1-site-evidence-v6.zip`
   nor the v6.2 bundle contains a file with those runs. Disclosed as author-reported in my
   v6.1 review; still worth archiving or dropping to a sentence.
7. **One-block chronological evidence beyond the reference year is available but not printed.**
   `size-sweep-folds.csv` gives the nine-block…one-block six-window series (1 block: +£7.58m total,
   −£1.23m excluding 2021/22, three of six windows positive). The advice "test one block first"
   would be stronger with those three numbers.
8. **Terminal no-start rule.** "The last three days allow no new starts" is stated in words but not
   expressed in (II.8); a reader rebuilding the model cannot see how the horizon is closed.
9. **§III.3 lists six block counts (1, 12, 22, 45, 7, 9) in one paragraph.** A small table would
   read better.

## Visual notes

Rendered and inspected pages 1, 3–8, 13–15. Body pages 1–6 are clean: Table II.3 fits, equations
(II.1)–(II.9) are legible with correct subscripts, Table III.1's two-column layout is readable,
and no table overflows. Appendix A4's Table B.1 and A5's Table C.1 are readable although the B row
of C.1 wraps to three lines. Figure II.1 has the axis/label issue above; Figure C.1 (appendix) is
correct and readable. No clipped text found.

## Numbers that were checked (selection of the 188)

| Claim | Printed | Recomputed from |
|:--|:--|:--|
| A four-day joint sizing | 45/6, £118.90m/yr, 90.16% served | `main-schedule-summary.json` 118.898893, 90.1611 |
| A feasible vs upper | within £2,000/yr | certificate 118.898893 / 118.900891 |
| A alternative 46/6 upper | £118.890634m/yr | `A-capacity-certificate.json` |
| A zero-battery plan | 7 modules, 35.217 MW, £13.68m, 89.61% | `A-7-finance.json`, `A-electrolysis-only.json` (6/8 upper < 13.679) |
| A seven-module finance | £51.43m, 2.85 y, NPV £210.28m, £3.82/kg | 7 × £7.3475m; capital/(gross − 7 × £0.13011m) = 2.8472; 13.6792 × 15.3725 = 210.28; 7.7990 − 13.6792/3.4377 = 3.8198 |
| A diverted sales / coverage | 118 GWh/yr, 0.047 pp | 118.394, −0.04672 |
| B four-day joint sizing | 9/0, £6.07m/yr, 91.23% | 6.070258, 91.2309 |
| B annual battery cost | £42.26m | 9 × 4.695346554 = 42.2581 |
| B ninth block | +£639/yr over eight | 6.0702580 − 6.0696195 = £638.5 |
| B hydrogen ceiling | 116 days, £0.326m/module vs £0.757m | `B-hydrogen-bound.json` |
| B empty-stock certificate | 561 = 536 Xpress + 25 HiGHS, gap < £0.17 | `B-battery-certificate.json`, gap £0.1667 |
| B best alternative | £6.069620m/yr upper | certificate |
| Tier 2B B six windows | −4.20, 65.31, −3.95, −16.83, −9.45, 8.57; Σ 39.45; ex-2021/22 −25.86; 2/6 | `comparison.csv` (refit gate) |
| Tier 2B A six windows | −20.45, 41.02, 6.17, −2.78, 2.31, 2.03; Σ 28.31; ex-2021/22 −12.71 | `a-stability.csv` (Xpress) |
| Reference-year size peaks | 12 blocks £3.01m (A), 22 blocks £12.51m (B); the 22 loses £2.39m elsewhere | `a-xpress-dense.csv`, `size-sweep-folds.csv` |
| One block / 45 blocks | £0.82m / £1.27m; 45 blocks −£21.26m | same |
| Calendar-year means | ex-2022 A £65.10m, B −£8.01m; B negative in 4 years | `main-schedule-summary.json` |
| Surplus | 24.75% of half-hours, 5,165 / 2,276 GWh/yr | same |
| Two-hour references | 12.46/2.18, 13.42/14.47, 3.78/2.46; ±1.05/−1.32 | `fixed_pair.csv`, `reference_day_*.json` |
| Brief-equivalent block | £51.247m = £256,235/MWh × 200 MWh | `reference_day_A_integer.json` |
| Break-even quotes | £213/kWh (A), £130/kWh (B) | 212.736 / 130.466 |
| Table B.1 rows | 14.10/5.48, 13.18/−8.14, 13.16/−8.32, 13.16/−8.32, 13.46/0, 13.68/0 | Julian `operating_rules.csv`, `main_table.csv`, `A-7-finance.json` |
| Julian 20% reserve | 10 modules, 50.31 MW, £8.11m, 61 GWh, −0.0242 pp | Julian `main_table.csv` |
| Solver evidence | 13,155 cols / 24,113 rows, 0.5 s; 551 blocks, 4.3 s, gap £5.1; 16.8 s, gap £0.17 | `reference_day_*.json`, `site_A_xpress.json`, `B_n9_h10.json` |
| Appendix B.4 | £256,235/MWh; 0.635, 0.6225; £78.13/MWh; £635 fill; £4.6946m block | arithmetic; `reference_day_A_integer.json` |
| Lazard per-kWh | £96.72 / £173.25 / £249.77 | 62.15/111.32/160.49 $m at 0.6225235 |
| Contract table | 12 rows incl. £9.50 stress and two-rate 11 modules £6.06m | `contract_sizing.csv` |
| Two-rate average receipt | £6.58/kg | 77.0% physical surplus × £7.80 + 23.0% × £2.50 |
| NPV 8% / +20% capex | £144m / £42m; £3.91 / £5.30; B 41.6% | `electrolyser_finance.csv` |

## Author-reported, not independently re-run

- The optimisation itself: I read the saved schedules, certificates and ledgers; I did not re-solve
  the MIPs or re-run `certify_a.py` / `certify_b.py`.
- The completeness of A's count screen over the full (blocks, modules) grid. The 17 retained
  relaxations are archived and each bound is below the winner; counts sampled from the flexible
  sweep (40/8, 41/4, 54/7, 90/8, 160/8) sit at or below £117.6m, consistent with the screen. The
  screen's own enumeration is not in the archive.
- The broad-market (1,559 t/day) rows; the EHO consumption totals are cited, not re-fetched.
- Tier 2B forecast training and the classifier refits.

## Score

Scored on the same descriptor convention I used for v6.1 (weights: presentation ×2).

| Descriptor (weight) | Anchor | Fraction | Basis |
|:--|:--|--:|:--|
| Understanding & Depth (1) | A3+ | 0.79 | Rule and limits now drive the decision; base load floor departs from the brief |
| Originality (1) | A3+ | 0.82 | Own capacity certificate, B exclusion bound, six-window handover |
| Amount of Work (1) | A3+/A4 | 0.86 | New certificates, schedules, per-year reconciliation, A finance, replays |
| Logic of Argument (1) | A3+ | 0.80 | Conditional recommendation chain is coherent; headline still leads with the screened, un-bought portfolio |
| Background & References (1) | A3+ | 0.82 | [9] fixed, [22]–[24] added, [25]/[26] checked (Carrión–Arroyo 2006; Sioshansi et al. 2009) |
| Validity of Results (1) | A3+/A4 | 0.84 | 188/188 reproduced; dual-solver bounds; residual terse caption |
| Presentation (2) | A3+ | 0.79 | Figure II.1 axis/annotation, "Battery .", no author names, one spare body page |

Weighted: (0.79 + 0.82 + 0.86 + 0.80 + 0.82 + 0.84 + 2 × 0.79) / 8 = **81** (v6.1: 79; range 78–84).

Comparability: my v6.1 review did not weigh P1-1 or P1-2, so v6.1's 79 is not on exactly this
basis. The content gain in v6.2 is larger than the two-point headline (closures in all four
disclosure items plus the new certificates); the two P1s cap it.

## What would change the score

- **Upward (84–85).** Put the brief-consistent 20% A plant (30.2 MW, £44.08m, 2.56 y) beside the
  12.5% seven-module case in §5.4, label the 12.5% as a supplier sensitivity, and record one
  full-licence Xpress solve for A; fix Figure II.1's axis and mean annotation; add author names.
- **Downward.** If the 20% floor is treated as binding and the 12.5% case is not argued, the A
  recommendation (not the B conclusion) would need re-sizing; that is the item a marker would
  challenge first.
- **No numeric regression:** the carried baselines (site portfolios, contract sizing, electrolyser finance,
  fixed-pair references, window sensitivities, Xpress replay) are re-asserted in the 188 checks and pass;
  the only unverified carry-overs are the author-reported items listed above.
