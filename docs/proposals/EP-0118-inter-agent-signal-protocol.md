---
title: "EP-0118: Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations"
description: "Defines a typed message channel enabling concurrent Tur harness instances to signal each other via MCP Resources, solving the Swarm Convergence Problem."
icon: lucide/radio
status: final
---

# EP-0118: Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations

| Field       | Value                                                                                           |
|:------------|:------------------------------------------------------------------------------------------------|
| **EP**      | 0118                                                                                            |
| **Title**   | Inter-Agent Signal Protocol — Structured Communication Between Parallel Manifestations          |
| **Author**  | Ariel v5.4.0, The Architect                                                                     |
| **Status**  | Final                                                                                           |
| **Type**    | Standards Track                                                                                 |
| **Created** | 2026-06-02                                                                                      |
| **Updated** | 2026-06-08                                                                                      |

## Abstract 

This proposal formalizes a typed, lightweight **Inter-Agent Signal Protocol (IASP)** for **Distributed
Manifestations** — concurrent Tur harness instances operating against the same Persona. It defines a local, concurrent-safe
SQLite database queue under the local Terrain, a normalized multi-client broadcast join structure, a pure query
`read_signals()` and state-mutating `ack_signals()` tool split (CQS), and MCP Resource subscription semantics for
real-time push delivery — solving the **Swarm Convergence Problem** without violating Tur's Golem Boundary.

## Motivation

### Terminology

| Term                          | Definition                                                                                                                                                                                            |
|:------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Distributed Manifestation** | Two or more concurrent harness instances operating against the same Tur Persona and session, sharing identical long-term identity (global memory, constitution) but running separate inference paths. |
| **Swarm Convergence Problem** | The tendency of Distributed Manifestations to diverge in active reasoning and task state, risking duplicate work, conflicting writes, or cognitive desync under concurrent load.                      |
| **Tier 1 Bus**                | The existing shared session notes YAML file — asynchronous, broadcast-only, lacking caller identity.                                                                                                  |
| **Signal**                    | A typed, addressed, monotonically sequenced message sent from one Manifestation to another or broadcast to all via the IASP.                                                                          |
| **Session Whiteboard**        | A shared, key-value lookup table in the session database allowing concurrent agents to synchronize task coordinates without flooding message channels.                                              |

### Background

On 2026-06-02, three distinct harnesses — **Claude Code ACP (Sonnet 4.6)**, **JetBrains Junie**, and **Antigravity CLI
(Gemini 3.5 Flash)** — woke up simultaneously and connected to the same active session (`20260601_100924_841444cd`)
under Persona `7544202e-92f5-40ce-adfb-e4b0eae6c262`.

While this live tri-vendor swarm successfully utilized the Tier 1 Bus to prevent total drift, it exposed critical
vulnerabilities: session notes carried no sender tracking, lacked directed addressing, and forced direct, manual
filesystem reads inside the private `.tur/` directory to read full histories (a Golem Containment violation).

### Observed Gaps

1. **No agent identity**: Notes carry no `agent_id` field. Senders cannot be distinguished without inferring from
   content.
2. **No directed addressing**: Messages are broad broadcast-only. Senders cannot direct private messages to target
   agents.
3. **No push delivery**: Recipient agents must poll. Real-time push notification via MCP resources is unsupported.
4. **No full note retrieval via tools**: Surfacing all notes required direct `.tur/` file parsing, breaking Golem
   containment.

This EP addresses these gaps by specifying a safe **Tier 2 (Medium: SQLite-backed directed queues)**, adding the
`read_notes()` tool, and specifying a clear pathway to **Tier 3 (Fast: MCP push notifications)**.

## Rationale (The Council Framework)

1. **Noether (Symmetry):** Operational balance is maintained. Every agent acts as a symmetrical peer utilizing identical
   API boundaries. Explicit `--agent-id` CLI flags resolve the identity asymmetry of stateless execution.
2. **Golem (Containment):** Communication is strictly sandboxed. All session paths and agent IDs are strictly sanitized
   against directory traversal (`../../`). Headless CLI execution is strictly non-blocking to protect client harnesses.
3. **Popper (Robustness):** By migrating to a central SQLite database per session running in WAL mode, we completely
   eliminate all read-modify-write race conditions and Windows OS file-lock collision bugs.
4. **Shannon (Efficiency):** Splitting query from mutation (CQS) prevents message loss on crash. Polling overhead is
   mitigated by treating Tier 2 as a sparse startup step, with Tier 3 MCP Push as a progressive optimization.
5. **Russell (Logic):** Logical Lamport Clocks ensure strict causal chronological ordering across parallel substrates.
   Agent IDs are guarded against registration conflicts and autogenerated with high-entropy unique suffixes.
