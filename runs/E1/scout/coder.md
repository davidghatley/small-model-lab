# E1 coder model shortlist (scout)

Date of research: 2026-11-03. Target: QLoRA DPO with Unsloth on RTX 3060 12 GB, 64 GB RAM, sequence length 4-6k tokens (prompt + full single-file HTML page).

Labels: primary source = model card or Unsloth docs fetched directly. **unverified** = secondary source or estimate. **estimate** = my arithmetic, not a published figure.

## Recommendation

- **Primary: Qwen2.5-Coder-7B-Instruct.** Apache-2.0, ungated, 7.6B params. Unsloth publishes a 4-bit (bnb) variant, and Unsloth's own 7B QLoRA minimum is 5 GB, which leaves headroom on 12 GB at 4-6k tokens. Weakness: it is a 2024-era model, so its HTML ceiling is low, which is the "room to improve" we want, but it is not benchmarked for HTML by anyone I could find.
- **Backup: Gemma 4 E4B (instruction-tuned).** Listed as Apache-2.0 on the card, ungated status not shown, about 8B params including per-layer embeddings (4.5B effective). Unsloth lists a bnb-4bit variant. Stronger on LiveCodeBench v6 (52.0%) than Qwen2.5-Coder-7B is known to be, but I have no comparable number for Qwen2.5-Coder, so that is not a like-for-like comparison.
- **Not recommended for this rig: Qwen3.5-9B and Mellum 2.1 (12B MoE).** Unsloth explicitly advises against QLoRA on Qwen3.5 and lists no 4-bit variant for the 9B (details below). Mellum 2.1 is not in Unsloth's catalog and is an MoE model.

## Per-candidate table

| Candidate | HF repo | License | Gated | Params / bf16 size | Unsloth | QLoRA DPO VRAM at 4-6k | HTML/web benchmark | Chat template |
|---|---|---|---|---|---|---|---|---|
| **Qwen2.5-Coder-7B-Instruct** | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | apache-2.0 (card) | Not stated on card | 7.61B; bf16 ~15 GB **estimate** (7.61B x 2 bytes) | Yes. Unsloth's catalog lists "Qwen2.5-Coder (128 K) 7 B" with a bnb-4bit link, marked fine-tune ready. https://unsloth.ai/docs/get-started/unsloth-model-catalog | Unsloth 7B QLoRA min 5 GB (https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements). At 4-6k with DPO (chosen+rejected, activations): ~9-11 GB **estimate**. Fits. | None found | Yes (card and template) |
| **Gemma 4 E4B (it)** | https://huggingface.co/google/gemma-4-E4B-it | apache-2.0 in metadata; body links Google's Gemma license page. **Conflict, verify before use.** | Not shown on page **unverified** | "8B params" with embeddings (4.5B effective); bf16 ~16 GB **estimate** | Yes. Catalog lists "E4B" with bnb-4bit and NVFP4 links, fine-tune ready (bnb). https://unsloth.ai/docs/get-started/unsloth-model-catalog | 8B-class QLoRA min 6 GB (Unsloth table). At 4-6k with DPO: ~10-13 GB **estimate**. Tighter than Qwen2.5-Coder-7B. | No web benchmark. LiveCodeBench v6 52.0%, Codeforces ELO 940 (https://huggingface.co/google/gemma-4-E4B-it) | Yes (it) |
| **Qwen3.5-9B** | https://huggingface.co/Qwen/Qwen3.5-9B | apache-2.0 | Not stated | 9B (10B in safetensors widget); bf16 ~18-20 GB **estimate** | **No 4-bit listed** in catalog for 9B. Unsloth says "It is not recommended to do QLoRA (4-bit) training on the Qwen3.5 models, no matter MoE or dense" (https://unsloth.ai/docs/models/qwen3.5/fine-tune). Unsloth's bf16 LoRA figure for 9B is 22 GB, so it does not fit 12 GB for our method. | Unsloth supports Qwen3.5 in bf16 only. QLoRA on 12 GB: **does not fit or is not recommended** per Unsloth. | None found. LiveCodeBench v6 65.6; no SWE/WebDev/Design2Code scores (https://huggingface.co/Qwen/Qwen3.5-9B) | Yes (thinking by default; non-thinking via enable_thinking=False) |
| **Mellum 2.1 (12B-A2.5B Thinking)** | https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking | apache-2.0 (card) | Not stated | 12B total, 2.5B active, MoE (64 experts, 8 active, 28 layers); bf16 ~24 GB **estimate** | **Not in Unsloth catalog.** Unsloth's MoE QLoRA guidance is "MoE QLoRA 4-bit is not recommended due to BitsandBytes limitations" (https://unsloth.ai/docs/models/qwen3.5/fine-tune; the statement appears on the Qwen3.5 page and may not be specific to Qwen3.5 **unverified** as to scope). | Unknown. Weights in 4-bit ~6-7 GB **estimate**, but MoE QLoRA is a risk. | None listed. Self-reported: LiveCodeBench v6 82.0, SWE-bench Verified 47.0, IFEval 90.6 (JetBrains, self-reported). No HTML/web score. | Yes (conversational; apply_chat_template) |
| Mellum-4b-dpo-all (extra) | https://huggingface.co/JetBrains/Mellum-4b-dpo-all | Base Mellum-4b-base listed Apache-2.0 by secondary sources **unverified**; dpo-all license not shown on collection page | Not shown | 4B | Not in catalog **unverified** | Likely fits (4B) **estimate** | None | Not verified |

