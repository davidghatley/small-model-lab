# E0 — Judge recon

RTX 3060 12 GB, gpu: **stock**, 2026-11-03. Raw results are in `runs/E0/bench/<judge>/results.json`, and the commands are in `scripts/README.md`.
Test: one fixture pair at 1280×800, a clean landing page (A) and a deliberately flawed one (B), in `runs/E0/fixtures/`. Each op got 1 warmup and 10 timed runs. "Pairwise" means both images in one call, run in both orders.

| Judge | License (gated?) | Quant | Peak VRAM (nvidia-smi) | p50 single | p50 pairwise | Pairwise works | P(clean better), A first / B first | P(good) clean / flawed | Calibrated probs? |
|---|---|---|---|---|---|---|---|---|---|
| **omnijev-0.8b** (OneJev 1.6) | Apache-2.0 (no) | bf16 | 5.3 GB | **146 ms** | **266 ms** | yes, swap-consistent | 0.953 / 0.995 | 0.804 / 0.003 | probs yes; calibration not documented |
| **rsi-jev-4b** (v6.1-VL) | Apache-2.0 weights, some NC image training data (no) | bf16 | 10.0 GB | 690 ms | 635 ms | yes, swap-consistent | 0.992 / 0.994 | 0.936 / 0.010 | probs yes; calibration not documented |
| **imajev-9b** | Apache-2.0 (no) | nf4 | 8.8 GB | 2787 ms | 2557 ms | yes, swap-consistent | 0.957 / 0.955 | 0.970 / 0.093 | self-reported (`calibration_version` per answer) |
| imajev-4b | Apache-2.0 (no) | bf16 | 10.4 GB | 1747 ms | 1652 ms | yes, swap-consistent | 0.996 / 0.979 | 0.939 / 0.061 | self-reported |
| imajev-2b | Apache-2.0 (no) | bf16 | 5.1 GB | 1155 ms | 1089 ms | yes, swap-consistent | 0.934 / 0.901 | 0.803 / 0.019 | self-reported |
| imajev-2b | Apache-2.0 (no) | nf4 | 2.6 GB | 1072 ms | 1003 ms | yes, swap-consistent | 0.917 / 0.891 | 0.827 / 0.041 | self-reported |
| omnijev-4b | Apache-2.0 (no) | bf16 | OOM on load | — | — | — | — | — | GGUF/low-mem path in progress |
| Vev | CC BY-NC 4.0 | — | not run | | | | | | non-commercial |
| StartLux-Decision | CC BY-NC 4.0 | — | not run | | | | | | non-commercial |
| Simple Jev / open-alternative-jev | Apache-2.0 code | — | not run | | | | | | 27B+ bases, no vision documented |
| Saina Omni | — | — | not found | | | | | | |
| Jev 1.14 (hosted) | commercial API | — | reference only | | | | | | image input experimental |

Every run was deterministic across all 10 repeats. NF4 moved imajev-2b's probabilities by ≤0.024 and halved its VRAM.

## What this does and doesn't show
- One easy pair proves the plumbing: every judge loads, compares two images and returns probabilities. It does **not** show taste, calibration or position bias, since every judge gets this pair right. Those are E1's job (300 pairs, swapped orders).
- Position gap on this pair (|P A-first − P B-first|) ranges from 0.002 (rsi-jev, imajev-9b) to 0.043 (omnijev-0.8b). It's a hint only.
- Cost of one E2 round (500 briefs × 4 samples = 3000 pairwise comparisons per round, ×2 for swap): omnijev-0.8b about 27 min, rsi-jev-4b about 64 min, imajev-9b about 4.3 h.

## Pick
- **Top 2: omnijev-0.8b** (training-judge candidate: 5–10× faster than the rest, so the DPO loop is cheap) and **imajev-9b nf4** (held-out judge candidate: a different model family, the strongest single-image separation, and slow is fine for 100 eval briefs).
- **rsi-jev-4b** also goes into E1, because scoring with it is cheap. If it beats omnijev on agreement, it becomes the training judge. Note its non-commercial training-data caveat in any writeup.
- This deviates from the brief's "top 2": three judges go into E1, because the ranking can't be made on one fixture pair.
