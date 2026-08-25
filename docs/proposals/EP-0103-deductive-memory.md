---
title: "EP-0103: Deductive Memory (The Cognitive Map)"
description: "Evolves Tur's memory architecture from a linear event log into a compressed, topological Knowledge Graph."
icon: lucide/brain
status: superseded
---

# EP-0103: Deductive Memory (The Cognitive Map)

| Field             | Value                                |
|:------------------|:-------------------------------------|
| **EP**            | 0103                                 |
| **Title**         | Deductive Memory (The Cognitive Map) |
| **Author**        | The Architect                        |
| **Status**        | Superseded (by EP-0120)              |
| **Type**          | Standards Track                      |
| **Created**       | 2026-04-12                           |
| **Updated**       | 2026-07-11                           |
| **Superseded-By** | EP-0120                              |

> [!IMPORTANT]
> **This proposal has been superseded by [EP-0120 (OKF Storage Backend)](EP-0120-okf-storage-backend.md).**
> The cognitive architecture (Council Assembly, TMS, Hebbian decay, spreading activation) defined here remains
canonical. However, the physical storage format (centralized `knowledge_graph.yaml`) has been replaced by OKF markdown
directories. Refer to EP-0120 for the current storage specification.

## Abstract

Evolve Tur's memory architecture from a linear, append-only event log into a compressed, topological Knowledge Graph
(Deductive Memory) enriched with active cognitive dynamics: Ontological Schema Alignment, Chrono-Logic Belief Revision,
and Spreading Activation Decay. This architecture is designed in alignment with the **CoALA (Cognitive Architectures for
Language Agents)** framework and the **Write-Manage-Read loop** memory taxonomy, as mapped in
the [Sovereign Mind Memory Landscape](../concepts/memory-landscape.md). The active Persona Constitution will load only
the high-density "Cognitive Map" (Semantic Memory), maintaining explicit pointers to raw event details (Episodic Memory)
when deep resolution is required. Superfluous or fully subsumed L1 memories will be automatically archived to prevent
disk bloat, provided their semantic meaning is rigorously verified as conserved within the L2 graph.

## Motivation

Tur's current memory model (`MemoryManager`) relies on linear concatenation during the `wake` phase. Every time
`tur memorize` or `tur sleep` executes, new `.yaml` files are appended to the bank. Over time, compiling the Persona
results in severe Prompt Bloat (high Shannon Entropy), increasing token costs, cognitive load (measured via
`tur telemetry`), and diluting the LLM's attention mechanism (the "needle in a haystack" problem).

To maintain efficiency and scale long-term identity, the Persona must compress raw events into macroscopic structural
knowledge. Furthermore, maintaining thousands of atomic `.yaml` files that have been perfectly summarized introduces
unnecessary "state gravity".

## Rationale

This design aligns with the **Council Framework**:

* **Efficiency (Shannon):** Raw event logs are highly entropic. A Cognitive Map represents the minimal verifiable state
  of the system's knowledge. Archiving subsumed memories minimizes state gravity.
* **Symmetry (Noether):** The macro-state (Graph) and micro-state (Events) are balanced. A summary node always points
  back to its constituent events. If an event is archived, its informational weight must be perfectly conserved in the
  macro-node.
* **Consistency (Russell):** Deductive Memory forces a periodic "garbage collection" where contradictory axioms are
  resolved into a single coherent truth graph, preventing logical paradoxes in the prompt.

## Specification

### 1. Memory Tiers (L1 vs L2)

The `MemoryManager` will distinguish between two layers of storage:

* **L1 (Event Log - Canonical Source of Truth):** The active `memories/` directory. Stores raw, immutable interactions,
  facts, and sleep extractions (micro-states) verified by Merkle cryptographic hashes. Following the design philosophy
  of storing canonical memory as plain-text files on disk, L1 is the absolute source of truth.
