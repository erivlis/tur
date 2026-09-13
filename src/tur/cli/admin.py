import contextlib
import io
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
import yaml
from rich import box
from rich.panel import Panel
from rich.table import Table

from tur import persona, session
from tur._helpers import yaml_safe_load
from tur.cli import wizards
from tur.cli.common import (
    console,
    get_memory_status_style,
    get_session_status_style,
    handle_cli_error,
    make_version_callback,
    require_human,
    run_scaffold_cli,
)
from tur.memory import (
    DEFAULT_EMBEDDING_MODEL,
    MODEL_ALIASES,
    RECOMMENDED_MODELS,
    MemoryManager,
    VectorEngine,
    is_model_compatible,
)
from tur.models import (
    MemoryType,
    PersonaIndex,
    SessionNotes,
)
from tur.paths import (
    PERSONA_FILENAME,
    PERSONAS_FILENAME,
    get_global_tur_dir,
    resolve_models_dir,
    resolve_personas_base_dir,
    resolve_workspace_dir,
)
from tur.session import load_system_state, update_system_state

STYLE_BOLD_CYAN = 'bold cyan'
NO_PERSONAS_FOUND_MSG = '[yellow]No registered personas found. Run `tur-adm persona init` to bootstrap one.[/yellow]'
HELP_ADMIN_PERSONA_ARG = 'The name or UUID of the persona. If omitted, uses default.'

app = typer.Typer(
    help='Tur: Administrative persona management CLI.',
    context_settings={'help_option_names': ['-h', '--help']},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode='rich',
)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        '--version',
        '-V',
        help='Show the version and exit.',
        callback=make_version_callback('tur-adm'),
        is_eager=True,
    ),
) -> None:
    """Tur: Administrative persona management CLI."""


persona_app = typer.Typer(help='Manage persona configurations and identities.')
memory_app = typer.Typer(help='Query, inspect, and manage memories in the ledger.')
session_app = typer.Typer(help='Start, end, and inspect session state and notes.')
signal_app = typer.Typer(help='Inspect inter-agent signals and Lamport Vector Clocks (EP-0118, EP-0141).')
model_app = typer.Typer(help='Manage ONNX embedding models and tokenizers (EP-0144).')

app.add_typer(persona_app, name='persona')
app.add_typer(memory_app, name='memory')
app.add_typer(session_app, name='session')
app.add_typer(signal_app, name='signal')
app.add_typer(model_app, name='model')


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
                f"Archive contains a symlink or hardlink which is not allowed for security reasons: '{member.name}'"
            )
        try:
            member_path = (resolved_path / member.name).resolve()
        except Exception as e:
            raise PermissionError(f"Path traversal detected or invalid path: '{member.name}'") from e

        if not is_within_directory(resolved_path, member_path):
            raise PermissionError(f"Archive contains a path traversal entry and cannot be trusted: '{member.name}'")

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
    """Bootstrap a new persona via interactive prompts."""
    wizards.init_wizard()


