---
title: "Tools that I need to try that just released in the last month"
date: 2026-09-26
type: research
tags: [AI, Research]
---

# AI Briefing: Tools & Releases Worth Trying — Last 30 Days

**Window covered:** ~Aug 27 – Sep 26, 2026 · **Compiled:** Sep 26, 2026

> **Verification note:** This briefing leans on a mix of primary sources (lab blogs, API changelogs, Hugging Face model cards, AWS/Google release notes) and secondary aggregators. Items marked **[1°]** were confirmed against a primary source; **[2°]** means secondary-only verification; **[?]** means rumored/unverified. Treat benchmark numbers as vendor-reported unless noted.

---

## Executive Summary

- **A frontier-model cadence spike hit Sept 22, 2026:** OpenAI shipped GPT-6 Sol/Luna (50% API price cut), Anthropic shipped Claude Opus 5.5 (tops the Artificial Analysis Intelligence Index at 58), and xAI shipped Grok 4.7 — all within ~24 hours. If you only try one thing this month, benchmark these against your actual workload.
- **Chinese labs now own the open-weights frontier.** Xiaomi's **MiMo-V2.6-Pro** (MIT, 1.02T MoE) scores 46 on the AA Intelligence Index — the highest of any open model and *tied with closed Grok 4.7*. DeepSeek V4.1 Flash (MIT), Tencent Hy4 (Apache 2.0), and GLM-5.3-Flash (MIT) round out the strongest open tier.
- **The "tool" story is agentic workspaces, not chatbots.** Claude Code Projects (parallel agent threads), Google Antigravity's managed-agent harness, Cursor Agent Skills, and Adobe's multi-model generative timeline in Premiere Pro all shipped in this window.
- **Extreme-sparsity MoE + linear attention is the dominant technical recipe** (4–8% active parameters, 1M-token contexts), and **speculative decoding is now default-on** in essentially every serving stack.
- **Caution:** a large share of "released this month" listicles recycle old news with new dates (e.g. Cursor 2.0 was Oct 2025). Items I could not anchor to a primary source are flagged inline.

---

## 1. Industry & Lab Announcements

### Frontier models (all shipped, publicly available)

| Tool | Lab | Date | Why try it | Access |
|---|---|---|---|---|
| **Claude Opus 5.5** | Anthropic | Sep 22 **[1°]** | #1 on AA Intelligence Index (58); Terminal-Bench 4.0 66.4%; 20% cheaper than Opus 5 ($4/$20 per M) | `claude-opus-5-5` via Claude apps, Claude Code, AWS/GCP/Azure |
| **GPT-6 Sol / Luna** | OpenAI | Sep 22 **[1°]** | ~50% price cut vs GPT-5.6; 1.05M context; Sol $2/$10, Luna $0.10/$0.50 per M | `gpt-6-sol`, `gpt-6-luna`; Luna in free desktop app |
| **Grok 4.7** | xAI | Sep 21 **[1°]** | Longer RL on multi-hour problems; overtakes GPT-5.6 Sol on Coding Agent Index; same price as 4.6 | `grok-4.7` API, Cursor model picker |
| **Gemini 3.8 Flash** | Google DeepMind | Sep 2 **[1°]** | Fastest measured at launch (~305 output tok/s); promo $0.75/$3.75 per M through Dec 31 | Gemini app, AI Studio, Antigravity, API |
| **Muse Spark 1.3** | Meta Superintelligence Labs | Sep 2 **[2°]** | Natively multimodal agentic/coding; ~25% fewer tokens for same work; cheap (~$0.10 blended) | Muse Code, Meta Model API |
| **Claude Fable 5.1** | Anthropic | Sep 1 **[1°]** | Most capable GA model at the time; new "preserved thinking" API controls | Claude Platform (paid) |

