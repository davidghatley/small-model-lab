#!/usr/bin/env python3
"""E1 analysis. Per judge: agreement vs label sources, high-confidence agreement + coverage, calibration (10 bins on
confidence 0.5-1.0, ECE), position bias, single-vs-pairwise consistency, gate.
  .venv/bin/python scripts/analyze_e1.py --pairs runs/E1/pairs --scores runs/E1/scores/*.jsonl --labels runs/E1/labels --out runs/E1
Label sources: by_construction (meta.json intended_better), reference (labels/reference.jsonl: pair_id,better,confidence,rationale),
david (labels/david.jsonl, same shape). Gate: PASS if agreement >= 0.75 on high-confidence pairs (order-averaged P>=0.8 or <=0.2) vs reference.
"""
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

HI = 0.8


def load_jsonl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def acc(pairs):  # list of (pred, label)
    n = len(pairs)
    return {"n": n, "agree": sum(p == l for p, l in pairs) / n if n else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="runs/E1/pairs"); ap.add_argument("--scores", nargs="+", required=True)
    ap.add_argument("--labels", default="runs/E1/labels"); ap.add_argument("--out", default="runs/E1")
    ap.add_argument("--reference", default=None); ap.add_argument("--david", default=None)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.command.txt").write_text(" ".join([sys.executable] + sys.argv) + "\n")
    meta = {}
    for d in Path(a.pairs).iterdir():
        if (d / "meta.json").exists(): meta[d.name] = json.loads((d / "meta.json").read_text())
    labels = {"by_construction": {k: m["intended_better"] for k, m in meta.items() if m.get("intended_better") in ("a", "b")}}
    for name, p in (("reference", a.reference or Path(a.labels) / "reference.jsonl"), ("david", a.david or Path(a.labels) / "david.jsonl")):
        rows = load_jsonl(p)
        if rows: labels[name] = {r["pair_id"]: r["better"] for r in rows if r.get("better") in ("a", "b")}
    ref_conf = {r["pair_id"]: r.get("confidence") for r in load_jsonl(Path(a.labels) / "reference.jsonl")}

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    res = {"labels_available": {k: len(v) for k, v in labels.items()}, "judges": {}}
    for sp in a.scores:
        rows = [r for r in load_jsonl(sp) if r.get("p_a_avg") is not None and r["pair_id"] in meta]
        name = rows[0]["judge"] if rows else Path(sp).stem
        J = {"n_scored": len(rows), "n_errors": sum(bool(r["errors"]) for r in load_jsonl(sp))}
        pred = {r["pair_id"]: ("a" if r["p_a_avg"] >= .5 else "b") for r in rows}
        conf = {r["pair_id"]: max(r["p_a_avg"], 1 - r["p_a_avg"]) for r in rows}
        hi = {k for k, r in ((r["pair_id"], r) for r in rows) if r["p_a_avg"] >= HI or r["p_a_avg"] <= 1 - HI}
        J["agreement"] = {}
        for src, lab in labels.items():
            ids = [k for k in pred if k in lab]
            S = {"overall": acc([(pred[k], lab[k]) for k in ids])}
            S["high_conf"] = {**acc([(pred[k], lab[k]) for k in ids if k in hi]), "coverage": (len([k for k in ids if k in hi]) / len(ids)) if ids else None}
            for grp, key in (("by_source", "source"), ("by_flaw_severity", "flaw_severity")):
                g = defaultdict(list)
                for k in ids: g[str(meta[k].get(key))].append((pred[k], lab[k]))
                S[grp] = {gk: acc(v) for gk, v in sorted(g.items())}
            if src == "reference":
                S["high_conf_by_reference_confidence>=0.8"] = acc([(pred[k], lab[k]) for k in ids if (ref_conf.get(k) or 0) >= .8])
            J["agreement"][src] = S
        # calibration vs the best label source: reference if present else by_construction
        csrc = "reference" if "reference" in labels else "by_construction"
        lab = labels.get(csrc, {}); ids = [k for k in pred if k in lab]
        bins = []
        for i in range(10):
            lo, hi_ = .5 + i * .05, .5 + (i + 1) * .05
            ks = [k for k in ids if lo <= conf[k] < hi_ or (i == 9 and conf[k] == 1.0)]
            bins.append({"lo": lo, "hi": hi_, "n": len(ks), "mean_conf": sum(conf[k] for k in ks) / len(ks) if ks else None,
                         "accuracy": sum(pred[k] == lab[k] for k in ks) / len(ks) if ks else None})
        ece = sum(b["n"] * abs(b["mean_conf"] - b["accuracy"]) for b in bins if b["n"]) / len(ids) if ids else None
        J["calibration"] = {"label_source": csrc, "bins": bins, "ece": ece}
        # position bias
        both = [r for r in rows if r["choice_ab"] and r["choice_ba"]]
        pf = [x for r in both for x in (r["p_first_ab"], r["p_first_ba"])]
        J["position_bias"] = {"n": len(both), "flip_rate": sum(r["choice_ab"] != r["choice_ba"] for r in both) / len(both) if both else None,
                              "mean_p_first_minus_0.5": sum(pf) / len(pf) - .5 if pf else None}
        # single vs pairwise
        sv = [r for r in rows if r.get("p_good_a") is not None and r.get("p_good_b") is not None and r["p_good_a"] != r["p_good_b"]]
        J["single_vs_pairwise"] = {"n": len(sv), "consistency": sum(("a" if r["p_good_a"] > r["p_good_b"] else "b") == pred[r["pair_id"]] for r in sv) / len(sv) if sv else None}
        for src, lab in labels.items():
            ids = [r for r in sv if r["pair_id"] in lab]
            J["single_vs_pairwise"][f"single_agrees_with_{src}"] = acc([("a" if r["p_good_a"] > r["p_good_b"] else "b", lab[r["pair_id"]]) for r in ids])
        lat = [r[k] for r in rows for k in ("lat_ab", "lat_ba") if r.get(k) is not None]
        J["pairwise_latency_mean_s"] = sum(lat) / len(lat) if lat else None
        g = J["agreement"].get("reference", {}).get("high_conf")
        J["gate"] = ("PASS" if g["agree"] >= .75 else "FAIL") if g and g["n"] else "N/A (no reference labels in range)"
        res["judges"][name] = J
        fig, ax = plt.subplots(figsize=(4.5, 4.5)); ax.plot([.5, 1], [.5, 1], "k--", lw=1)
        pts = [(b["mean_conf"], b["accuracy"], b["n"]) for b in bins if b["n"]]
        if pts: ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=[20 + 6 * p[2] for p in pts]); ax.plot([p[0] for p in pts], [p[1] for p in pts], lw=1)
        ax.set(xlabel="order-averaged confidence", ylabel=f"accuracy vs {csrc}", title=f"{name} (ECE {ece:.3f})" if ece is not None else name, xlim=(.5, 1), ylim=(0, 1))
        fig.tight_layout(); fig.savefig(out / f"calibration_{name}.png", dpi=110); plt.close(fig)
    (out / "analysis.json").write_text(json.dumps(res, indent=2))
    f = lambda x: "-" if x is None else f"{x:.3f}"
    ag = lambda d: f"{f(d['agree'])} (n={d['n']})" if d and d["n"] else "-"
    L = ["# E1 analysis", "", f"Labels: {res['labels_available']}", ""]
    L += ["| Judge | agree by-construction | agree reference | hi-conf vs ref (cov) | gate | ECE | flip rate | mean P(first)-0.5 | single~pairwise |", "|---|---|---|---|---|---|---|---|---|"]
    for n, J in res["judges"].items():
        A = J["agreement"]; hc = A.get("reference", {}).get("high_conf")
        L.append(f"| {n} | {ag(A.get('by_construction', {}).get('overall'))} | {ag(A.get('reference', {}).get('overall'))} | {ag(hc)} ({f(hc['coverage']) if hc else '-'}) | {J['gate']} | {f(J['calibration']['ece'])} | {f(J['position_bias']['flip_rate'])} | {f(J['position_bias']['mean_p_first_minus_0.5'])} | {f(J['single_vs_pairwise']['consistency'])} |")
    for n, J in res["judges"].items():
        L += ["", f"## {n}", f"scored {J['n_scored']} pairs, {J['n_errors']} rows with errors; mean pairwise latency {f(J['pairwise_latency_mean_s'])} s", ""]
        for src, S in J["agreement"].items():
            L.append(f"- **{src}**: overall {ag(S['overall'])}; high-conf {ag(S['high_conf'])}, coverage {f(S['high_conf']['coverage'])}")
            for grp in ("by_source", "by_flaw_severity"):
                L.append(f"  - {grp}: " + ", ".join(f"{k} {ag(v)}" for k, v in S[grp].items()))
        L += ["", f"Calibration vs {J['calibration']['label_source']} (ECE {f(J['calibration']['ece'])}); plot `calibration_{n}.png`", "", "| bin | n | mean conf | accuracy |", "|---|---|---|---|"]
        L += [f"| {b['lo']:.2f}-{b['hi']:.2f} | {b['n']} | {f(b['mean_conf'])} | {f(b['accuracy'])} |" for b in J["calibration"]["bins"]]
    (out / "analysis.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:8 + len(res['judges'])]))


if __name__ == "__main__":
    main()
