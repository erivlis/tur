"""
Shared path resolution utilities.

Single canonical source for global/local path predicates, workspace resolution,
and registry resolution.
All other modules import from here — no inline copies permitted.
"""

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)


def get_global_tur_dir() -> Path:
    """
    Returns the user-global ~/.tur directory, respecting TUR_HOME if set.
    """
    env_home = os.environ.get('TUR_HOME')
    if env_home:
        return Path(env_home).resolve()
    return (Path.home() / '.tur').resolve()


def is_global_path(p: Path) -> bool:
    """
    Returns True if *p* lives inside the user-global ~/.tur/ store (or TUR_HOME).

    This is the single canonical implementation of the global-path predicate.
    Do NOT duplicate this logic inline elsewhere.
    """
    resolved_p = p.resolve()
    try:
        resolved_p.relative_to(get_global_tur_dir())
    except ValueError:
        pass
    else:
        return True

    try:
        resolved_p.relative_to((Path.home() / '.tur').resolve())
    except ValueError:
        return False
    else:
        return True


def resolve_workspace_dir(ctx: Any | None = None) -> Path | None:
    """
    Deterministically resolves the active workspace / Terrain directory.

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
    """
    Returns the base directory that contains personas.yaml and personas/.

    Resolution order (global-first):
      1. ~/.tur/ (or TUR_HOME) — if personas.yaml exists there (the global registry)
      2. .tur/    — project-local fallback (pre-migration or test environments)

    A warning is emitted when falling back to local, so callers have
    visibility into which store was resolved.
    """
    global_base = get_global_tur_dir()
    if (global_base / 'personas.yaml').exists():
        return global_base

    ws = resolve_workspace_dir(ctx)
    if ws is not None and (ws / '.tur' / 'personas.yaml').exists():
        return ws / '.tur'

    local_base = Path('.tur').resolve()
    if (local_base / 'personas.yaml').exists():
        return local_base

    return global_base
