#!/usr/bin/env python3
"""E2 held-out evaluation: policy X (usually base) vs policy Y (tuned) on briefs/e2_eval.jsonl. Run with .venv/bin/python.
  .venv/bin/python scripts/e2_eval.py --out runs/E2/eval/round1 --policy-y runs/E2/round0/train/adapter --judges omnijev-0.8b,imajev-9b --stage all
Policy spec: 'base' (AWQ Qwen2.5-Coder-7B-Instruct) or a LoRA adapter dir served on the AWQ base. 1 sample/brief, temperature 0.7, seed 0 (the
per-sample seed depends only on brief id and seed, so X and Y share seeds). Stages: gen, render, judge, report, pack, all. GPU stages call
gpu_run and take --max-minutes (<30); exit 3 = incomplete, call again.
HELD-OUT guard: before any stage, asserts that no eval brief id / product text / description text occurs in any DPO dataset under runs/E2
(runs/E2/**/dpo*.jsonl), in the train briefs, or in --extra-datasets.
Report (report.json/.md): per judge, win rate of Y over X with bootstrap 95% CI (resampling briefs, 2000, seed 0), order-averaged P, a
length-controlled win rate (logistic regression win ~ log(len_Y/len_X); LC = predicted win rate at equal length; bootstrapped CI) and a
bucketed (terciles of the length ratio) win rate. Blind pack: --pack-n pairs, random sides, neutral ids; the key goes in pack_key.json,
outside pack/.
"""
import argparse, glob, json, math, os, random, re, shlex, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPU_RUN = os.path.expanduser("~/anime-pipeline/tools/gpu_run")
PY, PYV = str(ROOT / ".venv/bin/python"), str(ROOT / ".venv-vllm/bin/python")
NEED = dict(gen=11000, **{"omnijev-0.8b": 6500, "imajev-9b": 9800})
norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def holdout_guard(a, eval_briefs):
    ids = {b["id"] for b in eval_briefs}
    texts = {norm(b["product"]) for b in eval_briefs} | {norm(b["description"]) for b in eval_briefs}
    train = [json.loads(l) for l in open(ROOT / "briefs/e2_train.jsonl") if l.strip()]
    assert not ids & {b["id"] for b in train}, "eval ids overlap train briefs"
    assert not texts & ({norm(b["product"]) for b in train} | {norm(b["description"]) for b in train}), "eval text overlaps train briefs"
    files = sorted(set(glob.glob(str(ROOT / "runs/E2/**/dpo*.jsonl"), recursive=True)) | set(a.extra_datasets or []))
    n = 0
    for f in files:
        for l in open(f):
            if not l.strip(): continue
            r = json.loads(l); n += 1; blob = norm(r.get("prompt", "") + " " + str(r.get("brief_id", "")))
            assert r.get("brief_id") not in ids, f"HELD-OUT VIOLATION: eval id {r.get('brief_id')} in {f}"
            for t in texts:
                assert t not in blob, f"HELD-OUT VIOLATION: eval text {t[:60]!r} in {f}"
    print(f"held-out guard OK: {len(ids)} eval briefs vs {len(files)} DPO dataset(s), {n} rows, {len(train)} train briefs", flush=True)
    return dict(datasets_checked=files, rows_checked=n)


def run(cmd, log):
    print("+", " ".join(shlex.quote(x) for x in cmd)[:240], flush=True)
    with open(log, "a") as lg:
        return subprocess.run(cmd, stdout=lg, stderr=subprocess.STDOUT, cwd=ROOT).returncode


def policies(a):
    return [("x", a.name_x, a.policy_x), ("y", a.name_y, a.policy_y)]


def pdir(a, name): return Path(a.out) / f"pages_{name}"


