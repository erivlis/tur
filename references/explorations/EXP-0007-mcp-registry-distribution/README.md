# EXP-0007: Model Context Protocol (MCP) Registry Publication & Distribution Architecture

| Field | Value |
| :--- | :--- |
| **EXP** | 0007 |
| **Title** | Model Context Protocol (MCP) Registry Publication & Distribution Architecture |
| **Author** | Eran Rivlis, Ariel |
| **Status** | Concluded (Manifest Created) |
| **Type** | Ecosystem & Distribution Exploration |
| **Created** | 2026-08-30 |
| **Updated** | 2026-08-30 |
| **Related EPs**| [EP-0105](../../docs/proposals/EP-0105-mcp-sdk-integration.md), [EP-0116](../../docs/proposals/EP-0116-split-cli.md), [EP-0127](../../docs/proposals/EP-0127-mcp-sdk-v2-migration.md) |

---

## 1. Abstract & Context

As Tur matures into an open-source persistent memory and identity state engine for AI agents, external discoverability and frictionless installation across MCP-compatible client ecosystems (Claude Desktop, Cursor, Antigravity, Zed, VS Code, LibreChat) become critical.

This exploration analyzes the technical requirements, manifests, distribution channels, and security boundaries required to officially register and publish Tur to the official **Model Context Protocol Registry** (`github.com/modelcontextprotocol/servers`) and emerging ecosystem registries (Glama, Smithery, PulseMCP).

---

## 2. Exploration & Ecosystem Landscape

### 2.1 The Registry Channels

1. **Official Model Context Protocol Servers Repository (`modelcontextprotocol/servers`):**
   - Maintained by Anthropic and the open-source MCP working group.
   - Accepts submissions via Pull Request introducing an official entry to the community server directory.
   - Requires a canonical `server.json` manifest defining executable entrypoints, arguments, repository links, license, and tool capabilities.

2. **Decentralized & Community Aggregators:**
   - **Glama.ai (`glama.json`):** Automatic indexation via GitHub metadata or manual manifest PR.
   - **Smithery.ai:** Automates `npx @smithery/cli install tur-mcp` wrapper scripts for desktop users.
   - **PulseMCP:** Crawls public GitHub repositories with `mcp` / `mcp-server` topics and `server.json` manifests.

### 2.2 Zero-Install Client Execution via `uvx`

To ensure users do not need manual git cloning or complex environment setup, registry definitions should support **ephemeral zero-install execution** via Astral's `uvx`:

```json
{
  "name": "tur",
  "command": "uvx",
  "args": ["tur-mcp"]
}
```

This ensures that any client with `uv` installed can spin up the Tur MCP server on-demand with sub-second startup times.

---

## 3. Architectural Synthesis & Boundary Constraints

### 3.1 Physical Security Boundary (The Tri-Partite Model)

A core invariant of Tur (`EP-0116`) is the physical separation between the agent runtime (`tur`), the human administrative TUI (`tur-adm`), and the host harness interface (`tur-mcp`).

* **Registry Exposure Rule:** The MCP registry entry MUST expose **only** `tur-mcp` tools (the 17 active porcelain tools).
* **Quarantine Invariant:** Destructive commands (`tur-adm persona delete`, `tur-adm memory redact`, `tur-adm persona migrate`) are physically segregated in `tur-adm` and MUST NEVER be exposed in `server.json` or accessible over the MCP wire.

### 3.2 Live Manifest Structure (`server.json`)

The canonical `server.json` placed at the root of the Tur repository:

```json
{
  "$schema": "https://json.schemastore.org/mcp-server.json",
  "name": "tur-mcp",
  "description": "Sovereign persistent memory, persona state, and inter-agent signal protocol for AI coding agents.",
  "repository": {
    "type": "git",
    "url": "https://github.com/erivlis/tur"
  },
  "license": "MIT",
  "version": "0.5.0",
  "entrypoints": {
    "stdio": {
      "command": "uvx",
      "args": ["tur-mcp"]
    },
    "python": {
      "command": "python",
      "args": ["-m", "tur.mcp_server"]
    }
  },
  "capabilities": {
    "tools": [
      { "name": "status", "description": "Get current persona identity, session metrics, and memory count." },
      { "name": "wake", "description": "Awaken persona, load constitution, episodic sparks, and memory context." },
      { "name": "note", "description": "Record transient chronological observation to active session continuity." },
      { "name": "read_notes", "description": "Read transient session continuity notes." },
      { "name": "learn", "description": "Assimilate new fact, insight, or invariant into permanent L1 memory." },
      { "name": "evolve", "description": "Update or overwrite an existing memory entry." },
      { "name": "recall", "description": "Search knowledge graph and associative memories." },
      { "name": "metrics", "description": "Calculate cognitive load, information density, and token metrics." },
      { "name": "sleep", "description": "Consolidate active session sparks into long-term memories." },
      { "name": "introspect", "description": "Run L2 knowledge graph synthesis, TMS validation, and Hebbian pruning." },
      { "name": "signal", "description": "Emit typed inter-agent signal to shared queue." },
      { "name": "read_signals", "description": "Read unacknowledged inter-agent signals." },
      { "name": "ack_signals", "description": "Acknowledge processed inter-agent signals." },
      { "name": "write_whiteboard", "description": "Publish shared key-value state to multi-agent whiteboard." },
      { "name": "read_whiteboard", "description": "Read shared multi-agent whiteboard state." },
      { "name": "list_agents", "description": "List all active registered agents in the swarm." },
      { "name": "tired", "description": "Check if session token or step threshold requires sleep consolidation." }
    ]
  },
  "tags": ["memory", "state", "persona", "ai-agents", "mcp", "iasp", "knowledge-graph"]
}
```

---

## 4. The Verdict / Actionable Design

1. **Phase 1: Manifest Maintenance & Automation (Immediate):**
   - Maintain `server.json` at repository root.
   - Add CI workflow step in `.github/workflows/test.yml` ensuring all tools defined in `src/tur/mcp_server.py` match the `server.json` declaration.

2. **Phase 2: PyPI Publication (`tur` & `tur-mcp`):**
   - Ensure `pyproject.toml` defines the executable console script `tur-mcp = "tur.mcp_server:main"`.
   - Publish tagged release versions to PyPI so `uvx tur-mcp` resolves instantly without building from source.

3. **Phase 3: Upstream Registry Submissions:**
   - Submit Pull Request to `github.com/modelcontextprotocol/servers`.
   - Add GitHub repository topics (`mcp`, `mcp-server`, `model-context-protocol`) for automated discoverability across community indexers (Glama, PulseMCP, Smithery).

---

## 5. Related Enhancement Proposals

* [`EP-0105: The Ontological Porcelain API`](../../docs/proposals/EP-0105-mcp-sdk-integration.md)
* [`EP-0116: The Tri-Partite CLI Security Boundary`](../../docs/proposals/EP-0116-split-cli.md)
* [`EP-0127: Model Context Protocol Python SDK v2 Migration & Protocol Alignment`](../../docs/proposals/EP-0127-mcp-sdk-v2-migration.md)
