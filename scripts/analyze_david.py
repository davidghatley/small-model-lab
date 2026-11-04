"""E1: compare David's 30 hand labels with the planted truth, the reference labeler and each judge.
Usage: .venv/bin/python -I scripts/analyze_david.py  (writes runs/E1/labels/david_analysis.{md,json})"""
import json, pathlib
R = pathlib.Path(__file__).resolve().parent.parent / "runs/E1"
ids = json.load(open(R / "labels/david_subset.json"))
dav = {}
for i, pid in enumerate(ids, 1):
    d = json.load(open(R / f"labels/david_raw/labels/p{i:02d}.json"))
    dav[pid] = {"page": f"p{i:02d}", "better": d["better"], "strength": d.get("strength"), "note": d.get("note", "")}
ref = {r["pair_id"]: r for r in map(json.loads, open(R / "labels/reference.jsonl"))}
meta = {pid: json.load(open(R / f"pairs/{pid}/meta.json")) for pid in ids}
judges = ["omnijev-0.8b", "omnijev-4b", "rsi-jev-4b", "imajev-9b"]
sc = {j: {r["pair_id"]: r for r in map(json.loads, open(R / f"scores/{j}.jsonl"))} for j in judges}

def agree(rows, other):  # rows: pids with a David non-tie label and an `other` pick
    n = k = 0
    for pid in rows:
        o = other(pid)
        if o is None or dav[pid]["better"] == "tie": continue
        n += 1; k += dav[pid]["better"] == o
    return k, n

out = {"n_labels": len(dav), "ties": sum(v["better"] == "tie" for v in dav.values()), "by_source": {}, "rows": []}
srcs = {"fg": "graded (planted flaw)", "fh": "hard (frontier v1 vs v2)", "sm": "coder vs coder"}
others = {"truth/author": lambda p: meta[p].get("intended_better") or meta[p].get("author_pick_side"),
          "reference": lambda p: ref[p]["better"] if p in ref else None}
for j in judges:
    others[j] = (lambda jj: lambda p: ("a" if sc[jj][p]["p_a_avg"] > .5 else "b") if p in sc[jj] else None)(j)
    others[j + " conf>=0.7"] = (lambda jj: lambda p: (("a" if sc[jj][p]["p_a_avg"] > .5 else "b") if abs(sc[jj][p]["p_a_avg"] - .5) >= .2 else None) if p in sc[jj] else None)(j)
for s in ["all", "fg", "fh", "sm"]:
    pids = [p for p in ids if s == "all" or p.startswith(s)]
    res = {}
    for name, f in others.items():
        k, n = agree(pids, f); res[name] = [k, n]
    clear = [p for p in pids if dav[p]["strength"] == "clear"]
    res["reference (David clear only)"] = list(agree(clear, others["reference"]))
    res["omnijev-0.8b (David clear only)"] = list(agree(clear, others["omnijev-0.8b"]))
    out["by_source"][s] = {"n": len(pids), "ties": sum(dav[p]["better"] == "tie" for p in pids), "agree": res}
for p in ids:
    out["rows"].append({"pair": p, **dav[p], "truth_or_author": others["truth/author"](p),
                        "reference": others["reference"](p), "ref_conf": ref.get(p, {}).get("confidence"),
                        **{j: round(sc[j][p]["p_a_avg"], 3) for j in judges if p in sc[j]}})
json.dump(out, open(R / "labels/david_analysis.json", "w"), indent=1)
L = ["# E1: David's 30 hand labels vs everything else", "", "Agreement = k/n over pairs where David did not say tie and the other side gave a pick. Judge pick = order-averaged P(a) > 0.5; 'conf>=0.7' = only pairs with |P-0.5| >= 0.2.", ""]
cols = list(out["by_source"]["all"]["agree"])
L.append("| vs | " + " | ".join(f"{s} (n={out['by_source'][s]['n']}, ties {out['by_source'][s]['ties']})" for s in out["by_source"]) + " |")
L.append("|---" * (len(out["by_source"]) + 1) + "|")
for c in cols:
    L.append(f"| {c} | " + " | ".join(("%d/%d" % tuple(out["by_source"][s]["agree"][c])) if out["by_source"][s]["agree"][c][1] else "—" for s in out["by_source"]) + " |")
L += ["", "## Per pair", "", "| page | pair | David | strength | truth/author | ref (conf) | omni-0.8b P(a) | imajev-9b P(a) | note |", "|---|---|---|---|---|---|---|---|---|"]
for r in out["rows"]:
    L.append(f"| {r['page']} | {r['pair']} | {r['better']} | {r['strength']} | {r['truth_or_author'] or ''} | {r['reference']} ({r['ref_conf']}) | {r.get('omnijev-0.8b')} | {r.get('imajev-9b')} | {r['note']} |")
open(R / "labels/david_analysis.md", "w").write("\n".join(L) + "\n")
print("\n".join(L[:len(cols) + 6]))
