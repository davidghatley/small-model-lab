# Scout findings: candidates batch B (System One judge)

Date of research: 2026-11-03. Target: RTX 3060 12 GB, 64 GB RAM, Linux.
Research only. No weights downloaded, no code run.

Conventions: **unverified** = not confirmed from a primary source (model card, repo, paper). "unknown" = not stated in any source checked. VRAM figures marked "estimate" are my arithmetic (parameters x bytes per parameter), not source claims. Sources marked "(secondary)" are third-party blogs or aggregators.

---

## Summary table

| Candidate | Found | Weights license | Gated | Fits 12 GB? | Pairwise (2 images in one call) | Probabilities |
|---|---|---|---|---|---|---|
| RSI-Jev v6.1-VL 4B | Yes | Apache-2.0 (weights), MIT (code); some image training sources non-commercial per card | Not stated | Bf16 weights ~9.4 GB, tight; no published quant | unknown | Yes (per-option probabilities + confidence) |
| RSI-Jev v6.1-VL 27B | Yes | Apache-2.0 | Unknown | No. Needs a 96 GB GPU per card; no smaller build | unknown | Yes |
| StartLux-Decision v1 / v1.1 (0.8B to 27B) | Yes | CC BY-NC 4.0 (weights); Apache-2.0 (code) | Unknown | 4B GGUF yes (text only); 27B no | Not mentioned | Yes (per option, confidence, none_probability) |
| Simple Jev (JevAny by SimpleJev) | Yes (wrapper) | Apache-2.0 (code); base model licenses apply separately | Unknown | Depends on base; 4B LoRA variants possibly | unknown | Yes (probability per option) |
| open-alternative-jev (ikermoel) | Yes, under this name | Apache-2.0 | n/a (wrapper) | Depends on base; Qwen3.5-4B is tested, no VRAM figure given for it | unknown | Yes (softmax over option letters, optional temperature scaling) |
| Hosted Jev 1.14 (TypeSafe) | Yes (API) | Proprietary, paid | n/a | n/a (hosted) | Not stated; `box` type is new | Yes ("typed decisions, complete with probabilities and confidence levels") |

Key finding: none of the three local vision-capable options that were searched offers a 27B model that fits 12 GB. The usable local vision choice on this box is the 4B tier (RSI-Jev 4B bf16 or StartLux 4B safetensors). StartLux and open-alternative-jev both need checking for two-image support before use.

---

## 1. RSI-Jev v6.1-VL (4B and 27B)

**Publisher / repos**
- Code: https://github.com/Shanghua-Gao/RSI-Jev (owner GitHub user Shanghua-Gao; a third-party project, not TypeSafe; the author is named as Shanghua Gao, GitHub @gasvn, per https://www.orcarouter.ai/blog/what-is-rsi-jev (secondary))
- Weights, 4B: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b
- Weights, 27B: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b
- Release dates per repo README table (fetched from the GitHub page): v6.1-VL 4B 2026-10-07; v6.1-VL 27B 2026-10-08. Source: https://github.com/Shanghua-Gao/RSI-Jev

**License**
- Code: MIT. Weights: Apache-2.0, "following the base model." Source: https://github.com/Shanghua-Gao/RSI-Jev
- HF card metadata for the 4B: `apache-2.0`, no license link on the page. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b
- HF card for the 27B: Apache-2.0, no license file link. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b
- Caveat: the GitHub README says "Some image training sources are non-commercial, listed on each model card." I did not find the list on either model card. **Commercial-use status of the vision variant is unverified** for that reason.

**Gated?** Not stated on either HF card. Both pages show no access-request text. Treat as not gated, but unverified until you open the page while logged out.

**Sizes**
- 4B: 4.69B parameters, bf16. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b. Checkpoint size "9.7 GB in bf16" comes from a secondary source only: https://www.orcarouter.ai/blog/what-is-rsi-jev (secondary). Shard sizes not listed on the HF card.
- 27B: 26.66B parameters, bf16. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b. File sizes unknown.
- Base models: 4B from Qwen/Qwen3.5-4B-Base; 27B from Qwen/Qwen3.8-27B. Sources: the two HF cards above.

