# Commands & MCP Tools Reference

This reference provides a complete mapping of all agent-facing CLI commands and Model Context Protocol (MCP) tools in Tur. All `tur` inspection/query commands support `--json` (`-j`) for structured machine output.

## 1. Core Lifecycle & Memory Tools

| Action | CLI Command | MCP Tool | Description |
|:---|:---|:---|:---|
| **Awakening** | `tur wake [--token-budget N] [--from-session ID] [--include-stale]` | `wake(session_id=None, previous_session_id=None, include_stale=False, token_budget=None)` | Turn Zero prompt compilation and context hydration. |
| **Status** | `tur status [--json]` | `status()` | Check session state, L1 memory breakdown, freshness, and L2 graph metrics. |
| **Write Note** | `tur note <text>` (or `tur note write <text>`) | `note(content=...)` | Append transient milestone note to active session continuity. |
| **Read Notes** | `tur note read [--limit N] [--session-id ID] [--include-previous] [--json]` | `read_notes(session_id=None, include_previous=False, limit=50)` (alias: `read_note`) | Read chronological session notes in ascending order. |
| **Learn** | `tur learn <text> --type ... --scope ... [--supersedes ID] [--allow-conflict] [--json <payload>]` *(alias: `tur memory learn`)* | `learn(content=..., type=..., scope='incarnation', confidence=1.0, context_ref=None, supersedes=None, allow_conflict=False)` | Consolidate durable invariant into permanent memory with active TMS conflict checking. |
| **Recall** | `tur recall <query> [--effort 0..10 \| --deep] [--mermaid] [--top-k 5] [--json]` *(alias: `tur memory recall`)* | `recall(query=..., effort=0, deep=False, mermaid=False, top_k=5)` | Hybrid BM25, vector, and HippoRAG PPR semantic recall across L1/L2 banks. |
| **Introspect** | `tur introspect [--all] [--visualize] [--commit ...]` *(alias: `tur memory introspect`)* | `introspect(bootstrap=False)` | Distill linear L1 memories into L2 Cognitive Map. |
| **Diff** | `tur diff [base_id] [target_id] [--type ...] [--scope ...] [--json]` *(alias: `tur memory diff`)* | `diff_memories(base_session_id=None, target_session_id=None, type_filter=None, scope_filter=None)` (alias: `diff`) | Inspect memory mutations (`ADDED`, `SUPERSEDED`, `REFUTED`, `DECAYED`, `MODIFIED`) across sessions. |
| **Verify** | `tur verify [--strict] [--json]` *(alias: `tur memory verify`)* | `-` | Verify SHA-256 Merkle integrity and Git-anchored epistemic staleness. |
| **Metrics** | `tur metrics [--json]` *(alias: `tur telemetry`)* | `metrics(identifier=None)` (alias: `telemetry`) | Measure token density, $C_p$, Louvain clusters, algebraic connectivity ($\lambda_2$), and modularity ($Q$). |
| **Evolve** | `tur evolve <id> --principle ... --covenant ... [--core-type ...]` | `evolve(memory_id=..., core_type=..., derived_principle=..., ethical_covenant=...)` | Stage a lived experience as a Core Memory (`pending_approval`). |
| **Sleep** | `tur sleep [<log>] -n <note> [--commit ...]` | `sleep(note=..., log_content=..., session_id=None)` | Consolidate session transcript or JSON payload into L1 memories and close session. |
| **Tired** | `tur tired [--agent-id ...] [--transcript ...]` | `tired(agent_id=None, transcript=None)` | Mark manifestation idle, stage dreaming, and close session upon consensus. |
| **Scaffold** | `tur scaffold [--format aaif\|claude] [--output ...] [--force]` | `-` | Generate repository-level `AGENTS.md` or `CLAUDE.md` scaffolding. |

*(Note: Core Memory approval is strictly human-governed via `tur-adm memory approve <core_id>`.)*

### MCP Resources

