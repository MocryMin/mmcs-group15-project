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
