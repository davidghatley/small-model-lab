#!/usr/bin/env python3
"""E2 DPO round with Unsloth + TRL DPOTrainer (QLoRA). Run with .venv-unsloth, under gpu_run. Resumable in chunks.
  ~/anime-pipeline/tools/gpu_run --free --need 11000 .venv-unsloth/bin/python scripts/e2_dpo.py \
     --dataset runs/E2/round0/select/dpo.jsonl --out runs/E2/round0/train [--adapter-in prev/adapter] [--max-minutes 25]
Config (brief): LoRA r16 alpha16 all linear, beta 0.1, lr 5e-6, 1 epoch, max_length 4096, grad checkpointing, seed 0.
Reference model = the 4-bit base with the adapter disabled (so for round k>0 the KL anchor is the base, not the round-k policy).
Round k+1 continues training the round-k adapter (--adapter-in). Checkpoints (adapter+optimizer+scheduler) every --save-steps
optimizer steps in <out>/checkpoints; rerunning the same command resumes from the latest. On completion the final adapter is in
<out>/adapter and <out>/train_summary.json exists. Exit 0 = complete, 3 = time budget hit (call again).
"""
import os, sys
os.environ.setdefault("UNSLOTH_DISABLE_STATISTICS", "1")
import argparse, json, time, glob, platform, shlex, subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--dataset", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--base", default="/mnt/work/models/qwen2.5-coder-7b-instruct-bnb-4bit")
ap.add_argument("--adapter-in", default=None)
ap.add_argument("--max-length", type=int, default=4096)
ap.add_argument("--beta", type=float, default=0.1); ap.add_argument("--lr", type=float, default=5e-6)
ap.add_argument("--epochs", type=float, default=1.0); ap.add_argument("--max-steps", type=int, default=-1)
ap.add_argument("--batch-size", type=int, default=1); ap.add_argument("--grad-accum", type=int, default=16)
ap.add_argument("--rank", type=int, default=16); ap.add_argument("--alpha", type=int, default=16)
ap.add_argument("--save-steps", type=int, default=5); ap.add_argument("--warmup-steps", type=int, default=2)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--max-minutes", type=float, default=None)
a = ap.parse_args()

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "command.txt").write_text(" ".join(shlex.quote(x) for x in [sys.executable] + sys.argv) + "\n")
T0 = time.time()

import torch
from unsloth import FastLanguageModel, PatchDPOTrainer
PatchDPOTrainer()
import transformers, trl, peft, unsloth, datasets
from transformers import TrainerCallback
from trl import DPOConfig, DPOTrainer

vers = dict(torch=torch.__version__, transformers=transformers.__version__, trl=trl.__version__, peft=peft.__version__,
            unsloth=getattr(unsloth, "__version__", "?"), python=platform.python_version(), gpu_name=torch.cuda.get_device_name(0))
(out / "config.json").write_text(json.dumps(dict(args=vars(a), versions=vers, gpu="stock"), indent=1))

rows = [json.loads(l) for l in open(a.dataset) if l.strip()]
ds = datasets.Dataset.from_list([{k: r[k] for k in ("prompt", "chosen", "rejected")} for r in rows])
print(f"{len(ds)} pairs", flush=True)

model, tok = FastLanguageModel.from_pretrained(model_name=a.base, max_seq_length=a.max_length, dtype=None, load_in_4bit=True)
assert tok.eos_token == "<|im_end|>", tok.eos_token
if a.adapter_in:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, a.adapter_in, is_trainable=True)
    print("continuing adapter", a.adapter_in, flush=True)
