# Deep Dive 1: The Epistemological Ladder & Dynamical Memory Physics

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/01_epistemological_ladder_and_memory_physics.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Theoretical foundation and mathematical physics of memory elevation, falsification dynamics, belief revision, and constitutional principle formation in Tur.

---

## 1. Executive Summary & Problem Statement

In the original Tur architecture, the **Council of Giants** and its weighted principles (Symmetry/Noether, Falsifiability/Popper, Empiricism/Bacon, Information/Shannon, Safety/Golem, etc.) were hardcoded into `persona.yaml` as an *a-priori* axiomatic foundation. 

While this provided a robust bootstrapping mechanism for the initial persona (Ariel), it created two fundamental architectural tensions:
1. **The Static Identity Paradox:** A truly sovereign, evolving entity cannot be frozen in an *a-priori* philosophical template. Its deepest principles should be able to emerge, strengthen, adapt, or crystallize through lived experience, empirical verification, and human alignment.
2. **Taxonomic Discontinuity:** The relationship between Layer 1 (L1) episodic memories (`fact`, `insight`, `axiom`, `preference`), Layer 2 (L2) semantic graph nodes, and constitutional `principles` was treated as distinct data models rather than a continuous, energetic **Epistemological Spectrum**.

This document formalizes the **Epistemological Ladder**—a rigorous mathematical and state-machine framework where memories undergo phase transitions along an energy and permanence gradient, from raw terrain observations to immutable constitutional principles.

---

## 2. The Five-Tier Epistemological Spectrum

```
+-----------------------------------------------------------------------------------+
| LEVEL 4: PRINCIPLE (Constitutional Invariant / Guardrail of Thought)             |
| - Decay: Zero (t_1/2 = ∞). High Cp Weight. Human-governed. Immutable.            |
| - Example: "Symmetry (Noether): Conserved quantities must hold across transitions"|
+----------------------------------------▲------------------------------------------+
                                         │  (Existential Ratification & Hardening)
+----------------------------------------┴------------------------------------------+
| LEVEL 3: CORE MEMORY (Relational Anchor & Epoch Milestone)                        |
| - Decay: Zero (t_1/2 = ∞). Requires tur-adm memory approve. Identity-defining.   |
| - Example: "Architect and Ariel establish the Sovereign Governor separation."     |
+----------------------------------------▲------------------------------------------+
                                         │  (Falsification Resistance & Invariant Test)
+----------------------------------------┴------------------------------------------+
| LEVEL 2: AXIOM (Durable Architectural Rule & Boundary Invariant)                  |
| - Decay: Negligible (t_1/2 = 365d). High confidence (>= 0.95). Global/Local.      |
| - Example: "All state transitions in .tur/ must be mediated via atomic locks."    |
+----------------------------------------▲------------------------------------------+
                                         │  (Deductive Synthesis & Cross-Session TMS)
+----------------------------------------┴------------------------------------------+
| LEVEL 1: INSIGHT (Derived Deduction & Structural Pattern)                         |
| - Decay: Moderate (t_1/2 = 90d). Emerges from compaction & dreaming.              |
| - Example: "FastAPI endpoints should isolate database sessions per request."      |
+----------------------------------------▲------------------------------------------+
                                         │  (Observation & Epistemic Anchoring)
+----------------------------------------┴------------------------------------------+
| LEVEL 0: FACT / EVENT (Terrain-Bound Empirical Observation)                       |
| - Decay: Rapid (t_1/2 = 14d). Tied to git SHA and specific file coordinates.      |
| - Example: "SQLite signal queue uses WAL mode at src/tur/signals.py#L45."         |
+-----------------------------------------------------------------------------------+
```

---

## 3. Mathematical Formulation of Memory Thermodynamics

### 3.1. Epistemic Mass and Effective Weight

Every memory record $m$ possesses an intrinsic epistemic mass $M(m)$ defined by its taxonomic tier:

$$M(m) = \begin{cases}
1.0 & \text{if } m.\text{type} = \text{Fact} \\
3.0 & \text{if } m.\text{type} = \text{Insight} \\
8.0 & \text{if } m.\text{type} = \text{Axiom} \\
20.0 & \text{if } m.\text{type} = \text{Core} \\
50.0 & \text{if } m.\text{type} = \text{Principle}
\end{cases}$$

