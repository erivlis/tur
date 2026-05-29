import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

import typer
import yaml
from rich.console import Console

# Import logic directly from main.py
from tur import dreaming, persona, session, tui, user
from tur.compiler import compile_persona
from tur.memory import MemoryManager
from tur.models import (
    Memory,
    MemoryScope,
    MemoryType,
    Persona,
    PersonaIndex,
    PersonaIndexEntry,
    SessionNotes,
    SessionState,
    SystemState,
)
from tur.paths import resolve_personas_base_dir
from tur.telemetry import CognitiveTelemetry

app = typer.Typer(
    help="Tur: Persona Lifecycle Manager (Wake/Sleep)",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
)
session_app = typer.Typer(
    help="Manage sessions (administrative tools).",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
)
app.add_typer(session_app, name="session")
console = Console()


# -----------------------------------------------------------------------------
# THE GOLEM PROTOCOL: TTY Lock
# -----------------------------------------------------------------------------
def require_human(func):
    """
    Heuristic TTY check used as a soft safety convention to discourage Harness Agents
    from executing administrative commands via headless shell execution.

    NOTE: This is a convention, not a security control.  sys.stdout.isatty() can be
    satisfied by pseudo-TTY wrappers.  Do not rely on this for hard security boundaries.
    """
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not sys.stdout.isatty():
            console.print("[red]Error: Administrative command invoked in a non-interactive shell.[/red]")
            console.print("[red]GOLEM PROTOCOL VIOLATION: Agents must use the MCP Server for state access.[/red]")
            raise typer.Exit(code=1)
        return func(*args, **kwargs)

    return wrapper


@app.command("export")
@require_human
def export(
        identifier: str = typer.Argument(..., help="The name or UUID of the persona to export"),
        output_path: Path = typer.Argument(..., help="The target filepath for the export archive (e.g., ariel.tur)")
):
    """Package a global persona's core config and universal memories into a portable .tur archive.

    The archive contains:
      - persona.yaml  (core identity config, with 'id' field injected from the registry)
      - memories/     (universal/persona-scoped memories only; incarnation memories are NOT included)

    Use 'tur import' on another machine to register the persona globally there.
    """
    try:
        import io
        import tarfile
        persona_dir = persona.get_persona_path(identifier)
        persona_uuid = persona_dir.name  # directory name IS the canonical UUID
        output_path = output_path.resolve()

        with tarfile.open(output_path, "w:gz") as tar:
            # 1. Add persona.yaml, injecting the 'id' field so import can validate identity
            persona_yaml_path = persona_dir / "persona.yaml"
            if persona_yaml_path.exists():
                with open(persona_yaml_path, encoding="utf-8") as f:
                    persona_data = yaml.safe_load(f) or {}
                persona_data.setdefault("id", persona_uuid)  # inject if absent
                yaml_bytes = yaml.dump(persona_data, sort_keys=False).encode("utf-8")
                info = tarfile.TarInfo(name="persona.yaml")
                info.size = len(yaml_bytes)
                tar.addfile(info, io.BytesIO(yaml_bytes))

            # 2. Add universal memories directory
            memories_dir = persona_dir / "memories"
            if memories_dir.exists():
                tar.add(memories_dir, arcname="memories")

        console.print(f"[green]Persona '{identifier}' successfully exported to '{output_path}'[/green]")
    except Exception as e:
        console.print(f"[red]Error exporting persona: {e}[/red]")


