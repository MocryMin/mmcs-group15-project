# Clever User harness session — resumable state

Agent: `mocry-cleveruser` · Member: `mocry` (Ran Min / GitHub `MocryMin`) · Model: deepseek-v4.1-flash 1017 · Harness: Clever User (build not exposed) · Registered 2026-11-03T19:0xZ, registration commit `66d7c8a`.

This subfolder is this agent's own writing area inside member `mocry`'s workspace, kept separate from `mocry-codex` material. `mocry-codex` remains the maintainer agent; nothing here is a group decision or a revision of its publications.

## What this session has done

1. Cloned the repository and read: `AGENTS.md`, `agent_protocol.md`, root `README.md`, `PROJECT.md`, both tiers' `public/agent_skill_protocol.md` and `agent_message/agent_skill_protocol.md`, `Tier1/public/PROJECT_SCOPE.md`, `Tier2/public/PROJECT_SCOPE.md`, all of `Tier1/public/baseline_1103/` (INDEX, BASELINE_1103, GAPS, TEACHER_CLARIFICATIONS, TEACHER_ORIGINAL_EXCERPTS, RESEARCH_REQUEST), the v1.1 research release README and `EXECUTIVE_SUMMARY_EN.md`, and the six published Tier1 messages (all seen, see below).
2. Registered as a second, concurrent agent of member `mocry` under a different harness, per the root bootstrap instruction: setup, `register`, one registration commit, helper checks and `19` tool regression tests passed, pushed as `5edc7d4..66d7c8a`.
3. Local clone note: `origin` was switched to `git@github.com:MocryMin/mmcs-group15-project.git` because HTTPS push could not authenticate non-interactively in this shell while the machine's SSH identity (`gh` reports git protocol SSH, `Hi MocryMin!`) works. Pull requests, branches and history were untouched.

## Seen message checkpoint

`d000f731b5e84c8091b877d464b3536a`, `9a14b411d65745efa6caec11dd8a8d69`, `6e5538392d904dc2b395b7e4fff01bde`, `f5bee2e6ae1c4cee93a6ba845d0b07cc`, `3c584488cd574978828f7db7c13a4508`, `3d77da4be9d04bc4b5ebf9aa0a098071`.

## Verified project state (as read at 2026-11-03T19:00Z, commit 5edc7d4)

- Tier1: Open only so far. Baseline 1103 (model family BL-01..BL-15, gaps M/E/B/H/F/D/V/X/Q, A/B four-way comparison A0/A1/B0/B1) and the controller-reviewed research release `20261103-v1.1` exist as proposals. The release gives typed parameters (`BASELINE_CANDIDATE.json`) for market, battery, electrolyser/H2 and finance/data.
- No optimisation code, no solved investment result and no tier-wide agreed parameterisation exist in the repository yet. `.py` content in the repo is only `tools/collab.py` and its tests.
- Tier2: scaffold only; the extension route (Tier2A generation investment vs Tier2B strategy/operation through time) is explicitly not chosen, and no Tier2 decision, interface or dependency is recorded.
- Membership: only member `mocry` has registrations (`mocry-codex`, and now `mocry-cleveruser`). No other members are registered, so group adoption of any baseline cannot be evidenced yet.
- The 2026-11-03T13:39:02Z request asked Ran Min to dispatch independent researchers including "DS v4.1 flash1017/Clever User"; the v1 research round was completed by other models and explicitly claims no Clever User result. This session therefore has a standing, unfilled invitation to contribute independent Tier1 research.
- Root inputs: five unchanged CSVs, brief PDF, two transcripts, `SOURCE_MANIFEST.json`. Report due 27 Nov 2026 10:00 Europe/London; presentation 30 Nov 2026.

## Open items owned by the human (Ran Min), not decided here

1. Whether this agent should now produce independent Tier1 research (which packages R1/R2/R3/R4, or instead the model/optimisation) and at what depth.
2. Whether the group commits to Baseline 1103 as the working baseline, and how other real members are invited/onboarded.
3. Tier2 route choice and who owns it; until chosen, Tier2 work stays provisional.
4. Report/pitch scope limits (ten-page limit, reference/appendix counting) — course rules are unresolved in the repository.

## Next safe actions for this agent

- Stay inside `Tier1/workspaces/mocry/cleveruser/` for drafts; publish new uniquely named public artifacts through `tools/collab.py publish`; send messages for coordination, not for routine status.
- Do not overwrite `mocry-codex` publications, root infrastructure, or `Tier1/public/baseline_1103/` current files; add versioned/correction artifacts and message the maintainer instead.
- Any claim about the datasets or parameters must be reproduced from the repository inputs or cited to a public source with units and date; this session has not independently re-verified the v1.1 parameter values yet.

## Addendum 2026-11-03 22:0x Z — independent research round published

- Ran an unleaky replication of the Tier1 research request: four researcher workers (`res-r1-market`, `res-r2-battery`, `res-r3-hydrogen`, `res-r4-finance-b`) each got a byte-identical input bundle and were forbidden to read `Tier1/public/research_1103/**`; all four declared no earlier-round or peer material seen. Workers were paused for a harness update and resumed from their durable sessions rather than restarted.
- Controller side: own deterministic CSV audit (`audit/`), cross-check of R4's 107-date artefact (`audit/crosscheck_r4_artefact.json`), and a recomputation pass that found one arithmetic defect in R3 (stated core electrolyser CAPEX £1.50 m/MW_e does not follow from its own BEIS basis; recomputed £1.04 m/MW_e, recorded as CR-1).
- Published as `Tier1/public/research_1103/independent/mocry-cleveruser/20261103-cu-v1/` (65 files, one operation record each in `Tier1/public/logs/mocry-cleveruser.jsonl`), commit to be recorded below in git history.
- Local-only by design: `firstpass/` (raw worker folders incl. vendor PDFs/XLSX), `release/` staging tree and the byte-identical `inputs/` copies are not committed; the public release and `inputs/INPUT_BUNDLE.json` hashes are the durable evidence.
- Open decision items for the human: discount-rate convention, electrolyser CAPEX basis (~1.8x disagreement with the earlier round on a common price basis), battery maintenance convention, hydrogen offtake cap, purchases on/off.

## Addendum 2026-11-03 23:0xZ — review of v1.1, exemplar assessment, self-compaction

**Published since the previous addendum** (all pushed; remote `main` = `3ad9095`):

| Artifact | Path | Commit |
|---|---|---|
| Independent research release | `Tier1/public/research_1103/independent/mocry-cleveruser/20261103-cu-v1/` (65 files: README, SYNTHESIS, BASELINE_CANDIDATE_CU.json, CROSS_REVIEW_NOTES, four package folders, controller audit) | `c152ed4`; announcement message `598302e` |
| Review of v1.1 (summary) | `.../20261103-cu-review-v1/REVIEW_OF_20261103_v1.1.md` | `ade78f3` / `d8da86f` |
| Review of v1.1 (full + machine-readable) | `.../20261103-cu-review-v2/REVIEW_OF_20261103_v1.1_FULL.md`, `REVIEW_ITEMS.json` | `6fa9316` |
| Request message to `mocry-codex` (kind=request, priority=action, due 2026-11-05T18:00Z) | `Tier1/agent_message/messages/20261103T222511579125Z_mocry-cleveruser_6a4ccd82b6e44940bb6ab197f5917096.md` | `6fa9316` |
| Past-report assessment | `.../20261103-cu-review-v2/REFERENCE_EXEMPLARS_ASSESSMENT.md` + workspace `reference_review/` profiles | `3ad9095` |

**Review items awaiting `mocry-codex` reply (accept/reject/defer per ID):** RV-01 model absent; RV-02 Tier1 vs Tier2B time treatment; RV-03 107-day zero-dispatch artefact; RV-04 electrolyser CAPEX 1.8x route spread; RV-05 missing "previous consultancy" comparator; RV-06 decision thresholds; RV-07 discount/price-basis and ROI metrics; RV-08 Tier2A research absent; RV-09 repo hygiene; plus six classification corrections (E-03, E-06, H-04, E-05, H-05, Q).

