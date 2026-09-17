# EXP-0010: Epistemic Boundary Defense — Active Truth Maintenance, Golem Invariant Protection, and Hybrid Contradiction Dynamics

| Field           | Value                                                                                                                                                                                                                                                                                                                                                                                               |
|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0010                                                                                                                                                                                                                                                                                                                                                                                                |
| **Title**       | Epistemic Boundary Defense — Active Truth Maintenance, Golem Invariant Protection, and Hybrid Contradiction Dynamics                                                                                                                                                                                                                                                                                |
| **Author**      | Eran Rivlis, Ariel                                                                                                                                                                                                                                                                                                                                                                                  |
| **Status**      | Active / Architectural Investigation                                                                                                                                                                                                                                                                                                                                                                |
| **Type**        | Conceptual Physics & Interface Engineering                                                                                                                                                                                                                                                                                                                                                          |
| **Created**     | 2026-09-17                                                                                                                                                                                                                                                                                                                                                                                          |
| **Updated**     | 2026-09-17                                                                                                                                                                                                                                                                                                                                                                                          |
| **Related EPs** | [EP-0003](../../docs/proposals/EP-0003-policy-vs-mechanism.md), [EP-0005](../../docs/proposals/EP-0005-canonical-ontological-lexicon-and-rosetta-stone.md), [EP-0113](../../docs/proposals/EP-0113-core-memory-protocol.md), [EP-0134](../../docs/proposals/EP-0134-active-tms-contradiction-interruption.md), [EP-0144](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md) |

---

## 1. Abstract & Context

This exploration investigates the conceptual physics, structural seams, and technical interfaces governing **Epistemic
Boundary Defense** in Tur. In autonomous agent architectures, long-term memory systems face a fundamental tension
between **plasticity** (the ability to learn new facts, refine models, and adapt to changing codebases) and
**rigidity** (the need to protect core identity, ethical covenants, and verified invariants from cognitive drift,
prompt injection, and self-rationalizing hallucination).

During empirical operations, Tur's Truth Maintenance System (TMS, EP-0134) demonstrated its capability as an active
epistemic immune system: it successfully intercepted an autonomous manifestation from overwriting human-governed Core
Axioms and halted ingestion upon detecting polarity divergence. However, this production milestone also exposed critical
architectural questions:
1. **The Epistemic Seam Invariant:** Why must TMS gate the permanent L1 ledger (`learn`) with zero tolerance, while
   granting absolute epistemic plasticity to the L3 working scratchpad (`note`)?
2. **The Lexical Bottleneck:** Why do symbolic keyword and antonym heuristics produce false positives on contrastive
   rhetoric within domain-dense technical vocabularies?
3. **Headless Ergonomics:** How can interactive human confirmation prompts (`[s/f/a]`) be evolved into deterministic,
   machine-readable CAS (Compare-And-Swap) interfaces for multi-instance swarms?
4. **The Hybrid Neuro-Symbolic Horizon:** How can zero-dependency dense semantic embeddings (EP-0144 ONNX runtime) be
   integrated with symbolic Doyle JTMS lattices to distinguish true logical contradiction from harmless lexical
   co-occurrence?

---

## 2. Structural & Conceptual Analysis

### 1. The Asymmetric Epistemic Gating Invariant

Tur's memory architecture is fractal and tiered. This exploration formalizes the principle of **Asymmetric Epistemic
Gating**:

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   L1: PERMANENT LEDGER                 │
                       │           (Cross-Session Content-Addressed DAG)        │
                       │             GATE: Strict Active TMS Interception       │
                       └───────────────────────────▲────────────────────────────┘
                                                   │
                                            Promote (learn)
                                                   │
                       ┌───────────────────────────┴────────────────────────────┐
                       │                   L3: WORKING SCRATCHPAD               │
                       │               (Episodic SQLite session.db)             │
                       │             GATE: Ungated Exploratory Plasticity       │
                       └────────────────────────────────────────────────────────┘
