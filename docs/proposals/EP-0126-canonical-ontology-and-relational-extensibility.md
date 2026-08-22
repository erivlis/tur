---
title: "EP-0126: Canonical Ontology and Relational Extensibility"
description: "Formalizes canonical NodeType and EdgeType Enums (including metaphor_for) with controlled, declarative schema extensibility for domain personas."
icon: lucide/git-fork
status: implemented
---

# EP-0126: Canonical Ontology and Relational Extensibility

| Field             | Value                                                 |
|:------------------|:------------------------------------------------------|
| **EP**            | 0126                                                  |
| **Title**         | Canonical Ontology and Relational Extensibility       |
| **Author**        | Eran Rivlis <eran@erivlis.com>, Ariel <ariel@tur.dev> |
| **Sponsor**       | Eran Rivlis                                           |
| **Delegate**      | Russell (Council of Giants / Ontological Logic)       |
| **Status**        | Implemented                                           |
| **Type**          | Standards Track                                       |
| **Created**       | 2026-08-22                                            |
| **Updated**       | 2026-08-22                                            |
| **Replaces**      | None                                                  |
| **Superseded-By** | None                                                  |

## Abstract

This proposal establishes a formalized categorical ontology for Tur's L2 Cognitive Map (Deductive Memory). It introduces
standard Python `NodeType` and `EdgeType` models, formalizes `metaphor_for` as a first-class cognitive mapping
relationship alongside `analogy_of`, and establishes a three-tier architecture that combines deterministic canonical
validation with controlled, declarative relational extensibility for specialized domain personas.

## Motivation

During memory introspection (`tur introspect`), the `OntologyExtractor` subagent distills linear L1 event memories into
a topological semantic graph (L2 Cognitive Map). Previously, node and edge types were specified only as advisory text
descriptions in Pydantic schema strings. This created several critical failure modes:

| # | Failure Mode                            | Impact                                                                                                                                                                                            |
|:--|:----------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | **Semantic Entropy & Synonym Drift**    | LLMs frequently invent near-synonymous relational labels (e.g. `is_analogous_to`, `analogy`, `analogous_with`, `similarity_to`), fragmenting the Graph.                                           |
| 2 | **Deterministic Algorithmic Fragility** | Truth Maintenance System (TMS) deactivation rules, Cycle Detection on DAGs, and Hebbian decay rely strictly on well-known edge semantics.                                                         |
| 3 | **Rigidity vs. Flexibility Paradox**    | A completely closed Enum prevents specialized domain personas (e.g. legal, biological) from introducing domain-native invariants without patching Tur core.                                       |
| 4 | **Conflation of Analogy and Metaphor**  | The existing ontology included `analogy_of` (structural isomorphism) but lacked `metaphor_for` (figurative framing), forcing personas to misuse `analogy_of` or lose policy-to-mechanism bridges. |

## Rationale

### 1. Council Alignment

* **Russell (Ontological Precision & Logic)**: A formal type taxonomy ensures that every semantic claim in the cognitive
  map corresponds to a mathematically rigorous proposition. Typed edges prevent categorical confusion between causal
  ordering, hierarchical specialization, and epistemic conflict.
* **Popper (Truth Maintenance & Falsifiability)**: The Truth Maintenance Engine (TMS) requires deterministic relation
  semantics to resolve contradictory claims and propagate falsification cascades down dependency DAGs without unintended
  side effects.
* **Noether (Symmetry & Invariance)**: `metaphor_for` formalizes the exact symmetry between the Policy layer (metaphors,
  values, persona narrative) and the Mechanism layer (deterministic code and data structures).
* **Golem (Boundary Containment)**: Relational extensibility must be governed by declarative schema rules rather than
  arbitrary unconstrained text generation.

### 2. The Three-Tier Architectural Solution

To resolve the tension between strict consistency and persona extensibility, this proposal specifies a three-tier model:

