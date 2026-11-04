#!/usr/bin/env bash
# One-command E1 smoke test: 6 synthetic pairs -> render -> score (omnijev-0.8b) -> analyze. Output: runs/E1/_smoke/
set -euo pipefail
cd "$(dirname "$0")/.."
S=runs/E1/_smoke; rm -rf "$S.prev"; [ -d "$S" ] && mv "$S" "$S.prev.$(date +%s)"
.venv/bin/python scripts/make_smoke_pairs.py "$S"
.venv/bin/python scripts/render_pairs.py --pairs "$S/pairs"
~/anime-pipeline/tools/gpu_run --free --need 6000 .venv/bin/python scripts/score_pairs.py \
  --judge omnijev-0.8b --model-path /mnt/models/llm/omnijev-0.8b --pairs "$S/pairs" --out "$S/scores/omnijev-0.8b.jsonl"
.venv/bin/python scripts/analyze_e1.py --pairs "$S/pairs" --scores "$S"/scores/*.jsonl --labels "$S/labels" --out "$S"
test -s "$S/analysis.md" && echo "SMOKE OK: $S/analysis.md"
