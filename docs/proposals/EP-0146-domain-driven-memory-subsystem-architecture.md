---
title: "EP-0146: Domain-Driven Memory Subsystem Architecture"
description: "Consolidates flat memory, recall, introspection, dreaming, provenance, diff, and sanitizer modules into a cohesive, domain-driven tur.memory package."
icon: lucide/database
status: draft
---

# EP-0146: Domain-Driven Memory Subsystem Architecture

| Field        | Value                                                         |
|:-------------|:--------------------------------------------------------------|
| **EP**       | 0146                                                          |
| **Title**    | Domain-Driven Memory Subsystem Architecture                   |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                         |
| **Sponsor**  | Council of Giants                                             |
| **Delegate** | Turing (Machine Architecture), Maharal (Boundary Containment) |
| **Status**   | Draft                                                         |
| **Type**     | Standards Track                                               |
| **Created**  | 2026-09-04                                                    |
| **Updated**  | 2026-09-04                                                    |

---

## Abstract

This proposal refactors Tur's flat memory-related modules at the root of `src/tur/` (`memory.py`, `recall.py`,
`introspection.py`, `dreaming.py`, `provenance.py`, `diff.py`, and `sanitizer.py`) into a unified, domain-driven package
namespace: `src/tur/memory/`. By establishing a canonical `tur.memory` package with an explicit public facade in
`__init__.py`, Tur achieves clean internal decoupling, eliminates circular deferred import workarounds, and grounds its
architectural topology in functional computer science mechanisms while preserving 100% backwards compatibility for all
existing callers, test suites, and MCP server endpoints.

---

## Motivation

Throughout Waves 1 through 4, Tur's memory engine expanded from simple YAML persistence into an advanced, multi-tiered
cognitive state engine:

1. **L1 Flat Store & Merkle Ledger** (`memory.py`, EP-0106)
2. **Session Dreaming & Dehydration** (`dreaming.py`, EP-0110)
3. **L2 Cognitive Map & Council Assembly** (`introspection.py`, EP-0119, EP-0120)
4. **Graph-Theoretic Semantic Retrieval** (`recall.py`, EP-0136)
5. **Observation Provenance & Epistemic Decay** (`provenance.py`, EP-0131)
6. **Session Delta Observability** (`diff.py`, EP-0133)
7. **Secret Sanitization & Merkle Tombstones** (`sanitizer.py`, EP-0143)

Because these capabilities were introduced iteratively, they currently exist as sibling modules directly under
`src/tur/`. This flat structure produces several critical liabilities:

1. **Namespace Clutter & Low Domain Cohesion:** New contributors and agents inspecting `src/tur/` observe a flat list of
   18+ disparate files where storage, CLI routing, path resolution, and graph algorithms are intermingled at the same
   directory level.
2. **Proliferation of Inline Deferred Imports:** Because modules like `recall.py`, `introspection.py`, `dreaming.py`,
   and `metrics.py` mutually reference storage, hashing, and graph loaders, developers were forced to place import
   statements inside function bodies (`from tur.memory import MemoryManager`, `from tur.introspection import ...`) to
   prevent cyclic import failures at runtime.
3. **Muddled Abstraction Boundaries:** External callers and tests interact with fragmented top-level modules rather than
   a cohesive, authoritative memory API.

---

## Rationale

### Alignment with the Council Framework

- **Turing (Mechanism & Architecture):** Reorganizing modules into functional computer-science domains enforces clean
  boundaries between system inputs, storage mechanisms, and retrieval algorithms.
- **Maharal (Boundary Containment):** Preserves strict isolation between the Traveler (memory/state) and the Terrain
  (workspace execution) [EP-0001].
- **Noether (Symmetry & Invariance):** The public interface contract must be strictly invariant; existing external
  imports (`from tur.memory import MemoryManager`) must continue functioning seamlessly across the refactor.
- **Shannon (Information & Channel Capacity):** Eliminates redundant import overhead, reduces cognitive search space for
  agents reading the codebase, and establishes clear dependency direction.

---

## Specification

### 1. Target Package Structure

The flat files will be consolidated into the `src/tur/memory/` subpackage:

```text
src/tur/
├── memory/                      # Domain-driven memory subsystem package
│   ├── __init__.py              # Public facade re-exporting canonical symbols
│   ├── storage.py               # L1 persistence, Merkle trees, subsumption (formerly memory.py)
│   ├── recall.py                # HippoRAG PPR, Louvain clustering, effort spectrum (EP-0136)
│   ├── introspection.py         # L2 OKF graph compiler & Council subagents
│   ├── dreaming.py              # Session transcript dehydration & insight formation
│   ├── provenance.py            # Temporal anchors, git commit drift, staleness (EP-0131)
│   ├── diff.py                  # Cross-session memory mutations & delta classification (EP-0133)
│   └── sanitizer.py             # Merkle tombstones & credential scrubbing (EP-0143)
├── persona/                     # Persona identity & constitution
├── session/                     # Session state, scratchpad, inter-agent signals
├── cli/                         # Typer CLI binaries (tur, tur-adm, tur-mcp)
├── compiler.py                  # Prompt compilation from persona + memories
├── locking.py                   # FileLock multiprocessing primitives
├── metrics.py                   # Constraint dimensionality & spectral diagnostics
├── models.py                    # Pydantic schemas and enums
└── paths.py                     # OS-native directory and terrain isolation predicates
```

