# Tier 1 v6.2 review response

## Changes since v6.1

| Issue | v6.2 change |
|---|---|
| Headline operating rule | The 12.5% product load band and the scenario assumptions of midnight switching and four-day runs are stated separately. The commitment equation moves to the Tier 1 body. |
| Configuration and financial recommendation | Four-day joint sizing replaces the flexible headline. The A zero-battery plant is assessed at seven modules, with capital, payback, NPV, fixed-schedule break-even receipt and foregone sales. |
| Julian's service-rule alternative | The 20% minimum-load power reserve appears with the 50.3 MW result, financial gain and service trade-off. It explicitly relaxes strict B. Appendix B retains the 20% and five-day sensitivities. |
| Battery procurement and chronological evidence | Calendar-year results show the weight of the 2022 gains. Chapter III reports same-site one-block results, the A seven-block and B nine-block holdouts and the reference-window size peaks. The A replay uses flexible switching. |
| Brief and external evidence | The two-hour brief reference stays in the body. The flexible contract and UK aggregate-offtake sensitivities remain in the appendix. Two method references support stock linkage and the minimum-run formulation. |
| Solver scope | Distinguishes HiGHS A commitment/sizing from Xpress and HiGHS B replay, the earlier flexible Xpress validation, and the HiGHS daily reference. The flexible A replay improvement is consistently reported as about £4/year. |
| Evidence and presentation | Adds new schedules, per-year reconciliation and certificates, with file hashes. The body has six pages, including four pages for Tier 1. Group 15 remains the cover identifier. |

Points for review include the B hydrogen exclusion argument, the narrow eight-versus-nine block ranking, the fixed-dispatch nature of A's hydrogen receipt threshold, and the boundaries of the chronological comparisons. An all-horizon continuously online case, a reoptimised four-day two-rate hydrogen contract, an A four-day chronological replay and a full-licence Tier 1 Xpress rerun remain open. The evidence README corrects the earlier reference JSON's legacy cost-source label.

[Opus v6.1 review](https://github.com/MocryMin/mmcs-group15-project/blob/aef0372/Tier1/workspaces/mocry/claude/review/20261123-tier1-v6.1-content/REVIEW.md) · [CU v6.1 verification](https://github.com/MocryMin/mmcs-group15-project/blob/35f358f/Tier1/workspaces/mocry/cleveruser/review/20261123-tier1-v6.1-verification/VERIFICATION_v6.1.md)
