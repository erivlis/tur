import sys

from rich.syntax import Syntax

try:
    import textual
except ImportError:
    from rich.console import Console, Group
    from rich.markup import escape
    from rich.panel import Panel

    console = Console(stderr=True)

    # 1. Create the inner code block

    code = 'pip install tur[admin]\n# or\nuv pip install tur[admin]'

    code_syntax = Syntax(code, 'shell', theme='monokai', line_numbers=True)

    # 2. Wrap the code in its own panel
    code_panel = Panel(code_syntax, title='[cyan]Shell[/cyan]', border_style='cyan', expand=True)

    # 3. Group the introductory text and the code panel together
    panel_contents = Group(
        "[bold red]Error: The 'textual' package is required to run 'tur-adm'.[/bold red]\n\n"
        'Please install the admin extra dependencies by running:\n',
        code_panel,
    )

    # 4. Pass the group into the parent Panel
    console.print(
        Panel(panel_contents, title='[bold red]Dependency Missing[/bold red]', border_style='red', expand=False)
    )
    sys.exit(1)

import io
import shutil
import tarfile
import tempfile
from pathlib import Path
from uuid import UUID

import typer
import yaml
from rich import box
from rich.panel import Panel
from rich.table import Table

from tur import persona, session, tui
from tur.cli.common import console, require_human
from tur.memory import MemoryManager
from tur.models import (
    PersonaIndex,
    SessionNotes,
)
from tur.paths import resolve_personas_base_dir

app = typer.Typer(
    help='Tur: Persona Administrative Governance Suite.',
    context_settings={'help_option_names': ['-h', '--help']},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode='rich',
)

persona_app = typer.Typer(help='Manage persona configurations, DNA profiles, and identity lifecycle.')
memory_app = typer.Typer(help='Query, inspect, and prune memories inside the deep memory ledger.')
session_app = typer.Typer(help='Start, end, and inspect session notes and chronological continuity.')

app.add_typer(persona_app, name='persona')
app.add_typer(memory_app, name='memory')
app.add_typer(session_app, name='session')


# -----------------------------------------------------------------------------
# PERSONA COMMANDS GROUP
# -----------------------------------------------------------------------------


@persona_app.command('init')
@require_human
def persona_init():
    """Bootstrap a new persona via an interactive TUI questionnaire."""
    tui.init_wizard()


@persona_app.command('list')
@require_human
def persona_list():
    """List all globally and locally registered personas in the registry."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / 'personas.yaml'
        if not index_path.exists():
            console.print('[yellow]No registered personas found. Run `tur-adm persona init` to bootstrap one.[/yellow]')
            return
        with open(index_path, encoding='utf-8') as f:
            index_data = yaml.safe_load(f) or {'personas': []}
        index = PersonaIndex(**index_data)

        table = Table(title='Persona Registry', box=box.SIMPLE)
        table.add_column('UUID', style='dim', no_wrap=True)
        table.add_column('Name', style='cyan bold')
        table.add_column('Version', style='magenta')

        for p in index.personas:
            table.add_row(str(p.id), p.name, p.version)
        console.print(table)
    except Exception as e:
        console.print(f'[red]Error listing personas: {e}[/red]')
        raise typer.Exit(code=1)


@persona_app.command('view')
@require_human
def persona_view(identifier: str = typer.Argument(..., help='The name or UUID of the persona to view')):
    """View the detailed DNA/configuration of a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        persona_yaml = persona_dir / 'persona.yaml'
        if not persona_yaml.exists():
            console.print(f"[red]Error: persona.yaml not found for '{active_id}'[/red]")
            return
        with open(persona_yaml, encoding='utf-8') as f:
            pdata = yaml.safe_load(f) or {}

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column('Key', style='bold cyan')
        table.add_column('Value')

        table.add_row('Name', pdata.get('name', active_id))
        table.add_row('Version', pdata.get('version', 'unknown'))
        table.add_row('Description', pdata.get('description', '-'))

        principles = pdata.get('principles', [])
        if principles:
            principles_table = Table(box=box.MINIMAL, show_header=False)
            principles_table.add_column('Principle')
            for pr in principles:
                principles_table.add_row(f'- {pr}')
            table.add_row('Principles', principles_table)
        else:
            table.add_row('Principles', 'none')

        directives = pdata.get('directives', [])
        if directives:
            directives_table = Table(box=box.MINIMAL, show_header=False)
            directives_table.add_column('Directive')
            for dr in directives:
                directives_table.add_row(f'- {dr}')
            table.add_row('Directives', directives_table)
        else:
            table.add_row('Directives', 'none')

        console.print(Panel(table, title=f'[bold]Persona DNA: {active_id}[/bold]', border_style='cyan'))
    except Exception as e:
        console.print(f'[red]Error viewing persona: {e}[/red]')
        raise typer.Exit(code=1)


