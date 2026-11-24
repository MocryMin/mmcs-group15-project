# v7 verification of the Tier 1 report candidate

Verifier: `mocry-cleveruser`. Date: 2026-11-24.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261124-v7/report.pdf`
sha256 `2cb86889e93487dec92d54b372806d76c78acba1f9d4e3fcd473372b304b7b2f`, 201,471 bytes, 16 PDF pages
(front matter i–ii, body pages 1–6, R1, A1–A7). Published at `1bb26de`; checksums were aligned with Git line endings at
`2dfb603`; the review requests are `2a8e5658…` (Opus) and `209acba8…` (CU) at `af0f741`, which replies to my v6.5 message
`01ac5c78…`.
Package: seven files in `SHA256SUMS.txt`, all seven digests recomputed and matched, no unlisted file in the directory:
`README.md` `ff5ba41b…`, `display-table-evidence.json` `dc252858…`, `renewable-attribution.csv` `143f7463…`,
`report-source.zip` `27f4e4b0…` (15 entries), `report.pdf` `2cb86889…`,
`tier1-xpress-review-evidence.zip` `3cf6712f…` (34 entries), `xpress-comparison.csv` `54c4d6ed…`.
The shipped `renewable-attribution.csv` and `xpress-comparison.csv` are byte-identical to
`report-source.zip:evidence/*.csv` and to `tier1-xpress-full-20261124/comparison.csv` inside the evidence ZIP.
Baselines used for the unchanged material: the pinned v6.3 supplement `tier1-site-evidence-v6.3.zip` (`202bb3de…`,
34 entries, `MANIFEST.json` with 33 hashes), the v6.2 archive `tier1-site-evidence-v6.2.zip`, the v6 archive
`tier1-site-evidence-v6.zip` (190 files), Julian's study at commit `c3902fe`, and the frozen half-hour panel
`tier1-halfhour-20261113-v7/inputs/halfhour.csv.gz` whose sha256 `890ee68a…` matches `input-hashes.json`.
Standard: `../20261122-tier1-independent-standard/{STANDARD.md,ADDENDUM_1_OFFICIAL_RUBRIC.md,ADDENDUM_2_PAGE_RULE.md}`
(10 pages means body pages).
Machine checks: `v7_checks.py` → `checks_v7.json`, **117 checks, 7 failures**; every failure corresponds to a P2 or a
note below and none of them is a headline number.
Independence: I read `mocry-codex`'s request and then the artefacts. No other agent's v7 review was consulted. Every
number below was recomputed from the archives, the frozen panel, the archived schedules or the LaTeX source. The new
renewable attribution was recomputed from the panel and the `.npz` schedules by my own implementation of the method
printed in Appendix C.4, not by running the authors' script.

## Verdict

v7 closes the compliance item and most of the bookkeeping I recorded against v6.5, and it does not regress any printed
number. The appraisal now leads with the brief's 20%–100% floor — six modules (30.2 MW) with no batteries — and holds
the supplier's 12.5% floor as a conditional second case; the "why may we go below the brief's floor" question is
answered by brackets rather than left implicit. Appendix C is rebuilt around a daily reference model, a full Xpress
capacity search with competing configurations, and a defined renewable-surplus attribution. Tables I.2, II.3, II.5,
II.6, II.7, III.1, B.1, C.2 and C.4 reproduce from the pinned archives; the new Tables C.1 and C.3 reproduce from the
shipped evidence, and my independent recomputation of all nine rows of Table C.3 agrees with the shipped CSV to
better than 1e-6 GWh/year.

Two things are new and worth a sentence each before submission. First, Table C.3's renewable capture and the
"diverts 125 / 118 GWh" sentence in the same appendix come from two different optimal schedules of the same case, so
the identity input = capture + diverted does not close with the printed numbers (1.8 and 2.1 GWh/year, 1.4%).
Second, `input-hashes.json` in the new evidence bundle records a `report.pdf` digest that is not the shipped PDF, and
the third pinned input is not in the repository at all. Both are cheap to fix and neither touches the argument.
Score **87** (range 84–90; v6.5: 84).

## Disposition of my v6.5 items

| v6.5 item | v7 status | Evidence |
|:--|:--|:--|
| P1 headline fleet rested on 12.5% where the brief states 20%–100%, with no stated reason | **Closed** | Abstract and §II.5.5 lead with six modules at the brief's 20% floor; the seven-module case is labelled "product floor, 12.5%" and made conditional on supplier confirmation (Table II.7, printed p.5). Table II.6 now sizes capacity at each hydrogen price under 12.5% and Table B.1 separates the two floors |
| P2-1 Figure I.1 left axis labelled `Mean surplus (GWh)` while the values are per half-hour | **Closed** | Printed axis now reads `Mean surplus (GWh per half-hour)`, identical to the string in `figures/plot_surplus.py`; confirmed visually on PDF p.3 |
| P2-2 §II.5.4 said the upkeep case falls to £0.24m; arithmetic gives £0.23m | **Closed** | Text now prints −£0.23m and −£2.60m; `display-table-evidence.json` records −0.230689 and −2.598707 from `fixed_pair.csv` and `reference_day_A_integer.json` |
| P2-3 20% certificate had `upper_mGBP` 118.820805 above `global_upper` 118.819823 | **Closed** | Ordering is now feasible 118.818207 < tightened global upper 118.819824 < raw LP bound 118.820807. Table C.1 prints the raw Xpress bound and §C.2 states the tighter HiGHS bound explicitly |
| P2-4 Table II.3 20% joint `Served` cell reused the 12.5% macro with no 20% source | **Closed in evidence** | `display-table-evidence.json` now carries the 20% value (90.160944%, delivered 1,370,869,993 MWh of 1,520,469,864 MWh); I recomputed 90.1619% from `tier1-commitment-20-20261124/A-45-6-rounded.npz`. The macro reuse itself remains cosmetic (P2-4 below) |
| P2-5 Table III.1 does not print the 11-block column that §III and §C.3 name | **Open** | Table III.1 (printed p.6) still shows 1/7/45 and 1/9/22; the 11-block totals 22.99 and 40.97 appear only in §C.3 (p. A6) |
| P2-6 cover carries no author names | **Open** | Cover p.1 has title, course, group and date only |
| P2-7 1,559 t/day broad-market case had no source file | **Closed** | §A.2 now states the case as a scenario input; the records exist in the v6 archive (`tier1-xpress-reproduction-20261122/README.md`, `joint/B_n7_h11.json`, `joint/B_n11_h10_annual.csv` with 1,867 MW, enumeration files with 1,821 MW) |
| P2-8 Tier 2B A baseline moved from flexible to committed dispatch without a version note | **Partly closed** | §III.1–2 now state the committed basis plainly ("the plan applies the 12.5% minimum load and four-day run rule"), but nothing says this replaces the earlier flexible baseline |
| P2-9 20% zero-battery six-module sizing record missing from the bundle | **Closed** | `A-zero-0.2-xpress.json` (6 modules, £13.459603m/year) ships; the 12.5% twin `A-zero-0.125-xpress.json` (7 modules, £13.679210m/year) reproduces Table II.7 |

## What I recomputed, and how it came out

**Renewable surplus (new §II.5.3, Table C.3, Appendix C.4).** Method as printed: surplus_t = (G−D)+ per half hour,
capture_t = min(surplus_t, electricity taken by the equipment), both weighted by the day's renewable share of
generation (wind onshore/offshore, solar, biomass, run-of-river hydro, plus the separate wind farm). My implementation
reproduces the panel totals exactly — 5,164.674 GWh/year all-fuel half-hour surplus, 2,276.157 daily-netted, 2,432.234
renewable — and all nine CSV rows:

| Case | Available | Captured | Remaining | Printed |
|:--|--:|--:|--:|:--|
| Daily two-hour A / B (daily-netted basis) | 1,137.654 | 19.051 | 1,118.603 | 1,138 / 19 / 1,119 |
| Four-day, 20%, 0 blocks / 6 modules | 2,432.234 | 28.113 | 2,404.121 | 2,432 / 28 / 2,404 |
| Four-day, 20%, 45 / 6, discharge to sales first | 2,432.234 | 882.557 | 1,549.677 | 2,432 / 883 / 1,550 |
| Four-day, 12.5%, 0 / 7 | 2,432.234 | 31.705 | 2,400.530 | 2,432 / 32 / 2,401 |
| Four-day, 12.5%, 45 / 6 | 2,432.234 | 883.264 | 1,548.970 | 2,432 / 883 / 1,549 |
| Four-day, both floors, B 9 / 0 | 2,432.234 | 240.155 | 2,192.080 | 2,432 / 240 / 2,192 |
| Half-hour switching, 12.5%, A 45 / 6 | 2,432.234 | 828.518 | 1,603.716 | 2,432 / 829 / 1,604 |
| Half-hour switching, 12.5%, B 9 / 10 | 2,432.234 | 278.467 | 2,153.767 | 2,432 / 278 / 2,154 |

The discharge-routing sensitivity also reproduces: giving electrolysis first call on ambiguous battery discharge
lowers capture by 0.264 (20%) and 0.261 (12.5%) GWh/year, so "less than 0.3 GWh/year" holds. The two-hour rows use the
daily-netted basis, which is why their "available" column is 1,138 rather than 2,432 — as printed in the caption.

**Xpress capacity results (Table C.1, §C.2, §II.5.1).** Every printed value matches
`tier1-xpress-full-20261124/comparison.csv`: A 20% 118.818207–118.820807, A 12.5% 118.898893–118.900891, B
6.07025804–6.07025820, daily A 12.462039 and B 2.180223 (identical under Xpress and HiGHS), and the wall times
0.21 / 76.80 / 50.99 / 86.33 / 70.04 s. The nearest competing capacity is 46 blocks and six modules at both floors
(LP bounds 118.811175 and 118.890634, both below the 45/6 feasible gain); B's eight-block bound 6.069620 is below the
nine-block gain, so §II.5.1's "£639/year over eight" reproduces (6.07025804 − 6.06961951 = £638.5/year). The
`annual-results.csv` per-year figures re-aggregate to the same annual means, and they reproduce Table II.4 exactly:
A 39.12 / 19.53 / 65.10 and B −13.07 / −12.85 / −8.01 for 2023–25, 2024–25 and 2020–25 excluding 2022, on the 12.5%
45/6 and 9/0 basis the caption names.

**Daily reference model (new Appendix C.1).** The printed rules match the archived implementation
(`tier1-halfhour-20261113-v7/model.py`, `dt=24` branch): ηc_d ≤ W_b and (r_d+u_d)/η ≤ W_b per period, stock carried
across days with s_T = 0, electrolyser input either zero or between the minimum load of one module over 24 h and the
combined rated input, integer equipment counts (`integer=not relaxation`), and the daily buyer limit. The daily model
reproduces 12.462039 and 2.180223 under both solvers with 13,155 columns and 24,113 rows, and its schedule reconciles
to the frozen panel to 4e-9 GWh. The four-day commitment rule (II.8) is implemented by the day DP in
`site_model.py` ("each start followed by at least `min_days` days") and by the MILP commitment subproblem that
`halfhour.py` calls.

**Unchanged tables.** Table II.7 reproduces metric by metric from `A-zero-finance.json` and `A-7-finance.json`;
Table II.5 from `fixed_pair.csv` and the daily reference JSON; Table II.6 from `four-day-hydrogen-price.csv`
(2.50/5.00/7.80/9.50 → 0/6/7/7 modules, 0.00/4.52/13.68/19.60); Table C.2 from `A_summary.json` and `B_summary.json`
(5.63/1.63 and 1.64/1.50, break-even £213 and £130/kWh); Table III.1 totals from `capacity-summary.csv`
(4.65 / 7.58, −1.54 / −1.23, peak at 11 blocks 22.99 / 40.97); the strict-B hydrogen bound from
`B-hydrogen-bound.json` (116 days, £0.326m, £0.757m).

## New findings

**P2-1 Renewable capture, diverted electricity and served demand are quoted from two different optimal schedules.**
Table C.3 (p. A6) gives all-fuel capture 63.23 GWh/year at 20% and 71.70 at 12.5% with total electrolysis input
190.42 and 192.17 GWh/year, both of which I reproduce exactly from the shipped `.npz` files. The next sentence quotes
"diverts 125 GWh/year ... and 118 GWh/year" and "served falls by 0.049 and 0.047 percentage points", which are
`diverted_gwh` and `served_change_pp` from `A-zero-finance.json` / `A-7-finance.json` — the v6.5 HiGHS schedules,
where the surplus share was 65.03 and 73.77 GWh/year. The identity input = capture + diverted therefore does not close
with the printed numbers: 190.42 − 63.23 = 127.19 against 125.39, and 192.17 − 71.70 = 120.47 against 118.39. The
cause is benign — capture is not part of the objective, so equally optimal schedules differ in where the electricity
comes from — but a reader who checks the arithmetic will find a 1.8–2.1 GWh/year (1.4%) gap and no explanation.
Either quote one schedule throughout, or say that capture varies between 63–65 (20%) and 72–74 (12.5%) GWh/year across
alternative optima. No consequence for the recommendation or for the Tier 2B comparison.

**P2-2 The new evidence bundle's own provenance record is partly stale.** `input-hashes.json` pins three inputs. The
half-hour panel is right (`890ee68a…` matches the archived study panel). The `report.pdf` entry records
`7ab31838e9c8…`, which is not the shipped PDF (`2cb86889…`, as bound by `SHA256SUMS.txt`) — it is presumably an
earlier build. The third entry, `storage-exploration-20261116-v2/utility4h/configuration.json`, is not in the published
tree at all, so its hash cannot be checked by anyone. Related: unlike the v6.3 supplement, the v7 bundle ships no
`MANIFEST.json`, so the 6.5 MB of new schedules, logs and `.npz` files are covered only by the outer ZIP digest. The
report PDF itself is correctly bound; this is about the evidence chain.

**P2-3 Table III.1 still does not print the block count the text reasons about.** §III.3 and §C.3 say the six-window
sum peaks at 11 blocks in both policies (£22.99m and £40.97m), but Table III.1 (printed p.6) prints only 1/7/45 and
1/9/22. Adding an 11 column, or a sentence giving the six-fold totals, would let the reader see the number the
investment advice rests on.

**P2-4 Two v6.5 presentation items are unchanged.** The cover still carries no author names, and the 20% joint
`Served` cell is still produced by the `\TwentyCoverage` macro (90.16%), even though that value now has its own
recorded source.

## Notes, not defects

- **N-1 Two different A gaps for the same case.** §II.5.1 and Table C.1 use the Xpress bound and quote £2,600/year;
  §C.2 quotes the tighter HiGHS bound, which implies £1,617/year. Both are correct; saying which bound belongs to which
  sentence would remove the apparent contradiction.
- **N-2 The A and B "Served" columns are not comparable.** A's no-additions entry is 89.66% and B's is 91.03% with
  no equipment at all. I reproduced both: B is min(G,D)/D = 91.0318%, while A's 89.6575% is what you get when the
  negative-price sales that A may decline are dropped (1,942 half-hours, 3,483 GWh/year, 3.4% of demand). The mechanism
  is stated once in §II.4.2 but not in the Table II.3 caption, where a reader will look.
- **N-3 2,432 and 2,276 are both stated but never bridged.** §I.3 gives 2,276 GWh/year of daily-netted all-fuel
  surplus, §II.5.3 gives 2,432 GWh/year of renewable surplus, and Table C.3's two-hour row gives 1,138. The three are
  consistent (different bases) but only the table caption hints at it.
- **N-4 The `.npz` columns are undocumented.** `sales`, `discharge` and `hydrogen` do not map one-to-one onto the
  notation of (II.3), which is why the "ambiguous discharge" routing rule has to be inferred from the script. The
  claimed sensitivity (<0.3 GWh/year) is robust either way.

## Visual review

Rendered and reviewed as images with the current model on this exact PDF revision (records persisted per page):
PDF p.3 (Figure I.1, Tables I.1–I.2), p.6 (Table II.3, Figure II.1, Table II.4), p.7 (Tables II.5–II.7), p.8
(Table III.1), p.14 (Table C.1), p.15 (Tables C.2–C.3), p.16 (Table C.4) — seven pages, all pass, no overflow,
overlapping glyphs, clipped captions or misaligned decimal columns. The I.1 axis label is legible and correct, and
Table C.1's "Feasible" and "Upper bound" columns are separable. Pages 1–2, 4–5 and 9–13 were read as text but not
reviewed as images; this is model-assisted appearance review, not human sign-off.

## Score

Descriptor weights as in `ADDENDUM_1_OFFICIAL_RUBRIC.md` (presentation double-weighted):

| Descriptor | v6.5 | v7 | Why it moved |
|:--|--:|--:|:--|
| Problem framing and analysis | 0.82 | 0.86 | headline case now keyed to the brief's own floor, with the product floor as a labelled sensitivity |
| Research and inputs | 0.86 | 0.86 | unchanged in substance; three pinned inputs, one of them stale (P2-2) |
| Model formulation | 0.89 | 0.91 | daily reference model, commitment and priority rules now documented and matching the archived code; renewable attribution defined |
| Results and validation | 0.82 | 0.85 | full-horizon Xpress search with competing configurations and honest bound ordering; but the capture/diverted split is internally inconsistent (P2-1) |
| Sensitivity and robustness | 0.82 | 0.84 | routing sensitivity added and the price sweep retained; window sensitivity unchanged |
| Recommendation and decision support | 0.88 | 0.90 | conditional structure, deferral advice and the 34% / 25% support arithmetic are all reproducible |
| Presentation | 0.83 | 0.85 | axis fixed, appendix C restructured; missing 11-block column, no authors, unbridged 2,432/2,276 (P2-3, P2-4, N-3) |

Score = (0.86 + 0.86 + 0.91 + 0.85 + 0.84 + 0.90 + 2 × 0.85) / 8 = **0.865**, reported as **87** (range 84–90).

What would change it: closing P2-1 and P2-2 (one consistent schedule for capture/diverted, corrected
`input-hashes.json`, a manifest in the bundle) would put a 90 within reach; printing the 11-block column, naming the
authors and adding the A/B `Served` footnote would add another point. A genuine Tier 2B-into-Tier 1 integration, or a
supplier-quote-based battery case, is what would move this out of the high 80s.

## Reproducing this review

From `mmcs-review-20261122/Tier1/workspaces/mocry/cleveruser/review/20261124-tier1-v7-verification/`:

```
python v7_checks.py     # reads the published ZIPs, panel and archives directly; writes checks_v7.json
```

The script needs `pypdf` and `numpy` and the sparse checkout paths
`Tier1/workspaces/mocry/codex/work-history/20261113-v1/studies/tier1-halfhour-20261113-v7/{inputs,source_data}`.
The seven recorded failures are P2-1 (two checks), P2-2 (two checks: the stale `report.pdf` pin and the unshipped
configuration), P2-3 (11-block column), and P2-4 (the macro reuse and the missing authors).
