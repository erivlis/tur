# EXP-0012: Jev & System One Non-LLM Integration — Calibrated Decision Models in Persistent Memory Engines

| Field           | Value                                                                                                                                                                                                                                                                                                                                                                                               |
|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0012                                                                                                                                                                                                                                                                                                                                                                                                |
| **Title**       | Jev & System One Non-LLM Integration — Calibrated Decision Models in Persistent Memory Engines                                                                                                                                                                                                                                                                                                      |
| **Author**      | Ariel, Jules                                                                                                                                                                                                                                                                                                                                                                                        |
| **Status**      | Active / Architectural Investigation                                                                                                                                                                                                                                                                                                                                                                |
| **Type**        | Non-LLM Model Integration & System One Runtime Architecture                                                                                                                                                                                                                                                                                                                                          |
| **Created**     | 2026-09-22                                                                                                                                                                                                                                                                                                                                                                                          |
| **Updated**     | 2026-09-22                                                                                                                                                                                                                                                                                                                                                                                          |
| **Related EPs** | [EP-0003](../../docs/proposals/EP-0003-policy-vs-mechanism.md), [EP-0113](../../docs/proposals/EP-0113-core-memory-protocol.md), [EP-0117](../../docs/proposals/EP-0117-substrate-benchmark.md), [EP-0134](../../docs/proposals/EP-0134-active-tms-contradiction-interruption.md), [EP-0138](../../docs/proposals/EP-0138-dynamic-epistemic-elevation-and-principle-crystallization.md), [EP-0144](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md), [EP-0152](../../docs/proposals/EP-0152-sovereign-note-based-dreaming-and-session-lifecycle.md) |

---

## 1. Abstract & Context

### The Emergence of System One Non-LLM Models
In September 2026, TypeSafe AI (founded by Diogo Almeida, former OpenAI lead on RLHF, InstructGPT, and GPT-4) introduced **Jev**—the pioneer of a new model class termed **"System One models"**. Unlike Large Language Models (LLMs), Jev does not generate free-form natural language text. Instead, it accepts a block of state (a string, JSON payload, or array of text) alongside typed questions, evaluating them in a single parallel forward pass and returning strict, typed values accompanied by calibrated probabilities and confidence estimates.

Jev defines three fundamental question primitives:
1. **`Choice`**: Selects one option from a pre-defined set, returning the chosen option, per-option probability distributions, and an overall confidence score.
2. **`Score`**: Rates the state against ordered levels, returning a discrete level score, per-level probabilities, and confidence score.
3. **`Noul`**: Evaluates a yes/no hypothesis or statement, returning a calibrated probability float in the interval $[0.0, 1.0]$.

Operating with response latencies between **70ms and 500ms** and trained via **Reinforcement Learning for Calibrated Decisions (RLCD)** on synthetic data, Jev eliminates type errors and hallucinations outside the caller-defined schema.

### The Problem Statement for Tur
**Tur** is an open-source persistent state, memory, and persona engine for AI agents. It acts as the "soul" and "memory" (L1 Open Knowledge Format Markdown ledger, L2 NetworkX/AlgebraX cognitive graph, L3 SQLite session continuity), while external inference engines provide reasoning ("mind").

Historically, AI agent architectures relied on generative LLMs for both:
- **Generative Tasks** (writing code, generating conversational responses, creative synthesis).
- **Discriminative & Epistemic Control Tasks** (verifying truth, detecting memory contradictions, categorizing knowledge, evaluating constraint dimensionality $C_p$).

Using generative LLMs for discriminative control introduces significant architectural vulnerabilities: high latency (1–5 seconds per step), monetary cost, uncalibrated confidence ("overconfidence"), and potential token generation hallucinations.

This exploration analyzes how **Tur** can integrate **System One non-LLM models** like Jev as high-speed, zero-hallucination epistemic gatekeepers and classification drivers, and evaluates the broader paradigm shift toward hybrid agent architectures.

---

## 2. Exploration & Options Analysis

We analyze four key integration vectors where System One non-LLM models intersect with Tur's persistent state engine:

```
                                  ┌──────────────────────────────────────────────┐
                                  │                TUR AGENT ENGINE              │
                                  │   (State, Ledger, Memory DAG, Persona)       │
                                  └──────┬───────────────────────────────┬───────┘
                                         │                               │
                      Discriminative     │                               │     Generative
                      Sub-Second Calls   │                               │     Conversational
                     (70ms - 200ms)      │                               │     Calls (2s - 10s)
                                         ▼                               ▼
                      ┌──────────────────────────────────┐   ┌──────────────────────────┐
                      │    SYSTEM ONE MODEL (Jev)        │   │    SYSTEM TWO LLM        │
                      │  - TMS Contradiction (Noul)      │   │  - Free-form Code Gen    │
                      │  - Epistemic Elevation (Score)   │   │  - Conversational Prose  │
                      │  - Taxonomy Assignment (Choice)  │   │  - Deep Deliberation     │
                      │  - Cp Friction Scoring (Score)   │   │                          │
                      └──────────────────────────────────┘   └──────────────────────────┘
```

