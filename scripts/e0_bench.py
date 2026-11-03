#!/usr/bin/env python3
"""E0 benchmark: latency / VRAM / pairwise ability of local vision 'System One' judges.

Run through the GPU gate, e.g.
  ~/anime-pipeline/tools/gpu_run --free --need 6000 .venv/bin/python scripts/e0_bench.py \
      --judge imajev-2b --model-path /mnt/models/llm/imajev-2b --out runs/E0/bench/imajev-2b/
Adapters (one small class each): imajev (in-process torch), rsijev (in-process Decider),
omnijev (spawns `flide serve` or `qev serve` and talks Jev HTTP). Each adapter exposes
ask(images, state, questions) -> Jev-style response dict {"answers": {id: {...}}}.
"""
import argparse, base64, json, os, platform, random, shutil, socket, statistics, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "runs/E0/fixtures"
IMAJEV_SRC = Path(os.environ.get("IMAJEV_SRC", "/mnt/models/llm/_src/imajev"))

# ---- questions (Jev typed-decision shape) --------------------------------------------------
Q_SINGLE = {
    "good": {"type": "noul", "instructions": "This web page screenshot has a well-designed, polished, professional visual design."},
    "rating": {"type": "score", "instructions": "Rate the visual design quality of this web page screenshot.",
               "criteria": ["terrible", "poor", "mediocre", "good", "excellent"]},
}
Q_PAIR = {
    "better": {"type": "choice", "instructions": "Which web page screenshot has the better visual design, the first image or the second image?",
               "criteria": {"first": "the first image has the better design", "second": "the second image has the better design"}},
}
STATE_SINGLE = "Judge the visual design of one web page screenshot."
STATE_PAIR = "Compare the visual design of two web page screenshots: image 1 is the first, image 2 is the second."


# ---- adapters --------------------------------------------------------------------------------
class Imajev:
    """mohit67890/imajev-{2b,4b}: PEFT adapter + decision readout over a Qwen3.5 base in <model-path>/base."""
    supports_pairwise = True

    def __init__(self, a):
        import torch
        sys.path[:0] = [str(IMAJEV_SRC / "src"), str(IMAJEV_SRC / "scripts"), str(IMAJEV_SRC / "scripts/playground")]
        import server as S  # imajev's own playground module
        from vision_decision.images import load_image_bytes
        from vision_decision.jev_api import to_response
        from vision_decision.calibration import TemperatureCalibrator
        self.S, self.load_image_bytes, self.to_response = S, load_image_bytes, to_response
        mp = Path(a.model_path)
        bundle = mp / "bundle.json"
        bundle.write_text(json.dumps({"repo": "base", "path": str(mp / "base")}))
        self.backend = S.TorchBackend(str(bundle), str(mp), rotations=a.rotations, fast=a.fast)
        cal = mp / "calibration.json"
        self.cal = TemperatureCalibrator.load(cal) if cal.exists() and not a.no_calibration else None

    def ask(self, images, state, questions):
        loaded = [self.load_image_bytes(Path(p).read_bytes()) for p in images]
        imgs = [i for i, _ in loaded]
        req, plan = self.S.compile_payload({"state": state, "questions": questions}, getattr(self.backend, "max_options", 254))
        res, usage = self.backend.score(imgs, req)
        if self.cal:
            res = [self.cal.calibrate_result(r, f.type, len(r.scores) - 1, image=True, photo_only=False) for f, r in zip(req.fields, res)]
        return {**self.to_response(req, res, model=self.backend.model, plan=plan), "usage": usage}


class RsiJev:
    """shgao/rsi-jev-v6.1-vl-4b via `rsijev.Decider` (pip install rsi-jev[fast,vision]). UNTESTED."""
    supports_pairwise = True  # card: up to 4 images; verified at run time (failure is recorded)

    def __init__(self, a):
        from rsijev import Decider
        self.d = Decider(a.model_path if a.model_path else "v6.1-vl-4b", effort=a.effort) if a.effort else Decider(a.model_path)

    def ask(self, images, state, questions):
        marks = " ".join("<image>" for _ in images)
        out = self.d.decide(f"{state}\n{marks}", questions, images=[str(p) for p in images])
        return out if isinstance(out, dict) and "answers" in out else {"answers": out}