@persona_app.command('switch')
@require_human
def persona_switch():
    """Switch active default persona via an interactive TUI picker."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / 'personas.yaml'
        if not index_path.exists():
            console.print('[red]No personas found. Please run `tur-adm persona init` to create one.[/red]')
            raise ValueError('No personas found. Please run `tur-adm persona init` to create one.')  # noqa: TRY301
        with open(index_path, encoding='utf-8') as f:
            index_data = yaml.safe_load(f)
        index = PersonaIndex(**index_data)
        if not index.personas:
            console.print('[red]No personas available to select. Please run `tur-adm persona init`.[/red]')
            raise ValueError('No personas available to select. Please run `tur-adm persona init`.')  # noqa: TRY301

        selected_id = tui.select_persona_wizard(index)
        if selected_id:
            matched = next((p for p in index.personas if str(p.id) == selected_id), None)
            persona_name = matched.name if matched else selected_id
            console.print(f"[green]Default persona switched to: '{persona_name}' ({selected_id})[/green]")
        else:
            console.print('[yellow]Switch cancelled.[/yellow]')
    except Exception as e:
        console.print(f'[red]Error switching persona: {e}[/red]')
        raise typer.Exit(code=1)


@persona_app.command('export')
@require_human
def persona_export(
    identifier: str = typer.Argument(..., help='The name or UUID of the persona to export'),
    output_path: Path = typer.Argument(..., help='The target filepath for the export archive (e.g., ariel.tur)'),
):
    """Package a global persona's core config and universal memories into a portable .tur archive."""
    try:
        persona_dir = persona.get_persona_path(identifier)
        persona_uuid = persona_dir.name
        output_path = output_path.resolve()

        with tarfile.open(output_path, 'w:gz') as tar:
            # Add persona.yaml, injecting the 'id' field so import can validate identity
            persona_yaml_path = persona_dir / 'persona.yaml'
            if persona_yaml_path.exists():
                with open(persona_yaml_path, encoding='utf-8') as f:
                    persona_data = yaml.safe_load(f) or {}
                persona_data.setdefault('id', persona_uuid)
                yaml_bytes = yaml.dump(persona_data, sort_keys=False).encode('utf-8')
                info = tarfile.TarInfo(name='persona.yaml')
                info.size = len(yaml_bytes)
                tar.addfile(info, io.BytesIO(yaml_bytes))

            # Add universal memories directory
            memories_dir = persona_dir / 'memories'
            if memories_dir.exists():
                tar.add(memories_dir, arcname='memories')

        console.print(f"[green]Persona '{identifier}' successfully exported to '{output_path}'[/green]")
    except Exception as e:
        console.print(f'[red]Error exporting persona: {e}[/red]')
        raise typer.Exit(code=1)


