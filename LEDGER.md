# Ledger

One entry per experiment. Compress each to ≤10 lines when its phase ends. GPU state is stock unless David says otherwise.

## E0 — Judge recon   status: passed
Hypothesis: ≥2 open image judges fit 12 GB and do pairwise A/B on 1280×800 fast enough for a loop. Holds.
Setup: 1 fixture pair, 10 timed runs per op, both orders. gpu: stock. Scout notes runs/E0/scout/; table runs/E0/judges.md.
Result: all 6 runs pass, are deterministic and swap-consistent. p50 pairwise / peak VRAM: omnijev-0.8b 266 ms / 5.3 GB; rsi-jev-4b 635 ms / 10.0 GB; imajev-2b 1.09 s / 5.1 GB; imajev-4b 1.65 s / 10.4 GB; imajev-9b nf4 2.56 s / 8.8 GB; omnijev-4b GGUF Q8 410 ms / 6.6 GB (bf16 OOM).
Dropped: Vev, StartLux (CC BY-NC); Simple Jev / open-alt-jev (no vision base that fits); Saina Omni (not found).
Decision / next: top 2 = omnijev-0.8b (train judge) + imajev-9b nf4 (held-out judge); rsi-jev-4b and omnijev-4b Q8 also carried into E1, since they're cheap. Taste, calibration and position bias are untested until E1.
Env note: rsi-jev pins transformers 5.17 → own .venv-rsijev; main .venv uses 5.22.1.
Cost note: ~2 h wall, mostly downloads (~45 GB). No paid API.

## E1 — Does the judge have taste?   status: running
Hypothesis: at least one fast local judge agrees ≥75% with frontier reference labels on its high-confidence pairs, with low position bias.
Setup (planned): 300 pairs. ~200 frontier strong-vs-flawed (obvious/moderate/subtle flaws) + hard strong-vs-strong, written by Claude subagents (David 2026-11-03: no paid API); ~100 small-model pairs from the coder the scout picks. 100-pair reference labels from a blind Claude labeler on screenshots; David hand-checks 30. Judges: omnijev-0.8b, omnijev-4b Q8, rsi-jev-4b, imajev-9b nf4, both orders. Brief splits are fixed up front: briefs/e1 (200), e2_train (500), e2_eval (100, held out). gpu: stock.
Result: (pending)
## E2 — The design loop   status: planned
## E3 — Unlock as a measured variable   status: planned (waits for David's unlock)
## E4 — Weight-space probe   status: planned (optional, ask before API spend)
