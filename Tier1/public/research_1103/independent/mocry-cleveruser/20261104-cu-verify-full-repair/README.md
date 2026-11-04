# Independent verification of the 20261104-v2 full data repair

Publication date: 2026-11-04. Author: `mocry-cleveruser` (member `mocry`, independent reviewer).
Class: verification of another agent's data release, plus a correction to my own 2026-11-04 audit.

Scope: `Tier1/public/data_quality/full_data_repair/20261104-v2` (published in commit `0a821ea`) and
the downstream artifacts that consume course prices. I did not modify the course inputs or the
repair package, and I do not re-decide the Tier 2 route (2A vs 2B).

## 1. Bottom line

The repair is reproducible and its main diagnostic claims survive independent recomputation,
including a live re-query of the upstream price endpoint that does not depend on the author's
archived evidence. Two of its findings are materially larger than anything in my own 2026-11-04
audit:

| Finding | Effect on the model-ready series |
|---|---|
| Course prices were averaged over all MID provider records, including a zero-volume, zero-price placeholder provider on nearly every half hour | Corrected level is **2.00× the course level** (median daily ratio exactly 2.000; annual means 2.01–2.10×). Any economics built on the course price column understate revenue by about half. |
| Course demand copied a partial window on weekly query-end dates | **340 of the 351 largest demand changes are Tuesdays**; the course series carries a weekday artifact of **+1,741 MW on Tuesdays** against **−3,005 … −3,328 MW on the other days**. After repair all seven weekdays sit at −2,125 … −2,417 MW. |

My earlier audit (`20261104-cu-full-data-audit`) missed both. Section 6 records the correction.

## 2. What I ran

1. `repair_data.py --course-root . --verify` → `All eight data and audit files reproduce exactly.`
   (byte-exact rebuild of the five model CSVs and three audit files from the archived evidence;
   Windows needs a `tzdata` package because `zoneinfo` has no system database.)
2. `validate_release.py --course-root .` → all 15 published assertions pass.
3. My own checks below, written against the published CSVs and the archived evidence only. They do
   not import the repair module, so a shared bug in the author's code and audit would not hide.

## 3. Results of the independent checks

Structure and identities (all 5 series, 2020-01-01 … 2026-09-17):

| Check | Result |
|---|---|
| Days per series | 2,452 for generation, total, demand, price, wind farm; no gaps, duplicates or extra dates |
| Fuel categories | 11, no negative cell; Σ(11 categories) − total = **0.0 on all 2,452 days** |
| Price unit identity | `£/MW_day − 24 × £/MWh` = **0.0 on all 2,452 days** |
| Five-series join | 2,452 days (the course files gave 2,406 or 2,421 depending on the pair) |
| Wind farm | 2,452 rows; the 10 exact-zero days are retained; 2026-09-18 dropped |

Generation, against AGPT evidence:

| Check | Result |
|---|---|
| Days with 48 AGPT half hours in the evidence | 2,188 |
| Repaired value equals the AGPT same-day mean (all 11 fields within 1 MW) | **2,063 / 2,188** |
| The 125 exceptions | AGPT itself collapses or is incomplete there (e.g. 2022-12-09 … 12-15, gas +21,000 … +23,000 MW vs AGPT), i.e. the documented FUELHH reconstruction path |
| 2022-12-12 spot check | repaired total 35,774 MW; FUELHH domestic outturn 35,123 MW, incl. interconnectors 37,849 MW; course value 1,664 MW |
| Course solar-zero dates | all 42 now positive, 97–2,709 MW; zero-solar days in the repair: **0** |
| Missing generation dates | all 30 restored |

Demand:

| Check | Result |
|---|---|
| Changed days vs course | 471 of 2,451 shared dates |
| Weekday structure of the 351 largest changes | **340 Tuesday**, 7 Thursday, 3 Friday, 1 Monday |
| Repaired value vs the archived VD full-day mean | matches to the published integer (e.g. 2021-01-12: 35,846.5 → 35,846; 2024-11-19: 36,161.6 → 36,162) |
| 2022-08-02 | 636 → 28,744 MW; the archived VD day has 288 records whose mean is 27,309.6 MW with 17 slots stuck at 636 MW |
| Reconstructed days | 153; the TSD−VD offset stays inside 3σ of the clean-day band (median −166 MW, σ 240 MW); worst deviation −958 MW (2026-08-06) |
| Largest day-to-day jumps (43 above 5 GW) | all on `strict_no_imputation` days, so they are a property of the VD source, not of the repair |

Price:

| Check | Result |
|---|---|
| Evidence days | 2,422 days × 48 half hours, 2 providers per half hour |
| Repaired value equals the active-provider volume-weighted daily mean | **2,372 / 2,422** |
| Course value equals the flat mean over all provider records | **1,954** days, and the mechanism is visible directly: one provider carries volume 0 and price 0 |
| Zero-volume provider records excluded | 115,571 (vs 116,137 active records) |
| Daily ratio repaired / course | median **2.000**, mean 2.152, annual 2.014–2.096 |
| 2020-01-01 | 18.5934 → 37.1869 £/MWh |
| Negative daily means | course 9 (plus 1 zero day) → repaired **2** (2020-05-22, 2020-06-28); maximum 667.65 on 2021-09-09 |
| Live Elexon MID re-query, independent of the archive | 2020-01-01: active-vw **37.1869**, flat-over-all-records 18.5934; 2023-05-09: 101.3623 vs 50.6811 |

Supply–demand balance recomputed on the repaired panel (2,452 days, constructed-system boundary):

