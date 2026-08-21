import sys

from rich.syntax import Syntax

try:
    import textual
except ImportError:
    from rich.console import Console, Group
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
from tur._helpers import yaml_safe_load
from tur.cli.common import console, require_human
from tur.memory import MemoryManager
from tur.models import (
    PersonaIndex,
    SessionNotes,
)
from tur.paths import get_global_tur_dir, resolve_personas_base_dir, resolve_workspace_dir

app = typer.Typer(
    help='Tur: Administrative persona management CLI.',
    context_settings={'help_option_names': ['-h', '--help']},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode='rich',
)

persona_app = typer.Typer(help='Manage persona configurations and identities.')
memory_app = typer.Typer(help='Query, inspect, and manage memories in the ledger.')
session_app = typer.Typer(help='Start, end, and inspect session state and notes.')

app.add_typer(persona_app, name='persona')
app.add_typer(memory_app, name='memory')
app.add_typer(session_app, name='session')


# -----------------------------------------------------------------------------
# ARCHIVE EXTRACTION SECURITY HELPERS (CWE-22 / Tar Slip Prevention)
# -----------------------------------------------------------------------------


def is_within_directory(directory: Path, target: Path) -> bool:
    """Verify that target is strictly contained within directory."""
    try:
        target.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    else:
        return True


def safe_extract(tar: tarfile.TarFile, path: Path) -> None:
    """
    Safely extract tar archive members preventing Arbitrary File Write (Tar Slip / CWE-22).
    Validates against symlinks, hardlinks, path traversal, and uses PEP 706 data filters.
    """
    resolved_path = path.resolve()
    safe_members = []
    for member in tar.getmembers():
        if member.issym() or member.islnk():
            raise PermissionError(
                'Archive contains a symlink or hardlink '
                f"which is not allowed for security reasons: '{member.name}'"
            )
        try:
            member_path = (resolved_path / member.name).resolve()
        except Exception as e:
            raise PermissionError(f"Path traversal detected or invalid path: '{member.name}'") from e

        if not is_within_directory(resolved_path, member_path):
            raise PermissionError(
                f"Archive contains a path traversal entry and cannot be trusted: '{member.name}'"
            )

        safe_members.append(member)

    if hasattr(tarfile, 'data_filter'):
        tar.extractall(path=resolved_path, members=safe_members, filter='data')
    else:
        tar.extractall(path=resolved_path, members=safe_members)


# -----------------------------------------------------------------------------
# PERSONA COMMANDS GROUP
# -----------------------------------------------------------------------------


@persona_app.command('init')
@require_human
def persona_init() -> None:
    """Bootstrap a new persona via an interactive TUI questionnaire."""
    tui.init_wizard()