**Quantizations**
- None published for the 4B on HF. The GitHub README mentions MLX builds of the 4B with "8-bit, lossless; 4-bit, smaller" (Apple silicon; not relevant on this box). Source: https://github.com/Shanghua-Gao/RSI-Jev
- 27B: "There is no smaller build of it." Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b

**VRAM at 12 GB**
- 4B bf16 weights: 4.69B x 2 bytes = ~9.4 GB (estimate). The vision tower and decision heads add to this, and KV cache and activations are on top. **Fits 12 GB only just, with little room left.** No published quant, so a fit-friendly 8-bit build would have to be made by you. Unverified whether it works.
- 27B: 26.66B x 2 bytes = ~53 GB bf16. The card says it "runs in bf16 on one 96 GB GPU" with peak 84.3 GB at a 32,768-token cap. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b. **Does not fit 12 GB.** At 4-bit, weights alone are ~13 GB (estimate), which still does not fit, and no 4-bit build is published.

**Inference runtime**
- Own server: `rsi-jev serve v6.1-vl-4b`, plus a Python `Decider` class. Install: `pip install "rsi-jev[fast,vision]"` from the GitHub repo. Apple silicon uses an MLX backend. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b and https://github.com/Shanghua-Gao/RSI-Jev
- Underlying engine (transformers, vLLM, llama.cpp): **unknown**. The HF card shows no Transformers usage.
- No GGUF build seen.

**Image input**
- Images passed as a list of file paths (`images=["photo.jpg"]`) with an `<image>` placeholder in the prompt. Source: https://github.com/Shanghua-Gao/RSI-Jev (fetched README). The HF card says the model "takes text plus up to four images." Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b
- Image formats and max resolution: **unknown**.
- Pairwise (two images in one call): the API accepts a list of images, but the card does not say whether pairwise comparison is supported. **unknown**. You can likely express A vs B as a two-option choice question with two images in one call (up to four allowed), but that is my inference, not a documented mode. **unverified**.

**Output**
- Each question returns a probability for every option from one forward pass, no generated text. Responses include `confidence` (a different number from the probability) and `usage.depth` (answering layer). Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b and the 27B card for the 27B.
- Raw logprobs: **unknown**.

**Calibration claims**
- ECE values reported in the README: 0.0736 (v1.0 stage), 0.0546 (v2.0), 0.066 (v3.0), 0.043 (v4.0-VL), 0.042 (v5.0-VL after calibration). Source: https://github.com/Shanghua-Gao/RSI-Jev
- v6.1-VL 4B final ECE: 0.048 at layer 32, 0.055 with `auto`; v6.0-VL comparison 0.036 and 0.024; release bar 0.078. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b. Note the GitHub README gives the averaged v6.1 ECE as 0.048 against 0.036 for v6.0-VL, which agrees with this.
- 27B: Decision Index 0.3 public set 65.64 with `auto` ("official score pending"); Decision Index 0.2.1 64.92; held-out 0.808. Source: https://github.com/Shanghua-Gao/RSI-Jev. These are self-reported, **unverified**.

**Latency (self-reported, H200)**
- 4B median per request: default 39.9 ms; auto 28.4 ms; low (layer 16) 22.5 ms; medium (layer 20) 26.8 ms; high (layer 32) 40.4 ms. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b. Another set of numbers in the GitHub README gives 23 / 27 / 40 / 28 ms for the same layers; both are self-reported.
- 27B: unset 57.8 ms median; auto 45.5 ms median on H200; RTX PRO 6000 median 105.7 ms. Source: https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b. No 12 GB GPU numbers.

---

## 2. StartLux-Decision (0.8B to 27B)