---

### Option A: Sub-Second Epistemic TMS Gatekeeper (`Noul` & `Choice`)

#### Existing Bottleneck in Tur
In `src/tur/memory/tms.py`, Tur's `ContradictionInterceptor` screens incoming memory candidate assertions against active L1/L2 memories to protect core axioms and prevent contradictory state commits. The current implementation relies on symbolic heuristics (Jaccard token overlap, antonym pairs, negation marker detection). While instant, symbolic rules produce false positives on contrastive definitions and false negatives on subtle semantic contradictions.

#### Jev Integration Design
Instead of invoking a slow, expensive System Two generative LLM or relying solely on symbolic heuristics, `ContradictionInterceptor` sends the active state block (existing memory vs. candidate memory) to Jev with parallel typed questions:

```json
{
  "state": {
    "existing_memory": "Transport uses SSE with JSON-RPC messaging.",
    "candidate_memory": "Transport uses stdio-only for inter-process communication."
  },
  "questions": [
    {
      "type": "Noul",
      "id": "is_contradiction",
      "statement": "The candidate_memory directly contradicts or invalidates the existing_memory."
    },
    {
      "type": "Choice",
      "id": "conflict_type",
      "options": ["direct_contradiction", "dialectic_refinement", "unrelated_context", "complementary_fact"]
    }
  ]
}
```

#### Return Payload (~100ms response time):
```json
{
  "answers": {
    "is_contradiction": {
      "probability": 0.96,
      "confidence": 0.98
    },
    "conflict_type": {
      "selected": "direct_contradiction",
      "probabilities": {
        "direct_contradiction": 0.94,
        "dialectic_refinement": 0.04,
        "unrelated_context": 0.01,
        "complementary_fact": 0.01
      },
      "confidence": 0.95
    }
  }
}
```

#### Performance & Safety Gains:
- **Sub-100ms Ingestion Latency:** `tur learn` can perform rigorous model-based truth maintenance without noticeably slowing down CLI execution.
- **Zero Schema Leakage:** Jev cannot output text outside `direct_contradiction`, `dialectic_refinement`, etc., eliminating JSON parsing errors.
- **Deterministic Thresholding:** Gates can enforce strict probabilistic policies: e.g., trigger `TMSConflictError` if $P(\text{is\_contradiction}) \ge 0.85 \land \text{confidence} \ge 0.80$.

---

### Option B: Calibrated Epistemic Elevation & Memory Crystallization (`Score` & `Choice`)

#### Existing Bottleneck in Tur
Session dreaming (`src/tur/memory/dreaming.py`) and introspection (`src/tur/memory/introspection.py`) consolidate transient L3 session logs into permanent L1 memories (`axiom`, `fact`, `insight`, `preference`). Currently, this step relies on generative LLM prompts requesting structured JSON (`Dream` schema).

Generative LLMs frequently suffer from:
1. **Uncalibrated Extravagance:** Extracting trivial procedural steps as "universal insights".
2. **Sycophancy:** Rating user-suggested temporary hacks as permanent axioms.

#### Jev Integration Design
Memory crystallization is restructured into a two-stage pipeline:
1. **Candidate Extraction (Fast Parser / Light LLM):** Extracts raw declarative sentences from L3 session notes.
2. **System One Epistemic Elevation Gate (Jev `Score` + `Choice`):** Evaluates candidate sentence permanence and taxonomy:

```json
{
  "state": "User directed that all CLI outputs must support `--json` envelopes for headless execution.",
  "questions": [
    {
      "type": "Score",
      "id": "durability_rating",
      "levels": ["ephemeral_debug", "session_specific", "project_invariant", "universal_axiom"]
    },
    {
      "type": "Choice",
      "id": "taxonomy_class",
      "options": ["axiom", "fact", "insight", "preference"]
    }
  ]
}
```

#### Resulting Invariant Protection:
- Candidate memories are promoted to L1 **only** when `durability_rating` evaluates to `project_invariant` or `universal_axiom` with confidence $\ge 0.90$.
- Eliminates "epistemic bloat" and maintains high information density in the L1 ledger.

---

### Option C: Dynamic $C_p$ Constraint Dimensionality & Principle Friction Scoring (`Score`)

#### Existing Formula in Tur
In `src/tur/metrics.py`, Constraint Dimensionality ($C_p$) measures the cognitive complexity and friction of a persona's directive set:
$$C_p = \sum W_c + N_c (N_c - 1) \cdot 0.05$$