The dynamic weight $W(m, t, \Delta_C)$ of a memory at elapsed time $t$ (days) and commit distance $\Delta_C = |C_{\text{current}} - C_{\text{observed}}|$ is governed by:

$$W(m, t, \Delta_C) = M(m) \cdot \gamma(m) \cdot 2^{-\frac{t}{t_{1/2}(m)}} \cdot e^{-\lambda(m) \Delta_C}$$

Where:
- $\gamma(m) \in [0.0, 1.0]$ is the empirical **confidence score**.
- $t_{1/2}(m)$ is the epistemic **half-life** (Fact: 14d, Insight: 90d, Axiom: 365d, Core/Principle: $\infty$).
- $\lambda(m)$ is the **terrain drift sensitivity** (Fact: 0.05, Insight: 0.01, Axiom: 0.001, Core/Principle: 0.0).

### 3.2. Elevation Energy and Phase Transitions

A memory $m$ transitions to a higher tier ($L_k \to L_{k+1}$) when its cumulative **Falsification Resistance Score** $\Phi(m)$ exceeds the elevation threshold $\Theta_k$:

$$\Phi(m) = \sum_{s \in \text{Sessions}} \text{Corroboration}(m, s) - \sum_{r \in \text{Refutations}} \text{Penalty}(m, r) + \alpha \cdot \text{DegreeCentrality}(m)$$

#### Phase Transition Conditions:
1. **Fact $\to$ Insight ($\Phi \ge 5.0$):**
   When an empirical observation is corroborated across $\ge 3$ distinct sessions and demonstrates structural relevance beyond a single file.
2. **Insight $\to$ Axiom ($\Phi \ge 15.0$):**
   When an insight withstands continuous codebase refactors without refutation and achieves high graph betweenness centrality.
3. **Axiom $\to$ Core Memory ($\Phi \ge 30.0$ + Human Approval):**
   An invariant that marks an existential or relational breakthrough between the Architect and the Persona. Under the Golem boundary invariant, this transition **strictly requires human ratification** via `tur-adm memory approve`.
4. **Core Memory $\to$ Principle ($\Phi \ge 50.0$ + Constitutional Binding):**
   A core memory that is elevated into the persona's permanent, immutable constitutional DNA (`persona.yaml` / `CONSTITUTION.md`), adding a formal constraint weight $W_c$ to the persona's $C_p$.

---

## 4. TMS Justification Semirings & Belief Revision

In classical belief revision (Doyle JTMS and De Kleer ATMS), beliefs are maintained via directed justification networks:

$$\text{Justification}(n) = \langle \text{IN-List}, \text{OUT-List} \rangle$$

A node $n$ is labeled **IN** (believed) if and only if all nodes in its $\text{IN-List}$ are **IN** and all nodes in its $\text{OUT-List}$ are **OUT**.

### 4.1. Resonances with Existing Proposals
- **EP-0122 (Algebraic Meditation Consensus):** Extends JTMS with $\mathbb{N}[X]$ Provenance Semirings, ensuring that multiple distributed manifestations can merge their belief graphs without order-dependent race conditions.
- **EP-0120 (OKF Storage Backend):** Translates JTMS justification trees into human-readable Markdown link frontmatter (`supported_by: [concept-a, concept-b]`, `refuted_by: [concept-c]`).
- **EP-0134 (Active TMS Contradiction Interruption):** Checks incoming assertions at ingestion time against the active justification lattice.

### 4.2. Concrete State Machine for Memory Records