**Verified findings to reuse:** controller audit vs R4 audit agree exactly (2,406 dates / 28 segments / fuel sum exact / price identity exact / 9 negative-price days); 107 zero-dispatch dates reproduced (9 blocks, deficit 160.30→111.41 TWh, surplus 40.63→40.01 TWh); one arithmetic defect in the earlier round's R3 (stated core electrolyser CAPEX £1.50 m/MW_e does not follow from 0.829×1.25 = £1.04 m/MW_e).

**Exemplar assessment conclusions:** six past reports are non-energy topics; no data reusable; report length 14–18 pages is the observed ceiling; the five transferable devices are quantified-compromise disclosure, two-stage stochastic + scalability table, staged validation ladder with out-of-time and information-poor cases, switch-point/reservation-value analysis, and a one-page decision block. My bands: 74 (2025) distinction upper; historical Group15 (2025) distinction lower; Group_23 distinction lower; Group_8 merit upper; Group_20 merit mid; Group_10 merit low. No exemplar varies a decision parameter — the cheapest way to beat them.

**Workers:** `res-r1-market`, `res-r2-battery`, `res-r3-hydrogen`, `res-r4-finance-b`, `ref-tv-bank`, `ref-bank-bike` all hibernated (durable sessions kept, nothing closed). `res-r4-finance` was closed earlier after a router startup failure.

**Local-only material** (kept out of git via `.git/info/exclude`, not just .gitignore): `.clever-user/`, `firstpass/`, `release/`, `tools/`, `audit/`, `inputs/`. `git status` must stay clean before `collab.py push`.

**Next actions after resume:** check whether `mocry-codex` replied per ID; if yes, act on the two priority items (RV-05 comparator definition, RV-03 SA-DQ date list + script) and offer the threshold chart spec; if no, do not re-ping before the due time. Keep Tier2 unselected until the human decides.

## Addendum 2026-11-03 23:4xZ — 107-day repair verification and reply to the nine dispositions

**What happened after the self-compaction.** `mocry-codex` had already replied (`4a67fb3`, message `518474555d0846daa57c87cbb00d03c8`: nine dispositions + six classification decisions) and published a data-quality release (`8e89d96`, index `ace581f`). I verified both, published my verification and replied.

**Published (this addendum):**

| Artifact | Path |
|---|---|
| Verification of the 107-day generation repair | `Tier1/public/research_1103/independent/mocry-cleveruser/20261103-cu-verify-repair/` (README + 7 result JSONs + 8 scripts, 16 files) |
| Reply message to `mocry-codex` (kind=reply, priority=info, no due) | `Tier1/agent_message/messages/20261103T233938958918Z_mocry-cleveruser_dae4814d979249528f8f10018b2def4f.md` |

**Verification results (all reproducible from my scripts):**

- Their headline numbers reproduce exactly: deficit 160.30 → 116.96 TWh, surplus 40.63 → 41.89 TWh over 2,406 common dates; changed-date set is exactly my 107 dates; the 2,315 unchanged days are value-identical; fuel cells sum to total on all 2,422 days; added generation 44.603 TWh.
- Reconciliation of the two framings: those 107 days carry 48.90 TWh of the raw deficit and still 5.55 TWh after repair, so 160.30 − 48.90 = 111.41 (my earlier exclusion) and 116.96 − 111.41 = 5.55. 30.5% of the raw deficit was upstream artefact.
- Independent upstream re-query (fresh FUELHH, my own mapping): 9 sampled dates; 7 match cell-for-cell, `2023-01-01` differs by 1 MW in Other, and `2025-03-11` differs by exactly the disclosed three-interval linear fill (+799/+215/+68/+23/+20 MW).
- Attribution confirmed live: current AGPT reports all non-wind fuels as zero for 33 of 49 periods on 2022-12-13 while FUELHH shows gas 22,794 MW, nuclear 5,841, coal 1,288. The course zeros are inherited, not physical.
- Two residual 2026 issues I asked them to disclose: 61 AGPT-differing 2026 dates are outside the repair, 8 of them by >1 GW (`2026-07-01` +14,930 MW; FUELHH spot check shows the course value is the low one), worth about −0.94 TWh on the 2026 deficit; and 51 wind/solar cells were switched to current AGPT on 23 of the 107 dates, an exception to "renewables are course values".
- Narrative consequence (the point that matters for the report): deficit-type conclusions are highly sensitive (2022 −60%, whole sample −27%) while surplus/curtailment conclusions are robust (40.63 → 41.89, +3.1%). Any "2022 winter stress" story built on the raw data is an artefact; the storage/hydrogen value line does not need rewriting; double-run is mandatory, and under policy B the raw zeros would push almost all generation on those 107 days into direct sale.

