# small-model-lab

Cheap, reproducible experiments on small models that fit this box: **RTX 3060 (12 GB VRAM) + 64 GB RAM**, Linux. The aim is one publishable before/after result.
First target: the **design loop**. A small coder model writes HTML, a fast local "System One" vision judge scores the rendered page, and those judgments fine-tune the coder with DPO.

David's original brief is kept as written in `docs/brief.md`. It describes what he wants, not a fixed spec. Keep the goal, change the method when reality calls for it, and log each change in `LEDGER.md` / `PLAN.md`.

## Owner's rules (house rules + brief)
- **Never install or run a GPU unlock** (kernel module or UEFI). David does that himself. Record `gpu: stock|unlocked` on every run's setup line.
- GPU jobs always go through `~/anime-pipeline/tools/gpu_run [--free] [--need MiB]` (see the gpu-share skill). Keep batches under ~30 min. Never kill processes you didn't start. Free ComfyUI by API, never by killing it.
- Ask before downloads over **10 GB** (house rule, stricter than the brief's 20 GB), before sudo, before touching other projects' envs, and before anything that sends data to a paid API.
- Check every model's license before using it and record it in the ledger. Some judges are **non-commercial only**. Prefer ungated models.
- Fix seeds. Save the exact config and command for every result next to it in `runs/`.
- Held-out sets stay held out: never train on eval prompts.
- Never delete anything. Move it aside instead.
- Weights live in `/mnt/models/llm/<name>/`, never in this repo. `/` has almost no free space.
- Run Python that reads downloaded files with `python -I`, from scripts kept outside the download dir.

## Roles and model routing
| Role | Who | Model | Does |
|---|---|---|---|
| Orchestrator / evaluator | main session | strongest | Plans, writes briefs, checks reports against acceptance criteria, keeps `LEDGER.md`, decides the next step. Does no bulk work itself. |
| `scout` | subagent | haiku | Web/HF/GitHub lookups, license checks, reading READMEs. |
| `runner` | subagent | haiku | Runs scripts, benchmarks, training jobs. Reports numbers. Never changes code. |
| `builder` | subagent | sonnet | Writes and fixes code: harnesses, renderers, training configs. |
| `auditor` | subagent | sonnet | Independently checks a result it didn't produce. |

Use the cheapest model that can do the task. Escalate a subagent only after one failed attempt, and log it in the ledger.
Agent definitions are in `.claude/agents/`. A session started before those files existed won't see them as agent types; then use `general-purpose` with the same `model` and paste the agent file's instructions into the brief.

## Context rules
1. Files are the memory, not transcripts. Subagents write full output to `runs/<exp>/<task>/` and return a report of at most 150 words: status, key numbers, paths, blockers.
2. One task per subagent, with fresh context. Each brief is self-contained: goal, inputs (paths), checkable acceptance criteria, output paths, report format.
3. The orchestrator reads reports and `LEDGER.md`. It opens raw files only when a number looks wrong.
4. At each phase boundary, rewrite that experiment's ledger entry into 10 lines or fewer.
5. If a task would need more than ~40k tokens of reading, split it, or have a scout pre-summarize the material to a file.
6. Subagents never spawn subagents.

## Performer / evaluator loop
1. The brief states checkable acceptance criteria.
2. The performer does the work and reports back.
3. Pass → log it and move on. Fail → send one corrective brief naming exactly what failed. A second failure → escalate the model or re-scope the task, and log why.
4. Any result headed for a writeup gets an `auditor` pass first.

## Layout
- `LEDGER.md`: one entry per experiment (E0–E4). This is the source of truth for status.
- `PLAN.md`: phases, open questions, dated decisions.
- `docs/brief.md`: David's original brief.
- `runs/<exp>/<task>/`: outputs, logs, configs and commands. Small text results are committed; images, weights and big jsonl are ignored.
- `scripts/`: harnesses (renderer, judge clients, training).
- `.venv/`: uv Python 3.12 env (`VIRTUAL_ENV=.venv uv pip install ...`). Never the system Python.

## Traps
- `gpu_run` caps RAM at 20 GB, and the cap counts page cache. mmap-heavy engines need `GPU_RUN_MEM=44G`.
- Free space: `/mnt/models` has ~66 GB free (2026-11-03). Check `df -h /mnt/models` before pulling weights.
