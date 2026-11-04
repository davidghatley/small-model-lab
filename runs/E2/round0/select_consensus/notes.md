# Round 0 consensus select (omnijev-0.8b + rsi-jev-4b)
- rsi-jev-4b judged all 2906 round-0 pairs, 0 errors, 65.1 min GPU wall (3 chunks). scores: judge/scores_rsi-jev-4b.jsonl (gitignored).
- Side agreement omni vs rsi on all 2906 pairs: 80.4%. Both judges conf>=0.7: 1047 pairs, agree on 99.4% of those.
- conf>=0.7 per judge: omnijev 1233, rsi-jev 1879. Consensus kept 1041 pairs from 371 of 500 briefs (select/ unchanged: 1233).
- Length (completion tokens), kept chosen vs rejected: 1254.4 vs 1257.6, frac chosen longer 0.521, median diff +22. No length bias.
- Command: .venv/bin/python scripts/e2_loop.py --round 0 --stage select --judges omnijev-0.8b,rsi-jev-4b --consensus --select-out runs/E2/round0/select_consensus --out runs/E2/round0/
- Note: running any e2_loop stage rewrites round0/summary.json (summary reads <out>/select); it was regenerated afterwards without --select-out.
- Train: .venv/bin/python scripts/e2_loop.py --round 0 --stage train --out runs/E2/round0/ --dataset runs/E2/round0/select_consensus/dpo.jsonl --lr 1e-4 --epochs 2 --eval-frac 0.1 --train-out runs/E2/round0/train_cons_lr1e-4   (exit 3 = call again)
