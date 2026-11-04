# eval-frac smoke
Data: dpo40.jsonl (first 40 pairs, 14 briefs) -> 33 train pairs / 12 briefs, 7 eval pairs / 2 briefs (e2_train-0004, -0006). Disjoint assert passed.
Run: e2_dpo.py --max-steps 2 --eval-frac 0.1 --grad-accum 2 --save-steps 1, via gpu_run; out train_evalcheck/ (first run with eval bs 8 kept as train_evalcheck_bs8/; final uses eval bs 1).
eval_before: loss 0.6931 acc 0 margin 0 (step 0, as expected). eval_after: loss 0.6958 acc 0.286 margin -0.005.
Eval time: ~4.6 s/pair (32 s for 7 pairs, bs1) incl. model overhead; 123 pairs ~ 9.5 min per pass (two passes ~19 min).
lr: logged step1 0.0 (warmup), step2 2.5e-06; printed with %.3e.
Resume: eval_before only when no checkpoint exists and eval_before.json absent; split is a pure function of brief_id+seed (not tested across a real resume).
Loop: stage dir for custom train-out is stages/train_<basename>.