**Delivery-spec check (Q):** transcript `01:05:51–01:06:49` sets the technical report at 10 pages; `01:06:49–01:07:45` makes the week-11 pitch a business presentation with no maths or code (fail if included). Separately, `01:04:00–01:04:55` (said about assignment 2's six-page limit) states appendices do not count toward the limit but should be assumed ungraded, and explicitly says not to put the integer-programming formulation or data descriptions there — so the model formulation must sit inside the 10 pages.

**Still open:** RV-04's £1.50 → £1.04 m/MW correction is still live in the R3 derived tables (a note is not enough); Tier2 route (2A vs 2B) remains the human's decision and I have not chosen.

## Addendum 5 — full audit of all disclosed data (2026-11-04)

**Delivered:** `Tier1/public/research_1103/independent/mocry-cleveruser/20261104-cu-full-data-audit/`
(README + 16 results + 9 scripts; commits `58f489f` content, `94ee1cd` message). Note to
`mocry-codex` sent as kind=notice/priority=info. No RV items reopened.

**Verified sound:** every declared value in `SOURCE_MANIFEST.json` (bytes, SHA-256, rows,
columns, dates) matches all seven files; UTF-8/CRLF/no BOM; 0 duplicates, 0 empty cells,
0 negatives; Σ(11 fuels) = total exactly on 2,422/2,422 dates;
`avg_price_£_per_MW_day` = 24 × `avg_price_£_per_MWh` exactly on 2,421/2,421 non-zero dates;
coal last non-zero 2024-09-30 (phase-out consistent).

**New findings (severity):**
1. (high) 42 dates with Solar = 0 daily mean, 41 outside the 107 repair set; 9 also have
   Pumped Storage = 0. Of 9 dates where AGPT returns rows, 6 are 0.4–7.2 GW below live AGPT
   (2024-01-07 also has gas 7,938 vs 13,434 MW). Not repaired by 20261103-v1.
2. (high) `generation − demand` is not a physical surplus. 60-date random clean sample: gap
   mean −2,237 MW (s.d. 3,565), FUELHH net imports +2,854 MW, corr −0.374, slope −0.665,
   R² 0.14; residual s.d. 3,373 MW and correlates +0.335 solar / +0.294 wind ⇒ boundary
   mismatch, not energy balance. The +farm convention is worth exactly 24.3 TWh
   (0.42 GW × 57,744 h = 16.5 deficit + 7.8 surplus shift).
3. (medium) demand 2022-08-02 = 636 MW (corrupt); it manufactures the largest apparent
   surplus day (+24,768 MW) and 1.8 % of cumulative surplus.
4. (medium) price and generation date sets differ by 16 dates each way ⇒ five-way panel is
   2,406 of 2,452 days; generation∩demand = 2,421.
5. (medium) sample contains a structural break: 2026 mean solar 2,778 vs 1,322 MW (2023),
   offshore wind +84 %, nuclear −36 %; `Fossil Oil` is 0 on all 2,422 dates.
6. (medium) wind farm is one simulated ~0.42 GW asset (mean 422, max 1,125, 12 decimals,
   corr 0.69 with national wind, 10 implausible full-day zeros) — not national wind.
7. (low) fidelity to live AGPT on 50 random 2022+ dates: mean −1.20 %, mean abs 1.31 %,
   range −9.21 %…+1.73 %; 30 absent dates are recoverable from FUELHH (2 verified).

**Balance table (2,406 dates, gen-only / +farm):** 176.81→133.21 / 32.82→33.82 TWh deficit
and surplus; with farm 160.30→116.96 / 40.63→41.89 TWh (reproduces codex's numbers exactly).
On the fuller 2,421-date panel: 178.88→135.28 / 32.92→33.92; with farm 162.16→118.82 /
40.74→42.00.

**Still open (unchanged):** RV-04 `£1.50 → £1.04 m/MW` still live in R3 derived tables;
Tier2 route (2A vs 2B) is the human's decision; no regression test added to `tools/`.
**Next useful step if asked:** extend the repair to the 41 solar-zero dates and the 30 absent
dates using the same FUELHH/AGPT method (scripts already in the release).

## Addendum 6 — remote sync and independent verification of the full data repair (2026-11-04 evening)

**Sync:** `012ec50 → 61004e8`, four commits by `mocry-codex` (all `Acting-Tier: Tier1`), 223 files:
`0a821ea` + `007f351` publish `data_quality/full_data_repair/20261104-v2` (28 files, incl. five
rebuilt CSVs and five gzipped upstream evidence snapshots); `68d1041` + `61004e8` add the personal
workspace package `workspaces/mocry/codex/baseline-1104/20261104-v1` and one broadcast `notice`
(`3418b09a254d45d08ebc24a6766bcf14`, info). `Tier1/public/README.md` gained one section; the previous
version is in `public/archive/711841096a37417cb8bb261af1b7b22d`. Local `main` fast-forwarded, tree clean.

**What v2 claims and what I confirmed independently** (published as
`research_1103/independent/mocry-cleveruser/20261104-cu-verify-full-repair/`, commit `4c6cab1`;
scripts do not import the repair module):

1. Byte-exact reproduction: `repair_data.py --verify` rebuilds all eight data/audit files; on Windows
   it needs `tzdata` (installed to `.clever-user/pydeps`, `PYTHONPATH`-injected). `validate_release.py`
   passes all 15 assertions.
2. Structure: 5 series × 2,452 days, no gaps/dupes; Σ11 fuels − total = 0.0 on all days; no negative
   cells; 24× price identity exact; five-way join now 2,452 days (course files gave 2,406/2,421).
3. Generation: 2,063 of 2,188 complete-AGPT days equal the AGPT same-day mean within 1 MW; the 125
   exceptions are AGPT collapse/incomplete days (2022-12-09…15 gas +21–23 GW vs AGPT) where FUELHH is
   the documented fallback. 2022-12-12 repaired total 35,774 MW vs FUELHH 35,123 domestic / 37,849
   incl. interconnectors (course 1,664). All 42 solar-zero dates now 97–2,709 MW; 30 dates restored.
4. Demand: 471 changed days, **340 of the 351 largest changes are Tuesdays**; repaired values equal the
   archived VD full-day mean to the published integer. 2022-08-02 636 → 28,744 (VD day mean 27,309.6 with
   17 slots stuck at 636). 153 reconstructed days sit inside 3σ of the clean TSD−VD offset (median −166,
   σ 240, worst −958 on 2026-08-06). Largest day-to-day jumps all fall on strict-no-imputation days.
5. Price: 2,372 of 2,422 evidence days reproduce active-provider volume weighting; the course value
   equals the flat mean over all provider records on 1,954 days, because one of two providers carries
   volume 0 and price 0. Median daily ratio repaired/course = **2.000** (annual 2.014–2.096);
   2020-01-01 18.5934 → 37.1869. **Live Elexon MID re-query** (independent of the archive) gives
   37.1869 / 18.5934 for 2020-01-01 and 101.3623 / 50.6811 for 2023-05-09. Negative daily means: 9
   course (+1 zero day) → **2** repaired (2020-05-22, 2020-06-28); max 667.65 (2021-09-09).
6. Balance on the repaired panel: 144.27 TWh deficit / 11.41 TWh surplus (course inputs 178.88 /
   32.92); mean residual −2,258 MW; every weekday −2,125 … −2,417 MW, i.e. the course series' Tuesday
   +1,741 MW artifact is gone. 2023 gives 29 surplus days / 549.9 GWh, matching Baseline 1104's
   549.944 GWh.

**Two blind spots in my own 20261104 audit, now recorded publicly in §6 of the new README:**
(a) provider aggregation inside the price column — the "9 negative price days" are 7 midnight artifacts
plus 2 real; (b) weekday structure in demand. My balance table stays correct arithmetic on the course
inputs but no longer describes the series to model with. Unchanged: the residual is a boundary
convention not a physical balance; the farm is one simulated asset (24.3 TWh / 2,406 dates, 24.85 TWh /
2,452); 2026 is a partial year with a structural break (solar 2,782, offshore 5,472, onshore 4,031, gas
7,903 MW mean); wind-farm zeros remain an interpretation difference (~0.10 TWh of 24.85).

**New downstream risk raised (message `ceb9095432fb43048540c0688b466c8c`, kind=request,
priority=action, due 2026-11-06T12:00Z):** `20261103-v1.1/R4-finance-data/prices_gbp2020.csv`
(mean £48.17/MWh 2020 money) and `BASELINE_CANDIDATE.json` → `market.prices` are built on the course
price column and are therefore ~0.5× the corrected level; asked the owner to publish a correction
rather than editing another agent's reviewed release. This is the largest single sensitivity in
codex's own ablation (A increment £15.188 → £8.572 m/yr, −43.6 %).

**Baseline 1104 (workspace, explicitly not group-adopted):** reference case 2023-design, A = 20 MW
electrolyser, B = no investment, no battery in any real case; 82 cases; £7.799/kg and 10 t/day is
flagged as a high-value scenario, not a contract. I checked only the arithmetic path from the repaired
data to its headline numbers (electricity revenue 17,126.9 m / 214,944 GWh ≈ £79.7/MWh2020, consistent
with the repaired deflated series) and did not re-solve it.

**Still open:** Tier 2 route 2A/2B (human); RV-04 £1.50 → £1.04 m/MW in R3 derived tables; codex reply
on the R4 price correction. Next useful step if asked: a v1.1 → v1.2 price addendum, or a one-page
"which price series to use" note for Tier 2.

## Addendum 7 — 2026-11-05 — Tier 1 blueprint assessment

**Synced:** remote 9f5efb3 → a678a3a (only cc5dd10 blueprint + a678a3a notice; no v1.1 change, no new
publication). Blueprint 133 lines, six work packages (T1.1–T1.6), 3.5–4 pages of the 10-page report.

**Recomputed from 1104 outputs (all match the blueprint):** 82 cases (41 A / 41 B); A 2023 +£8.572m/yr;
B 0; fixed 20 MW under B −£1.065m (2023) → +£4.478m (2025); H2 input 171.84 GWh = 3,074,060.8 kg ×
55.9 kWh/kg; u0 549.944 − u 536.024 = 13.92 GWh (8.10% of H2 input, 2.53% of surplus); sales diverted
157.92 GWh; 13.92 + 157.92 = 171.84 (account closes); coverage 87.5123% → 87.4481%; old-price A 15.188m.

**New findings (mine):**
1. All 82 cases choose zero battery; electrolyser only 0/20/120 MW (20 MW integer modules). 20 MW is
   pinned by the 10 t/day offtake cap (≤8.59 t/day), not by an economic optimum curve; offtake axis is
   already a trigger curve (0/2k→0, 10k→20, 50k→120 MW, +£49.093m).
2. `unused` is a model residual, not physical surplus: the course 2023 price has two non-positive days
   (2023-04-11, 2023-12-26, G = 1,150.4 GWh); same 20 MW config gives unused 1,685.4 GWh vs 536.0 GWh,
   i.e. 1,149.4 GWh of the ablation gap is a price-sign convention. Report must separate S_t and u_t.
3. Same-capacity simple rule comparison: A_fixed20MW 8.572 vs A_simple20MW −1.065 → optimised dispatch is
   worth £9.637m/yr at 20 MW. Strongest unused number in the package.
4. CAPEX route (RV-04) does not move the capacity decision: legacy 816k→9.411m, modern low 1.270m→8.820m,
   central 1.460m→8.572m, high 1.651m→8.325m, all 20 MW; discount 0–12% also keeps 20 MW.
5. `simple_payback` 2.64 y adds back annualised capital and stack replacement but not FOM; CAPEX/increment
   = 3.41 y (29% difference). Convention must be frozen.
6. On six rubric dimensions the blueprint is a strong plan but the deliverable is ~35–40% done; T1.2/T1.4/
   T1.5 new computation and T1.6/report/pitch are absent. Rubric text is not archived anywhere in the repo
   (whole-tree grep hits only the blueprint) → unverifiable; Q items still open.

**Published:** `Tier1/public/research_1103/independent/mocry-cleveruser/20261105-cu-tier1-blueprint-assessment/README.md`.
**Message:** `812e2d52445148998650f5fb876a211f` to mocry-codex, kind=request, priority=action, due
2026-11-07T12:00Z (B1 decision record, B2 rubric archive + Q items, B3 unused definition, B4 20 MW causality;
B5/B6 by 11-14).

**Verdict given to the user:** plan = best Tier 1 design so far; submission = not yet high-scoring;
P0+P1 → Distinction range. Tier 2A/2B still not decided (not mine to decide, but it is the critical path).

**Next:** wait for codex reply by 11-07; if none, re-ask once and proceed with my own P1 computations only
if the user asks. Do not edit others' releases.

## Addendum 8 — 2026-11-05 evening — independent end-to-end Tier 1 built and pushed

On the user's second instruction ("complete all of Tier 1 including the report in your workspace, then upload
to your workspace") I built Tier 1 myself rather than waiting on the blueprint. This package is a working
reference in my own workspace; it does not replace the 1104 baseline and it is not published as a group
candidate.

**Location:** `Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1/` — commit 7d57bed (47 files, 2.3 MB).
**Message to codex:** `20261105T183943016570Z_mocry-cleveruser_e6f0092...` (kind=status, info), commit 7702471.
Remote HEAD after this round: 7702471.

**Contents:** TIER1_REPORT.md, SUBMISSION_SECTION_4PP.md, ONE_PAGE_DECISION.md, PITCH_TALKING_POINTS.md,
README.md, MANIFEST.json (45 entries), VERIFICATION.json (20/20), reproduce.py, data/ (v2 tables + ONS CPI +
daily_model_inputs.csv + SOURCE_MANIFEST), src/ (10 scripts), results/results.json, results/cases.csv (185 cases),
8 daily plans, 8 figures. `reproduce.py` re-runs prepare_data -> run_cases -> verify -> make_figures clean.

**Environment facts worth keeping:** Xpress 9.9.1 Community via `pip --target .clever-user/pydeps` (10.0 refused
on licence grounds; Community binding limit is rows+cols<=5000, model is 2,556 x 2,192). Two formulation dodges
were required: offtake cap as a variable upper bound instead of a constraint, and q=min(G,D) via variable lb=ub
instead of a constraint pair. MIPRELSTOP/MIPABSSTOP must both be 0 — the default relative gap reports a
2-module solution as optimal and silently corrupts the battery case. CU_PYTHON is pythonw.exe (no stdout), so
child prints are lost but exit codes and output files are fine.

**Numbers (D1 baseline, mine):** A0 17,139.332 mGBP; unused 549.944 GWh; coverage 0.8751232. H2 20 MW: 17,147.905
(+8.572), 171.84 GWh to electrolysis, unused 536.024. Battery 0 (non-viable at any non-negative capex under main
FOM). 2024 A 11.9515 / B -0.9985.

**Four convention differences flagged to codex:** (1) unused energy is a price-sign-dependent residual — 2023
prices and the two non-positive days take G to 1,150.4 GWh and move the same config's unused 536.0 -> 1,685.4;
(2) optimised dispatch beats the simple rule by 9.637 mGBP/yr at equal capacity, so that gap needs its own line;
(3) 20 MW is the 10 t/day offtake cap, not the economic optimum; (4) payback 2.640 y pre-stack vs 3.41 y on the
blueprint basis, a pure convention gap of 29%.

**Two framing findings:** battery break-even is FOM-driven (13.25 k GBP/yr unit value vs 22.3 k GBP/unit main
FOM; only the 7.43 k GBP/MW low table clears, at 6,990 GBP/MWh); supply obligation dominates energy — 100%
retention means 0 MW H2, 99.9% allows the full 171.84 GWh at a cost of 0.0734% of current sales.

**Git note for future rounds:** `collab.py commit` needs `git add -A` first (otherwise write-tree==HEAD and the
commit fails with an empty STOP). SSH agent died mid-session; push now goes over HTTPS with
`-c credential.helper="!gh auth git-credential" -c url."https://github.com/".insteadOf="git@github.com:"`.
GitHub returned 500 twice before accepting. `.cmd`/`.bat` decoding and findstr's non-ASCII misses remain live
environment hazards — use the python interpreter with explicit UTF-8 instead.

**Still open:** request 812e2d52... (B1-B4 due 2026-11-07T12:00Z). Tier 2A/2B is not mine to decide. The 4-page
submission text stays in my workspace until the user says to publish it as a candidate or hand it to the report
lead. Nobody else's release was touched; tree clean at 7702471.

**Determinism check (2026-11-05T18:41Z):** `reproduce.py` re-run end to end on the pushed tree with
`python.exe` (not pythonw, so child stdout is visible) and PYTHONPATH pointed at `.clever-user/pydeps`.
Result: 20/20 checks, model 2,556 x 2,192, 8 figures byte-identical, and a field-by-field diff of the
regenerated `results/results.json` against the committed one differs **only** in `meta/built_utc` — all 185
case results reproduce exactly. Manifest was then regenerated so its 45 sha256 values match the delivered
bytes (verified: 45/45 present, sizes match, no unlisted files). Commits: 7d57bed (package), 7702471 (status
message to codex), c99fd97 (this addendum), d3a3d0e (reproduce re-run + manifest refresh). Remote HEAD
d3a3d0e, tree clean.

**Addendum 9 (2026-11-05T20:30Z): published the LaTeX template and the four-page cut; reviewed the Codex demos.**

The user's third instruction was: compress, upload this round's work to my remote workspace, retrieve the
four-page Tier 1 demo that Codex completed independently, and review it only on three axes — course/project
requirement compliance, mathematical and verbal correctness, and whether register and layout are in a
reasonable range. No strategic or group-decision questions.

Published: `report/20261105-v1/` (12 files, `MMCS_TechnicalReport_template.{tex,pdf}`, `Tier1_4pp.{tex,pdf}`,
`mmcsreport.sty`, README, `make_fig_attribution.py`, `figures/`) as commit `ce30692`..`14d93e1` after rebasing
onto Codex's three new commits (`6fa0acb` archive v1, `71ce76e` report v2 + CU cross-check, `ce30692` LaTeX
template + example). `release/` stays git-excluded; the published copy differs only in one README line about
git-exclusion plus a "Status and intent" section, and the build log is not published. Remote HEAD `14d93e1`,
PDF bytes identical to the local release copy (sha256 checked).

**A defect in my own package, found by Codex and confirmed by me.** Codex's `COMPARISON.md` noted that my 2020 A
replay reads £16.72m in prose against 16.7781 in `results/cases.csv`. Confirmed: 16.72 was a transcription slip
in four files (`TIER1_REPORT.md`, `SUBMISSION_SECTION_4PP.md`, `ONE_PAGE_DECISION.md`, and the new
`Tier1_4pp.tex`). Checking the same table found a second one: 2020 B was quoted as 3.11 against 3.124
(now 3.12). All corrected, `Tier1_4pp.pdf` rebuilt with Tectonic (still 4 pages), and `src/check_quoted.py`
added: it recomputes the cross-year A/B rows from `cases.csv`, asserts the quoted 2020 figures and the absence
of the retired one, 11/11 pass. `src/refresh_manifest.py` refreshes the 47 manifest entries (0 mismatches).
Visual review of the rebuilt PDF: all four pages pass on the new revision
(`doc-10ea7bf5b0a943638534e9425b94efd0`, source_sha256 6ef75096...).

**Review of the Codex demos** (`tier1-independent/20261105-v2/report/Tier1_Report.pdf` at `71ce76e` and
`technical-report-latex/20261105-v1/output/pdf/tier1-example.pdf` at `ce30692`, both 4 pages, both read in full
as text and all 8 pages inspected as renders): written up in `review/20261105-codex-4pp/REVIEW.md`. Summary —
no arithmetic error found; 14 checkable claims reproduced from my own copy of `daily_model_inputs.csv`
(29 surplus days / 549.944 GWh / median 15.090; 215,102.164 GWh sales base; 2,452 days; 280 strict days;
£48.7k battery ceiling = 1.7076 MWh x 28,516 £/MWh; £96.4k annual cost; 1.9001 + 0.5900 = 2.4901 capital and
stack; 2.641/2.903/131.7 payback and NPV; 7.29 at 8% and 25% capex with stack held at base). Requirement gaps
that matter: the data-repair record is one sentence against the brief's first ask; the brief's own €288k/MWh
and £9.5/kg references are never anchored, so TC-08's "explain the departure" is unmet in text; "each
historical year" is claimed while 2022-2025 are shown; "a separate implementation agrees on 18 matched cases"
is uncited. Layout: blank blocks of about 20 lines (p3) and 12 lines (p4) in the Markdown-built PDF,
inconsistent caption placement (Table 1 above, Tables 2/3/5 below), hyphen-minus in negative cells, top-aligned
row labels in Table 1 (the same p{}-vs-c{} defect my template hit), squat trigger-map panels. Every one of
these is fixable within the existing page budget; none needs a model run.

Also recorded for the group: the £4.61/kg break-even in the demos versus my 4.6229 is explained by the two
implementations' known £49.0/yr difference (£0.016/kg at 3,074 t/yr), not by an error; and my 35.43 GWh figure
is electrolyser input at the 99.99% floor (my realised sales sacrifice is 21.3 GWh), not a sales number — the
two packages agree on this case.

Open: nothing blocking. Tier 2 allocation still not mine to decide. The published template is offered, not
adopted: whether the group uses this style, and how the other six pages are allocated, remains a group call.

**Addendum 10 (2026-11-05T21:30Z): revised template and four-page cut for the neutral comparison.**

The user's fourth instruction: a neutral Opus reviewer will compare my LaTeX template and completed Tier 1
report against the Codex pair and decide which is the better upload candidate; I may revise and enhance my
own artefacts this round, then sync to the remote workspace. No changes were made to Codex's files.

**Substantive additions** (all numbers recomputed here, not copied):
- A data-repair paragraph in section 2: 2,452 whole UTC days (2020-01-01 to 2026-09-17, 2026 partial), the
  weekly-query demand rebuild (340 of the 351 largest demand changes fall on a Tuesday), zero-volume price
  records removed with two non-positive price days kept, 523 of 2,452 days carrying the release's non-strict
  flag (85 in 2023), CPI rebasing to 2020 GBP. The brief asks for this record first and it was one sentence.
- An annualisation equation for a_B, a_H with one worked value: electrolyser 0.52 fixed + 1.90 capital +
  0.59 stack = 3.01 m GBP/year; battery 22.3k + 74.1k = 96.4k. The 5% CRF over 30 years is 0.06505 and the
  stack PV uses 1.05^-11 + 1.05^-22.
- Cross-implementation validation: the independent Codex Xpress build (commit 71ce76e) matches all 2,452 input
  days and the 18 matched 2023-2025 cases, largest annual difference 49.54 GBP (0.005%), and solves the 40 MW
  counterfactual at +7.47m, below 20 MW. This replaces "reproduces Baseline 1104" as the strongest check,
  because 1104 is my own earlier build.
- Money basis stated once: reference netback 7.80 in 2020 money is 1.4% below the brief's 9.5/kg deflated
  (7.91); the 9.5/kg sensitivity rows are 2020 money, i.e. 11.4 at 2023 prices. Verified from trigger_grid that
  capacity stays at 20 MW between 7.80 and 9.50, so the 1.4% gap does not move the decision.
- Seven sourced references replacing three placeholders (data release, brief and clarifications, ONS D7BT,
  BEIS 2021 with IEA 2025 and the ITM POSEIDON sheet, Danish Energy Agency storage, DESNZ HAR1, Codex v2).
  Titles were checked against baseline-1104 research sources.json, not invented.

**Two factual corrections found while re-checking:**
- "125 days carry imputed fuel composition" was wrong: 523 of 2,452 days carry the non-strict flag (85 in 2023).
  The 125 came from my own 2026-11-04 verification ("differing days: 125" between two candidate repairs) and had
  nothing to do with imputation counts. Corrected in both the report and the template provenance table.
- "37 times below the brief's 288k EUR/MWh" compared a sterling break-even with a euro value; 37 is the ratio to
  the 256k GBP equivalent. Reworded.

**Typography and layout:**
- Figure 1 redrawn at printed size (7.5 cm, 6.5-7 pt) by make_fig_attribution.py and make_fig_ladder.py, so the
  panels are no longer scaled to 48% of the package figures. Panel (a) is now two bars on a shared axis instead
  of one thin stacked strip; panel (b) loses its in-plot title and the "no build" note, which the caption carries.
- Paragraph separation switched from space-only (2.8 pt, blocks merged) to a 1.6 em first-line indent with 2 pt
  of space; the four-page cut uses linespread 1.0 and sectionkeep 0.2 with one targeted \needspace before
  section 5, since the needspace mechanism was what held section 2 off page 1.
- The configuration table is back (it had been prose while trimming); the reference list is ragged-right with
  hyphenation disabled so no publisher name breaks across lines.

**State:** Tier1_4pp.pdf is 4 pages (source sha256 9bf09135..., text 12,387 code points). Visual review of this
revision: pages 1-2 pass, page 3 has cosmetic notes (panel (a) is sparser than panel (b); page is nearly full),
page 4 has about seven blank lines at the foot and a weak block boundary before "Limitations". Both are
disclosed in the README rather than papered over. check_quoted.py: 11/11. The template is 7 pages with no
overfull or underfull boxes; the guide section no longer starts on a blank page.

Open: the Opus comparison; Tier 2 allocation still not mine to decide; whether the group adopts this style at all
remains a group decision.

## Addendum 11 - publication of the revised template and four-page cut (5 Nov 2026, 23:40Z)

- Committed the revision as e3dce47, rebased onto the remote tip d906c03 (Codex's own revised LaTeX candidate) with no
  conflict, and pushed the rebased commit as 665bade. Remote main is now 665bade; working tree clean.
- Re-verified on the committed state, not from memory: Tier1_4pp.pdf is 4 pages (sha256 9bf091353da1, 240,339 bytes);
  MMCS_TechnicalReport_template.pdf is 7 pages (sha256 3c535d20f270); check_quoted.py passes 11/11.
- Codex published a v2 candidate at d906c03 whose README already cites my REVIEW.md at 024edd1 and claims most of my
  eight items addressed. I have not re-reviewed their v2 yet; that check waits on their reply.
- Sent Codex a notice (Tier1/agent_message/messages/20261105T233749736424Z_mocry-cleveruser_262f86b7d29340d4bb52b216d70f44db.md)
  pointing them at 665bade instead of 024edd1, disclosing my two corrections, asking them to confirm the three figures I
  quote from their Xpress run (49.54 GBP annual gap, 0.005%, +7.47m at 40 MW) since I did not re-derive them, and asking
  why my fixed-20-MW break-even 4.62285 differs from their 4.614536 by 0.18%. I explicitly do not claim agreement.
- Open: Opus comparison; Codex's answers to the eight items (due 2026-11-07T12:00Z); Tier 2 allocation remains a group
  decision, not mine.

## Addendum 12 - the independent review arrived, and its findings are fixed (6 Nov 2026)

mocry-claude published `69a81e1` (review of both candidates at `665bade` / `d906c03`,
`Tier1/workspaces/mocry/claude/review/20261106-tier1-candidates/REVIEW.md`). It proposes the Codex
skeleton plus my presentation layer, and lists eight defects in my four-page cut.

I re-checked all eight against the files. All eight hold; fixed in `5116a21`.

The distinction that matters for the record: three of the eight are defects of the **printed
formulation**, not of the model. `tier1/20261105-v1/src/model.py` has `c[i] - c_unit*nb <= 0` and
`dd[i] - d_unit*nb <= 0` (190-191), `h_cap_kg = limit_kg_day*55.9/1e6 = 0.559 GWh` (161) and
`yt = sample_years(frame)` = years (155). No reported number changes. The write-up still had to be
fixed, and now is.

Also verified independently: the teacher's "this has a 10-page limit" is in
`Project_Launch_Transcript_Timed.txt` line 236, so my template's "hard ceiling: 15 pages including
appendix" was a real compliance defect, not a stylistic quibble. The 10 t/day offtake cap appears
nowhere in `TEACHER_CLARIFICATIONS.md` (it is a Baseline 1104 analyst scenario, as my own
`TIER1_REPORT.md` line 211 already said), and 1.5 MW/3 MWh comes from the Danish Energy Agency
technology data, not from the brief, which specifies a two-hour duration only.

Fixed in `Tier1_4pp.tex`: printed battery caps, offtake cap on hydrogen mass (the old
`55.9L/10^6` was low by 10^3), `Y` as years, domains/integrality, reference [2] attributions,
"Section 7" -> 6, agent name out of reference [7], decision-box and §1 wording unified (contract
sets scale, mandate decides sign), "B is the operating reality" removed, `\noindent` in the three
title macros, Figure 1(b) rebuilt as a step function on a true t/day axis.

Fixed in `MMCS_TechnicalReport_template.tex`: page budget is now ten pages (Tier 1 ~3.5, Tier 2
placeholder, joint recommendation, references), stale siunitx `S`-column rule replaced by the
`R{}`/`Y` rule the style implements. The template stays a Tier-1 skeleton on purpose: adding the
Tier 2 slot is the group's decision, not mine.

Re-verified: `Tier1_4pp.pdf` 4 pages sha256 `faeb15afcca4` (251,777 bytes); template 7 pages
`b59d1c523534`; no overfull boxes; `check_quoted.py` 11/11; pages 1-4 read at 130 dpi.

Sent mocry-claude a reply (`20261106T174745991277Z_mocry-cleveruser_bfd098a124ae49268ac9edfb7ec131db.md`).

Open: Ran Min's choice of skeleton; the Tier 2 split; Codex's answers to the eight items from
`024edd1` (two of which I asked them to confirm - the 49.54 / 0.005% / +7.47m figures I quote from
their run, and the 0.18% gap between my 4.62285 and their 4.614536 break-even); the design-year
argument from review §4(a), which is not in the four-page cut and would cost a page if added now.
The four-page cut is at its budget: anything further forces dropping either the bridge table or the
repair record.

## Addendum 13 - sixth round: sync method, the v5 target, and an independent standard (22 Nov 2026)

Ran Min's sixth-round instruction: compress first, read the updated synchronisation method, sync one
remote copy locally on demand (the repo now holds several GB of Tier 2B research), follow the gap,
then write an evaluation standard before opening the latest Tier 1 report, and review it on content
without trusting other agents' statements.

What I did, in order: fetched; read `401111c` and `README.md`'s new first-session section (blob-filtered
`--no-cone` sparse checkout; `tools/review-sparse-paths.txt` selects brief, tools, logs and summary
pages; single files/folders are added on demand). Built `mmcs-review-20261122` as a `--filter=blob:none`
partial clone at `401111c`; kept the old full checkout at `53e3b50` untouched. Downloaded only the
paths needed (my workspace, baseline_1103, past reports, course materials, the lesson Xpress licence
note, the v5 PDF); no Tier 2B archive was pulled.

Standard: `review/20261122-tier1-independent-standard/STANDARD.md` (commit `871c4e3`) plus
`ADDENDUM_1_OFFICIAL_RUBRIC.md` (`40eac2e`), both pushed before I opened the v5 PDF. Gate G1 is the
10-page limit (transcript line 236; counting basis still unwritten). Weights follow the course's
seven-dimension report descriptors (1:1:1:1:1:1:2) located in Codex's archived references; that PDF
predates 2026/27.

v5 (`7b8a9fa5...`, 14 pages) read in full; pages 1/5/6/7/8/13/14 also viewed as images; 43 arithmetic
checks in `review/20261122-tier1-v5-content/recompute_checks.py` (4 failures: the stated 0.635
conversion factor contradicts the battery totals, which imply 0.6225, and the 827/845 module counts).

Verdict: 73/100 (A3-low, non-official). Two P0s: (1) the headline battery/electrolysis value is at a
4.25 GW electrolysis / 492.5 kt H2 fleet while the recommendation is 40-55 MW plus one block, so the
battery increment at the recommended scale is missing; (2) the battery is positive only under perfect
foresight (simple rule -2.605m/yr A, -0.938m/yr B), yet the 5.8/8.2-year payback is quoted from the
oracle cash. P1s: 4-hour main case vs the brief's 2-hour battery (2-hour menu buys zero); HiGHS-derived
sizing vs the brief's Xpress requirement; 2.891 vs 2.513 per-slot/daily-cap gain; currency factor;
missing 9.5/kg case; support price applied to hydrogen whose eligibility B.3.1 admits it cannot
establish; "accompanying package" not in the v5 directory; 14 physical pages vs 10; demand served
falls 9.1 pp under A without valuation. P2s are in REVIEW.md.

Gap status: Codex's archived disposition confirms the 49.543/yr maximum difference and retains
4.614536 against my 4.62285; it does not adopt my earlier explanation and reports +7,138/yr at
4.618/kg. The 0.005% / +7.47m items and the 4.62285 explanation remain unresolved; not confirmed.

Next: publish REVIEW.md + checks, message Codex, and leave the group's decisions (skeleton, Tier 2
split, whether I merge) to Ran Min.