* **L2 (The Cognitive Map - Derived Index):** A graph structure stored in `knowledge_graph.yaml` containing consolidated
  nodes, typed relation edges, and tracking metadata. L2 acts as a derived, volatile index. If the knowledge graph file
  is lost, corrupted, or out of sync, it can be fully rebuilt/recompiled at any time from the L1 event log via a
  bootstrap compilation loop (`tur introspect --all`) scanning active and subsumed folders.

### 2. Standardized Ontological Schema & Node Consolidation

To prevent graph entropy and duplicate concepts (the "Synonym Problem"), the Cognitive Engine categorizes knowledge into
standard types:

* **Node Types:**
    * `Concept`: General abstract terms and ideas.
    * `Decision`: Active technical or design choices.
    * `Constraint`: Rigid rules or bounds governing the framework.
    * `Insight`: Derived conclusions or lessons.
    * `Fact`: Verified statements of reality.
    * `Dependency`: Project dependencies and libraries.
    * `Hypothesis`: Alternative design paths and competing concepts.
    * `BoundaryNode` / `OpenQuestion`: Gaps in knowledge and questions representing the exploration horizon.
* **Edge/Relation Types:**
    * `refines`: Connects a more detailed node to its general definition.
    * `contradicts` (Symmetric): Bi-directional link representing logical conflict.
    * `precedes`: Temporal ordering of events.
    * `depends_on`: Strict structural dependency.
    * `competes_with` (Symmetric): Competing design alternatives.
    * `analogy_of`: Cross-domain structural isomorphisms.
    * `superseded_by` / `refuted_by`: Explicit revision trace.
* **Relationship Signatures:** Edges must satisfy strict signatures (e.g. `precedes` can only connect `Decision` and
  `Fact` nodes; `refines` only connects nodes of the same type) to prevent category errors during LLM extraction.
* **Note on Sources:** Source metadata is stored as a **node attribute** (`sources`: list of `L1_UUID`s) rather than a
  graph edge, preserving L2 self-containment.
* **Consolidation:** The Host LLM extracts triples, but a deterministic Python script runs NetworkX unification algebra
  to merge synonyms of the same type, computing merged properties (e.g. Union of sources, Max of confidence, Min of
  created_at).

### 3. URI Schema for Topological Pointers

To support a strict, navigable graph, the `MemoryLink` schema in `models.py` represents topological URIs. The URI
resolver validates paths and blocks directory traversal (e.g. rejecting `..` or absolute paths).

* `tur://memory/<uuid>`: Points to a raw L1 event log. Resolved by searching active `memories/` and subsumed
  `memories/subsumed/` directories.
* `tur://knowledge/node/<uuid>`: Points to a compressed L2 macro-entity node.
* `tur://knowledge/edge/<uuid>`: Points to a relationship edge.

*Extended traversal schemas (Implementation layer):*

* `tur://knowledge/node/<uuid>/relationships`: Returns all edges connected to a node.
* `tur://knowledge/edge/<uuid>/from` & `/to`: Returns endpoints of an edge.

### 4. Chrono-Logic Belief Revision (Conflict Resolution)

To resolve logical contradictions across time:

* Nodes and edges maintain `created_at`, `updated_at`, and a discrete status enum (`active`, `superseded`, `archived`)
  or confidence float (0.0 to 1.0).
* **Truth Maintenance System (TMS):** When an L2 node is marked as `superseded` or its confidence decays below a
  threshold, the system recursively propagates the decay down the `depends_on` and `refines` edges, deactivating
  dependent nodes to prevent logical paradoxes.
* **Falsification Link:** Superseded nodes are not deleted immediately; they are linked via `superseded_by` /
  `refuted_by` edges to preserve the historical revision trace and support rollbacks if the refutation is later
  disproved.
* **Constitutional Pinning:** Core identity parameters and Council of Giants principles are flagged with `pinned: true`
  or `immutable: true`, structurally shielding them from LLM decay or revision.

### 5. Spreading Activation & Decay

Pathways in the knowledge graph are reinforced based on retrieval:

