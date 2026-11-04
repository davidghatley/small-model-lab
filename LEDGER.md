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

## E1 — Does the judge have taste?   status: passed (David's hand check done 2026-11-04)
Setup: 300 pairs at 1280×800 (150 frontier strong-vs-CSS-flawed, 50 strong-vs-strong, 100 base-coder s0-vs-s1), runs/E1/pairs, QA runs/E1/pairs_qa.md. 120 blind Opus reference labels (labeler 20/20 on graded). 4 judges × both orders. gpu: stock.
Result (audited, runs/E1/audit/audit.md): on coder pairs vs reference, omnijev-0.8b 73% [63–83] overall, 86% [71–96] at conf ≥0.7 (47% coverage), 88% at ≥0.8 (n=16). imajev-9b 67% overall, 89% at ≥0.7 (30% coverage). Planted flaws: imajev-9b 95%, omnijev-4b 90%, rsi 77%, 0.8b 69% (subtle ~chance for 0.8b/rsi). Flip on A/B swap 30–58% → always order-average. Trivial baselines ≤63%. ECE not meaningful at this n.
Gate: the coded gate pooled sources and reported PASS. On coder pairs only, 0.8b's lower CI bound is 0.71 (borderline); 4b/9b n too small.
Decision: training judge = omnijev-0.8b, order-averaged, keep pairs at conf ≥0.7 (not the brief's 0.8: accuracy is the same within CI and coverage doubles; 0.8 is the ablation). Held-out judges = imajev-9b (confident subset) + Opus on 50 eval briefs. Limits: flaws are mostly palette/type-scale CSS changes; hard pairs ≈ chance for everyone.
David (30 pairs, runs/E1/labels/david_analysis.md): 7 ties (6 of 15 coder pairs "both bad"). Non-tie agreement: planted/author truth 14/14, reference 20/23 (12/13 on his clear picks) → reference labels validated. Judges: omnijev-0.8b 16/23 (6/13 on his clear picks), omnijev-4b 18/23, rsi-jev 19/23 (conf≥0.7: 9/10), imajev-9b 19/23 (conf≥0.7: 7/7). n tiny; flags 0.8b as the weakest judge on human taste, and judges were confident on pairs David called both bad.
Cost note: ~20 Sonnet page-writing agents + 4 Opus labelers (plan usage, no API); GPU ≈ 2.5 h.

## E2 — The design loop   status: running (round 0 retrain)
- Setup: gpu stock; coder Qwen2.5-Coder-7B-Instruct (Apache-2.0), vLLM AWQ gen, judge omnijev-0.8b order-averaged, keep conf >= 0.7, DPO QLoRA r16 beta 0.1, ref = base, seed 0.
- Round 0 (2026-11-04, 4.5 h): 1968/2000 clean samples, 2906 pairs scored, 1233 kept from 402 briefs. No length bias in kept pairs (chosen longer 51.5%, mean diff -4.6 tok).
- Round 0 DPO at lr 5e-6: 78 steps, 2.9 h, peak 8.0 GiB. Did not learn: loss 0.693 -> 0.696 (last quarter), reward acc 0.43, margin ~0. Adapter kept at runs/E2/round0/train/ but treated as a null result.
- Next: retrain round 0 at lr 5e-5 with a brief-level held-out pair split to measure preference accuracy on unseen briefs.
## E3 — Unlock as a measured variable   status: planned (waits for David's unlock)
## E4 — Weight-space probe   status: planned (optional, ask before API spend)
