# scripts

All Python runs with the repo venv: `.venv/bin/python` (transformers 5.22.1), except rsi-jev, which uses `.venv-rsijev/bin/python` (uv, Python 3.12; never system Python).
GPU commands go through the shared gate: `~/anime-pipeline/tools/gpu_run --free --need 6000 <cmd>`.

## render.py
`.venv/bin/python scripts/render.py page.html out.png` renders at a fixed 1280x800 viewport (importable: `render_html`, `render_file`). E0 fixtures: `runs/E0/fixtures/{A_clean,B_flawed}.{html,png}`.

## e0_bench.py (E0 judge benchmark)
Per judge: load, then 1 warmup + 10 timed runs of 4 ops (single-image A, single-image B, pairwise A,B, pairwise B,A). Writes to `--out`: `results.json` (p50/p90 latency per op and overall, VRAM = torch max_allocated + nvidia-smi per-process and whole-GPU peak, raw answers, probabilities, pairwise worked, swap consistency, determinism), `config.json` (args, seed, versions, `gpu: stock`), `command.txt`, `run.log`.
Seed fixed by `--seed` (default 0). Other flags: `--runs`, `--warmup`, `--quant <label>` (imajev: `nf4` = bitsandbytes 4-bit NF4 + double quant + bf16 compute, or `int8`; vision tower and lm_head stay bf16; omnijev: `gguf*`), `--rotations N` and `--fast` and `--no-calibration` (imajev), `--effort` (rsijev), `--server-cmd` (omnijev), `--adapter` (override inference from the judge name).

Template (swap the judge/path):
```
~/anime-pipeline/tools/gpu_run --free --need 6000 .venv/bin/python scripts/e0_bench.py \
  --judge <name> --model-path /mnt/models/llm/<name> [--quant ...] --out runs/E0/bench/<name>/
```

### Per candidate (download first; all repos checked ungated, Apache-2.0)
imajev ships a LoRA adapter plus decision readout on a Qwen3.5 base. Layout the harness expects: adapter files at `<model-path>/`, base weights in `<model-path>/base/`. Code is cloned at `/mnt/models/llm/_src/imajev` (override with `IMAJEV_SRC`); no extra pip install needed beyond the venv.

| Judge | Download | Size | Run |
|---|---|---|---|
| imajev-2b (TESTED) | `hf download mohit67890/imajev-2b --local-dir /mnt/models/llm/imajev-2b --exclude 'assets/*' 'mlx/*'` and base `hf download Qwen/Qwen3.5-2B --revision 15852e8c16360a2fea060d615a32b45270f8a8fc --local-dir /mnt/models/llm/imajev-2b/base` | ~4.4 GB | `--judge imajev-2b --model-path /mnt/models/llm/imajev-2b` |
| imajev-4b (untested; same code path as 2b) | `hf download mohit67890/imajev-4b ...` same excludes, `--local-dir /mnt/models/llm/imajev-4b`; base `Qwen/Qwen3.5-4B --revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` into `.../imajev-4b/base` | ~9.3 GB base + adapter, tight on 12 GB | `--judge imajev-4b --model-path /mnt/models/llm/imajev-4b` |
| imajev-9b (TESTED, nf4 only; bf16 does not fit) | `hf download mohit67890/imajev-9b --local-dir /mnt/work/models/imajev-9b --exclude 'assets/*' --exclude 'mlx/*'` (repeat `--exclude`; the one-flag-two-patterns form fails) and base `hf download Qwen/Qwen3.5-9B --revision c202236235762e1c871ad0ccb60c8ee5ba337b9a --local-dir /mnt/work/models/imajev-9b/base` (on /mnt/work SSD, not /mnt/models) | ~19 GB | `--judge imajev-9b --model-path /mnt/work/models/imajev-9b --quant nf4` (8.8 GB nvidia-smi peak) |
| rsi-jev-4b (untested) | `hf download shgao/rsi-jev-v6.1-vl-4b --local-dir /mnt/models/llm/rsi-jev-4b`; own venv: `.venv-rsijev` (rsi-jev pins transformers 5.17.x; built from `runs/E0/bench/venv_after_rsijev.txt`). Run with `.venv-rsijev/bin/python`, not `.venv` | ~9.7 GB bf16, tight | `--judge rsi-jev-4b --model-path /mnt/models/llm/rsi-jev-4b [--effort auto]` |
| omnijev-0.8b (untested) | `hf download OmniJev/OneJev1.6-0.8B --local-dir /mnt/models/llm/omnijev-0.8b`; `VIRTUAL_ENV=.venv uv pip install flide torchvision` | ~1.7 GB | `--judge omnijev-0.8b --model-path /mnt/models/llm/omnijev-0.8b` |
| omnijev-4b (untested) | `hf download OmniJev/OneJev1.6-4B --local-dir /mnt/models/llm/omnijev-4b`; flide as above | ~9.1 GB bf16, tight | `--judge omnijev-4b --model-path /mnt/models/llm/omnijev-4b` |
| omnijev-4b GGUF Q8_0 (tested; bf16 4b OOMs in flide on 12 GB, flide --quantize fp8 needs sm_89+) | `hf download mradermacher/OneJev1.6-4B-GGUF OneJev1.6-4B.Q8_0.gguf OneJev1.6-4B.mmproj-f16.gguf --local-dir /mnt/work/models/omnijev-4b-gguf`; prebuilt llama.cpp b12083 CUDA 12.8 + cudart tarballs from github.com/ggml-org/llama.cpp/releases extracted into `/mnt/work/tools/llama.cpp-b12083/llama-b12083/` (cudart `.so.12` copied beside `llama-server`); `uv venv .venv-qev --python 3.12; VIRTUAL_ENV=.venv-qev uv pip install git+https://github.com/OmniJev/OneJev.git` (provides `qev`; Apache-2.0, ungated) | 4.5 GB + 0.23 GB mmproj | `~/anime-pipeline/tools/gpu_run --free --need 9000 .venv/bin/python scripts/e0_bench.py --judge omnijev-4b --adapter omnijev --quant gguf-q8_0 --model-path /mnt/work/models/omnijev-4b-gguf/OneJev1.6-4B.Q8_0.gguf --out runs/E0/bench/omnijev-4b-gguf-q8_0` (env overrides: `LLAMA_CPP_DIR`, `QEV_TOKENIZER` default `/mnt/models/llm/omnijev-4b`, `QEV_MMPROJ` default sibling `*mmproj-f16.gguf`) |