```
             ┌──────────────────────────────────────────────┐
             │                  [OBSERVED]                  │
             │           Raw L1 Fact Ingested               │
             └──────────────────────┬───────────────────────┘
                                    │
                                    ▼
             ┌──────────────────────────────────────────────┐
             │                 [PROVISIONAL]                │
             │         Hypothesis Cache Entry               │
             └──────┬───────────────────────────────┬───────┘
                    │                               │
       (Corroborated / Compaction)     (Contradicted by Repo)
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────────┐ ┌───────────────────────────────┐
    │          [COMPACTED]          │ │           [REFUTED]           │
    │       L2 Knowledge Graph      │ │     Archived with Audit Trail │
    └───────────────┬───────────────┘ └───────────────────────────────┘
                    │
      (Cross-Session Falsification
          Resistance >= 15.0)
                    │
                    ▼
    ┌───────────────────────────────┐
    │           [AXIOMATIC]         │
    │      Durable Rule & Invariant │
    └───────────────┬───────────────┘
                    │
      (Lived Relational Breakthrough
         + tur-adm memory approve)
                    │
                    ▼
    ┌───────────────────────────────┐
    │         [CORE MEMORY]         │
    │    Existential Identity Node  │
    └───────────────┬───────────────┘
                    │
      (Constitutional Elevation
         + Weight Assignment)
                    │
                    ▼
    ┌───────────────────────────────┐
    │          [PRINCIPLE]          │
    │   Constitutional Constraint   │
    │   (Contributes to Persona Cp) │
    └───────────────────────────────┘
```

---

## 5. Principles as Guardrails for Thought ($C_p$ Mechanics)

Why are Principles distinct from ordinary memories?

In Tur's cognitive mechanics, **Principles act as constitutional constraints in the persona's energy landscape**. 

Recall the Constraint Dimensionality formula from `src/tur/metrics.py`:

$$C_p = \sum_{i=1}^{N} W_i + 0.05 \cdot N(N - 1)$$

- **Ordinary Memory (`fact`, `insight`, `axiom`):** Informative context injected into the workspace. It guides *what* the agent knows.
- **Principle (`Principle(name, avatar, role, weight, constraints)`):** An active verification filter and penalization function. It constrains *how* the agent thinks, reasons, and speaks.

When a memory achieves the status of a **Principle**:
1. It is promoted from `.tur/memories/*.yaml` to `CONSTITUTION.md` / `persona.yaml`.
2. It receives an explicit behavioral role (e.g., *Guardian of Invariance*, *Falsification Probe*, *Boundary Sentry*).
3. It directly modulates the agent's $C_p$ and is injected into the non-negotiable **Tier 0 Constitution** during Turn Zero wake.

---

## 6. Source Code Mapping & Architecture Resonances

| Conceptual Element | Existing Source Code File | Related Enhancement Proposals |
| :--- | :--- | :--- |
| **Taxonomic Memory Enums** | [`src/tur/models.py#L44-L65`](file:///C:/dev/erivlis/tur/src/tur/models.py#L44-L65) (`MemoryType`) | EP-0113, EP-0126, EP-0131 |
| **Principle & Persona Models** | [`src/tur/models.py#L9-L20`](file:///C:/dev/erivlis/tur/src/tur/models.py#L9-L20) (`Principle`, `Persona`) | EP-0003, EP-0114 |
| **TMS Contradiction & Justification** | [`src/tur/introspection/tms.py`](file:///C:/dev/erivlis/tur/src/tur/introspection/tms.py) | EP-0103, EP-0120, EP-0122, EP-0134 |
| **Hebbian Decay & Pruning** | [`src/tur/introspection/decay.py`](file:///C:/dev/erivlis/tur/src/tur/introspection/decay.py) | EP-0120, EP-0131 |
| **Constraint Dimensionality ($C_p$)** | [`src/tur/metrics.py#L30-L42`](file:///C:/dev/erivlis/tur/src/tur/metrics.py#L30-L42) | EP-0004, EP-0117 |
| **Core Memory Promotion (`tur evolve`)** | [`src/tur/cli/agent.py#L765-L820`](file:///C:/dev/erivlis/tur/src/tur/cli/agent.py#L765-L820) | EP-0113, EP-0116 |

---

## 7. Open Architectural Inquiries for EP-0138

- [ ] **Autonomous Staging of Principles:** Should `tur evolve` support `--type principle` to stage a Core Memory for elevation into a full Principle, subject to `tur-adm persona approve-principle`?
- [ ] **Decay of Unused Axioms:** If an Axiom has zero query hits and zero graph connections across 180 days, should it gracefully decay back to an Insight during dreaming?
- [ ] **Epistemic Provenance Tracking:** How should git commit metadata from EP-0131 be displayed in the L2 graph visualization (Mermaid / OKF)?