- **Sources:** [Anthropic news](https://www.anthropic.com/news) · [Artificial Analysis on Opus 5.5](https://artificialanalysis.ai/articles/claude-opus-5-5) · [OpenAI ChatGPT Images 2.5 post](https://openai.com/index/introducing-chatgpt-images-2-5) · [x.ai/news](https://x.ai/news) · [9to5Google Gemini 3.8 Flash](https://9to5google.com/2026/09/02/gemini-3-8-flash-launch)
- ⚠️ **Sora API retires Sep 24, 2026** and **ChatGPT Atlas browser was discontinued Aug 9** — migrations, not launches. Don't plan new work on either.

### Voice, image, and video

- **Gemini 3.8 Live + Live Extended Thinking** (Sep 15 **[1°]**) — reasons *while speaking*, with live progress narration; #1 on AA Speech-to-Speech Quality Index; 97 languages. → [DeepMind blog](https://deepmind.google/blog/)
- **Gemini 3.8 Flash TTS / Flash-Lite TTS** (Sep 23 **[1°]**) — **design a voice from a natural-language description**, not pick from a catalog; 2,000+ prebuilt voices, SynthID watermarking. → [blog.google](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-text-to-speech)
- **Gemini 3.8 Live with Live Avatar** (Sep 24 **[1°]**) — low-latency lip-synced streaming avatar, 97 languages. **Enterprise-only**, not self-serve. → [blog.google](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-with-live-avatar)
- **ChatGPT Images 2.5** (Sep 8 **[1°]**) — Flare (fast) + Sunburst (precision, long edit chains); up to 50% lower latency; 3840px. → [OpenAI](https://openai.com/index/introducing-chatgpt-images-2-5)
- **Seedance 2.5** (global via Dreamina, ~Sep 24 **[2°]**) — 30-second single-pass clips, native joint audio+video, 50 multimodal references. Resolution caps at 720p. → [OpenRouter review](https://openrouter.ai/blog/insights/seedance-2-5-review)

### Developer tools & agentic workspaces

- **Claude Code "Projects" (beta)** (Sep 17 **[1°]**) — one coordinator agent spinning up **parallel threads that share memory, artifacts, and routines**. Widely called the best Claude Code update of the year. → [Claude release notes](https://support.claude.com/en/articles/12138966-release-notes)
- **Google Antigravity — `antigravity-preview-09-2026`** (Sep 17 **[1°]**) — updated managed-agent harness on Gemini 3.8 Flash, plus new Files API and a Credentials API where **the model never sees your secrets**. Free individual tier. → [AI Studio](https://aistudio.google.com/learn/managed-agents-updated-harness-files-credentials)
- **Cursor Agent Skills** (Sept 2026 **[2°]**) — the open `SKILL.md` standard as a first-class citizen next to Rules/MCP. Same skill file works in Cursor, Copilot in VS Code, Copilot CLI, and Claude Code. → [tech-insider](https://tech-insider.org/cursor-skills-setup-agent-skills-2026)
- **Unity first-party plugins for Claude Code & Codex** (Sep 16 **[2°]**) — 29–31 maintained skills for Unity 6+, including live Editor control via MCP. → [shattered.io](https://shattered.io/unity-claude-code-codex-plugin-skills-2026)
- **Adobe Generative Media Tool in Premiere Pro** (Sep 8, IBC **[1°]**) — **five competing video models in one timeline toolbar** (Firefly Video, Veo 3.1, Kling 3.0, Runway Gen-4.5, Luma). Kills the export/import round-trip. → [TechTimes](https://www.techtimes.com/articles/327054/20260909/adobe-embeds-five-competing-ai-video-models-premiere-killing-round-trip-export.htm)

### AI-native consumer apps

- **Meta Muse** (Sep 8, US only **[1°]**) — personal agent that actually *acts*: books, buys, negotiates, calls; per-user VM + "Sentinel" permission agent + single-use Stripe cards. 2.5M+ downloads in 12 days; free tier ~100M tokens/wk, Power $20/mo. → [CNN hands-on](https://www.cnn.com/2026/09/23/tech/meta-muse-ai-agent)
- **Claude Cowork merged into Claude + Docs/Slides beta** (Sep 16 **[1°]**) — no more choosing chat vs. workspace; tasks continue after you close your laptop; exports to PPTX/DOCX/PDF. Cowork reports **91.3% of sessions are non-coding**. → [claude.com/blog](https://claude.com/blog/cowork-is-now-claude)
- **Snap SPECS Intelligence** (Sep 16 **[1°]**) — anticipatory on-device + secure-cloud AI across iPhone/Mac/AR glasses; US 18+ preview. → [pulse2](https://pulse2.com/snap-launches-specs-intelligence-to-bring-anticipatory-ai-across-iphone-mac-and-ar-glasses)

### Announced / waitlisted / limited

- **Claude Sonnet 5.5 & Haiku 5.5** — named in the Sep 22 post as "coming weeks"; no dates or pricing.
- **Gemini 4** — Koray Kavukcuoglu said Sep 23 it's "close." No specs.
- **OpenAI Presence** — limited GA; requires OpenAI engineers/partner integrators, not self-serve.
- **OpenAI DevDay, Sep 29, 2026** — expected Astra wider release + platform announcements.
- **[?] Meta "Hatch" agent / "Watermelon" flagship** — The Information reporting only; Meta has not confirmed codenames or dates. **[?] Kimi K3.1** — teaser only, no model card or weights.

---

## 2. Academic & Frontier Research

### Training Object Permanence in World Models (WROP) — *top HF Daily Paper, 194 upvotes*
- **Authors:** 30-author team spanning USC, CMU, Michigan, JHU, UCSD, UCLA, Columbia, Toronto, Bristol, Berkeley, Waterloo, Oxford, NYU, Stanford, Harvard (incl. Yilun Du, Lvmin Zhang of ControlNet)
- **Sep 23, 2026 [1°]** · **Core contribution:** A 150-task cognitive-science benchmark (6 categories, 10,000+ Blender-generated samples per task) plus **PWM-WROP**, a 16B open world model trained on AWS Trainium2, and a **1.5M-sample training corpus**.
- **Results:** 3rd of 14 overall, **1st among true-continuation models**, Elo 1679.5 (+224 over Grok Imagine); 2.65× training speedup.
- **Code/weights: released** (CC BY 4.0) → [arXiv:2609.28654](https://arxiv.org/abs/2609.28654) · [project page](https://www.object-permanence.world/) · [GitHub](https://github.com/hokindeng/object-permanence)

### Rufus-Air: An Open LLM Post-Training Recipe — *Amazon AI Research*
- **Sep 24, 2026 [1°]** · **Core contribution:** A fully reproducible **8-stage post-training pipeline** on GLM-4.5-Air-Base (106B-A12B MoE) — SFT → Reasoning RL → Coding RL → IF RL → General Agent → Coding Agent → Search Agent → RLHF. **No proprietary teacher distillation or private human annotation.** Validates a "Reward Reliability Ordering" heuristic.
- **Results:** Beats the official GLM-4.5-Air checkpoint; **+21.8% on multi-turn coding agent tasks**; IFBench 76.9 (vs 33.6 base).
- **Code/recipe: released** → [arXiv:2609.29421](https://arxiv.org/html/2609.29421v1) · [HF paper](https://huggingface.co/papers/2609.29421)

### Agent-Editing World Model (AEWM) — *Renmin University + DeepSeek ecosystem*
- **Sep 23, 2026 [1°]** · **Core contribution:** Reframes world modeling for agents — instead of predicting tool responses, it models **task progress** and *edits noisy reasoning*. Action Judge (Critical/Exploratory/Noisy classification) + State Revision, integrated with real execution as EditAct.
- **Results:** 70.5% macro-F1 on Action Judge (+10.6 over the strongest frontier baseline); EditAct +3.2–6.7 pts across 6 benchmarks / 3 backbones.
- **⚠️ Paper only — no code or weights found.** → [arXiv:2609.28416](https://arxiv.org/abs/2609.28416)

### Your Transformer Can Hold Two Thoughts at Once (Linear Superposition)
- **Tikhonov, Korznikov, Mikhalchuk, et al.** · Sep 24, 2026 [1°] · 63 upvotes
- **Core contribution:** The "Superposition Linearity Hypothesis" — linearly combining two input streams yields a superposition of next-token distributions. Introduces **guided decoding** to produce two coherent continuations from a single forward pass.
- **⚠️ No code link in the abstract; no benchmarks reported.** → [arXiv:2609.29845](https://arxiv.org/abs/2609.29845)

### Also worth a look
- **AV-GRPO** (Shanghai AI Lab, ~Sep 26) — modality-anchored decoupled diffusion RL for **joint audio-video generation**. Code open-sourced. → [HF 2609.29816](https://huggingface.co/papers/2609.29816)
- **HEXIS** (Sep 24) — compiles agent skills into extended finite state machines to cut execution tokens. arXiv:2609.30123
- **Flash-dLLM** (Sep 22) — IO-aware KV caching + parallel decoding for diffusion LLMs. Code available.
- **GeoPair** — training-free cross-layer Transformer compression. arXiv:2609.25963
- **Qwen-Planner-Agent** — closed-loop AI-for-AI mobile planner agents. arXiv:2609.29892

---

## 3. Open Source Releases & Weights

| Model | Org | Size | License | Practical note |
|---|---|---|---|---|
| **MiMo-V2.6-Pro / Flash / Distill-Qwen-9B** | Xiaomi | 1.02T MoE, 42B active, 1M ctx | **MIT** | AA Index 46 — best open model, ties Grok 4.7. Distill-9B runs on one GPU. |
| **DeepSeek V4.1 Flash** | DeepSeek | 552B MoE, 8B/16B active, 1M ctx | **MIT** | Terminal-Bench 2.1 **90.6%**; KV cache 890 B/token (~¼ of V4). ~510GB FP8. |
| **Tencent Hy4-preview** | Tencent | 770B MoE, 49B active | **Apache 2.0** | Gated DSA + IndexCache; SWE-bench Pro 65.7; day-0 vLLM/SGLang images. |
| **GLM-5.3-Flash** | Z.ai | 320B MoE, 18B active, multimodal | **MIT** | AA Index 57 @ ~$0.045/task. Flagship GLM-5.3 uses a **custom non-OSI license** — read before commercial use. |
| **Nemotron 3.5 Lightning 30B-A3B** | NVIDIA | 30B / 3B active, 1M ctx | OpenMDW-1.1 | Interleaved Mamba-2 + MoE; **runs on 1× H100 or DGX Spark**; GGUF available. |
| **Ling-3.0-flash-VL** | InclusionAI (Ant) | 124B MoE / 5.5B active VL | **MIT** | VideoRoPE; GUI-agent capable; free OpenRouter endpoint. |
| **Qwen-Image-2.1** | Alibaba Qwen | 7B unified T2I + edit | Qwen Research (⚠️) | **Native transparent RGBA output**; 7.26GB INT8; day-zero ComfyUI/Diffusers. |
| **LLaDA2.2-mini** | InclusionAI (Ant) | 16B MoE / 1.4B active | **Apache 2.0** | Agentic **diffusion** LM with token insert/delete; quiet drop. |
| **LFM2.5-VL-DSpark** | Liquid AI | 280M draft model | — | **Exact-output** speculative decoding: 2.3–3.1× faster on M5 Max, up to 20.4× decode on H100. |
| **MiniMax H3 (Hailuo 3.0)** | MiniMax | 33B omni-modal | MiniMax Community | Text/image/video/audio → 15s native 2K video **with stereo audio in one pass**. |
| **IFM K2 Horizon (6 models)** | Institute of Foundation Models | 0.9B–375B | Apache 2.0 | Weights + **training data + code + methodology** all published. |

**Frameworks & tooling**
- **google/ax** (Apache 2.0, ~Sep 21) — declarative agentic control plane on Kubernetes built on Agent Substrate; claims billions of concurrent agent tasks per cluster with sub-second suspend/resume. → [explainx.ai](https://www.explainx.ai/blog/google-ax-agentic-orchestrator-kubernetes-2026)
- **Microsoft Agent Framework 1.19.0** — scoped MCP sessions, verified skill archives, new Cosmos/Mongo vector stores. ⚠️ **AutoGen is now in maintenance mode** — plan your migration.
- **Serving stacks:** llama.cpp v0.5.0 (Sep 24, adds MiMo-V2.6 + Gemma4 DSpark drafts), Unsloth 0.1.806-beta (default MTP → 2× faster on Qwen3.8-Flash-Next and GLM-5.3-Flash), SGLang distributed KV cache (HiCache), LiteLLM migrating to Rust.
- **GitHub trending:** `dream-num/univer` ("Office for AI Agents"), `browser-use/video-use`, `HKUDS/nanobot`, `anthropics/financial-services` (first lab-built domain vertical).

**⚠️ Flagged as NOT actually released:** Qwen3.8-Omni-Flash (API-only, no weights) · Meta Muse Spark open weights (roadmap only) · Reflection AI (nothing downloadable despite $2B raise).

---

## 4. Synthesis & Emerging Trends

**1. The open-weights frontier moved to China, and the gap closed at the top.** MiMo-V2.6-Pro (Xiaomi), DeepSeek V4.1 Flash, Tencent Hy4, GLM-5.3, Kimi K3, and Qwen3.8 all shipped in a ~6-week window. MiMo-V2.6-Pro ties *closed* Grok 4.7 on the AA Index. Meanwhile the leading US open models (Thinking Machines Inkling, Nemotron 3 Ultra) date to June/July and update less frequently. For anyone building on open weights, this month materially changed your option set. ([Interconnects](https://www.interconnects.ai/p/the-current-balance-of-power-in-open))

**2. Architectural convergence on "cheap long context."** Active-parameter share is collapsing toward 4–8% (Qwen3.8 2.4T-A95B at 4.0%, DeepSeek V4.1 Flash at 8B/552B). The recurring toolkit: Gated DeltaNet, Gated DSA + IndexCache, Compressed Sparse Attention 2, Mamba-2 interleaving — all in service of ~O(n) context at 256K–1M tokens. **Speculative decoding (DSpark, MTP, DFlash) is now default-on**, not an optimization you add later.

**3. Agentic RL is the post-training centerpiece.** Rufus-Air's 8-stage recipe, Xiaomi's public 6-day RL run with 7,000+ released environments, Qwen-Planner-Agent, and AEWM's rejection-sampling RFT all point the same direction. Named principles are emerging: **reward-reliability ordering** (hard verifiable signals before soft judge signals) and difficulty filtering.

**4. "Tools" now means agent workspaces, not chat windows.** Claude Code Projects, Antigravity's harness, Cursor Agent Skills, Adobe's in-timeline model picker, and Meta Muse all shipped this month. The unifying pattern: **orchestrate parallel/long-running work, and enforce permissions structurally** (Sentinel agents, Credentials APIs, sandbox bypass reduction). Anthropic's own data — 91.3% of Cowork sessions non-coding — suggests the audience is no longer developers.

**5. Skills are becoming the new distribution format.** Anthropic's open `SKILL.md` standard is now supported by Cursor, GitHub Copilot in VS Code, Copilot CLI, and Claude Code, with Unity shipping 29–31 first-party skills. This is the closest thing to an "npm for agents" the ecosystem has produced — and it's worth standardizing on now.

**6. World models are the next multimodal frontier.** WROP (object permanence), DeltaWAM (bimanual manipulation), Agent-Editing World Model, Rolling-WAM — video models are being reframed as world models and benchmarked against cognitive priors rather than visual fidelity. Diffusion LLMs are simultaneously going agentic and production-grade (LLaDA2.2-mini, Flash-dLLM).

---

## Your "Try It This Week" Shortlist

**If you have 30 minutes:**
1. **Claude Opus 5.5** or **GPT-6 Sol** — re-run your hardest eval; both shipped at a ~20–50% price *cut*.
2. **Gemini 3.8 Flash TTS** — design a custom voice from a text description in AI Studio.
3. **Claude Code Projects (beta)** — parallel agent threads with shared memory, if you're in the Pro/Max cohort.

**If you have an afternoon:**
4. **MiMo-V2.6-Distill-Qwen-9B** (MIT) — best single-GPU agent model released this month.
5. **DeepSeek V4.1 Flash** (MIT) — best cost/performance open model; 8-GPU floor.
6. **Nemotron 3.5 Lightning 30B-A3B** — GGUF, runs on one H100 or a DGX Spark.
7. **google/ax** (Apache 2.0) — if you're operating agents on Kubernetes at all.

**If you're doing research:**
8. **Rufus-Air** recipe — reproducible 8-stage post-training on public weights.
9. **WROP / PWM-WROP** — 16B world model + 1.5M-sample corpus, CC BY.

**Watch:** OpenAI DevDay (Sep 29) · Gemini 4 · Claude Sonnet/Haiku 5.5 · promo pricing expiry — **Gemini intro pricing doubles Jan 1, 2027**, GPT-6 Sol promo ends **Nov 21, 2026**.

---

*Caveats: benchmark figures are vendor- or aggregator-reported and not independently reproduced here. Items marked [2°] or [?] should be verified against primary sources before you commit engineering time. Several widely-circulated "September 2026 launch" claims trace only to SEO aggregators recycling older releases.*
