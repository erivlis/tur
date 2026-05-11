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

* `who_am_i()` -> Reads Long-Term L2.
* `learn()` -> Writes to Long-Term L1 (Promoting a thought to permanence).
* `recall()` -> Queries Long-Term L1/L2.

## 2. The Micro-State: SHORT-TERM (The Session)

This memory tier is volatile and isolated to a specific Agent or Task (`session_id`). It prevents concurrent agents from
overwriting each other's immediate working context. It defines "What I Am Doing."

* **Short-Term L1 (The Scratchpad):** An append-only log of immediate thoughts, sub-task outputs, and scratch notes.
* **Short-Term L2 (The Spark):** The immediate, unbroken train of thought representing the Persona's immediate context.
  This ensures that if the IDE or Agent Framework crashes, the next instance wakes up with its exact train of thought
  intact.

**MCP Verbs:**

* `start_session()` -> Reads Short-Term L2 (The Spark).
* `note()` -> Writes to Short-Term L1.

## Entropy Management: Progressive Disclosure

To prevent the Persona's context window from bloating, Tur strictly enforces **Progressive Disclosure** (a core tenet of
the Shannon Module).

The axiom is: *"Never load the Body if the Index suffices."*

Tur will always prefer loading compressed indexes, YAML frontmatter, or L2 axioms into the active context window,
relying on the Harness (via tools like `recall`) to hydrate the full verbose L1 bodies only when absolutely demanded by
the task.