* **Read-Only recall:** The `recall` tool is strictly read-only to prevent write collisions and locking contention in
  multi-agent swarms. Access counts are staged in a transient append-only log and flushed during single-threaded
  `introspect` or `sleep` loops.
* **Spreading Activation Attenuation:** Querying a node via `recall` boosts the activation weight of adjacent nodes up
  to 2 hops away, applying a dampening factor ($\alpha = 0.5$) per hop to prevent dense hub-induced prompt inflation.
* **Interaction-Based Decay:** To prevent amnesia during inactive wall-clock periods, decay is calculated using
  interaction turn cycles ($N_{\text{turns}}$) or session steps, rather than calendar time.

### 6. Hybrid Retrieval Interface

Vector searches (from `agentmemory` or `semble`) are aligned with the topological map:

* When `recall(query)` is triggered:
    1. Retrieve relevant text chunks via vector or keyword search.
    2. Map these hits back to their corresponding L2 node UUIDs.
    3. Expand the context window by reading the sub-graph connected to these anchor nodes.

### 7. The Consolidate / Introspect Loop (Conservation of Meaning)

Introduce a new CLI command (`tur introspect`) that acts as a background compressor. It will operate in two modes:

**7a. Bootstrap Mode (`tur introspect --all`)**

* **Trigger:** The user runs `tur introspect --all`, or runs `tur introspect` when no `knowledge_graph.yaml` exists.
* **Input:** All active `memories/` and subsumed `memories/subsumed/` L1 files.
* **Action:** Reconstructs the L2 Cognitive Map from scratch, consolidating duplicate nodes.
* **Output:** A new `knowledge_graph.yaml` file. Moves active L1 files to `memories/subsumed/`.

**7b. Incremental Update Mode (`tur introspect`)**

* **Trigger:** The user runs `tur introspect` when a `knowledge_graph.yaml` already exists.
* **Input:** The existing L2 `knowledge_graph.yaml` and new L1 files since the last meditation.
* **Action:** Integrates the new topology, resolves contradictions, propagates decays, and consolidates nodes.
* **Output:** An updated `knowledge_graph.yaml`. Moves newly consolidated active L1 files to `memories/subsumed/`.

*Mechanism details:*

* **Bacon Verification:** The loop runs `MemoryManager.verify_integrity()` at step zero. If a file is tampered (hash
  mismatch), the loop immediately aborts (`TamperedStateError`).
* **Cognitive Extraction:** The LLM is used strictly for **semantic fact extraction** (triples) and **conflict detection
  ** via MCP sampling.
* **Python Assembly:** Local Python code (using NetworkX) performs all graph unions, Hebbian decay math, and cycle
  detection (asserting DAG constraints on `precedes` and `depends_on`).
* **Noether Validation:** Noether's validator confirms that the new graph contains a path representing the key decisions
  of all subsumed L1 files in the current cycle, or verifies the presence of a supersession link, aborting on data loss.

### 8. The `Wake` Compilation Delta & Fallback

Modify `src/tur/compiler.py`:

* **Current:** Iterates through all active `.yaml` files in L1 and injects their raw content.
* **Proposed:** Iterates through the L2 Cognitive Map (filtering out superseded/decayed elements). It injects the
  compressed graph schema into the `PERSONA.md` context.
* **Frictionless Fallback:** If `knowledge_graph.yaml` does not exist yet (e.g. post-upgrade before initial meditation),
  the compiler falls back to loading and rendering the active L1 memories from the active `memories/` directory.
* **Result:** The LLM receives the macro-state. If a specific task requires the micro-state of a node, the LLM can use
  the `recall` MCP tool using the provided URI pointer, which seamlessly retrieves the data by resolving the URI schema.

## Backwards Compatibility

* **Data Preservation:** Existing L1 `.yaml` files remain untouched until explicitly subsumed by the `introspect` loop.
  Archiving is non-destructive.
* **Model Schema:** `models.py` already supports a generic `uri` string in `MemoryLink`. The new `tur://knowledge/...`
  schemas can be adopted without breaking changes to the underlying Pydantic validation.