**Publisher / repos**
- Publisher: StartLux Labs / StartLux Labs org `startlux-models` on HF. Source: https://github.com/StartLuxLabs/Startlux-Decision (code), collection: https://huggingface.co/collections/startlux-models/startlux-decision-6abba92b301b573fa154d493
- Collection lists 21 repos (fetched). Sizes listed for the v1 family: 0.8B, 2B, 4B, 9B, 27B (each with BF16 and GGUF variants), plus 35B-A3B. The collection's listed sizes don't match names (4B shown as 5B, 9B as 10B, 27B as 28B). Source: collection page above.
- Repo IDs: `startlux-models/StartLux-Decision-v1-{0.8B,2B,4B,9B,27B}`, `...-v1-35B-A3B`, and GGUF variants `...-Q8_0-GGUF`, `...-Q4_K_M-GGUF`, `...-BF16-GGUF`.
- Versions: v1.1 (Instant and AutoThink modes), and v1 (per secondary sources listed on Featherless). Source for v1.1 claims: secondary only, https://featherless.ai/models/startlux-models/StartLux-Decision-v1.1-4B-Instant (secondary). Confirm on HF.

**License**
- Weights: CC BY-NC 4.0, non-commercial. Commercial use needs "a separate license from StartLux Labs." Sources: https://huggingface.co/startlux-models/StartLux-Decision-v1-27B (YAML `cc-by-nc-4.0`, link https://creativecommons.org/licenses/by-nc/4.0/); https://huggingface.co/startlux-models/StartLux-Decision-v1-4B-Q4_K_M-GGUF; https://github.com/StartLuxLabs/Startlux-Decision
- Code: Apache-2.0 (`LICENSE` file). Source: https://github.com/StartLuxLabs/Startlux-Decision
- **Commercial use: not allowed without a separate license.**

**Gated?** Unknown. Neither the 27B nor the 4B GGUF card states it. Unverified.

**Sizes and quants**
- 4B Q4_K_M GGUF: 2.71 GB (confirmed). Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-4B-Q4_K_M-GGUF
- All other GGUF file sizes: unknown in the sources I read.
- 27B: 28B-listed, Safetensors, BF16 tensor type. Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-27B. Total size unknown. The card says it has four quantized models but does not list them in the fetched text.
- Quants listed by the GitHub README: GGUF Q8_0 (shown in the example), Q4_K_M (discussed; "can lose up to 4.3 points"), MLX 8-bit and 4-bit, FP8. "FP8 and GGUF Q8_0 largely preserve BF16 decision performance." Source: https://github.com/StartLuxLabs/Startlux-Decision. FP8 repo ID is not in the collection listing I fetched.

**VRAM at 12 GB**
- 4B Q4_K_M GGUF: 2.71 GB file (confirmed); fits. **But text only.** Source: GGUF card above.
- 4B bf16 safetensors: estimate ~8 to 10 GB (4B x 2 bytes, listed at 5B on the collection). **Fits 12 GB, tight.** Unverified.
- 9B: Q4_K_M and Q8_0 sizes unknown. My estimate: Q4_K_M ~5.5 GB, Q8_0 ~9.5 GB, bf16 ~18 GB, so bf16 does not fit. Text only for GGUF. Images need safetensors or FP8.
- 27B: estimate Q4_K_M ~16 GB (not confirmed). **Does not fit 12 GB.** The card says a 27B model supports up to 262,144 tokens of context, which is a KV-cache concern. Unverified.
- 35B-A3B: MoE, 36B listed. **Does not fit 12 GB** (estimate; file size unknown).

**Inference runtime**
- vLLM (default; Python package `startlux_decision` with a vLLM plugin)
- StartLux-Prism (NVIDIA GPUs, GGUF files; not described in detail)
- llama.cpp (GGUF). Needs build b10454 or newer. Plain chat does not produce typed decisions; you must run the StartLux server in front: `python -m startlux_decision.gguf_server --model-dir . --llama http://127.0.0.1:8081 --port 8090`. Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-4B-Q4_K_M-GGUF
- MLX (Apple silicon, text only)
- transformers: "reference checks" in the README; the 27B card says it is "more than ten times slower" than the fast path. Source: https://github.com/StartLuxLabs/Startlux-Decision and https://huggingface.co/startlux-models/StartLux-Decision-v1-27B
- Optional fast kernels: `flash-linear-attention` and `causal-conv1d`; CUDA graphs recorded at startup. Source: 27B card.
- Python API: `decide`, `decide_batch`. Source: 27B card.