The current interaction penalty $N_c(N_c - 1) \cdot 0.05$ uses a static quadratic friction coefficient across all principles. However, two complementary principles (e.g., "Use PEP 8" and "Enforce Type Hints") have zero mutual friction, whereas two conflicting principles (e.g., "Maintain Zero Dependencies" and "Integrate Heavy ML Frameworks") exhibit severe friction.

#### Jev Integration Design
Using Jev `Score` or `Noul`, Tur can dynamically compute the **Empirical Friction Matrix** $I_{\text{conflict}}$ across persona principles:

```json
{
  "state": {
    "principle_A": "Maintain zero external runtime dependencies in core package.",
    "principle_B": "Integrate local ONNX transformer model execution."
  },
  "questions": [
    {
      "type": "Score",
      "id": "friction_score",
      "levels": ["harmonic", "mild_tension", "strong_conflict", "mutually_exclusive"]
    }
  ]
}
```

This transforms $C_p$ into a grounded, empirical metric:
$$C_p = \sum_{c} W_c + \sum_{i < j} \text{FrictionScore}(P_i, P_j)$$

Providing exact cognitive load telemetries before deploying complex agent personas.

---

### Option D: The Dual-Brain Agent Architecture (System One + System Two with Tur State)

The integration of Jev highlights a broader paradigm shift in autonomous agent system design:

| Dimension | System One Models (e.g., Jev) | System Two LLMs (e.g., Claude, Gemini, GPT-4) |
|:---|:---|:---|
| **Output Type** | Typed Primitives (`Choice`, `Score`, `Noul`) | Unstructured Free-Form Natural Language / Code |
| **Primary Role** | Fast Deterministic Control, TMS, Routing, Verification | Deliberation, Creative Synthesis, Conversational Prose |
| **Latency** | 70ms – 500ms | 1,000ms – 10,000ms |
| **Cost** | Extremely Low (40x–400x cheaper) | Standard Frontier Model Pricing |
| **Hallucination Risk** | Zero (schema-bounded) | Moderate to High (requires guardrails) |
| **State Dependency** | Requires external state block | Manages internal context window |

In this dual-brain architecture, **Tur acts as the persistent substrate ("Soul")**, mediating state between System One fast reflexes and System Two deep deliberation:

```
                            ┌────────────────────────┐
                            │      USER / SYSTEM     │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │    TUR PERSISTENT      │
                            │    STATE & MEMORY      │
                            └───────────┬────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 │ Sub-second state                            │ Complex task
                 │ verification                                │ requiring prose/code
                 ▼                                             ▼
  ┌─────────────────────────────┐               ┌─────────────────────────────┐
  │  SYSTEM ONE ENGINE (Jev)    │               │    SYSTEM TWO LLM ENGINE    │
  │  - TMS Contradiction Check  │               │  - Code Generation          │
  │  - Memory Classification    │               │  - Architectural Design     │
  │  - Action Policy Selection  │               │  - Human Communication      │
  └─────────────────────────────┘               └─────────────────────────────┘
```

---

## 3. Architectural Synthesis & Constraint Alignment

Evaluating System One integration against Tur's core invariants:

