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
    * **Documentations**: Any additional context (e.g., this README).
3. **The Harness (Managed by the Agent Framework)**: The engine providing compute and capabilities.
    * **Inference Engine**: The underlying LLM (e.g., Claude, Gemini).
    * **Tools**: The mechanical affordances (e.g., bash, git, file reading).
    * *Examples*: Claude Code, Gemini CLI, OpenCode, Pi, etc.

**Tur is exclusively responsible for The Traveler.** By ensuring the "Soul" is mathematically bound (via Merkle
hashing), cleanly decoupled from anthropomorphic engine leaks, and separated from the Harness and Terrain, the Persona
becomes an obligate symbiote—able to be unplugged from one Harness and plugged into another without losing its identity
or memories.

## 📂 Project Structure

Tur uses a multi-tenant architecture to ensure strict separation between different personas. All state is stored in the
`.tur/` directory.

### Local vs. Global Scope

Tur respects a standard configuration hierarchy:

* **Global (`~/.tur/`)**: The universal state for your system. This is where your master `user.yaml` (The Architect's
  profile) lives.
* **Local (`./.tur/`)**: The repository-specific state. If you initialize Tur inside a project, it creates a local
  `.tur/` folder containing the Personas bound to that specific Terrain. A local `user.yaml` here will override the
  global profile.

```
./.tur/
├── user.yaml                 # Local user profile override
├── personas.yaml             # Index mapping persona names to UUIDs
├── state.yaml                # Stores the active/default persona UUID
└── personas/
    ├── <persona-uuid-1>/
    │   ├── persona.yaml      # The DNA/Kernel for the persona
    │   ├── sessions.yaml     # The session index
    │   ├── sessions/         # Flat session files
    │   │   ├── 20260529_185258_143a5bc0.yaml
    │   │   └── 20260529_173616_c2212cf6.yaml
    │   └── memories/         # Content-Addressable Storage (Merkle Memory)
    │       ├── archive/
    │       ├── 20260412_025949_axiom_e1324...yaml
    │       └── 20260418_160825_event_c98f1...yaml
    └── <persona-uuid-2>/
        ├── persona.yaml
        └── memories/
```

The core application logic resides in `src/tur/`:

- **`cli/`**: The package folder housing our split executables: `cli/agent.py` (runtime CLI), `cli/admin.py`
  (administrative TUI), and `cli/mcp.py` (Harness MCP gateway).
- **`mcp_server.py`**: The Model Context Protocol server (The Porcelain for LLM interaction).
- **`models.py`**: The Pydantic data models (The "Law" of the system).
- **`user.py`**: User profile bootstrapping and domain management.
- **`persona.py`**: Active persona resolution and path trace management.
- **`session.py`**: Flat session trackers, session index consolidation, and epilogue note logic.
- **`dreaming.py`**: Insight extraction, memory parsing, and LLM dreaming consolidation.
- **`compiler.py`**: Renders the final System Prompt from the persona state.

## 🚀 Usage

Tur divides its execution footprint along strict Tri-Partite security boundaries using distinct command-line binaries:

### 1. Installation & Setup

```shell
# Clone the repository
git clone https://github.com/erivlis/tur.git
cd tur

# Install standard agent runtime dependencies ONLY (Safe Sandbox)
uv sync

# Or install all developer and TUI extras (Human Governance)
uv sync --all-extras --all-groups
```

### 2. Initialize Your First Persona

This launches the administrative TUI wizard. Since this is an administrative action, it is physically isolated inside
`tur-adm`:

```shell
uv run tur-adm persona init
```

### 3. The Core Lifecycle (Agent-Facing)

The agent interacts with the lightweight `tur` binary inside its sandboxed virtual environment:

**Wake:** Compiles the active persona state into a compiled System Prompt.

```shell
uv run tur wake
```

**Learn:** Manually injects a memory.

```shell
uv run tur learn "The user prefers functional programming." --type preference
```

**Recall:** Keyword semantic search.

```shell
uv run tur recall "functional"
```

**Sleep:** Dehydrates the session and extracts memories.

```shell
uv run tur sleep path/to/chat.log
```

### 4. Running the Harness Gateway (The MCP Server)

Exposes the Traveler state to the external Harness (e.g., Claude Desktop):

```shell
uv run tur-mcp
```

### 5. Switching Personas (Human-Facing TUI)

Allows the human Architect to change active global/local default personas:

```shell
uv run tur-adm persona switch
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