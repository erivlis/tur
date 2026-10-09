# Technical & Comparative Audit: The Fall 2026 Decision Model Landscape

**Document:** EXP-0012 Artifact 01  
**Subject:** Comparative Architecture, Latency Economics, and Dual-Process Systems (Jev, Kev, Laya, OpenAI Decisions)  
**Authors:** Eran Rivlis, Ariel  
**Date:** 2026-10-09

---

## 1. Executive Overview: The Post-Generative Shift

For four years (2022–2026), agentic AI architectures operated almost exclusively under the **Generative Monolith
Assumption**: every decision—whether classifying a commit, routing a tool call, triaging a memory, or solving a
lemma—was delegated to an autoregressive causal language model generating sequential natural-language tokens.

In the autumn of 2026, this assumption fractured irreversibly into two distinct evolutionary paths:

1. **Ultra-Heavy System 2 (Long-Horizon Deliberation & Mechanized Proof):** Exemplified by OpenAI's October 6, 2026
   release of `openai/math` (722 manuscripts across 372 families generated via 3+ hours of inference-time search per
   result, validated through the Lean 4 proof assistant).
2. **Ultra-Fast System 1 (Non-Generative Decision Primitives):** Exemplified by the mid-September 2026 launch of **Jev**
   (TypeSafe AI) and the subsequent open-source releases of **Laya** (Convai Innovations) and **Kev** (Jared Palmer).

Decision models discard natural-language token generation entirely. Instead of predicting the next subword token, they
evaluate a context and question to output strictly typed, bounded, statistically calibrated values: **`Choice`** (1
of $N$), **`Score`** (rubric scale), or **`Noul`** (calibrated boolean probability).

---

## 2. The Decision Model Taxonomy (Fall 2026)

```
                              ┌────────────────────────────────────────────────────────┐
                              │            AGENTIC COGNITIVE SUBSTRATE                 │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
                             ┌────────────────────────────┴───────────────────────────┐
                             │                                                        │
              ┌──────────────▼─────────────┐                           ┌──────────────▼─────────────┐
              │     SYSTEM 1 (REFLEX)      │                           │  SYSTEM 2 (DELIBERATION)   │
              │   Non-Generative Decisions │                           │ Causal Generation & Proof  │
              └──────────────┬─────────────┘                           └──────────────┬─────────────┘
                             │                                                        │
             ┌───────────────┼───────────────┐                                        │
             ▼               ▼               ▼                                        ▼
      ┌────────────┐  ┌────────────┐  ┌────────────┐                           ┌────────────┐
      │    Laya    │  │    Kev     │  │    Jev     │                           │ Frontier   │
      │ (Encoder)  │  │ (LoRA+Head)│  │ (Hosted)   │                           │ LLM + Lean │
      │  Convai    │  │   Palmer   │  │  TypeSafe  │                           │  OpenAI    │
      └────────────┘  └────────────┘  └────────────┘                           └────────────┘
```

### 2.1 Jev (TypeSafe AI)

- **Founders:** Diogo Almeida (co-author of InstructGPT, RLHF, ChatGPT), Erik Gafni, Sasha Sheng.
- **Launch Date:** September 15, 2026.
- **Delivery Mode:** Proprietary Cloud API ($0.042 / 1M input tokens).
- **Core Primitives:**
    - `Choice`: Selection from up to 255 discrete options.
    - `Score`: Cardinal rating on an integer rubric (levels 2–10).
    - `Noul`: Calibrated true/false probability distribution ($P \in [0.0, 1.0]$).
- **Training Methodology:** **RLCD (Reinforcement Learning for Calibrated Decisions)**. Rather than training models
  against human preference rankings (which encourage verbose, sycophantic rhetoric), RLCD optimizes the output logit
  distribution to match true empirical outcome frequencies, ensuring confidence scores represent genuine probabilities.
- **Performance Characteristics:** End-to-end network latency typically 70–500ms; zero token generation delay.

### 2.2 Kev (Jared Palmer)

- **Author & License:** Jared Palmer; Apache 2.0.
- **Architecture:** Frozen autoregressive foundation model (Qwen 3.5 base) paired with a rank-16 Low-Rank Adaptation
  (LoRA) adapter and a custom classification/pointer head on top of the final transformer hidden state.
- **Model Sizes:** Tiered parameter footprints:
    - `kev-0.8b`: Ultra-lightweight CPU/edge execution.
    - `kev-4b`: Standard workstation inference (~3GB VRAM in FP16).
    - `kev-9b`: Balanced multi-label semantic reasoning.
    - `kev-27b`: High-capacity frontier decision logic.
