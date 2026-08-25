---
title: "EP-0128: OS-Native Directory Resolution and Runtime Storage Standards"
description: "Adopts platformdirs to standardize cross-platform OS directory resolution for runtime IPC sockets, caches, and global persona state while preserving workspace terrain isolation."
icon: lucide/folder-tree
status: draft
---

# EP-0128: OS-Native Directory Resolution and Runtime Storage Standards

| Field       | Value                                                        |
|:------------|:-------------------------------------------------------------|
| **EP**      | 0128                                                         |
| **Title**   | OS-Native Directory Resolution and Runtime Storage Standards |
| **Author**  | Eran Rivlis & Ariel                                          |
| **Status**  | Draft                                                        |
| **Type**    | Standards Track                                              |
| **Created** | 2026-08-25                                                   |
| **Updated** | 2026-08-25                                                   |

## Abstract

This proposal specifies the integration of the zero-dependency [`platformdirs`](https://github.com/tox-dev/platformdirs)
library into Tur's core runtime. It establishes canonical, cross-platform standards for resolving OS-native user data,
runtime IPC sockets, temporary lock files, and cache directories across Linux (XDG), macOS, and Windows. Crucially, it
codifies the boundary between global OS-level directories and local workspace storage, ensuring full compliance with
**EP-0124 (Terrain Isolation)**.

## Motivation

As Tur evolves towards multi-agent swarm coordination (EP-0118, EP-0122, EP-0123) and multi-tenant persona management
(EP-0114), the framework must manage multiple distinct classes of file system state:

1. **Transient Runtime & IPC State:** Named pipes, socket files, PID locks, and active signal databases (`.signals.db`)
   used by the Inter-Agent Signal Protocol (IASP). Placing these in permanent user directories risks stale state
   surviving reboots and system crashes.
2. **Ephemeral Cache State:** Deductive memory graph indexes, telemetry aggregation logs, and temporary template
   compilation artifacts that can be safely purged by OS disk-cleanup utilities.
3. **Global Persona Configurations (The Traveler):** Cross-project persona definitions and universal memory banks that
   belong in standard user config/data directories.
4. **Local Workspace State (The Terrain):** Project-specific session notes and incarnational OKF memory that must remain
   strictly within the workspace repository.

Currently, Tur relies on ad-hoc `Path.home() / ".tur"` paths for global lookups, which ignores platform conventions
(e.g., `%LOCALAPPDATA%` on Windows, `~/Library/Application Support/` on macOS, and XDG specs on Linux). By adopting
`platformdirs`, Tur eliminates platform-specific path boilerplate while achieving robust runtime isolation.

## Rationale

### Council Alignment

* **The Noether Module (Symmetry & Invariance):** `platformdirs` provides symmetrical directory resolution across POSIX,
  macOS, and Windows platforms without custom `sys.platform` branches or OS-specific path parsing hacks.
* **The Golem Protocol (Containment & Boundaries):** Clearly segregates ephemeral runtime data (`user_runtime_dir`) and
  cache (`user_cache_dir`) from permanent identity DNA (`user_data_dir`), preventing corrupted caches from polluting
  core persona memory.
* **The Steward Principle (Harmony & Pragmatism):** `platformdirs` is a zero-dependency, lightweight, and universally
  trusted Python standard library maintained by the PyPA/tox-dev ecosystem.
* **The Shannon Module (Efficiency):** Offloading platform-specific directory conventions to a dedicated library reduces
  internal codebase complexity and test matrix surface area.

## Specification

### 1. Core Dependency (`pyproject.toml`)

Add `platformdirs` to core `dependencies`:

```toml
[project]
dependencies = [
    "typer>=0.12.0",
    "pydantic>=2.6.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0.0",
    "rich>=13.0.0",
    "networkx>=3.6",
    "platformdirs>=4.2.0",
]
```

### 2. Path Resolution Architecture (`src/tur/paths.py`)

Refactor `paths.py` to expose distinct resolution primitives according to storage category:

```python
import os
from pathlib import Path
import platformdirs

APP_NAME = "tur"
APP_AUTHOR = "erivlis"


def resolve_runtime_dir() -> Path:
    """Resolve ephemeral runtime directory for IPC sockets, signal queues, and locks.
  
    Linux: /run/user/<uid>/tur (or $XDG_RUNTIME_DIR/tur) macOS:
    ~/Library/Caches/TemporaryItems/tur Windows: %LOCALAPPDATA%\\Temp\\tur
    """
    runtime_dir = Path(
        platformdirs.user_runtime_dir(
            appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
        )
    )
    return runtime_dir


def resolve_cache_dir() -> Path:
    """Resolve directory for ephemeral introspection indexes and telemetry cache."""
    cache_dir = Path(
        platformdirs.user_cache_dir(
            appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
        )
    )
    return cache_dir


def resolve_personas_base_dir() -> Path:
    """Resolve global personas base directory.
  
    Resolution Priority:
    1. TUR_HOME / TUR_PERSONAS_DIR environment override
    2. Legacy ~/.tur/personas/ (if exists, for backwards compatibility)
    3. platformdirs.user_data_dir("tur") / "personas"
    """
    env_home = os.environ.get("TUR_HOME") or os.environ.get("TUR_PERSONAS_DIR")
    if env_home:
        return Path(env_home).expanduser().resolve()

    legacy_home = Path.home() / ".tur" / "personas"
    if legacy_home.exists():
        return legacy_home

    data_dir = Path(
        platformdirs.user_data_dir(
            appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
        )
    )
    return data_dir / "personas"


def resolve_workspace_dir(
        target_path: Path | None = None,
) -> tuple[Path, Path | None]:
    """Resolve workspace repository root and its co-located .tur/ terrain state.
  
    INVARIANT (EP-0124): Workspace state is ALWAYS strictly co-located inside
    <workspace_root>/.tur/ and NEVER redirects to global platformdirs paths.
    """
    ...
```

### 3. Subsystem Storage Mapping

| Category                | Subsystem / Files                   | Target Path Function          | OS Example (Linux / Windows)                            |
|:------------------------|:------------------------------------|:------------------------------|:--------------------------------------------------------|
| **Workspace Terrain**   | Incarnational OKF, Session Notes    | `resolve_workspace_dir()`     | `<repo>/.tur/` *(Inviolable)*                           |
| **Global Traveler**     | Personas, Universal Memory          | `resolve_personas_base_dir()` | `~/.local/share/tur/` / `%APPDATA%\tur\` (or `~/.tur/`) |
| **Swarm IPC / Sockets** | SQLite Signal DB, Whiteboard, Locks | `resolve_runtime_dir()`       | `/run/user/1000/tur/` / `%LOCALAPPDATA%\Temp\tur\`      |
| **Telemetry & Cache**   | Graph indexes, Token cost metrics   | `resolve_cache_dir()`         | `~/.cache/tur/` / `%LOCALAPPDATA%\tur\Cache\`           |

## Backwards Compatibility

* **Legacy `~/.tur/` Preserved:** The resolution pipeline automatically detects and respects existing `~/.tur/personas/`
  directories, guaranteeing zero breakage for existing setups.
* **Environment Overrides:** `TUR_HOME` and `TUR_PERSONAS_DIR` take top precedence, allowing custom deployment paths in
  CI/CD and sandboxes.
* **Terrain Isolation (EP-0124):** No changes are made to local `<repo>/.tur/` resolution.

## How to Teach This / Documentation Plan

* Update `docs/concepts/harness-integration.md` and `docs/concepts/fractal-memory.md` to document global path resolution
  and runtime socket locations.
* Update `AGENTS.md` to reference `TUR_HOME` environment overrides.

## Reference Implementation

Drafted across `src/tur/paths.py` and integrated into `src/tur/session.py` signal storage.

## Rejected Ideas

* **Moving Workspace State into OS Data Directories:** Strictly rejected. Storing repository memories inside global user
  directories violates EP-0124 (Terrain Isolation) and prevents version-controlled project memory sharing.
* **Writing Custom Platform Branching Logic:** Rejected. Maintaining bespoke OS path resolvers violates the Shannon and
  Steward principles when `platformdirs` is already the battle-tested standard.

## Open Questions

- [ ] Should `tur-adm purge-cache` be introduced as a dedicated CLI command leveraging `resolve_cache_dir()`?

## Change Log

* **2026-08-25:**
    * Initial Draft proposing `platformdirs` integration for OS-native directory standards and ephemeral runtime IPC
      isolation.
