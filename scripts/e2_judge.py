#!/usr/bin/env python3
"""Pairwise judge scoring for E2 (train-time pairs and eval pairs). Resumable, cached by pair_id.
  ~/anime-pipeline/tools/gpu_run --free --need 6500 .venv/bin/python scripts/e2_judge.py \
      --judge omnijev-0.8b --manifest pairs.jsonl --out scores_omnijev-0.8b.jsonl [--max-minutes 25]
manifest rows: {"pair_id", "a_png", "b_png"}. Output rows: pair_id, judge, p_first_ab, p_first_ba,
p_a_ab (P a better, order a,b), p_a_ba (order b,a, flipped), p_a_avg (order-averaged P a better), errors, lat.
Scores already in --out are skipped, so a rerun (even with a bigger manifest) only scores what is missing.
Logic is the same as score_pairs.py (e0_bench adapters, Q_PAIR/STATE_PAIR, p_first) minus the single-image calls.
rsi-jev-4b: run with .venv-rsijev/bin/python and gpu_run --need 10500 (e2_loop.py stage_judge does this itself).
"""
import argparse, json, sys, time, types, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import e0_bench as E

PRESETS = {  # judge -> (adapter, model_path, quant)
    "omnijev-0.8b": ("omnijev", "/mnt/models/llm/omnijev-0.8b", None),
    "rsi-jev-4b": ("rsijev", "/mnt/models/llm/rsi-jev-4b", None),  # run under .venv-rsijev/bin/python (transformers 5.17)
    "imajev-9b": ("imajev", "/mnt/work/models/imajev-9b", "nf4"),
}


def load_done(path):
    done = {}
    if Path(path).exists():
        for l in open(path):
            try: r = json.loads(l); done[r["pair_id"]] = r
            except Exception: pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True); ap.add_argument("--manifest", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--model-path"); ap.add_argument("--quant"); ap.add_argument("--adapter")
    ap.add_argument("--max-minutes", type=float, default=None); ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    pre = PRESETS.get(a.judge, (None, None, None))
    adapter = a.adapter or pre[0] or E.family(a.judge)
    a.model_path = a.model_path or pre[1]; a.quant = a.quant or pre[2]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    random.seed(a.seed)
    done = load_done(out)
    rows = [json.loads(l) for l in open(a.manifest) if l.strip()]
    todo = [r for r in rows if r["pair_id"] not in done][: a.limit]
    print(f"{len(rows)} pairs, {len(done)} cached, {len(todo)} to score", flush=True)
    if not todo: return 0
    srv = out.parent / f"{out.stem}_server"; srv.mkdir(exist_ok=True)
    ns = types.SimpleNamespace(judge=a.judge, model_path=a.model_path, quant=a.quant, out=str(srv), rotations=1, fast=False,
                               no_calibration=False, effort=None, server_cmd=None)
    t0 = time.time(); deadline = t0 + a.max_minutes * 60 if a.max_minutes else None
    ad = E.ADAPTERS[adapter](ns)
    print(f"loaded {a.judge} in {time.time()-t0:.1f}s", flush=True)
    n = 0
    try:
        with out.open("a") as f:
            for r in todo:
                if deadline and time.time() > deadline:
                    print("time budget reached; rerun to resume", flush=True); break
                row = {"pair_id": r["pair_id"], "judge": a.judge, "errors": []}
                A, B = r["a_png"], r["b_png"]
                for key, imgs in (("ab", [A, B]), ("ba", [B, A])):
                    s = time.perf_counter()
                    try: p = E.p_first(ad.ask(imgs, E.STATE_PAIR, E.Q_PAIR)["answers"].get("better"))
                    except Exception as e: row["errors"].append(f"{key}: {type(e).__name__}: {e}"); p = None
                    row[f"lat_{key}"] = time.perf_counter() - s; row[f"p_first_{key}"] = p
                ab, ba = row["p_first_ab"], row["p_first_ba"]
                row["p_a_ab"] = ab; row["p_a_ba"] = None if ba is None else 1 - ba
                vals = [v for v in (row["p_a_ab"], row["p_a_ba"]) if v is not None]
                row["p_a_avg"] = sum(vals) / len(vals) if len(vals) == 2 else None  # need both orders
                f.write(json.dumps(row) + "\n"); f.flush(); n += 1
                if n % 50 == 0: print(f"[{n}/{len(todo)}] {time.time()-t0:.0f}s", flush=True)
    finally:
        if hasattr(ad, "close"): ad.close()
    print(f"scored {n} pairs in {time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