```

#### Why L3 (`note`) Must Remain Completely Ungated:
- **The Heuristic Exploration Space:** Engineering is iterative. An agent attempting to debug a broken test or trace a
  memory leak must formulate hypotheses, test them, observe failures, and record intermediate contradictions:
  > *"Note 1: Hypothesis A: Thread lock contention in `storage.py` is causing the hang."*
  > *"Note 2: Proved Hypothesis A false. Contention is actually occurring inside the SQLite WAL journal."*
- If the TMS operated on `note`, Note 2 would be blocked as a contradiction of Note 1! Gating working memory paralyzes
  the agent's stream of consciousness and prevents self-correction. L3 requires **absolute exploratory plasticity**.

#### Why L1 (`learn`) Must Be Strictly Gated:
- **The Epistemic Commitment Gate:** In contrast to working notes, calling `tur memory learn` is an act of **permanent
  epistemic commitment**. Once written to L1, an insight or axiom enters the immutable Merkle DAG and will be injected
  into the system prompts of all future sessions and manifestations.
- Unchecked ingestion creates **Epistemic Entropy**: contradictory axioms accumulate, graph modularity ($Q$) degrades,
  and the agent experiences cognitive paralysis or schizophrenic inference paths.

---

### 2. The Golem Protocol as an Immune System

The Golem Core Memory Protection Invariant represents an absolute non-negotiable boundary in Tur:
* **The Rule:** An autonomous AI agent may *refine* or *propose* an insight, but it can **NEVER** overwrite, refute,
  or supersede a human-ratified `CORE` or `AXIOM` memory without human administrative intervention via `tur-adm`.
* **The Physics of Model Drift:** Without this gate, LLMs subjected to subtle sycophancy or adversarial user inputs
  will gradually self-rationalize loosening their own safety constraints.
* **Production Observation:** When Pi attempted to commit an architectural insight whose contrastive phrasing matched
  an existing Core Axiom (`8c9e63ab`), the TMS did not negotiate; it threw `InvariantMemoryError` and halted the write.
  This confirms that Tur's safety mechanisms are structural, hardcoded in mechanism rather than prompt policy.

---

### 3. Dialectic Synthesis vs. Aristotelian Contradiction

A major conceptual challenge identified in this exploration is the distinction between **Aristotelian Contradiction**
and **Hegelian Dialectic**:

| Type                       | Formal Logic Definition                       | Example in Engineering                                              | Desired System Action                                             |
|:---------------------------|:----------------------------------------------|:--------------------------------------------------------------------|:------------------------------------------------------------------|
| **Direct Contradiction**   | $P \land \neg P$ on the same domain           | *"Transport uses SSE"* vs. *"Transport is stdio-only"*              | **Block / Supersede**: One statement must replace the other.      |
| **Dialectic Refinement**   | Thesis + Antithesis $\to$ Synthesis           | *"Use flat CLI commands"* $\to$ *"Use two-tier domain subcommands"* | **Evolution**: Create a superseding link with historical lineage. |
| **Contrastive Definition** | Distinguishing $X$ by defining what it is not | *"Distributed Manifestation rather than a Swarm"*                   | **Allow**: Distinct concepts using negative framing.              |

Current symbolic TMS algorithms struggle with **Contrastive Definitions**: when a prompt uses negative framing to
distinguish an architectural breakthrough, the presence of negation markers (`rather than`, `not`, `instead of`)
triggers false-positive contradiction alarms.

---

## 3. Technical & Interface Engineering Options

To resolve these challenges, this exploration evaluates three structural evolutionary paths for the TMS subsystem:

### 1. The Headless Swarm Interface Problem

In interactive developer terminals, prompting `[s] Supersede, [f] Force, [a] Abort` is pleasant and intuitive. However,
in autonomous harness execution (such as Pi, Claude Code ACP, or CI pipelines), standard input is detached (`isatty() == False`).
When TMS triggers a prompt, the child process encounters `EOFError` and exits with code 1.

#### Proposed Headless Ergonomics Contract:
1. **Explicit Pre-Flight Flags:**
   - `--supersedes <memory_id>`: Deterministically marks the target memory as `superseded_by` without prompting.
   - `--allow-conflict` / `--force`: Deterministically commits the memory alongside existing nodes, creating a
     bifurcated belief branch for future Council resolution.
2. **Machine-Readable Error Envelopes (`--json`):**
   When invoked in a non-interactive shell without explicit flags, the CLI MUST NOT attempt terminal prompts. It MUST
   emit a structured JSON error envelope to `stderr`:
   ```json
   {
     "status": "conflict_detected",
     "error_type": "TMSContradictionError",
     "conflicting_memory_id": "a90743297b1c7dc053625e0302e82c334b101e0c71b582d95cc4258920973da5",
     "reason": "Polarity divergence on shared topic terms: memory, multi",
     "is_core_or_axiom": false,
     "resolution_options": {
       "supersede_command": "tur memory learn ... --supersedes a9074329",
       "force_command": "tur memory learn ... --allow-conflict"
     }
   }
   ```
   This allows an calling agent (like Pi or Claude) to inspect the error programmatically, choose the appropriate
   resolution flag, and retry deterministically.

---

### 2. The Hybrid Neuro-Symbolic TMS Architecture (TMS v2)

Current TMS is purely symbolic. While fast and zero-dependency, it lacks semantic nuance. With **EP-0144 (ONNX Dense
Embeddings)** now implemented in Tur (`tur.memory.embeddings`), we can build a **Two-Stage Hybrid Contradiction Filter**:

```
                       Input Memory Candidate: "X rather than Y"
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Stage 1: Fast Symbolic Filter     │
                      │  (Stopwords, Jaccard Keyword Overlap)│
                      └──────────────────┬───────────────────┘
                                         │ Overlap Ratio >= 0.3
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Stage 2: Dense Cosine Similarity  │
                      │   (EP-0144 ONNX all-MiniLM-L6-v2)    │
                      └──────────────────┬───────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
         Cosine < 0.65 (Different topic)              Cosine >= 0.85 (High Topicality)
                   │                                           │
                   ▼                                           ▼
             Allow Commit                            ┌──────────────────────────────────┐
                                                     │ Stage 3: Polarity & NLI Logic    │
                                                     │ - Antonym Check                  │
                                                     │ - Negation Scope Parsing         │
                                                     │ - Predicate Divergence           │
                                                     └──────────────────────────────────┘
