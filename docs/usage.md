---
description: The complete guide to the Tur CLI commands and biological lifecycle.
icon: lucide/terminal
---

# Usage Guide

Tur is a lightweight, deterministic CLI that manages the lifecycle of your AI personas. It treats an AI identity as a
structured, immutable software object.

## Installation

### System-Wide CLI Tools via `uv tool` (Recommended)

`uv tool` installs Tur into an isolated virtual environment and exposes the executables globally on your system `PATH`:

```shell
# Install the core agent runtime CLI
uv tool install tur

# Or install with human administration TUI (tur-adm), Gemini dreaming (gemini), and MCP gateway (tur-mcp)
uv tool install "tur[admin,gemini,mcp]"

# Upgrade to the latest version anytime
uv tool upgrade tur
```

### Via PyPI / `pip`

```shell
# Install in your active Python environment
pip install tur

# Or with administrative, Gemini SDK, and MCP extras
pip install "tur[admin,gemini,mcp]"
```

### Zero-Install with `uvx`

You can invoke any Tur command instantly without installing anything into your global environment:

```shell
# Run agent lifecycle commands
uvx tur wake

# Run the human administration TUI
uvx --from "tur[admin]" tur-adm persona init

# Run the MCP server
uvx --from "tur[mcp]" tur-mcp
```

### From Source (Development)

```shell
# Clone the repository
git clone https://github.com/erivlis/tur.git
cd tur

# Install the project and all dependencies
uv sync --all-extras --all-groups
```

## The Default Persona Workflow

Tur is designed to be ergonomic. For most commands, **the persona identifier (name or UUID) is optional.**

When you run an agent command without specifying a persona, Tur resolves the persona via the following deterministic chain:

1. **Environment Variable**: Checks `TUR_ACTIVE_PERSONA_ID`.
2. **Workspace State**: Checks `.tur/state.yaml` in the local workspace directory.
3. **Single-Persona Auto-Resolution**: If no workspace state is set and only one persona exists in `~/.tur/personas.yaml` (e.g. `Ariel`), it is automatically selected with zero friction.
4. **Multiple Personas**: If multiple personas exist without a default in `.tur/state.yaml`, Tur prompts you to specify one (`tur wake <name>`), configure a default with `tur-adm persona default <name>`, or switch interactively using the human TUI (`tur-adm persona switch`).

You can always override the default by explicitly providing a name or UUID (e.g., `tur wake ariel` or `tur status ariel`).

---

## Core Commands & Split Architecture

Tur enforces strict physical security boundaries by separating agent runtime operations from human administrative
actions across three distinct executables:

| Executable    | Purpose                       | Target Audience         | Key Commands                                                                 |
|:--------------|:------------------------------|:------------------------|:-----------------------------------------------------------------------------|
| **`tur`**     | Agent Runtime & MCP Gateway   | AI Agent / Host Process | `wake`, `note`, `learn`, `recall`, `status`, `telemetry`, `sleep`            |
| **`tur-adm`** | Sovereign Human Governance    | Human Architect         | `init`, `switch`, `memory list/forget`, `session start/end`, `export/import` |
| **`tur-mcp`** | Model Context Protocol Server | External Harnesses      | MCP Standard JSON-RPC Endpoint                                               |

---

### 1. Initialize a Persona (`init`)

Bootstrap a new persona interactively. This creates the necessary `.tur/personas/` directory structure, generates a
unique UUID, and creates your first `persona.yaml` DNA file.

```shell
tur-adm persona init
```

### 2. Wake the Persona (`wake`)

**The Awakening:** Compiles the static DNA (`persona.yaml`), the User Context (`user.yaml`), and the Memory Bank into a
complete "System Prompt" ready to be fed to an LLM.

```shell
# Wake the default persona
tur wake

# Wake a specific persona
tur wake ariel
```

### 3. Learn a Memory (`learn`)

**Active Learning:** Manually inject a specific insight, fact, or preference directly into the active persona's Memory
Bank during a session.

```shell
tur learn "The user prefers functional programming over OOP." --type preference --scope incarnation

# Or via pure JSON payload:
tur learn --json '{"content": "SQLite is used for signal state", "type": "fact", "scope": "incarnation"}'

# Or for a specific persona:
tur learn "Code must be perfectly symmetrical." ariel --type axiom
```

### 4. Sleep & Consolidate (`sleep`)

**Dehydration:** Extracts insights, facts, and axioms from a raw chat log to update the long-term Memory Bank.

