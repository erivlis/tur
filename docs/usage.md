---
description: The complete guide to the Tur CLI commands and biological lifecycle.
icon: lucide/terminal
---
# Usage Guide

Tur is a lightweight, deterministic CLI that manages the lifecycle of your AI personas. It treats an AI identity as a
structured, immutable software object.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```shell
# Clone the repository
git clone https://github.com/erivlis/tur.git
cd tur

# Install the project and dependencies
uv sync --all-extras --all-groups
```

## The Default Persona Workflow

Tur is designed to be ergonomic. For most commands, **the persona identifier (name or UUID) is optional.**

If you run a command without specifying a persona, Tur will:

1. Check `.tur/state.yaml` for your active default persona.
2. If no default is set, it will launch an interactive Textual TUI asking you to select one from your available
   personas.
3. Your selection will be saved as the new default for all future commands.

You can always override the default by explicitly providing a name or UUID (e.g., `uv run tur wake turing`).

---

## Core Commands

The Tur CLI is invoked using `uv run tur` (or just `tur` if your virtual environment is active).

### 1. Initialize a Persona (`init`)

Bootstrap a new persona interactively. This creates the necessary `.tur/personas/` directory structure, generates a
unique UUID, and creates your first `persona.yaml` DNA file.

```shell
uv run tur init
```

### 2. Wake the Persona (`wake`)

**The Awakening:** Compiles the static DNA (`persona.yaml`), the User Context (`user.yaml`), and the Memory Bank into a
complete "System Prompt" ready to be fed to an LLM.

```shell
# Wake the default persona
uv run tur wake

# Wake a specific persona
uv run tur wake ariel
```

### 3. Learn a Memory (`learn`)

**Active Learning:** Manually inject a specific insight, fact, or preference directly into the active persona's Memory Bank during a session.

```shell
uv run tur learn "The user prefers functional programming over OOP." --type preference --scope incarnation

# Or for a specific persona:
uv run tur learn "Code must be perfectly symmetrical." ariel --type axiom
```

### 4. Sleep & Consolidate (`sleep`)

**Dehydration:** Extracts insights, facts, and axioms from a raw chat log to update the long-term Memory Bank. It uses
an LLM (acting as the Subconscious) to parse the log and structure the data.

*Note: Requires the `GEMINI_API_KEY` environment variable to be set.*

```shell
uv run tur sleep path/to/chat.log

# Or for a specific persona:
uv run tur sleep path/to/chat.log ariel
```

### 5. Running as an MCP Server (`serve`)

**The Symbiote:** Run Tur as an MCP (Model Context Protocol) server. This allows Tur to act as the "Traveler" state engine, seamlessly plugging into external "Harnesses" like Claude Desktop, Claude Code, or Gemini CLI.

```shell
uv run tur serve --transport stdio
```

### 6. View Memories (`memories`)

Inspect the contents of the Memory Bank. This lists all active memories that will be included during the next `wake`
cycle.

```shell
uv run tur memories
```

To include archived (forgotten) memories in the list:

```shell
uv run tur memories --include-archived
```

### 7. Measure Cognitive Load (`telemetry`)

Calculates the "Constraint Dimensionality" ($C_p$) of a persona based on its principles and weights. This helps you
understand if your persona's ruleset is becoming too complex for an LLM to handle reliably.

```shell
uv run tur telemetry
```

### 8. Forget a Memory (`forget`)

Archives a specific memory by its UUID, removing it from the active context window. The memory is moved to an `archive/`
folder and is no longer loaded during `wake`.

```shell
# You must provide the Memory ID
uv run tur forget <memory-hash>

# For a non-default persona:
uv run tur forget <memory-hash> ariel
```

### 9. Check Persona Status (`status`)

Renders a rich status panel containing the currently selected persona's details, the active or last session ID and its status, started/updated timestamps, total session notes, the latest note snippet, and total memory count.

```shell
uv run tur status
```

### 10. Search Memories (`recall`)

Perform an exact or keyword search across all memories inside the persona's memory bank to quickly retrieve matching insights or facts.

```shell
uv run tur recall "Noether"
```

### 11. Manage Sessions (`session` Subgroup)

Administrative tools to manually start and end sessions for a persona. 

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

#### Start a Session
```shell
uv run tur session start my-session-123
```

#### End a Session
```shell
uv run tur session end my-session-123
```

### 12. Append a Note (`note`)

Append a narrative note/utterance to the active session. These notes form the continuity bridge of your persona's sessions.

```shell
uv run tur note "Added status command and cleaned up legacy files."
```

### 13. Switch Active Default Persona (`switch`)

Interactive Textual TUI wizard to switch your current active default persona globally or locally. 

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
uv run tur switch
```

### 14. Export Persona (`export`)

**Portability:** Packages a global persona's core configuration and universal memories into a portable `.tur` gzip-compressed archive (excluding project-local incarnation-specific memories).

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
# Export a persona by its name or UUID to a destination file
uv run tur export ariel ariel.tur
```

### 15. Import Persona (`import`)

**Portability:** Unpacks a `.tur` archive and registers it globally as a new persona on the local system. The framework sanitizes all Member paths prior to extraction to guarantee safety against path traversal vulnerabilities.

*Requires a physical TUI/interactive terminal shell (decorated with `@require_human`).*

```shell
# Import a persona from a .tur archive
uv run tur import ariel.tur
```


## Customization

### Theming

You can control the theme of the interactive TUIs (`init` and `switch`) by setting the `TUR_THEME` environment variable.

- **textual-dark (Default):** `export TUR_THEME="textual-dark"`
- **textual-light:** `export TUR_THEME="textual-light"`
- **Gruvbox:** `export TUR_THEME="gruvbox"`
- **nord**: `export TUR_THEME="nord"`