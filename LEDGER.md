# Ledger

One entry per experiment. Compress each to ≤10 lines when its phase ends. GPU state is stock unless David says otherwise.

## E0 — Judge recon   status: passed (omnijev-4b low-mem path still running)
Hypothesis: ≥2 open image judges fit 12 GB and do pairwise A/B on 1280×800 fast enough for a loop. Holds.
Setup: 1 fixture pair, 10 timed runs per op, both orders. gpu: stock. Scout notes runs/E0/scout/; table runs/E0/judges.md.
Result: all 6 runs pass, are deterministic and swap-consistent. p50 pairwise / peak VRAM: omnijev-0.8b 266 ms / 5.3 GB; rsi-jev-4b 635 ms / 10.0 GB; imajev-2b 1.09 s / 5.1 GB; imajev-4b 1.65 s / 10.4 GB; imajev-9b nf4 2.56 s / 8.8 GB. omnijev-4b bf16 OOM.
Dropped: Vev, StartLux (CC BY-NC); Simple Jev / open-alt-jev (no vision base that fits); Saina Omni (not found).
Decision / next: top 2 = omnijev-0.8b (train judge) + imajev-9b nf4 (held-out judge); rsi-jev-4b also carried into E1, since it's cheap. Taste, calibration and position bias are untested until E1.
Env note: rsi-jev pins transformers 5.17 → own .venv-rsijev; main .venv uses 5.22.1.
Cost note: ~2 h wall, mostly downloads (~45 GB). No paid API.

## E1 — Does the judge have taste?   status: planned
## E2 — The design loop   status: planned
## E3 — Unlock as a measured variable   status: planned (waits for David's unlock)
## E4 — Weight-space probe   status: planned (optional, ask before API spend)
