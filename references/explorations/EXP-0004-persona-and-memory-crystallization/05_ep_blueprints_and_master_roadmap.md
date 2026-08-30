# Master Synthesis: EP Blueprints & Architectural Resonance Roadmap

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/05_ep_blueprints_and_master_roadmap.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Master synthesis connecting the 12 crystallization hypotheses, existing 40+ EPs, source code implementations, and concrete specifications for Enhancement Proposals EP-0135 through EP-0138.

---

## 1. Executive Summary

This master roadmap synthesizes the **August 28, 2026 Architectural Crystallization** into a concrete, executable engineering blueprint. It elevates Tur from a static, hardcoded prompt compiler into a **modular, graph-topological, contract-driven cognitive operating system**.

```
                                  ┌───────────────────────────────┐
                                  │      TUR EVOLUTION EPOCH      │
                                  │   (Mind & Substrate Synergy)  │
                                  └───────────────┬───────────────┘
                                                  │
                ┌───────────────────┬─────────────┴─────┬───────────────────┐
                ▼                   ▼                   ▼                   ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │    EP-0135    │   │    EP-0136    │   │    EP-0137    │   │    EP-0138    │
        │    Modular    │   │ Graph-Theory  │   │ Contract-     │   │  Epistemic    │
        │  Scaffolding  │   │ Topological   │   │ Driven Skills │   │   Elevation   │
        │  (AGENTS.md)  │   │   Retrieval   │   │  (The Forge)  │   │  (Principles) │
        └───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
```

---

## 2. Comprehensive Architectural Resonance Matrix

| # | Crystallization Hypothesis | Existing EP Resonances | Source Code Touchpoints | Target New EP |
| :-: | :--- | :--- | :--- | :--- |
| **1** | Shift away from persona engineering to state engine | **EP-0003, EP-0116, EP-0124** | `src/tur/cli/admin.py`, `paths.py`, `locking.py` | **EP-0135 / EP-0137** |
| **2** | `persona init` intended to create identity foundation | **EP-0004, EP-0114, EP-0116** | `src/tur/cli/wizards.py`, `cli/admin.py#L75` | **EP-0135** |
| **3** | Is *a-priori* Council definition appropriate? | **EP-0003, EP-0108, EP-0113** | `src/tur/models.py#L9`, `compiler.py` | **EP-0138** |
| **4** | Principles as elevated, heavy Core Memories ($C_p$ guardrails) | **EP-0108, EP-0113, EP-0120** | `src/tur/models.py#L44`, `metrics.py` | **EP-0138** |
| **5** | `AGENTS.md` as industry standard bootstrap (AAIF/Linux Foundation) | **EP-0101, EP-0109, EP-0121** | `AGENTS.md`, `src/tur/compiler.py` | **EP-0135** |
| **6** | `persona init` outcome as structured `AGENTS.md` + `.tur/` | **EP-0004, EP-0114, EP-0128** | `src/tur/cli/wizards.py`, `persona.py` | **EP-0135** |
| **7** | `tur wake` minimal and token-budgeted | **EP-0108, EP-0130, EP-0132** | `src/tur/cli/agent.py#L41`, `mcp_server.py#L141` | **EP-0132 / EP-0135** |
| **8** | Graph-theoretic measures in `metrics` (NetworkX) | **EP-0004, EP-0103, EP-0117** | `src/tur/metrics.py`, `introspection/graph.py` | **EP-0136** |
| **9** | Meaningful subgraphs (Louvain communities, PPR spreading activation) | **EP-0103, EP-0120, EP-0126** | `src/tur/recall.py`, `introspection/tms.py` | **EP-0136** |
| **10** | Principles in `CONSTITUTION.md` vs `AGENTS.md` separation | **EP-0003, EP-0114, EP-0116** | `src/tur/templates/persona.j2`, `persona.py` | **EP-0135** |
| **11** | Decoupling constitution generation to skills (e.g. `subagent-prompt-generator`)| **EP-0003, EP-0102, EP-0119** | `.agents/skills/tur/`, `src/tur/dreaming.py` | **EP-0137** |
| **12** | Generalizing Tur via contract-driven pluggable skills | **EP-0003, EP-0105, EP-0121** | `src/tur/models.py`, `introspection/` | **EP-0137** |

---

## 3. Detailed Specifications for Target Enhancement Proposals

---

### 3.1. Blueprint: EP-0135 (The Modular Scaffolding Protocol)

- **Title:** `EP-0135: The Modular Scaffolding Protocol — Decoupling Operational Harnessing (AGENTS.md) from Persona Identity (CONSTITUTION.md)`
- **Type:** Standards Track
- **Status:** Draft
- **Key Specifications:**
  1. **Dual-File Scaffolding on `tur-adm persona init`:**
     - Generates repository-root `AGENTS.md` (AAIF open standard for Cursor, Copilot, Claude Code, Antigravity).
     - Generates `.tur/CONSTITUTION.md` containing Persona Aleph ($\aleph$), active principle weights, and ethical boundaries.
  2. **Lean Prompt Compiler:**
     - Strips redundant mechanical tool instructions from `compile_persona()`, reducing Turn Zero context payload from $\sim 4,500$ tokens to $\sim 1,200$ tokens.
  3. **`tur scaffold` Utility:**
     - Adds `tur scaffold --format [aaif|claude|generic]` to automatically repair or generate harness configuration files on demand.

---

### 3.2. Blueprint: EP-0136 (Graph-Theoretic Semantic Retrieval & Metrics)