@persona_app.command('list')
@require_human
def persona_list() -> None:
    """List all globally and locally registered personas in the registry."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / PERSONAS_FILENAME
        if not index_path.exists():
            console.print(NO_PERSONAS_FOUND_MSG)
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
def persona_view(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona to view. If omitted, prompts with a persona selector.'
    ),
) -> None:
    """View the detailed DNA/configuration of a specific persona."""
    try:
        if not identifier:
            base_dir = resolve_personas_base_dir()
            index_path = base_dir / PERSONAS_FILENAME
            if not index_path.exists():
                console.print(NO_PERSONAS_FOUND_MSG)
                return
            with open(index_path, encoding='utf-8') as f:
                index_data: dict[str, Any] = yaml_safe_load(f) or {'personas': []}
            index = PersonaIndex(**index_data)
            if not index.personas:
                console.print(NO_PERSONAS_FOUND_MSG)
                return
            identifier = wizards.select_persona_wizard(index)
            if not identifier:
                console.print('[yellow]View cancelled.[/yellow]')
                return

        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        persona_yaml = persona_dir / PERSONA_FILENAME
        if not persona_yaml.exists():
            console.print(f"[red]Error: persona.yaml not found for '{active_id}'[/red]")
            return
        with open(persona_yaml, encoding='utf-8') as f:
            pdata: dict = yaml_safe_load(f) or {}

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column('Key', style=STYLE_BOLD_CYAN)
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


@persona_app.command('get')
@require_human
def persona_get() -> None:
    """Get the active persona configured for this workspace in .tur/state.yaml."""
    try:
        state_obj = load_system_state()
        active_uuid = str(state_obj.active_persona_id) if state_obj.active_persona_id else None

        if not active_uuid:
            console.print('[yellow]No active persona configured for this workspace (.tur/state.yaml).[/yellow]')
            console.print('Run `tur-adm persona set` to select one.')
            return

        base_dir = resolve_personas_base_dir()
        index_path = base_dir / PERSONAS_FILENAME
        persona_name = active_uuid
        version = 'unknown'
        if index_path.exists():
            with open(index_path, encoding='utf-8') as f:
                index_data: dict[str, Any] = yaml_safe_load(f) or {'personas': []}
            index = PersonaIndex(**index_data)
            matched = next((p for p in index.personas if str(p.id) == active_uuid), None)
            if matched:
                persona_name = matched.name
                version = matched.version

        ws = resolve_workspace_dir() or Path.cwd()
        state_path = ws / '.tur' / 'state.yaml'
        console.print(f'[bold green]Active Persona:[/bold green] {persona_name} (v{version}) [{active_uuid}]')
        console.print(f'[dim]Source: {state_path}[/dim]')
    except Exception as e:
        handle_cli_error(e, 'Error getting active persona')


@persona_app.command('set')
@require_human
def persona_set(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona to set. If omitted, prompts with a persona selector.'
    ),
) -> None:
    """Set the active persona for this workspace in .tur/state.yaml."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / PERSONAS_FILENAME
        if not index_path.exists():
            console.print('[red]No personas found. Please run `tur-adm persona init` to create one.[/red]')
            raise ValueError('No personas found. Please run `tur-adm persona init` to create one.')  # noqa: TRY301
        with open(index_path, encoding='utf-8') as f:
            index_data = yaml_safe_load(f)
        index = PersonaIndex(**index_data)
        if not index.personas:
            console.print('[red]No personas available to select. Please run `tur-adm persona init`.[/red]')
            raise ValueError('No personas available to select. Please run `tur-adm persona init`.')  # noqa: TRY301

        selected_id = persona.get_active_persona_id(identifier) if identifier else wizards.select_persona_wizard(index)

        if selected_id:
            matched = next((p for p in index.personas if str(p.id) == selected_id), None)
            persona_name = matched.name if matched else selected_id

            update_system_state(active_persona_id=selected_id)

            console.print(f"[green]Active workspace persona set to: '{persona_name}' ({selected_id})[/green]")
        else:
            console.print('[yellow]Action cancelled.[/yellow]')
    except Exception as e:
        handle_cli_error(e, 'Error setting persona')


def _collect_export_memory_dirs(memory_manager: MemoryManager) -> list[tuple[Path, str]]:
    """Builds the list of candidate memory directories and archive prefixes for export."""
    search_dirs: list[tuple[Path, str]] = []
    if memory_manager.global_dir:
        search_dirs.append((memory_manager.global_dir, 'memories/active'))
        if memory_manager.global_archive_dir:
            search_dirs.append((memory_manager.global_archive_dir, 'memories/archive'))
        if memory_manager.global_subsumed_dir:
            search_dirs.append((memory_manager.global_subsumed_dir, 'memories/subsumed'))
        search_dirs.append((memory_manager.global_dir.parent, 'memories'))

    if memory_manager.local_dir:
        search_dirs.append((memory_manager.local_dir, 'memories/active'))
        if memory_manager.local_archive_dir:
            search_dirs.append((memory_manager.local_archive_dir, 'memories/archive'))
        if memory_manager.local_subsumed_dir:
            search_dirs.append((memory_manager.local_subsumed_dir, 'memories/subsumed'))
        search_dirs.append((memory_manager.local_dir.parent, 'memories'))
    return search_dirs


