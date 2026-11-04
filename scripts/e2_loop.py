#!/usr/bin/env python3
"""E2 design loop: one resumable round. Run with the repo venv (.venv/bin/python). GPU stages call gpu_run themselves.

  .venv/bin/python scripts/e2_loop.py --round 0 --stage all --out runs/E2/round0/
  .venv/bin/python scripts/e2_loop.py --round 0 --stage gen --max-minutes 25 --out runs/E2/round0/   # one chunk; exit 3 = not finished, call again

Stages: gen -> render -> judge -> select -> train -> summary ('all' loops each stage in <=--max-minutes chunks until complete).
Policy: round 0 = base AWQ; round N>0 samples from the AWQ base + the LoRA trained in round N-1 (default <prev round>/train/adapter, override
--policy-adapter). The train stage of round N continues from that same adapter (--adapter-in), so "round k LoRA" = what round k-1 produced.
Layout in --out: pages/ (gen.jsonl, render.jsonl, s<k>.html/.png/.raw.txt), judge/ (manifest.jsonl, scores_<judge>.jsonl), select/ (dpo.jsonl,
stats.json), train/ (adapter/, checkpoints/, train_summary.json; or --train-out), stages/<stage>/{config.json,command.txt,chunks.jsonl,chunk<n>.log}, summary.json.
Exit codes: 0 stage(s) complete, 3 stage incomplete (time budget), other = failure.
"""
import argparse, collections, datetime, json, os, platform, shlex, statistics, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
GPU_RUN = os.path.expanduser("~/anime-pipeline/tools/gpu_run")
AWQ = "/mnt/work/models/qwen2.5-coder-7b-instruct-awq"
NEED = dict(gen=11000, judge=6500, train=9500)
PY, PYV, PYU = str(ROOT / ".venv/bin/python"), str(ROOT / ".venv-vllm/bin/python"), str(ROOT / ".venv-unsloth/bin/python")
STAGES = ["gen", "render", "judge", "select", "train", "summary"]


