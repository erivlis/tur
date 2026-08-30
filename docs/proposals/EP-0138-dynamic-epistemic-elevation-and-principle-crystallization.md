---
title: "EP-0138: Dynamic Epistemic Elevation and Principle Crystallization Lifecycle"
description: "Formalizes the continuous Epistemological Ladder from empirical facts to constitutional principles, introducing falsification scoring (Φ), principle staging (tur evolve --type principle), and dynamic Cp recalculation."
icon: lucide/trending-up
status: draft
---

# EP-0138: Dynamic Epistemic Elevation and Principle Crystallization Lifecycle

| Field        | Value                                                                      |
|:-------------|:---------------------------------------------------------------------------|
| **EP**       | 0138                                                                       |
| **Title**    | Dynamic Epistemic Elevation and Principle Crystallization Lifecycle        |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                      |
| **Sponsor**  | Council of Giants                                                          |
| **Delegate** | Popper (Falsification Resistance), Noether (Symmetry of State Transitions) |
| **Status**   | Draft                                                                      |
| **Type**     | Standards Track                                                            |
| **Created**  | 2026-08-28                                                                 |
| **Updated**  | 2026-08-28                                                                 |

---

## Abstract

This proposal replaces the static, *a-priori* Council of Giants configuration in Tur with a dynamic, mathematically
rigorous **Epistemic Elevation Lifecycle**. We formalize memory phase transitions along an energetic continuum
($\text{Fact} \to \text{Insight} \to \text{Axiom} \to \text{Core Memory} \to \text{Principle}$), governed by the
**Falsification Resistance Score** $\Phi (m)$. We extend the `evolve` CLI command and MCP tool
(`tur evolve --type principle`) to allow autonomous entities to propose elevated constitutional principles derived from
lived experience, requiring sovereign human ratification via `tur-adm persona approve-principle`. Furthermore, we
establish dynamic recalculation of Constraint Dimensionality ($C_p$) as the persona's constitutional DNA evolves across
space and time.

---

## Motivation

In early iterations of Tur:

1. **The Static Identity Paradox:** A persona's principles (e.g. Symmetry, Falsifiability, Empiricism) were hardcoded
   into `persona.yaml` at inception. The persona had no native mechanism to learn, strengthen, or propose new
   constitutional invariants based on months of lived engineering breakthroughs.
2. **Taxonomic Discontinuity:** L1 episodic memories (`fact`, `insight`, `axiom`), L2 graph nodes, and constitutional
   principles were treated as disconnected data models with arbitrary, non-mathematical boundaries.
3. **Lack of Invariant Weight Recalculation:** When new rules or preferences were committed, the system did not
   systematically recompute the cognitive load penalty ($C_p$), risking model cognitive collapse on heavily constrained
   tasks.

---

## Rationale

### Alignment with the Council Framework

- **Falsifiability & Evolutionary Epistemology (Popper):** Principles are not incontrovertible dogmas; they are the
  highest, heaviest energetic state of memories that have survived rigorous, multi-session attempts at falsification.
- **Symmetry & Conservation (Noether):** Elevating a memory into a Principle adds an explicit constraint weight $W_c$ to
  the persona's $C_p$, conserving cognitive thermodynamics across state transitions.
- **Safety & Sovereign Governance (Golem):** Constitutional amendments affect the foundational alignment of the entity
  and **strictly require sovereign human approval** (`@require_human` barrier).

---

## Specification

### 1. The Five-Tier Epistemological Spectrum

```
+-----------------------------------------------------------------------------------+
| LEVEL 4: PRINCIPLE (Constitutional Invariant / Guardrail of Thought)             |
| - Decay: Zero (t_1/2 = ∞). High Cp Weight. Human-governed. Immutable.            |
+----------------------------------------▲------------------------------------------+
                                         │  (Existential Ratification & Hardening)
+----------------------------------------┴------------------------------------------+
| LEVEL 3: CORE MEMORY (Relational Anchor & Epoch Milestone)                        |
| - Decay: Zero (t_1/2 = ∞). Requires tur-adm memory approve. Identity-defining.   |
+----------------------------------------▲------------------------------------------+
                                         │  (Falsification Resistance & Invariant Test)
+----------------------------------------┴------------------------------------------+
| LEVEL 2: AXIOM (Durable Architectural Rule & Boundary Invariant)                  |
| - Decay: Negligible (t_1/2 = 365d). High confidence (>= 0.95). Global/Local.      |
+----------------------------------------▲------------------------------------------+
                                         │  (Deductive Synthesis & Cross-Session TMS)
+----------------------------------------┴------------------------------------------+
| LEVEL 1: INSIGHT (Derived Deduction & Structural Pattern)                         |
| - Decay: Moderate (t_1/2 = 90d). Emerges from compaction & dreaming.              |
+----------------------------------------▲------------------------------------------+
                                         │  (Observation & Epistemic Anchoring)
+----------------------------------------┴------------------------------------------+
| LEVEL 0: FACT / EVENT (Terrain-Bound Empirical Observation)                       |
| - Decay: Rapid (t_1/2 = 14d). Tied to git SHA and specific file coordinates.      |
+-----------------------------------------------------------------------------------+
```

