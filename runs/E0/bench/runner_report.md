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

## omnijev rerun

Old failed outputs (requests missing) moved to `runs/E0/bench/omnijev-0.8b.failed1` and `runs/E0/bench/omnijev-4b.failed1`.

### omnijev-0.8b: PASS (exit 0)
- single p50: 146.3 ms (A_clean 147.1, B_flawed 145.4); pairwise p50: 266.1 ms
- nvidia_smi_proc_peak_mib: 5260 (gpu used peak 5820)
- pairwise.pairwise_worked: true; swap_consistent: true; picks_clean_page_both_orders: true (choice A_clean in both orders)
- pairwise probabilities: p_A_better_when_A_first 0.9527, p_A_better_when_B_first 0.9952
- single p_good: A_clean 0.8037, B_flawed 0.0028 (scores_A_gt_B: true)
- probability fields present: true; 0 errors; deterministic across runs
- Log: `runs/E0/bench/omnijev-0.8b.stdout.log`

### omnijev-4b: FAIL (exit 1), two attempts, same error
Attempt 1 (moved to `runs/E0/bench/omnijev-4b.failed2`, stdout at `runs/E0/bench/omnijev-4b.failed2.stdout.log`) and attempt 2 (current `runs/E0/bench/omnijev-4b/`, stdout at `runs/E0/bench/omnijev-4b.stdout.log`) both failed while loading weights in the child server:
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.19 GiB. GPU 0 has a total capacity of 11.62 GiB of which 1.19 GiB is free. ... this process has 9.89 GiB memory in use. Of the allocated memory 9.73 GiB is allocated by PyTorch ...
  File ".../flide/backbones/load.py", line 173, in _load_into   src = f.get_tensor(key)
RuntimeError: server exited 1; see server.log
```
- Context: the 0.8b run finished before this; gpu_run --need 10000 passed, and nvidia-smi showed 547 MiB used by others at the retry. The loader itself reached ~9.9 GiB, so the failure is not transient contention. imajev-4b and rsi-jev-4b (same ~9.7 GiB footprint, earlier) loaded fine on this card, so this is marginal headroom in the loader, not a missing package.
- No results.json produced, so no latency, VRAM, pairwise or probability numbers. Not run: pairwise, probabilities.
- Next options (not tried, need your call): set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (reserved-but-unallocated was only 38 MiB, so unlikely to help), or the omnijev-4b loader's lean/fp8 path if the script exposes one. scripts/ was not edited.

### Run summary
- gpu: stock (no driver, firmware or unlock changes; gpu_run used normally)
- Wall time: about 2 min for both judges (0.8b bench ~1 min, 4b two attempts ~30 s each)