## Benchmark search, for the record

I looked for HTML/front-end scores at this size and found none that apply:
- Design Arena: top HTML entry (GLM-5.2, MIT) is far larger than 9B. Figure came from a secondary search summary, no Design Arena URL fetched **unverified**.
- WebDev Arena listing shows only a proprietary model (https://llm-stats.com/benchmarks/webdev-arena).
- FrontendBench: no small-model results surfaced (https://www.alphaxiv.org/benchmarks/bytedance/frontendbench).
- Design2Code: only a VisCodex-8B number (90.1/90.9) on a modified metric (https://arxiv.org/pdf/2508.09945). Not comparable to our candidates and not verified against the original paper.

Implication: we will need our own HTML eval (render + automated checks) to set the baseline. Do not treat any leaderboard as a selection criterion.

## Unsloth facts used

- DPO/ORPO/KTO work with Unsloth, with an example using `load_in_4bit=True` and `ref_model=None`, `max_length=1024`, `max_prompt_length=512`. The example is far shorter than our 4-6k target, so long-sequence DPO memory is not validated by the docs. (https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/reinforcement-learning-dpo-orpo-and-kto)
- Unsloth's VRAM table (QLoRA 4-bit / LoRA 16-bit): 7B 5 GB / 19 GB; 8B 6 GB / 22 GB; 9B 6.5 GB / 24 GB; 11B 7.5 GB / 29 GB; 14B 8.5 GB / 33 GB. The page says these are the absolute minimum and that DPO memory is not covered. (https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements)
- Qwen3.5 page: QLoRA not recommended, MoE QLoRA not recommended, bf16 LoRA 9B 22 GB. (https://unsloth.ai/docs/models/qwen3.5/fine-tune)

## Open questions

1. Gemma 4 E4B license: the card metadata says Apache-2.0 but the body links Google's Gemma license. Check the license file before use.
2. Gated status of Gemma 4 E4B and Mellum 2.1 is not shown on the fetched pages. Confirm in a logged-out browser or via the HF API.
3. Long-sequence DPO VRAM (4-6k, chosen+rejected) is not documented by Unsloth for any model. Our first run should measure peak memory on the 3060 before committing to a model.
4. Is Mellum 2.1 supported by Unsloth MoE training at all? Unknown. Would need a short test run.
5. No public HTML benchmark exists for these small models. We need an internal baseline (for example, render + DOM and layout checks + a rubric) to decide whether Qwen2.5-Coder-7B has room to improve.
6. The Qwen2.5-Coder-7B "128K" context: its card says the default config is 32K, with YaRN needed beyond that. Our 4-6k need is well inside 32K.

## Sources

- https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking
- https://huggingface.co/Qwen/Qwen3.5-9B
- https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- https://huggingface.co/google/gemma-4-E4B-it
- https://huggingface.co/collections/JetBrains/mellum
- https://unsloth.ai/docs/get-started/unsloth-model-catalog
- https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements
- https://unsloth.ai/docs/models/qwen3.5/fine-tune
- https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/reinforcement-learning-dpo-orpo-and-kto
- https://arxiv.org/pdf/2508.09945 (VisCodex, Design2Code)
- https://www.alphaxiv.org/benchmarks/bytedance/frontendbench
- https://llm-stats.com/benchmarks/webdev-arena
- Secondary (Mellum 2.1 release date Oct 8 2026, Apache-2.0): https://tech-insider.org/jetbrains-mellum-2-1-12b-moe-coding-agents-2026/ **unverified**
