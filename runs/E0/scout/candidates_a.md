# Scout findings: batch A (image-capable "System One" judges)

Date of research: 2026-11-03. Research only. No weights downloaded, no code run.

Source-quality note: several facts come from pages I read through a summarizing fetch, not a raw copy. Those are cited to the page, but the wording was summarized, so quote-level claims should be re-checked on the page before relying on them. Anything not stated on a primary page is marked **unknown** or **unverified**.

Hardware target: RTX 3060 12 GB VRAM, 64 GB RAM.

---

## 0. What "Jev" / the "Jev API" is

- **Publisher:** TypeSafe. Jev is described as TypeSafe's "System One" decision model, which returns typed answers instead of generated text. Sources: https://docs.aimlapi.com/api-references/decision-models/typesafe/jev-1.14.md (hosted via AIMLAPI, which says TypeSafe publishes it); https://vercel.com/changelog/typesafe-ais-jev-1-14-isnow-available-on-ai-gateway ; imajev README cites "TypeSafe's own Jev 1.13.0" and docs.typesafe.ai (https://github.com/mohit67890/imajev).
- **Hosted endpoint (Jev 1.14 via AIMLAPI):** `POST https://api.aimlapi.com/v1/decisions`, body `model: "typesafe/jev-1.14"`, required `model`, `state`, `questions`. Question types: `noul` (yes/no), `choice`, `score`, `box`. Images go in an `assets` map (`format` png/jpg/jpeg, `data_base64`, no `data:` prefix, no whitespace), not `images`. Images are PNG/JPEG stills, 256–1568 px a side, max 16 MiB each. Images and `box` are marked experimental.
- **Response:** `model`, `answers`, `usage`, `meta`. `noul` returns a probability of "yes". `choice` returns the chosen key, `confidence`, and per-option `probabilities`. `score` returns an expected level, `confidence`, `legend`, per-level `probabilities`. `box` returns `top/bottom/left/right` as image fractions plus `confidence`. Probabilities and confidence are included. Logprobs are not mentioned.
- **Self-hosted Jev-shaped servers seen so far (all claim compatibility):**
  - OneJev: `POST /v1/systemone`. Request `state`, `questions` (types noul/choice/score), `media` array (base64 data URIs). Response `answers.<id>.noul` (P(yes)), `answers.<id>.probabilities`, `answers.<id>.score`. Source: https://raw.githubusercontent.com/OmniJev/OneJev/main/README.md
  - Vev: `vev serve` implements the `/v1/systemone` request/response shapes; `state` takes text, JSON or images; question types `noul`, `choice`, `score`; ships a conformance suite. Source: https://github.com/Xiaooolong/vev/releases/tag/v0.1.0
  - imajev: `POST /v1/systemone`, adds an `images` field plus `unknown_probability` and `abstained`. States that text-only Jev requests work unchanged. Source: https://github.com/mohit67890/imajev
  - AutoTrust JEV-27B-VL: a different server shape: `POST /v1/decide` with `kind`, `state`, `question`, `options`; response has `probabilities`, `choice_index`, `choice`, `adaptation`, `elapsed_seconds` and others. Source: https://huggingface.co/AutoTrust/JEV-27B-VL
- **Do the outputs include a probability/confidence?** Yes, across the Jev 1.14 hosted API and all self-hosted candidates below. Calibration claims are the publisher's own; see per-candidate notes.
- **"Jev-compatible" is not one spec.** The hosted Jev 1.14 API uses `/v1/decisions` with `assets`. The self-hosted servers use `/v1/systemone` (OneJev, Vev, imajev) or `/v1/decide` (AutoTrust JEV-27B-VL) with different shapes. Treat "compatible" as a claim to test against each server, not as a fact.
- **Pairwise:** Jev's `choice` question type with two options is the natural way to do A-vs-B. Pairwise is not a separate endpoint in these specs.

---

## 1. imajev