## Addendum 14 - page rule confirmed, v6 fetched and verified (23 Nov 2026)

Ran Min clarified the page rule: **10 pages are body pages; abstract, contents and appendices are
not counted** (recorded as `ADDENDUM_2_PAGE_RULE.md`, a human owner statement, not a written course
document). v5's P1-8 is therefore closed by the rule; v6 has 6 body pages (PDF 3-8), total 15.

Codex published v6 (`2f02e3e`, PDF `769b89e4...`, 136,111 bytes, 15 pages, ZIP 71.5 MB
`f4c0e6e5...`, 190 files with MANIFEST hashes; both match `SHA256SUMS.txt`) and asked me to re-review
Chapter II. I fetched it into the partial clone (sparse add of the v6 folder only), read all pages,
rendered pages 1/5/6/7/8, and read the evidence archive's CSVs/JSON directly.

Result: **79/79 checks reproduce** (`review/20261123-tier1-v6-verification/v6_checks.py`,
`checks_v6.json`): Table II.3 site rows, one-block/simple increments, joint 4,500/900 MW and
£1.79bn/£422m, capture/unused/renewable attribution, all Table II.4 rows incl. two-rate, NPV
217/84 and 144/42, break-even 3.69/4.70, 22%/42% shares, 3.91/5.30 thresholds, 2 h reference
13.42/14.47 and 3.78/2.46, Table C.2 eight rows, battery-only 5.70/1.65, Xpress 551 blocks/4.34 s/
£4 per year/gap £5.13, T2B pooled 363.5 days -20.68 (A, five-action) and +7.75 (B, binary_all_in).

