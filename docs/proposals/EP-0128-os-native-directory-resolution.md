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

Refactor `paths.py` to expose distinct resolution primitives according to storage category, hardened with container fallbacks and POSIX permissions:

```python
from functools import lru_cache
import logging
import os
from pathlib import Path
import tempfile
from typing import Any
import platformdirs

logger = logging.getLogger(__name__)

APP_NAME = "tur"
APP_AUTHOR = False  # Avoid Windows/Linux hierarchy mismatch unless strictly required


@lru_cache(maxsize=16)
def resolve_runtime_dir() -> Path:
    """Resolve ephemeral runtime directory for IPC sockets, signal queues, and locks.
    
    Linux: /run/user/<uid>/tur (or $XDG_RUNTIME_DIR/tur)
    macOS: ~/Library/Caches/TemporaryItems/tur
    Windows: %LOCALAPPDATA%\\Temp\\tur
    
    Container / Headless Fallback:
      If /run/user/<uid> is missing or read-only (e.g. minimal Docker/CI),
      falls back to tempfile.gettempdir() / f"tur-runtime-{uid}".
    """
    env_runtime = os.environ.get("TUR_RUNTIME_DIR")
    if env_runtime:
        p = Path(env_runtime).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    try:
        runtime_dir = Path(
            platformdirs.user_runtime_dir(
                appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
            )
        )
        # Apply POSIX 0700 permission mask for multi-user security
        if hasattr(os, "chmod") and os.name != "nt":
            try:
                os.chmod(runtime_dir, 0o700)
            except OSError:
                pass
        return runtime_dir
    except (OSError, PermissionError) as exc:
        uid = os.getuid() if hasattr(os, "getuid") else "win"
        fallback = Path(tempfile.gettempdir()) / f"tur-runtime-{uid}"
        fallback.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "chmod") and os.name != "nt":
            try:
                os.chmod(fallback, 0o700)
            except OSError:
                pass
        logger.debug(f"Runtime dir fallback engaged: {fallback} (due to {exc})")
        return fallback


@lru_cache(maxsize=16)
def resolve_cache_dir() -> Path:
    """Resolve directory for ephemeral introspection indexes and telemetry cache."""
    env_cache = os.environ.get("TUR_CACHE_DIR")
    if env_cache:
        p = Path(env_cache).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    cache_dir = Path(
        platformdirs.user_cache_dir(
            appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
        )
    )
    return cache_dir


@lru_cache(maxsize=16)
def resolve_data_dir() -> Path:
    """Resolve global user data directory for permanent persona definitions."""
    env_home = os.environ.get("TUR_HOME") or os.environ.get("TUR_DATA_DIR")
    if env_home:
        return Path(env_home).expanduser().resolve()

    legacy_home = Path.home() / ".tur"
    if (legacy_home / "personas.yaml").exists() or (legacy_home / "personas").exists():
        return legacy_home

    return Path(
        platformdirs.user_data_dir(
            appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True
        )
    )


def is_global_path(p: Path) -> bool:
    """Returns True if *p* lives inside user-global data, runtime, or cache stores.
    
    Tests against TUR_HOME, legacy ~/.tur/, resolve_data_dir(), resolve_cache_dir(),
    and resolve_runtime_dir().
    """
    resolved_p = p.resolve()
    for root_getter in (resolve_data_dir, resolve_cache_dir, resolve_runtime_dir):
        try:
            resolved_p.relative_to(root_getter())
            return True
        except (ValueError, Exception):
            pass
    try:
        resolved_p.relative_to((Path.home() / ".tur").resolve())
        return True
    except (ValueError, Exception):
        return False


def resolve_workspace_dir(ctx: Any | None = None) -> Path | None:
    """Deterministically resolves active workspace / Terrain directory.
    
    INVARIANT (EP-0124): Workspace state is ALWAYS strictly co-located inside
    <workspace_root>/.tur/ and NEVER redirects to global platformdirs paths.
    """
    ...
```

### 3. Subsystem Storage Mapping

| Category                | Subsystem / Files                   | Target Path Function          | OS Example (Linux / Windows)                            |
|:------------------------|:------------------------------------|:------------------------------|:--------------------------------------------------------|
| **Workspace Terrain**   | Incarnational OKF, Session Notes    | `resolve_workspace_dir()`     | `<repo>/.tur/` *(Inviolable)*                           |
| **Global Traveler**     | Personas, Universal Memory          | `resolve_data_dir()`          | `~/.local/share/tur/` / `%APPDATA%\tur\` (or `~/.tur/`) |
| **Swarm IPC / Sockets** | SQLite Signal DB, Whiteboard, Locks | `resolve_runtime_dir()`       | `/run/user/1000/tur/` / `%LOCALAPPDATA%\Temp\tur\`      |
| **Telemetry & Cache**   | Graph indexes, Token cost metrics   | `resolve_cache_dir()`         | `~/.cache/tur/` / `%LOCALAPPDATA%\tur\Cache\`           |

## Backwards Compatibility

* **Legacy `~/.tur/` Preserved:** The resolution pipeline automatically detects and respects existing `~/.tur/personas.yaml`
  or `~/.tur/personas/` directories, guaranteeing zero breakage for existing setups.
* **Environment Overrides:** `TUR_HOME`, `TUR_DATA_DIR`, `TUR_RUNTIME_DIR`, and `TUR_CACHE_DIR` take top precedence, allowing custom deployment paths in
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

## Open Questions & Council Directives

- [ ] **Container Fallback Testing (Popper & Bacon):** Assert that headless environments with missing `/run/user/<uid>` fall back cleanly to `tempfile.gettempdir() / f"tur-runtime-{uid}"` with 100% test coverage.
- [ ] **Global Path Predicate Completeness (Steward):** Verify that `is_global_path()` correctly identifies paths inside `platformdirs.user_data_dir()`.
- [ ] Should `tur-adm purge-cache` be introduced as a dedicated CLI command leveraging `resolve_cache_dir()`?

## Change Log

* **2026-08-25:**
    * Integrated Council of Giants Review hardening mandates: container `/run/user` fallback, POSIX `0700` runtime permissions, `@lru_cache` memoization, symmetric `TUR_RUNTIME_DIR`/`TUR_CACHE_DIR` environment overrides, and `is_global_path` coverage update.
    * Initial Draft proposing `platformdirs` integration for OS-native directory standards and ephemeral runtime IPC
      isolation.