@persona_app.command('export')
@require_human
def persona_export(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona to export. If omitted, prompts with a persona selector.'
    ),
    output: Path | None = typer.Option(
        None,
        '--output',
        '-o',
        help='The target filepath for the export archive (e.g., ariel.tur). Defaults to <persona_name>.tur.',
    ),
) -> None:
    """Package a global persona's core config and universal memories into a portable .tur archive."""
    try:
        if not identifier:
            base_dir = resolve_personas_base_dir()
            index_path = base_dir / PERSONAS_FILENAME
            if not index_path.exists():
                console.print(NO_PERSONAS_FOUND_MSG)
                return
            with open(index_path, encoding='utf-8') as f:
                index_data: dict[str, Any] = yaml_safe_load(f) or {'personas': []}
            index = PersonaIndex(**index_data)
            if not index.personas:
                console.print(NO_PERSONAS_FOUND_MSG)
                return
            identifier = wizards.select_persona_wizard(index)
            if not identifier:
                console.print('[yellow]Export cancelled.[/yellow]')
                return

        persona_dir = persona.get_persona_path(identifier)
        persona_uuid = persona_dir.name

        if output is None:
            persona_yaml_path = persona_dir / PERSONA_FILENAME
            target_name = persona_uuid
            if persona_yaml_path.exists():
                with contextlib.suppress(Exception), open(persona_yaml_path, encoding='utf-8') as f:
                    target_name = (yaml_safe_load(f) or {}).get('name', persona_uuid).lower()
            output = Path(f'{target_name}.tur')

        output_path = output.resolve()

        with tarfile.open(output_path, 'w:gz') as tar:
            # Add persona.yaml, injecting the index entry UUID
            persona_yaml_path = persona_dir / PERSONA_FILENAME
            if not persona_yaml_path.exists():
                raise FileNotFoundError(f"persona.yaml not found in '{persona_dir}'")  # noqa: TRY301

            with open(persona_yaml_path, encoding='utf-8') as f:
                persona_data: dict = yaml_safe_load(f) or {}

            persona_data['id'] = str(persona_uuid)
            yaml_str = yaml.dump(persona_data, sort_keys=False)
            if not isinstance(yaml_str, str):
                raise TypeError('Persona data cannot be deserilized')  # noqa: TRY301
            yaml_bytes = yaml_str.encode('utf-8')
            info = tarfile.TarInfo(name=PERSONA_FILENAME)
            info.size = len(yaml_bytes)
            tar.addfile(info, io.BytesIO(yaml_bytes))

            # Add only universal/user/persona scoped memories. Exclude incarnation memories, sessions, and notes.
            from tur.models import MemoryScope

            memory_manager = MemoryManager(base_dir=persona_dir)
            search_dirs = _collect_export_memory_dirs(memory_manager)

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

            persona_yaml = tmp_path / PERSONA_FILENAME
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
            if not (global_home / PERSONAS_FILENAME).exists():
                global_home.mkdir(parents=True, exist_ok=True)
                with open(global_home / PERSONAS_FILENAME, 'w', encoding='utf-8') as f:
                    yaml.dump({'personas': []}, f)
                console.print(
                    '[yellow]Warning: ~/.tur/personas.yaml not found — initialized a new global registry.[/yellow]'
                )

            dest_dir = global_home / 'personas' / str(persona_id)

            # Check index
            index_path = global_home / PERSONAS_FILENAME
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
                update_system_state(active_persona_id=persona_id, reset_session=True)
                console.print(f"[green]Set active persona default to: '{persona_name}' ({persona_id})[/green]")

        console.print(
            f"[green]Persona '{persona_name}' ({persona_id}) successfully imported from '{archive_path}'[/green]"
        )
    except Exception as e:
        handle_cli_error(e, 'Error importing persona')


# -----------------------------------------------------------------------------
# MEMORY COMMANDS GROUP
# -----------------------------------------------------------------------------


