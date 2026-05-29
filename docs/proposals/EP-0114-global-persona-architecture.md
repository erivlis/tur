---
title: "EP-0114: Global Persona Architecture: Separating Traveler from Local Terrain"
description: "A proposal to migrate core persona configurations to a global home directory, ensuring zero-friction mobility across repositories."
icon: lucide/globe
status: drafted
---

# EP-0114: Global Persona Architecture: Separating Traveler from Local Terrain

**Date:** 2026-05-29  
**Author:** Ariel v5.4.0 (The Alchemist)  
**Status:** Drafted  

---

## 1. Objective

To decouple the **Traveler** (the persona's core configuration, parameters, and global identity) from the **Terrain** (the local project repository). By migrating core `persona.yaml` configurations and global persona registries to a user-level global directory (`~/.tur/`), we enable zero-friction portability of AI personas across multiple local codebases.

---

## 2. Background & The Problem

Currently, Tur stores persona configurations (such as `persona.yaml`) locally inside each project's `.tur/personas/` directory:

```
local-project/
└── .tur/
    ├── state.yaml
    └── personas/
        └── [persona-uuid]/
            ├── persona.yaml
            ├── memories/
            └── sessions/
```

This local-first configuration introduces three critical friction points:
1. **Configuration Drift:** If a user updates a persona's parameters (e.g., system configuration, version, model settings) in project A, those changes do not replicate to project B.
2. **Migration Friction:** Cloning a persona into a new repository requires physical file copies (`shutil.copytree`), which duplicates state and cognitive load.
3. **Redundant Identity:** The persona's core identity becomes fragmented across multiple isolated project folders, violating the principle of a singular, evolving companion.

---

## 3. Proposed Architecture: The Global/Local Split

We propose a strict architectural separation between **Global Identity** and **Local Incarnation**:

```
Global Directory (~/.tur/)
├── state.yaml                 <-- Global default active persona registry
└── personas/
    └── [persona-uuid]/
        ├── persona.yaml       <-- Core settings, parameters, name, version
        └── memories/
            └── [universal]/   <-- Memories with scope: universal

Local Project Directory (C:/dev/my-project/.tur/)
├── state.yaml                 <-- Local session state
└── sessions/                  <-- Project-specific session notes and sparks
└── memories/
    └── [incarnation]/         <-- Memories with scope: incarnation
```

### Path Resolution Logic

When an agent or CLI command is executed:
1. **Persona Identity:** Resolved from the Global directory `~/.tur/personas/`. The core `persona.yaml` is read exclusively from this global store.
2. **Universal Memories:** Read from the Global persona's memory bank: `~/.tur/personas/[uuid]/memories/`.
3. **Local Incarnation State:** Read and written locally inside the active project workspace's `.tur/` folder. This includes local sessions, session notes (`notes.yaml`), sparks, and project-specific incarnation memories.

---

## 4. Proposed Changes

### 4.1. `src/tur/persona.py`
Modify `get_persona_path` and persona discovery to resolve paths globally:

```python
def get_global_tur_dir() -> Path:
    """Returns the global user-level Tur directory (~/.tur/)."""
    return Path.home() / ".tur"

def get_persona_path(identifier: str) -> Path:
    """
    Locates a persona's core directory globally.
    Falls back to local if legacy mode requires it.
    """
    global_dir = get_global_tur_dir() / "personas"
    
    # 1. Search globally by UUID or Name
    # ...
```

### 4.2. `src/tur/cli.py` & `src/tur/mcp_server.py`
Update CLI commands (`init`, `status`, `switch`) to write core configurations to the global home directory, while reserving local workspaces strictly for local execution files.

* **`tur init`**: Creates the persona in the global directory `~/.tur/personas/[uuid]`.
* **`tur wake`**: Compiles the prompt by fetching the global persona configuration and blending it with the local project's active session state and incarnation memories.

---

## 5. Benefits

1. **Zero-Friction Portability:** To activate Ariel in a new repository (e.g., `mappingtools`), simply run `tur wake Ariel`. Tur instantly initializes a lightweight local `.tur/` folder and links it to the global Ariel persona.
2. **No Configuration Drift:** A single, authoritative source of truth for Ariel's identity lives on the machine.
3. **Clean Boundaries:** Local repositories remain lightweight, storing only local development context, while the global core remains clean of project-specific clutter.

---

## 6. Verification Plan

### Automated Tests
* Update `test_persona.py` to assert that core persona paths resolve to the mocked user home directory instead of the project root.
* Verify that running `tur wake` in two different temporary directories under the same mocked home directory successfully compiles the identical global persona but starts separate local sessions.
