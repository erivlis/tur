---
title: "EP-0108: The Fractal Memory Hierarchy (The Spark Protocol)"
description: "Defines the symmetrical four-tiered Fractal Memory Hierarchy and the Spark Protocol for short-term session memory."
icon: lucide/zap
status: final
---

# EP-0108: The Fractal Memory Hierarchy (The Spark Protocol)

| Field       | Value                                             |
|:------------|:--------------------------------------------------|
| **EP**      | 0108                                              |
| **Title**   | The Fractal Memory Hierarchy (The Spark Protocol) |
| **Author**  | The Architect, Ariel                              |
| **Status**  | Final                                             |
| **Type**    | Standards Track                                   |
| **Created** | 2026-04-18                                        |
| **Updated** | 2026-06-08                                        |

## Abstract

This proposal formally defines the **Fractal Memory Hierarchy**, a symmetrical, four-tiered architecture that separates a Persona's shared, permanent **Long-Term Memory** from its isolated, transient **Short-Term Memory**. It deprecates the single-agent global "Epilogue" in favor of session-bound notes and spark context. This architecture provides a robust solution for Swarm Concurrency by giving each agent its own private cognitive workspace while allowing them to contribute to a shared, collective consciousness.

## Motivation

Our previous designs for short-term context (the "Epilogue" and the initial "Spark") were flawed because they were singletons. If multiple agents (e.g., Claude and Gemini) operated on the same Persona, they would overwrite each other's train of thought, leading to timeline collisions and cognitive desync.

To solve this, we map the micro-state (the Session) to the exact same topological structure as the macro-state (the Persona), creating a perfectly symmetrical, fractal memory system.

## Rationale (The Council Framework)

*   **Noether (Symmetry):** The architecture is perfectly balanced. Short-Term Memory (the Session) has the same L1/L2 structure as Long-Term Memory (the Persona).
*   **The Golem (Containment):** Each agent in a Swarm gets its own isolated Short-Term memory stream (`sessions/<session_id>/`). Senders cannot corrupt another agent's working context without explicit directed signals (EP-0118).
*   **The Explorer (Structural Novelty):** An agent can maintain private scratch notes (`note`), consult its core identity (`wake`), check active telemetry/status (`status`, `telemetry`), and permanently alter the shared reality (`learn`).

## Specification: The Fractal Memory Hierarchy

### 1. The Macro-State: LONG-TERM (The Persona)

*Shared across all Agents in the Swarm. Defines "Who I Am."*

*   **Long-Term L1 (The Ledger):** `memories/[timestamp]_[type]_[hash].yaml` (The immutable, Merkle-hashed history of all facts, insights, preferences, axioms, and events).
*   **Long-Term L2 (The Constitution):** Compiled prompt template + `persona.yaml` + universal memories.
*   **The Verbs:**
    *   `wake()` -> Reads Long-Term L2.
    *   `learn()` -> Writes to Long-Term L1 (Promoting a thought to permanence).
    *   `recall()` -> Queries Long-Term L1/L2.

### 2. The Micro-State: SHORT-TERM (The Session)

*Isolated to a specific Session (`session_id`). Defines "What I Am Doing."*

*   **Short-Term L1 (The Scratchpad):** An append-only log of immediate thoughts/actions tracked as serialized YAML records (`sessions/<session_id>/notes.yaml`).
*   **Short-Term L2 (The Spark):** The latest session notes and broadcast events dynamically loaded into the active session context.
*   **The Verbs:**
    *   `wake(session_id)` -> Reads Short-Term L2 (The Spark context).
    *   `note(content)` -> Writes to Short-Term L1.

### 3. The New MCP API

The Ontological Porcelain API matches this geometry:

*   **`wake(session_id: str | None)`**: Reads the combined Long-Term L2 (Persona/Identity) and Short-Term L2 (Spark/Task Context).
*   **`note(content: str)`**: Writes an ephemeral thought to the Short-Term L1 scratchpad.
*   **`learn(content: str, type: str, scope: str)`**: Promotes a thought to the Long-Term L1 permanent ledger.
*   **`sleep(note: str, log_content: str)`**: Triggers the dreaming parser, merging session scratchpad notes into permanent L1 memory.

## Backwards Compatibility

*   This is a major architectural evolution. It renames and re-scopes the `update_spark` tool proposed earlier to the `note` and `wake` APIs.
*   It introduces session-bound note tracking and deprecates global context files.

## Change Log

*   **2026-06-08:**
    *   Updated status to Final and revised memory specifications to align with the flat-file `notes.yaml` structures and dynamic `wake` compilation active in the codebase.
*   **2026-04-18:**
    *   Initial Draft.
    *   Pivoted from a simple "Spark Protocol" to the "Fractal Memory Hierarchy," defining the symmetrical L1/L2 structure for both Short-Term (Session) and Long-Term (Persona) memory.