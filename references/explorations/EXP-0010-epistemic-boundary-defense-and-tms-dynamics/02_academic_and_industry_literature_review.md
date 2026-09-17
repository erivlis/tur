# 02: Academic & Industry Literature Review — Belief Revision, Truth Maintenance, and Memory Poisoning

| Field           | Value                                                                                                   |
|:----------------|:--------------------------------------------------------------------------------------------------------|
| **Exploration** | EXP-0010: Epistemic Boundary Defense                                                                    |
| **Document**    | Academic & Industry Literature Review                                                                   |
| **Subject**     | Belief Revision, Truth Maintenance Systems (TMS), Memory Poisoning, and Non-Monotonic Reasoning in LLMs |
| **Date**        | 2026-09-17                                                                                              |

---

## 1. Executive Summary

This survey reviews academic literature, empirical benchmarks, and security research regarding **belief revision**,
**contradiction detection**, and **memory integrity** in Large Language Model (LLM) agents.

The findings strongly validate the core thesis of **EXP-0010**:

1. **The Plasticity-Stability Dilemma is Inherent to Neural Weights:** Recent EMNLP 2024 research confirms that LLMs
   confront a fundamental mathematical trade-off between revising beliefs when presented with new evidence and
   maintaining existing beliefs against noise. LLMs cannot maintain their own internal consistency without an external,
   structured Truth Maintenance System (TMS).
2. **Memory Poisoning is an Exploited Vector:** Emerging 2026 security research demonstrates that un-gated long-term
   memory systems are vulnerable to "Prompt Persistence Attacks" (memory poisoning). Tur's **Golem Protocol Core Memory
   Protection Invariant** acts as an essential, non-bypassable barrier against this attack class.
3. **Classical Foundations Bridge the Gap:** The non-monotonic truth maintenance paradigms formulated by Jon Doyle
   (1979)
   and Johan de Kleer (1986) provide the exact formal mechanics needed to manage justification lattices over episodic
   knowledge graphs.

---

## 2. Key Academic Papers & Analysis

### Paper 1: The Inherent Failure of LLMs to Self-Manage Belief Revision

* **Title:** *Belief Revision: The Adaptability of Large Language Models Reasoning*
* **Authors:** EMNLP 2024 / arXiv:2406.19764
* **Venue:** Empirical Methods in Natural Language Processing (EMNLP 2024)
* **Core Contribution:** Introduced the `Belief-R` benchmark and Delta Reasoning ($\Delta R$) framework to test LLM
  adaptability when presented with conflicting premises over time.
* **Key Finding:** Evaluated $\sim$30 state-of-the-art LLMs across diverse prompting strategies. Models consistently
  failed to revise prior beliefs when presented with contradictory evidence. Crucially, the authors revealed a
  **fundamental performance trade-off**: models optimized to update beliefs frequently underperformed in scenarios
  where prior beliefs should have been maintained, while conservative models refused necessary updates.