class OmniJev:
    """OmniJev/OneJev1.6-{0.8B,4B}: spawns `flide serve` (safetensors) or `qev serve --gguf` (--quant gguf) and POSTs
    /v1/systemone with base64 `media`. UNTESTED. VRAM is nvidia-smi only (torch runs in the child process)."""
    supports_pairwise = True  # not documented; tried at run time, failure is recorded

    def __init__(self, a):
        import requests
        self.requests = requests
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        if a.server_cmd:
            cmd = a.server_cmd.format(model_path=a.model_path, port=self.port)
        elif a.quant and a.quant.startswith("gguf"):
            cmd = f"qev serve --gguf {a.model_path} --port {self.port}"
        else:
            cmd = f"flide serve --model {a.model_path} --port {self.port}"
        exe = shutil.which(cmd.split()[0]) or str(ROOT / ".venv/bin" / cmd.split()[0])
        self.cmd = [exe] + cmd.split()[1:]
        self.proc = subprocess.Popen(self.cmd, stdout=open(Path(a.out) / "server.log", "w"), stderr=subprocess.STDOUT)
        self.child_pids = [self.proc.pid]
        self.url = f"http://127.0.0.1:{self.port}/v1/systemone"
        for _ in range(600):
            if self.proc.poll() is not None:
                raise RuntimeError(f"server exited {self.proc.returncode}; see server.log")
            try:
                socket.create_connection(("127.0.0.1", self.port), 1).close(); break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError("server did not come up in 600 s")

    def ask(self, images, state, questions):
        media = [{"type": "image", "data": "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()} for p in images]
        screen = " ".join(f"<image:{i+1}>" for i in range(len(images)))
        r = self.requests.post(self.url, json={"state": {"task": state, "screen": screen}, "media": media, "questions": questions}, timeout=300)
        r.raise_for_status()
        return r.json()

    def close(self):
        self.proc.terminate()  # we started it
        try: self.proc.wait(30)
        except subprocess.TimeoutExpired: self.proc.kill()


ADAPTERS = {"imajev": Imajev, "rsijev": RsiJev, "omnijev": OmniJev}


def family(judge):
    j = judge.lower()
    for k, names in (("imajev", ("imajev",)), ("rsijev", ("rsi",)), ("omnijev", ("omni", "onejev"))):
        if any(n in j for n in names): return k
    sys.exit(f"cannot infer adapter from --judge {judge!r}; pass --adapter")


# ---- measurement helpers ---------------------------------------------------------------------
class SmiPeak(threading.Thread):
    """Polls nvidia-smi: peak per-process MiB for our pids, and peak whole-GPU used MiB."""
    def __init__(self, pids):
        super().__init__(daemon=True); self.pids = set(pids); self.proc_peak = 0; self.gpu_peak = 0; self.stop = threading.Event()

    def run(self):
        while not self.stop.is_set():
            try:
                out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True, timeout=5).stdout
                mine = 0
                for line in out.strip().splitlines():
                    pid, mib = [x.strip() for x in line.split(",")]
                    if int(pid) in self.pids: mine += int(mib)
                self.proc_peak = max(self.proc_peak, mine)
                tot = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True, timeout=5).stdout.split()[0]
                self.gpu_peak = max(self.gpu_peak, int(tot))
            except Exception:
                pass
            self.stop.wait(0.2)


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summarize(xs):
    return {"n": len(xs), "p50_ms": pct(xs, .5) * 1000, "p90_ms": pct(xs, .9) * 1000, "mean_ms": statistics.mean(xs) * 1000} if xs else None


def p_yes(ans):
    return ans.get("noul") if isinstance(ans, dict) else None


