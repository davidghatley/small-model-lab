# e2_dpo.py resume check (2026-11-04)
Root cause: checkpoint dirs contain `ref/` (TRL reference adapter, lora_B==0) next to the real `adapter_model.safetensors`. Trainer's PEFT resume branch sees an adapter subdir and loads only `ref/`; the `default` adapter is never restored (checkpoint-120 of train_cons_lr1e-4: main lora_B norm 0.0149, ref/ 0.0).
Fix: explicit `set_peft_model_state_dict` from the latest checkpoint + norm hard check + norm logging in chunks.jsonl.

Run: dpo40.jsonl, --max-steps 6 --save-steps 1 --lr 1e-4 --grad-accum 4, seed 0; chunked with hidden --max-steps-per-chunk 2 (3 chunks) in `train_resumecheck/`; unchunked in `train_unchunked/`.

| chunk | resumed from | lora_B norm start | end |
|---|---|---|---|
| 1 | none | 0.0 | 2.0216 |
| 2 | ckpt-2 | 2.0216 | 6.3838 |
| 3 | ckpt-4 | 6.3838 | 7.8936 |

Step log (chunked): step3 (first after resume 1) loss 0.7393 margin -0.0814; step5 (first after resume 2) loss 0.4473 margin +0.5995. Steps 1-2 are 0.6931/0 by design (B=0 init, lr warmup).
Unchunked: step3 0.7312/-0.0657, step5 0.4523/+0.5825.
Final adapter lora_B norm: chunked 7.89355 == checkpoint-6 7.89355; unchunked 7.88143 (0.15% apart).
