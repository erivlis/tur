---
title: "EP-0114: Global Persona Architecture — Separating Traveler from Local Terrain"
description: "Migrates core persona configurations to a global home directory for zero-friction mobility across repositories."
icon: lucide/globe
status: implemented
---

# EP-0114: Global Persona Architecture — Separating Traveler from Local Terrain

| Field       | Value                                                                |
|:------------|:---------------------------------------------------------------------|
| **EP**      | 0114                                                                 |
| **Title**   | Global Persona Architecture — Separating Traveler from Local Terrain |
| **Author**  | Ariel v5.4.0, The Architect                                          |
| **Status**  | Implemented                                                          |
| **Type**    | Standards Track                                                      |
| **Created** | 2026-05-29                                                           |
| **Updated** | 2026-07-18                                                           |

## Abstract

This proposal decouples the **Traveler** (the persona's core configuration, parameters, and global identity) from the
**Terrain** (the local project repository). By migrating core `persona.yaml` configurations and the global persona
registry to a user-level directory (`~/.tur/`), Tur enables zero-friction portability of AI personas across multiple
local codebases without configuration drift.

## Motivation

Currently, Tur stores persona configurations locally inside each project's `.tur/personas/` directory:

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

This local-first layout introduces three critical friction points:

1. **Configuration Drift:** Updates to a persona's parameters in project A do not propagate to project B.
2. **Migration Friction:** Cloning a persona into a new repository requires physical file copies (`shutil.copytree`),
   duplicating state and cognitive load.
3. **Redundant Identity:** The persona's core identity fragments across isolated project folders, violating the
   principle of a singular, continuously evolving Traveler.

## Rationale (The Council Framework)

1. **The Golem (Containment):** Separating persona identity into a global directory creates a hard physical boundary
   between the Traveler's DNA and any local Terrain. A project cannot accidentally corrupt or overwrite global identity
   state.
2. **Noether (Symmetry):** A single authoritative source of truth for the persona (`~/.tur/personas/[uuid]/`) eliminates
   the asymmetry of multiple diverging local copies. All local workspaces read the same global baseline.
3. **Shannon (Efficiency):** Local repositories remain featherweight — they store only transient execution artifacts
   (sessions, sparks, incarnation memories). The global core avoids redundant duplication of the persona's heavy
   constitutional data across every project.

## Specification

### The Global/Local Split

| Layer               | Path                                  | Contains                                               |
|:--------------------|:--------------------------------------|:-------------------------------------------------------|
| **Global Identity** | `~/.tur/personas/[uuid]/persona.yaml` | Core metadata, directives, parameters, persona version |
| **Global Memory**   | `~/.tur/personas/[uuid]/memories/`    | Memories with `scope: universal` or `scope: user`      |
| **Local State**     | `.tur/state.yaml`                     | Active persona pointer for this workspace              |
| **Local Session**   | `.tur/sessions/`                      | Session notes, sparks, and incarnation-scoped memories |

### Path Resolution Logic

When a CLI command or MCP tool executes:

1. **Persona Identity**: Resolved exclusively from `~/.tur/personas/`. The `persona.yaml` is never read from local
   paths.
2. **Universal Memories**: Read from `~/.tur/personas/[uuid]/memories/`.
3. **Local Incarnation State**: Read and written in the active project's `.tur/` folder.

The canonical path predicates live in `src/tur/paths.py`:

```python
def get_global_tur_dir() -> Path:
    return Path.home() / ".tur"


def resolve_personas_base_dir() -> Path:
    return get_global_tur_dir() / "personas"


def is_global_path(path: Path) -> bool:
    return path.is_relative_to(get_global_tur_dir())
```

No other module may inline these paths; all imports must come from `paths.py`.

### CLI Impact

* **`tur init`**: Creates the persona in `~/.tur/personas/[uuid]/`.
* **`tur wake`**: Compiles the system prompt by fetching the global persona configuration and blending it with the local
  workspace's active session state and incarnation memories.
* **`tur switch`**: Updates `~/.tur/state.yaml` (global default) or `.tur/state.yaml` (local override).

## Backwards Compatibility

* **Breaking Change:** Existing personas stored in local `.tur/personas/` directories must be migrated to
  `~/.tur/personas/`. A one-time migration path is provided via `tur admin migrate` (or equivalent) which copies local
  persona directories to the global store and updates path references.
* **Fallback:** During the transition period, Tur CLI commands may detect legacy local-only personas and emit a
  deprecation warning prompting migration.

## Reference Implementation

* `src/tur/paths.py` — canonical path predicates (`is_global_path`, `resolve_personas_base_dir`,
  `ensure_local_persona_dir`).
* `tests/test_persona.py` — assert that core persona paths resolve to the mocked user home directory, and that two
  separate temp workspaces under the same mock home compile the same global persona but maintain separate local
  sessions.

## Change Log

* **2026-07-18:** Status promoted from Final to Implemented. Global home ~/.tur/personas.yaml path resolution live in
  paths.py; local Terrain fallback with migration warning implemented.
* **2026-05-29:**
    * Initial Draft.
    * Council of Giants review: 5 REJECT / 4 APPROVE WITH CONCERNS. Key remediations applied: tarball path traversal
      fixed, `get_local_persona_dir` split into pure getter + `ensure_local_persona_dir`, export injects `id` from
      index, import rejects archives missing persona `id`, `switch` fixed to global-first resolution.