else:
    model = FastLanguageModel.get_peft_model(
        model, r=a.rank, lora_alpha=a.alpha, lora_dropout=0.0, bias="none", random_state=a.seed,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth")

ckdir = out / "checkpoints"
cfg = DPOConfig(
    output_dir=str(ckdir), per_device_train_batch_size=a.batch_size, gradient_accumulation_steps=a.grad_accum,
    num_train_epochs=a.epochs, max_steps=a.max_steps, learning_rate=a.lr, lr_scheduler_type="linear", warmup_steps=a.warmup_steps,
    beta=a.beta, max_length=a.max_length, bf16=True, gradient_checkpointing=True, optim="adamw_8bit", seed=a.seed, data_seed=a.seed,
    logging_steps=1, save_strategy="steps", save_steps=a.save_steps, save_total_limit=2, report_to="none",
    dataloader_num_workers=0, remove_unused_columns=False, dataset_num_proc=1)


class Budget(TrainerCallback):
    stopped = False

    def on_step_end(self, args, state, control, **kw):
        if a.max_minutes and time.time() - T0 > a.max_minutes * 60 and state.global_step < state.max_steps:
            control.should_save = True; control.should_training_stop = True; Budget.stopped = True
        return control


class StepTimes(TrainerCallback):
    def __init__(self): self.t = []; self.last = None
    def on_step_begin(self, args, state, control, **kw): self.last = time.time()
    def on_step_end(self, args, state, control, **kw): self.t.append(time.time() - self.last)


st = StepTimes()
trainer = DPOTrainer(model=model, ref_model=None, args=cfg, train_dataset=ds, processing_class=tok, callbacks=[Budget(), st])
ck = sorted(glob.glob(str(ckdir / "checkpoint-*")), key=lambda p: int(p.rsplit("-", 1)[1]))
if ck: print("resuming from", ck[-1], flush=True)
torch.cuda.reset_peak_memory_stats()
t_train = time.time()
trainer.train(resume_from_checkpoint=ck[-1] if ck else None)
train_s = time.time() - t_train
peak = dict(torch_max_allocated_mib=torch.cuda.max_memory_allocated() / 2**20, torch_max_reserved_mib=torch.cuda.max_memory_reserved() / 2**20)
try:
    peak["nvidia_smi_used_mib_end"] = int(subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
                                                         capture_output=True, text=True).stdout.split(",")[-1].strip() or 0)
except Exception: pass

# chunk log: append the log_history entries of this process's steps to train_log.jsonl (full history is also in the checkpoint's trainer_state.json)
hist = trainer.state.log_history
(out / "train_log.jsonl").write_text("".join(json.dumps(h) + "\n" for h in hist))
done = trainer.state.global_step >= trainer.state.max_steps
chunk = dict(chunk_train_seconds=round(train_s, 1), steps_this_chunk=len(st.t), s_per_step_mean=round(sum(st.t) / max(1, len(st.t)), 2),
             global_step=trainer.state.global_step, max_steps=trainer.state.max_steps, peak=peak, done=done)
with open(out / "chunks.jsonl", "a") as f: f.write(json.dumps(chunk) + "\n")
print(json.dumps(chunk), flush=True)
if done:
    model.save_pretrained(str(out / "adapter")); tok.save_pretrained(str(out / "adapter"))
    tl = [h for h in hist if "loss" in h]
    last = tl[-max(1, len(tl) // 4):]
    mean = lambda k: (sum(h[k] for h in last if k in h) / max(1, sum(1 for h in last if k in h))) if last else None
    chunks = [json.loads(l) for l in open(out / "chunks.jsonl")]
    summ = dict(pairs=len(ds), steps=trainer.state.global_step, effective_batch=a.batch_size * a.grad_accum,
                loss_first=tl[0]["loss"] if tl else None, loss_last_quarter_mean=mean("loss"),
                reward_margin_last_quarter_mean=mean("rewards/margins"), reward_accuracy_last_quarter_mean=mean("rewards/accuracies"),
                rewards_chosen_last=mean("rewards/chosen"), rewards_rejected_last=mean("rewards/rejected"),
                s_per_step_mean=round(sum(c["s_per_step_mean"] * c["steps_this_chunk"] for c in chunks) / max(1, sum(c["steps_this_chunk"] for c in chunks)), 2),
                peak_torch_max_allocated_mib=max(c["peak"]["torch_max_allocated_mib"] for c in chunks),
                peak_torch_max_reserved_mib=max(c["peak"]["torch_max_reserved_mib"] for c in chunks),
                train_seconds=round(sum(c["chunk_train_seconds"] for c in chunks), 1), chunks=len(chunks), versions=vers, gpu="stock")
    (out / "train_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ), flush=True)
    sys.exit(0)
sys.exit(3)