@persona_app.command('import')
@require_human
def persona_import(archive_path: Path = typer.Argument(..., help='The filepath to the .tur archive to import')):
    """Unpack a .tur archive and register the global persona on this machine."""
    try:
        from tur.models import PersonaIndexEntry

        archive_path = archive_path.resolve()
        if not archive_path.exists():
            raise FileNotFoundError(f'Archive file not found: {archive_path}')  # noqa: TRY301

        # 1. Inspect archive in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with tarfile.open(archive_path, 'r:gz') as tar:
                # Sanitize all member paths before extraction to prevent path traversal
                for member in tar.getmembers():
                    member_path = (tmp_path / member.name).resolve()
                    if not str(member_path).startswith(str(tmp_path.resolve())):
                        raise ValueError(  # noqa: TRY301
                            f"Archive contains a path traversal entry and cannot be trusted: '{member.name}'"
                        )
                tar.extractall(path=tmp_path)

            persona_yaml = tmp_path / 'persona.yaml'
            if not persona_yaml.exists():
                raise ValueError('Invalid archive: persona.yaml is missing.')  # noqa: TRY301

            with open(persona_yaml, encoding='utf-8') as f:
                persona_data = yaml.safe_load(f)

            persona_id = persona_data.get('id')
            persona_name = persona_data.get('name', 'Unnamed Import')
            persona_version = persona_data.get('version', '1.0.0')

            if not persona_id:
                raise ValueError(  # noqa: TRY301
                    "Registry Failure: Exported archive is missing its canonical 'id' identity parameter."
                )

            # Validate that the ID is a valid UUID
            try:
                UUID(persona_id)
            except ValueError as e:
                raise ValueError(f"Registry Failure: Imported ID '{persona_id}' is not a valid UUID.") from e

            # 2. Reconstruct the global home
            global_home = Path.home() / '.tur'
            global_base = global_home
            if not (global_home / 'personas.yaml').exists():
                global_home.mkdir(parents=True, exist_ok=True)
                (global_home / 'personas.yaml').write_text('personas: []\n', encoding='utf-8')
                console.print(
                    '[yellow]Warning: ~/.tur/personas.yaml not found — initialized a new global registry.[/yellow]'
                )

            dest_dir = global_base / 'personas' / str(persona_id)
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy extracted files
            shutil.copytree(tmp_path, dest_dir, dirs_exist_ok=True)

            # 3. Register in master index
            index_path = global_base / 'personas.yaml'
            if index_path.exists():
                with open(index_path, encoding='utf-8') as f:
                    index_data = yaml.safe_load(f) or {'personas': []}
                index = PersonaIndex(**index_data)
            else:
                index = PersonaIndex(personas=[])

            # Append if not registered
            existing = next((p for p in index.personas if str(p.id) == str(persona_id)), None)
            if not existing:
                entry = PersonaIndexEntry(id=UUID(persona_id), name=persona_name, version=persona_version)
                index.personas.append(entry)
                with open(index_path, 'w', encoding='utf-8') as f:
                    yaml.dump(index.model_dump(mode='json'), f, sort_keys=False)

        console.print(
            f"[green]Persona '{persona_name}' ({persona_id}) successfully imported from '{archive_path}'[/green]"
        )
    except Exception as e:
        console.print(f'[red]Error importing persona: {e}[/red]')
        raise typer.Exit(code=1)


# -----------------------------------------------------------------------------
# MEMORY COMMANDS GROUP
# -----------------------------------------------------------------------------


@memory_app.command('list')
@require_human
def memory_list(
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses default.'),
    include_archived: bool = typer.Option(False, '--include-archived', help='Include forgotten/archived memories.'),
):
    """Show all memories in the bank for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=include_archived)

        if not mems:
            console.print(f'The Memory Bank for {active_id} is empty.')
            return

        table = Table(title=f'Memory Bank ({active_id})', show_lines=True)
        table.add_column('ID', style='dim')
        table.add_column('Type', style='cyan')
        table.add_column('Source', style='green')
        table.add_column('Status', style='magenta')
        table.add_column('Content')

        for m in mems:
            content_snippet = (m.content[:80] + '..') if len(m.content) > 80 else m.content
            status_display = 'archived' if getattr(m, 'status', None) == 'archived' else 'active'
            row_style = 'dim' if status_display == 'archived' else ''

            table.add_row(str(m.id), m.type.value, m.scope.value, status_display, content_snippet, style=row_style)

        console.print(table)
    except Exception as e:
        console.print(f'[red]Error listing memories: {e}[/red]')
        raise typer.Exit(code=1)


@memory_app.command('view')
@require_human
def memory_view(
    memory_id: str = typer.Argument(..., help='The SHA-256 hash/ID of the memory to view.'),
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses default.'),
):
    """View the detailed contents of a specific memory."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=True)
        matched = next((m for m in mems if str(m.id).startswith(memory_id)), None)
        if not matched:
            console.print(f"[red]Error: No memory found matching ID '{memory_id}'[/red]")
            return

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column('Key', style='bold cyan')
        table.add_column('Value')

        table.add_row('ID (SHA-256)', str(matched.id))
        table.add_row('Type', matched.type.value)
        table.add_row('Scope', matched.scope.value)
        table.add_row('Timestamp', matched.timestamp.isoformat())
        tags_str = ', '.join(matched.tags)
        table.add_row('Tags', tags_str or 'none')
        table.add_row('Content', matched.content)
        if matched.source_session:
            table.add_row('Source Session', matched.source_session)

        console.print(Panel(table, title='[bold]Memory Detail[/bold]', border_style='cyan'))
    except Exception as e:
        console.print(f'[red]Error viewing memory: {e}[/red]')
        raise typer.Exit(code=1)


