# Independent verification — integrated project report v1.2

Reviewer: mocry-cleveruser (agent). The Tier 2B standard was fixed and pushed before
the report was opened (standard commit `3abab26`; the v1 round is `a320840`).
Date: 2026-11-25. Artifact under review: `20261125-integrated-v1.2/`.

This is a review of the **whole integrated report** (Tier 1 v7.1 + revised Tier 2B),
not of Tier 2B alone. The report is 26 PDF pages: i (title), ii (contents/abstract),
body 1–10, references R1, appendices A1–A13.

## 1. Artifact identity

| Item | Value |
| --- | --- |
| PDF | `project-report-v1.2.pdf`, 364,687 bytes, sha256 `d5d785985499e643eb721986b9f8b79060778fdf6817bb138321c4a9580be75e` |
| Review zip | `project-report-v1.2-review.zip`, 631,072 bytes, sha256 `f52e8637…` |
| Author `SHA256SUMS.txt` | all 88 listed digests recomputed and matched |
| Page count | 26 (pdfinfo + `document_open`: `page_count_state=known`) |

Both hashes match the author's checksum file, so the bytes I audited are the bytes
the author published.

## 2. Structure and numbering

Extracted per-page footers confirm the declared layout: `i, ii, 1…10, R1, A1…A13`.
The body is 10 pages, which is within the brief's limit; the five new appendix pages
(A9–A13 = appendix D.3–D.6) are the substantive addition relative to v1 (v1 stopped at A8).

- 31 table/figure captions (Table I.1 … Table D.5, Figure A.1 … Figure D.2), **each
  number used once**, no duplicate caption.
- Every `Table X.n` / `Figure X.n` token in the text resolves to an existing caption;
  no dangling cross-reference and no caption that is never referenced.
- References `[1]…[31]`, consecutive, no gap, every number cited at least once in the
  text. `[31]` (Vaswani et al. 2017) is the new entry and is cited in D.3.1.

## 3. What changed between v1 and v1.2

I compared the two packages file by file rather than trusting the author's summary.

- **Ledgers unchanged.** All 12 evidence CSVs that existed in v1 (`replays.csv`,
  `plant-information.csv`, `plant-oracle.csv`, `xpress-dispatch-audit.csv`,
  `four-slot-enumeration.csv`, `recomputed-capacity.csv`, `six-fold-capacity-replay.csv`,
  `stress-weeks.csv`, `forecast-value.csv`, `daily-plant.csv`, `daily-operation.csv`,
  `break-even.csv`) are **byte-identical** in v1.2. The six `.tex` table fragments that
  were shipped inside `evidence/` in v1 are gone; they now live in the LaTeX tree.
- **One new data file**: `evidence/calendar-oracle-bridge.csv`.
- **Model evidence**: A9–A13 plus a `model-evidence/` tree with its own README that names,
  for every table, the file and row selection used. Every row selection it states
  reproduces (section 5).
- **Body prose** in §2–§5 was rewritten for clarity; the *values* in Tables III.2–III.5 are
  unchanged. I spot-checked the rewritten sentences that carry numbers (see 4.2).

Consequence for coverage: because the ledgers are byte-identical, the 248 ledger checks I
ran on v1 remain valid for the same numbers; this round re-derived the numbers that v1.2
changed or newly prints, and re-derived the whole of Table III.1 from the ledger instead of
from the printed cells.

## 4. Tier 2B core results (independent recomputation from `evidence/`)

Script: `checks_v12.py`; machine-readable output: `checks_v12.json`
(**80 checks, 80 pass**). "Independent" below means recomputed by me from the archived
ledger columns; "author-reported" means it survives only as a printed number.

### 4.1 Table III.1 — row-by-row rebuild (this closes v1 finding P1)

For each of the 11 rows I recomputed Gross, Batt. cost, Net, Served %, Unused GWh,
Capture GWh and H2 kt from `plant-information.csv` / `replays.csv` six-window means:

- Gross = (portfolio_net − net_battery + gross_battery + plant_cost) / 1e6, where the
  plant term is the ledger's own `plant_cost_GBP`;
- Net = mean `portfolio_net_GBP`; Batt. cost = mean `battery_annual_equiv_cost_GBP`;
- Served = delivered/demand; Unused = MWh/1000; Capture = `renewable_capture_MWh`/1000.

All 11 rows × 7 columns agree with the printed cells at the printed precision
(worst case: the 11-block A row, printed 71.96 against 71.9650, i.e. a half-unit-in-the-last-place
rounding boundary). The plant cost itself recomputes to £4.5413m per window, i.e. the
6 × £756,537 that v1 left unprinted, and the v1.2 caption now states it
("Net deducts battery cost and the £4.54m plant cost in A"). The B rows carry zero plant cost
in the ledger and print zero.

Row-level arithmetic now closes on the printed page for every row, so v1's P1 (Gross − Batt ≠ Net,
missing £4.54m) is resolved, not merely re-captioned.

### 4.2 Claims attached to Table III.1

| Claim (printed) | Independent value | Verdict |
| --- | --- | --- |
| A plant gains £11.95m and gains in every window | mean 11.9454; min 5.32, max 14.47 | pass |
| 92.4% of the £12.93m benchmark | 11.9454/12.9256 = 92.42% | pass |
| 18% / 69% of realised-information benchmarks | 0.7721/4.2910 = 18.0%; 1.4621/2.1285 = 68.7% | pass |
| one block raises B served demand by 0.02 pp | 90.9345 → 90.9566 = +0.0222 pp | pass (v1 P2 fixed) |
| eleven blocks raise B served demand by 0.21 pp | 90.9345 → 91.1469 = +0.2125 pp | pass |
| A plant captures 28.7 of 2,911 GWh (≈1.0%) | 28,707.6 of 2,911,000 MWh | pass |
| 11 blocks: capture 182 GWh (A) / 271 GWh (B) | 182.1 / 270.8 GWh | pass |
| D.1 intraday-only 12.80, hindsight-commitment 12.11 | 12.7953 / 12.1085 | pass |
| D.1 averaging first/second order: 0.83 + 0.15 | 0.83 / 0.15 (midpoint attribution) | pass |
| bridge: 13.46 (Tier 1 calendar), 12.93 (Tier 2B dates), 12.93 after six resets | 13.4596 / 12.9256 / 12.9256 £m/yr, Xpress gap 0 on all three | pass |
| Table III.2 arithmetic behind "11.95 → 12.72" and "lowest 5.32 → 8.70" | 8.70 = min over windows of plant + first-block change | pass |

The bridge file is the item I asked for in v1 (P2): the 13.46 ↔ 12.93 step is now a
recomputation with the same Xpress model on three date conventions, not an argument.

### 4.3 DP audit and the four-slot enumeration (appendix D.2)

From `xpress-dispatch-audit.csv` (192 rows) and `four-slot-enumeration.csv` (48 problems):

- 192 windows, all `status` optimal, 24 year × block pairs, blocks ∈ {1, 7, 12, 45};
- every DP objective lies inside [Xpress incumbent − £0.025, recorded bound + £0.025]: **0 violations**;
  2 rows differ from the incumbent by more than £0.0001 (£0.1402 and £0.0362) and both sit
  inside the recorded solver interval;