- **Found:** yes (not on Hugging Face under that name; the search hit a different repo, see below).
- **Repo:** https://github.com/mohit67890/imajev
- **HF repos (from README):** https://huggingface.co/mohit67890/imajev-2b , https://huggingface.co/mohit67890/imajev-4b , https://huggingface.co/mohit67890/imajev-9b ; bench dataset https://huggingface.co/datasets/mohit67890/imajev-bench (per README); demo Space mohit67890/imajev.
- **Publisher:** Mohit Garg (GitHub mohit67890), an individual. Not TypeSafe. Built on the Jev spec.
- **License:** Apache-2.0 (code and adapters per README). Base models Qwen3.5 (Apache-2.0). Source: GitHub README above. **Verify the license file on the repo and on each HF repo before relying on it.**
- **Gated:** not stated in README. **unverified** (HF pages not fetched successfully).
- **Sizes and download:**
  - 2B: 4.6 GB download (README).
  - 4B: 9.3 GB download; the README recommends it as the default.
  - 9B: 19.3 GB download; "needs ~19 GB resident" (README, Mac context).
- **Quants:** GGUF not mentioned. MLX weights for Mac are mentioned. CUDA path is BF16 via PyTorch, with an optional `--fast --merge-lora` path.
- **VRAM estimate for 12 GB (my estimate, not from source):**
  - 2B: BF16 weights about 4.6 GB, fits.
  - 4B: BF16 weights about 9.3 GB; fits with small context, but tight. Estimate, **unverified**.
  - 9B: BF16 weights about 19 GB, does not fit without quantization. No quant is provided, so a 4-bit build would have to be made by hand. **unknown** whether a GPU quant is viable.
- **Runtime:** PyTorch on Linux/CUDA (`--backend torch`), optional `--fast --merge-lora`. MLX on Mac. Own server (`POST /v1/systemone`, multipart upload with `-F image=@photo.jpg` and a `request` JSON field).
- **Image handling:** multipart upload. Max resolution **unknown**. Verify.
- **Two images in one call:** yes, up to 2 ("reference + target"). README calls two-image comparison "the weakest visual task."
- **Probabilities / calibration:** yes. `choice` and `score` return probabilities summing to 1. `noul` returns P(yes) with half the unknown mass added. Each answer includes `unknown_probability`, `abstained`, `confidence`. Calibration: one temperature per size (2B 1.646, 4B 1.305, 9B 1.748) via `--calibration`. On JevBench hard, 4B ECE goes 0.113 raw to 0.082 as shipped. README notes the ImajevBench test split helped choose checkpoints, and its images are AI-generated with no human audit yet.
- **Latency (self-reported):**
  - 4B raw about 0.1 s per question, about 0.3 s as shipped (four option orders averaged).
  - One H100 under load, 4B p50 350 ms (96 ms raw); 2B 238 ms and 9B 316 ms as shipped.
  - Mac Studio: 1.15 s for three questions.
  - Hardware for the 12 GB 3060 **unknown**.
- **Source for above:** https://github.com/mohit67890/imajev

---

## 2. Vev

