#!/usr/bin/env python3
"""Assemble runs/E1/staging/* into runs/E1/pairs/<pair_id>/ with integrity QA. Seeded, idempotent.
  .venv/bin/python scripts/assemble_pairs.py [--staging runs/E1/staging] [--out runs/E1] [--seed 0]
Writes pairs/, pairs_qa.md, pairs_qa.json, pairs_contact.png. Never edits staging.
"""
import argparse, difflib, json, random, re, shutil, statistics, sys
from html.parser import HTMLParser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from render import Renderer

SEV = ["obvious", "moderate", "subtle"]
PX_THRESH = 0.5  # % pixels changed below which the flaw is "not visible above fold"


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.parts = []
    def handle_starttag(self, t, a):
        if t in ("style", "script", "title", "noscript"): self.skip += 1
    def handle_endtag(self, t):
        if t in ("style", "script", "title", "noscript") and self.skip: self.skip -= 1
    def handle_data(self, d):
        if not self.skip: self.parts.append(d)


def visible_text(html):
    p = _Text(); p.feed(html)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def sim(a, b):
    if a == b: return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() if len(a) < 20000 else \
        difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio()


def pixdiff(pa, pb):
    import numpy as np
    from PIL import Image
    A = np.asarray(Image.open(pa).convert("RGB"), dtype=np.int16)[:800]
    B = np.asarray(Image.open(pb).convert("RGB"), dtype=np.int16)[:800]
    d = np.abs(A - B)
    return float(d.mean()), float((d.max(axis=2) > 8).mean() * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", default="runs/E1/staging"); ap.add_argument("--out", default="runs/E1")
    ap.add_argument("--briefs", default="briefs/e1.jsonl"); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    st, out = Path(a.staging), Path(a.out); pairs = out / "pairs"
    briefs = {}
    for l in Path(a.briefs).read_text().splitlines():
        if l.strip(): j = json.loads(l); briefs[j["id"]] = j
    rng = random.Random(a.seed)
    dirs = sorted(d for d in st.iterdir() if d.is_dir() and re.fullmatch(r"e1-\d{4}", d.name))
    rows = []
    with Renderer() as R:
        for d in dirs:
            num = int(d.name[3:]); graded = num < 150
            files = ["strong.html", "flawed.html"] if graded else ["v1.html", "v2.html"]
            flags = []
            for f in files + ["notes.json"]:
                if not (d / f).exists() or (d / f).stat().st_size == 0: flags.append(f"missing_or_empty:{f}")
            side = rng.choice("ab")  # drawn for every folder so assignment is stable
            if any(x.startswith("missing") for x in flags):
                rows.append(dict(id=d.name, flags=flags, skipped=True)); continue
            notes = json.loads((d / "notes.json").read_text())
            if notes.get("brief_id") != d.name: flags.append(f"notes_brief_id_mismatch:{notes.get('brief_id')}")
            h = [(d / f).read_text() for f in files]
            t = [visible_text(x) for x in h]
            brief = briefs.get(d.name)
            product = brief["product"].split(",")[0].strip() if brief else None
            if not brief: flags.append("no_brief")
            if graded:
                if notes.get("severity") != SEV[num % 3]: flags.append(f"severity_mismatch:{notes.get('severity')}!={SEV[num % 3]}")
                if h[0] == h[1]: flags.append("strong_flawed_identical")
                s = sim(t[0], t[1])
                if s < 0.9: flags.append(f"text_similarity_low:{s:.2f}")
            else:
                s = None
                if h[0] == h[1]: flags.append("v1_v2_identical")
                if notes.get("author_pick") not in ("v1", "v2"): flags.append(f"bad_author_pick:{notes.get('author_pick')}")
            if product:
                for f, tx in zip(files, t):
                    if product.lower() not in tx.lower(): flags.append(f"product_missing:{f}:{product}")
            # side assignment: graded -> strong goes to `side`; hard -> v1 goes to `side`
            first_side = side; second_side = "b" if side == "a" else "a"
            pid = ("fg-" if graded else "fh-") + d.name[3:]
            pd = pairs / pid; pd.mkdir(parents=True, exist_ok=True)
            infos = {}
            for src, sd, html in ((files[0], first_side, h[0]), (files[1], second_side, h[1])):
                shutil.copyfile(d / src, pd / f"{sd}.html")
                try: infos[sd] = R.render(html, pd / f"{sd}.png")
                except Exception as e:
                    infos[sd] = dict(fonts_ok=False, font_failures=[f"render_error:{e}"]); flags.append(f"render_error:{sd}")
            fonts_ok = all(i["fonts_ok"] for i in infos.values())
            ffail = {sd: i["font_failures"] for sd, i in infos.items() if i["font_failures"]}
            if not fonts_ok: flags.append("font_failure")
            md = pp = None
            if graded and not any(x.startswith("render_error") for x in flags):
                md, pp = pixdiff(pd / "a.png", pd / "b.png")
                if pp < PX_THRESH: flags.append(f"flaw_not_visible_above_fold:{pp:.2f}%")
            meta = dict(pair_id=pid, brief_id=d.name, source="frontier_graded" if graded else "frontier_hard",
                        intended_better=first_side if graded else None,
                        flaw_severity=notes.get("severity") if graded else None,
                        flaw_notes=notes.get("flaws") if graded else notes.get("why"),
                        staging_src=str(d), fonts_ok=fonts_ok, qa_flags=flags)
            if graded:
                meta.update(strong_side=first_side, text_similarity=round(s, 4), pixel_mean_abs_diff=None if md is None else round(md, 3),
                            pixel_pct_changed=None if pp is None else round(pp, 3))
            else:
                meta.update(author_pick_side=first_side if notes.get("author_pick") == "v1" else second_side,
                            directions=notes.get("directions"), v1_side=first_side)
            (pd / "meta.json").write_text(json.dumps(meta, indent=1))
            rows.append(dict(id=d.name, pair_id=pid, source=meta["source"], severity=meta["flaw_severity"],
                             intended_better=meta["intended_better"], flags=flags, font_failures=ffail,
                             md=md, pp=pp, sim=s))
    report(rows, out, pairs)


def report(rows, out, pairs):
    import numpy as np
    from PIL import Image
    ok = [r for r in rows if not r.get("skipped")]
    g = [r for r in ok if r["source"] == "frontier_graded"]; h = [r for r in ok if r["source"] == "frontier_hard"]
    bal = {s: sum(1 for r in g if r["intended_better"] == s) for s in "ab"}
    stats = {}
    for sv in SEV:
        xs = [r for r in g if r["severity"] == sv and r["pp"] is not None]
        if xs:
            stats[sv] = dict(n=len(xs), median_pct_changed=statistics.median(r["pp"] for r in xs),
                             min_pct_changed=min(r["pp"] for r in xs), median_mean_abs_diff=statistics.median(r["md"] for r in xs),
                             min_mean_abs_diff=min(r["md"] for r in xs))
    flagged = [r for r in rows if r["flags"]]
    fonts = [r for r in ok if r["font_failures"]]
    q = dict(n_staging=len(rows), n_pairs=len(ok), n_graded=len(g), n_hard=len(h),
             graded_by_severity={sv: sum(1 for r in g if r["severity"] == sv) for sv in SEV},
             side_balance_intended_better=bal, pixel_diff_by_severity=stats,
             flagged=[dict(id=r["id"], pair_id=r.get("pair_id"), flags=r["flags"]) for r in flagged],
             font_failures={r["pair_id"]: r["font_failures"] for r in fonts})
    (out / "pairs_qa.json").write_text(json.dumps(q, indent=1))
    L = ["# E1 pairs QA", "", f"- staging folders: {len(rows)}; pairs assembled: {len(ok)} (graded {len(g)}, hard {len(h)})",
         f"- graded by severity: {q['graded_by_severity']}",
         f"- side balance (intended_better, graded): a={bal['a']} b={bal['b']}",
         f"- flagged pairs: {len(flagged)}; pairs with font failures: {len(fonts)}", "", "## Pixel diff (strong vs flawed, top 800px)", "",
         "| severity | n | median % changed | min % changed | median mean-abs-diff | min mean-abs-diff |", "|---|---|---|---|---|---|"]
    for sv, s in stats.items():
        L.append(f"| {sv} | {s['n']} | {s['median_pct_changed']:.2f} | {s['min_pct_changed']:.2f} | {s['median_mean_abs_diff']:.2f} | {s['min_mean_abs_diff']:.2f} |")
    L += ["", f"Flag threshold: <{PX_THRESH}% pixels changed (channel diff > 8).", "", "## Flagged pairs", ""]
    L += [f"- {r.get('pair_id') or r['id']} ({r['id']}): {'; '.join(r['flags'])}" for r in flagged] or ["(none)"]
    L += ["", "## Font failures", ""]
    L += [f"- {r['pair_id']}: {r['font_failures']}" for r in fonts] or ["(none)"]
    (out / "pairs_qa.md").write_text("\n".join(L) + "\n")
    # contact sheet
    rr = random.Random(0); pick = sorted(rr.sample(g, min(12, len(g))), key=lambda r: r["pair_id"])
    tw, th = 400, 250; cols = 2
    sheet = Image.new("RGB", (cols * (2 * tw + 30), ((len(pick) + 1) // cols) * (th + 10)), "white")
    for i, r in enumerate(pick):
        d = pairs / r["pair_id"]; m = json.loads((d / "meta.json").read_text())
        strong = m["intended_better"]; weak = "b" if strong == "a" else "a"
        x = (i % cols) * (2 * tw + 30); y = (i // cols) * (th + 10)
        for k, s in enumerate((strong, weak)):
            sheet.paste(Image.open(d / f"{s}.png").convert("RGB").resize((tw, th)), (x + k * (tw + 10), y))
    sheet.save(out / "pairs_contact.png")
    (out / "pairs_contact.txt").write_text("contact sheet: left=strong right=flawed; order row-major: " + ", ".join(r["pair_id"] for r in pick) + "\n")


if __name__ == "__main__":
    main()
