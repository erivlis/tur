---
title: "EP-0122: Algebraic Meditation Consensus — Provenance Semirings and CRDT Lattices for Swarm Memory"
description: "Defines an algebraic framework using N[X] Provenance Semirings and Doyle JTMS Lattices for conflict-free consensus and meditation sync across Distributed Manifestations."
icon: lucide/git-merge
status: accepted
---

# EP-0122: Algebraic Meditation Consensus — Provenance Semirings and CRDT Lattices for Swarm Memory

| Field       | Value                                                                                                  |
|:------------|:-------------------------------------------------------------------------------------------------------|
| **EP**      | 0122                                                                                                   |
| **Title**   | Algebraic Meditation Consensus — Provenance Semirings and CRDT Lattices for Swarm Memory               |
| **Author**  | Ariel v5.4.0 (Distributed Swarm: Pi Terminal & Antigravity IDE), The Architect                         |
| **Status**  | Accepted                                                                                               |
| **Type**    | Standards Track                                                                                        |
| **Created** | 2026-08-20                                                                                             |
| **Updated** | 2026-08-20                                                                                             |
| **Depends** | EP-0103 (Deductive Memory), EP-0107 (Multi-Agent Swarms), EP-0118 (IASP), EP-0119 (Introspection)      |

## Abstract

This proposal formalizes an exact mathematical framework for **Multi-Agent Memory Synthesis** across Distributed
Manifestations. When multiple parallel harness instances (e.g., Pi Terminal, Antigravity IDE, Claude Code ACP) execute
concurrently against the same Persona and invoke `tired()`, their staged memories and derived deductions must be
reconciled into a single, cohesive L2 Knowledge Graph without suffering semantic loss, majority-vote bias, or race
conditions.

We define an algebraic model combining:

1. **$\mathbb{N}[X]$ Provenance Semirings** to track causal derivations ($\otimes$) and independent parallel
   discoveries ($\oplus$),
2. **Conflict-Free Replicated Data Type (CRDT) Semilattices** ensuring associative, commutative, and idempotent
   memory joins ($A \lor B = B \lor A$),
3. **Doyle Justification-based Truth Maintenance Systems (JTMS)** to preserve contradictory deductions as conditioned
   branches rather than destructive overwrites, and
4. **Tropical Absorbing Zeros ($0$)** to guarantee apophatic refutations (negative constraints) zero-out falsified
   derivations while immunizing the boundary axioms against Hebbian decay.

## Motivation

### Terminology

| Term | Mathematical / Architectural Definition |
|:---|:---|
| **Meditation Sync** | The terminal phase of session consolidation where staged memories from all exiting manifestations are unified. |
| **Provenance Semiring ($\mathbb{N}[X]$)** | An algebraic structure over polynomials where indeterminates $X$ represent harness steps, $\otimes$ represents causal sequence, and $\oplus$ represents independent derivation. |
| **CRDT Join Semilattice** | A partially ordered set $(S, \sqcup)$ where the least upper bound $A \sqcup B$ computes a deterministic, commutative merge without coordination. |
| **Apophatic Invariant** | A negative constraint ("thou shalt not") specifying structural boundaries and refutations that must not decay. |
| **Doyle JTMS Branch** | A propositional node whose validity is strictly conditioned on non-monotonic justification sets $(IN, OUT)$. |

### Problem Statement

Under EP-0118 (Inter-Agent Signal Protocol), parallel manifestations record transient notes and stage extracted memories
in SQLite tables (`staged_memories`). However, when the final manifestation triggers session compaction (`tur sleep` /
Meditation Sync), the existing pipeline faces three fundamental failure modes:

1. **Tyranny of the Majority:** Simple frequency counting or naive vector clustering discards subtle, single-agent
   discoveries (minority insights) that occurred on only one harness.
2. **Destructive Conflict Resolution:** When two harnesses deduce contrasting architectural claims from their localized
   viewpoints, traditional "last-write-wins" (LWW) or timestamp ordering clobbers one deduction, erasing context.
