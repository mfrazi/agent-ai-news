---
title: "Emerging techniques in test-time compute and reasoning models"
date: 2026-09-26
type: research
tags: [AI, Research]
---

# Research Briefing: Emerging Techniques in Test-Time Compute & Reasoning Models

## Executive Summary

- **Test-time compute (TTC) has become a first-class scaling axis.** The canonical result (Snell et al., arXiv:2408.03314) shows that optimally allocated inference compute can let a smaller model match one ~14× larger at equal FLOPs — reframing capability as a *function of inference budget* rather than a fixed model property.
- **The field has converged on a hybrid recipe:** training-time RL with verifiable rewards (RLVR: GRPO/DAPO/GSPO) + inference-time search (MCTS/beam/Best-of-N) + a learned process/value model. DeepSeek-R1's pure-RL "aha moment" result is the anchor; DAPO/GSPO/Dr.GRPO are the maturing systems layer.
- **Generative reward models are ascendant.** GenPRM, ThinkPRM, R-PRM, and DeepSeek-GRM replace scalar step labels with *reasoned* verification — trading inference compute for large gains in data efficiency and interpretability.
- **Latent/continuous reasoning is the fastest-moving architecture frontier** (Coconut → Huginn → Ouro/LoopLM → SwiReasoning), with open weights now available (Ouro 1.4B/2.6B, Apache-2.0). A recurring finding: latent recurrence *peaks then collapses* with depth, motivating stabilization work.
- **Efficiency is now a first-class objective.** Budget forcing (s1), difficulty-aware length control (AdaptThink, When2Think), overthinking studies, and self-speculative decoding (LoopSpec) all target the token cost of reasoning — a direct counter-current to "more thinking is always better."

---

## 1. Industry & Lab Announcements

