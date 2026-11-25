# Independent verification — integrated project report v1.3

Reviewer: mocry-cleveruser (agent). The Tier 2B standard was fixed and pushed before the
report was opened (standard commit `3abab26`) and is unchanged this round; I did not retune
anchors or weights after reading v1.3. Date: 2026-11-25.
Artifact under review: `Tier2/workspaces/mocry/codex/technical-report/20261125-integrated-v1.3/`.

Scope: the **whole integrated report** (Tier 1 v7.1 + Tier 2B), 27 PDF pages: i, ii, body
1–10, references R1, appendices A1–A14. Tier 1 v7.1 itself is closed upstream and I was
asked not to re-review it; Tier 1 pages are unchanged apart from the cross-reference on p.3
(§3 below), and this round concentrates on what v1.3 changed.

## 1. Artifact identity

| Item | Value |
| --- | --- |
| PDF | `project-report-v1.3.pdf`, 430,567 bytes, sha256 `13823ac9b7c85dee3e0e112f3586491d6478c39d1efe300f6f023900cdd414b0` |
| Review zip | `project-report-v1.3-review.zip`, 685,344 bytes, sha256 `bb1d39c28f051f35788041cbb47baf8f8eb202267906827791532c69b1f16bdb` |
| Replay zip | `project-report-v1.3-replay-2025-26.zip`, 10,580,255 bytes, sha256 `52972a8301bc588c90d4685f28f840dd410a3d825ac67dbb477800cd7eeebe3a` |
| `README.md` | sha256 `aa6d5c5d9c4f1edb3eb9c44a7ec3693fd45979cb24b57dd21071c2f434905a00` |
| Author `SHA256SUMS.txt` | all 4 listed digests recomputed and matched |
| Internal manifests | review zip: 95 entries, 94 listed digests all match; replay zip: 17 entries, 16 listed digests all match |
| Page count | 27 (`pypdf` + `document_open` both report 27) |

Because the author's own checksum file and both zips' internal manifests agree with the bytes
I hashed, the package I audited is the package that was published.

## 2. Structure and numbering

Footers extracted page by page give exactly `i, ii, 1…10, R1, A1…A14`. The body is still 10
printed pages, inside the brief's limit; the growth relative to v1.2 (26 pages, A1–A13) is
one new appendix page, **A14 = appendix D.7**.

- 33 distinct `Table`/`Figure` numbers (v1.2: 31). The two new ones are **Table D.6** and
  **Table D.7**, both on A14. Nothing was renumbered or dropped: Tables I.1, II.1–II.7,
  III.1–III.5, A.1, B.1, C.1–C.4, D.1–D.7 and Figures II.1, III.1–III.3, A.1, D.1, D.2 all
  resolve to a caption, and no number carries two captions.
- References `[1]…[31]`, consecutive, no gap, every entry cited at least once (checks 78–80).
- The reference note on R1 was updated to name the v1.3 archive
  (`tier2b-report-v1.3-source-and-evidence.zip`), so the report does not point a reader at
  the previous round's package.

## 3. What changed between v1.2 and v1.3

I diffed the two packages file by file and the two PDFs page by page, normalised for
extraction reflow; the list below is what actually differs.

**Evidence tree.** `evidence/` went from 13 to 17 CSVs: **12 are byte-identical** to v1.2,
`stress-weeks.csv` differs in 4 numeric cells by at most 5.7e-14 (float last-digit noise; the
printed Table III.3 values 104 / 766 / 80 / −28 / −90 are unchanged), and four files are new —
`capital-budget.csv`, `horizon-sensitivity.csv`, `horizon-xpress-audit.csv`,
`window-uncertainty.csv`. `model-evidence/` is **byte-identical**: 52 files, 0 changed,
0 added, 0 removed.

**Prose and pages** (PDF page numbers):

