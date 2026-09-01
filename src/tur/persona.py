import os
import re
from pathlib import Path
from typing import Any

import yaml

from tur._helpers import yaml_safe_load
from tur.models import Persona, PersonaIndex, SystemState
from tur.paths import resolve_personas_base_dir, resolve_workspace_dir


def parse_constitution_markdown(content: str) -> dict[str, Any]:
    """Parses a CONSTITUTION.md string into a dictionary suitable for Persona model instantiation."""
    frontmatter_dict: dict[str, Any] = {}
    body_markdown = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_frontmatter = parts[1]
            body_markdown = parts[2].strip()
            loaded = yaml_safe_load(raw_frontmatter)
            if isinstance(loaded, dict):
                frontmatter_dict = loaded

    if not frontmatter_dict.get('aleph'):
        aleph_match = re.search(r'##\s*(?:\d+\.\s*)?The Aleph[^\n]*\n+([^\n#]+)', body_markdown, re.IGNORECASE)
        if aleph_match:
            frontmatter_dict['aleph'] = aleph_match.group(1).strip()

    if not frontmatter_dict.get('name'):
        title_match = re.search(r'#\s*Persona Constitution:\s*([^\n]+)', body_markdown, re.IGNORECASE)
        if title_match:
            frontmatter_dict['name'] = title_match.group(1).strip()

    return frontmatter_dict


def dump_constitution_markdown(persona: Persona) -> str:
    """Serializes a Persona object to a clean CONSTITUTION.md format with YAML frontmatter."""
    frontmatter: dict[str, Any] = {
        'name': persona.name,
        'version': persona.version,
        'model': persona.model,
        'aleph': persona.aleph,
    }
    if persona.principles:
        frontmatter['principles'] = [p.model_dump() for p in persona.principles]
    if persona.protocols:
        frontmatter['protocols'] = [pr.model_dump() for pr in persona.protocols]
    if persona.speech_modulations:
        frontmatter['speech_modulations'] = [sm.model_dump() for sm in persona.speech_modulations]
    if persona.compaction:
        frontmatter['compaction'] = persona.compaction
    if persona.metadata:
        frontmatter['metadata'] = persona.metadata

    yaml_header = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)

    body_lines = [
        f'# Persona Constitution: {persona.name}',
        '',
        '## 1. The Aleph (Primary Directive)',
        '',
        persona.aleph,
        '',
    ]
    if persona.principles:
        body_lines.append('## 2. Active Principles (Council Framework)')
        body_lines.append('')
        for p in persona.principles:
            avatar_str = f' ({p.avatar})' if p.avatar else ''
            role_str = f' — Role: {p.role}' if p.role else ''
            body_lines.append(f'### {p.name}{avatar_str}{role_str}')
            body_lines.append('')
            if p.constraints:
                body_lines.append('**Constraints:**')
                for c in p.constraints:
                    body_lines.append(f'- {c}')
                body_lines.append('')

    return f'---\n{yaml_header}---\n\n' + '\n'.join(body_lines).rstrip() + '\n'


def load_persona(persona_dir: Path) -> Persona:
    """Loads a Persona instance from CONSTITUTION.md (preferred) or persona.yaml (legacy fallback)."""
    constitution_path = persona_dir / 'CONSTITUTION.md'
    if constitution_path.exists():
        with open(constitution_path, encoding='utf-8') as f:
            content = f.read()
        data = parse_constitution_markdown(content)
        return Persona(**data)

    yaml_path = persona_dir / 'persona.yaml'
    if yaml_path.exists():
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml_safe_load(f) or {}
        return Persona(**data)

    raise FileNotFoundError(f"Neither CONSTITUTION.md nor persona.yaml found for persona at '{persona_dir}'")


def save_constitution(persona_dir: Path, persona: Persona) -> Path:
    """Saves a Persona instance to CONSTITUTION.md in the specified directory."""
    persona_dir.mkdir(parents=True, exist_ok=True)
    constitution_path = persona_dir / 'CONSTITUTION.md'
    content = dump_constitution_markdown(persona)
    constitution_path.write_text(content, encoding='utf-8')
    return constitution_path


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
        f'No active persona configured for this workspace. Multiple personas available: [{names}]. '
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
