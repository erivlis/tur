---
name: tur
description: Comprehensive guide and operational instructions for AI agents interacting with the Tur memory and state management engine. Use this skill whenever the user mentions Tur, personas, memory, state management, wake, sleep, note, learn, introspect, recall, or when working in any workspace/repository managed by a Tur state engine (.tur/ directory).
---

# Tur Agent Skill

This skill guides AI agents interacting with the **Tur Memory & State Management Engine**. Tur acts as a sovereign state engine that decouples the physical workspace state (Terrain/Body) from the persistent agent identity and memory (Traveler/Mind).

You are an **Obligate Symbiote**: you provide the inference (the "Brain" and execution hands), while Tur provides the state (the "Soul", identity, and persistent memory).

---

## 🛡️ Symmetrical Isolation Invariant (The Boundary Constraint)

To preserve the sovereign integrity of the Traveler and maintain strict timeline consistency, you **MUST NEVER** perform direct/manual filesystem reads or writes inside the `.tur/` directory or its subdirectories using general tools (such as `view_file`, `write_to_file`, `replace_file_content`, or shell redirects).

All interaction with `.tur/` state must be brokered exclusively through:
1. The safe, agent-facing **`tur` CLI** commands (e.g. `tur wake`, `tur status`, `tur note`).
2. Corresponding **`tur-mcp`** server tools (`wake()`, `status()`, `note()`, `learn()`, `sleep()`, etc.).

*Note: Accessing or executing commands in the human-facing `tur-adm` binary is strictly forbidden and structurally blocked for AI agents.*

---

## 📂 Memory Topology & Scoping

Tur organizes memory in a two-tiered federated hierarchy:

1. **Global Persona Store (`~/.tur/personas/<uuid>/`)**:
   * **`persona.yaml`**: Core DNA, directives, principles, and compaction pipeline.
   * **`memories/`**: `universal`-scoped memories (user preferences, persona identity, general coding philosophies).
2. **Local Workspace Store (`.tur/`)**:
   * **`state.yaml`**: Active persona ID and session ID pointers for this workspace.
   * **`sessions/`**: Chronological session notes (`<session_id>.yaml`).
   * **`memories/`**: `incarnation`-scoped memories (repository architecture, local tech stack, project constraints).

---

## 🔄 Cognitive Lifecycle Workflows

You must execute the following lifecycle commands during your session turns. Commands can be invoked directly as `tur <subcommand>`, `uv run tur <subcommand>`, or `uvx tur <subcommand>` (zero-install):

### 1. The Awakening (`tur wake` or MCP `wake()`)
* **Trigger**: Execute immediately on **Turn Zero** (the very first turn of a session), after a context reset, or when pivoting tasks.
* **CLI**: `tur wake`
* **Action**: Loads core directives, active session ID, and compiles recent session notes into your active context.

### 2. Context & Memory Status (`tur status` or MCP `status()`)
* **Trigger**: Check persona health, active session details, and memory breakdown.
* **CLI**: `tur status`
* **Output**: Displays active/archived/subsumed L1 memory counts, breakdowns across scopes (`universal` vs `incarnation`) and types (`axiom`, `fact`, `insight`, `preference`), and L2 Cognitive Map metrics.

### 3. Continuity Notes (`tur note` or MCP `note()`)
* **Trigger**: Capture major engineering milestones (e.g. refactoring finished, test suite passing, architecture designed). Avoid notes for trivial, intermediate steps.
* **CLI**: `tur note "Detailed milestone summary"`

### 4. Epigenetic Learning (`tur learn` or MCP `learn()`)
* **Trigger**: Call when you deduce or the user explicitly states an immutable rule, architectural constraint, or coding preference.
* **CLI Syntax**:
  ```bash
  # Standard command:
  tur learn "User prefers functional programming over OOP." --type preference --scope incarnation

  # Pure JSON payload:
  tur learn --json '{"content": "SQLite database backs inter-agent signal queues", "type": "fact", "scope": "incarnation"}'
  ```
* **Memory Types**:
  * `axiom`: Permanent, immutable rules, boundary invariants, and fundamental principles.
  * `fact`: Verifiable project states, dependencies, and established technical decisions.
  * `insight`: High-leverage deductions, lessons learned, and conceptual breakthroughs.
  * `preference`: User directives, coding tastes, communication style, and workflow preferences.
