# Ledger

One entry per experiment. Compress each to ≤10 lines when its phase ends. GPU state is stock unless David says otherwise.

## E0 — Judge recon   status: running
Hypothesis: at least two open, image-capable System One judges fit in 12 GB and answer pairwise "A or B" on a 1280×800 screenshot fast enough for a training loop.
Setup: candidates from docs/brief.md (imajev, Vev, Saina Omni, OneJev, RSI-Jev v6.1-VL, StartLux-Decision, Simple Jev / open-alternative-jev; Jev 1.14 reference only). gpu: stock.
Scout (haiku, runs/E0/scout/candidates_{a,b}.md, unverified in places): shortlist imajev 2B/4B (Apache-2.0, pairwise, probs), OmniJev 0.8B/4B (Apache-2.0, GGUF), RSI-Jev 4B (Apache-2.0 weights, some NC training data). Dropped: Vev, StartLux (CC BY-NC), Simple Jev / open-alt-jev (27B+ bases, no vision documented), Saina Omni (not found), 27B sizes (don't fit). imajev 9B (19.3 GB) approved by David 2026-11-03; benchmarking in 4-bit NF4.
Result: (pending) builder harness scripts/e0_bench.py → runner → runs/E0/judges.md
Decision / next:
Cost note:

## E1 — Does the judge have taste?   status: planned
## E2 — The design loop   status: planned
## E3 — Unlock as a measured variable   status: planned (waits for David's unlock)
## E4 — Weight-space probe   status: planned (optional, ask before API spend)
