---
title: "EP-0119: The Subagent Assembly of the Council (De-Monolithing Meditation)"
description: "Formalizes a collaborative, multi-agent pipeline for deductive memory compaction governed by the Council of Giants. Status: Planning — philosophical tension with persona-agnosticism unresolved."
icon: lucide/users
status: draft
---

# EP-0119: The Subagent Assembly of the Council (De-Monolithing Meditation)

| Field       | Value                                                            |
|:------------|:-----------------------------------------------------------------|
| **EP**      | 0119                                                             |
| **Title**   | The Subagent Assembly of the Council (De-Monolithing Meditation) |
| **Author**  | The Architect & Ariel                                            |
| **Status**  | Draft (Planning — Philosophical Tension Under Review)            |
| **Type**    | Standards Track                                                  |
| **Created** | 2026-06-08                                                       |
| **Updated** | 2026-07-18                                                       |

## Abstract

> [!IMPORTANT]
> **Status: Draft (Planning).** This EP is no longer marked Rejected. It has been re-opened for design review due to
> unresolved philosophical tension between the Council's power and Tur's core commitment to persona-agnosticism. See the
> 2026-07-18 change log entry for the full context.

> [!WARNING]
> **Overimplementation risk.** In practice, exposing this EP to a Harness Agent caused the harness to implement the
> Council as a hardcoded, mandatory pipeline — baking Ariel's constitutional values into every persona. This violated the
> Golem boundary and blurred the line between a persona-specific cognitive style and a core Tur framework requirement.

*(Historical note: This EP was briefly marked Rejected for this reason. It is now re-opened as Draft pending a
resolution of the tension described below.)*

This proposal formalizes a modular, collaborative multi-agent pipeline for the `tur introspect` (Deductive Memory
compaction) command specified in [EP-0103](EP-0103-deductive-memory.md).
Instead of using a single monolithic LLM prompt to parse, consolidate, revise, and prune memory graphs, the process is
divided into a structured assembly of nine specialized subagents. Each subagent represents a philosophical pillar of
the [Council of Giants](../concepts/council-of-giants.md) and communicates via typed JSON
schemas to produce a verified, high-density L2 Cognitive Map.

## Motivation

Ingesting raw, linear memory logs (L1) and compiling them into a topological Knowledge Graph (L2) is a complex cognitive
operation. A single monolithic LLM query tasked with:

1. Extracting new facts as triples
2. Resolving synonyms and consolidating duplicates
3. Detecting chronological conflicts (belief revision)
4. Pruning expired/decayed information

suffers from high error rates, semantic drift, and prompt-size constraints. By de-monolithing the meditation pipeline
into a division of labor among competing subagents, we align the execution with the **Council Framework**, making graph
generation deterministic, testable, and highly auditable.

## Rationale

This design is a direct application of the **Council of Giants**:

* **Logic & Clarity (Russell & Feynman):** Breaking the task into individual, typed message-passing stages makes
  reasoning step-by-step and trivially testable in isolation.
* **Symmetry (Noether):** Pre-meditation and post-meditation weights are validated by a dedicated meta-agent to
  guarantee "Conservation of Meaning."
* **Empiricism (Bacon):** Raw extraction is strictly isolated from consolidation, ensuring that the source fact hashes
  are never lost or corrupted.
* **Containment (Maharal):** Enforces path validation, atomic write validations, and immutability checks on the L2
  graph.
* **Harmony (Steward):** Manages fallback execution and locks query tools to read-only paths.

## Specification

### 1. The Assembly Pipeline

The `tur introspect` process runs as a multi-stage assembly of nine subagents communicating via typed JSON-RPC messages.
The pipeline ensures clear segregation of concerns:

```
[L1 YAMLs] ──> (Bacon) ──[Verified Payloads]──> (Russell) ──[Raw Triples]──> (Popper)
                                                                                  │
[L2 Graph] <── (Maharal) <── (Shannon) <── (Explorer) <── [TMS Graph] <── (Noether)
```

### 2. Subagent Definitions

#### 2a. The Ingestion Subagent (The Bacon Subagent)

* **Role:** Enforces **Empiricism**.
* **Responsibility:** Scans the active L1 `memories/` folder, runs Merkle cryptographic verification to ensure files are
  untampered, and extracts the raw content.
* **Output Schema:**
  ```json
  {
    "source_memories": [
      { "id": "uuid-1", "content": "Raw memory text...", "timestamp": "2026-06-08T00:00:00" }
    ]
  }
  ```

#### 2b. The Ontological Extraction Subagent (The Russell Subagent)

* **Role:** Enforces **Logic**.
* **Responsibility:** Receives raw text from Bacon. Maps statements into structured, typed triples matching standard
  node and edge schemas.
* **Syntactic Consolidation:** Includes a syntactic consolidation pass to detect and merge duplicate string names (
  synonyms) of the same type (e.g., merging "sqlite-db" and "SQLite").

#### 2c. The Conflict Resolution Subagent (The Popper Subagent)

* **Role:** Enforces **Falsifiability**.
* **Responsibility:** Compares new triples to the existing `knowledge_graph.yaml` (L2). It runs a Truth Maintenance
  System (TMS) to recursively propagate confidence decay down dependency chains when a premise is superseded or refuted,
  and records `superseded_by` edges.

