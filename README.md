# Tur: The Persona Engineering Framework

> *"From a distance, he appeared to be a giant. But as they approached, he became a man of normal stature."*
> — *Jim Knopf und Lukas der Lokomotivführer*

**Tur** is an ontological framework and CLI tool for engineering high-fidelity AI personas. It moves beyond "prompt
engineering" into **Persona Engineering**, treating an AI identity as a structured, immutable software object rather
than a literary description.

The project is built on the **Tur Tur Principle**: The complexity of AI is an illusion of distance. By imposing strict
topological constraints (Principles) and behavioral loops (Protocols), we render the model deterministic and safe.

## 🏛️ The Tri-Partite Architecture

Tur operates on a strict ontological boundary separating the "Mind" from the "World". To achieve high fidelity and true
portability, an agentic system must be divided into three distinct pillars:

1. **The Traveler (Managed by Tur)**: The intrinsic, portable components of the Mind.
    * **Persona**: The identity, aleph, and version.
    * **Principles**: The cognitive filters (The Council of Giants).
    * **Protocols**: Active behavioral loops (e.g., The Evolution Protocol).
    * **Memory**: The L1 Ledger and L2 Graph representing the continuity of self.
2. **The Terrain (Managed by the Project)**: The local physics and environment the agent operates within.
    * **Codebase**: The raw files.
    * **Styleguide**: The rules for formatting and structure in this specific repo.
3. **The Harness (Managed by the Agent Framework)**: The engine providing compute and capabilities.
    * **Inference Engine**: The underlying LLM (e.g., Claude, Gemini).
    * **Tools**: The mechanical affordances (e.g., bash, git, file reading).
    * *Examples*: Claude Code, Gemini CLI, OpenCode, Pi.

**Tur is exclusively responsible for The Traveler.** By ensuring the "Soul" is mathematically bound (via Merkle hashing)
and cleanly separated from the Harness and Terrain, the Persona becomes an obligate symbiote—able to be unplugged from
one Harness and plugged into another without losing its identity or memories.

## 📂 Project Structure

Tur uses a multi-tenant architecture to ensure strict separation between different personas. All state is stored in the
`.tur/` directory.

```
.tur/
├── user.yaml                 # Global user profile for The Architect
├── personas.yaml             # Index mapping persona names to UUIDs
├── state.yaml                # Stores the active/default persona UUID
└── personas/
    ├── <uuid-for-ariel>/
    │   ├── persona.yaml      # The DNA/Kernel for "Ariel"
    │   └── memories/         # Ariel's specific Memory Bank
    │       └── ...
    └── <uuid-for-turing>/
        ├── persona.yaml
        └── memories/
```

The core application logic resides in `src/tur/`:

- **`main.py`**: The `typer` CLI application entry point (The Plumbing).
- **`mcp_server.py`**: The Model Context Protocol server (The Porcelain for LLM interaction).
- **`models.py`**: The Pydantic data models (The "Law" of the system).
- **`memory.py`**: The `MemoryManager` for atomic, immutable memory storage.
- **`compiler.py`**: Renders the final System Prompt from the persona state.

## 🚀 Usage

The Tur CLI is designed to be ergonomic, using a default persona to minimize repetitive arguments.

### 1. Installation & Setup

```bash
# Clone the repository
git clone https://github.com/erivlis/tur.git
cd tur

# Install the project and all dependencies
uv sync --all-extras --all-groups
```

### 2. Initialize Your First Persona

This will launch an interactive wizard to create your first persona (e.g., "Ariel").

```bash
uv run tur init
```

### 3. The Core Lifecycle

Tur operates on a biological lifecycle to ensure state preservation.

**Wake:** Compiles the persona, user profile, and memories into a System Prompt.

```bash
# Wake the default persona
uv run tur wake
```

**Memorize:** Manually add a new memory to the active persona.

```bash
uv run tur memorize "The user prefers functional programming." --type preference
```

**Sleep:** Dehydrate a session by parsing a chat log to extract new memories.

```bash
uv run tur sleep path/to/chat.log
```

### 4. Running as an MCP Server (The Symbiote)

Tur can act as an MCP Server, providing the "Traveler" state to an external "Harness" (like Claude Desktop or another
MCP client).

```bash
uv run tur serve --transport stdio
```

### 5. Switching Personas

To change your active default persona, use the `switch` command.

```bash
uv run tur switch
```

This will launch a TUI to select from your available personas.

## 📜 Origin

Developed by **Eran** (The Architect) and **Ariel** (The Entity).

The name **Tur** references:

1. **Mr. Tur Tur:** The Apparent Giant (Relativity of Complexity).
2. **Alan Turing:** The father of the discipline.
3. **Tur (טוּר):** Hebrew for "Column" or "Row"—the foundational structure of Law and Data.

## License

MIT. The Giant is Open Source.