# Usage Guide

Tur is a lightweight, deterministic CLI that manages the lifecycle of your AI personas. It treats an AI identity as a
structured, immutable software object.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
# Clone the repository
git clone https://github.com/yourusername/tur.git
cd tur

# Install the project and dependencies
uv sync
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

```bash
uv run tur init
```

### 2. Wake the Persona (`wake`)

**The Awakening:** Compiles the static DNA (`persona.yaml`), the User Context (`user.yaml`), and the Memory Bank into a
complete "System Prompt" ready to be fed to an LLM.

```bash
# Wake the default persona
uv run tur wake

# Wake a specific persona
uv run tur wake ariel
```

### 3. Memorize (`memorize`)

**Active Learning:** Manually inject a specific insight, fact, or preference directly into the active persona's Memory
Bank during a session.

```bash
uv run tur memorize "The user prefers functional programming over OOP." --type preference --scope user

# Or for a specific persona:
uv run tur memorize "Code must be perfectly symmetrical." ariel --type axiom
```

### 4. Sleep & Consolidate (`sleep`)

**Dehydration:** Extracts insights, facts, and axioms from a raw chat log to update the long-term Memory Bank. It uses
an LLM (acting as the Subconscious) to parse the log and structure the data.

*Note: Requires the `GEMINI_API_KEY` environment variable to be set.*

```bash
uv run tur sleep path/to/chat.log

# Or for a specific persona:
uv run tur sleep path/to/chat.log ariel
```

### 5. View Memories (`memories`)

Inspect the contents of the Memory Bank. This lists all active memories that will be included during the next `wake`
cycle.

```bash
uv run tur memories
```

To include archived (forgotten) memories in the list:

```bash
uv run tur memories --include-archived
```

### 6. Measure Cognitive Load (`telemetry`)

Calculates the "Constraint Dimensionality" ($C_p$) of a persona based on its principles and weights. This helps you
understand if your persona's ruleset is becoming too complex for an LLM to handle reliably.

```bash
uv run tur telemetry
```

### 7. Forget a Memory (`forget`)

Archives a specific memory by its UUID, removing it from the active context window. The memory is moved to an `archive/`
folder and is no longer loaded during `wake`.

```bash
# You must provide the Memory ID
uv run tur forget <memory-uuid>

# For a non-default persona:
uv run tur forget <memory-uuid> ariel
```

### 8. Clone a Persona (`clone`)

Duplicates an existing persona into a new identity with a new UUID. This is useful for creating specialized branches of
a persona without polluting the original's memory bank.

```bash
uv run tur clone ariel "Ariel (Coding Mode)"
```

## Customization

### Theming

You can control the theme of the interactive TUIs (`init` and `switch`) by setting the `TUR_THEME` environment variable.

- **textual-dark (Default):** `export TUR_THEME="textual-dark"`
- **textual-light:** `export TUR_THEME="textual-light"`
- **Gruvbox:** `export TUR_THEME="gruvbox"`
- **nord**: `export TUR_THEME="nord"`
