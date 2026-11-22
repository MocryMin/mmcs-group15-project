# Tier 2B research archive · 22 November 2026

This is Ran Min's working evidence after publication `63a78bd`. It includes source code, intermediate and negative results, validation selections, per-window cash, execution traces, model weights, prediction arrays and derived input panels. The reports inside preserve the information and dispatch conventions of each experiment.

- The prior-slot benchmark locks a half-hour request before current outcomes are known. B applies supply priority to generation and committed battery output, with actual conditions limiting execution.
- The A price studies cover swapped-period validation, day-ahead blending, Huber residuals, portfolio cash floors and decision-loss penalties. The action studies cover fixed 50 MWh with idle, four or five discrete requests and continuous quantities.
- The B studies cover historical supply-gap classification, threshold-aware regression, fixed requests, richer action sets and attribution of electricity and hydrogen cash.
- The direct-policy studies retain all trained seeds from the categorical policy and expected-cash experiments, including the Transformer width grid and the matched three-action A/B test.
- The five-minute studies retain publication-time data processing, oracle diagnostics, direct and adapter forecasts, and matched battery replays. The older oracle and latest strict B replay have distinct commitment rules.

`MANIFEST.json` maps every original project-relative path to its byte count and SHA-256, and orders the parts of each ZIP. All parts belong under `volumes/`. From this directory use `python restore.py --verify-only` to verify delivery, then `python restore.py path-to-experiment-copy` to extract it with the original paths. The script requires Python 3.11 or later. Existing files with different contents cause extraction to stop. Large checkpoints and arrays are stored in volume parts and reconstruct byte for byte. This archive supplements the preceding Tier 1 input archives and the frozen 19 November forecast release. Python environments, local browser-session artifacts and compiled Python caches are omitted.