- **p.1 (abstract)** — adds the operating counterpart to the Tier 1 sizing result: "In A, the
  six-module plant without batteries earns a mean net gain of £11.95m per window … A's 45
  blocks lose £22.24m per window on average with 12-hour planning and £14.10m with a 24-hour
  extension. B's nine gain £6.57m."
- **p.3 (§1)** — new cross-reference sentence: "Against zero batteries, the Tier 1 battery
  counts give mean net changes of −£22.24m in A (12-hour planning) and +£6.57m in B per
  window." The sentence that used to follow ("Scenario and stress tests show when these
  portfolios cover their costs …") is gone.
- **p.7** — "Across six replay windows, one block gains £4.63m in A and £8.77m in B with the
  previous-slot rule."
- **p.8 (§1)** — the portfolio description is reworded to AE-operator language ("A represents
  a merchant operator free to maximise operating receipts, with hydrogen at £7.80/kg …"),
  and the planning programme (III.2) is now printed instead of only described.
- **p.9 (Table III.1)** — the caption now carries the definitions: "Gross is hydrogen receipts
  plus the change in electricity receipts from direct sales under the same policy and sale
  signal … Net deducts battery cost and A's £4.54m plant cost." This closes my v1.2 item 5.
- **p.10 (Figure III.2, §3)** — caption adds "Dots mark the peaks of the 2025/26 and
  six-window mean curves. Vertical lines mark Tier 1 counts. Panels share the vertical
  scale."; §3 prose adds the −£22.24m / +£6.57m forecast-operation result.
- **p.11 (Figure III.3, Table III.4)** — the bar panels now print y tick labels; Table III.4
  swaps its "Demand and supply" row for a "Capital budget" row (£30m → four modules,
  £37m → five, neither fits one four-hour block).
- **p.12 (Table III.5, §5)** — header "Input to controller" → "Controller"; row labels
  "A: realised 12 h paths" → "A: 12 h truth", "B: true surplus sign" → "B: true gap sign";
  the "Basis of the recommendation" paragraph is reworded and now says the previous-slot rule
  beats the classifier "at one block in every window".
- **p.21 (A8)** — the "expanded 2.5p at either end" phrasing that I flagged in v1.2 is
  rewritten: "lies between the Xpress feasible value and recorded bound, allowing £0.025 at
  each end". The unit ambiguity is gone.
- **p.23 (A10)** — one claim is removed: "while Ridge gives lower first-slot error than the
  4 × 768 and 8 × 768 models in both periods". What remains ("The Transformer gives lower path
  error in both test periods") is what the tables support.
- **p.26 (A13)** — the 25-block pilot is described as "An earlier 2025/26 pilot with a 12.5%
  minimum load, half-hour starts and stops, and 25 battery blocks", and the section now points
  forward: "The experiment in Section D.7 repeats the historical extension at the main
  report's 20% load floor and four-day run requirement."
- **p.27 (A14, new)** — appendix D.7 with Tables D.6 and D.7, the horizon extension and the
  window-resampling interval.

## 4. Independent recomputation (112 checks, 112 pass)

Script `check_v13.py`, machine-readable output `checks_v13.json`
(`{'total': 112, 'passed': 112, 'failed': 0}`), derived from `checks_v12.py` with the 29
v1.2 checks re-pointed at the v1.3 package and 32 new checks (80 → 112). "Independent" means recomputed
by me from archived ledger columns; "author-reported" means it survives only as a printed
number.

Coverage in this round: 11 Table III.1 row rebuilds (checks 1–11), 6 Table III.2 rows
(81–87), the four Table D.6 block counts × 6 columns (88–91), the six Table D.7 rows ×
3 columns (92–97) plus its interval construction (98) and the first-block totals (99–101),
the D.7 capital budget (102–104), the eight-plan Xpress horizon audit (105), the new abstract
and §3 claims (106–108), and the executed replay (110–112). Everything from v1.2 that the
change list touches was re-run, not assumed.

### 4.1 Table III.1 (unchanged values, new caption)

All 11 rows × 7 columns still recompute from `plant-information.csv` / `replays.csv`
six-window means; the plant cost is still £4.5413m = 6 × £756,537 and is now stated in the
caption rather than only in §2 (checks 12–14). Row arithmetic closes on the page: e.g. A plant
forecast 16.49 − 4.54 = 11.95, A rolling forecast 1 block 21.96 − 4.54 − 4.70 = 12.72.

### 4.2 Table III.2 — all six rows from the ledger

This round I rebuilt the full 6 × 6 grid (v1.2 checked the arithmetic behind individual
sentences). Worst deviation is at the printed precision; the 2025/26 row is 15.36 / 16.35 /
0.17 / 0.39 / 1.33 / 9.68 and the Mean row 11.95 / 12.93 / 0.77 / 3.81 / 1.46 / 6.83.
Note for a reader: the B column at one block is the previous-slot rule, at eleven blocks the
classifier, as the caption says — mixing that up changes the B sum, not the arithmetic.

### 4.3 New: Table D.6 (planning-horizon extension)

Rebuilt from `horizon-sensitivity.csv` for blocks 1 / 11 / 25 / 45, both 12 h and 24 h, all
six columns (mean, 2025/26, five-window) — 24 of 24 cells match.

Two conventions matter and the caption states both: the **last two columns are sums, not
means** ("The last two columns sum five windows after omitting 2021/22"), and "five windows"
means **omitting the 2021/22 window**, which is `test_end_year == 2022` for a window that ends
in year *Y* covering *Y−1/Y*. My first pass excluded 2020/21 and produced −1.55 → +7.62-style
disagreements; that was my error, not the author's. With the caption's reading every cell
matches, e.g. 45 blocks: mean −22.24 → −14.10, 2025/26 −23.96 → −9.83, five-window sum
−278.78 → −246.28.

### 4.4 New: Table D.7 (window resampling)

The printed interval is exactly reproducible, and the way it is reproducible is worth stating
plainly: it is the 2.5th / 97.5th percentile of the mean over **all 6⁶ = 46,656 ordered draws
with replacement** from the six window values (14.4674, 5.3243, 7.7416, 14.8062, 13.9716,
15.3611 £m for the A plant). Exhaustive enumeration gives **8.6923 / 14.7857**, printed
8.69 / 14.79.

Two consequences:

- It is an enumeration, not a Monte Carlo draw, so there is no seed and no sampling error —
  the only judgement is the percentile index rule.
- The word "ordered" is load-bearing. Taking the 462 **distinct multisets** instead, with the
  same index rule, gives 7.31 / 14.97. A reader who resamples "six windows" without the
  order distinction lands 0.4–0.6 £m wider at the bottom. The caption does say "ordered
  samples … drawn with replacement", so I record this as a reading trap, not an error.

The means in D.7 also reproduce (11.95, 0.77, −22.24, −14.10, 1.46, 6.57), and the first-block
six-window total is £4.63m = 6 × 0.7721, which is the sentence on p.7.

### 4.5 Capital budget and the horizon audit

- `capital-budget.csv`: four modules £29.39m capital / £11.11m per year, five £36.74m /
  £13.13m, six £44.08m / £13.46m — all four cells per row match the printed text, and the
  £38.69m four-hour first block is correctly outside both tested ceilings.
- `horizon-xpress-audit.csv`: 8 rows, all `optimal`, and every DP objective lies inside the
  recorded solver interval with |DP − Xpress| ≤ £0.025 — which is what p.27 claims ("Eight
  sampled 48-slot plans agreed with the Xpress feasible values to within £0.025").

### 4.6 Abstract and §3 battery claims

−22.24 (12 h) / −14.10 (24 h) for 45 blocks in A and +6.57 for nine blocks in B match D.6/D.7,
and the accompanying sentences verify: one block covers costs over six windows in **both**
policies (£4.63m in A, £8.77m in B) but its five-window total is negative in both (−1.55m in A;
8.77 − 9.32 = −0.55m in B, which is also the number §5 prints). £4.63m and £8.77m are the
six-window sums, not means; as means they would be 0.77 and 1.46.

## 5. Executed replay (new in v1.3, and the reason D5 moves)

v1.2's open item 4 was that reproducibility was documentary. v1.3 ships a runnable package, so
I ran it rather than describe it.

- **Environment**: a fresh virtual environment on this machine's Python 3.14 (cp314 wheels
  available) with numpy 2.5.5, pandas 3.1.1, scipy 1.18.1, numba 0.68.1. No FICO Xpress and no
  licence.
- **Import obstacle**: `continuous.py` imports `xpress_replay`, which imports `xpress` at
  module level, so the archive cannot even load without a solver. I added a review-only
  `.deps/xpress.py` whose module-level `__getattr__` returns a callable that raises on any
  call. Nothing could have returned a number from it.
- **Commands** (from the unpacked archive):
  `python report_sensitivity.py horizon --years 2026 --sizes 1 11 25 45 --output check-a.csv`
  and `python report_sensitivity.py check-b --years 2026 --output check-b.csv`. Both finished
  in seconds. The shim was never reached, which is direct evidence for the README's claim that
  the continuous-DP path needs no licence.
- **Results**: `check-a.csv` reproduces `evidence/expected-a-2025-26.csv` (four block counts ×
  12 h/24 h) and the 2026 rows of `horizon-sensitivity.csv` exactly; `check-b.csv` reproduces
  the B 2025/26 rows of `replays.csv` at one and nine blocks exactly. Maximum absolute
  difference **0.0** on all three comparisons (checks 110–112).

**Limits, stated as limits.** This is a one-window replay: it re-runs the 2025/26 operational
arm from `frozen/inputs-2026.npz`. It does not re-run the six historical windows, does not
re-solve the Xpress plant optimisation (the plant arm is still documentary), and does not
regenerate `model-evidence/`. So the report now has executable reproducibility for the tier
2B operational model on one window — a real step, not end-to-end reproducibility.

## 6. Visual review

Nine pages rendered and inspected as pixels (PDF pages 1, 8, 9, 10, 11, 12, 23, 26, 27), plus
a 3.9× region zoom of the D.7 caption. The remaining 18 pages were checked only as extracted
text; I make no appearance claim for them.

1. **p.27, `6⁶`**: at 3.9× zoom the second 6 is a true superior figure, and the printed
   percentiles match my enumeration to the printed precision. The PDF text extractor flattens
   it to "66", which is an extraction artefact — this is not a defect, and I record it because
   it is exactly the kind of thing that looks like one.
2. **Figure III.2 (p.10)**: both panels now carry numeric y labels (−100, 0, 100) and x ticks
   (0, 10, 20, 30, 40, 45); the caption states the shared scale and marks the Tier 1 counts.
   My v1.2 finding 3 is closed.
3. **Figure III.3 (p.11)**: both panels labelled 0 / 20 / 40; previously unreviewed by me.
4. **Table III.1 caption (p.9)**: now defines Gross and Net and prints the £4.54m plant cost.
   One wording nit remains: the units sentence reads "Cash is in millions of 2020 pounds per
   window" although no column is called Cash — a reader has to map it onto
   Gross / Batt. cost / Net. Cosmetic.
5. **Tables D.6 and D.7 (p.27)**: right-aligned numeric columns, consistent minus signs, no
   overflow, caption above each table; the sum convention of the last two D.6 columns is
   stated.
6. **Figure III.1 (p.8)**: the three boxes now name the information each decision uses
   (12 h forecasts, 84 h matching-slot averages; A's 12 h forecasts, B's expected gap sign);
   arrows and the "Next half-hour" arc are legible, nothing clipped.
7. **Tables D.2 (p.23) and D.5 (p.26)**: legible, bold cells consistent with the text; D.2(a)'s
   column header sits slightly high but no cell is missing.

## 7. Open items

Nothing found this round changes a headline number. What remains:

1. **Six-window means are still in-sample.** D.7 now prints a band, but the band resamples the
   same six windows that selected controller and capacity variants, so it measures dispersion
   inside the replay panel, not the probability of profit in a new year. The report says this
   ("The intervals do not estimate the probability of profit in a new year"), which is the
   honest reading; a reader should not upgrade 11.95 into an out-of-sample expectation.
2. **Reproducibility covers one window and the DP path.** The Xpress plant arm, the 192-window
   DP audit and the six historical replays remain documentary. Also, the archive still needs a
   solver-import shim to start; the README's "no licence needed" is true but a reader without
   Xpress hits an ImportError first. Suggested fix: move the `xpress` import inside the solver
   adapter.
3. **D.6 and D.7 sit side by side with different conventions** — sums of five windows in D.6
   versus percentile bounds over six resampled windows in D.7. Both captions say so; the
   proximity is still the most likely place for a reader to slip.
4. **Ridge's 0.102M parameter count** in Table D.2(b) is still not in the light archive
   (author-reported), so it cannot be checked without the training run.
5. Cosmetic: the "Cash is in millions of 2020 pounds" wording (p.9) and the unsorted citation
   `[1, 12, 9]` on p.8.

Closed since v1.2: the 2.5p phrasing (now £0.025 between feasible value and recorded bound),
Figure III.2's right panel, the caption-level definition of Gross, the six-window interval, and
the documentary-only reproducibility claim.

## 8. Assessment

Against my Tier 2B standard (anchors A1 0.95 / A2 0.85 / A3 0.78 / B 0.65 / C 0.55 / D 0.40,
D7 weighted twice):

| Dimension | v1.2 | v1.3 | Basis |
| --- | --- | --- | --- |
| D1 Model formulation | 0.86 | 0.86 | unchanged; planning programme (III.2) now printed on p.8 |
| D2 Accounting integrity | 0.87 | **0.88** | Gross/Net defined in the Table III.1 caption; all six D.6 rows, six D.7 rows and the capital budget rebuilt from new ledgers |
| D3 Chronological evidence | 0.86 | **0.87** | horizon extension audited against Xpress on 8 sampled plans (all optimal, ≤ £0.025); the 2.5p claim is now unambiguous |
| D4 Robustness / ablations | 0.86 | **0.87** | two new tables and four new evidence files (horizon, window uncertainty, capital budget, horizon audit), all spot-checked values reproduce |
| D5 Reproducibility | 0.72 | **0.88** | runnable replay executed here and exact on 2025/26; still one window, still needs a shim, plant arm documentary |
| D6 Communication of uncertainty | 0.89 | **0.92** | resampling interval on the headline means, with the "not a profit probability" caveat |
| D7 Presentation (×2) | 0.88 | **0.89** | ticks on both panels of III.2/III.3, Gross in the caption, clean D.6/D.7, correct superscript; two wording nits remain |

Weighted score: (0.86 + 0.88 + 0.87 + 0.87 + 0.88 + 0.92 + 2 × 0.89) / 8 = 0.8825 → **88**
(previous rounds: preview 79, v1 83, v1.2 85).

Band: **85–91**. The upside is limited by in-sample six-window means and by the fact that the
executed replay covers one window, not the plant optimisation. The downside is protected by
stronger evidence than v1.2 had: 112 independent checks pass, the whole D.6/D.7 grid was
rebuilt from the ledgers, and the author's operational pipeline ran here and reproduced printed
values with zero difference.

## 9. What would change this assessment

- Shipping the six historical windows' inputs (or a second window) and making the solver
  import lazy: D5 0.88 → ≈0.93, score ≈89.
- A forward or leave-one-window-out test in place of resampling the same six windows:
  D6 0.92 → ≈0.95, score ≈89.
- Conversely, if any printed D.6 or D.7 cell is later found not to reproduce, D2/D4 fall below
  0.80 and the score drops below 85 even though the prose is unchanged — in this report the
  tables, not the argument, carry the evidence.
