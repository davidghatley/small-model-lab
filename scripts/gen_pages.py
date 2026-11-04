#!/usr/bin/env python
"""Batched landing-page generation with Qwen2.5-Coder-7B-Instruct via a local vLLM server.

Run under the GPU gate, e.g.
  ~/anime-pipeline/tools/gpu_run --free --need 10000 .venv-vllm/bin/python scripts/gen_pages.py \
      --briefs briefs/e1.jsonl --n-samples 2 --temperature 0.8 --seed 0 --max-tokens 6144 --out runs/E1/pages_base
Writes <out>/<brief_id>/s<k>.html, <out>/gen.jsonl (one row per sample), config.json, command.txt, server.log.
Resumable: samples already in gen.jsonl are skipped. Use the vllm venv (needs only stdlib + vllm server binary).
"""
import argparse, json, os, re, signal, subprocess, sys, threading, time, urllib.request, shlex, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEF_MODEL = "/mnt/work/models/qwen2.5-coder-7b-instruct-awq"  # official AWQ-Int4; bf16 weights are in ...-instruct/


def load_template(path):
    txt = Path(path).read_text()
    sys_p, user_p = txt.split("=====USER=====", 1)
    return sys_p.strip(), user_p.strip()


def build_messages(tpl, b):
    sec = b.get("sections", [])
    fields = dict(product=b.get("product") or b.get("description", ""), audience=b.get("audience", "general visitors"),
                  tone=b.get("tone", "clean and professional"), sections=", ".join(sec) if sec else "hero, features, CTA, footer",
                  description=b.get("description", ""))
    s, u = tpl
    return [{"role": "system", "content": s}, {"role": "user", "content": u.format(**fields)}]


def sample_seed(base, bid, k):
    return int(hashlib.sha256(f"{base}:{bid}:{k}".encode()).hexdigest()[:8], 16)


def extract_html(text):
    """Return (html, clean). clean = a complete document was recovered from a proper fence or bare doc."""
    m = re.search(r"```(?:html|HTML)?[ \t]*\n(.*?)```", text, re.S)
    body, fenced = (m.group(1), True) if m else (None, False)
    if body is None:
        m = re.search(r"```(?:html|HTML)?[ \t]*\n(.*)$", text, re.S)  # unclosed fence
        if m:
            body, fenced = m.group(1), False
    src = body if body is not None else text
    low = src.lower()
    i = low.find("<!doctype")
    if i < 0:
        i = low.find("<html")
    if i > 0:
        src = src[i:]
    j = src.lower().rfind("</html>")
    complete = j >= 0
    if complete:
        src = src[:j + 7]
    has_doc = ("<!doctype" in src.lower()[:200]) or ("<html" in src.lower()[:200])
    clean = complete and has_doc and "<body" in src.lower()
    return src.strip() + "\n", clean