@persona_app.command('list')
@require_human
def persona_list() -> None:
    """List all globally and locally registered personas in the registry."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / 'personas.yaml'
        if not index_path.exists():
            console.print('[yellow]No registered personas found. Run `tur-adm persona init` to bootstrap one.[/yellow]')
            return
        with open(index_path, encoding='utf-8') as f:
            index_data: dict = yaml_safe_load(f) or {'personas': []}
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
def persona_view(identifier: str = typer.Argument(..., help='The name or UUID of the persona to view')) -> None:
    """View the detailed DNA/configuration of a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        persona_yaml = persona_dir / 'persona.yaml'
        if not persona_yaml.exists():
            console.print(f"[red]Error: persona.yaml not found for '{active_id}'[/red]")
            return
        with open(persona_yaml, encoding='utf-8') as f:
            pdata: dict = yaml_safe_load(f) or {}

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
def persona_switch() -> None:
    """Switch active default persona via an interactive TUI picker."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / 'personas.yaml'
        if not index_path.exists():
            console.print('[red]No personas found. Please run `tur-adm persona init` to create one.[/red]')
            raise ValueError('No personas found. Please run `tur-adm persona init` to create one.')  # noqa: TRY301
        with open(index_path, encoding='utf-8') as f:
            index_data = yaml_safe_load(f)
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
        output: Path = typer.Option(
            ...,
            '--output',
            '-o',
            help='The target filepath for the export archive (e.g., ariel.tur)',
        ),
) -> None:
    """Package a global persona's core config and universal memories into a portable .tur archive."""
    try:
        persona_dir = persona.get_persona_path(identifier)
        persona_uuid = persona_dir.name
        output_path = output.resolve()

        with tarfile.open(output_path, 'w:gz') as tar:
            # Add persona.yaml, injecting the index entry UUID
            persona_yaml_path = persona_dir / 'persona.yaml'
            if not persona_yaml_path.exists():
                raise FileNotFoundError(f"persona.yaml not found in '{persona_dir}'")  # noqa: TRY301

            with open(persona_yaml_path, encoding='utf-8') as f:
                persona_data: dict = yaml_safe_load(f) or {}

            persona_data['id'] = str(persona_uuid)
            yaml_str = yaml.dump(persona_data, sort_keys=False)
            if not isinstance(yaml_str, str):
                raise TypeError("Persona data cannot be deserilized")  # noqa: TRY301
            yaml_bytes = yaml_str.encode('utf-8')
            info = tarfile.TarInfo(name='persona.yaml')
            info.size = len(yaml_bytes)
            tar.addfile(info, io.BytesIO(yaml_bytes))

            # Add only universal/user/persona scoped memories. Exclude incarnation memories, sessions, and notes.
            from tur.models import MemoryScope

            memory_manager = MemoryManager(base_dir=persona_dir)

            search_dirs = [
                (memory_manager.global_dir, 'memories/active'),
                (memory_manager.global_archive_dir, 'memories/archive'),
                (memory_manager.global_subsumed_dir, 'memories/subsumed'),
                (memory_manager.global_dir.parent, 'memories'),
                (memory_manager.local_dir, 'memories/active'),
                (memory_manager.local_archive_dir, 'memories/archive'),
                (memory_manager.local_subsumed_dir, 'memories/subsumed'),
                (memory_manager.local_dir.parent, 'memories'),
            ]

            seen_memories = set()
            for directory, arc_prefix in search_dirs:
                if not directory.exists():
                    continue
                for file_path in list(directory.glob('*.md')) + list(directory.glob('*.yaml')):
                    if not file_path.is_file():
                        continue
                    parent_name = file_path.parent.name
                    is_legacy = parent_name == 'memories' and file_path.suffix == '.yaml'
                    if parent_name not in ['active', 'archive', 'subsumed'] and not is_legacy:
                        continue

                    mem = memory_manager._load_file(file_path)
                    # _load_file may return None for invalid/unsupported files; guard before attribute access
                    if mem is None:
                        continue

                    in_scope = mem.scope in (MemoryScope.UNIVERSAL, MemoryScope.USER, MemoryScope.PERSONA)
                    if in_scope and mem.id not in seen_memories:
                        seen_memories.add(mem.id)
                        arcname = f'{arc_prefix}/{file_path.name}'
                        tar.add(file_path, arcname=arcname)

        console.print(f"[green]Persona '{identifier}' successfully exported to '{output_path}'[/green]")
    except Exception as e:
        console.print(f'[red]Error exporting persona: {e}[/red]')
        raise typer.Exit(code=1) from e


