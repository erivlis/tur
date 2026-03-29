# Tur: The Persona Engineering Framework

## Project Overview
**Tur** is an ontological framework and CLI tool for engineering high-fidelity AI personas. It moves beyond "prompt engineering" into **Persona Engineering**, treating an AI identity as a structured, immutable software object rather than a literary description.

The project is built on the **Tur Tur Principle**: The complexity of AI is an illusion of distance. By imposing strict topological constraints (Principles) and behavioral loops (Protocols), we render the model deterministic and safe.

## Architecture
The codebase is a Python CLI application using `typer`, `pydantic`, and `textual`.

*   **`src/tur/main.py`**: The CLI entry point. Handles command routing.
*   **`src/tur/models.py`**: The Constitutional Law. Defines the Pydantic data models (`Persona`, `Memory`, `PersonaIndex`, etc.).
*   **`src/tur/memory.py`**: The `MemoryManager` for atomic, immutable storage of thoughts.
*   **`src/tur/tui.py`**: The `textual`-based wizards for `init` and `switch`.
*   **`.tur/`**: The local state directory, using a multi-tenant structure:
    *   `.tur/personas.yaml`: An index of all available personas.
    *   `.tur/state.yaml`: Stores the currently active default persona.
    *   `.tur/personas/<uuid>/`: A directory for each persona, containing its `persona.yaml` and `memories/` bank.

## Usage & Workflow

The CLI is invoked via `uv run tur <command>`. Most commands operate on the default persona, which can be changed with `tur switch`.

### 1. Initialization
Bootstrap a new persona using the TUI wizard.
```bash
uv run tur init
```

### 2. The Lifecycle (Wake/Sleep/Memorize)
Tur operates on a biological lifecycle to ensure state preservation.
*   **Wake:** Compiles the persona and memories into a System Prompt.
    ```bash
    uv run tur wake
    ```
*   **Memorize:** Manually add a fact or insight to the active persona's memory.
    ```bash
    uv run tur memorize "The user prefers concise code." --type preference
    ```
*   **Sleep:** Dehydrates a session by parsing a chat log to extract new memories.
    ```bash
    uv run tur sleep path/to/session.log
    ```

### 3. Key Commands
*   **List Memories:** `uv run tur memories`
*   **Switch Default Persona:** `uv run tur switch`
*   **Measure Cognitive Load:** `uv run tur telemetry`
*   **Clone a Persona:** `uv run tur clone ariel "Ariel (Test Branch)"`

## Development Conventions
Developers contributing to Tur must adhere to the **Council Principles** defined in `PRINCIPLES.md`. All significant changes must be proposed and documented via the **Enhancement Proposal (EP)** process in the `docs/proposals/` directory.