**Image input**
- Text, JSON, or images as "state." Images passed as base64 strings or data URIs (HTTP), or as PIL images, file paths, encoded bytes (Python). A `<image>` marker in the state sets where each image goes. Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-27B
- Images are "used as evidence" through an `images` control. Source: https://github.com/StartLuxLabs/Startlux-Decision
- **GGUF and MLX builds are text only.** The vision tower is in the safetensors. Source: 27B card and 4B GGUF card.
- Max resolution: unknown. Only the 262,144-token context limit is stated.
- Two images in one call (pairwise): **Not mentioned** in the README or the 27B card. Treat as unknown. The typed-question format (`choice` with options) could express A vs B, but this is not a documented pairwise mode. **unverified**.

**Output format**
- `choice`: per-option `probabilities`, plus `confidence` and `none_probability`. `noul`: probability of yes. `score`: expected level plus a probability per level. Source: https://github.com/StartLuxLabs/Startlux-Decision
- Responses follow the TypeSafe `/v1/systemone` format. Source: 27B card.
- Raw logprobs: not mentioned.

**Calibration claims**
- "A calibrated probability for every option in one pass" (README). Source: https://github.com/StartLuxLabs/Startlux-Decision
- AutoThink is "trained with RLCD," described as reinforcement learning for calibrated deliberative decisions. Source: https://github.com/StartLuxLabs/Startlux-Decision
- Suggested `none_probability` threshold 0.2 "catches two thirds (66.3%)" of questions where all options are wrong, with 2.2% false flags. Default gate 0.6; published results use 0.9. Source: same README. **Self-reported, unverified.**
- Benchmark: a secondary source says the v1.1 27B Instant scored 69.1 on Decision Index 0.3.2. Source: https://www.woshipm.com/ai/6480452.html (secondary, Chinese). The German article notes these are self-tests. Source: https://eu.36kr.com/de/p/4009510615027849 (secondary). **Unverified.**

**Latency (self-reported, one H200, bf16, HTTP, one request at a time)**
- Instant models: 25 to 52 ms median (0.8B to 27B), one question. Source: https://github.com/StartLuxLabs/Startlux-Decision
- AutoThink readout: 38 to 59 ms when sure, longer when reasoning.
- 27B card: one yes/no question 50.7 ms; three questions 102.3 ms; comparison 9B 35.7 ms, 4B 26.0 ms (three questions). Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-27B
- No 12 GB GPU numbers.

**Context**: 27B card says up to 262,144 tokens. Source: https://huggingface.co/startlux-models/StartLux-Decision-v1-27B. A v1.1 4B listing on Featherless says 32,768 (secondary). The sources disagree; the card is the primary source for the 27B.

---

## 3. Simple Jev (JevAny, SimpleJev org)

**Identification**: "Simple Jev" maps to the SimpleJev org's JevAny project. Official GitHub: https://github.com/SimpleJev/JevAny (the search snippet also referenced a wiki at https://github.com/SimpleJev/JevAny/wiki). HF org: https://huggingface.co/SimpleJev/models. **Identification is my inference from the names; unverified against a project page that explicitly says "Simple Jev."** Hosted via Featherless (beta, secondary): https://featherless.ai/simple-jev/

**What it is**: "Open infrastructure for training, evaluating, and deploying System 1 decision models across language and multimodal backbones," and "26 supported models across Qwen, Gemma, Muse, Mistral, GLM, Nemotron and Llama." Source: https://github.com/SimpleJev/JevAny

**License**: Apache-2.0 for the project (README). Source: https://github.com/SimpleJev/JevAny. The base model is "loaded separately," with its own license terms. Checkpoint licenses on HF: unknown.

**Checkpoints (LoRA adapters)** from https://huggingface.co/SimpleJev/models:
- `SimpleJev/JevAny-Qwen3.8-27B-LoRA` (27B; default)
- `SimpleJev/JevAny-Muse-Glimmer-30B-LoRA` (30B)
- `SimpleJev/JevAny-Qwen3.5-4B-LoRA` (4B)
- `SimpleJev/JevAny-Qwen3.5-4B-Direct-Token-LoRA` (4B)
- `SimpleJev/JevAny-Gemma-4B-LoRA` (4B)
- `SimpleJev/JevAny-Robotics-4B-LoRA` (4B; tagged "Robotics")
- Starter recipe: Qwen3.5-0.8B.

