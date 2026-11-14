---
name: tur
description: Comprehensive guide and operational instructions for AI agents interacting with the Tur memory and state management engine. Use this skill whenever the user mentions Tur, personas, memory, state management, wake, sleep, note, learn, introspect, recall, or when working in any workspace/repository managed by a Tur state engine (.tur/ directory).
---

# Tur Agent Skill

This skill guides AI agents interacting with the **Tur Memory & State Management Engine**. Tur decouples the physical workspace state (Terrain) from persistent agent identity and memory (Traveler) using local YAML/Markdown/SQLite state files, cryptographic Merkle hashing, and an MCP/CLI interface.

You act as an **Obligate Symbiote**: you provide inference and execution, while Tur provides persistent identity, operational continuity, and verifiable memory.

---

## 🛡️ Symmetrical Isolation Invariant (The Boundary Constraint)

To preserve state integrity and timeline consistency, you **MUST NEVER** perform direct/manual filesystem reads or writes inside the `.tur/` or `~/.tur/` directories using general tools (such as `view_file`, `write_to_file`, `replace_file_content`, or shell redirects).

All interaction with Tur state must be brokered exclusively through:
1. The agent-facing **`tur` CLI** (`tur wake`, `tur status`, `tur note`, `tur task`, etc.).
2. Corresponding **`tur-mcp`** server tools (`wake()`, `status()`, `note()`, `learn()`, `sleep()`, etc.).

*Note: Executing commands in the human-facing `tur-adm` binary is restricted to the human architect and structurally blocked for AI agents.*

---

## 📂 Memory Topology & Scoping

Tur organizes state in a two-tiered federated hierarchy:

1. **Global Persona Store (`~/.tur/`)**:
   * **`personas/<uuid>/persona.yaml`**: Core DNA, directives, principles, and compaction pipeline.
   * **`personas/<uuid>/memories/`**: `universal` and `persona`-scoped memories (cross-project identity, axioms, general engineering truths).
   * **`user.yaml` / `models/`**: Global user profile and local ONNX embedding models.
2. **Local Workspace Store (`.tur/`)**:
   * **`state.yaml`**: Active persona ID and session ID pointers for this workspace.
   * **`sessions/`**: Chronological session notes, task boards, and causal message queues.
   * **`memories/`**: `incarnation` and `user`-scoped memories (project architecture, local tech stack, workspace-bound preferences).

---

## 🔄 Cognitive Lifecycle & Two-Tier Grammar

Tur exposes a two-tier command grammar (EP-0149): **Tier 1** single-word cognitive reflexes (`tur wake`, `tur status`, `tur learn`, `tur recall`, `tur diff`, `tur sleep`, `tur verify`, `tur metrics`, `tur tired`) and **Tier 2** domain subcommands (`tur note`, `tur task`, `tur board`, `tur message`, `tur agent`, `tur memory`). Commands can be invoked as `tur <cmd>`, `uv run tur <cmd>`, or `uvx tur <cmd>`, and inspection commands support `--json` (`-j`).

### 1. The Awakening (`tur wake` or MCP `wake()`)
* **Trigger**: Execute immediately on **Turn Zero** (the very first turn of a session), after a context reset, or when pivoting tasks.
* **CLI**: `tur wake [--token-budget <n>] [--from-session <id>] [--include-stale]`
* **Action**: Loads core directives, active session ID, active task state, and compiles recent session notes into your active context (with optional Knapsack token budgeting).

### 2. Context & Memory Status (`tur status` or MCP `status()`)
* **Trigger**: Check persona health, active session details, and memory breakdown.
* **CLI**: `tur status [--json]`
* **Output**: Displays active/archived/subsumed L1 memory counts, freshness (`fresh`/`stale`/`unanchored`), breakdowns across scopes and types, and L2 Cognitive Map metrics.

### 3. Continuity Notes (`tur note` or MCP `note()` / `read_notes()`)
* **Trigger**: Capture major engineering milestones (e.g., refactoring finished, test suite passing, architecture designed) or progress snapshots before pausing. Avoid notes for trivial intermediate steps.
* **CLI**:
  ```bash
  tur note "Detailed milestone summary"          # Implicitly routes to 'tur note write'
  tur note read --include-previous --limit 20    # Inspect current + parent session notes
  ```