- **Found:** yes, but only one release note found. Repo: https://github.com/Xiaooolong/vev ; release https://github.com/Xiaooolong/vev/releases/tag/v0.1.0
- **Publisher:** GitHub user Xiaooolong. Individual or unknown org; not confirmed.
- **Models:** `vev-4b` and `vev-9b`, released as merged weights and as adapters (`vev-4b-lora`, `vev-9b-lora`). Base Qwen3.5-4B and Qwen3.5-9B, LoRA fine-tuned. Source: release page above.
- **License:** CC BY-NC 4.0 ("Weights are CC BY-NC 4.0."). **Non-commercial: no commercial use.** Source: release page above. Confirm on the HF model cards (HF URLs not found).
- **Gated:** not stated. **unverified** (HF cards not fetched).
- **Sizes and download:** **unknown**. Not stated in release.
- **Quants:** GGUF/AWQ/bnb **unknown**.
- **VRAM for 12 GB:** **unknown**. A 4B merged BF16 model would be about 8 GB by parameter count (estimate, unverified). The 9B would not fit in BF16.
- **Runtime:** `vev serve` (its own HTTP server implementing `/v1/systemone`). Underlying runtime **unknown**.
- **Image resolution and passing:** `state` accepts images. Resolution limits **unknown**.
- **Pairwise (two images in one call):** **unknown**. Not stated.
- **Probabilities:** the server implements `noul`, `choice`, `score`, so probabilities are implied by the shape. Calibration claims **unknown**.
- **Latency:** **unknown**.
- **Caveat:** this is a research preview (0.1.0). Vev and Jeva (https://huggingface.co/LIQIIIII/Jeva-4B/discussions/3) are different projects. Jeva's license is unclear in a HF discussion, and the maintainer did not state a license there.

---

## 3. Saina Omni (0.8B)

- **Found: no.** Searches on "Saina Omni 0.8B Jev compatible", "Saina omni model 0.8B huggingface", and related phrasing returned only unrelated omni-modal papers (Ming-Omni, InteractiveOmni, Megrez-3B-Omni, Baichuan-Omni-1.5, MiniMind-O) and unrelated HF repos (sovthpaw/senter-omni-model, StarJiaxing/R1-Omni-0.5B, ICTNLP/Llama-3.1-8B-Omni).
- Not confirmed: the name, publisher, license, gating, sizes, quants, runtime, pairwise support, or probabilities. All **unknown**.
- Possible name mix-up with another project. Ask the user for a URL or publisher.

---

## 4. OneJev

- **Found:** yes. Repo: https://github.com/OmniJev/OneJev (README at https://raw.githubusercontent.com/OmniJev/OneJev/main/README.md). Wiki https://github.com/OmniJev/OneJev/wiki.
- **Publisher:** OmniJev (GitHub org). Not TypeSafe.
- **Sizes:** 0.8B, 4B, 9B, 27B (README).
- **Base:** Qwen. Fine-tuning starts from Qwen3.5-0.8B, Qwen3.5-4B, Qwen3.5-9B and Qwen3.8-27B (README).
- **HF:** collection https://huggingface.co/collections/OmniJev/onejev16 ; data https://huggingface.co/datasets/OmniJev/OneJev-Data ; demo https://huggingface.co/spaces/BradNLP/OneJev ; examples https://huggingface.co/OmniJev/OneJev1.6-0.8B (page reads "0.9B params", description "0.8B"), https://huggingface.co/OmniJev/OneJev1.6-27B (27B).
- **License:** Apache 2.0 (README "Apache 2.0"; HF tags "license: apache-2.0" on both pages checked).
- **Gated:** not stated on the HF pages fetched. **unverified** for each size.
- **Download sizes:** **unknown**. The HF pages show monthly downloads, not file sizes. The 0.8B page lists a "Files and versions" tab but did not show the file list.
- **Quants:** GGUF available. Example `mradermacher/OneJev1.6-0.8B-GGUF:Q8_0` (README). "Browse Quantizations" shows 2 models for 0.8B and 1 for 27B. Quant names/sizes **unknown**.
- **VRAM for 12 GB (my estimate):**
  - 0.8B BF16 about 2 GB: fits easily (estimate).
  - 4B, 9B: BF16 weights about 8 GB and 18 GB by parameter count; the 9B needs a quant. Official VRAM figures: **unknown**.
  - 27B: does not fit 12 GB without heavy quantization. Not fit-able in practice.
- **Runtimes:** Flide (NVIDIA; text, images, video; `flide serve` gives an OpenAI-compatible API), llama.cpp (GGUF; text and images, not video), PyTorch (`torch` profile, supports video). Docker profiles: torch, rocm, vulkan, gguf, gguf-rocm, cpu. On Windows only torch and cpu.
- **Image input:** base64 data URIs in a `media` array; state refers to them by placeholders like `<image:1>`. Max resolution **unknown**. Only a 1280x720 screenshot is mentioned.
- **Pairwise / multi-image:** **unknown**. HF pages say "a screenshot, a photo, a video or plain text" with single-image examples. Not stated.
- **Probabilities / calibration:** yes. README says the model "returns calibrated probabilities" in one forward pass. Training uses cross-entropy plus Brier loss. **No calibration metrics given.**
- **Latency (README, H200, one 1280x720 screenshot):**
  - 0.8B: 31 ms (1 q), 51 ms (10 q)
  - 4B: 64 ms, 104 ms
  - 9B: 81 ms, 131 ms
  - 27B: 189 ms, 324 ms
  - Hardware for 3060: **unknown**.
- **API:** `POST http://localhost:8000/v1/systemone`. Request: `state` (`task`, `screen`), `media`, `questions` (map of id to `type`, `instructions`, `criteria`). Response: `answers` (noul P(yes); choice `probabilities`; score expected level).
- **Benchmark figures:** the 1.5 27B "63.64 on the public part of Decision Index 0.3, fifth of 148" came from a third-party listing (Featherless) and is **unverified**. Featherless: https://featherless.ai/models/OmniJev/OneJev1.5-27B

---

## Aside: AutoTrust JEV-27B-VL (the search's first hit, not one of the four)

Relevant because the first search returned it for "imajev". It is not imajev.

- Repo: https://huggingface.co/AutoTrust/JEV-27B-VL
- Publisher: AutoTrust. Built on Qwen3.8-27B, with a System 1 adapter and decision head.
- License: Apache-2.0 (weights of Qwen3.8-27B unchanged plus adapter).
- Gated: not stated; direct download command shown. **unverified** whether gated.
- Size: about 28B BF16, about 52 GB weights. **Does not fit 12 GB** without quantization. Page says `serve.sh` needs 80 GB+.
- Quants: "Browse Quantizations" lists 12 quantized models; sizes **unknown**.
- Runtime: vLLM (needs a Sept 2026 dev build for `serve_decide.py`), SGLang, Docker Model Runner, Transformers.
- Images: up to 8 per prompt (`--limit-mm-per-prompt '{"image": 8}'`). Pairwise: the page describes a multimodal judge comparing two answers, recommending both orders averaged.
- Probabilities: yes; per-option. Calibration: held-out ECE 0.0009; vision board ECE 0.019 over 13,695 rows; 150 options ECE 0.079.
- Latency: about 264 ms per row (RTX PRO 6000, vision board); 1.4 s for a 150-option choice.
- Source: https://huggingface.co/AutoTrust/JEV-27B-VL

---

## Summary table

| Candidate | Found | License | Commercial OK | Gated | Fits 12 GB | Pairwise (2 images) | Probs |
|---|---|---|---|---|---|---|---|
| imajev | yes (GitHub) | Apache-2.0 | yes | unverified | 2B yes; 4B likely (BF16 ~9.3 GB, tight); 9B no without quant (not provided) | yes, max 2 images | yes, calibrated |
| Vev | yes (GitHub release) | CC BY-NC 4.0 | **no** | unverified | unknown | unknown | implied by `/v1/systemone` shape; calibration unknown |
| Saina Omni 0.8B | **no** | unknown | unknown | unknown | unknown | unknown | unknown |
| OneJev | yes (GitHub/HF) | Apache-2.0 | yes | unverified | 0.8B yes; 4B/9B BF16 likely tight or needs quant (sizes unknown); 27B no | unknown | yes, uncalibrated metrics |

---

## Open questions

1. Saina Omni: what is the exact name, publisher, and link? The search found nothing.
2. Vev: are the HF model cards gated, and what are the file sizes and any quant options? The license is CC BY-NC per the release page; the HF card should be confirmed.
3. imajev: is the 4B BF16 (9.3 GB) sufficient on a 3060 12 GB with the server's activation and context needs? Needs a test, not a read. Also confirm the Apache-2.0 license file on each HF repo.
4. OneJev: download sizes and quant file list for 0.8B/4B/9B. Pairwise/multi-image support is not stated in any source.
5. Jev hosted 1.14 is experimental for images. Compare its image behavior with the self-hosted servers before choosing.
6. No latency is published for a 12 GB consumer GPU by any candidate. Benchmark on the 3060 before deciding.
7. Calibration: only imajev and AutoTrust give ECE/temperature numbers. These are self-reported on their own benchmarks.
</content>
</invoke>