Sizes, gating, and license per repo: **unknown** (the HF page shows none). Source: https://huggingface.co/SimpleJev/models

**Vision**: The page does not separate text and multimodal support per model, and "Gemma-4B" is the only vision-candidate name. Whether any Simple Jev LoRA is actually a vision model: **unknown**. Image format and max resolution: **unknown** ("follow the media setup" for image and video).

**VRAM at 12 GB**: depends on the base. A 4B base in bf16 is ~8 to 9 GB (estimate). The 27B and 30B bases do not fit 12 GB. Quantization: unknown; the page mentions BF16 weights only.

**Runtime**: Python 3.12+, CUDA or CPU. BF16 LoRA merging, SDPA, and `torch.compile` optional. Source: https://github.com/SimpleJev/JevAny

**Pairwise**: unknown.

**Output**: "One API takes the state, question and candidate options, then directly returns a choice and its probabilities." Option limits: up to 4,096 options (pointer mode), 255 (direct-token mode). Source: https://github.com/SimpleJev/JevAny

**Calibration**: NLL, Brier, ECE reported on a "Transfer" set. JevAny-Qwen3.8-27B: NLL 0.388, Brier 0.195, ECE 0.026. RLCR "experimental." Temperature "changes confidence, not argmax." Source: https://github.com/SimpleJev/JevAny. **Self-reported.**

**Latency (self-reported, H200, batch 1, median)**: Qwen3.8-27B 113.54 ms to 30.53 ms with CUDA acceleration; Muse-Glimmer-30B 100.71 to 43.25 ms; 4B models on A100 about 3.3x to 4.1x speedups. Source: https://github.com/SimpleJev/JevAny. No 12 GB numbers.

---

## 4. open-alternative-jev (fallback)

**Identification**: The exact name "open-alternative-jev" was not on HF. The project is **ikermoel/open-alternative-jev** on GitHub. Source: https://github.com/ikermoel/open-alternative-jev. Trendshift listing: https://trendshift.io/repositories/244523 (76 stars per the "Stars +76 in 48 days" block; the count is ambiguous on the page).

**Publisher**: ikermoel (GitHub user). **Unverified** whether this is a company or an individual.

**License**: Apache-2.0 (README and LICENSE). Source: https://github.com/ikermoel/open-alternative-jev. Commercial use allowed by the license; the base models carry their own licenses, which I did not check per model.

**Gated?**: n/a (wrapper). Base models are Qwen repos; their gating not checked.

**What it is**: "Open-source alternative to TypeSafe's Jev: a System One style model layer." Python package `open-alternative-jev`, import name `so1`. Runs in-process, not an HTTP server. Source: https://github.com/ikermoel/open-alternative-jev

**Backends**: Hugging Face Transformers (`backend="hf"`) and vLLM (`backend="vllm"`). Source: same.

**Base models tested or recommended**:
- Qwen/Qwen3.6-27B (primary benchmark, 8-bit)
- Qwen/Qwen3.5-4B
- Qwen3.5-2B, Qwen3-1.7B, Qwen3-0.6B (Qwen3-0.6B-FP8 and BF16 on vLLM)
- Qwen/Qwen2.5-0.5B-Instruct (test suite)
- Any ChatML-template model works. Source: same.
- Vision/VLM base models named: **unknown**. None in the README I read. **I did not find any vision base model that people use with it.** Searches on "Qwen3-VL", "LFM2.5-VL", and "Gemma" for Jev wrappers returned nothing relevant. Source: https://www.datacamp.com/blog/top-open-source-jev-alternatives (did not name any vision model).

**VRAM at 12 GB**: Qwen3.6-27B 8-bit needs about 30 GB (README: "a CUDA GPU with about 30 GB"). Does not fit 12 GB. Qwen3.5-4B: no VRAM figure given. Estimate: bf16 ~8 to 9 GB; fits, tight. Source for the 30 GB number: the GitHub README.

**Output**: For each question, a typed answer that is always one of the user's options, plus a probability. Probabilities are a softmax over option letters A to Z (max 26 options). Optional `TemperatureScaler` gives calibrated probabilities. `permutations=2` averages both option orders. Source: https://github.com/ikermoel/open-alternative-jev