- **Title:** `EP-0136: Graph-Theoretic Semantic Subgraph Retrieval and Topological Cognitive Metrics`
- **Type:** Standards Track
- **Status:** Draft
- **Key Specifications:**
  1. **NetworkX Core Adoption:**
     - Formalizes `networkx.DiGraph` as the in-memory substrate for `src/tur/recall.py` and `src/tur/introspection/graph.py`.
  2. **Cognitive Effort Spectrum (`tur recall --effort <0-10>` / `--deep`):**
     - `--effort 0` (Default / Instant): Fast BM25 keyword + flat vector similarity ($< 5\text{ms}$).
     - `--effort 1-4` (Light Context): Vector match + 1-hop ego neighborhood.
     - `--effort 5-7` (`--deep`): Full HippoRAG Personalized PageRank (PPR) spreading activation + Louvain community subgraph extraction.
     - `--effort 8-10` (Exhaustive TMS): Full PPR + Louvain extraction + real-time Git commit verification (EP-0131) + TMS contradiction checks (EP-0134).
  3. **Spectral Health Diagnostics in `tur metrics`:**
     - Calculates Algebraic Connectivity (Fiedler eigenvalue $\lambda_2$) and Modularity ($Q$) to detect cognitive fragmentation in real time.

---

### 3.3. Blueprint: EP-0137 (Contract-Driven Cognitive Skills & Pluggable Forge)

- **Title:** `EP-0137: Contract-Driven Cognitive Skills and the Pluggable Forge Architecture`
- **Type:** Standards Track
- **Status:** Draft
- **Key Specifications:**
  1. **Standardized Pydantic I/O Contracts (`src/tur/contracts/`):**
     - `PersonaForgeContract`: User interview $\to$ `CONSTITUTION.md` + initial axioms.
     - `DreamingCompactionContract`: Session transcripts $\to$ L2 graph deltas.
     - `VerificationContract`: Memory provenance $\to$ Git ground-truth validation.
  2. **Zero Hardcoded Prompts in Core Kernel:**
     - Replaces monolithic Gemini API prompt strings in `src/tur/dreaming.py` with pure-function delegation contracts.
  3. **Local Skill Override Protocol:**
     - Allows workspaces to define custom skills in `.tur/skills/` (e.g. local Ollama dreamer, enterprise Jira persona forger).

---

### 3.4. Blueprint: EP-0138 (Dynamic Epistemic Elevation Lifecycle)

- **Title:** `EP-0138: Dynamic Epistemic Elevation and Principle Crystallization Lifecycle`
- **Type:** Standards Track
- **Status:** Draft
- **Key Specifications:**
  1. **The Epistemological Continuum:**
     - Formalizes mathematical phase transitions: $\text{Fact} \xrightarrow{\Phi \ge 5} \text{Insight} \xrightarrow{\Phi \ge 15} \text{Axiom} \xrightarrow{\Phi \ge 30 + \text{Approve}} \text{Core Memory} \xrightarrow{\Phi \ge 50} \text{Principle}$.
  2. **`tur evolve --type principle`:**
     - Extends the `evolve` tool to allow autonomous agents to stage lived invariants as candidate Principles for human ratification in `tur-adm`.
  3. **Dynamic $C_p$ Weight Recalculation:**
     - Automatically updates persona constraint dimensionality when new principles are crystallized or decayed.

---

## 4. Implementation Phasing & Execution Order

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           IMPLEMENTATION PHASING                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1: Scaffolding & Harness Separation (EP-0135)                             │
│   1. Implement AGENTS.md / CONSTITUTION.md emission in `tur-adm persona init`.  │
│   2. Refactor `compile_persona()` to eliminate redundant tool instructions.    │
│   3. Validate zero-turn bootstrapping across Copilot, Claude, and Antigravity.  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: Graph Theory & Associative Retrieval (EP-0136)                         │
│   1. Introduce NetworkX DiGraph loading in `src/tur/recall.py`.                 │
│   2. Implement Louvain community detection and PPR spreading activation.        │
│   3. Add Algebraic Connectivity (λ2) to `src/tur/metrics.py`.                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: Contract-Driven Pluggable Skills (EP-0137)                             │
│   1. Define Pydantic schema contracts in `src/tur/contracts/`.                  │
│   2. Decouple `dreaming.py` into pure-function delegation handlers.             │
│   3. Build the interactive `persona-forge` skill in `.agents/skills/`.          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: Epistemic Elevation Lifecycle (EP-0138)                                │
│   1. Implement Falsification Resistance score Φ(m) calculation.                 │
│   2. Extend `tur evolve` and `tur-adm memory approve` to support Principle tier.│
│   3. Connect memory promotion events to automatic CONSTITUTION.md updates.      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. References & Foundational Literature

1. **HippoRAG (Neurobiological Associative Memory):**
   - *Bernal et al. (2024)* — "HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models using Personalized PageRank." (arXiv:2405.14831)
2. **LightRAG (Dual-Level Knowledge Graphs):**
   - *Guo et al. (2024)* — "LightRAG: Simple and Fast Retrieval-Augmented Generation." (arXiv:2410.05779)
3. **Agentic AI Foundation (AAIF) Standards:**
   - *Linux Foundation (2025–2026)* — `AGENTS.md` Open Repository Specification.
4. **Belief Revision & Truth Maintenance Systems:**
   - *Doyle, J. (1979)* — "A Truth Maintenance System." *Artificial Intelligence*, 12(3), 231-272.
   - *De Kleer, J. (1986)* — "An Assumption-based TMS." *Artificial Intelligence*, 28(2), 127-162.
5. **Spectral Graph Theory & Modularity:**
   - *Fiedler, M. (1973)* — "Algebraic Connectivity of Graphs." *Czechoslovak Mathematical Journal*, 23(2), 298-305.
   - *Blondel et al. (2008)* — "Fast unfolding of communities in large networks (Louvain Method)." *J. Stat. Mech.*
