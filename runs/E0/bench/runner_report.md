# E0 runner report

Gate: all GPU runs via `~/anime-pipeline/tools/gpu_run --free --need 6000` (gpu: stock). Python: repo `.venv`.
Downloads: `.venv/bin/hf` (the `hf` on PATH is absent). Bench wall time = bench process only.

## Results

| Judge | Exit | Single p50 (ms) | Pairwise p50 (ms) | nvidia_smi_proc_peak_mib | pairwise_worked | swap_consistent | picks_clean_page_both_orders | probabilities present | Bench wall |
|---|---|---|---|---|---|---|---|---|---|
| omnijev-0.8b | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 4 s |
| imajev-4b | 0 | 1747 | 1652 | 10384 | True | True | True | True | 98 s |
| rsi-jev-4b | 0 | 690 | 635 | 9964 | True | True | True | True | 107 s |
| omnijev-4b | 1 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 3 s |

Extra detail (imajev-4b / rsi-jev-4b): 0 errors in results.json; deterministic across runs for all four ops; scores A_clean vs B_flawed: imajev 2.86 vs 0.74, rsi 3.09 vs 0.39; pairwise picks A_clean in both orders. Torch max allocated: imajev 9729 MiB, rsi 9724 MiB. Load: imajev 17.7 s.

## Errors

### omnijev-0.8b (exit 1)
Failed at adapter construction, before any model load:
```
File "scripts/e0_bench.py", line 82, in __init__
    import requests
ModuleNotFoundError: No module named 'requests'
```
Full log: `runs/E0/bench/omnijev-0.8b/stdout.log`.

### omnijev-4b (exit 1)
Same failure at the same line (`ModuleNotFoundError: No module named 'requests'`). Log: `runs/E0/bench/omnijev-4b/stdout.log`.

Not installed by the runner: `requests` is not in the README's install commands for omnijev (only `flide torchvision`), and scripts/ may not be edited. Fix needed: `VIRTUAL_ENV=.venv uv pip install requests`, then rerun both omnijev rows.

## Notes
- imajev-4b: first attempt used `--exclude 'mlx/*'` as a bare argument, which hf took as a filename (download failed; the bench it launched was killed and rerun cleanly). Final download used `--exclude 'assets/*' --exclude 'mlx/*'`. Base `Qwen/Qwen3.5-4B` at the pinned revision downloaded to `.../imajev-4b/base`. Two stalled transfers were restarted; both resumed.
- rsi-jev-4b: bench run without `--effort` (README lists it as optional). `uv pip install "rsi-jev[fast,vision]"` succeeded but also changed transformers 5.22.1 -> 5.17.0 in the shared `.venv`.
- omnijev-4b: download stalled twice and was restarted (retry loop); final size 14 GB on disk, hf exit 0.
- Disk: /mnt/models had 62 GB free at start, 26 GB at the end. Coordinator rule applied: stop threshold 12 GB; no fallback to /mnt/work was needed.
- Ungated models only; the GGUF row was skipped.

## Wall time
Runner session: about 1 h (started around 15:40 MST, finished 16:37 MST), mostly downloads (omnijev-0.8b 75 s, imajev-4b ~12 GB with restarts ~17 min, rsi-jev-4b 9.1 GB ~10 min, omnijev-4b 14 GB ~25 min with restarts). Bench runs: 4 s, 98 s, 107 s, 3 s.

Logs: `runs/E0/dl_imajev-4b.log`, `runs/E0/dl_rsi-jev-4b.log`, `runs/E0/dl3_omnijev-4b.log`, `runs/E0/install_*.log`.