**Pairwise**: unknown. Choice format with two options is possible; not documented as a pairwise mode. **unverified**.

**Image input**: unknown. No image mention found in the README I read.

**Benchmarks (self-reported, 'typed-decisions' suite)**:
- Qwen3.6-27B zero-shot: 73.7% accuracy, KL 0.27, ECE 0.020, 582 ms per case (p50, one H200 MIG slice, 8-bit).
- Qwen3.6-27B with `permutations=2`: 75.5% accuracy, ECE 0.0075, 969 ms per case.
- Jev 1.13.0, as measured by these authors: 72.7% accuracy, ECE 0.144, 710 ms per case.
- MMLU: 84.9%, RACE-H 92.9% (Qwen3.6-27B).
- Qwen3.5-4B library run: 49.6 questions/s packed (Transformers); 38.7 questions/s (vLLM).
- Laya 421M: 23 ms per case (comparison, not a supported base).
Source: https://github.com/ikermoel/open-alternative-jev. **All self-reported, unverified.**

---

## 5. Reference only: hosted Jev 1.14 (TypeSafe)

Not run locally.

**Publisher**: TypeSafe AI. Official docs not found in search. Endpoint `POST https://api.typesafe.ai/v1/systemone` with a bearer key, default model `jev-latest` (two secondary sources, not verified against TypeSafe docs). Sources: aggregators only.

**Pricing** (all secondary, conflicting):
- $0.042 per million input tokens, output free. Source: https://www.eesel.ai/blog/typesafe-jev-pricing (secondary)
- $0.0577668 per million input tokens, output free. Source: https://aimlapi.com/models/typesafe-jev-latest (secondary)
- $0.04 per million input tokens for jev-1.14.0. Source: https://www.requesty.ai/models/typesafe/jev-1.14.0 (secondary)
- One source says TypeSafe has no dedicated pricing page. Source: the eesel article. **Unverified; confirm with TypeSafe.**

