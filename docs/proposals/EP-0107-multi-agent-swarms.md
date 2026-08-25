---
title: "EP-0107: Multi-Agent Swarm Readiness (Synchronization & Concurrency)"
description: "Addresses concurrent MCP agent challenges via atomic writes and a subscribable MCP Resource model."
icon: lucide/network
status: deferred
---

# EP-0107: Multi-Agent Swarm Readiness (Synchronization & Concurrency)

| Field       | Value                                                       |
|:------------|:------------------------------------------------------------|
| **EP**      | 0107                                                        |
| **Title**   | Multi-Agent Swarm Readiness (Synchronization & Concurrency) |
| **Author**  | The Architect                                               |
| **Status**  | Deferred                                                    |
| **Type**    | Standards Track                                             |
| **Created** | 2026-04-18                                                  |
| **Updated** | 2026-06-08                                                  |

## Abstract

This proposal formally gathers and addresses the architectural challenges of running multiple, concurrent MCP Agents
(e.g., Claude Code, Gemini CLI, Cursor) against the same underlying Tur Persona. It outlines the transition from a pure
Tool-based state interface to a Subscribable Resource model, preventing "context window overload" while maintaining
real-time, optional synchronization across the Swarm.

## Motivation

As Tur transitions into an Orchestration Engine (EP-0102), the likelihood of a single Persona being operated
simultaneously by multiple agents increases dramatically. This introduces two critical vectors of failure:

1. **File Store Corruption:** If Agent A (`learn`) and Agent B (`forget`) attempt to modify the exact same cryptographic
   memory file (EP-0106) simultaneously, the OS will either throw an error or silently truncate the file, destroying the
   Persona's history.
2. **Cognitive Desync vs. Overload:** If Agent A deduces a critical new constraint ("Never use `cat` in shell
   commands"), Agent B remains ignorant of this constraint until its next `who_am_i` call. However, forcefully blasting
   Agent B with a "State Changed" notification while it is mid-generation could derail its attention mechanism and
   destroy its context window (The Shannon Principle).

## Rationale (The Council Framework)

* **The Golem (Containment):** The underlying `.tur/` file store must be hardened against multi-process race conditions.
* **Shannon (Efficiency):** We must provide a synchronization mechanism that agents can *opt into* (Subscriptions)
  rather than *forcing* updates into their context windows.
* **Noether (Symmetry):** We must perfectly align Tur's architecture with the dual-nature of the MCP Protocol: Actions
  (mutations) belong in **Tools**; State (read-only subscriptions) belong in **Resources**.

## Specification

### 1. Atomic File Operations (Hardening)

* **Implemented (2026-04-18):** The `MemoryManager` has already been refactored to use POSIX atomic write patterns (
  `tempfile` + `os.fsync` + `os.replace`). This guarantees that concurrent file mutations by different agents will never
  result in corrupted or truncated YAML files. The OS ensures the "last write wins" cleanly.

### 2. The Resource Subscription Model

To address the "Desync vs. Overload" dilemma, Tur will expose its active state not just via the `who_am_i` tool, but as
native MCP **Resources**.

* **Proposed Resources:**
    * `tur://universal/knowledge_graph` (The Soul)
    * `tur://incarnational/knowledge_graph` (The Mind)
    * `tur://active_constitution` (The compiled `PERSONA.md` + Telemetry)

* **The Synchronization Loop:**
    1. When an Agent connects, the Host Application (e.g., Cursor) can optionally *subscribe* to
       `tur://active_constitution`.
    2. When a peer Agent executes the `learn` tool, the Tur server modifies the file store (atomically).
    3. The Tur server then broadcasts an MCP `notifications/resources/updated` event to all subscribed Host
       Applications.
    4. The Host Application receives the notification. Its internal orchestrator decides *when* to interrupt the Agent
       to present the new state, entirely eliminating forced cognitive overload.

## Backwards Compatibility

* This is a purely additive architectural evolution for Phase 3 (The Agent Ecosystem).
* The existing "Ontological Porcelain" tools (`who_am_i`, `learn`, `recall`) will remain fully functional for stateless
  or single-agent interactions.

## Reference Implementation

Implemented in `src/tur/mcp_server.py` (`signal`, `read_signals`, `ack_signals`, `list_agents`, `write_whiteboard`,
`read_whiteboard`) and `src/tur/session.py`.

## Change Log

* **2026-04-18:**
    * Initial Draft created to capture the Architect's insights on swarm concurrency, atomic writes, and the necessity
      of shifting state synchronization to MCP Resources.