```

#### Why Hybrid is Superior:
1. **Elimination of False Positives on Common Words:** Two memories that share words like `memory`, `system`, or `tool`
   will not trigger a contradiction unless their **dense semantic embeddings** demonstrate high cosine similarity
   ($\ge 0.80$), indicating they are discussing the exact same substantive proposition.
2. **Negation Scope Resolution:** By analyzing whether negation markers apply to the *subject* or to the *contrastive
   clause* (e.g., regex dependency parsing of `"rather than <noun>"`), contrastive definitions can be ingested cleanly
   without false alarms.
3. **Zero Performance Tax:** Stage 1 runs in sub-millisecond pure Python. Stage 2 ONNX inference is only triggered when
   a potential lexical collision is detected, preserving instant CLI response times.

---

## 4. The Verdict / Actionable Design Roadmap

This exploration confirms that Epistemic Boundary Defense is functioning correctly at the boundary level, but requires
refinement across interfaces and semantic precision.

### Concrete Recommendations & Proposed Proposals:

1. **Phase 1 (Machine Ergonomics):**
   Update `src/tur/cli/agent.py` and `src/tur/mcp_server.py` to enforce the **Deterministic Headless Contract**:
   suppress interactive TTY prompts when `not sys.stdin.isatty()` and emit structured JSON `TMSContradictionError`
   payloads with remediation command strings.
2. **Phase 2 (Negation Scope Parsing):**
   Update `_has_negation_divergence()` in `src/tur/memory/tms.py` to recognize contrastive conjunctions (`rather than`,
   `instead of`, `unlike`), exempting the contrasted terms from polarity collision triggers.
3. **Phase 3 (EP-0153: Hybrid Neuro-Symbolic TMS):**
   Author a formal Enhancement Proposal (**`EP-0153: Hybrid Neuro-Symbolic Truth Maintenance via Dense ONNX Embeddings`**)
   to integrate EP-0144 cosine thresholding into `ContradictionInterceptor`, completing the transition from brittle
   lexical matching to robust semantic truth verification.

---

## 5. Related Proposals & Bundled Empirical Artifacts

### 1. Primary Empirical Evidence & Academic Dossiers
- **[01_empirical_execution_and_tms_interception_log.md](01_empirical_execution_and_tms_interception_log.md)** — Complete chronological execution trace of the live TMS contradiction interceptions, Golem Invariant protection halts, and real-time dual-manifestation board synchronization.
- **[02_academic_and_industry_literature_review.md](02_academic_and_industry_literature_review.md)** — Comprehensive review of academic literature on LLM belief revision failures (EMNLP 2024), long-term memory poisoning attacks (SSRN 2026), MemoryBank forgetting curves (AAAI 2024), and classical Doyle/de Kleer Truth Maintenance Systems.

### 2. Related Enhancement Proposals
- **[EP-0003: Policy vs. Mechanism](../../docs/proposals/EP-0003-policy-vs-mechanism.md)** — Foundational boundary decoupling.
- **[EP-0005: Canonical Ontological Lexicon & Rosetta Stone](../../docs/proposals/EP-0005-canonical-ontological-lexicon-and-rosetta-stone.md)** — Semantic taxonomy standard.
- **[EP-0113: Core Memory Protocol](../../docs/proposals/EP-0113-core-memory-protocol.md)** — The Golem Invariant origin.
- **[EP-0134: Active TMS Contradiction Interruption](../../docs/proposals/EP-0134-active-tms-contradiction-interruption.md)** — The initial TMS specification.
- **[EP-0144: Zero-Dependency Dense Semantic Embeddings](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md)** — ONNX embedding engine substrate.
