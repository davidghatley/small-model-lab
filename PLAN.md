# Plan

Goal: one publishable before/after result on the 3060: a small coder model improved by DPO on a local vision judge's pairwise taste, with a reward-hacking check.
Full queue and acceptance criteria: docs/brief.md. Status lives in LEDGER.md.

## Phases
- [ ] E0 judge recon → top-2 judges (runs/E0/judges.md)
- [ ] E1 judge taste validation (gate: ≥75% agreement on high-confidence pairs)
- [ ] E2 design loop, 2–3 DPO rounds, held-out eval under 3 judges
- [ ] E3 stock vs unlocked (after David applies the unlock)
- [ ] E4 weight-space probe (optional)

## Open questions
- E1/E2 frontier-model labels: which model and API, and what budget? (Ask David before any paid API call.)
- E1: David hand-checks 30 reference labels. Needs a small review page when we get there.

## Decisions
- 2026-11-03: Project created as `small-model-lab`, separate from 3060-recipes (that one is for models too big for the GPU).
- 2026-11-03: Download threshold is 10 GB (house rule), not the brief's 20 GB.
- 2026-11-03: Weights go in /mnt/models/llm/<name>/ (66 GB free today).
- 2026-11-03: David approved the imajev-9b download (19.3 GB, over the 10 GB rule). It runs in 4-bit NF4 because bf16 won't fit.
- 2026-11-03: David: use the other drives freely. Big weights now go to /mnt/work/models (imajev-9b first).