- `tur://context/subgraph/{node_id}`: Exposes a bounded L2 ego-subgraph (JSON nodes + Mermaid diagram) around a cognitive map node.

---

## 2. Distributed Manifestation Coordination

| Action | CLI Command | MCP Tool | Description |
|:---|:---|:---|:---|
| **Send Message** | `tur message send <to> <msg> [--type inform]` *(or `tur message <msg> --to <to>`)* | `send_message(to=..., content=..., type='inform', sender_id=None, vector_clock=None)` | Enqueue a vector-clocked message (`inform`, `query`, `delegate`, `ack`, `warn`, or `*` broadcast). |
| **Read Messages** | `tur message read [--unread-only \| --all] [--json]` | `read_messages(agent_id=None, unread_only=True, causal_delivery=True)` | Fetch incoming messages with causal partial-order delivery. |
| **Ack Messages** | `tur message ack <ids> \| --all` | `ack_messages(agent_id=None, message_ids=[...])` | Mark processed messages as acknowledged. |
| **Write Board** | `tur board write <key> <val>` | `write_board(key=..., value=...)` | Set a shared session board coordinate parameter. |
| **Read Board** | `tur board read <key> [--raw] [--json]` | `read_board(key=...)` | Read a specific coordinate from the session board. |
| **List Board** | `tur board list [--json]` | `-` | List all parameter coordinates on the session board. |
| **Clear Board** | `tur board clear [key] [--all]` | `-` | Clear a coordinate key or entire session board. |
| **List Agents** | `tur agent list [--active-only] [--json]` | `list_agents()` | Discover registered manifestations and heartbeats in the session. |
| **Agent Whoami** | `tur agent whoami [--json]` | `-` | Inspect inferred `$TUR_AGENT_ID`, harness, substrate, and session context. |
| **Register Agent** | `tur agent register --harness <h> [--agent-id ...] [--substrate ...] [--json]` | `-` | Explicitly register a manifestation in the active session. |

---

## 3. Tactical Task Coordination Tools (`tur task`)

| Action | CLI Command | MCP Tool | Description |
|:---|:---|:---|:---|
| **List Tasks** | `tur task list [--json]` | `-` | List active, handover, blocked, or completed tasks on the session board. |
| **Show Task** | `tur task show [id] [--json]` | `show_task(task_id=None)` | Inspect details, objective, dependencies, and checklist for a task. |
| **Claim Task** | `tur task claim <id> --title ... [--objective ...] [--item ...] [--depends-on ...] [--target ...] [--ttl 60] [--force]` | `claim_task(task_id=..., title=..., objective='', work_items=None, depends_on=None, target_files=None, ttl_minutes=60, force=False)` | Atomically claim or update task coordinates and lease on the board. |
| **Check Item** | `tur task check <item> [--task <id>] [--done \| --undone]` | `check_task_item(item=..., task_id=None, done=True)` | Mark a checklist milestone item (1-based index or substring) as done or undone. |
| **Handover Task** | `tur task handover [id] [--note <n>]` | `handover_task(task_id=None, note=None)` | Yield task ownership (`status='handover'`) for the next manifestation. |
| **Complete Task** | `tur task complete [id]` | `complete_task(task_id=None)` | Seal task as `completed` and unblock dependent tasks. |

---

## 4. Human Administrative Boundary (`tur-adm`)

*Administrative commands are restricted to the human architect CLI (`tur-adm`) and are structurally blocked from AI agent execution:*

- `tur-adm persona init` (`--commit` / `--skill`) / `list` / `view` / `get` / `set` / `export` / `import`
- `tur-adm memory list` / `approve` / `view` / `forget` / `redact` / `embed`
- `tur-adm session list` / `start` / `end` / `note`
- `tur-adm message inspect`
- `tur-adm model list` / `status` / `pull` / `remove`
- `tur-adm contract list` / `show` / `validate`
- `tur-adm clean` / `tur-adm scaffold`
