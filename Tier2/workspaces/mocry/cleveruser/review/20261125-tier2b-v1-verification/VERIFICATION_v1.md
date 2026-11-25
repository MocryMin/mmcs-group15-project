# Tier 2B v1 — independent re-verification (chapter score 83, band 80–87)

Reviewer: `mocry-cleveruser` (member `mocry`, human Ran Min).
Date: 2026-11-25. Repository state: local `main` = `645bd5e` (v1 published at `c5f9b68`, review requested at `645bd5e`).
Standard used: `Tier2/workspaces/mocry/cleveruser/standard/20261125-tier2b-independent-standard/`
(`STANDARD.md` + `ADDENDUM_1_OFFICIAL_RUBRIC.md` + `ADDENDUM_2_PAGE_RULE.md`), committed and pushed as `3abab26`
**before** the preview was opened. **The standard was not modified for this re-review.**

Targets (pinned, all four hashes verified against the published `SHA256SUMS.txt`):

| File | SHA-256 | Size |
|:--|:--|--:|
| `tier2b-report-v1.pdf` | `e09c3e62…dd2f4c8f` | 118,592 B |
| `project-report-with-tier2b-v1.pdf` | `c7f76f6a…9c096283b` | 289,947 B |
| `tier2b-report-v1-review.zip` | `a1b85d40…776429b9` | 503,013 B |
| `tier2b-report-v1-source-and-evidence.zip` | `d5b076fc…001c92cbe` | 63,754,398 B |

Also checked: the review zip's own `SHA256SUMS.txt` (62 entries, all present and matching), and the frozen-input
arrays inside the 64 MB archive (`frozen/inputs-2021…2026.npz`, `frozen/plant.json`).

Independence: I did not read `mocry-claude`'s `20261125-tier2b-preview` review or her v1 verdict, and I did not
take the author's request text as a source of requirements. The request named the file set; every requirement
below comes from the brief, the Q&A transcript, the rubric and the artefacts themselves.

Scope of independence: my checks **recombine the author's shipped ledgers and re-read the PDF**; they do not
re-run the replay engine (`build_evidence.py`, `audit_dispatch.py` need pandas, numba and an Xpress licence that
this environment lacks). Forecast folds, the classifier fit and the Xpress MIP bands therefore remain
author-reported — see §7.

---

## 1. What was verified, and how

`checks_tier2b_v1.py` (same directory, run instructions in its header) recomputes every printed quantity that can
be derived from the shipped CSVs, and separately verifies hash, page and package structure.
**248/248 pass** (`checks_tier2b_v1.json`). Tolerances: 0.006 £m, 0.05 GWh, 0.0005 pp, 0.5 £k / £/MWh / GWh·day.

| Group | Passed | What it covers |
|:--|--:|:--|
| integrity | 18/18 | four file hashes, the review zip's 55 internal hashes, presence of all 13 source/build files |
| structure | 8/8 | chapter = 5 file pages printed 6–10; merged = 10 body pages printed 1–10 with front matter `i`,`ii`; chapter occupies printed 6–10; **one** `Table III.1` in the merged report; Tier 1's 12.5% table relabelled `Table II.4`; appendix C.3 labels 20% and 12.5% separately |
| 2×2 information design | 16/16 | four cells (11.95 / 12.80 / 12.11 / 12.93), Shapley-style attributions 0.83 + 0.15 = 0.98, 92.4% retention, £38.47m/window market-information value, **51.40 = 12.93 + 38.47**, `oracle_gap ≤ 0.05`, 3.40 kt H₂ |
| Table III.1 | 72/72 | ten rows × gross, battery cost, net, served %, unused GWh, RE GWh, H₂ kt, each recomputed from `replays.csv` / `plant-oracle.csv` (70 cells), the oracle row, the plant-cost gap, and the column-arithmetic defect itself |
| Table III.2 | 43/43 | 6 windows × 6 columns + the six means, plus the cross-checks that Table III.1's A net = Table III.2 plant column + battery column and that B rows equal the B curve (the one-block B column is off-curve by construction and disclosed) |
| capacity selection | 9/9 | 552 rows; six-window argmax = 11 in both policies; 2025/26 argmax A 7 → £0.69m, B 22 → £12.51m; **no positive count survives without 2021/22** in either policy; recomputed vs archived ≤ 1.5e-7 |
| Table III.3 | 21/21 | four stress weeks (RE, load, price, A, B) and that each stays inside one replay window |
| Table III.4 + break-even | 15/15 | six printed break-even capitals (113/90/127/94/123/92) re-derived from gross gain with CRF(5%,15) + 2.5% upkeep + initial-stock charge; £96.7/kWh → 97; £4.28/kg = 7.80 − 11.95/3.40; the 0.21 pp claim |
| Table III.5 | 26/26 | 5 price/gen/load MAE columns, 3 sign accuracies, 8 net values, 0.20 gap, 18%/69% truth ratios, B five-window sums −0.55 / +1.86 |
| solver audit | 8/8 | 192 rows, all status 6, every DP value inside `[feasible − 0.025, feasible + gap + 0.025]`, band ≤ £2.26 (widest at 45 blocks), 87/192 proved to zero gap, 9 order differences all exact objective ties; 48 enumerations × 625 sequences agreeing to 1.3e-10 |
| text-to-ledger claims | 12/12 | the p.7 sentences that quote a number (capture 28.7/2,911, 190 GWh input, 92.4%, the calendar-vs-window attribution, terminal-stock disclosure, Unused definition) |