### 2. Public Facade Contract (`src/tur/memory/__init__.py`)

The package `__init__.py` exposes the canonical public interface:

```python
from tur.memory.diff import compute_session_diff, format_diff_json
from tur.memory.dreaming import perform_sleep_dreaming
from tur.memory.introspection import format_graph_as_mermaid, load_l2_graph_from_okf, run_introspection
from tur.memory.provenance import create_provenance_and_decay, evaluate_staleness
from tur.memory.recall import CognitiveGraphEngine, pure_algebraic_connectivity, pure_pagerank, topological_recall
from tur.memory.sanitizer import redact_memory
from tur.memory.storage import MemoryManager

__all__ = [
    "MemoryManager",
    "topological_recall",
    "CognitiveGraphEngine",
    "pure_pagerank",
    "pure_algebraic_connectivity",
    "run_introspection",
    "load_l2_graph_from_okf",
    "format_graph_as_mermaid",
    "perform_sleep_dreaming",
    "evaluate_staleness",
    "create_provenance_and_decay",
    "compute_session_diff",
    "format_diff_json",
    "redact_memory",
]
```

### 3. Root Compatibility Shims

To guarantee zero breakage across third-party extensions and older scripts during the transition period, root-level
module shims (e.g. `src/tur/recall.py`, `src/tur/introspection.py`, `src/tur/dreaming.py`, `src/tur/provenance.py`,
`src/tur/diff.py`, `src/tur/sanitizer.py`) will re-export their symbols from `tur.memory.<module>` with a deprecation
pathway, or be systematically migrated across all internal calls.

---

## Backwards Compatibility

1. **Import Invariance:**
   Code calling `from tur.memory import MemoryManager` will function identically without modification because
   `src/tur/memory/__init__.py` re-exports `MemoryManager` from `storage.py`.
2. **CLI & MCP Tool Compatibility:**
   `tur recall`, `tur status`, `tur diff`, `tur metrics`, and all MCP tools (`recall()`, `introspect()`, `diff()`, etc.)
   maintain identical CLI signatures, flags, and JSON output schemas.
3. **Zero State Store Mutations:**
   This is a pure mechanism and code organization refactor. On-disk formats (`.tur/memories/*.md`,
   `knowledge_graph.yaml`,
   `concepts/*.md`) remain 100% untouched.

---

## How to Teach This / Documentation Plan

- Update `docs/usage.md` and developer guides to reference `tur.memory`.
- Update `.agents/skills/tur/references/commands-and-mcp-tools.md` to reflect the package topology.
- Add an architectural diagram in `docs/architecture/` showing the three core domains: `persona`, `session`, and
  `memory`.

---

## Reference Implementation

- Target package directory: `src/tur/memory/`
- Facade: `src/tur/memory/__init__.py`
- Verification: 355/355 tests passing in `tests/` with `ty check src` producing 0 errors.

---

## Rejected Ideas

- **`tur.cognition`:** Rejected because in Tur's core Obligate Symbiote architecture, the LLM provides the
  cognition/inference ("Brain"), while Tur provides deterministic state and memory ("Soul/State"). Furthermore, the
  Grounded Technical Prose Invariant instructs us to prefer concrete computer science mechanisms over aspirational
  metaphors.
- **`tur.knowledge`:** Rejected because while accurate for L2 knowledge graphs, it fails to encompass raw L1 event logs,
  session transcript dreaming, and filesystem Merkle storage.
- **Splitting into `tur.memory` and `tur.graph`:** Rejected because L1 ledger storage and L2 graph compaction form a
  single, integrated fractal memory hierarchy. Separating them into disjoint packages would re-introduce cross-package
  coupling and import friction.

---

## Open Questions

- [ ] Should `models.py` memory models (`Memory`, `MemoryType`, `MemoryScope`) eventually migrate into
  `tur.memory.models`
  or remain in root `tur.models` for shared persona/session typing?
- [ ] Should root-level compatibility modules emit a runtime `DeprecationWarning` or remain silent shims indefinitely?

---

## Change Log

* **2026-09-04:**
    * Initial Draft authored following the consensus to establish `tur.memory` as the authoritative memory subsystem.
