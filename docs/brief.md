# Small-Model Lab — Orchestration Brief

(David's original brief, pasted 2026-11-03. Kept as written. The working rules are in `AGENTS.md`.)

## Mission

Run cheap, reproducible experiments on small models that fit an **RTX 3060 (12 GB VRAM) + 64 GB RAM** Linux box, aimed at one publishable, before/after result. The first target is the **design loop**: a small coder model writes HTML, a fast local "System One" vision judge scores the rendered page, and those judgments fine-tune the coder.

## Roles and model routing

| Role | Who | Model | Does |
|---|---|---|---|
| Orchestrator / evaluator | Main session | Opus (or your strongest) | Plans, assigns, checks results against acceptance criteria, keeps the ledger, decides next step. Never does bulk work itself. |
| `scout` | subagent | haiku | Web/HF/GitHub lookups, license checks, reading READMEs. |
| `runner` | subagent | haiku | Runs scripts, benchmarks, training jobs; tails logs; reports numbers. |
| `builder` | subagent | sonnet | Writes and fixes code: harnesses, renderers, training configs. |
| `auditor` | subagent | sonnet | Independent check of a result it did not produce (reruns, spot-checks, looks for judge-gaming or leakage). |

Default to the cheapest model that can do the task. Escalate a subagent to a stronger model only after one failed attempt, and record that in the ledger.

## Context and compression rules

1. **Files are memory, not transcripts.** Subagents write full output to `runs/<exp>/<task>/` and return only a report of **≤150 words**: status, key numbers, file paths, blockers.
2. **One task per subagent, fresh context.** Give each subagent a self-contained brief: goal, inputs (paths), exact acceptance criteria, output paths, and the report format. No conversation history.
3. **The orchestrator reads reports and `LEDGER.md`,** and opens raw files only when a number looks wrong.
4. **Compress at phase boundaries.** When an experiment phase ends, the orchestrator rewrites that experiment's ledger entry into ≤10 lines (what was tried, numbers, decision) and stops carrying the details.
5. **Keep work in the sharp part of the window.** If a subagent's task would need more than ~40k tokens of reading, split it, or have a `scout` pre-summarize the material to a file first.
6. **Subagents never spawn subagents.**

## Performer / evaluator loop

For every task:

1. The orchestrator writes the brief, including **acceptance criteria that can be checked** (e.g. "script exits 0, writes `scores.jsonl` with ≥200 rows, judge accuracy reported").
2. The performer subagent does the work and returns its report.
3. The orchestrator checks the report against the criteria:
   - **Pass** → log it in the ledger and move on.
   - **Fail** → send one corrective brief stating exactly what failed. After a second failure, escalate the model or re-scope the task, and log why.
4. Any result that would go into a writeup gets an **`auditor`** pass before it counts.

## Ledger

Keep `LEDGER.md` at the root. One entry per experiment:

```
## E<n> — <name>   status: planned | running | passed | failed | parked
Hypothesis:
Setup: model(s), quant, data size, hardware state (stock/unlocked)
Result: key numbers with file paths
Decision / next:
Cost note: wall time, API tokens if any
```

## Hard rules

- **Do not install or run any GPU unlock** (kernel module or UEFI). David does that manually. Just record in every run's setup line whether the GPU is stock or unlocked.
- Ask before downloads over 20 GB, or anything that sends data to a paid API.
- Check every model's license before using it, and record it. Some judges (e.g. Vev weights) are **non-commercial only**.
- Fix seeds, and save the exact configs and commands for every result.
- Keep held-out sets truly held out: no training on eval prompts, ever.

---

## Experiment queue

Run these in order. Each one gates the next.

### E0 — Judge recon (scout, then runner)

Find which open, image-capable System One judges run on this box, and how fast. Candidates:

- **imajev**: photo + state + typed questions; 2B/4B/9B; Jev-compatible API.
- **Vev**: vision-capable Jev implementation from Qwen3.5 4B/9B; non-commercial weights.
- **Saina Omni**: 0.8B; adds images and short audio; Jev-compatible server.
- **OneJev**: multimodal decisions about screens, photos, video and text.
- **RSI-Jev v6.1-VL** (4B/27B) and **StartLux-Decision** (0.8B–27B, reads images).
- **Simple Jev**, or **open-alternative-jev**: wraps any HF model (including vision models) for Jev-style output. This is the fallback if nothing else fits.
- Reference only: hosted **Jev 1.14**. Image input is experimental there, and TypeSafe doesn't recommend it for production.

Accept when: a table in `runs/E0/judges.md` gives, for each candidate, license, VRAM at the chosen quant, p50 latency on one 1280×800 screenshot, whether pairwise ("which is better, A or B") works, and whether it gives calibrated probabilities. Pick a top 2.

### E1 — Does the judge have taste? (builder, runner, auditor)

Before building a training loop, validate the judge.

- `builder`: a Playwright harness that renders an HTML string to a PNG at a fixed viewport.
- Build **300 landing-page pairs** from a mix of sources: a frontier model asked for deliberately strong and deliberately flawed versions of the same brief, plus small-model outputs.
- Get reference labels on a **100-pair subset** from a frontier model, with David hand-checking 30 of them.
- `runner`: score all pairs with the top 2 judges.

Accept when: you have judge–reference agreement, a calibration curve (does 0.9 confidence mean ~90% right?), and position-bias rate (does it favor whichever is shown first? swap A/B to test).
**Gate:** continue only if agreement ≥75% on high-confidence pairs. Otherwise, try a small scoring LoRA on the judge, or switch judges.

### E2 — The design loop (builder, runner, auditor)

- **Coder:** a small model that fits in VRAM for QLoRA, such as Mellum 2.1 or a ~9B Qwen. Record which.
- **Loop:** 500 briefs → 4 samples each → render → judge pairwise → keep pairs with confidence ≥0.8 → **DPO with Unsloth** → repeat for 2–3 rounds.
- **Eval (held out):** 100 new briefs, base vs tuned, judged by (a) the training judge, (b) a *different* judge, and (c) the frontier model on 50 of them.

Accept when: you have win rates under all three judges. **Reward hacking check:** if (a) rises while (b) and (c) stay flat, the coder is gaming the judge. The `auditor` looks at 20 "winning" pages to find the trick, and that finding is itself worth writing up.

### E3 — Unlock as a measured variable (runner)

Run only once David has applied the unlock himself. Repeat one E2 DPO round with an identical config on stock vs unlocked: tokens per second, wall time, peak VRAM, and an identical eval score (a sanity check that results are unchanged). This produces a small, clean data point that few people have published for a 3060.

### E4 — Weight-space probe (builder, auditor), optional

Following the "Sparks of Weight-Space Programming" setup: find one measurable failure in the coder (e.g. % of outputs with unclosed tags, or repetition loops), give a frontier model a Python kernel over the relevant layers plus a forward-pass budget, and ask it to fix that failure without gradients. Measure the failure rate and E2 eval before and after.
Ask David before spending API budget here.

### Parked

- Sparse-attention variants (ZHA/LSA) on a small model, once llama.cpp or vLLM support lands.
- OptMem for persistent memory across lab sessions.
- Linking two small models with cross-model attention (the neural-pairing idea) and judging the pair vs one bigger model.
