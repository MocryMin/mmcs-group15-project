# Tier 2B research archive · 22 November 2026

This is Ran Min's working evidence after publication `63a78bd`. It includes source code, intermediate and negative results, validation selections, per-window cash, execution traces, model weights, prediction arrays and derived input panels. The reports inside preserve the information and dispatch conventions of each experiment.

- The prior-slot benchmark locks a half-hour request before current outcomes are known. B applies supply priority to generation and committed battery output, with actual conditions limiting execution.
- The A price studies cover swapped-period validation, day-ahead blending, Huber residuals, portfolio cash floors and decision-loss penalties. The action studies cover fixed 50 MWh with idle, four or five discrete requests and continuous quantities.
- The B studies cover historical supply-gap classification, threshold-aware regression, fixed requests, richer action sets and attribution of electricity and hydrogen cash.
- The direct-policy studies retain all trained seeds from the categorical policy and expected-cash experiments, including the Transformer width grid and the matched three-action A/B test.
- The five-minute studies retain publication-time data processing, oracle diagnostics, direct and adapter forecasts, and matched battery replays. The older oracle and latest strict B replay have distinct commitment rules.

## Download and restore selected material

The initial lightweight checkout includes this summary. When you need an experiment, first select this folder's `MANIFEST.json` and `restore.py`. The manifest lists the original paths and SHA-256 checksums in each ZIP group. Find the group that contains the files you want and select its folder under `volumes/`. For example, selecting `volumes/arrays-02/` downloads that entire ZIP group (59 MiB).

From this directory, use `python restore.py --verify-only --group arrays-02.zip` to verify that group, then `python restore.py path-to-experiment-copy --group arrays-02.zip` to extract it. Repeat `--group` for multiple groups. Each selected group needs every part listed for it. With no group argument, those commands process the complete archive. The script requires Python 3.11 or later. Existing files with different contents cause extraction to stop.

This archive supplements the preceding Tier 1 input archives and the frozen 19 November forecast release. Python environments, local browser-session artifacts and compiled Python caches are omitted.