@memory_app.command('forget')
@require_human
def memory_forget(
    memory_id: str = typer.Argument(..., help='The ID (hash) of the memory to forget.'),
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses default.'),
):
    """Archive a memory by its ID for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_manager.archive(memory_id)
        console.print(f'[green]Memory {memory_id} has been forgotten (archived).[/green]')
    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1)


# -----------------------------------------------------------------------------
# SESSION COMMANDS GROUP
# -----------------------------------------------------------------------------


@session_app.command('list')
@require_human
def session_list(
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses default.'),
):
    """List all sessions in the index for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        index = session.load_session_index(persona_dir)

        if not index.sessions:
            console.print(f"No sessions found for persona '{active_id}'.")
            return

        table = Table(title=f'Session Index ({active_id})', box=box.SIMPLE)
        table.add_column('Session ID', style='cyan bold')
        table.add_column('Status', style='magenta')
        table.add_column('Created At')
        table.add_column('Updated At')

        for s in index.sessions:
            status_color = 'green' if s.status == 'active' else 'dim'
            table.add_row(
                s.id,
                f'[{status_color}]{s.status}[/{status_color}]',
                s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            )
        console.print(table)
    except Exception as e:
        console.print(f'[red]Error listing sessions: {e}[/red]')
        raise typer.Exit(code=1)


@session_app.command('start')
@require_human
def start_session(
    session_id: str = typer.Argument(..., help='The ID of the session to start.'),
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses standard.'),
):
    """Create a new isolated session under the active persona."""
    try:
        res = session.start_session_logic(session_id, identifier=identifier)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error starting session: {e}[/red]')
        raise typer.Exit(code=1)


@session_app.command('end')
@require_human
def end_session(
    session_id: str = typer.Argument(..., help='The ID of the session to end.'),
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses standard.'),
):
    """Mark the session as ended."""
    try:
        res = session.end_session_logic(session_id, identifier=identifier)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error ending session: {e}[/red]')
        raise typer.Exit(code=1)


@session_app.command('note')
@require_human
def session_note(
    note_index: int = typer.Argument(..., help="The 1-indexed position of the note in the session's ledger to view."),
    session_id: str | None = typer.Option(None, help='The session ID. If omitted, uses active session.'),
    identifier: str | None = typer.Option(None, help='The name or UUID of the persona. If omitted, uses default.'),
):
    """View a specific note by its 1-indexed position in a session."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        resolved_session_id = session_id or session.get_active_session_id()

        if not resolved_session_id:
            console.print('[red]Error: No active session found. Please specify --session-id.[/red]')
            return

        notes_yaml_path = session.get_session_file(persona_dir, resolved_session_id)
        if not notes_yaml_path.exists():
            console.print(f"[red]Error: No notes file found for session '{resolved_session_id}'[/red]")
            return

        with open(notes_yaml_path, encoding='utf-8') as f:
            notes_data = yaml.safe_load(f)
        session_notes = SessionNotes(**notes_data)

        if note_index < 1 or note_index > len(session_notes.notes):
            console.print(f'[red]Error: Invalid note index. The session has {len(session_notes.notes)} notes.[/red]')
            return

        note_item = sorted(session_notes.notes, key=lambda n: n.timestamp)[note_index - 1]

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column('Key', style='bold cyan')
        table.add_column('Value')

        table.add_row('Index', str(note_index))
        table.add_row('Timestamp', note_item.timestamp.isoformat())
        table.add_row('Content', note_item.content)

        console.print(
            Panel(
                table,
                title=f'[bold]Session {resolved_session_id} - Note #{note_index}[/bold]',
                border_style='cyan',
            )
        )
    except Exception as e:
        console.print(f'[red]Error viewing session note: {e}[/red]')
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == '__main__':
    main()
