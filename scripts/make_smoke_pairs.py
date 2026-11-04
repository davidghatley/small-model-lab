#!/usr/bin/env python3
"""Make 6 tiny synthetic pairs + a fake reference label file under <dir>/{pairs,labels}. Smoke test only."""
import json, sys
from pathlib import Path
GOOD = """<html><body style="margin:0;font-family:Inter,Arial,sans-serif;color:#1b2430;background:#fff">
<header style="display:flex;justify-content:space-between;padding:24px 80px"><b style="font-size:22px">{n}</b><span style="color:#556">Features &nbsp; Pricing &nbsp; Contact</span></header>
<section style="padding:90px 80px;background:#eef3ff"><h1 style="font-size:56px;margin:0 0 16px;max-width:700px">{h}</h1>
<p style="font-size:20px;color:#445;max-width:560px">A calm, clear page with generous spacing and a strong call to action.</p>
<a style="display:inline-block;margin-top:24px;padding:14px 28px;background:#2f5bea;color:#fff;border-radius:8px;font-weight:600">Get started</a></section>
<section style="display:flex;gap:24px;padding:60px 80px"><div style="flex:1;padding:24px;border-radius:12px;background:#f6f7fa"><h3>Fast</h3><p>Short, readable copy.</p></div>
<div style="flex:1;padding:24px;border-radius:12px;background:#f6f7fa"><h3>Simple</h3><p>Aligned grid, consistent type.</p></div>
<div style="flex:1;padding:24px;border-radius:12px;background:#f6f7fa"><h3>Fair</h3><p>Clear pricing.</p></div></section></body></html>"""
BAD = """<html><body style="margin:0;background:#ff00ff;font-family:'Comic Sans MS',cursive;color:#ffff00">
<h1 style="font-size:12px;margin:300px 0 0 700px">{h}</h1><p style="font-size:70px;color:#00ff00;background:#ffa500;margin:0">buy now buy now</p>
<div style="position:absolute;left:30px;top:40px;width:900px;height:60px;background:#00ffff;color:#fff">{n}</div>
<a style="position:absolute;left:1100px;top:700px;color:#ff00ff">click</a></body></html>"""
MID = GOOD.replace("#2f5bea", "#2a62e0").replace("56px", "48px")
pairs = [  # (id, a, b, intended_better, severity)
    ("p1", GOOD, BAD, "a", "obvious"), ("p2", BAD, GOOD, "b", "obvious"), ("p3", GOOD, BAD, "a", "obvious"),
    ("p4", BAD, GOOD, "b", "obvious"), ("p5", GOOD, MID, None, None), ("p6", MID, GOOD, None, None)]
root = Path(sys.argv[1]); (root / "labels").mkdir(parents=True, exist_ok=True)
ref = []
for i, (pid, a, b, ib, sev) in enumerate(pairs):
    d = root / "pairs" / pid; d.mkdir(parents=True, exist_ok=True)
    (d / "a.html").write_text(a.format(n="Acme", h=f"Ship faster {i}") if "{n}" in a else a)
    (d / "b.html").write_text(b.format(n="Acme", h=f"Ship faster {i}") if "{n}" in b else b)
    (d / "meta.json").write_text(json.dumps({"pair_id": pid, "brief_id": "smoke-0", "source": "frontier_graded", "intended_better": ib,
                                              "flaw_severity": sev, "flaw_notes": "synthetic"}, indent=2))
    ref.append({"pair_id": pid, "better": ib or "a", "confidence": 0.9 if ib else 0.55, "rationale": "fake smoke label"})
(root / "labels" / "reference.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ref))