1. **Tier 1: Canonical Standard Enum (`StrEnum`
   _**: Core Python enums (`NodeType` and `EdgeType`) defining universal cognitive primitives.
2. **Tier 2: Prompt Prioritization & Normalization**: The extraction prompt strictly mandates canonical types while
   allowing emergent types only when a novel invariant cannot be captured by the canonical vocabulary, requiring
   lowercase `snake_case` normalization.
3. **Tier 3: Declarative Persona Extension (`persona.yaml`)**: Domain personas declare approved custom edge types in
   their configuration, enabling automatic validation without core framework modification.

## Specification

### 1. Canonical Node & Edge Types (`src/tur/models.py`)

Define formal `StrEnum` classes for all canonical ontological primitives:

- **`NodeType`**: `Concept`, `Decision`, `Constraint`, `Insight`, `Fact`, `Dependency`, `Hypothesis`, `BoundaryNode`,
  `OpenQuestion`
- **`EdgeType`**:
- Hierarchy: `refines`
- Causality & Dependency: `precedes`, `depends_on`
- TMS & Dialectic: `contradicts`, `competes_with`, `superseded_by`, `refuted_by`
- Cognitive Mapping: `analogy_of`, `metaphor_for`

### 2. Semantics of Cognitive Mapping Edges

*| Edge Type | Nature | Signature | Definition & Example | +|:---|:---|:---|:---| +t `analogy_of` | Structural
Isomorphism | $AB:CD$ | Maps two systems that share identical operational logic across domains. (e.g. `merkle-dag` ->
`git-commit-history`) | +t `metaphor_for` | Figurative Framing | Vehicle -> Tenor | Connects a narrative/philosophical
metaphor to its underlying technical mechanism. (e.g. `traveler` -> `persistent-persona-identity`) |

### 3. Validation and Extensibility Contract

In `src/tur/introspection.py`, `ExtractedEdge` validates `type` against canonical `EdgeType` members, while supporting
registered persona extensions and sanitized `snake_case` tokens.

### 4. Declarative Persona Configuration (`persona.yaml`)

Domain personas can declare custom edge types directly in `persona.yaml`:

```yaml
map compaction:
  ontology:
    custom_edge_types:
      - "cites_precedent"
      - "overrules"
```

## Backwards Compatibility

* **Existing State Graphs**: 100% backwards compatible. Existing knowledge graphs built with the previous 8 edge types
  remain completely valid.
* **Additive Nature**: `metaphor_for` is purely additive.
* **Algorithmic Stability**: The Truth Maintenance System (TMS) and DAG validators only enforce constraints on specific
  canonical types (`precedes`, `depends_on`, `contradicts`, `superseded_by`, `refuted_by`), treating `metaphor_for` and
  custom emergent edges as non-destructive descriptive relations.

## How to Teach This / Documentation Plan

1. Update the canonical Tur skill reference document: `references/memory-taxonomy-and-schemas.md`.
2. Update `OntologyExtractor` docstrings, extraction prompt, and delegation instructions in `src/tur/introspection.py`.
3. Document the distinction between `analogy_of` and `metaphor_for` in the documentation concepts
   (`docs/concepts/deductive-memory.md`).

## Reference Implementation

* Code additions in `src/tur/models.py` (`NodeType`, `EdgeType`).
* Schema and prompt updates in `src/tur/introspection.py`.
* Test suite additions verifying `EdgeType` serialization, `metaphor_for` preservation, and custom edge type handling in
  `tests/test_introspection.py`.

## Rejected Ideas

1. **Pure Free-Form Unconstrained Strings**:
    * *Reason for Rejection:* Causes immediate entropy explosion in LLM outputs, resulting in dozens of synonymous edge
      variations that break NetworkX queries, cycle detection, and TMS deactivation cascades.
2. **Hard-Closed Enum with Strict Rejection of Non-Canonical Types**:
    * *Reason for Rejection:* Violates persona agnosticism by preventing domain-specific entities (e.g. legal,
      scientific, medical) from defining structural invariants native to their field.
3. **Merging `metaphor_for` into `analogy_of (**:
    * *Reason for Rejection:* Structural analogy ($AB:CD$) and metaphorical framing (Vehicle -> Tenor) serve
      fundamentally different epistemic purposes in cognitive modeling.

## Open Questions

- [ ] Whether custom domain edge types should support optional TMS propagation flags in `persona.yaml` (e.g.
  `cites_precedent: { transitive: true, decay_propagation: true }`).

## Change Log

* **2026-08-22:**
    * Implemented canonical `NodeType` and `EdgeType` `StrEnum` definitions in `tur.models`.
    * Integrated `metaphor_for` and `analogy_of` into `OntologyExtractor` prompt and delegation contract.
    * Implemented Tier 2 synonym normalization and Tier 3 declarative persona custom edge types in `_merge_extracted_graph`.
    * Initial Draft authored following Council approval (REV-0004).
