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
| omnijev GGUF (untested) | e.g. `hf download bartowski/OmniJev_OneJev-4B-GGUF <file>.gguf` (OneJev 1.0 naming; the scout saw `mradermacher/OneJev1.6-0.8B-GGUF:Q8_0` in the README); `uv pip install git+https://github.com/OmniJev/OneJev.git` plus llama.cpp on PATH | varies | add `--quant gguf-q8_0`, `--model-path` = the .gguf path (or HF `repo:quant` spec) |

Notes for the runner:
- Adapters for rsijev and omnijev were written from their READMEs only. Expect to fix small API details (`Decider` arguments and whether it takes a local path; flide flags). If a server command differs use `--server-cmd "flide serve --model {model_path} --port {port}"`.
- Pairwise is tried for every judge; a failure is recorded in `results.json` (`pairwise.pairwise_worked=false`, `failed_ops`), not fatal. Exit code 1 only if single-image scoring fails.
- omnijev runs as a child server, so torch VRAM reads 0; use `nvidia_smi_proc_peak_mib`.
- Smoke result (imajev-2b, 3060, eager bf16, rotations 1): p50 ~1.12 s per call, torch peak 4.67 GiB-ish (4667 MiB), nvidia-smi 5050 MiB.