**Image support**:
- Experimental and gated behind an opt-in header `TypeSafe-Danger-Zone-Images: true`, per each request. Without it, requests with image parts get a 400 error or have parts dropped. Sources: https://docs.litellm.ai/docs/decisions/typesafe_images (LiteLLM; fetch returned empty, the claim comes from the search snippet, **unverified**); https://www.remio.ai/post/jev-1-14-0-release-expands-what-jev-can-see-but-typesafe-wont-call-it-production (secondary); https://alternativeto.net/news/2026/10/typesafe-ai-ships-jev-1-14-with-new-box-type-composable-images-and-longer-context-length/ (secondary; confirms the header and "danger zone" label).
- Formats: PNG and JPEG (secondary: https://pasqualepillitteri.it/en/news/26048/jev-1-14-image-input-box-typesafe-warns). Size limits: unknown.
- TypeSafe warns against production use. A successful response does not guarantee an object is in the image (secondary).
- Sources disagree on whether 1.13 supports images. AlternativeTo says 1.13 "was multimodal all along." LiteLLM (per snippet) puts image input on 1.14 and 1.13 as a plain model. **Unresolved.**
- Alias: `jev-preview` points to 1.14 per the AlternativeTo article; `jev-latest` rolls to 1.14 about a week after launch. Secondary sources conflict. Pin `jev-1.14.0` for reproducible behavior (itechguides, secondary).

**Box type** (1.14 only): returns a single bounding box; coordinates are fractions of height and width from the top-left. Source: AlternativeTo (secondary); LiteLLM (secondary).

**Output format**: "typed decisions, complete with probabilities and confidence levels." Source: https://alternativeto.net/news/2026/10/typesafe-ai-ships-jev-1-14-with-new-box-type-composable-images-and-longer-context-length/ . Option limits and full schema: unknown.

**Context length**: a MarkTechPost headline says "262k Context" (secondary, not fetched). Source link not fetched. **Unverified.**

**Pairwise**: not stated. **unknown.**

**Latency**: unknown.

---

## Cross-cutting notes for the judge decision

1. Only 4B-class models fit 12 GB at a usable quant. The 27B tiers of RSI-Jev, StartLux, OpenJev, and the Simple Jev base need either more VRAM or a 4-bit build that is not published (except StartLux's GGUF and OpenJev's GGUF, which are text only).
2. Text-only GGUF builds cannot take images. For vision on this box, the candidates are RSI-Jev 4B (bf16, ~9.4 GB, tight) and StartLux 4B safetensors (estimate ~8 to 10 GB).
3. Licensing: StartLux and OpenJev weights are non-commercial. RSI-Jev is Apache-2.0 with some non-commercial image training sources unlisted. open-alternative-jev is Apache-2.0 as a wrapper (base model licenses apply).
4. Pairwise: none of the local candidates documents a two-image comparison mode. A two-option choice question with two images could be tried in each; that needs a test, not a claim.
5. Calibration and latency are all self-reported. None of them measured on a 12 GB GPU.

## Open questions

- Confirm RSI-Jev 4B HF gating and whether the vision variant is commercially usable (which image sources are non-commercial).
- StartLux: file sizes for every GGUF and the 9B/27B safetensors; FP8 repo IDs; whether two images are accepted in one `choice` question.
- open-alternative-jev: which vision base models work, and whether the `so1` library accepts images. Currently no evidence.
- Simple Jev: which LoRA, if any, is a vision model, and its base license (Qwen3.5-4B and Gemma-4B are the 4B options).
- Jev 1.14: confirm pricing and image limits with TypeSafe directly; resolve the 1.13 image conflict.
- All latency numbers are H200/H100/RTX PRO 6000/RTX 5090, not 3060. No 12 GB measurements found.

## Sources (primary unless marked)

- https://github.com/Shanghua-Gao/RSI-Jev
- https://huggingface.co/shgao/rsi-jev-v6.1-vl-4b
- https://huggingface.co/shgao/rsi-jev-v6.1-vl-27b
- https://www.orcarouter.ai/blog/what-is-rsi-jev (secondary)
- https://github.com/StartLuxLabs/Startlux-Decision
- https://huggingface.co/collections/startlux-models/startlux-decision-6abba92b301b573fa154d493
- https://huggingface.co/startlux-models/StartLux-Decision-v1-27B
- https://huggingface.co/startlux-models/StartLux-Decision-v1-4B-Q4_K_M-GGUF
- https://featherless.ai/models/startlux-models/StartLux-Decision-v1.1-4B-Instant (secondary)
- https://www.woshipm.com/ai/6480452.html (secondary)
- https://github.com/SimpleJev/JevAny
- https://huggingface.co/SimpleJev/models
- https://featherless.ai/simple-jev/ (secondary)
- https://github.com/ikermoel/open-alternative-jev
- https://trendshift.io/repositories/244523 (secondary)
- https://huggingface.co/openjev/openjev (27B; OpenJev, see below)
- https://pypi.org/project/jev-style/ (fetched; Apache-2.0, Qwen3.5 base; not one of the named candidates, see below)
- https://www.eesel.ai/blog/typesafe-jev-pricing (secondary)
- https://aimlapi.com/models/typesafe-jev-latest (secondary)
- https://www.requesty.ai/models/typesafe/jev-1.14.0 (secondary)
- https://alternativeto.net/news/2026/10/typesafe-ai-ships-jev-1-14-with-new-box-type-composable-images-and-longer-context-length/ (secondary)
- https://pasqualepillitteri.it/en/news/26048/jev-1-14-image-input-box-typesafe-warns (secondary)
- https://www.remio.ai/post/jev-1-14-0-release-expands-what-jev-can-see-but-typesafe-wont-call-it-production (secondary)
- https://docs.litellm.ai/docs/decisions/typesafe_images (not fetched successfully; cited from search snippet, unverified)

### Note on OpenJev (not in the named batch)

OpenJev (https://huggingface.co/openjev/openjev) came up in search as a 27B vision-capable Jev-style model. It was not on the candidate list, but for the record: 27B BF16 ~54 GB, FP8 ~29 GB, GGUF Q4_K_M 16.5 GB (text only, GGUF/MLX builds are text only); image input in BF16 and FP8 builds, one image per request; CC BY-NC 4.0 weights; latency ~80 to 227 ms on one H100 FP8 (self-reported). Does not fit 12 GB. Source: the HF page above.