@persona_app.command('import')
@require_human
def persona_import(
        archive_path: Path = typer.Argument(..., help='The filepath to the .tur archive to import'),
        set_active: bool = typer.Option(
            False,
            '--set-active',
            '--set-default',
            help='Set the imported persona as the active default in state.yaml.',
        ),
        force: bool = typer.Option(
            False,
            '--force',
            '-f',
            help='Force overwrite of an existing persona with the same UUID.',
        ),
) -> None:
    """Unpack a .tur archive and register the global persona on this machine."""
    try:
        from tur.models import PersonaIndexEntry, SystemState

        archive_path = archive_path.resolve()
        if not archive_path.exists():
            raise FileNotFoundError(f'Archive file not found: {archive_path}')  # noqa: TRY301

        # 1. Inspect archive in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with tarfile.open(archive_path, 'r:gz') as tar:
                safe_extract(tar, tmp_path)

            persona_yaml = tmp_path / 'persona.yaml'
            if not persona_yaml.exists():
                raise ValueError('Invalid archive: persona.yaml is missing.')  # noqa: TRY301

            with open(persona_yaml, encoding='utf-8') as f:
                persona_data = yaml_safe_load(f)

            if not persona_data or not isinstance(persona_data, dict):
                raise ValueError('Invalid archive: persona.yaml is empty or invalid.')  # noqa: TRY301

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
            if not (global_home / 'personas.yaml').exists():
                global_home.mkdir(parents=True, exist_ok=True)
                with open(global_home / 'personas.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump({'personas': []}, f)
                console.print(
                    '[yellow]Warning: ~/.tur/personas.yaml not found — initialized a new global registry.[/yellow]'
                )

            dest_dir = global_home / 'personas' / str(persona_id)

            # Check index
            index_path = global_home / 'personas.yaml'
            with open(index_path, encoding='utf-8') as f:
                index_data: dict = yaml_safe_load(f) or {'personas': []}
            index = PersonaIndex(**index_data)

            exists_on_disk = dest_dir.exists()
            exists_in_index = any(str(p.id) == str(persona_id) for p in index.personas)

            if exists_on_disk or exists_in_index:
                if not force:
                    raise ValueError(  # noqa: TRY301
                        f"Registry Failure: Persona '{persona_id}' already exists. Use --force to overwrite."
                    )
                else:
                    if exists_on_disk:
                        if dest_dir.is_dir():
                            shutil.rmtree(dest_dir)
                        else:
                            dest_dir.unlink()

            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy extracted files
            shutil.copytree(tmp_path, dest_dir, dirs_exist_ok=True)

            # 3. Register/update in master index
            existing_idx = None
            for idx, p in enumerate(index.personas):
                if str(p.id) == str(persona_id):
                    existing_idx = idx
                    break

            entry = PersonaIndexEntry(id=UUID(persona_id), name=persona_name, version=persona_version)

            if existing_idx is not None:
                index.personas[existing_idx] = entry
            else:
                index.personas.append(entry)

            with open(index_path, 'w', encoding='utf-8') as f:
                yaml.dump(index.model_dump(mode='json'), f, sort_keys=False)

            # 4. Optionally set active default in .tur/state.yaml
            if set_active:
                state_path = Path('.tur/state.yaml')
                state_path.parent.mkdir(parents=True, exist_ok=True)
                if state_path.exists():
                    try:
                        with open(state_path, encoding='utf-8') as f:
                            state_data: dict = yaml_safe_load(f) or {}
                        state_obj = SystemState(**state_data)
                        state_obj.active_persona_id = UUID(persona_id)
                        state_obj.active_session_id = None  # Reset active session on persona switch
                    except Exception:
                        state_obj = SystemState(active_persona_id=UUID(persona_id), active_session_id=None)
                else:
                    state_obj = SystemState(active_persona_id=UUID(persona_id), active_session_id=None)

                with open(state_path, 'w', encoding='utf-8') as f:
                    yaml.dump(state_obj.model_dump(mode='json'), f)
                console.print(f"[green]Set active persona default to: '{persona_name}' ({persona_id})[/green]")

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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses default.'),
        include_archived: bool = typer.Option(False, '--include-archived', help='Include forgotten/archived memories.'),
) -> None:
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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses default.'),
) -> None:
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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses default.'),
) -> None:
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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses default.'),
) -> None:
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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses standard.'),
) -> None:
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
        identifier: str | None = typer.Argument(None,
                                                help='The name or UUID of the persona. If omitted, uses standard.'),
) -> None:
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
        note_index: int = typer.Argument(
            ...,
            help="The 1-indexed position of the note in the session's ledger to view.",
        ),
        session_id: str | None = typer.Option(None, help='The session ID. If omitted, uses active session.'),
        identifier: str | None = typer.Option(None, help='The name or UUID of the persona. If omitted, uses default.'),
) -> None:
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
            notes_data = yaml_safe_load(f)
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


def _resolve_target_stores(
        scope: str, global_only: bool, local_only: bool
) -> list[tuple[str, Path]]:
    if global_only:
        target_scopes = ['global']
    elif local_only:
        target_scopes = ['local']
    elif scope in ['global', 'local']:
        target_scopes = [scope]
    else:
        target_scopes = ['global', 'local']

    stores: list[tuple[str, Path]] = []
    if 'global' in target_scopes:
        stores.append(('global', get_global_tur_dir()))
    if 'local' in target_scopes:
        ws = resolve_workspace_dir()
        if ws:
            stores.append(('local', ws / '.tur'))
        elif Path('.tur').exists():
            stores.append(('local', Path('.tur').resolve()))
    return stores