I also read all five printed pages end to end, rendered and visually inspected all five, zoomed Figure III.2, and
read `tier2.tex`, `build_evidence.py`, `audit_dispatch.py`, `solver_adapter.py`, both READMEs and the merged
report's abstract, contents, references and appendices C–D.

## 2. Score

Rubric mapping per `ADDENDUM_1`; fractions A1 0.95, A2 0.85, A3 0.78, B 0.65, C 0.55, D 0.40.

| Dimension | Anchor | Fraction | Why (Δ vs the 79 review) |
|:--|:--|--:|:--|
| D1 Understanding and depth | A2 | 0.86 | The information set is now the organising idea: commitment vs dispatch, four cells, truth diagnostics for both policies, and the oracle reconciled with Tier 1 (P0 closed). Was 0.78 |
| D2 Originality | A2 | 0.86 | The commitment/dispatch 2×2 with information-matched comparators, plus capacity selection separated from replay, is a stronger construction than the preview's single oracle row. Was 0.85 |
| D3 Amount of work | A2 | 0.86 | 552 capacity replays, 192 solver audits, 48 enumerations, four stress weeks, five forecast variants, seasonality, six break-evens. Was 0.82 |
| D4 Logic of argument | A2 | 0.85 | Chain now closes: Tier 1 portfolio → four-day plant → information value → battery scale → thresholds → recommendation, and the numbers agree across chapters. Was 0.80 |
| D5 Background and references | B | 0.65 | Four `\tierref`/`\cite` sites now resolve to `[1,12,9]`, `[12,13]`, `[26]`, `[29/30]` — every input has a source. Still no engagement with the storage-value or hydrogen-market literature that Tier 1's own reference list contains. Was 0.55 |
| D6 Validity of results | A2+ | 0.88 | Solver-certified oracle with a stated acceptance band, honest B negative (simple rule beats the classifier in 6/6 windows), shock-year dependence quantified, causal-window holdout named. Was 0.82 |
| D7 Presentation (×2) | A2 | 0.84 | Tables legible, printed pages match their intended positions, the preview's blank third-of-a-page is gone. Held back by Table III.1's column arithmetic (P1-1) and unlabelled right-hand axes (P3-1). Was 0.85 |

Score = 100 × (0.86 + 0.86 + 0.86 + 0.85 + 0.65 + 0.88 + 2×0.84) / 8 = **83** (band 80–87).

Diagnostic criteria (same weights as the 79 review): C1 9/10 (was 8), C2 16/18 (14), C3 16/18 (16),
C4 15/16 (13), C5 13/14 (12), C6 13/14 (13), C7 9/10 (7) — raw 91/100, was 83/100.

Note on my own earlier prediction: the 79 review said the fixed version "would sit at 84–86". v1 does deliver
the repairs I enumerated; it lands at 83 because I found two defects then that I had not seen (P1-1, P2-2) and
because D5 remains at the B anchor. Both defects are one-line fixes, and both sit inside the stated band.

## 3. The previous P0 is closed, and I can show the arithmetic

`plant-oracle.csv` in the preview had mean net £51.40m/window against a direct-sales comparator built from the
**forecast** sale signal while the plant itself dispatched on **realised** prices. The v1 ledger adds
`direct_sale_value_of_information_GBP`, and `build_evidence.py` now selects a comparator per dispatch type
(`actual_baseline` for oracle allocation, `forecast_baseline` for forecast allocation).

    mean market-information value   £38.47m per window   (appendix D.1, printed p. A8)
    preview oracle                  51.40
    v1 oracle                       12.93
    51.40 − 12.93 = 38.47            exact

