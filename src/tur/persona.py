import os
from pathlib import Path

import yaml

from tur.models import PersonaIndex, SystemState
from tur.tui import select_persona_wizard


def get_active_persona_id(identifier: str | None = None) -> str:
    """
    Resolves the active persona ID.
    - If an identifier is provided, it's returned.
    - If not, it checks the .tur/state.yaml file.
    - If the state file doesn't exist, it launches a TUI to select and set the default.
    """
    if identifier:
        return identifier

    env_id = os.environ.get("TUR_ACTIVE_PERSONA_ID")
    if env_id:
        return env_id

    state_path = Path(".tur/state.yaml")
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                state_data = yaml.safe_load(f)
            state_obj = SystemState(**state_data)
        except Exception:
            pass
        else:
            if state_obj.active_persona_id:
                return str(state_obj.active_persona_id)

    # If we're here, no default is set, so we launch the selector TUI
    index_path = Path(".tur/personas.yaml")
    if not index_path.exists():
        raise FileNotFoundError("No personas found. Please run `tur init` to create one.")

    with open(index_path, encoding="utf-8") as f:
        index = PersonaIndex(**yaml.safe_load(f))

    if not index.personas:
        import typer
        raise ValueError("No personas available to select. Please run `tur init`.")

    new_active_id = select_persona_wizard(index)
    if not new_active_id:
        import typer
        raise typer.Exit("No persona selected. Aborting.")

    return new_active_id


def get_persona_path(identifier: str) -> Path:
    """
    Resolves a persona identifier (UUID or name) to its directory path.
    """
    base_dir = Path(".tur")
    index_path = base_dir / "personas.yaml"

    if not index_path.exists():
        raise FileNotFoundError("No personas.yaml index found. Please run migration or init.")

    with open(index_path, encoding="utf-8") as f:
        index_data = yaml.safe_load(f)
        index = PersonaIndex(**index_data)

    for entry in index.personas:
        if str(entry.id) == identifier or entry.name.lower() == identifier.lower():
            return base_dir / "personas" / str(entry.id)

    raise ValueError(f"Persona '{identifier}' not found in index.")
