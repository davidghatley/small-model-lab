#!/usr/bin/env bash
# E2 smoke, one command: round 0 on 10 briefs x 4 samples -> render -> judge -> select -> DPO (<=30 steps) -> vLLM generates 2 pages
# from the adapter on the AWQ base -> e2_eval (5 eval briefs, base vs smoke adapter, omnijev-0.8b). Outputs: runs/E2/_smoke/.
# Resumable/idempotent: finished stages are skipped (move runs/E2/_smoke aside for a clean run). ~15 min on the 3060.
set -euo pipefail
cd "$(dirname "$0")/.."
S=runs/E2/_smoke
.venv/bin/python scripts/e2_loop.py --round 0 --stage all --limit 10 --n-samples 4 --out $S/round0 --max-steps 30 --grad-accum 2
.venv/bin/python scripts/e2_loop.py --round 1 --stage gen --limit 2 --n-samples 1 --policy-adapter $S/round0/train/adapter --out $S/round1_gen
.venv/bin/python scripts/e2_eval.py --out $S/eval --policy-y $S/round0/train/adapter --name-y smoke_r0 --judges omnijev-0.8b --limit 5 --pack-n 5 --stage all
echo "SMOKE OK"