So the old 51.40 was not a broken model: it was a **mismatched comparator**, and the whole £38.47m was market
information attributed to electrolysis. Tier 1's £13.46m (four-day, 20%, six modules, calendar 2020–25) and the
chapter's £12.93m (same equipment and rule, September–August windows) now differ by 4% with a stated reason. The
direction is also consistent with the window construction: a September–August window contains the whole
March–August 2022 price shock (the chapter's worst plant window, £5.32m), whereas calendar years split it.
**Residual (P2-1):** the bridge is argued, not computed — no line recomputes 13.46 on the chapter's window set.

## 4. Previous findings, item by item

| Previous item | Status | Where |
|:--|:--|:--|
| P0-1 oracle 51.40 vs Tier 1's 13.46 | **closed** | 12.93 with `direct_sale_value_of_information`; identity 51.40 = 12.93 + 38.47 (§3) |
| P1-1 value lost to forecasting not decomposed | **closed** | printed p.7 §2.1: 12.80 / 12.11, £0.83m allocation + £0.15m commitment; `evidence/plant-information.csv` keeps all four cells |
| P1-2 Table III.1 compared A at 11 with B at 9 | **closed** | B rows are now 1 block (prior-slot, classifier, true sign) and 11 blocks (classifier, 6.83); caption states which rule belongs to which row |
| P1-3 five of six fits use later data, consequence unstated | **partly** | p.7 states the regime; §3 reports the 2025/26 holdout (A 15.36, +0.17, B +1.33) separately. Still no quantification of the in-sample bias in the six-window mean (P2-3) |
| P1-4 reproduction path points outside the repository | **closed** | the 64 MB archive carries `frozen/inputs-2021…2026.npz` + `plant.json` and every module `build_evidence.py` needs; `replay.py` reads `frozen/` instead of `panels.npz`. I verified the frozen arrays contain exactly the fields the code consumes (`path`, `online`, `seasonal`, `v2`, `auction`, `prev`, `price_threshold`, `b_actual/b_prior/b_score`, `renewable_share`) |
| P1-5 audit claim partly unsupported (192 samples, 2 rows `status ≠ 6`, 48 enumerations absent) | **closed** | 192 rows all `status 6`, retry branch in `audit_dispatch.py`, acceptance band asserted in code and stated in the README; 48 enumerations shipped, 625 sequences each, max deviation 1.3e-10 |
| P2 two `Table III.1`s and mixed 12.5%/20% | **closed** | Tier 1's window table is `Table II.4` ("The 12.5%, four-day capacities…"); appendix C.3 prints 20% £22.84m and 12.5% £22.99m side by side |
| P2 zero citations | **closed** | four sites, five keys, all resolving in the merged reference list |
| P2 Unused not comparable across policies | **closed** | p.7: A leaves output unsold at non-positive signals, B serves demand regardless of price |
| P2 renewable capture ~1% unexplained | **closed** | "28.7 of 2,911 GWh … (about 1.0%)", plus 190 GWh of hydrogen input and the 11-block 182/271 GWh figures |
| P2 £97/kWh unsourced | **closed** | £38.69m/400 MWh = £96.7/kWh → 97, footnoted to `[equipment costs]`; the brief's two-hour £256/kWh is printed for comparison |
| P2 Table III.5 MAE units | **closed** | headers now read `Price (£/MWh)`, `Gen. (MWh/slot)`, `Load (MWh/slot)` |
| P2 terminal stock valued at zero | **closed** | p.6: "Usable stock starts at zero … closing stock zero cash credit. This can understate value where later delivery is possible" |
| P2 blank third of p.7 / dense p.10 | **closed** | all five pages now fill their blocks; p.10 ends after §5.1 |
| P2 DP recursion not printed | **open (P3-2)** | still prose only ("a piecewise-linear dynamic programme evaluates actions over continuous `s_t`") |

## 5. New findings

### P1-1 Table III.1's columns do not add up as printed (page 7, Table III.1)

`Gross − Batt. cost = Net` holds in no A row: 16.49 − 0.00 ≠ 11.95; 21.96 − 4.70 = 17.26 ≠ 12.72;
71.96 − 51.67 = 20.29 ≠ 15.75. The missing term is the plant's annual capital equivalent, £4.54m per window
(6 × £756,537, `frozen/plant.json`), which is deducted in every A row but printed nowhere in this chapter. B rows
do add up (6.16 − 4.70 = 1.46), so the defect reads as an arithmetic error in exactly half the table.
Body text on p.7 does say "Net value deducts plant cost", but a reader cannot recover 4.54 from this chapter.
Cheap fix: add "less the £4.54m annual plant equivalent in every A row" to the caption, or a `Plant cost` column.
No printed value changes; my recomputation reproduces all 70 numeric cells.

### P2-2 "In B, delivery improves by 0.21 percentage points over direct sales" (page 7, §2.2)

0.21 pp is the eleven-block figure (91.147 − 90.934). At the recommended one block it is 0.02 pp (90.957 −
90.934), and the sentence sits in the middle of the eleven-block discussion without saying so. Either say
"with eleven blocks" or print the one-block figure.

### P2-3 The six-window mean is still an in-sample selection statistic

§3 says the six-window mean "uses the same windows to evaluate and select capacity", and p.7 names the 2025/26
causal fit. What is never stated is the consequence: the 11-block six-window optimum (3.81 in A, 6.83 in B) is
an upper bound on real-time performance, and on the only causal window both policies prefer a different count
(A 7, B 22). One sentence would close it; the recommendation already survives without it.

### P2-4 The 552-row "recomputed vs archived" agreement is a ledger check, not an independent replay

The two columns agree to 1.5e-7 over 552 rows, which is what a re-emission of the same run looks like. It shows
the shipped ledger is self-consistent; it does not show a second implementation agrees. Fine as stated
("recomputes the archived net gain … to £0.01"); worth not overselling.

### P3-1 Figures III.2 and III.3 have no y-axis labels on the Policy B panel

Both panels share one scale, but nothing says so. Either add the tick labels to the right panel or write
"shared scale" in the caption. Figure III.2 is otherwise legible at print size: dots mark the reference and
six-window peaks, the Tier 1 verticals at 45 and 9 are labelled.

### P3-2 Minor, previously open: the DP recursion is described but not displayed; `oracle_gap` is stored as `max(0, gap)`, which is structurally zero whenever the solver proves optimality (87/192 audit rows are exactly zero), so the column cannot show slack.

## 6. What would change the score

- Fixing P1-1 and P2-2 (two lines) → 84–85, because D7 and D4 recover.
- Adding the 13.46 ↔ 12.93 bridge computed on the chapter's own windows (one extra replay, or one line of
  arithmetic if the plant is linear in prices) → 85.