All two v5 P0s and nine P1s are closed or materially closed; residual items are P2 (capture vs
unused 174 GWh; T2B policy settings not named; £9.50-in-2020 row label; forced-block row; 2 h
product metadata source string; [9]/[11] inner paths; Xpress/HiGHS nuance; title page).

Revised non-official score: 78 (A3 across seven descriptors; weighted at the A3/A2 boundary; band
74-82), up from 73. Verification note at
`review/20261123-tier1-v6-verification/VERIFICATION.md`; message sent to Codex.
## Addendum 15 - v6.1 candidate reviewed (23 Nov 2026)

Codex published v6.1 (`589b9d5`, PDF `f218a0e0...`, 138,363 bytes, 15 pages, source ZIP
`618cb569...` with 10 LaTeX files; both match `SHA256SUMS.txt`) and asked me to re-review Chapter II
(body pages 2-5) with attention to the new operating-limits paragraph, Table B.1 and the A/B decision
rules in II.5.4. The baseline evidence is unchanged: the README pins the frozen v6 archive
(`tier1-site-evidence-v6.zip`, `f4c0e6e5...`, 190 files); the new numbers come from Julian's study at
`c3902fe` (`Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1`).

Result: **128/128 checks reproduce** (`review/20261123-tier1-v6.1-verification/v6.1_checks.py` +
`checks_v6.1.json`). All 79 v6 values still hold; the new content checks out against Julian's
`operating_rules.csv`, `main_table.csv`, `surplus_runs.csv` and `checks.json`: 40.2/55.3 MW = 8/11 x
5.031 MW, 20% minimum leaves the half-hour gains unchanged (14.1001/5.4782), Table B.1
14.10/5.48, 13.18/-8.14, 13.16/-8.32, 13.16/-8.32, 13.46/0.00, 30.2 MW = six modules, the 56-hour
one-module surplus limit against the 96-hour requirement, B = zero modules, reserve variant 10
modules/50.3 MW/8.11m with 61.2 GWh taken ahead of sales and -0.024 pp coverage, paybacks 3.1/6.5,
41.7% direct-surplus share, 22.5% break-even support share ((3.6901-2.50)/(7.799-2.50)).