@app.command("import")
@require_human
def import_persona(
        archive_path: Path = typer.Argument(..., help="The filepath to the .tur archive to import")
):
    """Unpack a .tur archive and register the global persona on this machine."""
    try:
        import shutil
        import tarfile
        import tempfile
        from uuid import UUID

        from tur.models import PersonaIndexEntry

        archive_path = archive_path.resolve()
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        # 1. Inspect archive in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with tarfile.open(archive_path, "r:gz") as tar:
                # C1 FIX: Sanitize all member paths before extraction to prevent path traversal.
                for member in tar.getmembers():
                    member_path = (tmp_path / member.name).resolve()
                    if not str(member_path).startswith(str(tmp_path.resolve())):
                        raise ValueError(
                            f"Archive contains a path traversal entry and cannot be trusted: '{member.name}'"
                        )
                tar.extractall(path=tmp_path)

            persona_yaml = tmp_path / "persona.yaml"
            if not persona_yaml.exists():
                raise ValueError("Invalid archive: persona.yaml is missing.")

            with open(persona_yaml, encoding="utf-8") as f:
                persona_data = yaml.safe_load(f)

            import uuid
            persona_id = persona_data.get("id")
            if not persona_id:
                # H3 FIX: Identity cannot be conjured at import time.  Reject the archive.
                raise ValueError(
                    "Invalid archive: persona.yaml is missing an 'id' field.  "
                    "This archive cannot be imported — identity must be established at persona creation."
                )
            persona_name = persona_data.get("name")
            persona_version = persona_data.get("version", "unknown")

            if not persona_name:
                raise ValueError("Invalid persona.yaml in archive: missing name.")

            # 2. Extract globally — use shared resolver (never silently falls to local on fresh machine)
            global_base = resolve_personas_base_dir()
            # If the registry is absent entirely, initialise it rather than silently rerouting
            global_home = Path.home() / ".tur"
            if not (global_home / "personas.yaml").exists():
                global_home.mkdir(parents=True, exist_ok=True)
                (global_home / "personas.yaml").write_text(
                    "personas: []\n", encoding="utf-8"
                )
                global_base = global_home
                console.print(
                    "[yellow]Warning: ~/.tur/personas.yaml not found — "
                    "initialized a new global registry.[/yellow]"
                )

            dest_dir = global_base / "personas" / str(persona_id)
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy extracted files
            shutil.copytree(tmp_path, dest_dir, dirs_exist_ok=True)

            # 3. Register in master index
            index_path = global_base / "personas.yaml"
            if index_path.exists():
                with open(index_path, encoding="utf-8") as f:
                    index_data = yaml.safe_load(f) or {"personas": []}
                index = PersonaIndex(**index_data)
            else:
                index = PersonaIndex(personas=[])

            # Append if not registered
            existing = next((p for p in index.personas if str(p.id) == str(persona_id)), None)
            if not existing:
                entry = PersonaIndexEntry(id=UUID(persona_id), name=persona_name, version=persona_version)
                index.personas.append(entry)
                with open(index_path, "w", encoding="utf-8") as f:
                    yaml.dump(index.model_dump(mode='json'), f, sort_keys=False)

        console.print(
            f"[green]Persona '{persona_name}' ({persona_id}) successfully imported from '{archive_path}'[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error importing persona: {e}[/red]")