def wait_ready(port, proc, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError("vllm server exited early; see server.log")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
            return
        except Exception:
            time.sleep(3)
    raise TimeoutError("server not ready")


def post(port, payload):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--n-samples", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=6144)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-path", default=DEF_MODEL)
    ap.add_argument("--quant", default="none", help="vllm --quantization value (e.g. fp8 for on-the-fly with the bf16 checkpoint); none = auto-detect (AWQ)")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--kv-dtype", default="auto")
    ap.add_argument("--max-model-len", type=int, default=8192)
    ap.add_argument("--gpu-util", type=float, default=0.90)
    ap.add_argument("--max-num-seqs", type=int, default=48)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None, help="only first N briefs")
    ap.add_argument("--prompt", default=str(ROOT / "scripts/prompts/coder_page.txt"))
    ap.add_argument("--adapter", default=None, help="optional LoRA dir served as model name 'adapter'")
    ap.add_argument("--max-minutes", type=float, default=None, help="stop starting new samples after this many minutes (in-flight ones finish); rerun to resume")
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--server-url-port", type=int, default=None, help="reuse an already running server on this port")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "command.txt").write_text(" ".join(shlex.quote(x) for x in [sys.executable] + sys.argv) + "\n")
    vers = subprocess.run([sys.executable, "-c", "import vllm;print(vllm.__version__)"], capture_output=True, text=True).stdout.strip()
    rev = ""
    try:
        rev = next((Path(a.model_path) / ".cache/huggingface/download/config.json.metadata").open()).strip()
    except Exception:
        pass
    (out / "config.json").write_text(json.dumps(dict(vars(a), vllm=vers, model_revision=rev, gpu="stock"), indent=1))

    briefs = [json.loads(l) for l in open(a.briefs) if l.strip()]
    if a.limit: briefs = briefs[:a.limit]
    tpl = load_template(a.prompt)
    genp = out / "gen.jsonl"
    done = set()
    if genp.exists():
        for l in open(genp):
            try:
                r = json.loads(l); done.add((r["brief_id"], r["k"]))
            except Exception:
                pass
    todo = [(b, k) for k in range(a.n_samples) for b in briefs if (b["id"], k) not in done]
    print(f"{len(todo)} samples to generate ({len(done)} already done)", flush=True)
    if not todo:
        return 0

    proc = None
    port = a.server_url_port or a.port
    if not a.server_url_port:
        cmd = [str(ROOT / ".venv-vllm/bin/vllm"), "serve", a.model_path, "--served-model-name", "coder", "--port", str(port),
               "--host", "127.0.0.1", "--max-model-len", str(a.max_model_len), "--gpu-memory-utilization", str(a.gpu_util),
               "--max-num-seqs", str(a.max_num_seqs), "--dtype", a.dtype, "--seed", str(a.seed), "--kv-cache-dtype", a.kv_dtype,
               "--enable-prefix-caching"]
        if a.quant != "none": cmd += ["--quantization", a.quant]
        if a.adapter: cmd += ["--enable-lora", "--lora-modules", f"adapter={a.adapter}", "--max-lora-rank", "64"]
        (out / "server_cmd.txt").write_text(" ".join(cmd) + "\n")
        env = dict(os.environ, VLLM_USE_FLASHINFER_SAMPLER="0")  # flashinfer sampler needs nvcc JIT
        proc = subprocess.Popen(cmd, env=env, stdout=open(out / "server.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)

    lock = threading.Lock()
    rc = 0
    try:
        wait_ready(port, proc) if proc else None
        model = "adapter" if a.adapter else "coder"
        t_start = time.time()
        stats = dict(tok=0, n=0)

        deadline = time.time() + a.max_minutes * 60 if a.max_minutes else None

        def work(b, k):
            if deadline and time.time() > deadline:
                return None
            seed = sample_seed(a.seed, b["id"], k)
            t0 = time.time()
            r = post(port, dict(model=model, messages=build_messages(tpl, b), temperature=a.temperature, top_p=a.top_p,
                                max_tokens=a.max_tokens, seed=seed))
            lat = time.time() - t0
            ch = r["choices"][0]; text = ch["message"]["content"] or ""
            html, clean = extract_html(text)
            fin = ch["finish_reason"]
            d = out / b["id"]; d.mkdir(exist_ok=True)
            (d / f"s{k}.html").write_text(html)
            (d / f"s{k}.raw.txt").write_text(text)  # exact model output (E2 trains on it)
            row = dict(brief_id=b["id"], k=k, seed=seed, tokens=r["usage"]["completion_tokens"], prompt_tokens=r["usage"]["prompt_tokens"],
                       finish_reason=fin, truncated=(fin == "length"), latency=round(lat, 2), extracted_cleanly=bool(clean and fin != "length"),
                       temperature=a.temperature)
            with lock:
                with open(genp, "a") as f: f.write(json.dumps(row) + "\n")
                stats["tok"] += row["tokens"]; stats["n"] += 1
                if stats["n"] % 8 == 0 or stats["n"] == len(todo):
                    el = time.time() - t_start
                    print(f"[{stats['n']}/{len(todo)}] {stats['tok']/el:.0f} tok/s agg, {el:.0f}s", flush=True)
            return row

        conc = a.concurrency or a.max_num_seqs
        with ThreadPoolExecutor(conc) as ex:
            futs = [ex.submit(work, b, k) for b, k in todo]
            for f in as_completed(futs):
                try: f.result()
                except Exception as e:
                    print("sample failed:", repr(e), flush=True); rc = 1
        el = time.time() - t_start
        (out / "summary.json").write_text(json.dumps(dict(samples=stats["n"], tokens=stats["tok"], wall_s=round(el, 1),
                                                          agg_tok_per_s=round(stats["tok"] / el, 1)), indent=1))
    finally:
        if proc and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGINT)
            try: proc.wait(60)
            except subprocess.TimeoutExpired: os.killpg(proc.pid, signal.SIGKILL)
    return rc


if __name__ == "__main__":
    sys.exit(main())
