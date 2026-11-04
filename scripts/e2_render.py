#!/usr/bin/env python3
"""Render E2 pages at 1280x800 with N parallel browser processes. CPU only (no gpu_run). Resumable.
  .venv/bin/python scripts/e2_render.py --pages runs/E2/round0/pages [--workers 6] [--max-minutes 25]
Reads <pages>/gen.jsonl, renders every <pages>/<brief>/s<k>.html to s<k>.png, appends to <pages>/render.jsonl:
{brief_id,k,png,ok,blank,error,fonts_ok,font_failures,distinct_colors,top_color_frac,seconds}.
ok = rendered without exception. blank = (nearly) one flat color (top color covers >=99.5% of pixels or <4 distinct colors).
Clean for training = gen.extracted_cleanly and render ok and not blank.
"""
import argparse, json, sys, time, os
from multiprocessing import Pool
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

_R = None


def _init():
    global _R
    from render import Renderer
    _R = Renderer().__enter__()


def _blank(png):
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(png).convert("RGB")).reshape(-1, 3)
    cols, counts = np.unique(im, axis=0, return_counts=True)
    top = counts.max() / len(im)
    return bool(top >= 0.995 or len(cols) < 4), int(len(cols)), float(top)


def _one(job):
    bid, k, html_p, png_p = job
    t0 = time.time(); row = dict(brief_id=bid, k=k, png=png_p, ok=False, blank=None, error=None)
    try:
        info = _R.render(Path(html_p).read_text(), png_p)
        row.update(ok=True, fonts_ok=info["fonts_ok"], font_failures=info["font_failures"])
        row["blank"], row["distinct_colors"], row["top_color_frac"] = _blank(png_p)
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    row["seconds"] = round(time.time() - t0, 2)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True); ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-minutes", type=float, default=None)
    a = ap.parse_args()
    pages = Path(a.pages); rp = pages / "render.jsonl"
    done = set()
    if rp.exists():
        for l in open(rp):
            try: r = json.loads(l); done.add((r["brief_id"], r["k"]))
            except Exception: pass
    jobs = []
    for l in open(pages / "gen.jsonl"):
        r = json.loads(l); key = (r["brief_id"], r["k"])
        h = pages / r["brief_id"] / f"s{r['k']}.html"
        if key not in done and h.exists():
            jobs.append((r["brief_id"], r["k"], str(h), str(h.with_suffix(".png"))))
    print(f"{len(jobs)} to render ({len(done)} done)", flush=True)
    if not jobs: return 0
    t0 = time.time(); deadline = t0 + a.max_minutes * 60 if a.max_minutes else None
    n = bad = 0
    with Pool(a.workers, initializer=_init) as pool, open(rp, "a") as f:
        it = pool.imap_unordered(_one, jobs, chunksize=1)
        for row in it:
            f.write(json.dumps(row) + "\n"); f.flush(); n += 1; bad += (not row["ok"]) or bool(row["blank"])
            if n % 25 == 0: print(f"[{n}/{len(jobs)}] {time.time()-t0:.0f}s flagged={bad}", flush=True)
            if deadline and time.time() > deadline:
                print("time budget reached; rerun to resume", flush=True); pool.terminate(); break
    print(f"rendered {n} in {time.time()-t0:.0f}s, flagged {bad}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