- **Key Advantage:** Wire-compatible drop-in alternative to the Jev SDK. Enables offline, self-hosted, air-gapped
  sovereign execution without third-party network egress.

### 2.3 Laya (Convai Innovations)

- **Author & License:** Convai Innovations; Apache 2.0.
- **Architecture:** Non-autoregressive bidirectional encoder based on **ModernBERT-large** (~421M parameters).
- **Core Mechanism:** Because it is an encoder rather than a causal decoder, Laya processes the entire input sequence in
  a single forward pass ($\mathcal{O} (1)$ pass instead of $\mathcal{O} (T)$ autoregressive steps).
- **Performance Characteristics:** Sub-50ms execution on local hardware; capable of executing inside embedded runtimes
  or edge microservices with minimal footprint.
- **Trade-off:** Shorter context window than Kev/Qwen (typically 8,192 tokens), but significantly higher throughput for
  high-frequency triage.

### 2.4 Cloud & Foundation Provider Counterparts

- **OpenAI Decisions API (`gpt-6-luna`):** Announced late September 2026, offering native structured decision endpoints
  directly inside OpenAI's platform.
- **Cloudflare Clef:** Edge-distributed decision worker infrastructure optimized for sub-20ms routing at CDN points of
  presence.

---

## 3. Comparative Architecture & Economics Matrix

| Dimension              | Standard Autoregressive LLM (e.g. GPT-4o, Claude 3.5 Sonnet) | TypeSafe Jev                                | Kev (Qwen 3.5 + LoRA)                       | Laya (ModernBERT-large)                     |
|:-----------------------|:-------------------------------------------------------------|:--------------------------------------------|:--------------------------------------------|:--------------------------------------------|
| **Primary Output**     | Unbounded Token Stream ($\ge 100$ tokens)                    | Typed Primitive (`Choice`, `Score`, `Noul`) | Typed Primitive (`Choice`, `Score`, `Noul`) | Typed Primitive (`Choice`, `Score`, `Noul`) |
| **Pass Complexity**    | Sequential Autoregressive ($\mathcal{O}(T)$)                 | Single Forward Classification Pass          | Single Forward Head Evaluation              | Single Bidirectional Pass                   |
| **Typical Latency**    | 1,200ms – 4,500ms                                            | 70ms – 300ms                                | 30ms – 150ms (local GPU)                    | **15ms – 45ms** (local GPU/CPU)             |
| **Token Cost (1M)**    | $2.50 – $15.00                                               | $0.042                                      | $0.00 (Self-hosted)                         | $0.00 (Self-hosted)                         |
| **Hallucination Risk** | Moderate to High (Formatting, Syntax)                        | **Zero** (Closed output space)              | **Zero** (Closed output space)              | **Zero** (Closed output space)              |
| **Schema Validation**  | Required (Pydantic / Regex / JSON repairs)                   | **None** (Kernel-typed return)              | **None** (Kernel-typed return)              | **None** (Kernel-typed return)              |
| **Offline Sovereign**  | No (API dependent)                                           | No (API dependent)                          | **Yes** (Apache 2.0 weights)                | **Yes** (Apache 2.0 weights)                |

---

## 4. The Epistemological Boundary: Decision Models vs. Formal Provers

A critical conceptual distinction must be drawn between the two 2026 breakthroughs:

```
[ Generative Prose ]  ──(Calibration)──►  [ Decision Models (Jev/Kev/Laya) ]  ──(Mechanization)──►  [ Formal Kernels (Lean 4) ]
   Subjective / Plausible                       Statistically Calibrated                             Deterministically Verified
   Prone to confabulation                       Zero-hallucination routing                           Unconditional mathematical truth
```

1. **Decision Models provide Statistical Grounding:**
    - They do *not* prove theorems.
    - They do not replace formal verification.
    - What they provide is **well-calibrated reflexivity**: when a model outputs `noul = 0.94`, the probability of
      correctness in empirical trials converges to 94%. This is optimal for triage, routing, and filtering.

2. **Formal Provers (Lean 4) provide Axiomatic Grounding:**
    - They accept no probabilities.
    - A theorem is either sound ($1.0$) or type-rejected ($0.0$).
    - What they lack is speed and open-ended contextual awareness.

In a mature cognitive architecture, **Decision Models act as the afferent nervous system** (rapid reflex, filtering,
routing), while **Formal Verifiers and Causal Synthesizers act as the cortical core** (axiomatic truth, deep reasoning,
and invariant validation).