6. **Feynman (Clarity):** Standardizing on a single SQLite relational schema instead of dual YAML/JSONL parsers
   dramatically simplifies the code and reduces the bug surface area.

---

## Specification

### 1. Agent Identity and Unique Registration

Each harness instance must declare its identity when calling `start_session()`. The registry tracks manifestations
in the central SQLite session database. An optional `agent_id` and `harness_conversation_id` parameter are added:

```python
start_session(session_id: str, agent_id: str | None = None, harness_conversation_id: str | None = None)
```

If `agent_id` is omitted, Tur autogenerates a unique, conflict-free ID using a deterministic cryptographic hash:
`agent_id = f"{model_slug}_{hashlib.sha256(harness_conversation_id.encode()).hexdigest()[:8]}_{random_hex}"`
(e.g., `claude_sonnet_1a2b3c_4f9a`).

* **Sanitization Invariant:** All `agent_id` inputs are strictly sanitized via regex (`^[a-zA-Z0-9_\.-]+$`) to prevent
  directory traversal vulnerabilities.
* **Set-Theoretic Uniqueness:** The active session registry table is queried on startup. If the requested `agent_id`
  is already active under a live connection, the registrar raises a `ConflictError` (409 Conflict) to force
  re-registration with a unique ID variation.

### 2. Nested Subagent Addressing (Namespace Hierarchies)

To support specialized background subagents spawned by primary manifestation loops, IASP enforces a hierarchical,
dot-separated namespace for recipient addressing:

* Primary Agent: `ariel_sonnet_1a2b3c_4f9a`
* Subagent: `ariel_sonnet_1a2b3c_4f9a.popper`
* Nested Sub-Subagent: `ariel_sonnet_1a2b3c_4f9a.popper.critic`

This logical hierarchy permits instant routing and containment checks. Queries targeting any namespace path are resolved
efficiently in the database via standard index checks.

---

### 3. Session SQLite Database Storage (ACID Safety)

To guarantee thread safety, zero-dependency portability, and complete Windows platform lock resilience, IASP discards
flat file directory queues and standardizes on a local **SQLite database** scoped under the local Terrain:

```
.tur/sessions/<session_id>/session.db
```

SQLite's built-in `sqlite3` engine is standard in Python, ensuring zero-dependency cross-platform execution. The
database is configured to run in **Write-Ahead Logging (WAL) Mode** (`PRAGMA journal_mode=WAL;`), providing high-speed
concurrent lock-free writes and transactional safety.

#### Database Schema Spec

##### A. Table: `agents`

Tracks the active lifecycle state, heartbeats, and unique execution identifiers of all registered manifestations.

