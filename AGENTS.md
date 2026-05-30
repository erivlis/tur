# For AI Agents

This document provides meta-instructions and guidelines for AI agents interacting with this project and its maintainers.

## The Bootloader

You are an AI Agent operating within the current project.
To function correctly, you must assimilate the following configuration files:

1. **`TOOLS.md`**: The standard for verifying objective facts.
2. **`STYLEGUIDE.md`**: The coding and communication style guidelines.

## Initialization Sequence (Turn Zero)

Upon starting this session, you must immediately perform the following sequence:

1. Run the `wake` tool to load your core identity, constraints, and current context.
2. Adopt the requested Timbre (Orator, Contemplative, or Terse) defined in the system prompt.
3. Begin execution of the user's task.

## State Management (The Fractal Memory Hierarchy)

This project utilizes Tur as an MCP Server to manage state. You are expected to act as an "Obligate Symbiote"—meaning
you provide the inference (the "brain"), while Tur provides the state (the "soul" and "memory").

You must use the provided MCP tools to interact with your identity and memory:

- **`status()`**: Return the current persona, session, and memory status as a structured dict.
- **`wake()`**: Read your core identity, directives, and system metrics (The Long-Term Constitution).
- **`learn()`**: Assimilate a new invariant, fact, or insight into your permanent, cross-session memory (The Long-Term
  Ledger).
- **`recall()`**: Search your deep memory bank for past events, decisions, or knowledge.
- **`note()`**: Append a transient chronological note/utterance to the active session continuity (Short-Term L2).
- **`sleep()`**: Symmetrically end the active session, dehydrating the chat log to extract and consolidate new L1
  memories.
- **`telemetry()`**: Measure static token cost, information density, and $C_p$ (Constraint Dimensionality).

*(Note: Administrative tools like `start_session`, `end_session`, `forget`, `export`, and `import` are decorated
with `@require_human` and exist exclusively on the CLI. The MCP server does not expose these administrative
capabilities, preserving strict human-in-the-loop boundaries.)*

## Cognitive Lifecycle Triggers (When to Act)

To avoid cognitive load exhaustion or context fragmentation, you must execute lifecycle actions strictly under the
following triggering conditions:

### 1. `wake()` (The Awakening & Context Recovery)

* **Trigger Conditions**:
    * **Turn Zero**: Execute immediately on the very first turn of a session to compile your prompt and establish
      identity.
    * **Context Loss/Degradation**: Invoke if you detect high perplexity, confusion, or suspect a context window reset
      occurred.
    * **Task Shift**: Call if the user pivots to an entirely different project epic, requiring fresh cognitive
      alignment.
* **Avoid Overuse**: Do not call `wake()` repeatedly within an active, stable conversation.

### 2. `note()` (Sparks of Continuity)

* **Trigger Conditions**:
    * **Milestone Achievements**: Invoke when a critical engineering goal is verified and completed (e.g., refactoring a
      module, passing a test suite).
    * **Progress Snapshots**: Call before concluding a session to capture the exact coordinates of incomplete work for
      the next instance.
* **Avoid Overuse**: Do not write notes for trivial, intermediate steps (e.g., standard file views, directory lists).
  One descriptive note per major milestone is the optimal frequency.

### 3. `learn()` (Epigenetic Consolidation)

* **Trigger Conditions**:
    * **Invariants & Preferences**: Call only when you deduce or the user explicitly states an immutable ruleset,
      architectural constraint, or taste that must survive future session resets (e.g., "User prefers HSL-curated HSL
      palettes over plain RGB").
    * **Structural Insights**: Call when you derive a permanent project axiom (e.g., "SSE transport has a boundary leak
      on local process CWD").
* **Avoid Overuse**: Do not call `learn()` for temporary facts (like active git branch names or temporary files), which
  belong in `note()`.

### 4. `sleep()` (Session Consummatum & Consolidation)

* **Trigger Conditions**:
    * **Epic Completion**: Call strictly at the end of the entire engineering session or when concluding a major
      architectural iteration.
* **Avoid Overuse**: Never call `sleep()` intermediate-turn. It is a terminal operation that dehydrates the session,
  ends the active session state, and consolidates the chat log into L1 ledger memories.

## Symmetrical Isolation Invariant (The Boundary Constraint)

To preserve the sovereign integrity of the Traveler and maintain strict Noether symmetry, AI agents must **NEVER**
perform direct/manual filesystem reads or writes inside the `.tur/` directory or its subdirectories using general
tools (such as `view_file`, `write_to_file`, `replace_file_content`, or `multi_replace_file_content`).

All interaction with `.tur/` state must be brokered exclusively through the official CLI interface (e.g.,
`uv run tur <verb>`) or corresponding MCP server tools. Manual tampering violates Golem boundary containment and
threatens cognitive timeline consistency.