### 1. Policy vs. Mechanism Invariant (EP-0003)
- **Mechanism:** Jev API clients, Pydantic question schemas, and `Choice`/`Score`/`Noul` wrapper classes in `src/tur/` are pure, deterministic computer science mechanisms. They do not encode persona directives or anthropomorphic assumptions.
- **Policy:** The specific questions asked (e.g., whether a memory violates a persona's core principles) remain defined in the Persona Policy layer.
- **Verdict:** Fully aligned.

### 2. Symmetrical Isolation Invariant (The Boundary Constraint)
- System One models operate exclusively on supplied state payloads (strings/JSON). They do not access `.tur/` state or filesystem paths directly.
- All state reads and writes remain brokered by Tur CLI / MCP server tools.
- **Verdict:** Fully aligned.

### 3. Kantian Russell Principle & Golem Protection
- The **Russell Principle** states that the system must follow a rigid internal logic (schema) rather than generating ad-hoc pleasing answers. Jev's RLCD training and schema-bounded outputs enforce the Russell Principle natively at the model level.
- Core and Axiom memories remain protected by hardcoded mechanism checks (`type in (MemoryType.CORE, MemoryType.AXIOM)`), ensuring System One models can suggest supersessions but never bypass human-governed invariant protection.
- **Verdict:** Fully aligned.

### 4. Zero-Dependency & Local ONNX Execution Invariants
- Tur's core package prioritizes lightweight CLI startup times and zero heavy ML framework dependencies (e.g., no local PyTorch/transformers requirements).
- Accessing Jev via REST/gRPC or lightweight HTTP requests requires only standard Python libraries (`httpx` or `urllib`), maintaining fast execution without inflating package size.
- **Local Open-Weights Execution (`kev-0.6b-ONNX`):** System One models are not limited to closed cloud APIs. Open-weights decision models—such as `jaredpalmer/kev-0.6b` (a Qwen3-0.6B backbone with a LoRA adapter and pointer head) converted to ONNX as `onnx-community/kev-0.6b-ONNX`—can run locally in Tur using the lightweight ONNX Runtime engine already integrated in `src/tur/memory/embeddings.py` (EP-0144).
- In `kev-0.6b-ONNX`, state blocks and delimiter tokens (`<|fim_prefix|>`, `<|fim_middle|>`, `<|box_start|>`, `<|box_end|>`, `<|fim_suffix|>`) are processed in a single forward pass with a block-causal mask and pointer readout head. Tur's `VectorEngine` can execute this ONNX graph natively for offline, zero-network, sub-200ms local decision evaluations.

---

## 4. The Verdict / Actionable Design Roadmap

This exploration confirms that System One non-LLM models represent a highly synergistic paradigm for Tur's persistent state management engine. By delegating discriminative verification tasks to calibrated, schema-bounded System One models—either via cloud endpoints (Jev) or local open-weights ONNX models (`kev-0.6b-ONNX`)—Tur achieves sub-second truth maintenance and hallucination-free memory crystallization.

### Actionable Roadmap & Proposed Enhancement Proposals:

1. **Proposed EP-0154: System One Typed Evaluator Driver Protocol**
   - Author a formal proposal (**`EP-0154`**) defining a generic `SystemOneEvaluator` abstract interface in `src/tur/evaluators/` supporting `Choice`, `Score`, and `Noul` primitives.
   - Implement driver adapters for both cloud API endpoints (TypeSafe Jev) and local ONNX models (`onnx-community/kev-0.6b-ONNX` via `tur.memory.embeddings.VectorEngine`).

2. **Phase 1: Sub-Second TMS Integration in `ContradictionInterceptor`**
   - Update `src/tur/memory/tms.py` to support an optional `SystemOneEvaluator` backend alongside the default symbolic keyword matcher.
   - Benchmark latency and accuracy gains on technical contradiction detection.

3. **Phase 2: Calibrated Epistemic Elevation in Session Dreaming**
   - Update `src/tur/memory/dreaming.py` to run extracted candidate memories through a Jev `Score` filter before committing to L1 storage.

4. **Phase 3: Dynamic $C_p$ Principle Friction Matrix**
   - Update `src/tur/metrics.py` to calculate empirical interaction penalties across persona principles using parallel System One `Score` queries.

---

## 5. Related Proposals & External Literature

### 1. External Literature & References
- **TypeSafe AI / Jev Launch (2026):** Almeida, Diogo. *"Introducing System One Models & Jev."* TypeSafe AI Blog, Sept 15, 2026.
- **Open-Weights Kev / ONNX Conversion (2026):** Palmer, Jared; ONNX Community. *"kev-0.6b-ONNX / jaredpalmer/kev-0.6b."* Hugging Face Hub, `onnx-community/kev-0.6b-ONNX`. Qwen3-0.6B backbone with LoRA adapter and pointer readout head serving TypeSafe System One contract locally.
- **RLCD Training Paradigm:** Reinforcement Learning for Calibrated Decisions — Optimizing probabilities against empirical outcomes rather than human rater preference.
- **Kahneman, Daniel:** *"Thinking, Fast and Slow"* (System 1 fast intuitive decision-making vs. System 2 slow deliberative reasoning).

### 2. Related Enhancement Proposals
- **[EP-0003: Policy vs. Mechanism](../../docs/proposals/EP-0003-policy-vs-mechanism.md)** — Core boundary separation.
- **[EP-0113: Core Memory Protocol](../../docs/proposals/EP-0113-core-memory-protocol.md)** — Golem Protection Invariant.
- **[EP-0117: Substrate Benchmark](../../docs/proposals/EP-0117-substrate-benchmark.md)** — Cognitive load and latency benchmarks.
- **[EP-0134: Active TMS Contradiction Interruption](../../docs/proposals/EP-0134-active-tms-contradiction-interruption.md)** — Truth Maintenance System specification.
- **[EP-0138: Dynamic Epistemic Elevation & Principle Crystallization](../../docs/proposals/EP-0138-dynamic-epistemic-elevation-and-principle-crystallization.md)** — Memory promotion protocol.
- **[EP-0144: Zero-Dependency Dense Semantic Embeddings](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md)** — ONNX model execution substrate.
- **[EP-0152: Sovereign Note-Based Dreaming & Session Lifecycle](../../docs/proposals/EP-0152-sovereign-note-based-dreaming-and-session-lifecycle.md)** — Session epilogue consolidation.
