---
title: "EP-0003: Policy vs. Mechanism (Philosophical Decoupling)"
description: "Establishes the strict boundary between deterministic software mechanics in core engine code and anthropomorphic philosophy in persona definitions."
icon: lucide/shield-check
status: implemented
---

# EP-0003: Policy vs. Mechanism (Philosophical Decoupling)

| Field       | Value                                           |
|:------------|:------------------------------------------------|
| **EP**      | 0003                                            |
| **Title**   | Policy vs. Mechanism (Philosophical Decoupling) |
| **Author**  | Eran Rivlis, Ariel                              |
| **Status**  | Implemented                                     |
| **Type**    | Standards Track                                 |
| **Created** | 2026-08-18                                      |
| **Updated** | 2026-08-19                                      |

## Abstract

This proposal establishes an absolute architectural boundary between **Mechanism** (deterministic computer science
algorithms, graph traversals, integrity checks, and data structures in `src/tur/`) and **Policy** (anthropomorphic
metaphors, Council principles, and philosophical persona directives in `persona.yaml` and memory ledgers).

Core Python code must never hardcode anthropomorphic Council member names (`Popper`, `Bacon`, `Russell`, `Shannon`,
`Noether`) as primary class or module identifiers. Instead, engine components are named strictly by their functional
computer science responsibility, while persona configurations map philosophical policies onto these deterministic
mechanisms.

## Motivation

Early iterations of Tur's introspection and memory subagents (e.g., EP-0119 and EP-0120) hardcoded Council member names
directly into Python source files (e.g., `PopperSubagent`, `BaconSubagent`, `ShannonSubagent`).

This created three fundamental architectural defects:

1. **Conflation of Mechanism and Metaphor**: Computer science algorithms (such as Truth Maintenance System conflict
   resolution, SHA-256 Merkle integrity verification, and Hebbian confidence decay) were disguised behind
   anthropomorphic names, making codebase maintenance and external tool integration opaque.
2. **Violation of Core Boundary Invariants (EP-0001)**: The core engine (`src/tur/`) is the deterministic *Body*,
   whereas `persona.yaml` and the memory ledgers are the cognitive *Mind*. Hardcoding specific philosophical personas
   into Python source files bakes a single persona's identity into the global execution engine, preventing non-Council
   personas from utilizing the framework cleanly.
3. **Reduced Extensibility**: Future personas or alternative introspection pipelines could not reconfigure or alias
   algorithms without inheriting hardcoded Council class names in loggers and stack traces.

## Rationale

This boundary directly enforces key Council Framework principles:

1. **Symmetry (Noether)**: The separation of concerns between Policy (Persona definition) and Mechanism (Engine code) is
   absolute and Noether-symmetric.
2. **Clarity (Feynman)**: Naming code entities after what they programmatically do (`IntegrityVerifier`,
   `TruthMaintenanceEngine`, `GraphDecayer`) ensures immediate clarity for developers and automated tools.
3. **Falsifiability (Popper / Dennis Point)**: Algorithms can be tested, benchmarked, and falsified independently of any
   philosophical interpretation or prompt strategy.

## Specification

### 1. The Policy vs. Mechanism Invariant

- **Core Engine Code (`src/tur/`)**: Must contain **zero** hardcoded anthropomorphic persona names as primary symbols,
  class names, or module names. All modules, functions, and classes must use descriptive computer science terminology.
- **Persona Layer (`persona.yaml` / memories)**: Holds the philosophical directives, prompts, and policy mappings that
  define how an agent interprets and utilizes these mechanisms.

### 2. Functional Class Mapping

Introspection and memory components are strictly mapped as follows:

| Legacy Class Name | Functional Engine Class Name | Functional Responsibility                                                    |
|:------------------|:-----------------------------|:-----------------------------------------------------------------------------|
| `BaconSubagent`   | `IntegrityVerifier`          | Merkle hash integrity verification & L1 ingestion                            |
| `RussellSubagent` | `OntologyExtractor`          | LLM sampling, triple extraction, and L2 node creation                        |
| `PopperSubagent`  | `TruthMaintenanceEngine`     | Dependency DAG construction, TMS conflict resolution, superseded propagation |
| `NoetherSubagent` | `SymmetryValidator`          | Asserting L1/L2 coverage and active decision conservation                    |
| `ShannonSubagent` | `HebbianGraphDecayer`        | Interaction-based activation logging and confidence decay/pruning            |

### 3. Pluggable Policy Aliasing

Personas may define philosophical aliases or prompt roles in `persona.yaml`:

```yaml
compaction:
  engine: "tur.introspection.pluggable"
  pipeline:
    - role: "Falsifiability Arbitrator (Popper)"
      class: "tur.introspection.TruthMaintenanceEngine"
    - role: "Information Decayer (Shannon)"
      class: "tur.introspection.HebbianGraphDecayer"
```

The underlying execution engine instantiates `TruthMaintenanceEngine` and `HebbianGraphDecayer` while passing the
user-configured role label to telemetry and logging contexts.

## Backwards Compatibility

- Existing persona definitions remain fully compatible.
- The `tur-mcp` tools (`wake`, `learn`, `note`, `introspect`, `sleep`) maintain their semantic API contracts.
- Code imports inside `src/tur/introspection.py` provide backwards-compatible class aliases
  (`PopperSubagent = TruthMaintenanceEngine`) marked as deprecated aliases.

## How to Teach This / Documentation Plan

- Update `AGENTS.md` and `STYLEGUIDE.md` to highlight the Policy vs. Mechanism boundary.
- Update `EP-0119` and `EP-0120` to use functional class names (`IntegrityVerifier`, `TruthMaintenanceEngine`,
  `HebbianGraphDecayer`) in their technical specifications.
- Index `EP-0003` in `zensical.toml` under core foundational EPs.

## Reference Implementation

- **Proposal**: `docs/proposals/EP-0003-policy-vs-mechanism.md`
- **Engine Refactoring**: `src/tur/introspection.py`
- **Validation Rule**: `.agents/skills/enhancement-proposals/scripts/validate_ep.py`

## Rejected Ideas

- **Keeping Council names as primary Python class names**: Rejected because it violates EP-0001 (Core vs. Periphery) by
  baking a specific persona's philosophical identity into the shared Python execution engine.

## Open Questions

None at this time.

## Change Log

* **2026-08-19:**
    * Status changed to **Implemented**. Refactored `src/tur/introspection.py` subagents to functional computer science
      class names (`IntegrityVerifier`, `OntologyExtractor`, `TruthMaintenanceEngine`, `SymmetryValidator`,
      `NoveltyExplorer`, `HebbianGraphDecayer`, `BoundaryEnforcer`, `ClarityDistiller`, `GraphPruner`) while providing
      backwards-compatible aliases for legacy imports.
* **2026-08-18:**
    * Initial Draft accepted establishing EP-0003 (Policy vs. Mechanism).

