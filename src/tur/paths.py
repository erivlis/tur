"""
Shared path resolution utilities.

Single canonical source for the global/local path predicates and registry resolution.
All other modules import from here — no inline copies permitted.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_global_path(p: Path) -> bool:
    """
    Returns True if *p* lives inside the user-global ~/.tur/ store.

    This is the single canonical implementation of the global-path predicate.
    Do NOT duplicate this logic inline elsewhere.
    """
    try:
        p.relative_to(Path.home() / ".tur")
    except ValueError:
        return False
    else:
        return True


def resolve_personas_base_dir() -> Path:
    """
    Returns the base directory that contains personas.yaml and personas/.

    Resolution order (global-first):
      1. ~/.tur/  — if personas.yaml exists there (the global registry)
      2. .tur/    — project-local fallback (pre-migration or test environments)

    A warning is emitted when falling back to local, so callers have
    visibility into which store was resolved.
    """
    global_base = Path.home() / ".tur"
    if (global_base / "personas.yaml").exists():
        return global_base

    local_base = Path(".tur")
    logger.warning(
        "Falling back to local .tur/ registry — "
        "global ~/.tur/personas.yaml not found. "
        "Run migration if this is unexpected."
    )
    return local_base