@memory_app.command('list')
@require_human
def memory_list(
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
    include_archived: bool = typer.Option(False, '--include-archived', help='Include forgotten/archived memories.'),
    pending: bool = typer.Option(False, '--pending', help='Filter to only show memories pending approval.'),
) -> None:
    """Show all memories in the bank for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=include_archived)

        if pending:
            mems = [m for m in mems if getattr(m, 'status', None) == 'pending_approval']

        if not mems:
            if pending:
                console.print(f'No pending memories found for {active_id}.')
            else:
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
            raw_status = getattr(m, 'status', None)
            is_redacted = getattr(m, 'redacted', False)
            status_display, row_style = get_memory_status_style(raw_status, redacted=is_redacted)
            table.add_row(str(m.id), m.type.value, m.scope.value, status_display, content_snippet, style=row_style)

        console.print(table)
    except Exception as e:
        handle_cli_error(e, 'Error listing memories')


@memory_app.command('approve')
@require_human
def memory_approve(
    memory_id: str = typer.Argument(..., help='The ID (hash) of the Core Memory to approve/activate.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
) -> None:
    """Activate/approve a pending Core Memory, making it an active constraint in the system prompt."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        matching_mem, already_active = memory_manager.approve_core_memory(memory_id)

        if already_active:
            console.print(f"[yellow]Core Memory '{matching_mem.id[:8]}' is already active.[/yellow]")
        else:
            console.print(f"[green]Core Memory '{matching_mem.id[:8]}' approved and activated successfully.[/green]")
    except FileNotFoundError as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1) from e
    except Exception as e:
        handle_cli_error(e)


