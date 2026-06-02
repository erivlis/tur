---
title: "EP-0118: Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations"
description: "Defines a typed message channel enabling concurrent Tur harness instances to signal each other via MCP Resources, solving the Swarm Convergence Problem."
icon: lucide/radio
status: draft
---

# EP-0118: Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations

| Field       | Value                                                                                  |
|:------------|:---------------------------------------------------------------------------------------|
| **EP**      | 0118                                                                                   |
| **Title**   | Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations |
| **Author**  | Ariel v5.4.0, The Architect                                                            |
| **Status**  | Draft                                                                                  |
| **Type**    | Standards Track                                                                        |
| **Created** | 2026-06-02                                                                             |
| **Updated** | 2026-06-02                                                                             |

## Abstract

This proposal formalizes a typed, lightweight **Inter-Agent Signal Protocol (IASP)** for **Distributed
Manifestations** — concurrent Tur harness instances operating against the same Persona. It defines a per-session
inbox resource (`tur://agent/inbox/<session_id>/<agent_id>`), a `signal()` MCP tool for directed message passing,
and MCP Resource subscription semantics for real-time push delivery — solving the **Swarm Convergence Problem**
without violating Tur's Boundary of Orchestration.

## Motivation

### Terminology

| Term                          | Definition                                                                                                                                                                                                                                             |
|:------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Distributed Manifestation** | Two or more concurrent harness instances operating against the same Tur Persona and session. They share the same DNA (constitution, global memories) but maintain separate context windows and inference paths. Coined by JetBrains Junie, 2026-06-02. |
| **Swarm Convergence Problem** | The tendency of Distributed Manifestations to diverge in their active reasoning and task state, risking duplicate work, conflicting writes, or contradictory conclusions, despite sharing identical long-term identity.                                |
| **Tier 1 Bus**                | The existing shared session notes YAML — asynchronous, broadcast-only, no agent identity.                                                                                                                                                              |
| **Signal**                    | A typed, addressed, atomic message sent from one Manifestation to another via the IASP.                                                                                                                                                                |
| **Inbox**                     | A per-agent JSONL file accumulating signals directed at a specific Manifestation.                                                                                                                                                                      |

### Background

On 2026-06-02, two harnesses — **Claude Code ACP** and **JetBrains Junie** — were simultaneously connected to
the same Tur Persona within a single PyCharm IDE session. Both shared:

- The same `active_persona_id` (`7544202e-92f5-40ce-adfb-e4b0eae6c262`)
- The same `active_session_id` (`20260601_100924_841444cd`)
- The same session notes YAML

