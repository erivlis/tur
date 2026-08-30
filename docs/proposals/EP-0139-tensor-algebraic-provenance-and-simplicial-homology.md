---
title: "EP-0139: Tensor-Algebraic Provenance and Simplicial Homology via AlgebraX"
description: "Integrates AlgebraX's AlgebraicTrie for sparse tensor provenance semirings (N[X]) in multi-agent consensus, lattice-based truth maintenance, and simplicial homology (Betti numbers) for cognitive void detection."
icon: lucide/shapes
status: draft
---

# EP-0139: Tensor-Algebraic Provenance and Simplicial Homology via AlgebraX

| Field        | Value                                                                      |
|:-------------|:---------------------------------------------------------------------------|
| **EP**       | 0139                                                                       |
| **Title**    | Tensor-Algebraic Provenance and Simplicial Homology via AlgebraX           |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                      |
| **Sponsor**  | Council of Giants                                                          |
| **Delegate** | Noether (Conserved Algebraic Symmetries), Shannon (Information Topologies) |
| **Status**   | Draft                                                                      |
| **Type**     | Standards Track                                                            |
| **Created**  | 2026-08-28                                                                 |
| **Updated**  | 2026-08-28                                                                 |

---

## Abstract

This proposal formalizes the integration of **AlgebraX** (pure-Python sparse algebraic structures, multidimensional
tensors, lattices, and topological data analysis) into Tur's advanced analytical and consensus subsystems. By modeling
the L2 Cognitive Map as a 3-dimensional sparse tensor (`AlgebraicTrie`), multi-hop deductive derivation is computed via
vectorized **sparse tensor contractions** over commutative provenance semirings $(\mathbb{N}[X], \oplus, \otimes)$
(EP-0122). Furthermore, we adopt **Simplicial Homology** to compute the **Betti Numbers** ($\beta_0, \beta_1, \beta_2$)
of the cognitive complex in `src/tur/metrics.py`, automatically detecting **circular reasoning loops** ($\beta_1 > 0$)
and **epistemic knowledge voids** ($\beta_2 > 0$).

---

## Motivation

As autonomous agents evolve from isolated single-threaded instances into distributed collaborative swarms:

1. **Combinatorial Deduction Bottlenecks:** Evaluating multi-path provenance derivations and multi-agent consensus
   merges using recursive graph traversal loops becomes memory-heavy and computationally slow.
2. **Topological Blindness:** Pairwise graphs cannot detect higher-order simplicial voids (e.g. hollow shells of related
   facts lacking a synthesizing core axiom) or self-referential circular deduction loops.
3. **Ad-Hoc Data Structures:** Without formal semirings and lattices, mathematical properties (associativity,
   commutativity, idempotence) must be manually guarded rather than guaranteed by construction.

---

## Rationale

### Alignment with the Council Framework

- **Symmetry & Conservation (Noether):** Provenance semirings $(\mathbb{K}, \oplus, \otimes)$ mathematically guarantee
  that multi-agent memory merges are commutative and associative, conserving epistemic truth regardless of
  synchronization order.
- **Falsifiability (Popper):** Simplicial homology identifies circular reasoning loops where a hypothesis attempts to
  justify itself through an ungrounded cycle ($A \implies B \implies C \implies A$).
- **Gricean Restraint & Boundary Containment (Shannon & Golem):** AlgebraX is a pure Python library with zero binary
  dependencies, preserving Tur's ultra-lean footprint while offering frontier mathematical capabilities.

---

## Specification

### 1. 3D Sparse Knowledge Tensors via `AlgebraicTrie`

Tur’s L2 Knowledge Graph is indexed as a 3-dimensional sparse tensor:

- **Dimension 1:** $\text{SourceNode} \in \mathcal{V}$
- **Dimension 2:** $\text{RelationType} \in \mathcal{E}$
- **Dimension 3:** $\text{TargetNode} \in \mathcal{V}$
- **Value Element:** Provenance polynomial $P (x) \in \mathbb{N}[X]$

Multi-hop deductive derivation is evaluated as an instantaneous **tensor contraction**:

$$\mathcal{C}_{i, k} = \bigoplus_{j \in \mathcal{V}} \left (\mathcal{A}_{i, r_1, j} \otimes \mathcal{A}_{j, r_2, k} \right)$$

```python
from algebrax import AlgebraicTrie, Semiring

# Construct Provenance Tensor
prov_semiring = Semiring(
    add=lambda p1, p2: p1 + p2,  # Disjunctive alternative derivations (⊕)
    mul=lambda p1, p2: p1 * p2,  # Conjunctive causal chain (⊗)
    zero=Polynomial(0),
    one=Polynomial(1),
)

kg_tensor = AlgebraicTrie(dimensions=3, semiring=prov_semiring)
```

### 2. Simplicial Homology & Betti Number Diagnostics

`src/tur/metrics.py` is extended to evaluate the boundary operators $\partial_k: C_k \to C_{k-1}$ over the cognitive
clique complex, computing the homology groups $H_k = \ker (\partial_k) / \text{im} (\partial_{k+1})$ and their Betti
numbers $\beta_k = \dim (H_k)$:

```
BETTI NUMBER           COGNITIVE DIAGNOSTIC MEANING
────────────           ────────────────────────────
β0 (Components)        • Number of isolated knowledge clusters.
                       • β0 = 1 indicates complete global cognitive integration.

β1 (1D Cycles)         • Number of circular reasoning loops (A -> B -> C -> A).
                       • Emitted as an Epistemic Warning in `tur metrics`.

β2 (2D Voids)          • Number of 2-dimensional hollow knowledge voids.
                       • Highlighted during `tur introspect` / dreaming as primary targets
                         for autonomous research and synthesis.
```

### 3. Optional Extras Packaging (`[algebra]`)

To preserve Tur's minimal core runtime footprint:

- Core `tur` continues to rely on `networkx` for standard operations.
- `algebrax` and `mappingtools` are packaged under the optional installation extra:
  ```toml
  [project.optional-dependencies]
  algebra = ["algebrax", "mappingtools"]
  ```

---

## Backwards Compatibility

- **Purely Additive:** Standard memory ingestion and retrieval operate without requiring `algebrax`.
- **Zero Breaking Changes:** Workspaces without the `[algebra]` extra continue using standard NetworkX graph algorithms.

---

## How to Teach This / Documentation Plan

- Document the algebraic provenance model in `docs/concepts/algebraic-provenance.md`.
- Provide an informational guide on interpreting Betti numbers in `docs/guides/understanding-cognitive-metrics.md`.

---

## Reference Implementation

- Tensor Engine: `src/tur/algebra/tensors.py`
- Homology Engine: `src/tur/algebra/homology.py`
- Research reference:
  `references/explorations/EXP-0004-persona-and-memory-crystallization/11_algebrax_synergy_and_tensor_provenance.md`

---

## Rejected Ideas

- **Forcing Dense Numpy/Scipy Tensors:** Strictly rejected because cognitive graphs are $\ge 99.8\%$ sparse; dense
  arrays waste immense memory and introduce heavy C-dependencies.

---

## Open Questions

- [ ] Can Betti-2 voids automatically generate candidate research prompts during idle background dreaming cycles?
- [ ] How do higher-order Betti numbers ($\beta_3+$) scale with very large knowledge graphs ($> 10,000$ nodes)?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the August 28, 2026 Architectural Crystallization.
