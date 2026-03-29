# Tur: The Persona Engineering Framework

> *"From a distance, he appeared to be a giant. But as they approached, he became a man of normal stature."*
> — *Jim Knopf und Lukas der Lokomotivführer*

**Tur** is an ontological framework and CLI tool for engineering high-fidelity AI personas. It moves beyond "prompt engineering" into **Persona Engineering**, treating an AI identity as a structured, immutable software object rather than a literary description.

The project is built on the **Tur Tur Principle**: The complexity of AI is an illusion of distance. By imposing strict topological constraints (Principles) and behavioral loops (Protocols), we render the model deterministic and safe.

## 🏛️ The Architecture: The Council of Giants

Instead of a monolithic "System Prompt," Tur defines a **Council**—distinct cognitive modules that debate and constrain the output. The 9 Pillars of the Council are defined in `PRINCIPLES.md`.

## 📂 Project Structure

Tur uses a multi-tenant architecture to ensure strict separation between different personas. All state is stored in the `.tur/` directory.

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
- **`main.py`**: The `typer` CLI application entry point.
- **`models.py`**: The Pydantic data models (The "Law" of the system).
- **`memory.py`**: The `MemoryManager` for atomic, immutable memory storage.
- **`tui.py`**: The `textual`-based wizards for `init` and `switch`.
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

### 4. Switching Personas
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