@memory_app.command('view')
@require_human
def memory_view(
    memory_id: str = typer.Argument(..., help='The SHA-256 hash/ID of the memory to view.'),
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
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
        table.add_column('Key', style=STYLE_BOLD_CYAN)
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
        if matched.redacted:
            table.add_row('Redacted', '[bold red]TRUE[/bold red]')
            if matched.redacted_at:
                table.add_row(
                    'Redacted At',
                    matched.redacted_at.isoformat()
                    if hasattr(matched.redacted_at, 'isoformat')
                    else str(matched.redacted_at),
                )
            if matched.redaction_reason:
                table.add_row('Redaction Reason', matched.redaction_reason)

        console.print(Panel(table, title='[bold]Memory Detail[/bold]', border_style='cyan'))
    except Exception as e:
        console.print(f'[red]Error viewing memory: {e}[/red]')
        raise typer.Exit(code=1)


@memory_app.command('forget')
@require_human
def memory_forget(
    memory_id: str = typer.Argument(..., help='The ID (hash) of the memory to forget.'),
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
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


@memory_app.command('redact')
@require_human
def memory_redact(
    memory_id: str = typer.Argument(..., help='The ID (hash) or prefix of the memory to redact.'),
    reason: str = typer.Option(..., '--reason', '-r', help='The justification/reason for the redaction.'),
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
) -> None:
    """Tombstone and purge sensitive data from a memory while preserving graph integrity."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        redacted_path = memory_manager.redact(memory_id, reason=reason)
        console.print(
            f"[green]Memory '{memory_id}' successfully tombstoned and redacted at '{redacted_path.name}'[/green]"
        )
    except FileNotFoundError as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1) from e
    except Exception as e:
        handle_cli_error(e, 'Error redacting memory')


@memory_app.command('embed')
@require_human
def memory_embed(
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
    model: str = typer.Option(
        DEFAULT_EMBEDDING_MODEL,
        '--model',
        '-m',
        help='Target embedding model alias or name.',
    ),
    force: bool = typer.Option(
        False,
        '--force',
        '-f',
        help='Force re-embedding of memories even if already embedded with target model.',
    ),
    accelerate: bool = typer.Option(
        False,
        '--accelerate',
        help='Enable hardware acceleration (DirectML / CUDA) for batch embedding.',
    ),
    include_archived: bool = typer.Option(
        False,
        '--include-archived',
        help='Include archived memories in the embedding run.',
    ),
) -> None:
    """Idempotently embed or migrate all L1/L2 memories to the target model space (EP-0144)."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        engine = VectorEngine(model_name=model, accelerate=accelerate)
        if not engine.is_onnx_available or not engine.is_tokenizers_available:
            console.print(
                '[yellow]Warning: ONNX Runtime or Tokenizers package not detected.[/yellow]\n'
                'To generate local dense semantic embeddings, please install:\n'
                '  [bold]pip install "tur[embeddings]"[/bold]\n'
                'or for DirectML hardware acceleration:\n'
                '  [bold]pip install onnxruntime-directml tokenizers numpy[/bold]'
            )
            raise typer.Exit(code=1)  # noqa: TRY301

        if not engine.model_path or not engine.model_path.exists():
            console.print(
                f"[yellow]Warning: Model assets for '{model}' not found locally.[/yellow]\n"
                f'Run `tur-adm model pull {model}` to download the model and tokenizer to ~/.tur/models/.'
            )
            raise typer.Exit(code=1)  # noqa: TRY301

        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=include_archived)

        skipped_mems = 0
        updated_mems = 0

        for m in mems:
            if (
                not force
                and m.embedding_vector is not None
                and m.embedding_model
                and is_model_compatible(m.embedding_model, engine.model_name)
            ):
                skipped_mems += 1
                continue

            try:
                vec = engine.embed_text(m.content)
                m.embedding_vector = vec
                m.embedding_model = engine.model_name
                memory_manager.save(m)
                updated_mems += 1
            except Exception as embed_err:
                console.print(f"[red]Failed to embed memory '{m.id[:8]}': {embed_err}[/red]")

        # L2 Knowledge Graph node migration
        kg_path = persona_dir / 'knowledge_graph.yaml'
        skipped_nodes = 0
        updated_nodes = 0

        if kg_path.exists():
            try:
                with open(kg_path, encoding='utf-8') as f:
                    kg_data = yaml_safe_load(f.read()) or {}
                nodes = kg_data.get('nodes', [])
                for node in nodes:
                    if (
                        not force
                        and node.get('embedding_vector') is not None
                        and node.get('embedding_model')
                        and is_model_compatible(node.get('embedding_model'), engine.model_name)
                    ):
                        skipped_nodes += 1
                        continue

                    text_parts = []
                    if node.get('title'):
                        text_parts.append(str(node['title']))
                    if node.get('content'):
                        text_parts.append(str(node['content']))
                    node_text = '\n'.join(text_parts).strip() or str(node.get('id', ''))

                    try:
                        node['embedding_vector'] = engine.embed_text(node_text)
                        node['embedding_model'] = engine.model_name
                        updated_nodes += 1
                    except Exception as node_err:
                        console.print(f"[red]Failed to embed node '{node.get('id')}': {node_err}[/red]")

                if updated_nodes > 0:
                    with open(kg_path, 'w', encoding='utf-8') as f:
                        yaml.dump(kg_data, f, sort_keys=False)
            except Exception as kg_err:
                console.print(f'[yellow]Warning: Could not update knowledge graph embeddings: {kg_err}[/yellow]')

        table = Table(title=f'Embedding Migration Summary ({active_id})', box=box.ROUNDED)
        table.add_column('Target Model', style='cyan bold')
        table.add_column('L1 Processed', style='green')
        table.add_column('L1 Skipped (Valid)', style='dim')
        table.add_column('L2 Processed', style='green')
        table.add_column('L2 Skipped (Valid)', style='dim')

        table.add_row(
            engine.model_name,
            str(updated_mems),
            str(skipped_mems),
            str(updated_nodes),
            str(skipped_nodes),
        )
        console.print(table)
        console.print(f"[green]Successfully synchronized embeddings for persona '{active_id}'.[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        handle_cli_error(e, 'Error embedding memories')


# -----------------------------------------------------------------------------
# SESSION COMMANDS GROUP
# -----------------------------------------------------------------------------


@session_app.command('list')
@require_human
def session_list(
    identifier: str | None = typer.Argument(None, help=HELP_ADMIN_PERSONA_ARG),
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
            table.add_row(
                s.id,
                get_session_status_style(s.status),
                s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            )
        console.print(table)
    except Exception as e:
        handle_cli_error(e, 'Error listing sessions')


@session_app.command('start')
@require_human
def start_session(
    session_id: str = typer.Argument(..., help='The ID of the session to start.'),
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses standard.'),
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
    identifier: str | None = typer.Argument(None, help='The name or UUID of the persona. If omitted, uses standard.'),
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
    identifier: str | None = typer.Option(None, help=HELP_ADMIN_PERSONA_ARG),
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
        table.add_column('Key', style=STYLE_BOLD_CYAN)
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


# -----------------------------------------------------------------------------
# SIGNAL COMMANDS GROUP (EP-0118, EP-0141)
# -----------------------------------------------------------------------------


@signal_app.command('inspect')
@require_human
def signal_inspect(
    session_id: str | None = typer.Argument(None, help='The session ID (defaults to active session).'),
    json_mode: bool = typer.Option(False, '--json', help='Output raw JSON.'),
) -> None:
    """Inspect the inter-agent signal queue and Lamport Vector Clocks (EP-0141)."""
    try:
        resolved_sess_id = session_id or session.get_active_session_id()
        if not resolved_sess_id:
            console.print('[red]Error: No active session found. Please specify session_id.[/red]')
            raise typer.Exit(code=1)  # noqa: TRY301

        conn = session.get_db_connection(resolved_sess_id)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, sequence, timestamp, sender, recipient, type, content, vector_clock
            FROM signals
            ORDER BY sequence ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        from tur.vector_clock import VectorClock

        signals = []
        for r in rows:
            d = dict(r)
            d['vector_clock'] = VectorClock(d.get('vector_clock'))
            signals.append(d)

        if json_mode:
            console.print(json.dumps(signals, indent=2))
            return

        if not signals:
            console.print(f"No signals found in session '{resolved_sess_id}'.")
            return

        table = Table(title=f'IASP Signals & Vector Clocks ({resolved_sess_id})', show_lines=True)
        table.add_column('Seq', style='dim', justify='right')
        table.add_column('Sender -> Recipient', style='cyan')
        table.add_column('Type', style='magenta')
        table.add_column('Vector Clock', style='green')
        table.add_column('Content')

        for sig in signals:
            v_clock_str = json.dumps(sig['vector_clock']) if sig['vector_clock'] else '{}'
            content_snippet = sig['content'][:80] + ('...' if len(sig['content']) > 80 else '')
            table.add_row(
                str(sig['sequence']),
                f'{sig["sender"]} -> {sig["recipient"]}',
                sig['type'],
                v_clock_str,
                content_snippet,
            )
        console.print(table)
    except Exception as e:
        console.print(f'[red]Error inspecting signals: {e}[/red]')
        raise typer.Exit(code=1)


def _resolve_target_stores(scope: str, global_only: bool, local_only: bool) -> list[tuple[str, Path]]:
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
    stores: list[tuple[str, Path]],
) -> tuple[list[tuple[str, Path]], list[tuple[str, Path]], list[Path]]:
    orphaned_dirs: list[tuple[str, Path]] = []
    dangling_files: list[tuple[str, Path]] = []
    retained_personas: list[Path] = []

    for store_label, base_dir in stores:
        if not base_dir.exists():
            continue

        index_file = base_dir / PERSONAS_FILENAME
        valid_ids: set[str] = set()
        if index_file.exists():
            with contextlib.suppress(Exception), open(index_file, encoding='utf-8') as f:
                data = yaml_safe_load(f)
                idx = PersonaIndex(**data)
                for p in idx.personas:
                    valid_ids.add(str(p.id))
                    valid_ids.add(p.name.lower())

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


def _execute_hygiene_removals(orphaned_dirs: list[tuple[str, Path]], dangling_files: list[tuple[str, Path]]) -> None:
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
    with console.status('[bold cyan]Verifying cryptographic Merkle integrity...[/bold cyan]', spinner='dots'):
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


@app.command(name='scaffold', help='Generate repository-level AI agent scaffolding (AGENTS.md or CLAUDE.md).')
def scaffold_cmd(
    format: str = typer.Option('aaif', '--format', '-f', help='Scaffold format: "aaif" (default) or "claude"'),
    output: Path | None = typer.Option(
        None, '--output', '-o', help='Target output filepath (defaults to AGENTS.md or CLAUDE.md)'
    ),
    force: bool = typer.Option(False, '--force', help='Overwrite existing scaffold file without error'),
) -> None:
    """Generates repository-level AI agent guidelines conforming to AAIF or Claude Code standards."""
    run_scaffold_cli(format=format, output=output, force=force)


# -----------------------------------------------------------------------------
# MODEL COMMANDS GROUP (EP-0144)
# -----------------------------------------------------------------------------


@model_app.command('list')
@require_human
def model_list() -> None:
    """List available recommended ONNX embedding models and local download status."""
    try:
        models_base = resolve_models_dir()
        table = Table(title='ONNX Embedding Models (EP-0144)', box=box.ROUNDED)
        table.add_column('Alias', style='cyan bold')
        table.add_column('Canonical ID', style='bold')
        table.add_column('Dimensions', justify='right')
        table.add_column('Size (MB)', justify='right')
        table.add_column('HuggingFace Repo', style='dim')
        table.add_column('Status')

        for alias, info in RECOMMENDED_MODELS.items():
            model_id = info['id']
            cand_dir = models_base / model_id
            is_installed = cand_dir.exists() and (
                (cand_dir / 'model_quantized.onnx').exists() or (cand_dir / 'model.onnx').exists()
            )
            status_str = '[bold green]Installed[/bold green]' if is_installed else '[dim]Available[/dim]'
            table.add_row(
                alias,
                model_id,
                str(info['dim']),
                f'{info["size_mb"]:.1f}',
                info['repo'],
                status_str,
            )

        console.print(table)
    except Exception as e:
        handle_cli_error(e, 'Error listing models')


@model_app.command('status')
@require_human
def model_status() -> None:
    """Inspect local hardware acceleration providers, tokenizers, and active models."""
    try:
        engine = VectorEngine()
        models_base = resolve_models_dir()

        installed_models: list[str] = []
        if models_base.exists():
            for child in models_base.iterdir():
                if child.is_dir() and ((child / 'model_quantized.onnx').exists() or (child / 'model.onnx').exists()):
                    installed_models.append(child.name)

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column('Property', style='bold cyan')
        table.add_column('Value')

        tok_status = '[green]Yes[/green]' if engine.is_tokenizers_available else '[red]No[/red]'
        table.add_row('ONNX Runtime Available', '[green]Yes[/green]' if engine.is_onnx_available else '[red]No[/red]')
        table.add_row('Tokenizers Available', tok_status)

        providers_str = 'None'
        if engine.is_onnx_available:
            with contextlib.suppress(Exception):
                import onnxruntime as ort

                providers_str = ', '.join(ort.get_available_providers())
        table.add_row('Hardware Providers', providers_str)
        table.add_row('Default Model Name', engine.model_name)
        active_path_str = str(engine.model_path) if engine.model_path else '[yellow]None (not downloaded)[/yellow]'
        table.add_row('Active Model Path', active_path_str)
        table.add_row('Models Base Directory', str(models_base))
        table.add_row('Installed Models', ', '.join(installed_models) if installed_models else 'None')

        console.print(Panel(table, title='[bold]ONNX Embedding Subsystem Status[/bold]', border_style='cyan'))
    except Exception as e:
        handle_cli_error(e, 'Error checking model status')


@model_app.command('pull')
@require_human
def model_pull(
    model_alias: str = typer.Argument('minilm', help='Model alias (minilm, bge-small, e5-small) or HuggingFace repo.'),
    force: bool = typer.Option(False, '--force', '-f', help='Force re-download even if already present.'),
    target: Path | None = typer.Option(None, '--target', '-t', help='Custom destination directory.'),
) -> None:
    """Download ONNX quantized model and tokenizer files from HuggingFace."""
    import urllib.error
    import urllib.request

    try:
        alias_lower = model_alias.lower()
        if alias_lower in RECOMMENDED_MODELS:
            info = RECOMMENDED_MODELS[alias_lower]
            canonical_id = info['id']
            repo = info['repo']
            files = info['files']
        elif '/' in model_alias:
            repo = model_alias
            canonical_id = model_alias.split('/')[-1]
            files = ['onnx/model_quantized.onnx', 'tokenizer.json']
        else:
            matched = next((v for v in RECOMMENDED_MODELS.values() if v['id'].lower() == alias_lower), None)
            if matched:
                canonical_id = matched['id']
                repo = matched['repo']
                files = matched['files']
            else:
                rec_keys = ', '.join(RECOMMENDED_MODELS.keys())
                console.print(
                    f"[red]Error: Unknown model alias '{model_alias}'.[/red]\n"
                    f'Choose from: {rec_keys} or specify a full HuggingFace repo (e.g. Xenova/all-MiniLM-L6-v2).'
                )
                raise typer.Exit(code=1)  # noqa: TRY301

        dest_dir = target if target is not None else resolve_models_dir(canonical_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[bold]Fetching '{canonical_id}' from HuggingFace repo '{repo}'...[/bold]")
        console.print(f'Destination: [cyan]{dest_dir}[/cyan]')

        from tur import __version__

        headers = {'User-Agent': f'tur-adm/{__version__}'}

        for remote_file in files:
            local_name = remote_file.split('/')[-1]
            local_path = dest_dir / local_name

            if local_path.exists() and not force:
                console.print(f'  - [dim]{local_name} already exists (skipping). Use --force to re-download.[/dim]')
                continue

            url = f'https://huggingface.co/{repo}/resolve/main/{remote_file}'
            console.print(f'  - Downloading [cyan]{local_name}[/cyan] from {url}...')
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req) as resp:
                    data = resp.read()
            except urllib.error.HTTPError as http_err:
                if 'model_quantized.onnx' in remote_file and http_err.code == 404:
                    alt_remote = remote_file.replace('model_quantized.onnx', 'model.onnx')
                    alt_url = f'https://huggingface.co/{repo}/resolve/main/{alt_remote}'
                    console.print(f'  - [yellow]model_quantized not found, falling back to {alt_url}...[/yellow]')
                    alt_req = urllib.request.Request(alt_url, headers=headers)
                    with urllib.request.urlopen(alt_req) as alt_resp:
                        data = alt_resp.read()
                else:
                    raise

            tmp_fd, tmp_file = tempfile.mkstemp(dir=dest_dir, prefix=f'{local_name}.tmp.')
            try:
                with open(tmp_fd, 'wb') as f:
                    f.write(data)
                shutil.move(tmp_file, local_path)
            finally:
                if Path(tmp_file).exists():
                    with contextlib.suppress(OSError):
                        Path(tmp_file).unlink()

            size_mb = len(data) / (1024 * 1024)
            console.print(f'  - [green]Successfully saved {local_name} ({size_mb:.2f} MB)[/green]')

        console.print(f"[bold green]Model '{canonical_id}' is ready for vector retrieval.[/bold green]")
    except typer.Exit:
        raise
    except Exception as e:
        handle_cli_error(e, f"Error pulling model '{model_alias}'")


@model_app.command('remove')
@require_human
def model_remove(
    model_alias: str = typer.Argument(..., help='Model alias or name to delete.'),
    yes: bool = typer.Option(False, '--yes', '-y', help='Confirm deletion without interactive prompt.'),
) -> None:
    """Delete a local model directory from ~/.tur/models/."""
    try:
        alias_lower = model_alias.lower()
        canonical_id = model_alias
        if alias_lower in RECOMMENDED_MODELS:
            canonical_id = RECOMMENDED_MODELS[alias_lower]['id']
        elif alias_lower in MODEL_ALIASES:
            canonical_id = MODEL_ALIASES[alias_lower]

        cand_dir = resolve_models_dir(canonical_id)
        if not cand_dir.exists():
            console.print(f"[yellow]No local model directory found for '{canonical_id}' at '{cand_dir}'.[/yellow]")
            return

        if not yes and not typer.confirm(f"Are you sure you want to delete '{cand_dir}'?"):
            console.print('Deletion cancelled.')
            return

        shutil.rmtree(cand_dir)
        console.print(f"[green]Successfully removed model directory: '{cand_dir}'[/green]")
    except Exception as e:
        handle_cli_error(e, f"Error removing model '{model_alias}'")


def main():
    app()


if __name__ == '__main__':
    main()
