#!/usr/bin/env python3
"""Score E1 pairs with one judge: pairwise in both orders + single-image p_good per side. Resumable.
  ~/anime-pipeline/tools/gpu_run --free --need 6000 .venv/bin/python scripts/score_pairs.py \
     --judge omnijev-0.8b --model-path /mnt/models/llm/omnijev-0.8b --pairs runs/E1/pairs --out runs/E1/scores/omnijev-0.8b.jsonl
Judge flags are those of e0_bench.py (--adapter --quant --rotations --fast --no-calibration --effort --server-cmd).
rsi-jev: use .venv-rsijev/bin/python. Adapters are reused from e0_bench.py.
Row fields: p_first_ab = P(first image better) with (a,b); p_first_ba with (b,a); p_a_ab = p_first_ab,
p_a_ba = 1 - p_first_ba; p_a_avg = mean; choice_* in {a,b}; p_good_a/p_good_b; lat_* seconds.
"""
import argparse, json, platform, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import e0_bench as E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True); ap.add_argument("--model-path", required=True)
    ap.add_argument("--adapter", choices=sorted(E.ADAPTERS)); ap.add_argument("--quant", default=None)
    ap.add_argument("--pairs", default="runs/E1/pairs"); ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--rotations", type=int, default=1); ap.add_argument("--fast", action="store_true")
    ap.add_argument("--no-calibration", action="store_true"); ap.add_argument("--effort", default=None)
    ap.add_argument("--server-cmd", default=None)
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    srv_dir = out.parent / f"{out.stem}_server"; srv_dir.mkdir(exist_ok=True)
    cmdline = " ".join([sys.executable] + sys.argv)
    (out.parent / f"{out.stem}.command.txt").write_text(cmdline + "\n")
    random.seed(a.seed)
    try:
        import numpy as np; np.random.seed(a.seed)
    except ImportError: pass
    try:
        import torch; torch.manual_seed(a.seed); torch.cuda.manual_seed_all(a.seed)
    except ImportError: pass
    (out.parent / f"{out.stem}.config.json").write_text(json.dumps(
        {"args": {k: v for k, v in vars(a).items()}, "seed": a.seed, "gpu": "stock", "python": platform.python_version(), "command": cmdline}, indent=2))
    done = set()
    if out.exists():
        done = {json.loads(l)["pair_id"] for l in out.read_text().splitlines() if l.strip()}
    dirs = [d for d in sorted(Path(a.pairs).iterdir()) if d.is_dir() and (d / "a.png").exists() and (d / "b.png").exists()]
    todo = [d for d in dirs if d.name not in done][: a.limit]
    print(f"{len(dirs)} pairs, {len(done)} done, {len(todo)} to score", flush=True)
    if not todo: return
    a.out = str(srv_dir)  # adapters write server.log into a.out
    t0 = time.time()
    ad = E.ADAPTERS[a.adapter or E.family(a.judge)](a)
    print(f"loaded {a.judge} in {time.time()-t0:.1f}s", flush=True)
    try:
        with out.open("a") as f:
            for i, d in enumerate(todo):
                A, B = str(d / "a.png"), str(d / "b.png")
                row = {"pair_id": d.name, "judge": a.judge, "errors": []}

                def call(key, imgs, st, qs):
                    s = time.perf_counter()
                    try: r = ad.ask(imgs, st, qs)["answers"]
                    except Exception as e: row["errors"].append(f"{key}: {type(e).__name__}: {e}"); r = {}
                    row[f"lat_{key}"] = time.perf_counter() - s
                    return r
                r = call("ab", [A, B], E.STATE_PAIR, E.Q_PAIR); row["p_first_ab"] = E.p_first(r.get("better"))
                r = call("ba", [B, A], E.STATE_PAIR, E.Q_PAIR); row["p_first_ba"] = E.p_first(r.get("better"))
                r = call("single_a", [A], E.STATE_SINGLE, E.Q_SINGLE); row["p_good_a"] = E.p_yes(r.get("good")); row["rating_a"] = r.get("rating")
                r = call("single_b", [B], E.STATE_SINGLE, E.Q_SINGLE); row["p_good_b"] = E.p_yes(r.get("good")); row["rating_b"] = r.get("rating")
                ab, ba = row["p_first_ab"], row["p_first_ba"]
                row["p_a_ab"] = ab; row["p_a_ba"] = None if ba is None else 1 - ba
                vals = [v for v in (row["p_a_ab"], row["p_a_ba"]) if v is not None]
                row["p_a_avg"] = sum(vals) / len(vals) if vals else None
                row["choice_ab"] = None if ab is None else ("a" if ab > .5 else "b")
                row["choice_ba"] = None if ba is None else ("b" if ba > .5 else "a")
                f.write(json.dumps(row, default=str) + "\n"); f.flush()
                if i % 10 == 0: print(f"[{i+1}/{len(todo)}] {d.name} p_a_avg={row['p_a_avg']}", flush=True)
    finally:
        if hasattr(ad, "close"): ad.close()
    print("done", out)


if __name__ == "__main__":
    main()