def _collect_hygiene_items(
        stores: list[tuple[str, Path]]
) -> tuple[list[tuple[str, Path]], list[tuple[str, Path]], list[Path]]:
    orphaned_dirs: list[tuple[str, Path]] = []
    dangling_files: list[tuple[str, Path]] = []
    retained_personas: list[Path] = []

    for store_label, base_dir in stores:
        if not base_dir.exists():
            continue

        index_file = base_dir / 'personas.yaml'
        valid_ids: set[str] = set()
        if index_file.exists():
            try:
                with open(index_file, encoding='utf-8') as f:
                    data = yaml_safe_load(f)
                idx = PersonaIndex(**data)
                for p in idx.personas:
                    valid_ids.add(str(p.id))
                    valid_ids.add(p.name.lower())
            except Exception:
                pass

        personas_dir = base_dir / 'personas'
        if personas_dir.exists():
            for p_dir in personas_dir.iterdir():
                if p_dir.is_dir():
                    if p_dir.name not in valid_ids and p_dir.name.lower() not in valid_ids:
                        orphaned_dirs.append((store_label, p_dir))
                    else:
                        retained_personas.append(p_dir)

        for tmp_file in base_dir.glob('**/*.tmp.*'):
            if tmp_file.is_file():
                dangling_files.append((store_label, tmp_file))

    return orphaned_dirs, dangling_files, retained_personas


def _execute_hygiene_removals(
        orphaned_dirs: list[tuple[str, Path]], dangling_files: list[tuple[str, Path]]
) -> None:
    for _, p in orphaned_dirs:
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
            console.print(f'[green]Removed orphaned directory:[/green] {p}')

    for _, p in dangling_files:
        if p.exists() and p.is_file():
            p.unlink(missing_ok=True)
            console.print(f'[green]Removed dangling temp file:[/green] {p}')


def _verify_retained_stores(retained_personas: list[Path]) -> int:
    console.print('\n[bold cyan]Running Merkle Integrity Verification on Retained Stores...[/bold cyan]')
    total_failures = 0
    for p_dir in retained_personas:
        mm = MemoryManager(base_dir=p_dir)
        failures = mm.verify_integrity()
        if failures:
            total_failures += len(failures)
            console.print(f"[red]Integrity check failed for persona '{p_dir.name}':[/red]")
            for f_path, reason in failures:
                console.print(f'  [red]{f_path.name}:[/red] {reason}')
        else:
            console.print(f"[green]Persona '{p_dir.name}': 100% Merkle integrity verified.[/green]")
    return total_failures


@app.command('clean')
@require_human
def clean(
        dry_run: bool = typer.Option(False, '--dry-run', help='Display what would be cleaned without modifying files.'),
        scope: str = typer.Option('all', '--scope', help='Storage scope to clean: all, global, or local.'),
        global_only: bool = typer.Option(False, '--global', help='Clean global storage only.'),
        local_only: bool = typer.Option(False, '--local', help='Clean local storage only.'),
        yes: bool = typer.Option(False, '-y', '--yes', help='Bypass confirmation prompt.'),
) -> None:
    """
    Storage bank hygiene: prune unindexed/orphaned persona directories and dangling temp files.
    """
    stores = _resolve_target_stores(scope, global_only, local_only)
    orphaned_dirs, dangling_files, retained_personas = _collect_hygiene_items(stores)

    table = Table(title='Storage Bank Hygiene Audit', box=box.ROUNDED)
    table.add_column('Scope', style='cyan')
    table.add_column('Type', style='yellow')
    table.add_column('Path', style='white')

    for s_lbl, p in orphaned_dirs:
        table.add_row(s_lbl, 'Orphaned Persona Dir', str(p))
    for s_lbl, p in dangling_files:
        table.add_row(s_lbl, 'Dangling Temp File', str(p))

    if not orphaned_dirs and not dangling_files:
        console.print('[bold green]Storage banks are clean. No orphaned or dangling artifacts found.[/bold green]')
    else:
        console.print(table)
        if dry_run:
            console.print(
                f'[bold cyan]Dry run completed.[/bold cyan] {len(orphaned_dirs)} orphaned dirs, '
                f'{len(dangling_files)} dangling files identified.'
            )
            return

        if not yes and not typer.confirm('Proceed with storage hygiene cleanup?'):
            console.print('Aborted.')
            return

        _execute_hygiene_removals(orphaned_dirs, dangling_files)
        console.print('[bold green]Hygiene cleanup completed.[/bold green]')

    failures = _verify_retained_stores(retained_personas)
    if failures > 0:
        console.print(f'[bold red]Verification completed with {failures} integrity failure(s).[/bold red]')
        raise typer.Exit(code=1)

    console.print('[bold green]All retained stores verified with 100% Merkle integrity.[/bold green]')


def main():
    app()


if __name__ == '__main__':
    main()