```shell
# With local Gemini API key:
tur sleep path/to/chat.log

# Or in keyless/offline environments using Pure-Function Delegation:
tur sleep --commit '<JSON_PAYLOAD>'

# Multi-batch / multi-chunk ingestion:
tur sleep --commit '<CHUNK_1>' --commit '<CHUNK_2>'

# File glob ingestion:
tur sleep --commit 'chunks/*.json'
```

### 5. Deductive Memory Introspection (`introspect`)

**The Cognitive Map:** Compiles linear L1 memories into a topological, typed semantic graph (L2 OKF knowledge graph).

```shell
# Run ontological extraction across all active memories:
tur introspect --all

# Or commit synthesized graph payload from external harness delegation:
tur introspect --commit '<EXTRACTED_GRAPH_JSON>'
```

### 6. Running as an MCP Server (`tur-mcp`)

**The Symbiote:** Run Tur as an MCP (Model Context Protocol) server. This exposes the Traveler's memory and state engine
to external Harnesses like Claude Desktop, Claude Code, Cursor, or Antigravity.

```shell
tur-mcp
```

#### Client Configuration

Add Tur to your host's MCP configuration file (e.g. `claude_desktop_config.json`,
`.gemini/antigravity-cli/mcp_servers.json`, or `.cursor/mcp.json`):

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

### 7. View Memories (`memories`)

Inspect the contents of the Memory Bank. This lists all active memories that will be included during the next `wake`
cycle.

```shell
tur-adm memory list
```

To include archived (forgotten) memories in the list:

```shell
tur-adm memory list --include-archived
```

### 8. Measure Cognitive Load (`telemetry`)

Calculates the "Constraint Dimensionality" ($C_p$) of a persona based on its principles and weights. This helps you
understand if your persona's ruleset is becoming too complex for an LLM to handle reliably.

```shell
tur telemetry
```

### 9. Forget a Memory (`forget`)

Archives a specific memory by its UUID, removing it from the active context window. The memory is moved to an `archive/`
folder and is no longer loaded during `wake`.

```shell
# You must provide the Memory ID
tur-adm memory forget <memory-hash>

# For a non-default persona:
tur-adm memory forget <memory-hash> ariel
```

### 10. Check Persona Status (`status`)

Renders a rich, structured status panel displaying:
- **Persona identity**: Name, version, and active UUID.
- **Session lifecycle**: Session ID, active/ended status, start/update timestamps, and note counts.
- **L1 Memory Breakdown**: Counts of active, archived, and subsumed memories categorized across federated **scopes** (`universal` vs. `incarnation`) and **types** (`axiom`, `fact`, `insight`, `preference`).
- **L2 Knowledge Metrics**: Total nodes and relational edges in the active Cognitive Map.

```shell
tur status
```

### 11. Search Memories (`recall`)

Perform an exact or keyword search across all memories inside the persona's memory bank to quickly retrieve matching
insights or facts.

```shell
tur recall "Noether"
```

### 12. Manage Sessions (`session` Subgroup)

Administrative tools to manually start and end sessions for a persona.

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

#### Start a Session

```shell
tur-adm session start my-session-123
```

#### End a Session

```shell
tur-adm session end my-session-123
```

### 13. Append a Note (`note`)

Append a narrative note/utterance to the active session. These notes form the continuity bridge of your persona's
sessions.

```shell
tur note "Added status command and cleaned up legacy files."
```

### 14. Switch Active Default Persona (`switch`)

Interactive Textual TUI wizard to switch your current active default persona globally or locally.

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
tur-adm persona switch
```

### 15. Export Persona (`export`)

**Portability:** Packages a global persona's core configuration and universal memories into a portable `.tur`
gzip-compressed archive (excluding project-local incarnation-specific memories).

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
# Export a persona by its name or UUID to a destination file using --output or -o
tur-adm persona export ariel -o ariel.tur
```

### 16. Import Persona (`import`)

**Portability:** Unpacks a `.tur` archive and registers it globally as a new persona on the local system. The framework
sanitizes all Member paths prior to extraction to guarantee safety against path traversal vulnerabilities.

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
# Import a persona from a .tur archive
tur-adm persona import ariel.tur

# Force overwrite an existing persona and set it as active
tur-adm persona import ariel.tur --force --set-active
```

## Customization

### Theming

You can control the theme of the interactive TUIs (`init` and `switch`) by setting the `TUR_THEME` environment variable.

- **textual-dark (Default):** `export TUR_THEME="textual-dark"`
- **textual-light:** `export TUR_THEME="textual-light"`
- **Gruvbox:** `export TUR_THEME="gruvbox"`
- **nord**: `export TUR_THEME="nord"`