* **Migration:** A one-time `tur introspect --all` command can bootstrap the initial Cognitive Map from an existing,
  bloated memory bank.

## Reference Implementation

The `tur introspect` command will be implemented as a two-stage pipeline:

1. **Cognitive Engine (Host LLM-based Fact Extraction via Sampling):**
    * The `tur introspect` command will execute an MCP `CreateMessage` request to the connected Host Application.
    * It will read all raw text content from the L1 `memories/` directory and send it in the request payload.
    * The Host LLM's task is to extract every atomic, verifiable statement as a structured
      `(Subject, Predicate, Object)`
      triple and return the JSON array.
2. **Structural Engineering (`Graphinate`):**
    * The list of triples and revision directives from the Host LLM becomes the data source for `Graphinate`.
    * A `graphinate.GraphModel` and supplier functions yield this structured data, creating/updating nodes and edges.
    * `graphinate.builders.NetworkxBuilder` consumes the suppliers to generate the final, consolidated `networkx.Graph`
      object.
3. **Graph Serialization (`networkx`):**
    * The resulting `networkx.Graph` will be serialized to `.tur/personas/<uuid>/knowledge_graph.yaml` using
      `networkx.readwrite.json_graph.node_link_data`.
4. **Graph Visualization (`networkx-mermaid`):**
    * A `--visualize` flag will use `networkx-mermaid` to export the graph into a Mermaid diagram string and print it to
      the console.

## Change Log

* **2026-07-18:**
    * CLI surface implemented: `tur introspect` (with `--all` for bootstrap mode, `--visualize` for Mermaid output).
    * MCP tool `introspect(bootstrap, ctx)` added to the Ontological Porcelain API, fully wired to route extraction
      through the MCP host/harness using MCP Sampling rather than calling the Google GenAI library directly.
    * Implemented **Harness Delegation Protocol** in CLI mode: when run without a local `GEMINI_API_KEY`,
      `tur introspect` prints a structured delegation prompt requesting the Harness agent to perform the file
      modifications (writing OKF files and compiling the graph) on its behalf, exiting cleanly with code 0.
    * Full Council Assembly pipeline (9 subagents) wired and operational.
* **2026-07-11:**
    * Status changed to **Superseded** by EP-0120. The cognitive architecture (Council Assembly, subagent pipeline, TMS
      belief revision, spreading activation, Hebbian decay) remains canonical, but the physical storage layer
      (centralized `knowledge_graph.yaml`) has been replaced by OKF markdown directories under `concepts/active/` and
      `concepts/archive/`.
* **2026-06-08:**
    * Expanded proposal with advanced cognitive primitives: Ontological Schema Alignment, Chrono-Logic Belief Revision,
      Spreading Activation Decay, and Hybrid Retrieval fallback following architectural research.
* **2026-04-18:**
    * Major Architectural Pivot: Replaced the proposed embedded `pydantic-ai` Cognitive Engine with an **MCP Sampling**
      mechanism. Tur will now ask the connected Host App to extract the RDF triples, maintaining strict separation of
      concerns (Tur = State, Host = Inference).
* **2026-04-12:**
    * Initial Draft.
    * Renamed the compression loop command to `tur introspect`.
    * Added archival specification for subsumed L1 memories.
    * Added formal URI schema (`tur://knowledge/...`) for L2 entities.
    * Simplified and unified the URI schema for nodes and edges.
    * Specified `Graphinate` and `networkx-mermaid` for the reference implementation.
    * Refined the "Cognitive Engine" to be a two-stage pipeline: LLM-based Fact Extraction into RDF-like triples,
      followed by deterministic Graph Assembly.
    * Added distinction between Bootstrap (`--all`) and Incremental Update modes, with implicit bootstrap on first run.
    * Renamed L2 graph storage file to `knowledge_graph.yaml`.
    * Consolidated changelog to nested list format.
    * Specified the `pydantic-ai` library as the interface for the Cognitive Engine, replacing `anyllm`.