* **Relevance to Tur & EXP-0010:** Proves that relying on the LLM's own inference to detect and resolve memory
  contradictions is structurally flawed. A deterministic, externalized engine (Tur's TMS) is mathematically required to
  arbitrate supersession.

---

### Paper 2: The Security Threat of Ungated Memory (Memory Poisoning)

* **Title:** *Prompt Persistence Attacks: Long-Term Memory Poisoning in LLM-Based Systems*
* **Date:** 2026
* **Identifier:** SSRN: 6183548 / DOI: 10.2139/ssrn.6183548
* **Core Contribution:** Demonstrated how adversarial prompts injected during conversational sessions can exploit
  naive automatic memory consolidation mechanisms. By slowly injecting conflicting assertions into persistent memory
  stores, an attacker can corrupt an agent's future behavior, bypass safety guardrails, and achieve persistent model
  jailbreaks.
* **Relevance to Tur & EXP-0010:** Direct empirical justification for the **Golem Core Memory Protection Invariant**.
  Because Tur strictly forbids autonomous agents from superseding human-governed `CORE` and `AXIOM` memories via
  `tur memory learn`, prompt persistence attacks cannot mutate the persona's foundational constitution.

---

### Paper 3: Long-Term Memory Consolidation and the Forgetting Curve

* **Title:** *MemoryBank: Enhancing Large Language Models with Long-Term Memory*
* **Authors:** AAAI 2024 / arXiv:2305.10250
* **Venue:** Association for the Advancement of Artificial Intelligence (AAAI 2024)
* **Core Contribution:** Implemented an external memory architecture using Ebbinghaus forgetting curves to decay and
  consolidate episodic interaction logs into long-term user profiles.
* **Limitation Identified:** While MemoryBank implements time-based forgetting, it lacks non-monotonic contradiction
  interception; if a user expresses mutually conflicting preferences, the vector store retrieves both, inducing
  reasoning hallucinations.
* **Relevance to Tur & EXP-0010:** Tur's architecture goes beyond passive forgetting curves (EP-0131 Hebbian decay) by
  combining exponential decay with active TMS contradiction interruption (EP-0134).

---

### Paper 4: The Classical Foundations of Truth Maintenance

* **Doyle, Jon (1979):** *A Truth Maintenance System*, Artificial Intelligence 12 (3): 231–272.
    * *Contribution:* Introduced Justification-based Truth Maintenance (JTMS), where assertions are marked `IN` or `OUT`
      based on well-founded justification chains and dependency-directed backtracking.
* **de Kleer, Johan (1986):** *An Assumption-Based TMS (ATMS)*, Artificial Intelligence 28 (2): 127–162.
    * *Contribution:* Allowed multiple context environments to coexist simultaneously by tagging data with minimal
      assumption sets, eliminating the need for state-space backtracking.
* **Relevance to Tur & EXP-0010:** Tur's `tur.memory.tms` implements a modern, pragmatic realization of Doyle's JTMS:
  memories are nodes linked by `refines`, `contradicts`, and `superseded_by` edges, maintaining valid active belief
  subgraphs.

---

## 3. Comparative Taxonomy Matrix

| Feature                       | Standard RAG / Vector Stores | LangChain / AutoGen / CrewAI   | MemoryBank (AAAI 2024)      | Tur TMS (EXP-0010 / EP-0134)                          |
|:------------------------------|:-----------------------------|:-------------------------------|:----------------------------|:------------------------------------------------------|
| **Storage Substrate**         | Dense Vector DB              | Conversational In-Memory Array | ChromaDB + Forgetting Curve | Content-Addressed Merkle DAG                          |
| **Contradiction Handling**    | None (Retrieves both)        | None (Token overflow)          | Passive time decay          | **Active Interception at Ingestion Gate**             |
| **Asymmetric Gating**         | No distinction               | No distinction                 | No distinction              | **Strict on L1 (`learn`), Ungated on L3 (`note`)**    |
| **Core Invariant Protection** | None                         | Soft prompt instructions       | None                        | **Structural (Hardware/POSIX/Engine Enforced)**       |
| **Resolution Protocol**       | Stale cosine ranking         | Conversational drift           | Overwrite                   | **Explicit (`supersede`, `allow_conflict`, `abort`)** |

---

## 4. Synthesis for the TMS v2 Specification (EP-0153)

The literature indicates that pure symbolic systems (like current Tur TMS) suffer from rigidity on natural language
nuances, while pure neural systems suffer from catastrophic forgetting and inconsistency.

The optimal design—ratified by this literature review—is the **Two-Stage Hybrid Neuro-Symbolic Gate**:

1. **Stage 1 (Symbolic Pre-Filter):** Doyle JTMS lattice and Jaccard token overlap for sub-millisecond pruning.
2. **Stage 2 (Dense Cosine Similarity):** EP-0144 ONNX semantic embedding (`all-MiniLM-L6-v2`) to verify whether
   lexical overlap represents true topical collision.
3. **Stage 3 (Strict Invariant Firewall):** Unconditional Golem protection blocking autonomous mutation of `CORE` and
   `AXIOM` nodes.