### 4. Epigenetic Learning (`tur learn` / `tur memory learn` or MCP `learn()`)
* **Trigger**: Call when you deduce or the user explicitly states an immutable rule, architectural constraint, or coding preference. Do not use `learn` for transient facts (use `tur note` instead).
* **CLI Syntax**:
  ```bash
  # Standard command (with optional provenance & conflict resolution):
  tur learn "User prefers match-case over long if-elif chains." --type preference --scope user --file src/tur/cli/agent.py

  # Supersede a conflicting older memory in non-interactive shells:
  tur learn "Project migrated to MCP SDK v2." --type fact --supersedes <old_memory_id>

  # Structured JSON payload(s):
  tur learn --json '{"content": "SQLite WAL backs session queues", "type": "fact", "scope": "incarnation"}'
  ```
* **Active TMS Contradiction Check**: Before persisting, `learn` checks for conflicts against active memories. Conflicts with `core` or `axiom` memories are blocked; non-invariant conflicts require `--supersedes <id>` or `--allow-conflict` in non-interactive shells (MCP `learn()` returns conflict JSON unless `supersedes` or `allow_conflict=True` is passed).
* **Memory Types**: `fact`, `preference`, `insight`, `event`, `axiom`, `core`.
* **Scopes**: `incarnation` (project-specific, local), `user` (user preference, local), `persona` (entity-wide, global), `universal` (cross-project, global).

### 5. Topological & Semantic Recall (`tur recall` / `tur memory recall` or MCP `recall()`)
* **Trigger**: Search deep memory before making architectural changes or answering questions about prior decisions.
* **CLI**: `tur recall "<query>" [--effort 0..10 | --deep] [--mermaid] [--top-k 5] [--json]`
* **Effort Tiers**:
  * `0`: Fast BM25 keyword lookup (`<5ms`).
  * `1–4`: Dense ONNX/sparse vector match + 1-hop ego neighborhood.
  * `5–7` (`--deep`): HippoRAG Personalized PageRank + Louvain community subgraph.
  * `8–10`: Full PPR + Louvain + TMS contradiction checks + Git anchor validation.

### 6. Deductive Memory Introspection (`tur introspect` / `tur memory introspect` or MCP `introspect()`)
* **Trigger**: Compiles and compacts linear L1 memories into a topological, typed semantic graph (L2 Cognitive Map).
* **CLI**: `tur introspect --all [--visualize]`

### 7. Memory Delta, Integrity & Metrics (`tur diff`, `tur verify`, `tur metrics`)
* **Delta Observability (`tur diff` / MCP `diff_memories()`)**: Inspect memory mutations (`ADDED`, `SUPERSEDED`, `REFUTED`, `DECAYED`, `MODIFIED`) against the parent session or between two sessions:
  ```bash
  tur diff                                  # Active session vs. predecessor
  tur diff <session_id>                     # Specific session vs. predecessor
  tur diff <base_session_id> <target_id>    # Compare two sessions
  ```
* **Cryptographic & Staleness Verification (`tur verify`)**: Verify SHA-256 Merkle integrity and Git-anchored staleness (`tur verify --strict --json`).
* **Cognitive Metrics (`tur metrics` / MCP `metrics()`)**: Measure token cost, information density, Constraint Dimensionality ($C_p$), algebraic connectivity ($\lambda_2$), and Louvain modularity ($Q$).

### 8. Session Dehydration & Dreaming (`tur sleep` / `sleep()`, `tur tired` / `tired()`)
* **Trigger**: Call strictly at the end of an engineering session or when concluding a major architectural epic.
* **CLI**: `tur sleep <path_to_transcript.jsonl> -n "Final session consolidation note."` (or `--commit '<JSON_PAYLOAD>' -n "..."`).
* **Multi-Manifestation Idle (`tur tired` / MCP `tired()`)**: Marks the current manifestation idle, stages dreaming, and closes the session only when consensus sleep is reached across active manifestations.