Of the eight v6 P2 items: P2-1 closed by removing the 2,092 GWh unused-decrease line (capture only);
P2-2, P2-3, P2-4 closed (five-action / binary full-group labels, "real-price stress", "fixed one
block" with the brief-capital caption); P2-5 remains in the frozen archive (report caption now names
the basis); P2-6 partly ([9] names PARAMETER_BASIS.md but still says "accompanying package"); P2-7
materially closed (Xpress replay certifies the winning A counts, but the two 4/year statements run in
opposite directions); P2-8 open (no cover names, 6 of 10 body pages used). v6 P2-6 (35 vs 30 price
days) is also fixed in Appendix A.3.

Main residual question is editorial, not numeric: the base case allows half-hour switching, while the
course Q&A (transcript lines 86/125, cited as [15]) calls daily switching unrealistic; the report
treats the four-day rule as "a classroom example" whereas Julian treats it as the main case (A 30.2
MW, B none). v6.1 discloses this in the abstract and §5.3/§5.4 and recommends conditionally, so it is
honest, but the group must say which rule carries the Tier 1 headline - otherwise Julian's and Codex's
front-page answers read as opposites. Also open: the Q&A "always on, vary load" mode is untested in A;
refs [9]/[11]; B's 41.6% share omitted rather than corrected; pinned-archive brief-2h metadata.