Notes for the runner:
- Adapters for rsijev and omnijev were written from their READMEs only. Expect to fix small API details (`Decider` arguments and whether it takes a local path; flide flags). If a server command differs use `--server-cmd "flide serve --model {model_path} --port {port}"`.
- Pairwise is tried for every judge; a failure is recorded in `results.json` (`pairwise.pairwise_worked=false`, `failed_ops`), not fatal. Exit code 1 only if single-image scoring fails.
- omnijev runs as a child server, so torch VRAM reads 0; use `nvidia_smi_proc_peak_mib`.
- Smoke result (imajev-2b, 3060, eager bf16, rotations 1): p50 ~1.12 s per call, torch peak 4.67 GiB-ish (4667 MiB), nvidia-smi 5050 MiB.

## E1 (does the judge have taste?)
Briefs: `.venv/bin/python scripts/make_briefs.py` (seeded; `--check` only verifies) writes `briefs/e1.jsonl` (200), `briefs/e2_train.jsonl` (500), `briefs/e2_eval.jsonl` (100, HELD OUT: never train on it, never use in E1). Fields: id, product, industry, audience, tone, sections, description. The check asserts unique ids and no exact or normalized text shared across any briefs/splits.

Pair layout (`runs/E1/pairs/<pair_id>/`): `a.html b.html a.png b.png meta.json`; meta.json = `{pair_id, brief_id, source: frontier_graded|frontier_hard|small_model, intended_better: "a"|"b"|null, flaw_severity: obvious|moderate|subtle|null, flaw_notes}`. Optional labels: `runs/E1/labels/reference.jsonl` (`{pair_id, better: "a"|"b", confidence, rationale}`) and `labels/david.jsonl` (same shape).

```
.venv/bin/python scripts/render_pairs.py --pairs runs/E1/pairs          # renders missing PNGs (1280x800 viewport), validates; exit 1 if invalid
# score (resumable; writes <out>.config.json and <out>.command.txt beside the jsonl); all four judges:
G="$HOME/anime-pipeline/tools/gpu_run --free --need 9000"
$G .venv/bin/python scripts/score_pairs.py --judge omnijev-0.8b --model-path /mnt/models/llm/omnijev-0.8b --out runs/E1/scores/omnijev-0.8b.jsonl
$G .venv/bin/python scripts/score_pairs.py --judge omnijev-4b --adapter omnijev --quant gguf-q8_0 --model-path /mnt/work/models/omnijev-4b-gguf/OneJev1.6-4B.Q8_0.gguf --out runs/E1/scores/omnijev-4b.jsonl
$G .venv-rsijev/bin/python scripts/score_pairs.py --judge rsi-jev-4b --model-path /mnt/models/llm/rsi-jev-4b --out runs/E1/scores/rsi-jev-4b.jsonl
$G .venv/bin/python scripts/score_pairs.py --judge imajev-9b --quant nf4 --model-path /mnt/work/models/imajev-9b --out runs/E1/scores/imajev-9b.jsonl
.venv/bin/python scripts/analyze_e1.py --scores runs/E1/scores/*.jsonl --out runs/E1   # analysis.md/json + calibration_<judge>.png
bash scripts/smoke_e1.sh                                                              # 6 synthetic pairs end to end, runs/E1/_smoke/
```
score_pairs.py reuses the adapters in e0_bench.py (same flags: `--adapter --quant --rotations --fast --no-calibration --effort --server-cmd`; `--limit N` for a trial). Row: `p_first_ab`, `p_first_ba` (P first image better, orders (a,b) and (b,a)), `p_a_ab`, `p_a_ba`, `p_a_avg`, `choice_ab`, `choice_ba`, `p_good_a`, `p_good_b`, `lat_*`. analyze_e1.py: high-confidence = order-averaged P(a) >= 0.8 or <= 0.2; calibration = 10 bins over confidence 0.5-1.0 vs the reference labels (by-construction if no reference); gate PASS if high-confidence agreement vs reference >= 0.75. matplotlib was added to `.venv` for the plots.
