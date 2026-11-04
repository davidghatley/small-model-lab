#!/usr/bin/env python3
"""Assemble 'small_model' pairs (base coder s0 vs s1) into runs/E1/pairs/sm-<num>/, pick 60-pair reference subset, append QA.
  .venv/bin/python scripts/assemble_sm_pairs.py [--n 100] [--seed 0]
Reuses Renderer/pixdiff from assemble_pairs.py. Idempotent; never touches fg-*/fh-* folders.
"""
import argparse, json, random, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from render import Renderer
from assemble_pairs import pixdiff, visible_text

BAD = {"e1-0026", "e1-0075", "e1-0076", "e1-0120", "e1-0122", "e1-0151", "e1-0170", "e1-0173"}


def blank_frac(png):
    import numpy as np
    from PIL import Image
    A = np.asarray(Image.open(png).convert("RGB")).reshape(-1, 3)
    _, c = np.unique(A, axis=0, return_counts=True)
    return float(c.max() / len(A))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="runs/E1/pages_base"); ap.add_argument("--out", default="runs/E1")
    ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out); pairs = out / "pairs"
    g = {}
    for l in (src / "gen.jsonl").read_text().splitlines():
        if l.strip(): j = json.loads(l); g[(j["brief_id"], j["k"])] = j
    ids = sorted({b for b, _ in g})
    elig = [b for b in ids if b not in BAD and all(
        (b, k) in g and g[(b, k)]["extracted_cleanly"] and not g[(b, k)]["truncated"] and (src / b / f"s{k}.html").exists()
        for k in (0, 1))]
    rng = random.Random(a.seed); order = elig[:]; rng.shuffle(order)
    sides = {b: rng.choice("ab") for b in elig}  # side of s0, drawn per eligible brief (sorted order -> stable)
    rows, rejected = [], []
    with Renderer() as R:
        for b in order:
            if len(rows) >= a.n: break
            pid = "sm-" + b[3:]; pd = pairs / pid; pd.mkdir(parents=True, exist_ok=True)
            s0side = sides[b]; s1side = "b" if s0side == "a" else "a"
            flags, infos = [], {}
            for k, sd in ((0, s0side), (1, s1side)):
                shutil.copyfile(src / b / f"s{k}.html", pd / f"{sd}.html")
                try: infos[sd] = R.render((pd / f"{sd}.html").read_text(), pd / f"{sd}.png")
                except Exception as e:
                    infos[sd] = dict(fonts_ok=False, font_failures=[f"render_error:{e}"]); flags.append(f"render_error:{sd}")
            if not any(f.startswith("render_error") for f in flags):
                for sd in "ab":
                    bf = blank_frac(pd / f"{sd}.png")
                    if bf > 0.98: flags.append(f"blank:{sd}:{bf:.3f}")
            if any(f.startswith(("render_error", "blank")) for f in flags):
                rejected.append((b, flags)); shutil.rmtree(pd); continue
            fonts_ok = all(i["fonts_ok"] for i in infos.values())
            if not fonts_ok: flags.append("font_failure")
            md, pp = pixdiff(pd / "a.png", pd / "b.png")
            meta = dict(pair_id=pid, brief_id=b, source="small_model", intended_better=None, flaw_severity=None, flaw_notes=None,
                        gen_src={sd: str(src / b / f"s{0 if sd == s0side else 1}.html") for sd in "ab"}, s0_side=s0side,
                        fonts_ok=fonts_ok, qa_flags=flags, pixel_diff_pct=round(pp, 3), pixel_mean_abs_diff=round(md, 3))
            (pd / "meta.json").write_text(json.dumps(meta, indent=1))
            rows.append(dict(pair_id=pid, flags=flags, pp=pp))
    rows.sort(key=lambda r: r["pair_id"])
    # reference subset
    ok = [r["pair_id"] for r in rows if r["pp"] >= 1.0]
    rest = [r["pair_id"] for r in rows if r["pp"] < 1.0]
    r2 = random.Random(a.seed)
    pool = ok[:]; r2.shuffle(pool)
    sub = pool[:60]
    if len(sub) < 60:
        r2.shuffle(rest); sub += rest[:60 - len(sub)]
    lab = out / "labels"
    (lab / "batch2.txt").write_text("\n".join(sub[:30]) + "\n"); (lab / "batch3.txt").write_text("\n".join(sub[30:60]) + "\n")
    rs = json.loads((lab / "reference_subset.json").read_text()); rs["small_model"] = sub
    (lab / "reference_subset.json").write_text(json.dumps(rs, indent=1))
    # QA
    pps = sorted(r["pp"] for r in rows)
    def q(p): return pps[min(len(pps) - 1, int(p * len(pps)))]
    bins = [0, 0.5, 1, 5, 20, 50, 100.01]
    hist = {f"{bins[i]}-{bins[i+1]:.0f}%" if i == len(bins) - 2 else f"{bins[i]}-{bins[i+1]}%": sum(1 for x in pps if bins[i] <= x < bins[i+1]) for i in range(len(bins) - 1)}
    flagged = [r for r in rows if r["flags"]]
    L = ["", "## small_model", "",
         f"- source: runs/E1/pages_base s0 vs s1 (Qwen2.5-Coder-7B base); script scripts/assemble_sm_pairs.py seed {a.seed}",
         f"- eligible briefs (clean, untruncated, minus {len(BAD)} known bad ids): {len(elig)}; pairs assembled: {len(rows)}; rejected on render/blank check: {len(rejected)} {[r[0] for r in rejected]}",
         f"- flagged pairs: {len(flagged)} {[(r['pair_id'], r['flags']) for r in flagged]}",
         f"- near-identical (pixel_diff_pct < 1%): {len(rest) if False else sum(1 for x in pps if x < 1)}; < 0.5%: {sum(1 for x in pps if x < 0.5)}",
         f"- pixel_diff_pct (channel diff > 8, top 800px): min {pps[0]:.2f}, p25 {q(.25):.2f}, median {q(.5):.2f}, p75 {q(.75):.2f}, max {pps[-1]:.2f}",
         f"- histogram: {hist}",
         f"- reference subset: 60 ids (excluded <1% diff: {len(sub) == len([s for s in sub if s in ok])}) in labels/batch2.txt, batch3.txt, reference_subset.json['small_model']",
         "- contact sheet: runs/E1/pairs_contact_sm.png (left=a, right=b)", ""]
    with open(out / "pairs_qa.md", "a") as f: f.write("\n".join(L))
    from PIL import Image
    pick = sorted(random.Random(a.seed).sample([r["pair_id"] for r in rows], min(8, len(rows))))
    tw, th, cols = 400, 250, 2
    sheet = Image.new("RGB", (cols * (2 * tw + 30), ((len(pick) + 1) // cols) * (th + 10)), "white")
    for i, pid in enumerate(pick):
        x = (i % cols) * (2 * tw + 30); y = (i // cols) * (th + 10)
        for k, s in enumerate("ab"):
            sheet.paste(Image.open(pairs / pid / f"{s}.png").convert("RGB").resize((tw, th)), (x + k * (tw + 10), y))
    sheet.save(out / "pairs_contact_sm.png")
    print(len(elig), len(rows), rejected, "near-identical", sum(1 for x in pps if x < 1), "sheet:", pick)


if __name__ == "__main__":
    main()