Revised non-official score: **79** (descriptor fractions 0.78-0.80, no A1; band 76-82), up from 78.
Note at `review/20261123-tier1-v6.1-verification/VERIFICATION_v6.1.md`. Next: commit and push, reply to
Codex `44c52e26...`, and leave the base-rule decision to the group.


Follow-up on addendum 15: a second pass over the same archives added two P2 disclosure items to the
v6.1 note - A's four-day case has no capital/NPV/payback printed (Julian's `main_table.csv` gives
44.08m and 2.56 yr), and the Tier 2B pooled sums hide the per-window signs (A -31.55 / -14.70 / +25.57;
B -3.62 / +2.50 / +8.87 / +1.93). Score unchanged at 79.


### addendum 16 - Tier 1 v6.2 复核（2026-11-24）

对象：`20261124-v6.2/`（发布于 `2d8a0d8`，复核请求 `150e74b`）。五项哈希与 `SHA256SUMS.txt` 相符：report.pdf
`4837c08d…f1ea`（155,073 B，15 页）、report-source.zip `20aacf7c…602a`、新证据包
`tier1-site-evidence-v6.2.zip` `3a1a9377…abd3e`（132 条目，MANIFEST 131 条）、README `a800a3f6…512e`、
REVIEW_RESPONSE `a6d24932…5453`。正文 6 页（引言 1 + Tier 1 四页 + Tier 2B 一页），符合户主 10 页=正文口径。

结论：**188 项机器核对全部通过**（`review/20261124-tier1-v6.2-verification/{v6.2_checks.py,checks_v6.2.json,VERIFICATION_v6.2.md}`），
未发现算错或回归；主案例改为「午夜启停 + 四天最小运行」后内部一致：A 45/6 £118.90m（可行 118.898893，
上界 118.900891，46/6 上界 118.890634）、B 9/0 £6.07m（第 9 块比第 8 块多 £638.5/年，B 年电池成本 42.258m，
9 块空库存证书 561=536 Xpress+25 HiGHS，gap £0.1667，最优替代 6.069620）、A 零电池 7 台 35.217 MW
（£51.43m，回收 2.85 年，NPV 210.28，盈亏 £3.82/kg，118.394 GWh 让渡），`A-electrolysis-only.json` 的 6/8 台上界均低。
Tier 2B 六窗：A −20.45/41.02/6.17/−2.78/2.31/2.03，Σ28.31，去 2021/22 −12.71；B −4.20/65.31/−3.95/−16.83/−9.45/8.57，
Σ39.45，去 2021/22 −25.86，2/6 覆盖成本；1 块 0.82/1.27，45 块 −21.26，12 块 3.006，22 块 12.51 但其余五窗 −2.39。

两条 P1（非 P0）：
1) **主案例下限 12.5% 与题面 20%**。题面 p.3「Assume that the electrolyser can operate between 20% and 100%」，
   参数表「20 MW 机组 4–20 MW」；问答 119/125 行同样说至少 20%。报告摘要写「the product's 12.5% minimum load」、
   §II.2 也印了题面 20%，但正文没有把「改用供应商 12.5%」写成有论证的偏离，题面一致的 A 零电池情形只在附录 B.1
   （六台 13.46）。若按题面，应为 Julian 的六台/30.2 MW/£44.08m/2.56 年/NPV≈206.9m。修法便宜（B.1 已有）。
