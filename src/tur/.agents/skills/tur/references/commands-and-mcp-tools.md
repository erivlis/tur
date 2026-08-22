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
| **Telemetry**      | tur telemetry                     | telemetry()             | Measure token density and Constraint Dimensionality ($C_p$).    |
| **Evolve**         | tur evolve &lt;id&gt; --type ...  | evolve(...)             | Stage a lived experience as a Core Memory (pending approval).   |

*(Note: Core Memory approval is strictly human-governed via the administrative CLI: `tur-adm memory approve <core_id>`)*

---

## 2. Multi-Agent Swarm Concurrency Tools

| Action                  | MCP Tool         | Parameters                      | Description                                          |
|:------------------------|:-----------------|:--------------------------------|:-----------------------------------------------------|
| **Send Signal**         | signal           | recipient, signal_type, payload | Enqueue a typed inter-agent signal for a peer agent. |
| **Read Signals**        | read_signals     | unread_only=True                | Fetch incoming signals from other agents.            |
| **Acknowledge Signals** | ack_signals      | signal_ids=[...]                | Mark processed signals as acknowledged.              |
| **Write Whiteboard**    | write_whiteboard | key, value                      | Set a shared workspace state key.                    |
| **Read Whiteboard**     | read_whiteboard  | key=None                        | Read a specific key or entire whiteboard dict.       |
| **List Agents**         | list_agents      | -                               | Discover active and idle agents in the workspace.    |

---

## 3. Human Administrative Boundary (`tur-adm`)

*Note: Administrative commands are restricted to the human architect CLI (`tur-adm`) and are structurally blocked from
AI agent runtime execution:*

- `tur-adm persona init` / `switch`/ `export` / `import`
- `tur-adm memory list`/ `forget`
- `tur-adm session start`/ `end`
- `tur-adm clean` (Storage bank hygiene)
