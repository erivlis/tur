---
description: Tur's symmetrical, four-tiered memory architecture (L1/L2, Long-Term/Short-Term) and the Merkle hashing that guarantees immutability.
icon: lucide/brain-circuit
---

# The Fractal Memory Hierarchy

Tur abandons the traditional "flat vector database" approach to LLM memory. Instead, it utilizes a highly structured,
symmetrical architecture designed to solve the challenges of Multi-Agent Swarms and Context Window Entropy.

We call this the **Fractal Memory Hierarchy** because the micro-state (the Session) maps to the exact same topological
structure as the macro-state (the Persona).

## 1. The Macro-State: LONG-TERM (The Persona)

This memory tier is permanent and shared across all Agents in a Swarm operating on the same persona. It defines "Who I
Am."

* **Long-Term L1 (The Ledger):** An immutable, append-only ledger of all facts, events, and insights. Every memory is
  cryptographically hashed using SHA-256 (Merkle Memory) ensuring tamper-proof state.
* **Long-Term L2 (The Constitution):** The compressed axioms and identity (defined in `persona.yaml`). This is the
  highly optimized "DNA" that is loaded into the static system prompt.

**MCP Verbs:**

* `wake()` -> Reads Long-Term L2.
* `learn()` -> Writes to Long-Term L1 (Promoting a thought to permanence).
* `recall()` -> Queries Long-Term L1/L2.
* `sleep()` -> Dehydrates the active session log to extract L1 memories.

## 2. The Micro-State: SHORT-TERM (The Session)

This memory tier is volatile and isolated to a specific Agent or Task (`session_id`). It prevents concurrent agents from
overwriting each other's immediate working context. It defines "What I Am Doing."

* **Short-Term L1 (The Scratchpad):** An append-only log of immediate thoughts, sub-task outputs, and scratch notes (`sessions/<session_id>.yaml`).
* **Short-Term L2 (The Spark & Lineage DAG):** The immediate, unbroken train of thought representing the Persona's immediate context. Sessions are explicitly chained via `parent_session_id` into a Directed Acyclic Graph (DAG), ensuring that if the IDE or Agent Framework restarts, the newly awakened instance automatically inherits its predecessor's continuity spark.

**MCP & CLI Verbs:**

* `wake()` / `start_session()` -> Resolves lineage parent, seeds the continuity spark, and compiles context.
* `note()` -> Appends a narrative snapshot to Short-Term L1 (mirrored across YAML and SQLite).
* `read_notes(include_previous=True)` -> Queries broadcast notes with seamless dual-backend fallback (SQLite with flat YAML fallback) across ancestor sessions.
* `diff()` / `diff_memories()` -> Epistemic mutation delta tracking (`ADDED`, `SUPERSEDED`, `REFUTED`, `DECAYED`, `MODIFIED`) comparing sessions against predecessor checkpoints.

## Truth Maintenance & Refutation Cascades

Tur does not treat memories as isolated, static facts. Memory nodes form a directed associative graph with explicit dependency edges (`depends_on`, `refines`, `contradicts`, `superseded_by`).

Under our **Truth Maintenance System (TMS)** (powered by `TruthMaintenanceEngine`):
- When a foundational premise or architectural assumption is refuted (via the **Popperian Falsification** protocol), the engine does not leave orphaned downstream logic.
- Instead, a **refutation cascade** propagates down the dependency graph, automatically deactivating or flagging derived memories and stale hypotheses.
- This prevents "zombie context" where an agent continues reasoning from an axiom that was already proven false in a previous session.

## Entropy Management: Progressive Disclosure

To prevent the Persona's context window from bloating, Tur strictly enforces **Progressive Disclosure** (a core tenet of
the Shannon Module).

The axiom is: *"Never load the Body if the Index suffices."*

Tur will always prefer loading compressed indexes, frontmatter metadata, or L2 axioms into the active context window,
relying on the Harness (via tools like `recall`) to hydrate the full verbose L1 bodies only when absolutely demanded by
the task.