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

## E2 — The design loop   status: rounds 0-1 done, audited; round 2 on hold (decision)
- Setup: gpu stock; coder Qwen2.5-Coder-7B-Instruct (Apache-2.0), vLLM AWQ gen, 500 train briefs x 4 samples; pairs kept if omnijev-0.8b AND rsi-jev-4b agree at order-averaged conf >= 0.7; DPO QLoRA r16 beta 0.1 lr 5e-5 1 epoch, ref = base, seed 0. Eval: 100 held-out briefs, 1 sample each, judges omnijev-0.8b, imajev-9b (never used in training), blind Opus on 50.
- Bug history: lr 5e-6 run + two more runs were void: chunked resume reloaded TRL's zero ref/ adapter, so LoRA reset every chunk (fixed 2026-11-04, lora_B norm now asserted; old dirs *.INVALID_resume_bug). omnijev-only pairs were dropped after David's labels flagged it as weakest.
- Round 0 (1041 pairs/371 briefs, 60 steps, 2.3 h): win vs base imajev-9b 0.708 [0.62,0.80] (LC 0.72), Opus 0.68 [0.54,0.80], omnijev 0.65. 0/100 pages identical to base.
- Round 1 (from r0; only 302/2900 pairs confident, 18 steps): imajev-9b 0.926 [0.87,0.97] (LC 0.88), Opus 0.78 [0.66,0.88] (conf n=21: 0.90), omnijev 0.85.
- Audits (runs/E2/audit/r0_cons, r1): gains are mostly fixed base failures (full-viewport hero 23% -> 3%, rainbow gradients, broken images), content not stripped (r1 words +22%), no fake trust/praise or brief copying. But palette/template collapse: #6a11cb->#2575fc gradient 28% -> 34% -> 63% of pages, "Welcome to X" 67 -> 78 -> 87%, within-brief visual diversity down (0.271 -> 0.220). Template pages win 97% vs 86% without it (~11 pts of r1's win). Layout and text diversity across briefs unchanged.
- Limits: 1 seed, 1 sample/brief, viewport-only judging; small judges gain more than Opus (+22 vs +10 pts), consistent with a judge-pleasing style.
- Next (pending David): round 2 with a diversity guard, or stop at r1 and firm up (more samples/brief, 2nd seed, final auditor pass) for the writeup.

## E3 — Unlock as a measured variable   status: planned (waits for David's unlock)
## E4 — Weight-space probe   status: planned (optional, ask before API spend)
