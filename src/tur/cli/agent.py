from datetime import datetime
from pathlib import Path
from uuid import UUID

import typer
import yaml
from tur._helpers import yaml_safe_load

from tur import persona, session
from tur.cli.common import console
from tur.compiler import compile_persona
from tur.memory import MemoryManager
from tur.models import (
    Memory,
    MemoryScope,
    MemoryType,
    SessionNotes,
    SystemState,
)

app = typer.Typer(
    help='Tur: Persona safe agent runtime.',
    context_settings={'help_option_names': ['-h', '--help']},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode='rich',
)


@app.command()
def wake(
    session_id: str | None = typer.Option(
        None, help='The session ID to resume or wake under. If omitted, uses active or auto-starts one.'
    ),
    from_session: str | None = typer.Option(
        None, help='Optional ID of a previous session whose last note will seed a newly started session.'
    ),
    agent_id: str | None = typer.Option(None, help='The unique agent ID representing this manifestation.'),
    harness_conversation_id: str | None = typer.Option(None, help='The harness conversation ID.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Wake the persona and compile the prompt."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        _persona_dir = persona.get_persona_path(active_id)

        resolved_session_id = session_id or session.get_active_session_id()
        is_auto_started = False

        if not resolved_session_id:
            import uuid

            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            short_hex = uuid.uuid4().hex[:8]
            resolved_session_id = f'{ts}_{short_hex}'
            is_auto_started = True

        session.start_session_logic(
            resolved_session_id,
            identifier=active_id,
            previous_session_id=from_session,
            agent_id=agent_id,
            harness_conversation_id=harness_conversation_id,
        )

        # Update .tur/state.yaml
        state_path = Path('.tur/state.yaml')
        if state_path.exists():
            try:
                with open(state_path, encoding='utf-8') as f:
                    state_data = yaml_safe_load(f)
                state_obj = SystemState(**state_data)
                changed = False
                if state_obj.active_persona_id != UUID(active_id):
                    state_obj.active_persona_id = UUID(active_id)
                    changed = True
                if state_obj.active_session_id != resolved_session_id:
                    state_obj.active_session_id = resolved_session_id
                    changed = True
                if changed:
                    with open(state_path, 'w', encoding='utf-8') as f:
                        yaml.dump(state_obj.model_dump(mode='json'), f)
            except Exception:
                pass
        else:
            try:
                state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=resolved_session_id)
                state_path.parent.mkdir(parents=True, exist_ok=True)
                with open(state_path, 'w', encoding='utf-8') as f:
                    yaml.dump(state_obj.model_dump(mode='json'), f)
            except Exception:
                pass

        state = session.hydrate_session_state(active_id, session_id=resolved_session_id)

        # Compile (The Awakening)
        system_prompt = compile_persona(state)

        # Output
        console.print(f'[bold green]--- SYSTEM WAKE: {state.persona.name} (v{state.persona.version}) ---[/bold green]')
        console.print(f'[dim]Active Persona: {active_id} ({state.persona.name})[/dim]')
        if resolved_session_id:
            console.print(f'[dim]Session ID: {resolved_session_id}[/dim]')
        if is_auto_started:
            console.print(f'[dim]Auto-started new session: {resolved_session_id}[/dim]')

        console.print(system_prompt)
        console.print('[bold green]--- SYSTEM READY ---[/bold green]')

    except Exception as e:
        console.print(f'[red]Error during wake: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def learn(
    content: str = typer.Argument(..., help='The content of the memory to store.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    type: MemoryType = typer.Option(MemoryType.INSIGHT, help='The type of memory.'),
    scope: MemoryScope = typer.Option(MemoryScope.INCARNATION, help='The scope of the memory.'),
    session_id: str = typer.Option(None, help='The name/ID of the session this memory belongs to'),
):
    """Create a new memory for a persona."""
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)

        console.print(f"Consolidating memory for '{active_id}': '{content[:50]}...' [{scope.value}]")

        memory = Memory(type=type, scope=scope, tags=['manual', 'cli'], content=content, source_session=session_id)
        saved_path = memory_manager.save(memory)
        console.print(f'[green]Memory saved to {saved_path}[/green]')

    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def recall(
    query: str = typer.Argument(..., help='The topic or concept to search for in past memories.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Search your deep memory bank for past events, decisions, or knowledge."""
    try:
        from tur.recall import topological_recall
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        result_json = topological_recall(query, persona_dir)
        console.print(result_json)

    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def note(
    content: str = typer.Argument(..., help='The transient content/note of the current session state.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    session_id: str | None = typer.Option(None, help='The session ID to isolate this note to.'),
):
    """Append a note to the active session's notes.yaml."""
    try:
        res = session.note_logic(content, session_id=session_id, identifier=identifier)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error saving note: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def status(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Show the current persona, session, and memory status."""
    from rich import box
    from rich.panel import Panel
    from rich.table import Table

    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        # --- Persona info ---
        persona_yaml = persona_dir / 'persona.yaml'
        persona_name = active_id
        persona_version = 'unknown'
        if persona_yaml.exists():
            try:
                with open(persona_yaml, encoding='utf-8') as f:
                    pdata = yaml_safe_load(f)
                persona_name = pdata.get('name', active_id)
                persona_version = pdata.get('version', 'unknown')
            except Exception:
                pass

        # --- Session info ---
        session_id = session.get_active_session_id()
        session_status = 'none'
        session_created = '-'
        session_updated = '-'
        note_count = 0
        latest_note = '-'

        index = session.load_session_index(persona_dir)

        if session_id:
            entry = next((s for s in index.sessions if s.id == session_id), None)
            if entry:
                session_status = entry.status
                session_created = entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
                session_updated = entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')

            notes_yaml_path = session.get_session_file(persona_dir, session_id)
            if notes_yaml_path.exists():
                try:
                    with open(notes_yaml_path, encoding='utf-8') as f:
                        notes_data = yaml_safe_load(f)
                    session_notes = SessionNotes(**notes_data)
                    note_count = len(session_notes.notes)
                    if session_notes.notes:
                        last = sorted(session_notes.notes, key=lambda n: n.timestamp, reverse=True)[0]
                        snippet = last.content[:80].replace('\n', ' ')
                        if len(last.content) > 80:
                            snippet += '…'
                        latest_note = snippet
                except Exception:
                    pass
        elif index.sessions:
            # No active session — show most recently touched one
            most_recent = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)[0]
            session_id = most_recent.id + ' (last)'
            session_status = most_recent.status
            session_updated = most_recent.updated_at.strftime('%Y-%m-%d %H:%M:%S')

        # --- Memory count ---
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_count = memory_manager.count_all()

        # --- Render ---
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column('Key', style='bold cyan', no_wrap=True)
        table.add_column('Value', style='white')

        table.add_row('Persona', f'{persona_name} [dim](v{persona_version})[/dim]')
        table.add_row('Persona ID', active_id)
        table.add_row('', '')
        table.add_row('Session ID', session_id or '[dim]none[/dim]')
        table.add_row(
            'Status',
            f'[green]{session_status}[/green]' if session_status == 'active' else f'[dim]{session_status}[/dim]',
        )
        table.add_row('Started', session_created)
        table.add_row('Updated', session_updated)
        table.add_row('Notes', str(note_count))
        table.add_row('Latest note', f'[dim]{latest_note}[/dim]')
        table.add_row('', '')
        table.add_row('Memories', str(memory_count))

        console.print(Panel(table, title='[bold]Tur Status[/bold]', border_style='cyan'))

    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def sleep(
    log_path: str = typer.Argument(..., help='Path to the chat log file to be parsed.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    session_id: str = typer.Option(None, help='The name/ID of the session these memories belong to'),
    model: str = typer.Option('gemini-3.1-pro-preview', help='The model to use for dreaming (insight extraction)'),
    note: str = typer.Option(..., '-n', '--note', help='Final note/utterance to append before sleeping.'),
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
            console.print(f'[dim]Auto-ended session: {res_end}[/dim]')

        console.print(f"Processing session log for '{active_id}' from {log_path}...")
        console.print(f'Extracting insights using {model}... (Dreaming)')

        try:
            from tur import dreaming
            count = dreaming.perform_sleep_dreaming(
                log_content=Path(log_path).read_text(encoding='utf-8'),
                active_id=active_id,
                session_id=resolved_session_id,
                model=model,
            )

            console.print(f'[bold green]Dreams consolidated. {count} new memories formed.[/bold green]')

        except Exception as e:
            console.print(f'[red]Error during dreaming: {e}[/red]')

        console.print('[bold green]State saved. Persona is now sleeping.[/bold green]')

    except Exception as e:
        console.print(f'[red]Error during sleep: {e}[/red]')
        raise typer.Exit(code=1)


def resolve_cli_context(agent_id_opt: str | None, session_id_opt: str | None):
    import os

    # 1. Resolve session_id
    sess_id = session_id_opt or session.get_active_session_id()
    if not sess_id:
        console.print("[red]Error: No active session ID found. Run 'wake' first or provide --session-id option.[/red]")
        raise typer.Exit(code=1)

    # 2. Resolve agent_id
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if (
        agent_id_opt
        and env_agent_id
        and agent_id_opt != env_agent_id
        and not agent_id_opt.startswith(env_agent_id + '.')
    ):
        console.print(
            f"[red]Error: Namespace violation: agent_id '{agent_id_opt}' "
            f"does not match calling agent '{env_agent_id}'.[/red]"
        )
        raise typer.Exit(code=1)

    agent_id = agent_id_opt or env_agent_id
    if not agent_id:
        active_agents = []
        try:
            agents = session.list_agents_logic(sess_id)
            active_agents = [a['id'] for a in agents if a['status'] == 'active']
        except Exception:
            pass

        if len(active_agents) == 1:
            agent_id = active_agents[0]
        elif len(active_agents) > 1:
            console.print(
                f'[red]AmbiguousIdentityError: Multiple active agents found: {active_agents}. '
                f'Please specify --agent-id.[/red]'
            )
            raise typer.Exit(code=1)

    if not agent_id:
        model_slug = os.environ.get('TUR_MODEL_SLUG', 'agent')
        import uuid

        short_hex = uuid.uuid4().hex[:8]
        agent_id = f'{model_slug}_cli_{short_hex}'

    return agent_id, sess_id


@app.command()
def list_agents(
    session_id: str | None = typer.Option(None, help='Session ID. If omitted, uses active session.'),
    json_mode: bool = typer.Option(False, '--json', help='Output in JSON format.'),
):
    sess_id = session_id or session.get_active_session_id()
    if not sess_id:
        console.print('[red]Error: No active session ID found.[/red]')
        raise typer.Exit(code=1)

    try:
        agents = session.list_agents_logic(sess_id)
        if json_mode:
            import json

            console.print(json.dumps(agents, indent=2))
        else:
            from rich.table import Table

            table = Table(title=f'Manifestations in Session {sess_id}')
            table.add_column('Agent ID', style='cyan')
            table.add_column('Harness', style='magenta')
            table.add_column('Substrate', style='green')
            table.add_column('Status', style='yellow')
            table.add_column('Last Heartbeat', style='white')

            for agent in agents:
                table.add_row(
                    agent['id'], agent['harness'], agent['substrate'], agent['status'], agent['last_heartbeat']
                )
            console.print(table)
    except Exception as e:
        console.print(f'[red]Error listing agents: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def signal(
    to: str = typer.Argument(..., help='The recipient agent ID or dot-notation handle, or "*" for broadcast.'),
    content: str = typer.Argument(..., help='The content string of the signal.'),
    type: str = typer.Option('inform', help='The signal type (inform, query, delegate, ack, warn, etc.).'),
    agent_id: str | None = typer.Option(None, help='The sender agent ID.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    """Send a coordination message signal to another manifestation."""
    try:
        sender_id, sess_id = resolve_cli_context(agent_id, session_id)
        sig_id = session.signal_logic(sess_id, sender_id, to, content, type)
        console.print(f'[green]Signal sent successfully. ID: {sig_id}[/green]')
    except Exception as e:
        console.print(f'[red]Error sending signal: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def read_signals(
    unread_only: bool = typer.Option(True, '--unread-only/--all', help='Retrieve only unread signals or all.'),
    json_mode: bool = typer.Option(False, '--json', help='Output raw JSON.'),
    agent_id: str | None = typer.Option(None, help='The reader agent ID.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    """Retrieve incoming coordination signals."""
    try:
        reader_id, sess_id = resolve_cli_context(agent_id, session_id)
        signals = session.read_signals_logic(sess_id, reader_id, unread_only)

        if json_mode:
            import json

            console.print(json.dumps(signals, indent=2))
        else:
            if not signals:
                console.print('[dim]No incoming signals.[/dim]')
                return
            for sig in signals:
                console.print(f'[bold cyan][{sig["sender"]} -> {sig["recipient"]}][/bold cyan] ({sig["type"]})')
                console.print(f'  Sequence: {sig["sequence"]} | Timestamp: {sig["timestamp"]}')
                console.print(f'  Content: {sig["content"]}')
                console.print('')
    except Exception as e:
        console.print(f'[red]Error reading signals: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def ack_signals(
    signal_ids: str = typer.Argument(..., help='Comma-separated list of signal IDs to acknowledge.'),
    agent_id: str | None = typer.Option(None, help='The reader agent ID.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    """Acknowledge read signals to mark them as read."""
    try:
        reader_id, sess_id = resolve_cli_context(agent_id, session_id)
        ids = [sid.strip() for sid in signal_ids.split(',') if sid.strip()]
        res = session.ack_signals_logic(sess_id, reader_id, ids)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error acknowledging signals: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def read_notes(
    limit: int = typer.Option(50, help='Max number of notes to retrieve.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    sess_id = session_id or session.get_active_session_id()
    if not sess_id:
        console.print('[red]Error: No active session ID found.[/red]')
        raise typer.Exit(code=1)

    try:
        notes = session.read_notes_logic(sess_id, limit)
        if not notes:
            console.print('[dim]No broadcast notes found.[/dim]')
            return
        for note_data in notes:
            console.print(f'[bold yellow][{note_data["sender"]}][/bold yellow] ({note_data["timestamp"]})')
            console.print(f'  {note_data["content"]}')
            console.print('')
    except Exception as e:
        console.print(f'[red]Error reading notes: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def whiteboard_write(
    key: str = typer.Argument(..., help='The coordinate key.'),
    value: str = typer.Argument(..., help='The value string.'),
    agent_id: str | None = typer.Option(None, help='The modifier agent ID.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    """Write or update parameters on the shared session whiteboard."""
    try:
        modifier_id, sess_id = resolve_cli_context(agent_id, session_id)
        res = session.write_whiteboard_logic(sess_id, key, value, modifier_id)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error writing to whiteboard: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def whiteboard_read(
    key: str = typer.Argument(..., help='The coordinate key.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
):
    sess_id = session_id or session.get_active_session_id()
    if not sess_id:
        console.print('[red]Error: No active session ID found.[/red]')
        raise typer.Exit(code=1)

    try:
        val = session.read_whiteboard_logic(sess_id, key)
        if val is None:
            console.print(f"[dim]Key '{key}' not set.[/dim]")
        else:
            console.print(val)
    except Exception as e:
        console.print(f'[red]Error reading from whiteboard: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def tired(
    agent_id: str | None = typer.Option(None, help='The agent ID.'),
    session_id: str | None = typer.Option(None, help='The session ID.'),
    transcript: str | None = typer.Option(None, help='Optional chat log transcript content.'),
):
    """Transition agent to idle, runs staged dreaming, and evaluates sleep consensus."""
    try:
        active_agent, sess_id = resolve_cli_context(agent_id, session_id)
        res = session.tired_logic(sess_id, active_agent, transcript)
        console.print(f'[green]{res}[/green]')
    except Exception as e:
        console.print(f'[red]Error executing tired command: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
def verify(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Verify the cryptographic integrity of all memory files (EP-0106)."""
    failures = None
    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)

        console.print(f"Verifying memory integrity for persona '{active_id}'...")
        failures = memory_manager.verify_integrity()
        if failures:
            console.print('[bold red]TAMPERED STATE: Cryptographic verification failed![/bold red]')
            for path, error in failures:
                console.print(f'  [red]File:[/red] {path}')
                console.print(f'  [red]Reason:[/red] {error}')
        else:
            console.print('[bold green]All memory banks verified successfully. Integrity conserved.[/bold green]')
    except Exception as e:
        console.print(f'[bold red]TAMPERED STATE: {e}[/bold red]')
        raise typer.Exit(code=1)

    if failures:
        raise typer.Exit(code=1)


@app.command()
def introspect(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    all: bool = typer.Option(
        False, '--all', help='Force bootstrap compilation from scratch (loads active and subsumed).'
    ),
    visualize: bool = typer.Option(
        False, '--visualize', help='Output a Mermaid representation of the Knowledge Graph.'
    ),
    model: str = typer.Option(
        'gemini-3.1-pro-preview', help='The model to use for extraction (MCP sampling emulator).'
    ),
    test_mode: bool = typer.Option(
        False, '--test-mode', hidden=True, help='Enable mock mode for testing without GenAI key.'
    ),
):
    """
    Compress L1 event logs into a topological L2 Knowledge Graph using the Council of Giants.
    """
    try:
        from tur.introspection import format_graph_as_mermaid, run_introspection
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        console.print(f"Running Council Introspection Assembly for persona '{active_id}'...")
        graph = run_introspection(persona_dir, bootstrap=all, model=model, test_mode=test_mode)
        console.print(
            "[bold green]Introspection Assembly completed successfully. L2 Cognitive Map updated.[/bold green]"
        )

        if visualize:
            console.print("\n[bold cyan]--- Mermaid L2 Graph ---[/bold cyan]")
            console.print(format_graph_as_mermaid(graph))
            console.print("[bold cyan]------------------------[/bold cyan]")

    except Exception as e:
        console.print(f"[red]Error during introspection: {e}[/red]")
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == '__main__':
    main()