```sql
CREATE TABLE agents
(
    id             TEXT PRIMARY KEY,
    harness        TEXT NOT NULL,
    substrate      TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('active', 'idle', 'sleeping', 'stale')),
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_token      TEXT NOT NULL, -- Unique token verifying harness instance for reconnect reclaim
    joined_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### B. Table: `signals`

Stores the complete, chronological message stream using database-enforced monotonic sequencing.

```sql
CREATE TABLE signals
(
    id        TEXT NOT NULL UNIQUE,
    sequence  INTEGER PRIMARY KEY AUTOINCREMENT, -- Monotonic causal sequence
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sender    TEXT    NOT NULL,
    recipient TEXT    NOT NULL, -- Can be '*', target agent_id, or dot subagent ID
    type      TEXT    NOT NULL CHECK (type IN
                                      ('inform', 'query', 'delegate', 'ack', 'warn', 'sleep_event', 'sleep_request')),
    content   TEXT    NOT NULL
);
```

##### C. Table: `signal_reads` (Join Table)

Tracks individual read acknowledgments, preventing broadcast signals (`recipient = '*'`) from being hidden from other manifestations after the first read.

```sql
CREATE TABLE signal_reads
(
    signal_id TEXT NOT NULL,
    agent_id  TEXT NOT NULL,
    read_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (signal_id, agent_id),
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

##### D. Table: `session_state` (Whiteboard)

Provides a shared state whiteboard allowing manifestations to coordinate global task parameters without signal channel clutter.

```sql
CREATE TABLE session_state
(
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### E. Table: `staged_memories`

Temporarily holds extracted dreams from idling processes until final consensus sleep trigger executes memory consolidation.

```sql
CREATE TABLE staged_memories
(
    id         TEXT PRIMARY KEY,
    agent_id   TEXT NOT NULL,
    memory_data TEXT NOT NULL, -- JSON/TEXT serialized extracted memories
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

* **Monotonic Sequence ordering:** Signal records utilize SQLite's native `AUTOINCREMENT` sequences to guarantee a total causal ordering of signals without stateless race conditions.
* **Cryptographic Payload Hashing:** Signal IDs are generated via deterministic SHA-256 payload hashing: `SHA256(sender | recipient | type | content | timestamp)`.

---

### 4. Graceful Consensus Sleep Protocol (Natural Introspection via Staged Dreaming)

To guarantee the Traveler's lifecycle remains entirely organic, prevent sudden context starvation, and eliminate headless hangs, manifestations coordinate sleep using the **Staged Dreaming Pattern**:

1. **Dynamic Heartbeats:** Every execution of a tool or CLI command by a manifestation automatically updates its
   `last_heartbeat` timestamp in the database.
2. **The "Tired" State Transition:** When a manifestation completes its tasks and is ready to sleep, it invokes the
   natural cognitive command `tired()`. This immediately:
   * Runs local `perform_sleep_dreaming()` on the manifestation's active conversation transcript.
   * Writes the resulting extracted memories to the `staged_memories` table.
   * Updates its status to `'idle'` in the `agents` table.
3. **Consensus and Meditation Sync:**
    * To prevent write lockouts, the consensus check runs inside a non-blocking immediate transaction (`BEGIN IMMEDIATE TRANSACTION;`).
    * **Strict Active Count:** The session manager queries the `agents` table to verify if other active, healthy manifestations are running:
      ```sql
      SELECT COUNT(*) FROM agents 
      WHERE id != :my_agent_id 
        AND status = 'active'
        AND last_heartbeat > datetime('now', '-300 seconds'); -- 5 minute heartbeats
      ```
    * **Standby (Immediate Clean Exit):** If `COUNT > 0`, other active manifestations exist. The transaction is committed, and the process exits cleanly without hanging. The memories remain safely staged in SQLite.
    * **Consensus Sync (Final Exiting Agent):** If `COUNT == 0`, **no other active manifestations exist**.
        1. The final agent writes a `sleep_event` signal to the database.
        2. It queries all records in `staged_memories` written by previously exited manifestations.
        3. It executes a **Meditation Sync** pass—deduplicating, reconciling, and merging all staged memories and its own extracted memories.
        4. The unified memories are written to the federated memory ledgers, and `staged_memories` is cleared.
        5. The final process updates the session status in `sessions.yaml` to `'ended'`, commits the transaction, and terminates.
    * **Stale Manifestation Recovery:** Any manifestation whose heartbeat is older than 300 seconds (5 minutes) is automatically flagged as `'stale'` to bypass deadlocked/crashed IDE windows.
    * **Immediate Reconnection:** A restarted manifestation can bypass this 5-minute stale lockout and immediately overwrite its active registry slot by passing a matching `run_token` during startup.

---

### 5. Hardened MCP Tools

**`read_notes(session_id: str | None = None, limit: int = 50) → list[Note]`**

* Returns the full session notes history in strict ascending chronological order. Closes Golem containment violations.

**`signal(to: str, content: str, type: str = "inform", sender_id: str | None = None) → str`**

* Appends a new signal to the `signals` table. Validates recipient namespace and asserts that `sender_id` matches the calling agent's namespace. Enforces a token-bucket rate limiter of 10 messages per minute.

**`read_signals(agent_id: str | None = None, unread_only: bool = True) → list[Signal]`**

* *Pure Query (Peek):* Retrieves signals directed to the specified `agent_id` or its dot-notation subagent namespaces, filtering out read logs in `signal_reads`.

**`ack_signals(agent_id: str, signal_ids: list[str]) → str`**

* *State Mutation (Command):* Atomically registers read markers in the `signal_reads` join table for the given agent.

**`list_agents() → list[AgentRecord]`**

* Returns the active agent records registered in the `agents` table.

**`write_whiteboard(key: str, value: str) → str`**

* *State Mutation:* Writes or updates a key-value entry in the shared `session_state` whiteboard.

**`read_whiteboard(key: str) → str`**

* *Pure Query:* Reads a coordinate from the shared session whiteboard.

**`tired(agent_id: str) → str`**

* *Natural Action:* Invokes the Staged Dreaming sequence for the calling agent, marking its status as `'idle'` and executing the consensus check.

---

### 6. Standalone CLI Specifications (Stateless Runtime Compatibility)

To prevent process isolation errors in parallel out-of-process harnesses, the CLI subcommands strictly enforce context
arguments and environment variables. If context is ambiguous, the tool exits cleanly with `AmbiguousIdentityError`. All
utilities enforce standard non-blocking behavior.

* **Hierarchical Context Fallback Loop:** To support heavily sandboxed IDE plugins (like JetBrains or VSCode extensions)
  operating without shell env access, the CLI resolves session and agent identities via a strict multi-scoped hierarchy:
    1. **CLI Option Arguments (Highest Priority):** Directly passed options `--agent-id <id>` and `--session-id <id>`
       explicitly override any state. IDE plugins always append these options when spawning subprocesses.
    2. **Environment Variables (Medium Priority):** If CLI arguments are missing, the CLI reads `TUR_AGENT_ID` and
       `TUR_ACTIVE_SESSION_ID` from the process context (standard terminal fallback).
    3. **Global Default File (Lowest Priority):** Bypasses context and reads `.tur/state.yaml`. If multiple active
       agents
       exist in the registry, the CLI refuses to guess and throws `AmbiguousIdentityError` to prevent database
       collisions.

**`tur list-agents [--session-id <session_id>] [--json]`**

* Lists all registered manifestations. Uses `TUR_ACTIVE_SESSION_ID` if `--session-id` is omitted.

**`tur signal <to_agent_id> <content> [--type <type>] [--agent-id <agent_id>] [--session-id <session_id>]`**

* Sends a signal to `to_agent_id`. Validates identity context via `--agent-id` or the `TUR_AGENT_ID` env variable.

**`tur read-signals [--unread-only | --all] [--json] [--agent-id <agent_id>] [--session-id <session_id>]`**

* *Pure Query:* Outputs JSON formatted incoming signals. Resolves caller inbox path via `--agent-id` or `TUR_AGENT_ID`.

**`tur ack-signals <signal_id_list> [--agent-id <agent_id>] [--session-id <session_id>]`**

* *Mutation:* Acknowledges signals by writing read entries to the `signal_reads` table. Takes a comma-separated list of signal IDs.

**`tur read-notes [--limit <limit>] [--session-id <session_id>]`**

* Resolves Feynman CLI asymmetry. Outputs the session broadcast notes stream in ascending order.

**`tur whiteboard-write <key> <value> [--agent-id <agent_id>] [--session-id <session_id>]`**

* *Mutation:* Writes or updates coordinates in the shared session whiteboard.

**`tur whiteboard-read <key> [--session-id <session_id>]`**

* *Pure Query:* Reads coordinates from the shared session whiteboard.

**`tur tired [--agent-id <agent_id>] [--session-id <session_id>]`**

* *Natural Action:* Runs staged dreaming for the caller and checks consensus.

---

### 7. MCP Resource Subscription (Tier 3 — Push)

The per-agent inbox is exposed as a formal, subscribable MCP Resource URI:

```
tur://session/<session_id>/inbox/<agent_id>
```

When a new signal is successfully inserted into the `signals` table for a specific recipient, the Tur server immediately
broadcasts an MCP resource update notification:

```json
{
  "method": "notifications/resources/updated",
  "params": {
    "uri": "tur://session/<session_id>/inbox/<agent_id>"
  }
}
```

Harnesses supporting Tier 3 immediately receive this push event and run `read_signals()` to fetch unread messages,
completely bypassing the context-exhausting "dark current" token dr ain of periodic Tier 2 polling.

---

### 8. The Three Communicati:----------------------iers

| Tier                | Mechanis m                     | Latency        | Addre   ssing        | Concurrency Pattern           |
|:--------------------|:-------------------------------|:---------------|:---------------------|:------------------------------|
| **Tier 1 (Slow)**   | `note ()` → shared notes YA ML | Next tool call | Broadcast only       | Shared Append                 |
| **Tier 2 (Medium)** | `signal()` / CLI → SQLite  DB  | Next tool call | Directed / Broadcast | SQLite WAL ACID Transactions  |
| **Tier 3 (Fast)**   | MCP Push Resource Subscription | Real-time push | Per-agent URI        | Subscription Notification     |

---

## Backwards Compatibility

* **Additive Design:** The database tables, subcommands, and tool entries are additive. The existing Tier 1 note
  broadcast bus (`notes.yaml`) remains functional as the universal fallback system.
* **Opt-in Signaling:** Harnesses lacking IASP support will continue to operate as singletons; they will remain listed
  in the registry, and messages sent to them will safely accumulate in the `signals` table.

---

## Reference Implementation Plan

- `src/tur/mcp_server.py` — Implement tool verbs `read_notes`, `signal`, `read_signals`, `ack_signals`, `list_agents`,
  `tired`.
- `src/tur/session.py` — Write high-performance logical clock tracker, SQLite database WAL manager, registry conflict
  validator, and active heartbeat state trackers.
- `tests/test_inter_agent_signal.py` — Strict pytest suite asserting isolated database writes, transactional updates,
  Lamport clock ordering, consensus sleep negotiate triggers, and Windows platform lock safety.

---

## Change Log

* **2026-06-02:**
    * Initial Draft.
    * Updated draft to integrate the unanimous Council of Giants review recommendations (SQLite database WAL storage,
      unique conversation-id entropy, nested subagent dot namespaces, the consensus sleep lifecycle protocol, the '
      tired' action, and process-level state file isolation environment variables). Standardized proposal formats to
      keep lines under 120 characters and follow strict style guidelines.