def ok_pages(a):
    """{brief_id: {x:(html_path,png_path,chars), y:...}} for briefs where each policy has a clean, non-blank render."""
    res, flags = {}, {}
    for key, name, _ in policies(a):
        d = pdir(a, name)
        gen = {r["brief_id"]: r for r in jl(d / "gen.jsonl")}; ren = {r["brief_id"]: r for r in jl(d / "render.jsonl")}
        flags[key] = dict(n=len(gen), clean=0, unclean=0, render_failed=0, blank=0)
        for bid, g in gen.items():
            r = ren.get(bid)
            if not g["extracted_cleanly"]: flags[key]["unclean"] += 1
            elif r is None or not r["ok"]: flags[key]["render_failed"] += 1
            elif r["blank"]: flags[key]["blank"] += 1
            else:
                flags[key]["clean"] += 1
                h = d / bid / "s0.html"
                res.setdefault(bid, {})[key] = (str(h), str(h.with_suffix(".png")), len(h.read_text()))
    return {b: v for b, v in res.items() if len(v) == 2}, flags


def stage_gen(a, briefs):
    rc_all = 0
    for key, name, pol in policies(a):
        d = pdir(a, name); d.mkdir(parents=True, exist_ok=True)
        if len({r["brief_id"] for r in jl(d / "gen.jsonl")}) >= len(briefs): continue
        cmd = [GPU_RUN, "--free", "--need", str(NEED["gen"]), PYV, "scripts/gen_pages.py", "--briefs", a.briefs, "--n-samples", "1", "--temperature", "0.7",
               "--seed", "0", "--max-tokens", "6144", "--out", str(d), "--max-minutes", str(a.max_minutes)]
        if a.limit: cmd += ["--limit", str(a.limit)]
        if pol != "base": cmd += ["--adapter", pol]
        run(cmd, d / "stage_gen.log")
        if len({r["brief_id"] for r in jl(d / "gen.jsonl")}) < len(briefs): rc_all = 3
    return rc_all


def stage_render(a, briefs):
    rc = 0
    for key, name, _ in policies(a):
        d = pdir(a, name)
        if len(jl(d / "render.jsonl")) < len(jl(d / "gen.jsonl")) or not jl(d / "gen.jsonl"):
            run([PY, "scripts/e2_render.py", "--pages", str(d), "--workers", "6", "--max-minutes", str(a.max_minutes)], d / "stage_render.log")
        if len(jl(d / "render.jsonl")) < len(jl(d / "gen.jsonl")): rc = 3
    return rc


def manifest(a, judge):
    pages, _ = ok_pages(a)
    rows = [dict(pair_id=bid, a_png=str(Path(v["x"][1]).resolve()), b_png=str(Path(v["y"][1]).resolve())) for bid, v in sorted(pages.items())]
    jd = Path(a.out) / "judge"; jd.mkdir(exist_ok=True)
    (jd / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows, jd


def stage_judge(a, briefs):
    rc = 0
    for j in a.judges.split(","):
        rows, jd = manifest(a, j)
        sc = jd / f"scores_{j}.jsonl"
        done = lambda: {r["pair_id"] for r in jl(sc) if r.get("p_a_avg") is not None}
        if all(r["pair_id"] in done() for r in rows): continue
        run([GPU_RUN, "--free", "--need", str(NEED[j]), PY, "scripts/e2_judge.py", "--judge", j, "--manifest", str(jd / "manifest.jsonl"),
             "--out", str(sc), "--max-minutes", str(a.max_minutes)], jd / f"stage_judge_{j}.log")
        if not all(r["pair_id"] in done() for r in rows): rc = 3
    return rc


# ---------------------------------------------------------------- stats
def logit_fit(x, y, iters=50, ridge=1e-3):
    """Logistic regression y ~ b0 + b1*x by Newton with a tiny ridge on the slope. Returns (b0, b1)."""
    import numpy as np
    X = np.column_stack([np.ones(len(x)), np.asarray(x, float)]); y = np.asarray(y, float); b = np.zeros(2)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p) + 1e-9
        g = X.T @ (y - p) - ridge * np.array([0, b[1]]); H = (X * W[:, None]).T @ X + ridge * np.diag([0, 1])
        step = np.linalg.solve(H, g); b = b + step
        if np.abs(step).max() < 1e-8: break
    return float(b[0]), float(b[1])


def sig(z): return 1 / (1 + math.exp(-z))