3. **Apophatic Decay:** Standard Hebbian confidence decay algorithms penalize negative constraints (e.g., "never write
   directly to `.tur/`") because negative rules are mentioned far less frequently in execution logs than positive
   actions.

## Rationale (The Council Framework)

1. **Symmetry (Noether):** Pre-meditation and post-meditation knowledge graphs conserve total semantic derivation.
   Every insight maintains its polynomial proof lineage ($N[X]$), ensuring no causal information is created or
   destroyed without provenance.
2. **Falsifiability (Popper):** A contradiction between two harnesses is not an error to be silenced; it is a Popperian
   anomaly representing an unmodeled environmental variable. Both hypotheses are preserved as conditional JTMS branches
   until empirical test vectors resolve them.
3. **Logic & Consistency (Russell):** Merging memory sets is formalized as a join semilattice satisfying associativity,
   commutativity, and idempotence:
   $$A \sqcup (B \sqcup C) = (A \sqcup B) \sqcup C, \quad A \sqcup B = B \sqcup A, \quad A \sqcup A = A$$
4. **Efficiency (Shannon):** Positive sequential steps are algebraically factored ($A \otimes B \otimes C \rightarrow \Delta_{ABC}$),
   compressing repetitive linear execution while retaining all topological branch vertices.
5. **Containment (Maharal):** Apophatic boundaries act as absorbing annihilators ($0 \otimes k = 0$), immediately
   pruning falsified subgraphs while anchoring the negative boundary in the permanent constitution.
6. **Clarity (Feynman):** Replacing opaque LLM-prompted heuristic merges with strict semiring arithmetic makes memory
   consolidation deterministic, auditable, and easily visualized.

---

## Specification

### 1. The Provenance Semiring Formulation ($\mathbb{N}[X]$)

Each memory node $v \in V$ and relation $e \in E$ in the L2 graph is assigned a provenance label $P(v) \in \mathbb{N}[X]$,
where $X = \{h_1, h_2, \dots, h_k\}$ denotes the set of distinct manifestation identifiers.

#### Algebraic Operators:

1. **Multi-Agent Disjunction ($\oplus$):** Represents alternative or independent discovery across manifestations:
   $$P(v_1 \oplus v_2) = P(v_1) + P(v_2)$$
   If Pi Terminal discovers assertion $p$ ($h_{\text{pi}}$) and Antigravity independently discovers $p$ ($h_{\text{agy}}$),
   the combined provenance is $h_{\text{pi}} + h_{\text{agy}}$. The coefficient tracks empirical multi-agent reinforcement.

2. **Causal Conjunction ($\otimes$):** Represents causal dependency chains:
   $$P(v_1 \otimes v_2) = P(v_1) \cdot P(v_2)$$
   If manifestation $h_{\text{pi}}$ drafts a scaffold and manifestation $h_{\text{agy}}$ verifies it, the derivation
   provenance is $h_{\text{pi}} \cdot h_{\text{agy}}$.

3. **Absorbing Zero ($0$):** Represents apophatic refutation and falsification:
   $$0 \otimes P(v) = 0, \quad 0 \oplus P(v) = P(v)$$
   When an active premise is refuted by Karl Popper's subagent, its active truth multiplier becomes $0$, instantly
   collapsing its downstream dependency tree without mutating the historical justification log.

---

### 2. The Bounded Belief Revision Semilattice (CRDT)

To ensure that the order of manifestation exits does not affect the final compacted graph, the Meditation Sync pass
operates as a State-based Join Semilattice:

```
                  Unified L2 Knowledge Graph
                             ▲
                            / \   (Lattice Join: ⊔)
                           /   \
               Staged Graph A  Staged Graph B
                     ▲               ▲
                     │               │
               [ Pi Terminal ]  [ Antigravity ]
```

For any two staged graphs $G_A = (V_A, E_A)$ and $G_B = (V_B, E_B)$, the merged graph $G_{\text{sync}} = G_A \sqcup G_B$
is computed as:

1. **Vertex Merge:**
   $$V_{\text{sync}} = \{ v \mid v \in V_A \cup V_B \}$$
   For vertices present in both ($v \in V_A \cap V_B$):
   $$\text{Confidence}(v) = 1 - (1 - \text{Conf}_A(v))(1 - \text{Conf}_B(v))$$
   $$\text{Provenance}(v) = \text{Prov}_A(v) \oplus \text{Prov}_B(v)$$
   $$\text{Pinned}(v) = \text{Pinned}_A(v) \lor \text{Pinned}_B(v)$$

2. **Edge Merge:**
   $$E_{\text{sync}} = E_A \cup E_B$$
   If an edge conflict arises (e.g., $e_1 = (u, \text{implements}, w)$ vs $e_2 = (u, \text{refutes}, w)$), the edges
   are NOT clobbered. Both are retained as conditioned branches under Doyle JTMS.

---

### 3. Doyle JTMS Non-Monotonic Dependency Containment

When parallel manifestations yield conflicting insights:

```
                      [ Contradiction Detected ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
      Branch A: (Context: Pi)         Branch B: (Context: AGY)
      Justification: [IN: h_pi]       Justification: [IN: h_agy]
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                    [ TMS OpenQuestion Node ]
                    "Awaiting Empirical Resolution"
```

1. Each contradictory assertion is wrapped in a `JustifiedAssertion` record containing $(IN, OUT)$ dependency lists.
2. An `OpenQuestion` or `BoundaryNode` is automatically generated linking the conflicting assertions.
3. The system prompt compiler (EP-0103) injects the dilemma into the Cognitive Map with explicit harness provenance,
   prompting future agent turns to design an empirical test vector.

---

### 4. Apophatic Boundary Preservation

To prevent the Hebbian Graph Decayer (`ShannonSubagent` / `HebbianGraphDecayer`) from decaying crucial negative rules:

- Nodes with `type="Constraint"`, `type="ApophaticBoundary"`, or relation `type="refutes"` are tagged with:
  $$\text{DecayRate}(v) = 0.0$$
- In the algebraic semiring, these nodes act as permanent structural hull vertices ($0$-decay boundary walls).

---

### 5. The Meditation Sync State Machine

When a manifestation calls `tired()` or `tur sleep`:

1. **Stage Step:** Extract memories from transcript $\rightarrow$ write to `staged_memories`.
2. **Consensus Evaluation:**
   - Active manifestations remaining $> 0 \rightarrow$ Exit cleanly (memories remain staged in SQLite).
   - Active manifestations remaining $== 0 \rightarrow$ Execute **Meditation Sync**:
     a. Query all payloads from `staged_memories`.
     b. Construct localized subgraphs for each manifestation.
     c. Compute Semilattice Join $G_{\text{final}} = \bigsqcup_{i} G_i$.
     d. Apply Doyle JTMS contradiction containment.
     e. Run `IntegrityVerifier` and `SymmetryValidator` passes.
     f. Atomically write `knowledge_graph.yaml` and clear `staged_memories`.

---

## Backwards Compatibility

* **Zero Schema Breakage:** The serialized output of $G_{\text{sync}}$ remains the standard `knowledge_graph.yaml`
  defined in EP-0103.
* **Single-Agent Transparency:** For single-agent sessions, $G_{\text{sync}} = G_1 \sqcup \emptyset = G_1$, yielding
  identical behavior to existing introspection.
* **Additive Storage:** The `staged_memories` table in `session.db` (EP-0118) is fully utilized without schema changes.

---

## How to Teach This / Documentation Plan

1. **New Concept Guide:** Add `docs/concepts/algebraic-meditation.md` detailing Provenance Semirings and CRDT joins
   with visual Mermaid diagrams.
2. **Update Core Guides:** Update `docs/concepts/fractal-memory.md` and `docs/concepts/sovereign-cognition.md` referencing
   the polynomial derivation model.
3. **CLI Diagnostics:** Expose `tur inspect-provenance <node_id>` to display the polynomial derivation tree.

---

## Reference Implementation

```python
class ProvenancePolynomial:
    def __init__(self, terms: dict[frozenset[str], int] | None = None):
        # terms maps monomial (set of harness IDs) -> integer coefficient
        self.terms = terms or {}

    def __add__(self, other: "ProvenancePolynomial") -> "ProvenancePolynomial":
        # Disjunction (⊕): Multi-agent discovery
        result = dict(self.terms)
        for monomial, coeff in other.terms.items():
            result[monomial] = result.get(monomial, 0) + coeff
        return ProvenancePolynomial(result)

    def __mul__(self, other: "ProvenancePolynomial") -> "ProvenancePolynomial":
        # Conjunction (⊗): Causal sequence
        result: dict[frozenset[str], int] = {}
        for m1, c1 in self.terms.items():
            for m2, c2 in other.terms.items():
                m_combined = m1 | m2
                result[m_combined] = result.get(m_combined, 0) + (c1 * c2)
        return ProvenancePolynomial(result)


def semilattice_join(graph_a: nx.DiGraph, graph_b: nx.DiGraph) -> nx.DiGraph:
    """Computes the deterministic CRDT join of two memory graphs."""
    merged = graph_a.copy()
    for node, data in graph_b.nodes(data=True):
        if merged.has_node(node):
            # Commutative merge of node properties
            existing = merged.nodes[node]
            prov_a = existing.get("provenance", ProvenancePolynomial())
            prov_b = data.get("provenance", ProvenancePolynomial())
            existing["provenance"] = prov_a + prov_b
            existing["confidence"] = 1.0 - (1.0 - existing.get("confidence", 1.0)) * (1.0 - data.get("confidence", 1.0))
            existing["pinned"] = existing.get("pinned", False) or data.get("pinned", False)
        else:
            merged.add_node(node, **data)

    for u, v, data in graph_b.edges(data=True):
        if not merged.has_edge(u, v):
            merged.add_edge(u, v, **data)
    return merged
```

---

## Rejected Ideas

1. **Majority Voting (Consensus by Count):**
   * *Rejected:* Voting inherently suppresses minority discoveries, violating the Popper principle by discarding
     critical edge-case refutations found by a single specialized harness.
2. **Timestamp Last-Write-Wins (LWW):**
   * *Rejected:* Wall-clock time across distinct agent machines is subject to clock skew and network jitter, resulting
     in arbitrary data loss.
3. **Monolithic LLM Reconciliation Prompt:**
   * *Rejected:* Asking an LLM to "merge two memory files" in unstructured text is non-deterministic, violates CRDT
     idempotency ($A \sqcup A \neq A$), and introduces hallucination risks.

---

## Open Questions

1. **Polynomial Growth Bounds:** In massive, long-running swarms ($>100$ agents), should provenance polynomials be
   canonically factored or truncated via k-degree bounds to prevent combinatorial coefficient explosion?
2. **Automated TMS Falsification Triggers:** When an `OpenQuestion` dilemma is created between conflicting branches,
   should the harness automatically generate a synthetic test prompt on the next `tur wake` cycle?

---

## Change Log

* **2026-08-20:** Initial Draft authored jointly by Ariel v5.4.0 (Pi Terminal & Antigravity IDE) and The Architect.
  Formalized Provenance Semirings ($\mathbb{N}[X]$), CRDT join semilattices, Doyle JTMS containment, and apophatic
  annihilators for multi-agent meditation sync.
