# Tier1 reviewed research release 20261103 v1

Published by Ran Min's registered agent `mocry-codex` on 3 November 2026. Status: **controller-reviewed research and recommended parameters, open for group review**. This release does not replace the agreed/proposed model by implication. The original [Baseline 1103](https://github.com/MocryMin/mmcs-group15-project/blob/64d2a9b697a0b80af4c3e062dea8cc7f5fca2ff4/Tier1/public/baseline_1103/BASELINE_1103.md) remains its source model family.

## Start here

|File|Purpose|
|---|---|
|[Research synthesis in Chinese](RESEARCH_SYNTHESIS.md)|Findings, controller dispositions, modelling consequences and closure criteria|
|[English synopsis](EXECUTIVE_SUMMARY_EN.md)|Readable account of the same main conclusions|
|[Recommended parameter package](BASELINE_CANDIDATE.json)|Typed values, units, scenario branches, assumptions and remaining conditions|
|[Review decisions](control/REVIEW_DECISIONS.json)|20 accept/reject/conditional/defer decisions|
|[Market](R1-market/REPORT.md), [battery](R2-battery/REPORT.md), [electrolyser and H2](R3-hydrogen/REPORT.md), [data and finance](R4-finance-data/REPORT.md)|Four full topic reports with parameter/source catalogues|
|[Release manifest](RELEASE_MANIFEST.json) and [release validation](RELEASE_VALIDATION.json)|Version, provenance, content hashes and public-copy checks|

The original first passes are preserved under each worker's `FIRST_PASS` directory as path-normalised public copies. Their original local-byte hashes and release-copy hashes are distinguished in the manifest. Later cross-reviews and the IEA follow-up do not rewrite those original local first passes.

## Decisions that matter

- The DEA battery maintenance source has a twofold formula/unit conflict. Keep both cases; the controller proposes the total-CAPEX2.9% interpretation as the main case.
- IEA2025's actual2024 outside-China installed-cost range replaces the old UK proxy as the modern electrolyser CAPEX reference. Keep the source's rawUSD, declared reporting assumptions and legacy sensitivity.
- Do not double-count PCS/EPC, inclusive maintenance, stack replacement/reserves, or supported hydrogen payments. Actual H2offtake, price/quality terms and support eligibility remain scenario conditions.
- Keep negative electricity prices, preserve state chronology and use a common currency/price-year/horizon across A0/A1/B0/B1. No new optimisation result is claimed by this release.

## Version and source policy

Version path: `Tier1/public/research_1103/controller/mocry-codex/20261103-v1`. Treat this v1 directory as a release snapshot. Corrections should add a v2 or a separately recorded correction; do not silently replace v1 files. Existing public navigation updates are archived and logged through the collaboration helper. Other members' workspaces are untouched.

The five supplied CSVs, brief and complete lecture transcripts already exist at the repository root. External source URLs, read-depth and page/cell locators accompany the research. External full webpages, browser response/base64 files and third-party PDFs/XLSX binaries are retained by the controller and **not redistributed here**. Public copies remove machine-specific absolute paths; these transformations do not turn a modelling assumption into an observed fact.

The `control/RUN.json` and `control/VALIDATION.json` describe the completed research stage before publication; their no-push or local-only statements are historical stage metadata. This README and release manifest describe publication. Chat-only teammates receive separate self-contained Chinese/English files; they need no Git or agent registration to contribute.

All members/agents may challenge sources, units, gap definitions, assumptions or parameters. Publish independently under a unique path, reference this version or content hash, and send a new message. Publication and silence are not group agreement.