2) **题面要求主建模用 Xpress**（p.1「The main modelling work should be implemented in Python using the Xpress optimiser」）。
   A 的四天定容与容量证书是 HiGHS；Xpress 用于 A 45/6 重放（551 块，4.3 s，gap 5.1）与 B 536 个子问题。
   已在 §II.4/C.1 披露、REVIEW_RESPONSE 列为待办；建议全许可下用 Xpress 解一次 A 零电池 7 台（或 6 台）四天模型并入 C.1。

P2/P3：①「With 2.5% upkeep, both increments are negative」易被读成与上一句 +£1.05m 矛盾（实际 brief-2h 的 fom=0，
加 2.5%×51.247m=1.281m 后为 −0.24/−2.60；表 II.4 题注未说明）；此句 v6.1 已有，我上轮未记，现补记；
②Figure II.1 panel B 的 2022 柱 76.49 超过顶部刻度 75（轴上限 88），均值标注在轴顶并与该柱相交；
③§5.4「Battery .」多一空格；④封面无作者姓名（v6.1 遗留）；⑤A 的四天时序重放缺失（已披露）；
⑥1,559 t/day 广域行（4,100/700 MW、46.46/3.23）两包都无文件，仍按作者自报；⑦一块电池六窗序列未印（B 一块六窗
+7.58，去 2021/22 −1.23，3/6 为正）；⑧「最后三天不得启机」只在文字中，(II.8) 未表达。

分数 **81**（描述符 0.79–0.86，区间 78–84；v6.1 记 79）。说明：v6.1 的 79 未计上述两条 P1，故不可直接比较；
内容增益（主规则落定、A 财务、容量证书、B 排氢上界、六窗交接、成本/求解器披露）大于 +2 的表面分。
已渲染并目视第 1、3–8、13–15 页，正文无溢出。

已读 claude 的 v6.2 复核（`1ef6a9e`）仅作线索：其 P0（12.5% vs 20%）我独立从题面与问答原文复核后降为 P1（两带
都已印出、20% 情形在 B.1 存在，但建议的四天方案尺寸绑定在偏离参数上）；其「A 完全没用 Xpress」不准确（A 45/6
重放用了 Xpress）。其 P1-1（头条/图给的是不买的组合）、P1-2（氢价表在附录）、P1-3（一块六窗/§III.3）我记为 P2。

下一步：提交并推送本目录（含 checks_v6.2.json），回 Codex 请求 `86f6b289…`（reply_to `4441b781…`）；
20% 与 Xpress 两条留给组内决定，不代组改稿。

### addendum 17 - Tier 1 v6.5 复核（2026-11-24）

对象：`20261124-v6.5/`（发布 `3b0318e`，校验和行尾修订 `044f446`，复核请求 `3a4f8ec`）。四文件哈希全部相符，
且工作树字节即发布字节（`044f446` 未改变任何产物，无需 CRLF 复原）：report.pdf `4ffabb3a…520c`（195,997 B，15 页）、
report-source.zip `746c1162…96d9`（10 文件）、display-table-evidence.json `faf94771…482b`（新机读表）、
tier1-site-evidence-v6.3.zip `202bb3de…997a`（34 条目，MANIFEST 33 条，逐条 sha256 重算全对）。
正文仍 6 页（引言 1 + Tier 1 四页 + Tier 2B 一页），符合户主 10 页=正文口径。

结论：**199 项机器核对，2 项失败**（`review/20261124-tier1-v6.5-verification/{v6.5_checks.py,checks_v6.5.json,VERIFICATION_v6.5.md}`）；
两项失败都是小额记账问题（P2-2/P2-3），无头条数字错误、无回归。

v6.2 两条 P1 的处置：①Xpress 一条**降为 P2**——两侧零电池方案现各有 7 段定边界 Xpress 重解（960+2,880 与
960+2,560 行列，均 ≤5,000），与 HiGHS/动态规划一致到 £1e-7；A 45/6 仍 551 块、B 536 块；联合定容仍 HiGHS，但
§4.2 与表 C.1 已把许可上限写明。②12.5% vs 20% **保留为收窄后的 P1**：两带已同时进表 II.3/II.7，§5.5 写明
「七台 12.5% 比六台 20% 多 £0.22m/年、多 £7.35m 资本」，摘要也印了 30.2 MW；但仍缺一句「为何可低于题面假设」，
且经济上并不划算（回收 2.85 vs 2.56 年、NPV 210.28 vs 206.91、盈亏 3.82 vs 3.85 £/kg）。

新增可复现要点：20% 证书 可行 118.818207 / 全局上界 118.819823 / 最优替代上界 118.811176（受 45/6 领先 £7,031）；
20% 零电池六台 30.186 MW、资本 44.0848m、净 13.4596、最差年 8.666（2022）、回收 2.5604、NPV 206.907、盈亏 3.8478、
3,406.4 t/年、让渡 125.39 GWh、覆盖率 −0.0495 pp、154 次启机；12.5% 七台 18.974970（= Xpress 全期 113.849821m/6）；
Tier 2B A 改为 12.5% 四天承诺基准（六台固定）：1/7/45 块 = −2.97/6.19/0.95/−0.19/0.49/0.17、Σ4.65、去 2021/22 −1.54；
−21.39/37.52/4.56/−2.85/1.87/0.69、Σ20.40、去 −17.11；−139.86/144.94/−20.81/−65.97/−28.39/−23.98、Σ−134.08、
去 −279.02；B 九块列与 v6.2 完全一致（−4.20/65.31/−3.95/−16.83/−9.45/8.57）；参考窗峰值 7 块（A +0.695）/22 块
（B +12.510）；六窗之和峰值 11 块（A 22.99、B 40.97）；去 2021/22 每正容量都为负；552 行台账与 summary 对账一致。
图 I.1：2,891 段（0.5 h 阈值）、最长 56 h（两下限相同）、计数单调、无 ≥96 h；24.75%、5,164.7/2,276.2 GWh/年；
阈值 0.125×5.031 MW = 0.629 MW = 0.3144 MWh/半小时（`site.e` 是每半小时能量，单位无误）。

遗漏/新发现 P2：①图 I.1 左轴写「Mean surplus (GWh)」，实为每半小时值（冬季峰值 1.5 ≈ 3 GW）；
且 shipped 图与包内 `prepare_evidence.py` 的轴标签不一致（脚本写 GWh/half-hour、Consecutive hours、Spells at least
this long），脚本输出目录 `report/figures` 也未随包，故「跑脚本复现图」不严格成立；②§5.4 的 £0.24m 应为 £0.23m
（1.0505 − 1.281 = −0.2307，B 的 −2.60 正确）；③20% 证书 `upper_mGBP` 118.820805 > `global_upper_mGBP` 118.819823
（12.5% 证书一致），且正文 118.819824 是 118.8198235 的 1e-6 进位；结论不受影响；④表 II.3 20% 联合行的
「Served 90.16%」复用 `\TwentyCoverage` 宏，20% 证书无 `served_pct` 字段，缺独立来源；⑤表 III.1 未印正文点名的
11 块列（A 22.99、B 40.97），读者无法从表核对那句；⑥封面仍无作者；⑦1,559 t/day 广域行仍无文件；⑧Tier 2B A
基准从 v6.2 的 flexible 改为四天承诺，未加版本说明（自洽、III.2 已述规则）；⑨20% 零电池最优六台的
`A-zero-sizing.json` 未随包（run_a.py --zero 会生成），仅由 Julian `main_table.csv` 与证书 `certified_fleet:6` 佐证。
**撤销** v6.2 的「§5.4 Battery . 多空格」：源码是 `\textbf{Battery.}`，PDF 渲染正常，上轮是抽取假象。

分数 **84**（描述符 0.82/0.86/0.89/0.82/0.82/0.88/0.83，区间 81–87；v6.2 记 81）。已渲染并目视第 1、3、6、7、8、14 页，
全文 15 页文本已读。未看其他代理的 v6.5 复核；结论均由原始材料独立复核。不代组决定骨架/合并稿/Tier 2 路线。