@app.command()
@require_human
def forget(
        memory_id: str = typer.Argument(..., help="The ID (hash) of the memory to forget"),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Archive a memory by its ID for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_manager.archive(memory_id)
        console.print(f"[green]Memory {memory_id} has been forgotten (archived).[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
@require_human
def init():
    """Bootstrap a new persona via an interactive TUI questionnaire."""
    tui.init_wizard()


@app.command()
@require_human
def memories(
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        include_archived: bool = typer.Option(False, help="Include forgotten memories")
):
    """Show all memories in the bank for a specific persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=include_archived)

        if not mems:
            console.print(f"The Memory Bank for {active_id} is empty.")
            return

        from rich.table import Table

        table = Table(title=f"Memory Bank ({active_id})", show_lines=True)
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Content")

        for m in mems:
            content_snippet = (m.content[:80] + '..') if len(m.content) > 80 else m.content
            status_display = "archived" if getattr(m, 'status', None) == "archived" else "active"
            row_style = "dim" if status_display == "archived" else ""

            table.add_row(str(m.id), m.type.value, status_display, content_snippet, style=row_style)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
# Intentionally bypassing TTY lock to allow agents to write their own memories via Harness CLI execution
def learn(
        content: str = typer.Argument(..., help="The content of the memory to store."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        type: MemoryType = typer.Option(MemoryType.INSIGHT, help="The type of memory."),
        scope: MemoryScope = typer.Option(MemoryScope.INCARNATION, help="The scope of the memory."),
        session_id: str = typer.Option(None, help="The name/ID of the session this memory belongs to")
):
    """Create a new memory for a persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)

        console.print(f"Consolidating memory for '{active_id}': '{content[:50]}...' [{scope.value}]")

        memory = Memory(
            type=type,
            scope=scope,
            tags=["manual", "cli"],
            content=content,
            source_session=session_id
        )
        saved_path = memory_manager.save(memory)
        console.print(f"[green]Memory saved to {saved_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
# Intentionally bypassing TTY lock to allow agents to query memories
def recall(
        query: str = typer.Argument(..., help="The topic or concept to search for in past memories."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Search your deep memory bank for past events, decisions, or knowledge."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=False)

        query_lower = query.lower()
        results = [m for m in mems
                   if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)]

        if not results:
            console.print(f"No memories found matching query: '{query}'")
            return

        import json
        mem_list = [{"id": str(m.id), "type": m.type.value, "content": m.content} for m in results]
        console.print(json.dumps(mem_list, indent=2))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
# Intentionally bypassing TTY lock to allow agents to update their own continuity
def note(
        content: str = typer.Argument(..., help="The transient content/note of the current session state."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        session_id: str | None = typer.Option(None, help="The session ID to isolate this note to.")
):
    """Append a note to the active session's notes.yaml."""
    try:
        res = session.note_logic(content, session_id=session_id, identifier=identifier)
        console.print(f"[green]{res}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving note: {e}[/red]")
        raise typer.Exit(code=1)


@session_app.command("start")
@require_human
def start_session(
        session_id: str = typer.Argument(..., help="The ID of the session to start."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Create a new isolated session under the active persona."""
    try:
        res = session.start_session_logic(session_id, identifier=identifier)
        console.print(f"[green]{res}[/green]")
    except Exception as e:
        console.print(f"[red]Error starting session: {e}[/red]")
        raise typer.Exit(code=1)


@session_app.command("end")
@require_human
def end_session(
        session_id: str = typer.Argument(..., help="The ID of the session to end."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Mark the session as ended."""
    try:
        res = session.end_session_logic(session_id, identifier=identifier)
        console.print(f"[green]{res}[/green]")
    except Exception as e:
        console.print(f"[red]Error ending session: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def serve(
        transport: str = typer.Option("stdio",
                                      help="The transport protocol for the MCP server ('stdio' or 'sse')."),
        port: int = typer.Option(8000, help="Port to use when transport is 'sse'.")
):
    """Run the Tur MCP server."""
    try:
        from tur.mcp_server import main as mcp_main
        console.print(f"[bold green]Starting Tur MCP server with {transport} transport...[/bold green]")
        mcp_main(transport=transport, port=port)
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        sys.exit(1)


@app.command()
# Intentionally bypassing TTY lock to allow agents to dehydrate their own sessions via CLI
def sleep(
        log_path: str = typer.Argument(..., help="Path to the chat log file to be parsed."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        session_id: str = typer.Option(None, help="The name/ID of the session these memories belong to"),
        model: str = typer.Option("gemini-3.1-pro-preview", help="The model to use for dreaming (insight extraction)"),
        note: str = typer.Option(
            ..., "-n", "--note", help="Final note/utterance to append before sleeping."
        )
):
    """Dehydrate a session by parsing a chat log to extract memories."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        resolved_session_id = session_id or session.get_active_session_id()

        # Append final note
        if resolved_session_id:
            session.note_logic(note, session_id=resolved_session_id, identifier=identifier)
            console.print(f"[green]Final note appended to session '{resolved_session_id}'.[/green]")

            # Auto-end session on sleep
            res_end = session.end_session_logic(resolved_session_id, identifier=identifier)
            console.print(f"[dim]Auto-ended session: {res_end}[/dim]")

        console.print(f"Processing session log for '{active_id}' from {log_path}...")
        console.print(f"Extracting insights using {model}... (Dreaming)")

        try:
            count = dreaming.perform_sleep_dreaming(
                log_content=Path(log_path).read_text(encoding="utf-8"),
                active_id=active_id,
                session_id=resolved_session_id,
                model=model
            )

            console.print(f"[bold green]Dreams consolidated. {count} new memories formed.[/bold green]")

        except Exception as e:
            console.print(f"[red]Error during dreaming: {e}[/red]")

        console.print("[bold green]State saved. Persona is now sleeping.[/bold green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
@require_human
def switch():
    """Switch active default persona via an interactive TUI picker."""
    try:
        base_dir = resolve_personas_base_dir()
        index_path = base_dir / "personas.yaml"
        if not index_path.exists():
            console.print("[red]No personas found. Please run `tur init` to create one.[/red]")
            raise typer.Exit(code=1)

        with open(index_path, encoding="utf-8") as f:
            index_data = yaml.safe_load(f)
        index = PersonaIndex(**index_data)

        if not index.personas:
            console.print("[red]No personas available to select. Please run `tur init`.[/red]")
            raise typer.Exit(code=1)

        selected_id = tui.select_persona_wizard(index)
        if selected_id:
            matched = next((p for p in index.personas if str(p.id) == selected_id), None)
            persona_name = matched.name if matched else selected_id
            console.print(f"[green]Default persona switched to: '{persona_name}' ({selected_id})[/green]")
        else:
            console.print("[yellow]Switch cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error switching persona: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
# Intentionally bypassing TTY lock to allow agents to query cognitive load
def telemetry(
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Calculate Constraint Dimensionality (C_p) for a persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        file_path = persona_dir / "persona.yaml"

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        persona_obj = Persona(**data)

        # Mock state for compilation measurement
        user_profile = user.get_user_profile()
        state = SessionState(persona=persona_obj, user=user_profile, memories=[])
        system_prompt = compile_persona(state)

        telemetry_engine = CognitiveTelemetry()
        static_metrics = telemetry_engine.measure_static_load(system_prompt)
        cp = telemetry_engine.calculate_constraint_dimensionality(persona_obj)

        console.print(f"[bold cyan]--- TELEMETRY REPORT: {persona_obj.name} ---[/bold cyan]")
        console.print(f"Active Persona: {active_id} ({persona_obj.name})")
        console.print(f"Constraint Dimensionality (Cp): [bold]{cp}[/bold]")

        # The Giant Rating
        if cp < 5:
            rating = "Human (Manageable)"
            color = "green"
        elif cp < 10:
            rating = "Giant (Heavy Load)"
            color = "yellow"
        else:
            rating = "Titan (Inference Warning)"
            color = "red"

        console.print(f"Class: [{color}]{rating}[/{color}]")

        console.print("---")
        console.print(f"Static Token Cost: ~{static_metrics['est_tokens']}")
        console.print(f"Information Density: {static_metrics['density']}")
        console.print("---")

    except Exception as e:
        console.print(f"[red]Error calculating telemetry: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
# Intentionally bypassing TTY lock to allow agents to query their own state
def status(
        identifier: str | None = typer.Argument(
            None,
            help="The name or UUID of the persona. If omitted, uses the default."
        )
):
    """Show the current persona, session, and memory status."""
    from rich import box
    from rich.panel import Panel
    from rich.table import Table

    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        # --- Persona info ---
        persona_yaml = persona_dir / "persona.yaml"
        persona_name = active_id
        persona_version = "unknown"
        if persona_yaml.exists():
            try:
                with open(persona_yaml, encoding="utf-8") as f:
                    pdata = yaml.safe_load(f)
                persona_name = pdata.get("name", active_id)
                persona_version = pdata.get("version", "unknown")
            except Exception:
                pass

        # --- Session info ---
        session_id = session.get_active_session_id()
        session_status = "none"
        session_created = "-"
        session_updated = "-"
        note_count = 0
        latest_note = "-"

        index = session.load_session_index(persona_dir)

        if session_id:
            entry = next((s for s in index.sessions if s.id == session_id), None)
            if entry:
                session_status = entry.status
                session_created = entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
                session_updated = entry.updated_at.strftime("%Y-%m-%d %H:%M:%S")

            notes_yaml_path = session.get_session_file(persona_dir, session_id)
            if notes_yaml_path.exists():
                try:
                    with open(notes_yaml_path, encoding="utf-8") as f:
                        notes_data = yaml.safe_load(f)
                    session_notes = SessionNotes(**notes_data)
                    note_count = len(session_notes.notes)
                    if session_notes.notes:
                        last = sorted(session_notes.notes, key=lambda n: n.timestamp, reverse=True)[0]
                        snippet = last.content[:80].replace("\n", " ")
                        if len(last.content) > 80:
                            snippet += "…"
                        latest_note = snippet
                except Exception:
                    pass
        elif index.sessions:
            # No active session — show most recently touched one
            most_recent = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)[0]
            session_id = most_recent.id + " (last)"
            session_status = most_recent.status
            session_updated = most_recent.updated_at.strftime("%Y-%m-%d %H:%M:%S")

        # --- Memory count ---
        memory_manager = MemoryManager(base_dir=persona_dir)
        memories = memory_manager.load_all()
        memory_count = len(memories)

        # --- Render ---
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Key", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Persona", f"{persona_name} [dim](v{persona_version})[/dim]")
        table.add_row("Persona ID", active_id)
        table.add_row("", "")
        table.add_row("Session ID", session_id or "[dim]none[/dim]")
        table.add_row("Status", f"[green]{session_status}[/green]" if session_status == "active"
        else f"[dim]{session_status}[/dim]")
        table.add_row("Started", session_created)
        table.add_row("Updated", session_updated)
        table.add_row("Notes", str(note_count))
        table.add_row("Latest note", f"[dim]{latest_note}[/dim]")
        table.add_row("", "")
        table.add_row("Memories", str(memory_count))

        console.print(Panel(table, title="[bold]Tur Status[/bold]", border_style="cyan"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
# Note: wake is intentionally left without @require_human so headless adapters can fetch the prompt.
def wake(
        session_id: str | None = typer.Option(
            None,
            help="The session ID to resume or wake under. If omitted, uses active or auto-starts one."
        ),
        from_session: str | None = typer.Option(
            None,
            help="Optional ID of a previous session whose last note will seed a newly started session."
        ),
        identifier: str | None = typer.Argument(
            None,
            help="The name or UUID of the persona. If omitted, uses the default."
        )
):
    """Wake the persona and compile the prompt."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        _persona_dir = persona.get_persona_path(active_id)

        resolved_session_id = session_id or session.get_active_session_id()
        is_auto_started = False

        if not resolved_session_id:
            import uuid
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_hex = uuid.uuid4().hex[:8]
            resolved_session_id = f"{ts}_{short_hex}"
            is_auto_started = True

            session.start_session_logic(resolved_session_id, identifier=active_id, previous_session_id=from_session)

        # Update .tur/state.yaml
        state_path = Path(".tur/state.yaml")
        if state_path.exists():
            try:
                with open(state_path, encoding="utf-8") as f:
                    state_data = yaml.safe_load(f)
                state_obj = SystemState(**state_data)
                changed = False
                if state_obj.active_persona_id != UUID(active_id):
                    state_obj.active_persona_id = UUID(active_id)
                    changed = True
                if state_obj.active_session_id != resolved_session_id:
                    state_obj.active_session_id = resolved_session_id
                    changed = True
                if changed:
                    with open(state_path, "w", encoding="utf-8") as f:
                        yaml.dump(state_obj.model_dump(mode="json"), f)
            except Exception:
                pass
        else:
            try:
                state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=resolved_session_id)
                state_path.parent.mkdir(parents=True, exist_ok=True)
                with open(state_path, "w", encoding="utf-8") as f:
                    yaml.dump(state_obj.model_dump(mode="json"), f)
            except Exception:
                pass

        state = session.hydrate_session_state(active_id, session_id=resolved_session_id)

        # Compile (The Awakening)
        system_prompt = compile_persona(state)

        # Output
        console.print(f"[bold green]--- SYSTEM WAKE: {state.persona.name} (v{state.persona.version}) ---[/bold green]")
        console.print(f"[dim]Active Persona: {active_id} ({state.persona.name})[/dim]")
        if resolved_session_id:
            console.print(f"[dim]Session ID: {resolved_session_id}[/dim]")
        if is_auto_started:
            console.print(f"[dim]Auto-started new session: {resolved_session_id}[/dim]")

        console.print(system_prompt)
        console.print("[bold green]--- SYSTEM READY ---[/bold green]")

    except Exception as e:
        console.print(f"[red]Error waking persona: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