def analyze(rows, conf_min=0.0, nboot=2000, seed=0):
    """rows: dict(p_y = P(Y better), lr = log(len_y/len_x)). Ties (p==.5) count 0.5."""
    import numpy as np
    rows = [r for r in rows if max(r["p_y"], 1 - r["p_y"]) >= conf_min]
    n = len(rows)
    if n < 2: return dict(n=n)
    win = np.array([1.0 if r["p_y"] > .5 else 0.5 if r["p_y"] == .5 else 0.0 for r in rows]); pm = np.array([r["p_y"] for r in rows]); lr = np.array([r["lr"] for r in rows])
    def lc(idx):
        w = win[idx]; x = lr[idx]
        keep = w != .5
        if keep.sum() < 4 or len(set(w[keep])) < 2: return float("nan")
        return sig(logit_fit(x[keep], w[keep])[0])
    rng = np.random.default_rng(seed); wins, lcs, pms = [], [], []
    for _ in range(nboot):
        idx = rng.integers(0, n, n); wins.append(win[idx].mean()); pms.append(pm[idx].mean()); lcs.append(lc(idx))
    ci = lambda v: [round(float(np.nanpercentile(v, 2.5)), 3), round(float(np.nanpercentile(v, 97.5)), 3)]
    keep = win != .5; b0, b1 = logit_fit(lr[keep], win[keep]) if keep.sum() >= 4 and len(set(win[keep])) > 1 else (float("nan"), float("nan"))
    order = np.argsort(lr); tern = np.array_split(order, 3)
    buckets = [dict(lr_range=[round(float(lr[t].min()), 3), round(float(lr[t].max()), 3)], n=int(len(t)), win_rate=round(float(win[t].mean()), 3)) for t in tern]
    return dict(n=n, win_rate=round(float(win.mean()), 3), win_rate_ci95=ci(wins), mean_p_y=round(float(pm.mean()), 3), mean_p_y_ci95=ci(pms),
                mean_log_len_ratio_y_over_x=round(float(lr.mean()), 3), frac_y_longer=round(float((lr > 0).mean()), 3),
                lc_win_rate=round(sig(b0), 3) if b0 == b0 else None, lc_win_rate_ci95=ci(lcs), length_slope=round(b1, 3) if b1 == b1 else None,
                bucketed_win_rate_by_length_tercile=buckets, bucketed_lc_win_rate=round(float(np.mean([b["win_rate"] for b in buckets])), 3),
                n_ties=int((win == .5).sum()))


def stage_report(a, briefs, guard=None):
    pages, flags = ok_pages(a)
    rep = dict(policy_x=dict(name=a.name_x, spec=a.policy_x), policy_y=dict(name=a.name_y, spec=a.policy_y), n_briefs=len(briefs),
               page_validity=flags, n_pairs_both_clean=len(pages), temperature=0.7, seed=0, gpu="stock", holdout_guard=guard, judges={})
    for j in a.judges.split(","):
        sc = {r["pair_id"]: r for r in jl(Path(a.out) / "judge" / f"scores_{j}.jsonl") if r.get("p_a_avg") is not None}
        rows = [dict(brief_id=b, p_y=1 - sc[b]["p_a_avg"], lr=math.log(v["y"][2] / v["x"][2]), flip=(sc[b]["p_a_ab"] > .5) != (sc[b]["p_a_ba"] > .5))
                for b, v in pages.items() if b in sc]
        rep["judges"][j] = dict(all=analyze(rows), conf_ge_0_7=analyze(rows, 0.7), order_flip_rate=round(sum(r["flip"] for r in rows) / max(1, len(rows)), 3))
    (Path(a.out) / "report.json").write_text(json.dumps(rep, indent=1))
    md = [f"# E2 eval: {a.name_y} vs {a.name_x}", f"{len(pages)} pairs with both pages clean (of {len(briefs)} briefs). Page validity: {json.dumps(flags)}", ""]
    for j, r in rep["judges"].items():
        for lab, k in (("all pairs", "all"), ("confident (order-avg >=0.7)", "conf_ge_0_7")):
            s = r[k]
            if s.get("n", 0) < 2: md.append(f"- {j} / {lab}: n={s.get('n')}"); continue
            md.append(f"- **{j} / {lab}** n={s['n']}: win rate of {a.name_y} {s['win_rate']} CI{s['win_rate_ci95']}; length-controlled {s['lc_win_rate']} CI{s['lc_win_rate_ci95']}; "
                      f"bucketed LC {s['bucketed_lc_win_rate']}; {a.name_y} longer in {s['frac_y_longer']:.0%} of pairs (slope {s['length_slope']}).")
        md.append(f"  order-flip rate {r['order_flip_rate']}")
    (Path(a.out) / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md)); return 0