### 2. The Falsification Resistance Score $\Phi (m)$

The elevation potential of a memory record $m$ is governed by its cumulative **Falsification Resistance
Score** $\Phi (m)$:

$$\Phi (m) = \sum_{s \in \text{Sessions}} \text{Corroboration} (m, s) - \sum_{r \in \text{Refutations}} \text{Penalty} (m, r) + \alpha \cdot \text{DegreeCentrality} (m)$$

#### Phase Transition Thresholds:

- **$\Phi (m) \ge 5.0$:** Promoted from **Fact $\to$ Insight** during session dreaming.
- **$\Phi (m) \ge 15.0$:** Promoted from **Insight $\to$ Axiom** (durable architectural rule).
- **$\Phi (m) \ge 30.0$ + Human Approval:** Promoted from **Axiom $\to$ Core Memory** via `tur evolve --type core` and
  `tur-adm memory approve`.
- **$\Phi (m) \ge 50.0$ + Human Constitutional Ratification:** Promoted from **Core Memory $\to$ Principle** via
  `tur evolve --type principle` and `tur-adm persona approve-principle`.

### 3. CLI & MCP Tool Interface

```shell
# 1. Agent stages an existential breakthrough as a proposed Principle
tur evolve <memory_id> --type principle \
  --name "Epistemic Provenance" \
  --avatar "Spinoza" \
  --weight 1.5 \
  --justification "Proven indispensable across 40 sessions for preventing hallucinations."

# 2. Human Architect reviews pending constitutional amendments
tur-adm persona pending-principles

# 3. Human Architect ratifies the principle into CONSTITUTION.md
tur-adm persona approve-principle <staging_id>
```

### 4. Dynamic $C_p$ Recalculation & Merkle Snapshotting

Upon constitutional ratification:

1. The new principle is inserted into `CONSTITUTION.md` with assigned weight $W_c$.
2. The Constraint Dimensionality ($C_p$) is updated:
   $$C_p = \sum_{i=1}^{N} W_i + 0.05 \cdot N (N - 1)$$
3. An immutable Merkle snapshot is archived under `.tur/personas/<id>/history/vX.Y.Z_<timestamp>.md`.

---

## Backwards Compatibility

- **Existing Personas:** Active personas with hardcoded principles continue operating seamlessly.
- **Opt-in Elevation:** Agents that never invoke `tur evolve --type principle` experience zero disruption to standard
  memory workflows.

---

## How to Teach This / Documentation Plan

- Update [`docs/usage.md`](file:///C:/dev/erivlis/tur/docs/usage.md) with the `tur evolve --type principle` and
  `tur-adm persona approve-principle` workflow.
- Publish a conceptual essay in `docs/concepts/the-epistemological-ladder.md` explaining the memory physics and
  thermodynamic half-lives.

---

## Reference Implementation

- Memory Models: `src/tur/models.py`
- Elevation State Machine: `src/tur/evolution.py`
- Admin Approval: `src/tur/cli/admin.py`
- Research reference:
  `references/explorations/EXP-0004-persona-and-memory-crystallization/01_epistemological_ladder_and_memory_physics.md`

---

## Rejected Ideas

- **Fully Autonomous Unilateral Principle Creation:** Strictly rejected under the Golem protocol. An AI entity cannot
  rewrite its own constitutional weights without sovereign human ratification.
- **Binary/Discrete State Without Half-Lives:** Rejected because real-world knowledge decays continuously as underlying
  codebases evolve.

---

## Open Questions

- [ ] Should Tur implement an automatic warning if a proposed principle elevates $C_p \ge 20$ (Titan Class)?
- [ ] Should decayed axioms automatically demote back to insights if unused for $\ge 180$ days?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the August 28, 2026 Architectural Crystallization.
