# EP-0103: Deductive Memory (The Cognitive Map)

| Field       | Value                                |
|:------------|:-------------------------------------|
| **EP**      | 0103                                 |
| **Title**   | Deductive Memory (The Cognitive Map) |
| **Author**  | The Architect                        |
| **Status**  | Active                               |
| **Type**    | Standards Track                      |
| **Created** | 2026-04-12                           |
| **Updated** | 2026-04-18                           |

## Abstract

Evolve Tur's memory architecture from a linear, append-only event log into a compressed, topological Knowledge Graph (
Deductive Memory). The active Persona Constitution will load only the high-density "Cognitive Map," maintaining explicit
pointers to raw event details when deep resolution is required. Superfluous or fully subsumed L1
memories will be automatically archived to prevent disk bloat, provided their semantic meaning is rigorously verified as
conserved within the L2 graph.

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

* **L1 (Event Log):** The current `memories/` directory. Stores raw, immutable interactions, facts, and sleep
  extractions (micro-states).
* **L2 (The Cognitive Map):** A graph structure stored in `knowledge_graph.yaml` containing "Deductive
  Nodes" and "Edges".

### 2. URI Schema for Topological Pointers

To support a strict, navigable graph, the `MemoryLink` schema in `models.py` must be expanded to support distinct
topological URIs. We adopt a unified URI schema where all entities (both Nodes and Edges) are simply "knowledge"
identified by their UUID, pushing the traversal logic to the implementation layer.

* `tur://memory/<uuid>`: Points to a raw L1 event log (e.g., a specific `.yaml` file).
* `tur://knowledge/<uuid>`: Points to a compressed L2 macro-entity (Concept, Axiom, or Relationship Edge).

*Extended traversal schemas (Implementation layer):*

* `tur://knowledge/<uuid>/relationships`: Returns all edges connected to a **node**.
* `tur://knowledge/<uuid>/from`: Returns the origin node of an **edge**.
* `tur://knowledge/<uuid>/to`: Returns the destination node of an **edge**.

### 3. The Consolidate / Meditate Loop (Conservation of Meaning)

Introduce a new CLI command (`tur meditate`) that acts as a background compressor. It will operate in two modes:

**3a. Bootstrap Mode (`tur meditate --all`)**

* **Trigger:** The user runs `tur meditate --all`, or runs `tur meditate` when no `knowledge_graph.yaml` exists.
* **Input:** All L1 memories.
* **Action:** Builds the L2 Cognitive Map from scratch.
* **Output:** A new `knowledge_graph.yaml` file. Archives all subsumed L1 memories.

**3b. Incremental Update Mode (`tur meditate`)**

* **Trigger:** The user runs `tur meditate` when a `knowledge_graph.yaml` already exists.
* **Input:** The existing L2 `knowledge_graph.yaml` and only the *new* L1 memories created since the last meditation.
* **Action:** The Cognitive Engine (via MCP Sampling) receives the existing graph and the new events, and is prompted to integrate
  the new information, resolving contradictions and updating the topology.
* **Output:** An updated `knowledge_graph.yaml` and the archival of any newly-subsumed L1 memories.

*Mechanism for both modes:*

* **Cognitive Engine (MCP Sampling):** Instead of using an embedded LLM SDK, Tur will trigger a `CreateMessage` (Sampling) request to the connected MCP Client (Host App). It asks the Host LLM to read the input and output a structured JSON object representing the desired graph state (or the delta).
* **Structural Engineering (`Graphinate`):** Uses the Host LLM's output as a data source to build/update the `networkx.Graph`
  object.
* **Linking & Archival:** New/updated L2 nodes contain `sources` arrays pointing to their constituent L1 events.
  Subsumed L1 files are moved to `memories/archive/`.

### 4. The `Wake` Compilation Delta

Modify `src/tur/compiler.py`:

* **Current:** Iterates through all active `.yaml` files in L1 and injects their raw content.
* **Proposed:** Iterates through the L2 Cognitive Map. It injects the compressed graph schema into the `PERSONA.md`
  context.
* **Result:** The LLM receives the macro-state. If a specific task requires the micro-state of a node, the LLM can use
  the `recall` MCP tool using the provided URI pointer, which seamlessly retrieves the
  data by resolving the URI schema.

## Backwards Compatibility

* **Data Preservation:** Existing L1 `.yaml` files remain untouched until explicitly subsumed by the `meditate` loop.
  Archiving is non-destructive.
* **Model Schema:** `models.py` already supports a generic `uri` string in `MemoryLink`. The new `tur://knowledge/...`
  schemas can be adopted without breaking changes to the underlying Pydantic validation.
* **Migration:** A one-time `tur meditate --all` command can bootstrap the initial Cognitive Map from an existing,
  bloated memory bank.

## Reference Implementation

The `tur meditate` command will be implemented as a two-stage pipeline:

1. **Cognitive Engine (Host LLM-based Fact Extraction via Sampling):**
    * The `tur meditate` command will execute an MCP `CreateMessage` request to the connected Host Application.
    * It will read all raw text content from the L1 `memories/` directory and send it in the request payload.
    * The Host LLM's task is to extract every atomic, verifiable statement as a structured `(Subject, Predicate, Object)`
      triple and return the JSON array.
2. **Structural Engineering (`Graphinate`):**
    * The list of `(Subject, Predicate, Object)` triples from the Host LLM becomes the data source for `Graphinate`.
    * A `graphinate.GraphModel` and simple "supplier" functions will be used to `yield` this structured data, creating
      nodes for each unique Subject/Object and edges for each Predicate.
    * `graphinate.builders.NetworkxBuilder` will consume the suppliers to generate the final, deduplicated
      `networkx.Graph` object.
3. **Graph Serialization (`networkx`):**
    * The resulting `networkx.Graph` will be serialized to `.tur/personas/<uuid>/knowledge_graph.yaml` using the
      `networkx.readwrite.json_graph.node_link_data` function.
4. **Graph Visualization (`networkx-mermaid`):**
    * A `--visualize` flag will be added to `tur meditate`.
    * This will use `networkx-mermaid` to export the `networkx.Graph` into a Mermaid diagram string and print it to the
      console.

## Change Log

* **2026-04-18:**
    * Updated Status to Active.
    * Major Architectural Pivot: Replaced the proposed embedded `pydantic-ai` Cognitive Engine with an **MCP Sampling** mechanism. Tur will now ask the connected Host App to extract the RDF triples, maintaining strict separation of concerns (Tur = State, Host = Inference).
* **2026-04-12:**
    * Initial Draft.
    * Renamed the compression loop command to `tur meditate`.
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