def jl(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


class Paths:
    def __init__(s, a):
        s.out = Path(a.out); s.pages = s.out / "pages"; s.judge = s.out / "judge"; s.sel = s.out / "select"; s.train = Path(a.train_out) if a.train_out else s.out / "train"
        s.scores = s.judge / f"scores_{a.judge}.jsonl"; s.manifest = s.judge / "manifest.jsonl"; s.dpo = s.sel / "dpo.jsonl"


def vers():
    v = dict(python=platform.python_version())
    for name, py in (("main", PY), ("vllm", PYV), ("unsloth", PYU)):
        r = subprocess.run([py, "-c", {"main": "import transformers as t;print(t.__version__)", "vllm": "import vllm;print(vllm.__version__)",
                                       "unsloth": "import trl,unsloth;print('trl',trl.__version__,'unsloth',unsloth.__version__)"}[name]],
                           capture_output=True, text=True)
        v[name] = (r.stdout.strip().splitlines() or ["?"])[-1]
    return v


def run_chunk(a, P, stage, cmd, need=0):
    """Run one stage chunk (through gpu_run if need), record wall time + whole-GPU VRAM peak. Returns rc."""
    sd = P.out / "stages" / stage; sd.mkdir(parents=True, exist_ok=True)
    full = ([GPU_RUN, "--free", "--need", str(need)] if need and not a.no_gpu_run else []) + cmd
    n = len(jl(sd / "chunks.jsonl"))
    (sd / "command.txt").write_text(" ".join(shlex.quote(x) for x in full) + "\n")
    (sd / "config.json").write_text(json.dumps(dict(args=vars(a), stage=stage, versions=vers(), gpu="stock", gpu_run_need_mib=need), indent=1))
    peak = [0]; stop = threading.Event()

    def poll():
        while not stop.is_set():
            try:
                u = int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.split()[0])
                peak[0] = max(peak[0], u)
            except Exception: pass
            stop.wait(1.5)
    th = threading.Thread(target=poll, daemon=True)
    t0 = time.time(); th.start()
    print(f"[{stage}] chunk {n}: {' '.join(full)[:200]}", flush=True)
    with open(sd / f"chunk{n}.log", "w") as lg:
        rc = subprocess.run(full, stdout=lg, stderr=subprocess.STDOUT, cwd=ROOT).returncode
    stop.set(); th.join(2)
    rec = dict(chunk=n, rc=rc, wall_s=round(time.time() - t0, 1), peak_gpu_used_mib=peak[0], t=datetime.datetime.now().isoformat(timespec="seconds"))
    with open(sd / "chunks.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    print(f"[{stage}] rc={rc} wall={rec['wall_s']}s peak_gpu={peak[0]} MiB (log {sd}/chunk{n}.log)", flush=True)
    return rc


def load_briefs(a):
    b = [json.loads(l) for l in open(a.briefs) if l.strip()]
    return b[: a.limit] if a.limit else b


def policy_adapter(a):
    if a.policy_adapter:
        return None if a.policy_adapter == "none" else a.policy_adapter
    if a.round > 0:
        p = Path(a.out).resolve().parent / f"round{a.round-1}/train/adapter"
        if not p.exists(): sys.exit(f"round {a.round} needs the round-{a.round-1} adapter at {p} (or --policy-adapter)")
        return str(p)
    return None


# ---------------------------------------------------------------- stages
def gen_done(a, P):
    got = {(r["brief_id"], r["k"]) for r in jl(P.pages / "gen.jsonl")}
    return len(got), len(load_briefs(a)) * a.n_samples


def stage_gen(a, P):
    have, want = gen_done(a, P)
    if have >= want: return 0
    cmd = [PYV, "scripts/gen_pages.py", "--briefs", a.briefs, "--n-samples", str(a.n_samples), "--temperature", str(a.temperature),
           "--seed", str(a.seed), "--max-tokens", str(a.gen_max_tokens), "--out", str(P.pages), "--max-minutes", str(a.max_minutes)]
    if a.limit: cmd += ["--limit", str(a.limit)]
    ad = policy_adapter(a)
    if ad: cmd += ["--adapter", ad]
    (P.pages).mkdir(parents=True, exist_ok=True)
    run_chunk(a, P, "gen", cmd, NEED["gen"])
    have, want = gen_done(a, P)
    return 0 if have >= want else 3


def stage_render(a, P):
    nrender = len({(r["brief_id"], r["k"]) for r in jl(P.pages / "render.jsonl")})
    if nrender >= len(jl(P.pages / "gen.jsonl")) > 0: return 0
    run_chunk(a, P, "render", [PY, "scripts/e2_render.py", "--pages", str(P.pages), "--workers", str(a.render_workers), "--max-minutes", str(a.max_minutes)])
    nrender = len({(r["brief_id"], r["k"]) for r in jl(P.pages / "render.jsonl")})
    return 0 if nrender >= len(jl(P.pages / "gen.jsonl")) else 3


def clean_samples(P):
    """{brief_id: [k,...]} samples that are cleanly extracted, rendered ok and not blank; plus counts of what was flagged."""
    gen = {(r["brief_id"], r["k"]): r for r in jl(P.pages / "gen.jsonl")}
    ren = {(r["brief_id"], r["k"]): r for r in jl(P.pages / "render.jsonl")}
    ok, flags = collections.defaultdict(list), collections.Counter()
    for key, g in sorted(gen.items()):
        r = ren.get(key)
        if not g["extracted_cleanly"]: flags["unclean_or_truncated"] += 1
        elif r is None: flags["not_rendered"] += 1
        elif not r["ok"]: flags["render_failed"] += 1
        elif r["blank"]: flags["blank"] += 1
        else: ok[key[0]].append(key[1])
    return ok, flags, gen


def build_manifest(a, P):
    ok, flags, _ = clean_samples(P)
    P.judge.mkdir(parents=True, exist_ok=True)
    rows = []
    for bid, ks in sorted(ok.items()):
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                rows.append(dict(pair_id=f"{bid}|s{ks[i]}|s{ks[j]}", brief_id=bid, i=ks[i], j=ks[j],
                                 a_png=str((P.pages / bid / f"s{ks[i]}.png").resolve()), b_png=str((P.pages / bid / f"s{ks[j]}.png").resolve())))
    P.manifest.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows, flags


def stage_judge(a, P):
    rows, _ = build_manifest(a, P)
    scored = {r["pair_id"] for r in jl(P.scores) if r.get("p_a_avg") is not None}
    if all(r["pair_id"] in scored for r in rows): return 0
    run_chunk(a, P, "judge", [PY, "scripts/e2_judge.py", "--judge", a.judge, "--manifest", str(P.manifest), "--out", str(P.scores),
                              "--max-minutes", str(a.max_minutes)], NEED["judge"])
    scored = {r["pair_id"] for r in jl(P.scores) if r.get("p_a_avg") is not None}
    return 0 if all(r["pair_id"] in scored for r in rows) else 3


def sccs(nodes, edges):
    """Tarjan SCC; edges = {u: set(v)} (winner -> loser)."""
    idx, low, st, on, out, c = {}, {}, [], set(), [], [0]
    def go(v):
        idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
        for w in edges.get(v, ()):
            if w not in idx: go(w); low[v] = min(low[v], low[w])
            elif w in on: low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v: break
            out.append(comp)
    for v in nodes:
        if v not in idx: go(v)
    return out


def stage_select(a, P):
    from transformers import AutoTokenizer
    import gen_pages as G
    tok = AutoTokenizer.from_pretrained(AWQ)
    tpl = G.load_template(a.prompt)
    briefs = {b["id"]: b for b in load_briefs(a)}
    ok, flags, gen = clean_samples(P)
    rows, _ = build_manifest(a, P)
    sc = {r["pair_id"]: r for r in jl(P.scores)}
    P.sel.mkdir(parents=True, exist_ok=True)
    cand, n_scored, n_unscored = [], 0, 0
    allpairs = []  # every scored pair, for the length-bias diagnostics
    for r in rows:
        s = sc.get(r["pair_id"])
        if not s or s.get("p_a_avg") is None: n_unscored += 1; continue
        n_scored += 1
        p = s["p_a_avg"]; conf = max(p, 1 - p)
        w, l = (r["i"], r["j"]) if p > 0.5 else (r["j"], r["i"])
        pc = p if p > 0.5 else 1 - p  # P(chosen better), order-averaged
        d = dict(brief_id=r["brief_id"], w=w, l=l, p=pc, conf=conf, flip=(s["p_a_ab"] > .5) != (s["p_a_ba"] > .5))
        allpairs.append(d)
        if conf >= a.conf: cand.append(d)
    # drop cycles per brief: every kept edge whose endpoints share a strongly connected component (>1 node)
    byb = collections.defaultdict(list)
    for d in cand: byb[d["brief_id"]].append(d)
    kept, dropped_cycle = [], 0
    for bid, ds in byb.items():
        edges = collections.defaultdict(set)
        for d in ds: edges[d["w"]].add(d["l"])
        comp = {}
        for ci, c in enumerate(sccs(sorted({d["w"] for d in ds} | {d["l"] for d in ds}), edges)):
            if len(c) > 1:
                for v in c: comp[v] = ci
        for d in ds:
            if d["w"] in comp and comp.get(d["l"]) == comp[d["w"]]: dropped_cycle += 1
            else: kept.append(d)
    out_rows, dropped_len = [], 0
    for d in sorted(kept, key=lambda d: (d["brief_id"], d["w"], d["l"])):
        bid = d["brief_id"]
        gw, gl = gen[(bid, d["w"])], gen[(bid, d["l"])]
        if gw["prompt_tokens"] + max(gw["tokens"], gl["tokens"]) + 1 > a.max_length: dropped_len += 1; continue
        msgs = G.build_messages(tpl, briefs[bid])
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        assert len(tok(prompt, add_special_tokens=False)["input_ids"]) == gw["prompt_tokens"], "prompt tokenization differs from the gen server's"
        ch = (P.pages / bid / f"s{d['w']}.raw.txt").read_text(); rj = (P.pages / bid / f"s{d['l']}.raw.txt").read_text()
        out_rows.append(dict(prompt=prompt, chosen=ch, rejected=rj, brief_id=bid, p=round(d["p"], 4), round=a.round,
                             chosen_k=d["w"], rejected_k=d["l"], chosen_tokens=gw["tokens"], rejected_tokens=gl["tokens"],
                             chosen_chars=len(ch), rejected_chars=len(rj)))
    P.dpo.write_text("".join(json.dumps(r) + "\n" for r in out_rows))

    def tl(w, l): return gen[(w[0], w[1])]["tokens"], gen[(l[0], l[1])]["tokens"]
    def lenstats(pairs):
        if not pairs: return None
        cw = [gen[(d["brief_id"], d["w"])]["tokens"] for d in pairs]; cl = [gen[(d["brief_id"], d["l"])]["tokens"] for d in pairs]
        diff = [x - y for x, y in zip(cw, cl)]
        return dict(n=len(pairs), mean_tokens_chosen=round(statistics.mean(cw), 1), mean_tokens_rejected=round(statistics.mean(cl), 1),
                    median_diff=statistics.median(diff), mean_diff=round(statistics.mean(diff), 1),
                    frac_chosen_longer=round(sum(x > 0 for x in diff) / len(diff), 3), frac_equal=round(sum(x == 0 for x in diff) / len(diff), 3))
    per = collections.Counter(r["brief_id"] for r in out_rows)
    final_keys = {(r["brief_id"], r["chosen_k"], r["rejected_k"]) for r in out_rows}
    nb = len(ok)
    stats = dict(round=a.round, conf_threshold=a.conf, judge=a.judge, briefs_in_set=len(load_briefs(a)), briefs_with_2plus_clean=sum(len(v) >= 2 for v in ok.values()),
                 sample_flags=dict(flags), clean_samples=sum(len(v) for v in ok.values()), pairs_scored=n_scored, pairs_unscored=n_unscored,
                 pairs_conf_ge_thr=len(cand), dropped_cycle=dropped_cycle, dropped_too_long=dropped_len, pairs_kept=len(out_rows),
                 order_flip_rate_all_scored=round(sum(d["flip"] for d in allpairs) / max(1, len(allpairs)), 3),
                 per_brief_pair_count_hist=dict(sorted(collections.Counter(per.get(b, 0) for b in briefs).items())),
                 briefs_with_pairs=len(per), per_brief_pairs=dict(sorted(per.items())),
                 length_all_scored_pairs_judge_preferred_vs_other=lenstats(allpairs), length_kept_chosen_vs_rejected=lenstats(
                     [d for d in kept if (d["brief_id"], d["w"], d["l"]) in final_keys]),
                 note="length in completion tokens; frac_chosen_longer ~0.5 = no length preference")
    (P.sel / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps({k: v for k, v in stats.items() if k not in ("per_brief_pairs",)}, indent=1)[:2500])
    return 0


def stage_train(a, P):
    if (P.train / "train_summary.json").exists(): return 0
    if not P.dpo.exists() or not P.dpo.read_text().strip(): sys.exit("no DPO dataset (run select; or zero pairs kept)")
    cmd = [PYU, "scripts/e2_dpo.py", "--dataset", str(P.dpo), "--out", str(P.train), "--max-minutes", str(a.max_minutes),
           "--grad-accum", str(a.grad_accum), "--save-steps", str(a.save_steps), "--seed", str(a.seed)]
    if a.lr is not None: cmd += ["--lr", str(a.lr)]
    if a.beta is not None: cmd += ["--beta", str(a.beta)]
    if a.epochs is not None: cmd += ["--epochs", str(a.epochs)]
    if a.eval_frac: cmd += ["--eval-frac", str(a.eval_frac)]
    if a.max_steps > 0: cmd += ["--max-steps", str(a.max_steps)]
    ad = a.adapter_in or policy_adapter(a)
    if ad: cmd += ["--adapter-in", ad]
    run_chunk(a, P, "train" if not a.train_out else "train_" + Path(a.train_out).name, cmd, NEED["train"])
    return 0 if (P.train / "train_summary.json").exists() else 3


def stage_summary(a, P):
    S = dict(round=a.round, out=str(P.out), gpu="stock", versions=vers(), written=datetime.datetime.now().isoformat(timespec="seconds"))
    stg = {}
    for s in ("gen", "render", "judge", "select", "train"):
        ch = jl(P.out / "stages" / s / "chunks.jsonl")
        if ch: stg[s] = dict(chunks=len(ch), wall_s=round(sum(c["wall_s"] for c in ch), 1), peak_gpu_used_mib=max(c["peak_gpu_used_mib"] for c in ch))
    S["stages"] = stg
    S["gen"] = (json.loads((P.pages / "summary.json").read_text()) if (P.pages / "summary.json").exists() else None)
    st = P.sel / "stats.json"
    if st.exists():
        x = json.loads(st.read_text())
        S["select"] = {k: x[k] for k in ("pairs_scored", "pairs_conf_ge_thr", "dropped_cycle", "dropped_too_long", "pairs_kept", "briefs_with_pairs",
                                         "clean_samples", "sample_flags", "length_kept_chosen_vs_rejected")}
    ts = P.train / "train_summary.json"
    if ts.exists(): S["train"] = json.loads(ts.read_text())
    try: S["policy_adapter"] = policy_adapter(a)
    except SystemExit: S["policy_adapter"] = "missing"
    (P.out / "summary.json").write_text(json.dumps(S, indent=1))
    print(json.dumps(S, indent=1)[:3000])
    return 0


FN = dict(gen=stage_gen, render=stage_render, judge=stage_judge, select=stage_select, train=stage_train, summary=stage_summary)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--round", type=int, required=True); ap.add_argument("--stage", required=True, choices=STAGES + ["all"])
    ap.add_argument("--out", required=True); ap.add_argument("--briefs", default=str(ROOT / "briefs/e2_train.jsonl"))
    ap.add_argument("--limit", type=int, default=None, help="first N briefs")
    ap.add_argument("--n-samples", type=int, default=4); ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--gen-max-tokens", type=int, default=6144)
    ap.add_argument("--max-minutes", type=float, default=25.0, help="per GPU call; keep < 30 (house rule)")
    ap.add_argument("--judge", default="omnijev-0.8b"); ap.add_argument("--conf", type=float, default=0.7)
    ap.add_argument("--max-length", type=int, default=4096, help="drop pairs whose prompt+longer completion exceeds this")
    ap.add_argument("--prompt", default=str(ROOT / "scripts/prompts/coder_page.txt"))
    ap.add_argument("--policy-adapter", default=None, help="LoRA dir to sample from ('none' = base); default prev round's train/adapter")
    ap.add_argument("--adapter-in", default=None, help="train: adapter to continue from (default = policy adapter)")
    ap.add_argument("--max-steps", type=int, default=-1); ap.add_argument("--grad-accum", type=int, default=16); ap.add_argument("--save-steps", type=int, default=5)
    ap.add_argument("--lr", type=float, default=None, help="train: learning rate (default: e2_dpo.py's 5e-6)")
    ap.add_argument("--beta", type=float, default=None, help="train: DPO beta (default 0.1)")
    ap.add_argument("--epochs", type=float, default=None, help="train: epochs (default 1)")
    ap.add_argument("--eval-frac", type=float, default=0.0, help="train: fraction of briefs held out for one eval before and one after training")
    ap.add_argument("--train-out", default=None, help="train: output dir (default <out>/train); summary reads it too")
    ap.add_argument("--render-workers", type=int, default=6); ap.add_argument("--no-gpu-run", action="store_true")
    a = ap.parse_args()
    a.out = str(Path(a.out)); P = Paths(a); P.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    stages = [s for s in STAGES] if a.stage == "all" else [a.stage]
    for s in stages:
        for attempt in range(40):
            rc = FN[s](a, P)
            if rc != 3 or a.stage != "all": break
            print(f"[{s}] incomplete, calling again", flush=True)
        if rc != 0:
            print(f"stage {s} exit {rc}"); stage_summary(a, P) if s != "summary" else None; return rc
    if a.stage != "summary": stage_summary(a, P)
    print(f"done in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
