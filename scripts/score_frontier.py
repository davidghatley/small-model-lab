"""Unblind the frontier (Opus) labels for an E2 eval pack and report tuned-vs-base win rate with a bootstrap CI.
Usage: .venv/bin/python -I scripts/score_frontier.py runs/E2/eval/<name>  (writes frontier/report.{md,json})"""
import json, sys, pathlib, random
E = pathlib.Path(sys.argv[1]); key = json.load(open(E / "pack_key.json"))
names = {v for k in key.values() for v in (k["a"], k["b"])}; assert len(names) == 2 and "base" in names, names
y = (names - {"base"}).pop()
labs = [json.loads(l) for f in sorted((E / "frontier").glob("labels_*.jsonl")) for l in open(f) if l.strip()]
rows = []
for r in labs:
    k = key[r["pair_id"]]; w = 0.5 if r["better"] == "tie" else float(k[r["better"]] == y)
    rows.append(dict(pair_id=r["pair_id"], brief_id=k["brief_id"], win_y=w, conf=r["confidence"]))
rng = random.Random(0); n = len(rows); mean = lambda v: sum(v) / len(v)
boots = sorted(mean([rows[rng.randrange(n)]["win_y"] for _ in range(n)]) for _ in range(2000))
conf = [r for r in rows if r["conf"] >= 0.7]
out = dict(n=n, policy_y=y, win_rate_y=round(mean([r["win_y"] for r in rows]), 3), ci95=[boots[49], boots[1949]],
           n_conf_ge_0_7=len(conf), win_rate_conf=round(mean([r["win_y"] for r in conf]), 3) if conf else None, rows=rows)
json.dump(out, open(E / "frontier/report.json", "w"), indent=1)
md = f"# Frontier (Opus, blind) judge: {y} vs base\n\nn={n}: {y} win rate {out['win_rate_y']} 95% CI {out['ci95']} (bootstrap 2000, seed 0, ties=0.5). Confident (>=0.7) n={len(conf)}: {out['win_rate_conf']}.\n"
open(E / "frontier/report.md", "w").write(md); print(md)