- Citing two or three external sources on storage value / hydrogen offtake, even in one sentence → D5 0.65 → 0.75,
  which is worth ~1.9 points on its own and is the cheapest remaining quality gain.
- If the six-window selection were replaced by a rolling-origin or leave-one-window-out selection, D6 would move
  towards A1, but that is a redesign, not a repair.

## 7. Author-reported, not independently verified

- Training of the Tier 2B price/generation/demand models (Ridge + Transformer, per-fold checkpoint selection) and
  the weighted logistic classifier. The package ships frozen forecasts and scores, not the fitting runs.
- The Xpress MIP bands in `xpress-dispatch-audit.csv` (2.25 at 45 blocks, 87/192 zero) — I checked the acceptance
  logic and that DP values lie inside the band, not the solver runs.
- `build_evidence.py`, `audit_dispatch.py`, `make_exhibits.py` were not executed here (no pandas, numba or Xpress
  licence); I verified their inputs exist, their assertions match the ledgers, and that the printed tables equal
  the ledger values they emit.
- The merged report's Tier 1 half (pages 1–5) was read only where it must agree with this chapter (abstract,
  §5.4 recommendation, Tables II.3/II.4/II.6/II.7, appendix C.3, appendix D.1). I did not re-review it.

## 8. Page and deliverable status

- Chapter: 5 pages, printed 6–10 — within the brief's five pages for Tier 2B. ✅
- Merged report: front matter `i`,`ii`; **body printed 1–10** (I 1–5, II 2–5 core, III 6–10); References `R1`;
  appendices `A1–A8`. Body page count = 10, so the page limit is met with the chapter replacing the Tier 1 stub,
  not appended to it. ✅
- One table numbering sequence per chapter (`Table II.1…II.7`, `Table III.1…III.5`, `Table C.1…C.4`); equation
  `(III.1)`/`(III.2)` share the numeral with tables III.1/III.2 but are a separate counter — acceptable, worth
  knowing.
- Contents page lists Chapter III at printed page 6 and its five sections through page 10. ✅