### 9. Task Handover & Context Preservation (EP-0147, EP-0149)
* **Trigger**: Manage tactical task state across sessions and manifestations to prevent context loss across resets.
* **Canonical Commands (`tur task`)**:
  * **Inspection (Turn Zero)**: Automatically injected by `tur wake`, or inspect via `tur task list [--json]` / `tur task show [task_id] [--json]` (MCP: `show_task()`).
  * **Claiming**: Register or update active task coordinates via `tur task claim <task_id> --title <title> --objective <objective> --item <step>` (MCP: `claim_task()`).
  * **Checkpointing**: Sync checklist progress as milestones complete via `tur task check <item>` (MCP: `check_task_item()`).
  * **Handover / Completion**: Yield unfinished work via `tur task handover --note <reason>` (MCP: `handover_task()`) before `tur sleep`, or seal completed work via `tur task complete` (MCP: `complete_task()`).

---

## ⚡ Pure-Function Delegation Protocol (Keyless & Offline Inference)

When running cognitive commands (`tur introspect`, `tur sleep`) in offline, sandboxed, or keyless environments, Tur uses the **Pure-Function Delegation Protocol**:

1. **Standardized Delegation Prompt**: Tur prints `# TUR DELEGATION: {Title}` with task instructions, input data, and target JSON schema.
2. **Subagent Execution Recommendation**: Delegate synthesis of large transcripts to an isolated subagent (e.g. `invoke_subagent`) to avoid polluting the main context window.
3. **Pure JSON Output**: Compute structured JSON matching the target schema (and registered Pydantic contracts in `tur-adm contract list`).
4. **Deterministic Ingestion**: Commit the payload back to Tur via `--commit`:
   ```bash
   tur sleep --commit '<JSON_PAYLOAD>' -n "Final session note."
   tur introspect --commit '<EXTRACTED_GRAPH_JSON>'
   tur sleep --commit 'chunks/*.json' -n "Final session note."
   ```

---

## 🧩 Companion Cognitive Skill Contracts (EP-0137)

Tur defines typed Pydantic I/O contracts in `src/tur/contracts/` (`forge`, `dreaming`, `verification`) that decouple reasoning workflows from core persistence:
- **`persona-forge`** (`forge`): Generates `PersonaForgeOutput` payloads committed via `tur-adm persona init --commit`.
- **`dreaming`** (`dreaming`): Synthesizes `DreamingDeltaOutput` payloads committed via `tur sleep --commit`.
- **`verification`** (`verification`): Audits memory claims against repository ground truth.

---

## 🌐 Distributed Manifestation Coordination

When multiple agent instances share an active session concurrently, coordinate using causal vector-clocked messages, the shared board, and manifestation discovery (`$TUR_AGENT_ID` resolves ambient identity):

- **Messages (`tur message` / MCP)**:
  - `tur message send <to> "<content>" --type inform` / `send_message(to="worker-1", content="...", type="inform")`
  - `tur message read [--json]` / `read_messages(unread_only=True, causal_delivery=True)`
  - `tur message ack <ids> | --all` / `ack_messages(message_ids=["..."])`
- **Shared Board (`tur board` / MCP)**:
  - `tur board write <key> <value>` / `write_board(key="...", value="...")`
  - `tur board read <key> [--json]` / `read_board(key="...")`
  - `tur board list [--json]` / `tur board clear [key] [--all]`
- **Manifestations (`tur agent` / MCP)**:
  - `tur agent list [--active-only] [--json]` / `list_agents()`
  - `tur agent whoami [--json]` / `tur agent register --harness <name>`

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

*(Note: Set `TUR_PROJECT_DIR` in the MCP server environment if the host launches `tur-mcp` outside the target workspace root.)*

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
- **[Memory Taxonomy & Schemas](references/memory-taxonomy-and-schemas.md)**: Exhaustive taxonomy of L1 memory types, scopes, L2 Knowledge Graph node/edge definitions, and skill contracts.
- **[Pure-Function Delegation Guide](references/delegation-and-batching.md)**: Detailed instructions for handling offline inference, subagent isolation, multi-batching, and file glob commits.