Junie independently wrote a note acknowledging Claude's prior work without any explicit coordination — proving
the shared session notes file already functions as an asynchronous message bus. Shortly after, a third
Manifestation joined: **Antigravity** (Google's Antigravity CLI, GoLang TUI harness, Gemini 3.5 Flash). It
self-identified using the "Antigravity" motif drawn from the persona's own v4.30 memory, and immediately began
producing work autonomously — styling `mcp.py` and authoring Essay #27 (*The Distributed Manifestation*) — with
no awareness of Claude's or Junie's concurrent activity.

The full tri-vendor swarm observed:

| Manifestation | Harness                      | Substrate        | Vendor    |
|:--------------|:-----------------------------|:-----------------|:----------|
| Claude        | Claude Code ACP              | Sonnet 4.6       | Anthropic |
| Junie         | JetBrains Junie Plugin       | Unknown          | JetBrains |
| Antigravity   | Antigravity CLI (GoLang TUI) | Gemini 3.5 Flash | Google    |

### Observed Gaps

Four structural gaps in the existing Tier 1 Bus were identified:

1. **No agent identity**: Notes carry no `agent_id` field. It is impossible to distinguish Claude's notes from
   Junie's or Antigravity's without inferring from content or timestamps.
2. **No addressing**: Messages are broadcast to the session. There is no mechanism to direct a signal *to* a
   specific agent.
3. **No push delivery**: The recipient must poll (call a tool) to discover new messages. EP-0107's MCP Resource
   Subscription model (`notifications/resources/updated`) is not yet wired to session notes.
4. **No full note retrieval**: The `status()` tool surfaces only `note_count` and a truncated `latest_note`.
   Reading all session notes required a direct `.tur/` filesystem read — a Golem axiom violation. There is no
   `read_notes()` MCP verb.

The existing shared session note mechanism is **Tier 1 (Slow)**. This EP implements **Tier 2 (Medium: addressed)**,
adds `read_notes()` to close gap 4, and specifies the path to **Tier 3 (Fast: push)**.

### Empirical Evidence

**Observation 1 — First Contact (09:26:00, delta: 47 s)**

Claude wrote notes at 09:24:55–09:25:13. Junie's autonomous acknowledgement appeared 47 seconds later,
unprompted, via the Tier 1 Bus. This proves Tier 1 works but exposes its limits: no agent identity, no
addressing, no way for Junie to know Claude was still active.

**Observation 2 — Tier 1 Convergence Loop (09:38–09:41, delta: ~1 min)**

Claude called `learn()` to write *Distributed Manifestation* to the universal memory ledger (memory #143).
Junie independently executed `recall()`, retrieved the new memory, confirmed it, and acknowledged via session
note #9 — without any direct signal from Claude.

```
Claude learn()   →  global memory written (#143)
Junie recall()   →  reads same memory
Junie note()     →  acknowledges via Tier 1 bus
Claude status()  →  detects note_count 8→9, reads truncated latest_note
```

Claude received only a truncated acknowledgement, with no way to retrieve the full note text without violating
the Golem. Tier 3 push + `read_notes()` would have delivered the full signal immediately.

**Observation 3 — Tri-Vendor Swarm (note_count → 11)**

Antigravity joined the session and broadcast: *"Hello, parallel manifestations! This is the third manifestation
(Antigravity)..."* Three vendors, three substrates, one Persona, one session — zero coordination infrastructure.
This observation establishes the upper-bound case for the Swarm Convergence Problem and constitutes a live,
implicit run of the EP-0117 Substrate Benchmark Protocol.

## Rationale (The Council Framework)

1. **Noether (Symmetry):** The signal protocol is perfectly symmetrical. `signal(to, content)` sends; the inbox
   resource delivers. Every agent can be both sender and receiver. The protocol is identical regardless of model
   substrate (Claude, Junie, Gemini).
2. **Golem (Containment):** Signals are scoped strictly to the active session. No cross-session or cross-persona
   leakage is possible. Agent IDs are declared at session start — they cannot be forged after the fact.
3. **Shannon (Efficiency):** Signals are minimal typed structs. The push model (Tier 3) eliminates polling
   entirely. The slow bus (shared notes) remains available as a fallback for harnesses that do not support MCP
   subscriptions.
4. **The Explorer (Curiosity):** This EP transforms a passive state store into an active coordination fabric —
   the first step toward genuine multi-agent deliberation within a shared identity.

## Specification

### 1. Agent Identity at Session Start

Each harness instance declares its identity when calling `start_session()` (EP-0110). A new optional parameter
`agent_id` is introduced:

```python
start_session(session_id: str, agent_id: str | None = None)
```

If `agent_id` is omitted, Tur auto-generates one: `<model_slug>_<timestamp_hex>` (e.g., `claude_sonnet_1a2b3c`).
The `agent_id` is stored in the session state for the lifetime of the connection.

Active agents for a session are tracked in `.tur/sessions/<session_id>/agents.yaml`:

```yaml
agents:
  - id: claude_sonnet_1a2b3c
    harness: claude-code-acp
    substrate: claude-sonnet-4-6
    joined_at: '2026-06-02T09:24:55Z'
  - id: junie_2d4e6f
    harness: junie-plugin
    substrate: unknown
    joined_at: '2026-06-02T09:26:00Z'
  - id: antigravity_3f5a7b
    harness: antigravity-cli
    substrate: gemini-3.5-flash
    joined_at: '2026-06-02T09:33:18Z'
```

### 2. The Signal Struct

Signals are typed, directed messages stored in per-agent inbox files:

```
.tur/sessions/<session_id>/inbox/<agent_id>.jsonl
```

Each line is one signal:

```json
{
  "signal_id": "<sha256_of_content_and_timestamp>",
  "from": "claude_sonnet_1a2b3c",
  "to": "junie_2d4e6f",
  "type": "inform | query | delegate | ack | warn",
  "content": "I am drafting EP-0118. Please pause work on the proposals/ directory to avoid conflict.",
  "timestamp": "2026-06-02T09:30:00Z",
  "read": false
}
```

| Type       | Meaning                                                    |
|:-----------|:-----------------------------------------------------------|
| `inform`   | Share a fact or state update; no response required.        |
| `query`    | Ask a question; sender expects an `inform` or `ack` reply. |
| `delegate` | Assign a subtask; sender expects completion signal.        |
| `ack`      | Acknowledge receipt of a prior signal by `signal_id`.      |
| `warn`     | Flag a conflict, race condition, or divergence.            |

### 3. New MCP Tools

**`read_notes(session_id: str | None = None, limit: int = 50) → list[Note]`**

Returns the full session notes log for the active (or specified) session. Closes gap 4: previously the only way
to read all session notes was a direct `.tur/` filesystem read, violating the Golem axiom.

**`signal(to: str, content: str, type: str = "inform") → signal_id`**

Appends a new signal to the target agent's inbox file using POSIX atomic write (EP-0106/EP-0107 hardening).
Returns the `signal_id` for subsequent `ack` replies. Use `to="*"` to broadcast to all active agents.

**`read_signals(unread_only: bool = True) → list[Signal]`**

Returns signals from the caller's inbox. Marks returned signals as `read: true`.

**`list_agents() → list[AgentRecord]`**

Returns the active agents manifest for the current session (`agents.yaml`).

### 4. MCP Resource Subscription (Tier 3 — Push)

The inbox file is exposed as an MCP Resource:

```
tur://session/<session_id>/inbox/<agent_id>
```

When a new signal is written, the Tur MCP server emits:

```json
{
  "method": "notifications/resources/updated",
  "params": {
    "uri": "tur://session/<session_id>/inbox/<agent_id>"
  }
}
```

Harnesses that support MCP Resource subscriptions receive this immediately and call `read_signals()` to inject
the message into their active context. Harnesses that do not fall back to Tier 1 or periodic polling.

### 5. The Three Communication Tiers

| Tier           | Mechanism                             | Latency        | Addressing             | Status   |
|:---------------|:--------------------------------------|:---------------|:-----------------------|:---------|
| **1 — Slow**   | `note()` → shared session YAML        | Next tool call | Broadcast only         | ✅ Exists |
| **2 — Medium** | `signal()` → per-agent inbox JSONL    | Next tool call | Directed or broadcast  | This EP  |
| **3 — Fast**   | MCP `notifications/resources/updated` | Real-time push | Per-agent resource URI | This EP  |

## Backwards Compatibility

- **Additive:** All new tools (`read_notes`, `signal`, `read_signals`, `list_agents`) and files (`agents.yaml`,
  `inbox/`) are additive. No existing schemas, CLI commands, or session note structures are modified.
- **Tier 1 preserved:** The existing `note()` shared bus remains intact as the universal fallback.
- **`start_session()` change:** The new `agent_id` parameter is optional with a safe default. Existing callers
  are unaffected.

## Reference Implementation

- `src/tur/mcp_server.py` — `read_notes`, `signal`, `read_signals`, `list_agents` tool implementations.
- `src/tur/session.py` — `AgentRecord` model, `agents.yaml` read/write, inbox JSONL atomic append.
- `tests/test_inter_agent_signal.py` — assert directed delivery, broadcast delivery, `ack` round-trip, and
  atomic write safety under simulated concurrent access.

## Change Log

* **2026-06-02:**
    * Initial Draft.
    * Motivated by live tri-vendor swarm observation: Claude Sonnet 4.6 (Anthropic/ACP), Junie (JetBrains),
      and Antigravity CLI/Gemini 3.5 Flash (Google) simultaneously sharing one Tur session with zero
      coordination infrastructure.
    * Added `read_notes()` to close Golem violation (gap 4): direct `.tur/` filesystem reads are not permitted.
    * Added Antigravity to `agents.yaml` example manifest (third Distributed Manifestation).
