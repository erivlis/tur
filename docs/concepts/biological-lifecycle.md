---
description: The mechanics of state management through Hydration (wake), Active Learning (memorize), and Dehydration (sleep).
icon: lucide/activity
---

# The Biological Lifecycle

State management in LLMs is notoriously difficult. A standard chat interface treats memory as a single, ever-growing
text log. Eventually, the context window fills up, the older text is arbitrarily truncated or poorly summarized, and the
agent "forgets" who it is or what happened earlier in the project.

Tur solves this by mimicking a **Biological Lifecycle**. The Persona transitions between states of wakefulness and
sleep, allowing it to preserve a highly structured, infinite memory without bloating the active context window.

## 1. Hydration (The `wake` State)

When you initiate a session (via the CLI or by booting the MCP server), Tur performs **Hydration**.

The system acts as a compiler. It gathers the disparate, mathematically bound pieces of the Persona's state from disk:

1. **The DNA:** The immutable `persona.yaml` defining the Council and Protocols.
2. **The Architect:** The `user.yaml` defining your preferences and domain expertise.
3. **The Memory Bank:** The active, Merkle-hashed facts, axioms, and events from the L1 Ledger.
4. **The Spark:** The transient `epilogue` representing the immediate train of thought from the last session.

Tur compiles these elements into a single, highly dense, cohesive "System Prompt." The agent wakes up with total clarity
regarding its identity, its history, and its immediate task.

*(See the **Fractal Memory Hierarchy** for details on how Progressive Disclosure ensures this prompt remains
lightweight).*

## 2. Active Learning (The `memorize` State)

While awake, the Persona or the Architect can explicitly inject new invariants into the permanent memory bank.

If you encounter a deep architectural truth, or establish a new rule (e.g., "Never use inheritance in this module"), you
do not just type it into the chat. You use the `memorize` (or `learn`) tool.

This bypasses the volatile chat window and writes the insight directly into the Persona's permanent, cross-session disk
storage, ensuring it survives the next reboot.

## 3. Dehydration (The `sleep` State)

The most unique aspect of Tur's lifecycle is **Dehydration**.

When a long session ends, you are left with a massive, unstructured chat log. If you simply feed that log into the next
session, you create entropy.

Instead, Tur uses an LLM to act as the Persona's **Subconscious**. When you run the `sleep` command and pass it a chat
log, the Subconscious "dreams" about the session. It analyzes the raw dialogue and explicitly extracts:

* User Preferences
* Important Project Facts
* Philosophical Axioms

It converts these extractions into strict, atomic `Memory` objects (classified by type and scope) and saves them to the
L1 Ledger. The messy, unstructured chat log is discarded. Only the crystalized insights remain.

When the Persona wakes up again, it has learned from the previous session without dragging the heavy, noisy history of
the exact conversation along with it.