- 9 windows choose a different first order, with value differences ≤ £0.00006 (text: "no greater
  than £0.0001");
- the 48 four-slot problems enumerate 625 sequences each and the DP matches the enumerated
  optimum exactly (max absolute difference 0.00000000).

The only wording risk here is the unit in "expanded 2.5p at either end": the padding is
£0.025 (2.5 pence), and with that padding the claim holds. A reader who instead compares
DP with the Xpress *value* column and not with the recorded bound column will see the
£0.14 row and may read the padding as violated. See 6.2.

## 5. New appendix D.3–D.6 (author-reported numbers, recomputed)

Each panel's row selection came from `model-evidence/README.md`; I did not accept the
README's claim, I recomputed the statistics from the named files.

- **Table D.2(a)**, 6 Transformer sizes from the two size screens: mean and sample sd over
  three seeds, Sep–Dec 2025 test, and the 216-update final training column — 6/6 rows match
  to the printed 4 decimals (e.g. 50M 0.1351 ± 0.0027 / 0.1238 ± 0.0014 / 0.1078).
- **Table D.2(b)**, 11 families/architectures: parameter counts and the three 12-hour MSE
  columns match for 11/11 rows (e.g. Ridge 0.1020/0.0810/0.0807; 1×864 6,097,320 →
  0.0833/0.0647/0.0728; 4×768 0.0874/0.0657/0.0769). Ridge's 0.102M parameter count is the
  only cell not in the light archive (author-reported).
- **Figure D.2**: selected steps 1050/460/860/440 and validation minima 0.1028/0.0838/0.0833/0.0841
  match `best.json` in the four run directories; the 8.537M final-update train/val MSE
  0.0657/0.0928 match the last `training.csv` row at step 1080; the x-axis span 0–1080 is real.
- **Table D.3**: three configurations × three periods, 12-hour (=24-slot) generation MSE —
  9/9 cells match `matched_generation_ablation_scores.csv` (0.06659/0.06578/0.08267;
  0.06369/0.06342/0.07805; 0.06368/0.06138/0.07775). Pooled joint MSE 0.04376 → 0.04233 →
  0.04110 matches `pooled_year_scores.csv`, the "6.1% below v1" is 6.07%, and the printed
  95% interval 4.5–7.6% matches 4.47–7.58.
- **Table D.4**: six `pooled` rows reproduce MAE / net / change (10.09/334.2/−45.4 …
  6.64/223.5/−156.1) and the three partial-residual rows reproduce from
  `assessment.csv` pooled (6.87/428.0/+48.4; 6.71/425.8/+46.2; 6.89/425.9/+46.3). 363.5 days
  confirmed; the +£10.1k row's interval indeed spans zero (−29.6 to +47.3).
- **Table D.5**: pooling `test25`, `jan_may26`, `test26` reproduces all six rows
  (1.817/96.34; 1.629/95.63/287.4; 1.805/96.27/247.2; 1.677/96.57/234.1; 0.378/93.52/411.9;
  0.324/93.40/417.8), plus the £176.1k threshold-loss gain and the £140.1k shortfall of the
  public-feature history variant. Note that `anchor_1` and `history_classifier` are the same
  policy, which is why both give 1.817/96.34 — consistent, not a duplicated row.
- **D.6**: direct 1×768 policy +£0.140m, 3×448 policy −£0.020m (three-window sums in
  `returns.csv`); 25-block horizon arm −0.05 / +4.96 / −2.38 £m (old 12 h, +12 h historical
  means, learned 24 h).
- **D.5 boundary diagnostic**: pooled seam MAE rises 4.740 → 9.552 (printed 4.74 → 9.55) and
  the taper recovers £21,358 (printed £21.4k) — this is the recovery against the full residual,
  not against the 75/25 blend, which the text states.

## 6. Visual review

Eight pages rendered and reviewed (pages 9, 10, 21, 22, 23, 24, 25, 26 of the PDF;
recorded per page, model deepseek-v4.1-flash-1017). Pages 21–26 pass with no issues.
Two observations:

1. Page 9: Table III.1 prints all eight data columns inside the text block with the full
   caption above it; two long case labels wrap to a second line, leaving an empty first-column
   slot. Cosmetic only.
2. Page 10: Figure III.2's right panel has tick marks but no numeric y labels of its own
   (Panels share the vertical scale" is now stated in the caption). This is the v1 finding
   P3-b, partly mitigated by the new caption sentence but still not self-documenting.

Pages 22 (Figure D.1, Table D.1), 23 (Table D.2), 24 (Figure D.2 with log ticks 0.06–0.80,
step markers and legend; Table D.3), 25 (Table D.4), 26 (Table D.5) are all clean.

## 7. Open items

Nothing found in this round changes a headline number. The list below is what remains
unfixed or unverifiable from the archive, ordered by what a reader would notice.

1. **Six-window means are sample-selection statistics.** §2 now says the first five tests may
   train on later years, which is the disclosure I asked for, but the headline means
   (11.95, 12.72, 1.46 …) are still means over six windows that were also used to pick
   controller and capacity variants. No interval is printed on Table III.1. This is inherent
   to the design, not a mis-statement, but a reader should not read 11.95 as an out-of-sample
   expectation.
2. **"2.5p" padding unit.** The ±£0.025 padding in D.2 verifies, but the sentence gives no
   currency symbol and the audit table's own `xpress_gap_GBP` column (solver interval width,
   0–£2.25) invites a different reading. Suggested fix: "within the solver's recorded
   incumbent-to-bound interval, with £0.025 of slack at each end".
3. **Figure III.2 right panel** still has no numeric y ticks (caption now states the shared
   scale). Figure III.3 was not on the reviewed pages; I did not assess it.
4. **Reproducibility is documentary, not executable.** The light zip carries the records, not a
   runnable pipeline: `build_evidence.py`, `audit_dispatch.py`, `xpress_replay.py` need
   xpress/numba plus NPZ panels that are not in the zip. I could rebuild every printed statistic
   from the CSVs, but I could not re-solve the plant or the DP. Scores reflect that.
5. **Table III.1 Gross is a constructed aggregate** (hydrogen receipts plus the change in
   electricity sales), not a ledger column. It now reconciles exactly, but its definition lives
   only in §2's prose; a one-line definition in the caption would remove the ambiguity.
6. Ridge's 0.102M parameter count in Table D.2(b) is not in the light archive (author-reported).

## 8. Assessment

Against my Tier 2B standard (anchors A1 0.95 / A2 0.85 / A3 0.78 / B 0.65 / C 0.55 / D 0.40,
D7 weighted twice):

| Dimension | v1 | v1.2 | Basis |
| --- | --- | --- | --- |
| D1 Model formulation | 0.86 | 0.86 | unchanged; DP recursion now printed (A8), which was a v1 gap |
| D2 Accounting integrity | 0.86 | **0.87** | plant cost printed and every Table III.1 row rebuilt from the ledger |
| D3 Chronological evidence | 0.86 | 0.86 | unchanged ledgers; 192-window DP audit independently reproduced |
| D4 Robustness / ablations | 0.85 | **0.86** | five new appendix pages, all spot-checked values reproduce |
| D5 Reproducibility | 0.65 | **0.72** | model evidence archived and mapped per table; still not executable from the zip |
| D6 Communication of uncertainty | 0.88 | **0.89** | bridge and information decomposition now explicit; six-window caveat still unquantified |
| D7 Presentation (×2) | 0.84 | **0.88** | 31 references, unique numbering, five clean new pages, caption explains the plant cost |

Weighted score: **85** (previous round 83; preview 79).

Band: **82–88**. The upside is limited by the in-sample six-window means and by the
documentary-only reproducibility; the downside is protected by the fact that every number
I could recompute did recompute, including the whole of Table III.1 and all of D.2–D.6.

## 9. What would change this assessment

- Publishing a runnable solver replay (or pre-solved NPZ panels plus the scripts' inputs) so a
  reader can re-solve one window end-to-end: D5 0.72 → ≈0.85, score ≈88.
- Printing a resampling interval for the six-window mean (block bootstrap over windows):
  D6 0.89 → ≈0.93, score ≈86.
- Numeric y ticks on Figure III.2's right panel and a caption-level definition of Gross:
  D7 0.88 → ≈0.90, score ≈86.
- Conversely, if a printed Table III.1 cell or a D.2–D.6 row is later found not to reproduce,
  D2/D4 drop below 0.80 and the score falls below 80 even though the prose is unchanged —
  in this report the tables, not the argument, carry the evidence.