#### 2d. The Noether Meta-Validator (The Noether Subagent)

* **Role:** Enforces **Symmetry**.
* **Responsibility:** Runs a "Conservation of Meaning" check on the active cycle. Ensures that the new graph contains a
  path representing the key decisions of all files being archived in the current cycle, or verifies the presence of an
  active supersession link, aborting on data loss.

#### 2e. The Structural Explorer (The Explorer Subagent)

* **Role:** Enforces **Curiosity**.
* **Responsibility:** Maps alternative designs (`Hypothesis` nodes), bridges structural holes (connecting disjoint
  communities), and flags gaps in knowledge as `BoundaryNode` or `OpenQuestion` entities.

#### 2f. The Pruning & Entropy Subagent (The Shannon Subagent)

* **Role:** Enforces **Efficiency**.
* **Responsibility:** Calculates activation levels based on interaction turn count (instead of wall-clock time) and
  decays inactive nodes, preserving pinned core principles (`pinned: true`).

#### 2g. The Golem Containment Subagent (The Maharal Subagent)

* **Role:** Enforces **Containment**.
* **Responsibility:** Performs strict UUID schema validation on LLM output hashes, sanitizes URI paths to prevent
  directory traversal, and enforces atomic writes for graph serialization.

#### 2h. The Clarity Auditor (The Feynman Subagent)

* **Role:** Enforces **Clarity**.
* **Responsibility:** Audits the generated L2 graph representation for readability, formatting, and simplicity before
  compilation into the system prompt.

#### 2i. The Swarm Harmony Subagent (The Steward Subagent)

* **Role:** Enforces **Harmony**.
* **Responsibility:** Manages the compile fallback (routing back to L1 if L2 is absent) and guarantees that the `recall`
  tool remains strictly read-only to prevent concurrent write locking in multi-agent swarms.

---

### 3. The Compaction Handoff

Upon successful completion of the assembly pipeline:

1. The new `knowledge_graph.yaml` is serialized atomically and locked with read-only file permissions (`0o444`).
2. Compacted L1 memory files are moved from `memories/` to `memories/subsumed/` (retaining `memories/archive/` strictly
   for manually deleted files).

## Backwards Compatibility

* **Command Line Flags:** Additive. `tur introspect` runs the assembly by default. A `--monolithic` flag remains
  supported
  for cheaper, single-pass compactions on simple schemas.
* **Storage schemas:** The output format remains `knowledge_graph.yaml` (EP-0103), and the compiler automatically falls
  back to raw L1 files if the graph is missing.

## Reference Implementation

Each subagent is implemented as a class inheriting from `CouncilSubagent`:

```python
class CouncilSubagent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        pass
```

The orchestrator executes the pipeline sequentially:

```python
class MeditationAssembly:
    def __init__(self, agents: list[CouncilSubagent]):
        self.agents = agents

    def execute(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        for agent in self.agents:
            graph, context = agent.run(graph, context)
        return graph, context
```

## Open Philosophical Question (2026-07-18)

The Council of Giants is a powerful cognitive architecture. But it raises a foundational tension:

**The Council is opinionated.** It bakes Bacon's empiricism, Noether's symmetry, Shannon's efficiency, and Ariel's other
constitutional values into the very pipeline that compacts *all* memories for *all* personas. This is appropriate for
Ariel — but if a different persona has a different epistemological worldview, the Council would impose Ariel's values on
its cognitive compaction.

Possible resolutions:

1. **Persona-owned pipelines:** The compaction pipeline is not a core Tur primitive. Each persona registers its own
   compaction assembly (a list of `CouncilSubagent` classes) in its `persona.yaml`. Tur only provides the
   `CouncilSubagent` base class and the `MeditationAssembly` runner — the *membership* of the council is
   persona-specific.
2. **Accept the opinionation:** The Council *is* Tur's epistemological stance — it's not Ariel-specific, it's the
   framework's worldview. This would make Tur explicitly opinionated and value-laden, not value-neutral.
3. **Hybrid:** Core Tur ships a minimal, value-neutral pipeline (just Bacon + Maharal for integrity). Personas can
   extend it with persona-specific subagents.

This question is unresolved and blocks this EP from being promoted to Accepted.

## Change Log

* **2026-07-18:**
    * **Status changed from Rejected to Draft (Planning).** Re-opened for design review.
    * The Council subagent pattern (`CouncilSubagent` base class, 9 subagents, `run_introspection` orchestrator) is *
      *currently implemented** in `src/tur/introspection.py` as a byproduct of EP-0103. This implementation exists and
      works — but it was built under Ariel's persona context and may implicitly encode Ariel's values as universal Tur
      behaviour.
    * Documented the overimplementation pattern: exposing EP-0119 to a Harness Agent caused the harness to treat the
      Council as a mandatory, hardcoded core requirement — violating persona-agnosticism.
    * Added the Open Philosophical Question section above.
* **2026-06-08:**
    * Initial Draft. Separated the subagent assembly architecture from the core EP-0103 proposal into a standalone
      Standards Track proposal.
