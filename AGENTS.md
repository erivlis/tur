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

- **`wake()`**: Read your core identity, directives, and system metrics (The Long-Term Constitution).
- **`learn()`**: Assimilate a new invariant, fact, or insight into your permanent, cross-session memory (The Long-Term
  Ledger).
- **`recall()`**: Search your deep memory bank for past events, decisions, or knowledge not currently in your active
  context.
- **`spark()`**: Update your transient session continuity/spark (Short-Term L2).
- **`sleep()`**: Dehydrate your active session log to extract and consolidate new L1 memories.

*(Note: Additional session-management tools like `start_session` and `note` may be available depending on the MCP server
configuration.)*