def stage_pack(a, briefs):
    pages, _ = ok_pages(a); bmap = {b["id"]: b for b in briefs}
    rng = random.Random(0); ids = sorted(pages); rng.shuffle(ids); ids = ids[: a.pack_n]
    pk = Path(a.out) / "pack"
    if pk.exists(): shutil.move(str(pk), str(pk) + f".old{int(time.time())}")  # never delete
    key, man = {}, []
    for n, bid in enumerate(ids, 1):
        pid = f"pair_{n:02d}"; swap = rng.random() < 0.5
        left, right = ("y", "x") if swap else ("x", "y")
        d = pk / pid; d.mkdir(parents=True)
        shutil.copy(pages[bid][left][1], d / "a.png"); shutil.copy(pages[bid][right][1], d / "b.png")
        b = bmap[bid]
        brief = dict(product=b["product"], audience=b["audience"], tone=b["tone"], sections=b["sections"])
        (d / "brief.json").write_text(json.dumps(brief, indent=1))
        key[pid] = dict(brief_id=bid, a=getattr(a, "name_" + left), b=getattr(a, "name_" + right))
        man.append(dict(pair_id=pid, **brief))
    (pk / "manifest.jsonl").write_text("".join(json.dumps(m) + "\n" for m in man))
    (pk / "README.txt").write_text("Blind pairs of landing-page screenshots (1280x800). For each pair_XX, a.png vs b.png, decide which has the better "
                                   "visual design for the brief in brief.json. Answer: better = a|b, confidence 0.5-1.0, one-line reason.\n")
    (Path(a.out) / "pack_key.json").write_text(json.dumps(key, indent=1))
    print(f"pack: {len(ids)} pairs in {pk}; key in {Path(a.out)/'pack_key.json'} (keep it away from the labeler)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True); ap.add_argument("--policy-x", default="base"); ap.add_argument("--policy-y", required=True)
    ap.add_argument("--name-x", default="base"); ap.add_argument("--name-y", default="tuned")
    ap.add_argument("--judges", default="omnijev-0.8b,imajev-9b"); ap.add_argument("--briefs", default=str(ROOT / "briefs/e2_eval.jsonl"))
    ap.add_argument("--limit", type=int, default=None); ap.add_argument("--max-minutes", type=float, default=25.0)
    ap.add_argument("--pack-n", type=int, default=50); ap.add_argument("--extra-datasets", nargs="*")
    ap.add_argument("--stage", default="all", choices=["gen", "render", "judge", "report", "pack", "all"])
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "command.txt").write_text(" ".join(shlex.quote(x) for x in [sys.executable] + sys.argv) + "\n")
    (Path(a.out) / "config.json").write_text(json.dumps(dict(args=vars(a), gpu="stock", sampling=dict(n=1, temperature=0.7, seed=0, top_p=0.95, max_tokens=6144)), indent=1))
    briefs = [json.loads(l) for l in open(a.briefs) if l.strip()]
    if a.limit: briefs = briefs[: a.limit]
    guard = holdout_guard(a, briefs)
    order = ["gen", "render", "judge", "report", "pack"] if a.stage == "all" else [a.stage]
    fn = dict(gen=stage_gen, render=stage_render, judge=stage_judge, pack=stage_pack)
    for s in order:
        for _ in range(40 if a.stage == "all" else 1):
            rc = stage_report(a, briefs, guard) if s == "report" else fn[s](a, briefs)
            if rc != 3 or a.stage != "all": break
        if rc: return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