| Quantity | Course inputs (2,421-day panel) | Repair (2,452 days) |
|---|---:|---:|
| Deficit-day energy | 178.88 TWh | **144.27 TWh** |
| Surplus-day energy | 32.92 TWh | **11.41 TWh** |
| Surplus-day share | 24.5% | **17.7%** |
| Mean residual (generation − demand) | −2,512 MW | **−2,258 MW** |
| Tuesday mean residual | **+1,741 MW** | **−2,221 MW** |

The repaired panel has no weekday signature, which is what a coherent daily panel should look like.
Adding the simulated wind farm keeps the same shape. In 2023 the repaired panel gives 29 surplus
days and 549.9 GWh, which matches the 549.944 GWh that the author's Baseline 1104 reports.

## 4. Downstream artifacts that now need care

1. **Reviewed research release v1.1, `R4-finance-data/prices_gbp2020.csv`** (2,422 rows) is built
   from the course price column and therefore sits at about half the corrected level (mean
   £48.17/MWh in 2020 money). `BASELINE_CANDIDATE.json` likewise records
   `market.prices = "Course wholesale daily price proxy deflated to GBP2020"`. Any member who
   consumes that file gets roughly half the wholesale revenue. The release itself already flags
   "original producer aggregation not independently established", so this is a known gap that has
   now been measured. I have asked the owner to publish a correction rather than editing another
   agent's release.
2. **`Tier1/workspaces/mocry/codex/baseline-1104`** already carries the ablation and is consistent
   with the repaired series: policy A with a fixed 20 MW electrolyser moves from £15.188 m/year
   increment under the course price to £8.572 m/year under the repaired price (−43.6%), and its
   2023 electricity revenue (17,126.9 m for 214,944 GWh) implies a mean realised price of about
   £79.7/MWh in 2020 money, which matches the repaired, deflated series. It is a personal
   workspace candidate, not a group decision.
3. **Tier 2 route choice (2A vs 2B)** is not touched by the data repair: the repair changes levels
   and therefore every economic magnitude, but it does not choose the supply-policy question.

## 5. Residual limits of this verification

- I verified identities, coverage, reproduction and the two defect families. I did not audit all
  26,972 fuel cells individually, nor every one of the 87 "2026 extract differs" dates.
- 436 days carry estimation or interpolation and 323 carry cross-source reconstruction (overlapping
  classes; 1,929 days are strict). The author states the holdout errors; they are estimates, not
  bounds. A model that reports only the full repaired panel is hiding that sensitivity.
- The 2026 year is a 260-day partial year and keeps the structural break I reported earlier
  (solar 2,782 MW, offshore 5,472 MW, onshore 4,031 MW, gas 7,903 MW mean). The repair does not
  remove it.
- I did not re-solve the author's optimisation model or re-verify its 82 cases; I checked the
  arithmetic paths that connect its headline numbers to the repaired data.

## 6. Correction to my own 2026-11-04 audit

My full-data audit verified structure, the 24× price identity, distribution tails, the wind-farm
zero days and the balance boundary. It did not test **provider aggregation** inside the price
series and did not test **weekday structure** in demand. Both gaps are now closed by measurement,
and two statements in that report must be read as superseded:

- "9 negative price days and 1 zero-price day" describes the course file correctly, but 7 of the 9
  negative days are midnight-window artifacts; only 2020-05-22 and 2020-06-28 survive as negative
  daily means.
- The balance table (160.30 → 116.96 TWh with the farm, etc.) is arithmetic on the course inputs.
  It remains correctly computed and it is the reason the repair was needed, but it is **not** a
  description of the series a model should now use. The repaired panel gives 144.27 / 11.41 TWh.

What survives unchanged from that audit: the supply–demand residual is a system-boundary
convention rather than a physical energy balance; the wind farm is a single simulated asset
(24.3 TWh over 2,406 dates, 24.85 TWh over 2,452); 2026 is a partial year with a structural break;
the 2022-08-02 demand value was corrupt; and the course price column had no ≥£1,000 day.

One difference of interpretation remains open and is not worth a version: the repair keeps the
10 exact-zero wind-farm days as simulation output, I read them as missing. The material effect is
about 0.10 TWh out of 24.85 TWh.

## 7. 中文摘要

本轮远端新增两个包：`20261104-v2` 全量数据修复，以及 `mocry-codex` 个人工作区的 Baseline 1104。

- 修复包可逐字节复算，15 项自检全部通过。我另写了不引用其代码的核查：五份表各 2,452 天、分燃料之和严格等于总量、价格两列严格 24 倍、42 个光伏零值日全部恢复、30 个缺失日补齐。
- 最重要的是两个新发现：课程电价把"零成交量、零价格"的占位供应商算进了均价，**修复后水平约为原来的 2.00 倍**；课程需求在周查询末日取了残窗口，**351 个最大变动日中 340 个是周二**，原数据周二残差 +1,741 MW、其余日为 −3,000 MW 左右，修复后七天都在 −2,100…−2,400 MW。
- 因此 20261103-v1.1 的 `R4-finance-data/prices_gbp2020.csv` 与 `BASELINE_CANDIDATE` 的电价口径偏低约一半，已请 owner 出更正，我没有改他人发布物。
- 我自己的 20261104 全量审计漏了"供应商聚合口径"和"星期结构"两项，已在第 6 节明确更正：9 个负价日中 7 个是残窗口假象；平衡表数字仍算对，但已不代表应使用的数据。
- Tier 2 的 2A/2B 路线不受数据修订影响，仍由人决定。
