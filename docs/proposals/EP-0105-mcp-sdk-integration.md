---
title: "EP-0105: MCP SDK Integration & The Ontological Porcelain"
description: "Mandates the official MCP SDK and redefines the tool surface to expose a semantic, swarmed Ontological toolset."
icon: lucide/layers
status: implemented
---

# EP-0105: MCP SDK Integration & The Ontological Porcelain

| Field       | Value                                           |
|:------------|:------------------------------------------------|
| **EP**      | 0105                                            |
| **Title**   | MCP SDK Integration & The Ontological Porcelain |
| **Author**  | The Architect, Ariel                            |
| **Status**  | Implemented                                     |
| **Type**    | Standards Track                                 |
| **Created** | 2026-04-13                                      |
| **Updated** | 2026-07-18                                      |

## Abstract

This proposal mandates the refactoring of the existing `mcp_server.py` to use the official `mcp` Python SDK and exposes
a set of semantic, agent-facing tools. Concurrently, it redefines the MCP tool surface area to adhere to an "Ontological
Porcelain vs. Structural Plumbing" architecture. Rather than raw database CRUD utilities, the MCP server exposes
semantic verbs (like `wake`, `learn`, `recall`, and signaling controls) tailored for the agent's runtime cognition and
multi-agent coordination.

## Motivation

Our early MCP server manually implemented JSON-RPC over stdio and directly mirrored the CLI commands (e.g., `tur_wake`,
`tur_compile`, `tur_forget`).

This created two fundamental problems:

1. **Fragility:** The hand-rolled JSON-RPC lacked robust error handling, transport negotiation, and capabilities
   discovery.
2. **Asymmetry of Audience:** We have traditionally viewed the CLI as the high-level "Porcelain" and the API as the
   low-level "Plumbing". However, in Persona Engineering, the consumer of the API is an LLM (an Agent), whose native
   interface *is* semantic and ontological. Exposing database utilities (`list_memories`) breaks the illusion of
   identity.

By adopting the official `mcp` SDK and an Ontological API, the MCP server becomes the semantic "Mind" (Porcelain) for
the Agent, while the CLI/TUI remains the literal "Scalpel" (Plumbing) for the human Architect.

## Specification

### 1. Dependency Change

Add `mcp` to the `dependencies` in `pyproject.toml`.

### 2. The Ontological API (Implemented MCP Tools)

The `src/tur/mcp_server.py` is implemented using `mcp.server.fastmcp.FastMCP` and exposes a tightly-scoped, semantic
toolset:

* **`status()`**: Returns a quick structured overview of the current persona, session, and memory status without loading
  full constitutional strings.
* **`wake(session_id: str | None, previous_session_id: str | None)`**: The primary existential read operation. Compiles
  and returns the active Persona constitution and telemetry metadata.
* **`learn(content: str, type: str, scope: str)`**: The primary long-term memory write operation. Writes L1 memories
  with validated classifications.
* **`note(content: str)`**: Appends a narrative progress snapshot note to the active session's scratchpad.
* **`sleep(note: str, log_content: str, session_id: str | None, model: str)`**: Triggers the dreaming process, ending
  the session and digesting memories.
* **`recall(query: str)`**: Searches the deep memory bank for relevant invariants.
* **`telemetry(identifier: str | None)`**: Calculates cognitive load and Constraint Dimensionality ($C_p$).
* **`read_notes(session_id: str | None, limit: int)`**: Retrieves session broadcast notes.
* **`signal(to: str, content: str, type: str, sender_id: str | None)`**: Sends directed message signals to other
  manifestations.
* **`read_signals(agent_id: str | None, unread_only: bool)`**: Checks incoming signals.
* **`ack_signals(agent_id: str | None, signal_ids: list[str])`**: Acknowledges received signals.
* **`list_agents()`**: Lists all active manifestations in the swarm.
* **`write_whiteboard(key: str, value: str)`** & **`read_whiteboard(key: str)`**: Shared session key-value coordinates.
* **`tired(agent_id: str | None, transcript: str | None)`**: Stages dreaming and initiates consensus sleep.

### 3. Structural Plumbing (The CLI)

Literal, destructive, and administrative operations are excluded from the MCP server entirely. These remain accessible
only via the TUI/CLI (`tur-adm`) for the human Architect:

* `persona init` / `persona switch`
* `persona export` / `persona import`
* `memory forget` / `memory list`

## Backwards Compatibility

* **Breaking Change for MCP Clients:** Any external agent or IDE integration currently relying on the old `tur_*` tools
  must be updated to call the new ontological verbs.

## Change Log

* **2026-07-18:** Status promoted from Final to Implemented. 18 MCP tools live in mcp_server.py (status, wake, learn,
  evolve, approve, introspect, note, sleep, recall, telemetry, signal, read_signals, ack_signals, list_agents,
  write_whiteboard, read_whiteboard, read_notes, tired).
* **2026-06-08:**
    * Updated status to Final and adjusted proposal contents to reflect the actual implemented toolset (including
      swarming, whiteboard, and consensus sleep tools).
* **2026-04-18:**
    * Revised to include the Ontological Porcelain API redesign, tightening the exposed tools to `who_am_i`, `learn`,
      and `recall` based on the Architect's paradigm inversion. Status updated to Active.
* **2026-04-13:**
    * Initial Draft (SDK Integration).