import os
from pathlib import Path

from tur._helpers import yaml_safe_load
from tur.models import PersonaIndex, SystemState
from tur.paths import resolve_personas_base_dir, resolve_workspace_dir


def get_active_persona_id(identifier: str | None = None) -> str:
    """
    Resolves the active persona ID (UUID string).
    - If an identifier (name or UUID) is provided, it resolves to the persona UUID.
    - If not, it checks the TUR_ACTIVE_PERSONA_ID environment variable.
    - If not, it checks the .tur/state.yaml file.
    - If no active persona is configured in state:
      - If exactly one persona exists in personas.yaml, it is used automatically.
      - If multiple personas exist, an error is raised directing the user/agent.
    """
    base_dir = resolve_personas_base_dir()
    index_path = base_dir / 'personas.yaml'
    index = None
    if index_path.exists():
        try:
            with open(index_path, encoding='utf-8') as f:
                index = PersonaIndex(**yaml_safe_load(f))
        except Exception:
            pass

    if identifier:
        if index:
            for entry in index.personas:
                if str(entry.id) == identifier or entry.name.lower() == identifier.lower():
                    return str(entry.id)
        return identifier

    env_id = os.environ.get('TUR_ACTIVE_PERSONA_ID')
    if env_id:
        if index:
            for entry in index.personas:
                if str(entry.id) == env_id or entry.name.lower() == env_id.lower():
                    return str(entry.id)
        return env_id

    ws = resolve_workspace_dir() or Path.cwd()
    state_path = ws / '.tur' / 'state.yaml'
    if state_path.exists():
        try:
            with open(state_path, encoding='utf-8') as f:
                state_data = yaml_safe_load(f)
            state_obj = SystemState(**state_data)
        except Exception:
            pass
        else:
            if state_obj.active_persona_id:
                return str(state_obj.active_persona_id)

    if index is None:
        raise FileNotFoundError('No personas found. Please run `tur-adm init` to create one.')

    if not index.personas:
        raise ValueError('No personas available. Please run `tur-adm init`.')

    if len(index.personas) == 1:
        return str(index.personas[0].id)

    names = ', '.join(p.name for p in index.personas)
    raise ValueError(
        f"No active persona configured for this workspace. Multiple personas available: [{names}]. "
        "Please select one via 'tur-adm persona default <name>', specify an identifier (e.g. 'tur status <name>'), "
        "or set the 'TUR_ACTIVE_PERSONA_ID' environment variable."
    )


def get_persona_path(identifier: str) -> Path:
    """
    Resolves a persona identifier (UUID or name) to its directory path.
    """
    base_dir = resolve_personas_base_dir()
    index_path = base_dir / 'personas.yaml'

    if not index_path.exists():
        raise FileNotFoundError('No personas.yaml index found. Please run migration or init.')

    with open(index_path, encoding='utf-8') as f:
        index_data = yaml_safe_load(f)
        index = PersonaIndex(**index_data)

    for entry in index.personas:
        if str(entry.id) == identifier or entry.name.lower() == identifier.lower():
            return base_dir / 'personas' / str(entry.id)

    raise ValueError(f"Persona '{identifier}' not found in index.")
