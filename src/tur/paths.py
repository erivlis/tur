"""
Shared OS-native path resolution utilities for Tur.

Single canonical source for global/local path predicates, workspace resolution,
and registry resolution.
All other modules import from here — no inline copies permitted.
Implements EP-0128 with platformdirs, hardened with container fallbacks and POSIX permissions.
"""

import contextlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from platformdirs import PlatformDirs

logger = logging.getLogger(__name__)

APP_NAME = 'tur'
APP_AUTHOR = False  # Suppress Windows publisher folder duplication (AppData/Local/tur vs tur/tur)

# Module-level PlatformDirs instance avoiding per-call object allocations
_PLATFORM_DIRS = PlatformDirs(
    appname=APP_NAME,
    appauthor=APP_AUTHOR,
    roaming=False,
    opinion=True,
)


def resolve_runtime_dir() -> Path:
    """Resolve ephemeral runtime directory for IPC sockets, signal queues, and locks.

    Paths:
      Linux:   /run/user/<uid>/tur (or $XDG_RUNTIME_DIR/tur)
      macOS:   ~/Library/Caches/TemporaryItems/tur
      Windows: %LOCALAPPDATA%\\Temp\\tur

    Container / Headless Fallback:
      If /run/user/<uid> is missing or read-only (e.g. minimal Docker/CI),
      falls back to tempfile.gettempdir() / f"tur-runtime-{uid}".
    """
    env_runtime = os.environ.get('TUR_RUNTIME_DIR')
    if env_runtime:
        p = Path(env_runtime).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    try:
        runtime_dir = _PLATFORM_DIRS.user_runtime_path
        runtime_dir.mkdir(parents=True, exist_ok=True)

        # Apply POSIX 0700 permission mask for multi-user IPC socket security
        if hasattr(os, 'chmod') and os.name != 'nt':
            with contextlib.suppress(OSError):
                os.chmod(runtime_dir, 0o700)
        return runtime_dir.resolve()
    except (OSError, PermissionError) as exc:
        uid = os.getuid() if hasattr(os, 'getuid') else 'win'
        fallback = Path(tempfile.gettempdir()) / f'tur-runtime-{uid}'
        fallback.mkdir(parents=True, exist_ok=True)
        if hasattr(os, 'chmod') and os.name != 'nt':
            with contextlib.suppress(OSError):
                os.chmod(fallback, 0o700)
        logger.debug(f'Runtime dir fallback engaged: {fallback} (due to {exc})')
        return fallback.resolve()


def resolve_cache_dir() -> Path:
    """Resolve directory for ephemeral introspection indexes and graph caches."""
    env_cache = os.environ.get('TUR_CACHE_DIR')
    if env_cache:
        p = Path(env_cache).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    cache_dir = _PLATFORM_DIRS.user_cache_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir.resolve()


def resolve_log_dir() -> Path:
    """Resolve directory for diagnostic logs, telemetry metrics, and traces."""
    env_log = os.environ.get('TUR_LOG_DIR')
    if env_log:
        p = Path(env_log).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    log_dir = _PLATFORM_DIRS.user_log_path
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir.resolve()


def resolve_data_dir() -> Path:
    """Resolve global user data directory for permanent persona definitions."""
    return get_global_tur_dir()


def get_global_tur_dir() -> Path:
    """Returns the user-global directory for Tur state, respecting TUR_HOME / TUR_DATA_DIR."""
    env_home = os.environ.get('TUR_HOME') or os.environ.get('TUR_DATA_DIR')
    if env_home:
        return Path(env_home).expanduser().resolve()
    return (Path.home() / '.tur').resolve()


def is_global_path(p: Path) -> bool:
    """Returns True if *p* lives inside user-global data, runtime, log, or cache stores."""
    resolved_p = p.resolve()
    for root_getter in (resolve_data_dir, resolve_cache_dir, resolve_runtime_dir, resolve_log_dir):
        try:
            resolved_p.relative_to(root_getter())
        except (ValueError, Exception):
            pass
        else:
            return True
    try:
        resolved_p.relative_to((Path.home() / '.tur').resolve())
    except (ValueError, Exception):
        return False
    else:
        return True


def resolve_workspace_dir(ctx: Any | None = None) -> Path | None:
    """Deterministically resolves the active workspace / Terrain directory.

    Resolution Order:
      1. Explicit environment variable: TUR_PROJECT_DIR (if set and points to an existing directory)
      2. MCP Client Roots: ctx (when running under MCP)
      3. Process Invocation CWD: Path.cwd() (if it contains .tur or is a valid directory with state)
      4. None (Pure Traveler mode - no local terrain attached)
    """
    # 1. Explicit environment variable
    env_dir = os.environ.get('TUR_PROJECT_DIR')
    if env_dir:
        p = Path(env_dir).resolve()
        if p.exists() and p.is_dir():
            return p

    # 2. MCP Client Roots
    if ctx is not None:
        roots = getattr(ctx, 'roots', None)
        if not roots and hasattr(ctx, 'session'):
            roots = getattr(ctx.session, 'roots', None)
        if roots and isinstance(roots, list) and len(roots) > 0:
            root_item = roots[0]
            root_uri = getattr(root_item, 'uri', root_item)
            if str(root_uri).startswith('file://'):
                parsed = urlparse(str(root_uri))
                path_str = unquote(parsed.path)
                if os.name == 'nt' and path_str.startswith('/') and len(path_str) > 2 and path_str[2] == ':':
                    path_str = path_str.lstrip('/')
                root_path = Path(path_str).resolve()
                if root_path.exists() and root_path.is_dir():
                    return root_path

    # 3. Process Invocation CWD (if it contains .tur)
    cwd = Path.cwd().resolve()
    if (cwd / '.tur').exists() and (cwd / '.tur').is_dir():
        return cwd

    # 4. Pure Traveler fallback
    return None


def resolve_personas_base_dir(ctx: Any | None = None) -> Path:
    """Returns the base directory that contains personas.yaml and personas/.

    Resolution order (global-first):
      1. resolve_data_dir() — if personas.yaml exists there (the global registry)
      2. .tur/    — project-local fallback (pre-migration or test environments)
    """
    global_base = resolve_data_dir()
    if (global_base / 'personas.yaml').exists():
        return global_base

    ws = resolve_workspace_dir(ctx)
    if ws is not None and (ws / '.tur' / 'personas.yaml').exists():
        return ws / '.tur'

    local_base = Path('.tur').resolve()
    if (local_base / 'personas.yaml').exists():
        return local_base

    return global_base
