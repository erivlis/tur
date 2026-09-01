"""
Interactive terminal prompts and wizards for tur-adm.

Uses standard Rich prompts (Prompt, IntPrompt) for pure, zero-dependency interactive workflows.
"""

import uuid
from pathlib import Path

import yaml
from rich import box
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from tur._helpers import yaml_safe_load
from tur.cli.common import console
from tur.models import Persona, PersonaIndex, PersonaIndexEntry, Principle, SystemState
from tur.paths import resolve_personas_base_dir, resolve_workspace_dir
from tur.persona import save_constitution
from tur.scaffold import scaffold_workspace


def init_wizard() -> str:
    """
    Interactive wizard to bootstrap a new persona using Rich prompts.
    """
    console.print(Panel('[bold cyan]Bootstrap New Persona[/bold cyan]', border_style='cyan'))

    name = Prompt.ask('[bold]Enter Persona Name[/bold] (e.g. Ariel)').strip()
    while not name:
        console.print('[red]Persona name cannot be empty.[/red]')
        name = Prompt.ask('[bold]Enter Persona Name[/bold]').strip()

    aleph = Prompt.ask('[bold]Enter The Aleph (Existential Axiom)[/bold] (e.g. To safeguard reality)').strip()
    while not aleph:
        console.print('[red]The Aleph cannot be empty.[/red]')
        aleph = Prompt.ask('[bold]Enter The Aleph[/bold]').strip()

    default_principles = [
        Principle(name='Symmetry', avatar=None, role='Guardian of Invariance', weight=1.5),
        Principle(name='Safety', avatar=None, role='Containment Protocol', weight=2.0),
    ]
    persona = Persona(
        name=name,
        aleph=aleph,
        principles=default_principles,
        version='0.1.0',
        model='gemini-3.1-pro-preview',
    )

    base_dir = resolve_personas_base_dir()
    personas_dir = base_dir / 'personas'
    index_path = base_dir / 'personas.yaml'
    personas_dir.mkdir(parents=True, exist_ok=True)
    persona_id = uuid.uuid4()
    persona_folder = personas_dir / str(persona_id)
    persona_folder.mkdir(exist_ok=True)

    # Save CONSTITUTION.md (EP-0135) and persona.yaml (backwards compatibility)
    save_constitution(persona_folder, persona)
    file_path = persona_folder / 'persona.yaml'
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(persona.model_dump(mode='json'), f, sort_keys=False)

    if index_path.exists():
        with open(index_path, encoding='utf-8') as f:
            index_data: dict = yaml_safe_load(f) or {'personas': []}
            index = PersonaIndex(**index_data)
    else:
        index = PersonaIndex(personas=[])

    entry = PersonaIndexEntry(id=persona_id, name=persona.name, version=persona.version)
    index.personas.append(entry)

    with open(index_path, 'w', encoding='utf-8') as f:
        yaml.dump(index.model_dump(mode='json'), f, sort_keys=False)

    # Automatically scaffold AGENTS.md in workspace if not already present
    try:
        scaffold_workspace(force=False)
    except FileExistsError:
        pass
    except Exception:
        pass

    msg = f"Persona '{name}' created successfully in .tur/personas/{persona_id}/CONSTITUTION.md"
    console.print(f'[bold green]{msg}[/bold green]')
    return msg


def select_persona_wizard(index: PersonaIndex) -> str | None:
    """
    Interactive wizard to select a persona using a Rich table and IntPrompt.
    Returns the selected persona UUID as a string, or None if cancelled.
    """
    if not index.personas:
        return None

    table = Table(title='Available Personas', box=box.ROUNDED, border_style='cyan')
    table.add_column('#', style='bold cyan', justify='right')
    table.add_column('Name', style='bold green')
    table.add_column('Version', style='dim')
    table.add_column('UUID', style='dim')

    from tur.session import load_system_state

    state_obj = load_system_state()
    active_uuid = str(state_obj.active_persona_id) if state_obj.active_persona_id else None

    for i, p in enumerate(index.personas, 1):
        is_active = ' (Active)' if str(p.id) == active_uuid else ''
        table.add_row(str(i), f'{p.name}{is_active}', f'v{p.version}', str(p.id)[:8] + '…')

    table.add_row('0', '[yellow]Cancel[/yellow]', '', '')
    console.print(table)

    valid_choices = list(range(len(index.personas) + 1))
    choice = IntPrompt.ask(
        'Select active persona',
        choices=[str(c) for c in valid_choices],
        default=1,
    )

    if choice == 0:
        return None

    selected_persona = index.personas[choice - 1]
    return str(selected_persona.id)
