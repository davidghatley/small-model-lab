# small-model-lab

Can a 7B coder model get better at web design by learning from a small local vision judge, on one 12 GB GPU? This repo runs that loop and checks how much of the gain is real and how much is the judge being gamed.

## The loop

1. **Generate.** Qwen2.5-Coder-7B-Instruct writes 4 landing pages for each of 500 training briefs.
2. **Render.** Playwright screenshots every page at 1280×800.
3. **Judge.** Two local vision "System One" judges (OneJev1.6-0.8B and RSI-Jev v6.1-VL 4B) compare pages of the same brief in both orders.
4. **Select.** A pair is kept only when both judges pick the same page with order-averaged confidence ≥ 0.7.
5. **Train.** DPO on the kept pairs. The next round samples from the new adapter.
6. **Evaluate** on 100 held-out briefs that never enter training: tuned vs base, scored by a judge never used for training (imajev-9b), by the training judge, and by a blind frontier model (Claude Opus) on 50 of them. Then audit the pages for reward hacking.

## Setup

| | |
|---|---|
| Policy | Qwen2.5-Coder-7B-Instruct (Apache-2.0). Sampled with vLLM from the official AWQ build; trained on the Unsloth bnb-4bit build |
| Training | DPO, QLoRA rank 16, beta 0.1, lr 5e-5, 1 epoch, reference = base, seed 0 |
| Training judges | OneJev1.6-0.8B (OmniJev, Apache-2.0) + RSI-Jev v6.1-VL 4B (Shanghua Gao, Apache-2.0 weights), consensus |
| Held-out judge | imajev-9b (Mohit Garg, Apache-2.0), 4-bit NF4 |
| Hardware | one RTX 3060 12 GB, 64 GB RAM, stock GPU |
| Stack | Unsloth, TRL, PEFT, bitsandbytes, Transformers, vLLM, Playwright, llama.cpp |

All judges run locally. Every chosen and rejected page in the DPO data was written by the Qwen coder itself.

## Results

From [`LEDGER.md`](LEDGER.md) (E2). Win rate of the tuned coder against the base on held-out briefs, 95% CI in brackets.

| | imajev-9b (held-out judge) | Opus, blind (n=50) | OneJev 0.8B (training judge) |
|---|---|---|---|
| Round 0: 1041 pairs, 60 steps | 0.708 [0.62, 0.80] | 0.68 [0.54, 0.80] | 0.65 |
| Round 1: 302 pairs, 18 steps | 0.926 [0.87, 0.97] | 0.78 [0.66, 0.88] | 0.85 |

**What improved.** Mostly fixed base failures: full-viewport heroes dropped from 23% to 3% of pages, along with fewer rainbow gradients and broken images. Pages did not get emptier (round 1 has 22% more words), and there is no fake trust or praise copy and no copying of the brief.

**Reward hacking.** The palette collapsed toward one template. Pages using the `#6a11cb → #2575fc` gradient went from 28% (base) to 34% (round 0) to 63% (round 1). "Welcome to X" headlines went from 67% to 78% to 87%. Template pages win 97% of the time against 86% without it, so about 11 points of round 1's win comes from the template. The small judges gained more than Opus did (+22 vs +10 points), which fits a judge-pleasing style. Layout and text diversity across briefs did not change. Details: `runs/E2/audit/r0_cons/audit.md`, `runs/E2/audit/r1/audit.md`.

## Limitations

- Round 1 trained for only 18 steps on 302 pairs, because few pairs passed the consensus filter.
- One GPU, one seed, one sample per held-out brief; Opus scored 50 briefs.
- Judges see only the first 1280×800 viewport, not the full page.
- The judges' own taste was checked on 300 pairs and 30 hand labels (E1). OneJev 0.8B was the weakest match to human picks, which is why the consensus filter was added.
- RSI-Jev's weights are Apache-2.0, but its model card lists some non-commercial and research-only image training sources.
- Scripts assume weights at the local paths in `scripts/README.md` and launch GPU jobs through a local `gpu_run` wrapper (`e2_loop.py --no-gpu-run` skips it; `e2_eval.py` does not have that flag yet). No weights or adapters are in this repo.

## Reproduce

Environments (uv, Python 3.12) and model downloads with pinned revisions are in [`scripts/README.md`](scripts/README.md). The commands used for each result sit next to it in `runs/` as `command.txt` and `config.json`.

```bash
bash scripts/smoke_e2.sh                      # whole loop at toy size, about 15 min

# round 0: generate, render, judge (both judges), consensus select, train
.venv/bin/python scripts/e2_loop.py --round 0 --stage all --out runs/E2/round0/          # repeat while exit code is 3
.venv/bin/python scripts/e2_loop.py --round 0 --stage judge --judge rsi-jev-4b --out runs/E2/round0/
.venv/bin/python scripts/e2_loop.py --round 0 --stage select --judges omnijev-0.8b,rsi-jev-4b --consensus \
  --select-out runs/E2/round0/select_consensus --out runs/E2/round0/
.venv/bin/python scripts/e2_loop.py --round 0 --stage train --out runs/E2/round0/ --dataset runs/E2/round0/select_consensus/dpo.jsonl \
  --lr 5e-5 --eval-frac 0.1 --train-out runs/E2/round0/train_cons_lr5e-5

# held-out evaluation against the base
.venv/bin/python scripts/e2_eval.py --out runs/E2/eval/r0_cons_lr5e-5 --policy-y runs/E2/round0/train_cons_lr5e-5/adapter \
  --name-y r0_cons --judges omnijev-0.8b,imajev-9b --stage all
```

Round 1 repeats the same stages with `--round 1 --policy-adapter runs/E2/round0/train_cons_lr5e-5/adapter`.

## Where things are

- [`LEDGER.md`](LEDGER.md): status and results of every experiment. Start here.
- [`PLAN.md`](PLAN.md): phases and dated decisions.
- `runs/E0/judges.md`: judge speed, memory and licences. `runs/E1/audit/audit.md`: judge taste check.
- `briefs/`: seeded, disjoint train / eval brief splits (`scripts/make_briefs.py --check` verifies them).

The method is Direct Preference Optimization (Rafailov et al., 2023), with judges from the open "System One" decision-model community (OneJev, RSI-Jev, imajev).

## License

Code: MIT (see [`LICENSE`](LICENSE)). Models and judges keep their own licences.