def p_first(ans):
    pr = (ans or {}).get("probabilities") or {}
    return pr.get("first")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", required=True, help="name, e.g. imajev-2b (also names the output dir default)")
    ap.add_argument("--model-path", required=True, help="dir under /mnt/models/llm/<name>/ (or HF id for rsijev)")
    ap.add_argument("--adapter", choices=sorted(ADAPTERS), help="override adapter inferred from --judge")
    ap.add_argument("--quant", default=None, help="label for quant used (bf16 default); 'gguf*' makes omnijev use qev serve")
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rotations", type=int, default=1, help="imajev: option orders averaged per question")
    ap.add_argument("--fast", action="store_true", help="imajev: CUDA-graph fast path")
    ap.add_argument("--no-calibration", action="store_true", help="imajev: skip calibration.json")
    ap.add_argument("--effort", default=None, help="rsijev: low|medium|high|auto")
    ap.add_argument("--server-cmd", default=None, help="omnijev: override server command, {model_path} and {port} substituted")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    log = open(out / "run.log", "w")
    def L(*m):
        s = time.strftime("%H:%M:%S ") + " ".join(map(str, m)); print(s, flush=True); log.write(s + "\n"); log.flush()

    random.seed(a.seed)
    try:
        import numpy as np; np.random.seed(a.seed)
    except ImportError: pass
    import torch
    torch.manual_seed(a.seed); torch.cuda.manual_seed_all(a.seed)

    cmdline = " ".join([sys.executable] + sys.argv)
    (out / "command.txt").write_text(cmdline + "\n")
    import importlib.metadata as md
    vers = {p: md.version(p) for p in ("torch", "transformers", "peft", "playwright", "Pillow") if _has(md, p)}
    cfg = {"args": vars(a), "seed": a.seed, "gpu": "stock", "versions": vers, "python": platform.python_version(),
           "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "command": cmdline}
    (out / "config.json").write_text(json.dumps(cfg, indent=2))

    imgA, imgB = FIX / "A_clean.png", FIX / "B_flawed.png"
    res = {"judge": a.judge, "quant": a.quant or "bf16", "errors": []}
    t0 = time.time()
    adapter = ADAPTERS[a.adapter or family(a.judge)](a)
    L("loaded", a.judge, f"{time.time()-t0:.1f}s")
    res["load_s"] = time.time() - t0
    pids = [os.getpid()] + getattr(adapter, "child_pids", [])
    smi = SmiPeak(pids); smi.start()
    torch.cuda.reset_peak_memory_stats()

    ops = {"single_A": ([imgA], STATE_SINGLE, Q_SINGLE), "single_B": ([imgB], STATE_SINGLE, Q_SINGLE),
           "pair_AB": ([imgA, imgB], STATE_PAIR, Q_PAIR), "pair_BA": ([imgB, imgA], STATE_PAIR, Q_PAIR)}
    lat = {k: [] for k in ops}; raw = {k: [] for k in ops}; failed = {}
    try:
        for i in range(a.warmup + a.runs):
            timed = i >= a.warmup
            for name, (ims, st, qs) in ops.items():
                if name in failed: continue
                if name.startswith("pair") and not adapter.supports_pairwise: continue
                try:
                    torch.cuda.synchronize(); s = time.perf_counter()
                    r = adapter.ask(ims, st, qs)
                    torch.cuda.synchronize(); dt = time.perf_counter() - s
                except Exception as e:
                    failed[name] = f"{type(e).__name__}: {e}"; L("FAIL", name, failed[name]); continue
                if timed:
                    lat[name].append(dt); raw[name].append(r)
                L("warm" if not timed else f"run{i-a.warmup}", name, f"{dt*1000:.0f}ms")
    finally:
        smi.stop.set(); smi.join(2)
        if hasattr(adapter, "close"): adapter.close()

    res["latency"] = {k: summarize(v) for k, v in lat.items()}
    allv = [x for v in lat.values() for x in v]
    res["latency_all_ops"] = summarize(allv)
    res["latency_single"] = summarize(lat["single_A"] + lat["single_B"])
    res["latency_pairwise"] = summarize(lat["pair_AB"] + lat["pair_BA"])
    res["vram"] = {"torch_max_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                   "nvidia_smi_proc_peak_mib": smi.proc_peak, "nvidia_smi_gpu_used_peak_mib": smi.gpu_peak,
                   "note": "torch figure is 0 when the model runs in a child server (omnijev); use nvidia_smi_proc_peak_mib"}
    last = {k: (v[-1] if v else None) for k, v in raw.items()}
    sA = (last["single_A"] or {}).get("answers", {}); sB = (last["single_B"] or {}).get("answers", {})
    res["single"] = {"A_clean": {"p_good": p_yes(sA.get("good")), "rating": sA.get("rating")},
                     "B_flawed": {"p_good": p_yes(sB.get("good")), "rating": sB.get("rating")}}
    pa, pb = p_yes(sA.get("good")), p_yes(sB.get("good"))
    res["single"]["scores_A_gt_B"] = None if pa is None or pb is None else pa > pb
    ab = p_first(((last["pair_AB"] or {}).get("answers") or {}).get("better"))   # P(first=A is better)
    ba = p_first(((last["pair_BA"] or {}).get("answers") or {}).get("better"))   # P(first=B is better)
    pw_ok = ab is not None and ba is not None
    pair = {"pairwise_worked": pw_ok, "failures": {k: v for k, v in failed.items() if k.startswith("pair")}}
    if pw_ok:
        pref_ab = "A_clean" if ab > .5 else "B_flawed"; pref_ba = "B_flawed" if ba > .5 else "A_clean"
        pair.update({"p_A_better_when_A_first": ab, "p_A_better_when_B_first": 1 - ba,
                     "choice_AB": pref_ab, "choice_BA": pref_ba, "swap_consistent": pref_ab == pref_ba,
                     "picks_clean_page_both_orders": pref_ab == pref_ba == "A_clean",
                     "yes_no_answer": "A (clean)" if pref_ab == pref_ba == "A_clean" else "inconsistent/other"})
    res["pairwise"] = pair
    res["probability_field_present"] = pa is not None
    # determinism over timed runs
    def sig(r): return json.dumps((r or {}).get("answers"), sort_keys=True)
    res["deterministic_across_runs"] = {k: len({sig(x) for x in v}) <= 1 for k, v in raw.items() if v}
    res["failed_ops"] = failed
    res["raw_outputs_last_run"] = last
    (out / "results.json").write_text(json.dumps(res, indent=2, default=str))
    L("wrote", out / "results.json")
    L(json.dumps({k: res[k] for k in ("latency_all_ops", "vram", "pairwise")}, default=str)[:1500])
    sys.exit(0 if not failed.keys() & {"single_A", "single_B"} else 1)


def _has(md, p):
    try: md.version(p); return True
    except md.PackageNotFoundError: return False


if __name__ == "__main__":
    main()
