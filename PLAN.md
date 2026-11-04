# Plan

Goal: one publishable before/after result on the 3060: a small coder model improved by DPO on a local vision judge's pairwise taste, with a reward-hacking check.
Full queue and acceptance criteria: docs/brief.md. Status lives in LEDGER.md.

## Phases
- [x] E0 judge recon → top-2 judges (runs/E0/judges.md)
- [x] E1 judge taste validation (conditional pass) (gate: ≥75% agreement on high-confidence pairs)
- [ ] E2 design loop, 2–3 DPO rounds, held-out eval under 3 judges
- [ ] E3 stock vs unlocked (after David applies the unlock)
- [ ] E4 weight-space probe (optional)

## Open questions
- E1/E2 frontier-model labels: which model and API, and what budget? (Ask David before any paid API call.)
- E1: David hand-checks 30 reference labels. Needs a small review page when we get there.

## Decisions
- 2026-11-03: Project created as `small-model-lab`, separate from 3060-recipes (that one is for models too big for the GPU).
- 2026-11-03: No download size limit (David dropped the 10 GB rule the same day).
- 2026-11-03: Weights go in /mnt/models/llm/<name>/ (66 GB free today).
- 2026-11-03: David approved the imajev-9b download (19.3 GB, over the 10 GB rule). It runs in 4-bit NF4 because bf16 won't fit.
- 2026-11-03: David: use the other drives freely. Big weights now go to /mnt/work/models (imajev-9b first).
- 2026-11-03: E0 picks: omnijev-0.8b (training judge), imajev-9b nf4 (held-out judge), rsi-jev-4b also scored in E1. Three judges go to E1, not two, because one fixture pair can't rank taste.
- 2026-11-03: E1 frontier work (300 page pairs, 100 reference labels) is done by Claude Code subagents, not a paid API (David). A scout picks the local coder (David).
- 2026-11-03: Coder = Qwen2.5-Coder-7B-Instruct (Apache-2.0, ungated), QLoRA via Unsloth. Not Qwen3.5-9B: Unsloth advises against QLoRA on Qwen3.5 and bf16 LoRA at 9B needs 22 GB (https://unsloth.ai/docs/models/qwen3.5/fine-tune). Not Mellum 2.1: MoE, not in Unsloth's catalog. Backup: Qwen3.5-2B or 4B bf16 LoRA if 7B DPO runs out of memory.
- 2026-11-03: Coder serving = vLLM 0.33 + official Qwen2.5-Coder-7B-Instruct-AWQ in .venv-vllm (fp8 left no KV room, and fp8 KV needs nvcc). About 720–900 tok/s at 64 concurrent requests, ~1.3k tokens/page, so 2000 pages take ~1 h. E2 note: samples come from the AWQ model while DPO trains a bf16/4-bit LoRA. Serve the trained LoRA on the AWQ base in vLLM (or re-quantize) and log the mismatch.
- 2026-11-03: E1 small_model pairs are all coder-vs-coder (s0 vs s1, same brief), since that's exactly what the judge compares in the E2 loop. Reference labels: 60 small_model + 40 hard + 20 graded. The graded 20 check the labeler against by-construction labels.
- 2026-11-03: E1 conditional pass. E2 keeps judge pairs at order-averaged confidence ≥0.7, not 0.8: audited accuracy is the same within CI (86% vs 88%) and coverage doubles (47% vs 27%). 0.8 is run as an ablation if time allows.
- 2026-11-03: E2 tooling built (scripts/e2_*.py, smoke runs/E2/_smoke). LoRA from Unsloth bnb-4bit DPO loads directly on the AWQ base in vLLM (--enable-lora), so no merge/requantize. Round N samples from the round N-1 adapter; DPO reference stays the base (adapter disabled), a known deviation for rounds >= 1.
- 2026-11-03: E2 DPO reference model = base with the adapter disabled in every round (more conservative than using the round-k policy as reference). Round 0 = first training round, sampling from base.