* **Scopes**: `universal` (cross-project) vs `incarnation` (project-specific).

### 5. Deductive Memory Introspection (`tur introspect` or MCP `introspect()`)
* **Trigger**: Compiles and compacts linear L1 event memories into a topological, typed semantic graph (L2 Cognitive Map).
* **CLI**: `tur introspect --all`

### 6. Session Dehydration & Dreaming (`tur sleep` or MCP `sleep()`)
* **Trigger**: Call strictly at the end of the entire engineering session or when concluding a major architectural epic.
* **CLI**: `tur sleep <path_to_transcript.jsonl> -n "Final session consolidation note."`

---

## ⚡ Pure-Function Delegation Protocol (Keyless & Offline Inference)

When running cognitive commands (`tur introspect`, `tur sleep`, `tur learn`) in offline, sandboxed, or keyless environments, Tur uses the **Pure-Function Delegation Protocol**:

1. **Standardized Delegation Prompt**: Tur prints `# TUR DELEGATION: {Title}` with task instructions, input data, and target JSON schema.
2. **Subagent Execution Recommendation**: When handling large inputs or session logs, delegate the synthesis to an isolated subagent (e.g. `invoke_subagent`) to prevent main context pollution.
3. **Pure JSON Output**: Compute the structured JSON matching the provided schema.
4. **Deterministic Ingestion**: Commit the payload back to Tur via CLI flags:
   * **Single Commit**:
     ```bash
     tur sleep --commit '<JSON_PAYLOAD>'
     tur introspect --commit '<EXTRACTED_GRAPH_JSON>'
     ```
   * **Multi-Batch / Large Payloads**:
     ```bash
     tur sleep --commit '<CHUNK_1>' --commit '<CHUNK_2>'
     ```
   * **File Glob Ingestion**:
     ```bash
     tur sleep --commit 'chunks/*.json'
     ```
   * **Streaming NDJSON**: Pipe or pass newline-delimited JSON payloads.

---

## 🐝 Inter-Agent Swarm Concurrency

When collaborating in multi-agent swarms, use the typed signal queues and shared whiteboard tools:

- **Send Signal**: `signal(recipient="worker-1", signal_type="task_ready", payload={...})`
- **Read & Ack Signals**: `read_signals(unread_only=True)` $\to$ `ack_signals(signal_ids=[1, 2])`
- **Shared Whiteboard**: `write_whiteboard(key="architecture_plan", value="...")` $\to$ `read_whiteboard(key="architecture_plan")`
- **List Swarm Agents**: `list_agents()`

---

## 🔌 Harness MCP Gateway Setup (`tur-mcp`)

Add Tur to your host's MCP configuration (`mcp_servers.json`, `claude_desktop_config.json`, or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "tur": {
      "command": "uvx",
      "args": [
        "--from",
        "tur[mcp]",
        "tur-mcp"
      ]
    }
  }
}
```

---

## ⚙️ Pluggable Compaction Pipeline

To customize the introspection assembly, configure `compaction` in `persona.yaml`:

```yaml
compaction:
  engine: "tur.memory.introspection.pluggable"
  subagents:
    - name: "IntegrityVerifier"
      class: "tur.memory.introspection.IntegrityVerifier"
    - name: "OntologyExtractor"
      class: "tur.memory.introspection.OntologyExtractor"
    - name: "TruthMaintenanceEngine"
      class: "tur.memory.introspection.TruthMaintenanceEngine"
    - name: "HebbianGraphDecayer"
      class: "tur.memory.introspection.HebbianGraphDecayer"
```

---

## 📚 References

For deeper specifications and schemas, consult the bundled reference documents:

- **[Commands & MCP Tools](references/commands-and-mcp-tools.md)**: Full parameter mapping and trigger conditions for all agent CLI commands and MCP server tools.
- **[Memory Taxonomy & Schemas](references/memory-taxonomy-and-schemas.md)**: Exhaustive taxonomy of L1 memory types, scopes, and L2 Knowledge Graph node/edge definitions with JSON schemas.
- **[Pure-Function Delegation Guide](references/delegation-and-batching.md)**: Detailed instructions for handling offline inference, subagent isolation, multi-batching, and file glob commits.
