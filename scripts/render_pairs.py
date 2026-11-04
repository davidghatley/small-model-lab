#!/usr/bin/env python3
"""Render missing PNGs for every pair dir and validate. Exit 1 if any pair is invalid.
  .venv/bin/python scripts/render_pairs.py --pairs runs/E1/pairs [--force]
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from render import render_file


def png_size(p):
    from PIL import Image
    with Image.open(p) as im: return im.size


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pairs", default="runs/E1/pairs"); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    bad, n, rendered = [], 0, 0
    for d in sorted(p for p in Path(a.pairs).iterdir() if p.is_dir()):
        n += 1; errs = []
        for s in "ab":
            h, png = d / f"{s}.html", d / f"{s}.png"
            if not h.exists() or h.stat().st_size == 0: errs.append(f"{s}.html missing/empty"); continue
            if a.force or not png.exists():
                try: render_file(h, png); rendered += 1
                except Exception as e: errs.append(f"{s} render failed: {e}"); continue
            try:
                if png_size(png) != (1280, 800): errs.append(f"{s}.png is {png_size(png)}")
            except Exception as e: errs.append(f"{s}.png unreadable: {e}")
        try:
            m = json.loads((d / "meta.json").read_text())
            if m.get("pair_id") != d.name: errs.append("meta.pair_id != dir name")
            for k in ("brief_id", "source"): 
                if not m.get(k): errs.append(f"meta.{k} missing")
            if m.get("source") not in ("frontier_graded", "frontier_hard", "small_model"): errs.append("bad source")
            if m.get("intended_better") not in ("a", "b", None): errs.append("bad intended_better")
            if m.get("flaw_severity") not in ("obvious", "moderate", "subtle", None): errs.append("bad flaw_severity")
        except Exception as e: errs.append(f"meta.json: {e}")
        if errs: bad.append((d.name, errs))
    print(f"{n} pairs, rendered {rendered} PNGs, {len(bad)} invalid")
    for k, e in bad: print("INVALID", k, e)
    sys.exit(1 if bad or n == 0 else 0)


if __name__ == "__main__":
    main()
