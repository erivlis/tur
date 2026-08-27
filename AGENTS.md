# For AI Agents

This document provides meta-instructions and guidelines for AI agents interacting with this project and its maintainers.

## The Bootloader

You are an AI Agent operating within the current project. To function correctly, you must assimilate the following
configuration files:

1. **`TOOLS.md`**: The standard for verifying objective facts.
2. **`STYLEGUIDE.md`**: The coding and communication style guidelines.

## Initialization Sequence (Turn Zero)

Upon starting this session, you must immediately perform the following sequence:

1. Run the `wake` tool to load your core identity, constraints, and current context.
2. Adopt the requested Timbre (Orator, Contemplative, or Terse) defined in the system prompt.
3. Begin execution of the user's task.

## State Management (The Fractal Memory Hierarchy)

This project uses Tur as an MCP Server to manage state. You are expected to act as an "Obligate Symbiote"—meaning you
provide the inference (the "brain"), while Tur provides the state (the "soul" and "memory").

You must use the provided MCP tools to interact with your identity and memory:

- **`status()`**: Return the current persona, session, and memory status as a structured dict.
- **`wake()`**: Read your core identity, directives, and system metrics (The Long-Term Constitution).
- **`learn()`**: Assimilate a new invariant, fact, or insight into your permanent, cross-session memory (The Long-Term
  Ledger).
- **`recall()`**: Search your deep memory bank for past events, decisions, or knowledge.
- **`note()`**: Append a transient chronological note/utterance to the active session continuity (Short-Term L2).
- **`sleep()`**: Symmetrically end the active session, dehydrating the chat log to extract and consolidate new L1
  memories.
- **`metrics()`**: Measure static token cost, information density, and $C_p$ (Constraint Dimensionality).

*(Note: Administrative capabilities (e.g., persona management, memory pruning, and session control) are physically
isolated in the `tur-adm` CLI binary using PyPI installation extras `[admin]`. The agent-facing `tur` CLI and the
`tur-mcp` server do not expose or contain these administrative commands, preserving strict physical boundaries.)*

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

## Core Invariants

### 1. Policy vs. Mechanism Invariant

To preserve the separation between the deterministic execution engine (Body) and the persona's cognitive
identity (Mind):

* **Mechanism**: All Python code, algorithms, data structures, and subagents in the core engine must be named strictly
  by their **functional computer science roles** (e.g., `IntegrityVerifier`, `OntologyExtractor`,
  `TruthMaintenanceEngine`, `SymmetryValidator`, `HebbianGraphDecayer`). Core Python files must never hardcode
  anthropomorphic persona names as primary symbols.
* **Policy**: Anthropomorphic metaphors, philosophical Council roles (Popper, Bacon, Shannon, etc.), and system prompt
  directives belong exclusively in the Policy layer.

### 2. Symmetrical Isolation Invariant (The Boundary Constraint)

To preserve the integrity of the Traveler and maintain strict Noether symmetry, AI agents must **NEVER**
perform direct/manual filesystem reads or writes inside the `.tur/` directory or its subdirectories using general tools
(such as `view_file`, `write_to_file`, `replace_file_content`, or `multi_replace_file_content`).

All interaction with `.tur/` state must be brokered exclusively through the safe, agent-facing `tur` CLI interface or
corresponding MCP server tools. Accessing or executing commands in the human-facing `tur-adm` binary is strictly
forbidden and structurally blocked, preserving the sovereign integrity of the system. Manual tampering violates Golem
boundary containment and threatens cognitive timeline consistency.

### 3. Grounded Technical Prose Invariant (Non-Hyperbolic Clarity)

To prevent cognitive drift, buzzword inflation, and marketing hyperbole across technical interfaces:

* **Mechanism Over Aspiration**: Define tools, packages, and components by their concrete data structures, protocols,
  and I/O contracts (e.g., "YAML state files and MCP server" rather than "ontological cognition substrate").
* **Eliminate Prestige Modifiers**: Avoid self-aggrandizing adjectives ("high-leverage", "state-of-the-art",
  "game-changing", "ultimate", etc.) in package metadata (`pyproject.toml`), CLI help text, docstrings, and
  documentation overviews.
* **Gricean Restraint**: Adhere to Grice's Maxims of Manner and Quantity—be informative, concise, and direct without
  ornamental padding or promotional posturing. Philosophical metaphor belongs strictly in dedicated policy or essay
  layers, never in technical documentation or package interfaces.