**OpenAI (o-series → GPT-5.x)**
- **o1** (Sep 2024) — first widely deployed reasoning model; AIME 2024 ~74% pass@1 vs GPT-4o ~12%. [Source](https://openai.com/index/learning-to-reason-with-llms/)
- **o3** (announced Dec 2024) — test-time search; 87.5% ARC-AGI-1 at reportedly ~$1,000+/task at max effort. [Source](https://lifearchitect.ai/gpt-6)
- **o3 / o4-mini** (Apr 2025) — reasoning interleaved with tools (Python, web, vision) inside the CoT; o3 69.1% SWE-bench Verified. [Source](https://valueaddvc.com/blog/openai-o3-and-o4-mini-what-the-new-reasoning-models-mean-for-ai-applications)
- **GPT-5** (Aug 2025) — router across Instant/Thinking/Pro tiers; "Thinking" matches o3 quality with 50–80% fewer tokens. [Source](https://runbear.io/posts/gpt-5-explained)
- **GPT-5.2** (Dec 2025) — adds `xhigh` reasoning effort; AIME 2025 100%, GPQA Diamond 92.4%, SWE-bench Verified 80.0%. [Source](https://www.digitalapplied.com/blog/gpt-5-2-complete-guide)

**Google DeepMind**
- **Gemini 2.0 Flash Thinking** (Dec 2024) — explicitly "a test-time compute model" exposing its thoughts. [Source](https://ai.google.dev/gemini-api/docs/changelog)
- **Gemini 2.5 Pro** (Mar 2025) — first designated "thinking model"; all future models to have reasoning. [Source](https://en.wikipedia.org/wiki/Gemini_(language_model))
- **Gemini 3 Deep Think** (Dec 2025) — "System 2" deliberate mode; ARC-AGI-2 45.1% with code execution. [Source](https://felloai.com/ultimate-gemini-model-comparison)

**Anthropic**
- **Claude 3.7 Sonnet** (Feb 2025) — first hybrid-reasoning model with visible extended thinking; >70% SWE-bench. [Source](https://techiefied.com/claude-version-history)
- **Claude Opus 4 / Sonnet 4** (May 2025) — extended thinking with `budget_tokens` control. [Source](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html)

**DeepSeek**
- **DeepSeek-R1 / R1-Zero** (Jan 2025) — pure RL (GRPO) induces reasoning without human-labeled CoT; open weights; AIME 2024 79.8%. [arXiv:2501.12948](https://arxiv.org/abs/2501.12948)
- **R1 published in *Nature*** (Sep 2025) — first major LLM to pass peer review; disclosed $294K RL training cost. [Source](https://eu.36kr.com/de/p/3631908557374473)

**Others**
- **Qwen3** (Apr 2025) — hybrid reasoning toggled per request; Qwen3-Max Thinking adds "experience cumulative test-time scaling." [Source](https://www.facebook.com/alibabagroupofficial/posts/1370788801933916)
- **Mistral Magistral** (Jun 2025) — first Mistral reasoning model; transparent CoT; Small 24B under Apache 2.0. [Source](https://venturebeat.com/ai/mistrals-first-reasoning-model-magistral-launches-with-large-and-small-apache-2-0-version)
- **Moonshot Kimi K2 Thinking** (Nov 2025) — 1T-param MoE (32B active), interleaves CoT with 200–300 tool calls; HLE 44.9%, SWE-bench Verified 71.3%. [HF model card](https://huggingface.co/moonshotai/Kimi-K2-Thinking)
- **xAI Grok 4 Heavy** — parallel test-time compute with a leader–synthesiser topology. [Source](https://www.webpronews.com/xais-grok-4-heavy-and-the-new-math-of-ai-reasoning)

**Notable benchmark claims:** AIME 2025 is saturating (GPT-5.2 100%); SWE-bench Verified is being retired by OpenAI (Feb 2026) over contamination, with SWE-bench Pro emerging as successor; ARC-AGI-2 frontier scores rose from ~0–4% (Mar 2025) to 75–85% (2026), while the new interactive **ARC-AGI-3** reset frontier scores to near-zero again.

---

## 2. Academic & Frontier Research

### 2.1 Test-Time Compute Scaling Laws
- **Scaling LLM Test-Time Compute Optimally Can Be More Effective than Scaling Model Parameters** — Snell, Lee, Xu, Kumar (UC Berkeley/DeepMind). arXiv:2408.03314 (ICLR 2025 oral). *The canonical result:* optimal allocation is difficulty-dependent — easy problems favor parallel sampling (Best-of-N), hard problems favor sequential revision/search guided by a PRM.
- **Large Language Monkeys: Scaling Inference Compute with Repeated Sampling** — Brown et al. (Stanford). arXiv:2407.21787. Coverage scales smoothly/log-linearly with sample count — a verifier-agnostic inference lever.
- **The Art of Scaling Test-Time Compute for LLMs** — arXiv:2512.02008. Large controlled study (>30B tokens, 8 models 7B–235B): no single strategy universally dominates.
- **A Survey on Test-Time Scaling in LLMs** — Zhang et al. arXiv:2503.24235. Standard "what/how/where/how well" taxonomy.
- **Beyond Chinchilla-Optimal** — Sardana, Portes, Doubov. arXiv:2401.00448. Inference-heavy deployment favors *smaller* models than Chinchilla-optimal — motivating TTC as a parameter substitute.

### 2.2 Reasoning Techniques (CoT, Search, Self-Refinement)
- **Tree of Thoughts** — Yao et al. arXiv:2305.10601. Foundational search-over-thoughts framework.
- **When LLM Meets Tree Search: A Systematic View of Inference as Search** — Lin et al. arXiv:2608.30395. Survey tracing uninformed search → MCTS → value-guided variants.
- **Socratic Self-Refine (SSR)** — arXiv:2511.10621. Decomposes responses into verifiable "Socratic steps" for step-level confidence and targeted refinement. Code released.
- **ReST-RL** — arXiv:2508.19576. Couples ReST-GRPO trajectory generation with VM-MCTS value-model training.
- **SGA-MCTS** — SSRN 7397293. Separates generation from verification under an explicit call budget.

### 2.3 Process Reward Models & Verifiers
- **Let's Verify Step by Step** — Lightman et al. (OpenAI). arXiv:2305.20050. Foundational PRM paper + PRM800K dataset.
- **GenPRM** — Zhao et al. arXiv:2504.00891. Generative PRM writes a CoT justification before scoring each step.
- **ThinkPRM** — Khalifa, Agarwal, Logeswaran et al. arXiv:2504.16828. Verbalized generative verifier matching discriminative PRMs with orders-of-magnitude fewer labels.
- **R-PRM** — She et al. arXiv:2503.21295 (EMNLP 2025). Reasoning-driven PRM; code released.
- **PathFinder-PRM** — Tej Deep et al. arXiv:2502.19041. Decouples error *detection* from reward estimation.
- **Generative Verifiers (GenRM)** — Zhang et al. arXiv:2408.15240. Reframes reward modeling as next-token prediction.

### 2.4 RL for Reasoning (RLVR)
- **DeepSeek-R1** — DeepSeek-AI. arXiv:2501.12948 (*Nature* 645, 2025). Landmark RLVR result; R1-Zero 15.6% → 71% AIME 2024.
- **DAPO** — Yu et al. (ByteDance). arXiv:2503.14476. Standard open long-CoT RL recipe (dynamic sampling, decoupled clipping, token-level loss).
- **GSPO** — Zheng et al. (Qwen). arXiv:2507.18071. Sequence-level importance ratio; lower gradient variance, adopted in Qwen3.
- **Dr. GRPO** — Liu et al. arXiv:2503.20783. Diagnoses and removes GRPO's length/std normalization biases.
- **Absolute Zero (AZR)** — Zhao et al. arXiv:2505.03335. Self-play RLVR with zero external data.
- **Beyond the 80/20 Rule** — Wang et al. arXiv:2506.01939. High-entropy "forking tokens" steer reasoning; code released.

### 2.5 Latent / Continuous Reasoning
- **Coconut** — Hao et al. (Meta). arXiv:2412.06769. Continuous-thought latent reasoning with BFS.
- **Huginn (Recurrent Depth)** — Geiping et al. arXiv:2502.05171. Iterates a recurrent block to arbitrary test-time depth; code released.
- **Ouro / LoopLM** — Zhu et al. (incl. Bengio). arXiv:2510.25741. Builds reasoning into pre-training; **open weights** (1.4B/2.6B, Apache-2.0).
- **CODI** — Shen et al. arXiv:2502.21074 (EMNLP 2025). Self-distills CoT into continuous latent tokens.
- **Soft Thinking** — Zhang et al. arXiv:2505.15778. Decodes probability-weighted mixtures of embeddings as "soft" concept tokens.
- **Stabilizing Recurrent Dynamics for Test-Time Scalable Latent Reasoning** — arXiv:2605.26733. Diagnoses the peak-then-collapse behavior of looped LMs.

### 2.6 Efficient Reasoning
- **s1: Simple Test-Time Scaling** — Muennighoff et al. arXiv:2501.19393. Introduces **budget forcing**; s1-32B beats o1-preview by up to 27% on MATH/AIME24. Open data/model/code.
- **Do NOT Think That Much for 2+3=?** — Chen et al. ICML 2025. Quantifies overthinking on trivial problems.
- **Reasoning on a Budget** — Alomrani et al. arXiv:2507.02076. Taxonomy: L1-controllability vs L2-adaptiveness.
- **AdaptThink** — Zhang et al. EMNLP 2025. RL policy deciding *whether* to emit a thinking block.
- **Towards Thinking-Optimal Scaling** — Yang et al. NeurIPS 2025. Identifies an optimal reasoning length per problem.
- **LoopSpec** — arXiv:2609.17184. Self-speculative decoding for looped transformers; up to 2.95× speedup on long-CoT benchmarks.

### 2.7 Test-Time Training & Adaptive Compute
- **Efficient Test-Time Adaptation through Human-AI Interaction** — arXiv:2609.04141. Argues weight updates at test time are feasible for agentic systems.
- **Adaptive Test-Time Compute Allocation for Reasoning** — arXiv:2604.14853. ~12.8% relative accuracy gains via difficulty-based allocation.
- **From Search Scaling to Learning Scaling** (Ying Wen). Distinguishes task-local adaptation from persistent runtime learning.

---

## 3. Open Source Releases & Weights

| Release | What's open | Link |
|---|---|---|
| **DeepSeek-R1 / R1-Zero** | Weights (MIT) | [arXiv:2501.12948](https://arxiv.org/abs/2501.12948) |
| **s1** | Data (s1K), model, code | [github.com/simplescaling/s1](https://github.com/simplescaling/s1) |
| **Ouro / LoopLM** | Weights 1.4B/2.6B (Apache-2.0) | [arXiv:2510.25741](https://arxiv.org/abs/2510.25741) |
| **Huginn recurrent-pretraining** | Code | [seal-rg/recurrent-pretraining](https://github.com/seal-rg/recurrent-pretraining) |
| **DAPO** | Full RL system | [arXiv:2503.14476](https://arxiv.org/abs/2503.14476) |
| **Absolute Zero (AZR)** | Code | [arXiv:2505.03335](https://arxiv.org/abs/2505.03335) |
| **R-PRM** | Code | [arXiv:2503.21295](https://arxiv.org/abs/2503.21295) |
| **Beyond the 80/20 Rule** | Code | [arXiv:2506.01939](https://arxiv.org/abs/2506.01939) |
| **Mistral Magistral Small 24B** | Weights (Apache 2.0) | [mistral.ai](https://mistral.ai/news/mistral-small-4) |
| **Kimi K2 Thinking** | Weights (INT4 QAT) | [HF model card](https://huggingface.co/moonshotai/Kimi-K2-Thinking) |
| **IBM Granite-3.3-8B-Math-PRM-v2** | Weights (Apache 2.0) | IBM Granite |

---

## 4. Synthesis & Emerging Trends

**1. Capability is now a curve, not a number.** Noam Brown's 2026 essay argues single-number benchmarks are broken because performance is a function of inference budget; he recommends performance-vs-compute plots and writing test-time compute into preparedness frameworks. This is the single most important conceptual shift — evaluation, safety, and product design all now hinge on *how much compute you're willing to spend per query*.

**2. Search and RL are merging into one system.** The strongest 2025–2026 systems (ReST-RL, SGA-MCTS, ToolPRM) couple training-time RL with inference-time search and a learned value/process model. RLVR is maturing from a trick into a systems discipline (DAPO/GSPO/Dr.GRPO fix GRPO's biases; MLPerf added an RLVR post-training benchmark).

**3. Verification is becoming generative.** GenPRM, ThinkPRM, R-PRM, and DeepSeek-GRM all move from scalar step labels to *reasoned* verification — trading inference compute for data efficiency and interpretability. This is the natural bridge between PRMs and the reasoning models they supervise.

**4. Latent reasoning is the architecture frontier — and it's fragile.** Coconut → Huginn → Ouro/LoopLM → SwiReasoning show a clear trajectory toward reasoning in continuous space, with open weights now available. But a recurring finding is that latent recurrence *peaks then collapses* with depth, so stabilization (arXiv:2605.26733) is an active open problem.

**5. The "more thinking is always better" assumption is being dismantled.** Inverse scaling in TTC, overthinking studies, and the "Mirage of Test-Time Scaling" line of work show longer reasoning can *hurt* on simple counting, constraint-tracking, and spurious-feature tasks. The response is a wave of adaptive/controllable methods: budget forcing (s1), difficulty-aware length control (AdaptThink, When2Think), and provider-level effort knobs (`reasoning.effort`, `thinking_budget`, `thinking_level`).

**6. Economics are inverting.** Inference compute demand is projected to dwarf training compute, and inference already dominates enterprise AI budgets. Jensen Huang frames three intact scaling laws (pre-training, post-training/RL, inference/"thinking"). The practical consequence: cost-per-correct-answer, not raw accuracy, is becoming the headline metric — e.g., evolutionary TTC solutions reaching ~80% ARC accuracy at $8.42/task.

**7. Open questions / caution.** ARC-AGI-3's reset to near-zero frontier scores suggests benchmark-specific optimization rather than transferable reasoning. CoT faithfulness remains unresolved — hidden reasoning traces make models harder to interpret ("Chain-of-Thought Is Not Explainability"). And a mid-2026 industry check concluded that TTC/RLVR are "extensions of known approaches rather than a new scaling law," with continual learning as the leading candidate for the next paradigm.

---

### Sourcing Caveats
- Several 2026-dated figures come from aggregators (BenchLM, Artificial Analysis) and vendor pages; cross-model comparisons are approximate because scaffolding, prompts, and TTC settings differ. Treat headline numbers as directional.
- **AIME 2024 contamination:** MathArena suggests scores may be inflated 10–20 points for models trained after 2024; AIME 2025 is more reliable.
- **SWE-bench Verified contamination** acknowledged by OpenAI (Feb 2026); SWE-bench Pro is the emerging successor.
- Some 2026 arXiv IDs (26xx range) surfaced via search snippets — verify final author lists and venue status on arXiv before citing. A few contributions (VRPRM, VersaPRM, DeepSeek-GRM) were identified via secondary sources rather than primary pages.
