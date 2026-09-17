# Commands & MCP Tools Reference

This reference provides a complete mapping of all agent-facing CLI commands and Model Context Protocol (MCP) tools in
Tur.

## 1. Core Lifecycle Tools

| Action             | CLI Command                       | MCP Tool                | Description                                                     |
|:-------------------|:----------------------------------|:------------------------|:----------------------------------------------------------------|
| **Awakening**      | tur wake                          | wake()                  | Turn Zero prompt compilation and context hydration.             |
| **Status**         | tur status                        | status()                | Check session state, L1 memory breakdown, and L2 graph metrics. |
| **Milestone Note** | tur note &lt;text&gt;             | note(content=...)       | Append transient milestone note to active session continuity.   |
| **Learn**          | tur learn &lt;text&gt; --type ... | learn(content=..., ...) | Consolidate durable invariant into permanent memory.            |
| **Introspect**     | tur introspect --all              | introspect()            | Distill linear L1 memories into L2 Cognitive Map.               |
| **Sleep**          | tur sleep &lt;log&gt; -n ...      | sleep(...)              | Consolidate session transcript into L1 memories.                |
| **Recall**         | tur recall &lt;query&gt;          | recall(query=...)       | Semantic & keyword search across L1/L2 memory banks.            |
| **Metrics**        | tur metrics                       | metrics()               | Measure token density and Constraint Dimensionality ($C_p$).    |
| **Evolve**         | tur evolve &lt;id&gt; --type ...  | evolve(...)             | Stage a lived experience as a Core Memory (pending approval).   |

*(Note: Core Memory approval is strictly human-governed via the administrative CLI: `tur-adm memory approve <core_id>`)*

---

## 2. Distributed Manifestation Coordination

| Action                   | CLI Command                             | MCP Tool      | Parameters        | Description                                             |
|:-------------------------|:----------------------------------------|:--------------|:------------------|:--------------------------------------------------------|
| **Send Message**         | tur message send &lt;to&gt; &lt;msg&gt; | send_message  | to, content, type | Enqueue a typed inter-manifestation message for a peer. |
| **Read Messages**        | tur message read                        | read_messages | unread_only=True  | Fetch incoming messages from other manifestations.      |
| **Acknowledge Messages** | tur message ack &lt;ids&gt; [--all]     | ack_messages  | message_ids=[...] | Mark processed messages as acknowledged.                |
| **Write Board**          | tur board write &lt;key&gt; &lt;val&gt; | write_board   | key, value        | Set a shared session board coordinate parameter.        |
| **Read Board**           | tur board read &lt;key&gt;              | read_board    | key               | Read a specific coordinate from the session board.      |
| **List Board**           | tur board list                          | -             | -                 | List all parameter coordinates on session board.        |
| **Clear Board**          | tur board clear [key] [--all]           | -             | -                 | Clear a coordinate key or entire session board.         |
| **List Manifestations**  | tur agent list                          | list_agents   | -                 | Discover active and idle manifestations in the session. |

---

## 3. Tactical Task Coordination Tools

| Action                   | CLI Command                         | MCP Tool          | Description                                         |
|:-------------------------|:------------------------------------|:------------------|:----------------------------------------------------|
| **List Tasks**           | tur task list                       | -                 | List all tasks registered on the session board.     |
| **Show Task**            | tur task show &lt;id&gt;            | show_task()       | Display details and checklist for a task.           |
| **Claim Task**           | tur task claim &lt;id&gt; -t ...    | claim_task(...)   | Claim task with objective and checklist items.      |
| **Check Item**           | tur task check &lt;item&gt;         | check_task_item() | Check off a completed milestone item in task.       |
| **Handover Task**        | tur task handover -n ...            | handover_task()   | Hand over active task coordinates before pausing.   |
| **Complete Task**        | tur task complete                   | complete_task()   | Mark task completed and unblock dependent tasks.    |

---

## 4. Human Administrative Boundary (`tur-adm`)

*Note: Administrative commands are restricted to the human architect CLI (`tur-adm`) and are structurally blocked from
AI agent runtime execution:*

- `tur-adm persona init` / `list` / `view` / `get` / `set` / `export` / `import`
- `tur-adm memory list` / `view` / `forget` / `approve`
- `tur-adm session start` / `end` / `list` / `note`
- `tur-adm message inspect` (alias: `tur-adm signal inspect`)
- `tur-adm model list` / `pull`
- `tur-adm clean` (Storage bank hygiene)
