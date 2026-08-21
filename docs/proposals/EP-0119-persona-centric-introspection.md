---
title: "EP-0119: Persona-Centric Introspection Architecture"
description: "Formalizes a collaborative, multi-agent pipeline for persona-driven deductive memory compaction. Status: Accepted — Persona-Centric Introspection Architecture."
icon: lucide/users
status: accepted
---

# EP-0119: Persona-Centric Introspection Architecture

| Field       | Value                                                |
|:------------|:-----------------------------------------------------|
| **EP**      | 0119                                                 |
| **Title**   | Persona-Centric Introspection Architecture           |
| **Author**  | The Architect & Ariel                                |
| **Status**  | Accepted                                             |
| **Type**    | Standards Track                                      |
| **Created** | 2026-06-08                                           |
| **Updated** | 2026-08-18                                           |

## Abstract

> [!IMPORTANT]
> **Status: Accepted.** This EP has been accepted following resolution of the philosophical tension regarding persona-agnosticism.
> Introspection is formalized as a persona-centric capability where the execution strategy (single prompt, prompt chain, or multi-subagent assembly) is owned and configured by the persona (`persona.yaml`).


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

#### 2b. The Ontological Extraction Subagent (The Russell Subagent / `OntologyExtractor`)

* **Role:** Enforces **Logic & Ontological Structure**.
* **Responsibility:** Receives raw text from Bacon/L1 storage. Maps statements into structured, typed triples matching standard node and edge schemas.
* **Extraction Principles & Guidelines:**
  - **Canonicalization & Disambiguation:** Resolve synonyms and merges against existing L2 nodes to avoid graph fragmentation.
  - **Identifier Conventions:** Use concise, lowercase kebab-case identifiers (`isolated-workspace-resolution`, `merkle-state-integrity`).
  - **Attribution (Noether Tracing):** Every node derived from an input memory MUST list the corresponding memory ID in its `sources` array to maintain Merkle auditability.
* **Categorical Node Taxonomy:**
  - `Concept`: Fundamental domain entities and core abstract ideas.
  - `Decision`: Architectural choices and design commitments.
  - `Constraint`: Boundary conditions, invariants, and negative rules (*"MUST NOT..."*).
  - `Insight`: Lessons learned, deductions, and synthesized principles.
  - `Fact`: Objective empirical states and verified observations.
  - `Dependency`: Upstream prerequisites or structural couplings.
  - `Hypothesis`: Active conjectures or experiments under test.
  - `BoundaryNode` / `OpenQuestion`: Perimeter definitions or unresolved inquiries.
* **Relational Edge Signatures:**
  - `refines`: Specializes another node of the SAME type (e.g., Specific Decision -> Base Decision).
  - `contradicts`: Marks mutually exclusive claims or competing hypotheses.
  - `precedes`: Indicates causal or temporal ordering between decisions or facts.
  - `depends_on`: Explicit prerequisite dependency where node A requires node B.
  - `competes_with`, `analogy_of`, `superseded_by`, `refuted_by`: Structural graph relations.
* **Delegation Integration:** Standardized under the pure-function delegation framework in [EP-0124](EP-0124-terrain-isolation-and-workspace-resolution.md).

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

## Resolved Architectural Decision (2026-08-18)

The foundational tension between Council opinionation and persona-agnosticism is resolved via **Persona-Centric Introspection**:

1. **Persona-Owned Execution**: Introspection (`introspect`) is fundamentally driven by the persona's own identity, directives, and prompts. The choice of execution engine (monolithic prompt, prompt chain sequence, or multi-subagent pipeline) is configured at the persona level (`persona.yaml`).
2. **Subagents as Opt-In Tooling**: Spawning subagents (such as the Council of Giants pipeline) is an opt-in capability configured per persona during creation, configuration, or administration (via `tur-adm`), rather than a framework-wide mandatory pipeline.
3. **Framework Responsibility**: The core `tur` framework provides the generic introspection runner, OKF Markdown graph persistence, and subagent orchestration abstractions. The persona provides the prompts, reflection criteria, and subagent selection.

## Change Log

* **2026-08-22:**
    * **Ontological Concept Extraction Specification**: Defined rich ontological extraction principles (canonicalization, lowercase kebab-case IDs, Noether attribution in `sources`, categorical node taxonomy, and relational edge signatures).
    * Integrated with the pure-function delegation framework and multi-batch ingestion protocol established in EP-0124.
* **2026-08-18:**
    * **Status changed from Draft to Accepted.**
    * Formalized **Persona-Centric Introspection Architecture**: introspection is configured per persona, allowing monolithic prompts, prompt sequences, or opt-in subagent assemblies (e.g. Council of Giants) as defined in `persona.yaml`.
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

