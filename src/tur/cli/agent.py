import json
import os
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import typer
import yaml
from rich import box
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from tur import dreaming, persona, session
from tur.cli.common import (
    cli_guard,
    console,
    get_session_status_style,
    handle_cli_error,
    make_version_callback,
    run_scaffold_cli,
)
from tur.compiler import compile_persona
from tur.introspection import format_graph_as_mermaid, run_introspection
from tur.memory import MemoryManager
from tur.metrics import compute_persona_metrics
from tur.models import (
    HarnessDelegationError,
    Memory,
    MemoryLink,
    MemoryScope,
    MemoryType,
)
from tur.recall import topological_recall
from tur.session import update_system_state

app = typer.Typer(
    help='Tur: Persona safe agent runtime.',
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
        callback=make_version_callback('tur'),
        is_eager=True,
    ),
) -> None:
    """Tur: Persona safe agent runtime."""


@app.command()
@cli_guard('Error during wake')
def wake(
    session_id: str | None = typer.Option(
        None, help='The session ID to resume or wake under. If omitted, uses active or auto-starts one.'
    ),
    from_session: str | None = typer.Option(
        None, help='Optional ID of a previous session whose last note will seed a newly started session.'
    ),
    agent_id: str | None = typer.Option(None, help='The unique agent ID representing this manifestation.'),
    harness_conversation_id: str | None = typer.Option(None, help='The harness conversation ID.'),
    include_stale: bool = typer.Option(
        False, '--include-stale', help='Include stale/decayed memories in the compiled wake prompt.'
    ),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Wake the persona and compile the prompt."""
    active_id = persona.get_active_persona_id(identifier)
    _persona_dir = persona.get_persona_path(active_id)

    resolved_session_id = session_id or session.get_active_session_id()
    is_auto_started = False

    if not resolved_session_id:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_hex = uuid4().hex[:8]
        resolved_session_id = f'{ts}_{short_hex}'
        is_auto_started = True

    session.start_session_logic(
        resolved_session_id,
        identifier=active_id,
        previous_session_id=from_session,
        agent_id=agent_id,
        harness_conversation_id=harness_conversation_id,
    )

    update_system_state(active_persona_id=active_id, active_session_id=resolved_session_id)

    state = session.hydrate_session_state(
        active_id,
        session_id=resolved_session_id,
        include_stale=include_stale,
    )

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


@app.command()
@cli_guard()
def learn(
    content: str | None = typer.Argument(None, help='The content of the memory to store.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    type: MemoryType = typer.Option(MemoryType.INSIGHT, help='The type of memory.'),
    scope: MemoryScope = typer.Option(MemoryScope.INCARNATION, help='The scope of the memory.'),
    session_id: str = typer.Option(None, help='The name/ID of the session this memory belongs to'),
    confidence: float = typer.Option(
        1.0, '--confidence', min=0.0, max=1.0, help='Epistemic confidence rating in [0.0, 1.0].'
    ),
    file: str | None = typer.Option(
        None, '--file', '--ref', help='Source file or context URI reference (e.g., src/auth.py#L10-L20).'
    ),
    agent: str | None = typer.Option(None, '--agent', help='Author agent ID recording this observation.'),
    harness: str | None = typer.Option(None, '--harness', help='Harness runtime identifier (e.g., antigravity).'),
    json_payload: list[str] | None = typer.Option(
        None, '--json', help='Structured JSON payload(s), file paths, or globs to commit.'
    ),
):
    """Create a new memory for a persona, or commit structured JSON memories."""
    if not json_payload and not content:
        console.print('[red]Error: Must provide memory content or --json payload.[/red]')
        raise typer.Exit(code=1)

    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    memory_manager = MemoryManager(base_dir=persona_dir)
    from tur.provenance import create_provenance_and_decay

    if json_payload:
        from tur._helpers import parse_multi_json_payloads

        payloads = parse_multi_json_payloads(json_payload)
        extracted_memories = []
        for p in payloads:
            if isinstance(p, dict):
                if 'memories' in p and isinstance(p['memories'], list):
                    extracted_memories.extend(p['memories'])
                elif 'type' in p and 'content' in p:
                    extracted_memories.append(p)

        count = 0
        for mem_dict in extracted_memories:
            m_type = MemoryType(mem_dict.get('type', type.value))
            m_scope = MemoryScope(mem_dict.get('scope', scope.value))
            m_content = mem_dict.get('content', '')
            m_tags = mem_dict.get('tags', ['json', 'cli'])
            m_conf = float(mem_dict.get('confidence', confidence))
            m_file = mem_dict.get('context_ref') or mem_dict.get('file') or file
            m_agent = mem_dict.get('source_agent') or agent
            m_harness = mem_dict.get('source_harness') or harness or os.environ.get('TUR_HARNESS')

            prov, dec = create_provenance_and_decay(
                memory_type=m_type,
                confidence=m_conf,
                context_ref=m_file,
                source_agent=m_agent,
                source_harness=m_harness,
            )

            memory = Memory(
                type=m_type,
                scope=m_scope,
                tags=m_tags,
                content=m_content,
                source_session=session_id or mem_dict.get('source_session') or session.get_active_session_id(),
                confidence=m_conf,
                provenance=prov,
                decay=dec,
            )
            saved_path = memory_manager.save(memory)
            count += 1
            console.print(f'[green]Memory saved to {saved_path}[/green]')
        console.print(f'[bold green]Committed {count} memories from JSON payload(s).[/bold green]')
        return

    assert content is not None
    console.print(f"Consolidating memory for '{active_id}': '{content[:50]}...' [{scope.value}]")

    prov, dec = create_provenance_and_decay(
        memory_type=type,
        confidence=confidence,
        context_ref=file,
        source_agent=agent,
        source_harness=harness or os.environ.get('TUR_HARNESS'),
    )

    memory = Memory(
        type=type,
        scope=scope,
        tags=['manual', 'cli'],
        content=content,
        source_session=session_id or session.get_active_session_id(),
        confidence=confidence,
        provenance=prov,
        decay=dec,
    )
    saved_path = memory_manager.save(memory)
    console.print(f'[green]Memory saved to {saved_path}[/green]')


@app.command()
@cli_guard()
def recall(
    query: str = typer.Argument(..., help='The topic or concept to search for in past memories.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    effort: int = typer.Option(
        0, '--effort', '-e', min=0, max=10, help='Cognitive effort level in [0..10] for graph retrieval.'
    ),
    deep: bool = typer.Option(
        False, '--deep', help='Convenience alias for --effort 5 (HippoRAG Personalized PageRank + Louvain clusters).'
    ),
    mermaid: bool = typer.Option(False, '--mermaid', help='Render retrieved subgraph as Mermaid flowchart.'),
    top_k: int = typer.Option(5, '--top-k', '-k', help='Maximum number of memory nodes to return.'),
):
    """Search your deep memory bank for past events, decisions, or knowledge with graph-theoretic retrieval."""
    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)

    result = topological_recall(
        query=query,
        persona_dir=persona_dir,
        effort=effort,
        deep=deep,
        mermaid=mermaid,
        top_k=top_k,
    )
    console.print(result)


@app.command()
@cli_guard('Error saving note')
def note(
    content: str = typer.Argument(..., help='The transient content/note of the current session state.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    session_id: str | None = typer.Option(None, help='The session ID to isolate this note to.'),
):
    """Append a note to the active session's notes.yaml."""
    res = session.note_logic(content, session_id=session_id, identifier=identifier)
    console.print(f'[green]{res}[/green]')


@app.command()
@cli_guard()
def status(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Show the current persona, session, and memory status."""
    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    summary = session.get_persona_status_summary(persona_dir=persona_dir, persona_id=active_id)

    # --- Memory stats ---
    stats = summary['memory_stats']
    active_count = stats['active']
    archived_count = stats['archived']
    subsumed_count = stats['subsumed']

    scope_parts = [f'{k}: {v}' for k, v in sorted(stats['by_scope'].items())]
    scope_str = ', '.join(scope_parts) if scope_parts else 'none'

    type_parts = [f'{k}: {v}' for k, v in sorted(stats['by_type'].items(), key=lambda x: -x[1])]
    type_str = ', '.join(type_parts) if type_parts else 'none'

    l2_info = None
    if summary['l2_stats'] and summary['l2_stats']['nodes'] > 0:
        l2_info = f"{summary['l2_stats']['nodes']} nodes, {summary['l2_stats']['edges']} edges"

    # --- Render ---
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column('Key', style='bold cyan', no_wrap=True)
    table.add_column('Value', style='white')

    table.add_row('Persona', f"{summary['persona_name']} [dim](v{summary['persona_version']})[/dim]")
    table.add_row('Persona ID', summary['persona_id'])
    table.add_row('', '')
    table.add_row('Session ID', summary['session_id'] or '[dim]none[/dim]')
    table.add_row('Status', get_session_status_style(summary['session_status']))
    table.add_row('Started', summary['session_created'])
    table.add_row('Updated', summary['session_updated'])
    table.add_row('Notes', str(summary['note_count']))
    table.add_row('Latest note', f"[dim]{summary['latest_note_snippet']}[/dim]")
    table.add_row('', '')
    table.add_row(
        'L1 Memories',
        f'{active_count} active [dim]({archived_count} archived, {subsumed_count} subsumed)[/dim]',
    )
    if 'staleness' in stats and stats['total'] > 0:
        st = stats['staleness']
        fresh_str = f'[green]{st["fresh"]} fresh[/green]'
        stale_str = f'[yellow]{st["stale"]} stale[/yellow]'
        unanch_str = f'[dim]{st["unanchored"]} unanchored[/dim]'
        table.add_row('  Freshness', f'{fresh_str}, {stale_str}, {unanch_str}')
    if stats['by_scope']:
        table.add_row('  Scopes', f'[dim]{scope_str}[/dim]')
    if stats['by_type']:
        table.add_row('  Types', f'[dim]{type_str}[/dim]')
    if l2_info:
        table.add_row('L2 Knowledge', f'[green]{l2_info}[/green]')

    console.print(Panel(table, title='[bold]Tur Status[/bold]', border_style='cyan'))


@app.command()
@cli_guard('Error calculating metrics')
def metrics(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    json_output: bool = typer.Option(False, '--json', help='Output metrics as raw JSON.'),
):
    """Calculate Constraint Dimensionality (C_p) and cognitive load metrics for a persona."""
    report = compute_persona_metrics(identifier)

    if json_output:
        console.print(
            json.dumps(
                report.to_dict(),
                indent=2,
            )
        )
        return

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column('Key', style='bold cyan', no_wrap=True)
    table.add_column('Value', style='white')

    table.add_row('Persona', f'{report.persona_name} [dim]({report.persona_id})[/dim]')
    table.add_row('Principles (N)', str(report.num_principles))
    table.add_row('Constraint Dim (Cp)', f'{report.constraint_dimensionality} [dim]({report.rating_class})[/dim]')
    table.add_row('', '')
    table.add_row('Static Token Cost', f'~{report.static_token_cost}')
    table.add_row('Information Density', f'{report.information_density}')
    table.add_row('', '')
    table.add_row('Graph Nodes / Edges', f'{report.graph_nodes} nodes / {report.graph_edges} edges')
    table.add_row('Knowledge Communities', f'{report.community_count} Louvain Clusters')
    table.add_row(
        'Algebraic Connectivity', f'{report.algebraic_connectivity} [dim]({report.connectivity_status})[/dim]'
    )
    table.add_row('Modularity Score (Q)', f'{report.modularity_score}')

    console.print(Panel(table, title=f'[bold]System Metrics: {report.persona_name}[/bold]', border_style='cyan'))


@app.command(name='telemetry', hidden=True)
def telemetry(
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    json_output: bool = typer.Option(False, '--json', help='Output metrics as raw JSON.'),
):
    """Backwards-compatible alias for metrics."""
    return metrics(identifier=identifier, json_output=json_output)


@app.command()
@cli_guard('Error during sleep')
def sleep(
    log_path: str | None = typer.Argument(None, help='Path to the chat log file to be parsed.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
    session_id: str = typer.Option(None, help='The name/ID of the session these memories belong to'),
    model: str = typer.Option('gemini-3.1-pro-preview', help='The model to use for dreaming (insight extraction)'),
    note: str = typer.Option(..., '-n', '--note', help='Final note/utterance to append before sleeping.'),
    commit: list[str] | None = typer.Option(
        None, '--commit', help='Structured JSON payload(s), file path(s), or glob(s) to commit directly.'
    ),
):
    """Dehydrate a session by parsing a chat log to extract memories or commit structured JSON."""
    if not commit and not log_path:
        console.print('[red]Error: Must provide log_path or --commit payload.[/red]')
        raise typer.Exit(code=1)

    active_id = persona.get_active_persona_id(identifier)
    resolved_session_id = session_id or session.get_active_session_id()

    # Append final note
    if resolved_session_id:
        session.note_logic(note, session_id=resolved_session_id, identifier=identifier)
        console.print(f"[green]Final note appended to session '{resolved_session_id}'.[/green]")

        # Auto-end session on sleep
        res_end = session.end_session_logic(resolved_session_id, identifier=identifier)
        console.print(f'[dim]Auto-ended session: {res_end}[/dim]')

    if commit:
        console.print(f"Committing dreams directly for '{active_id}'...")
        try:
            with console.status(
                f"[bold cyan]Committing insights & consolidating memories for '{active_id}'...[/bold cyan]",
                spinner='dots',
            ):
                count = dreaming.perform_sleep_dreaming(
                    log_content='',
                    active_id=active_id,
                    session_id=resolved_session_id,
                    model=model,
                    commit_payload=commit,
                )
            console.print(f'[bold green]Dreams consolidated. {count} new memories formed.[/bold green]')
        except Exception as e:
            handle_cli_error(e, 'Error during committing dreams')

        console.print('[bold green]State saved. Persona is now sleeping.[/bold green]')
        return

    assert log_path is not None
    console.print(f"Processing session log for '{active_id}' from {log_path}...")
    try:
        with console.status(
            f'[bold cyan]Extracting insights & consolidating memories via {model}... (Dreaming)[/bold cyan]',
            spinner='dots',
        ):
            count = dreaming.perform_sleep_dreaming(
                log_content=Path(log_path).read_text(encoding='utf-8'),
                active_id=active_id,
                session_id=resolved_session_id,
                model=model,
            )

        console.print(f'[bold green]Dreams consolidated. {count} new memories formed.[/bold green]')

    except HarnessDelegationError as e:
        console.print(e.prompt)
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f'[red]Error during dreaming: {e}[/red]')

    console.print('[bold green]State saved. Persona is now sleeping.[/bold green]')


def resolve_cli_context(agent_id_opt: str | None, session_id_opt: str | None):
    # 1. Resolve session_id
    sess_id = session_id_opt or session.get_active_session_id()
    if not sess_id:
        console.print("[red]Error: No active session ID found. Run 'wake' first or provide --session-id option.[/red]")
        raise typer.Exit(code=1)

    # 2. Resolve agent_id
    env_agent_id = os.getenv('TUR_AGENT_ID')
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

        short_hex = uuid4().hex[:8]
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
            console.print(json.dumps(agents, indent=2))
        else:
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
            console.print(json.dumps(signals, indent=2))
        else:
            if not signals:
                console.print('[dim]No incoming signals.[/dim]')
                return
            for sig in signals:
                console.print(f'[bold cyan][{sig["sender"]} -> {sig["recipient"]}][/bold cyan] ({sig["type"]})')
                clock_str = f' | VectorClock: {sig["vector_clock"]}' if sig.get('vector_clock') else ''
                console.print(f'  Sequence: {sig["sequence"]}{clock_str} | Timestamp: {sig["timestamp"]}')
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
@cli_guard('Error during diff')
def diff(
    base_session_id: str | None = typer.Argument(None, help='Base session ID (or predecessor if omitted).'),
    target_session_id: str | None = typer.Argument(None, help='Target session ID (or active session if omitted).'),
    json_output: bool = typer.Option(False, '--json', help='Output diff as structured JSON.'),
    type_filter: str | None = typer.Option(None, '--type', help='Filter by memory type (e.g. fact, insight).'),
    scope_filter: str | None = typer.Option(
        None, '--scope', help='Filter by memory scope (e.g. incarnation, universal).'
    ),
    identifier: str | None = typer.Option(None, '--persona', help='Persona identifier (default: active persona).'),
):
    """Inspect memory mutations, additions, supersessions, and contradictions across sessions (EP-0133)."""
    from tur.diff import compute_session_diff, format_diff_json, format_diff_terminal

    deltas = compute_session_diff(
        base_session_id=base_session_id,
        target_session_id=target_session_id,
        persona_id=identifier,
        type_filter=type_filter,
        scope_filter=scope_filter,
    )

    if json_output:
        console.print(json.dumps(format_diff_json(deltas), indent=2))
    else:
        console.print(format_diff_terminal(deltas, session_id=target_session_id))


@app.command()
def read_notes(
    limit: int = typer.Option(50, help='Max number of notes to retrieve.'),
    session_id: str | None = typer.Option(None, help="The session ID, or 'previous' for immediate parent session."),
    include_previous: bool = typer.Option(False, '--include-previous', help='Prepend notes from the parent session.'),
):
    sess_id = session_id or session.get_active_session_id()
    if not sess_id:
        console.print('[red]Error: No active session ID found.[/red]')
        raise typer.Exit(code=1)

    try:
        notes = session.read_notes_logic(sess_id, limit=limit, include_previous=include_previous)
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
    strict: bool = typer.Option(
        False, '--strict', help='Fail with non-zero exit code if any stale memories are detected.'
    ),
):
    """Verify the cryptographic integrity and epistemic staleness of all memory files."""
    failures = None
    stale_memories = []
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

        # Epistemic staleness checks (EP-0131)
        stale_memories = memory_manager.get_stale_memories()
        if stale_memories:
            console.print(
                f'[yellow]Detected {len(stale_memories)} stale/unanchored/refuted memories (EP-0131):[/yellow]'
            )
            for mem, st, reason in stale_memories:
                status_color = 'red' if st in ('stale', 'refuted') else 'dim'
                console.print(f'  [{status_color}]• [{st.upper()}][/] {mem.id[:8]} ({mem.type.value}): {reason}')

    except Exception as e:
        console.print(f'[bold red]TAMPERED STATE: {e}[/bold red]')
        raise typer.Exit(code=1)

    if failures or (strict and any(st == 'stale' for _, st, _ in stale_memories)):
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
    commit: list[str] | None = typer.Option(
        None,
        '--commit',
        help='Structured JSON payload(s), file path(s), or glob(s) containing ExtractedGraph(s) to commit.',
    ),
    test_mode: bool = typer.Option(
        False, '--test-mode', hidden=True, help='Enable mock mode for testing without GenAI key.'
    ),
):
    """
    Compress L1 memories into the L2 Cognitive Map. Runs the Council Assembly pipeline.
    """

    try:
        active_id = persona.get_active_persona_id(identifier)
        persona_dir = persona.get_persona_path(active_id)

        console.print(f"Running Council Introspection Assembly for persona '{active_id}'...")
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task('[cyan]Introspecting L2 Cognitive Map...[/cyan]', total=9)

            def on_progress(current: int, total: int, description: str) -> None:
                progress.update(
                    task,
                    total=total,
                    completed=current - 1,
                    description=f'[cyan][{current}/{total}] {description}[/cyan]',
                )

            graph = run_introspection(
                persona_dir,
                bootstrap=all,
                model=model,
                test_mode=test_mode,
                commit_payload=commit,
                progress_callback=on_progress,
            )
            progress.update(task, completed=9, description='[bold green]✓ Introspection complete.[/bold green]')

        console.print(
            '[bold green]Introspection Assembly completed successfully. L2 Cognitive Map updated.[/bold green]'
        )

        if visualize:
            console.print('\n[bold cyan]--- Mermaid L2 Graph ---[/bold cyan]')
            console.print(format_graph_as_mermaid(graph))
            console.print('[bold cyan]------------------------[/bold cyan]')

    except HarnessDelegationError as e:
        console.print(e.prompt)
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f'[red]Error during introspection: {e}[/red]')
        raise typer.Exit(code=1)


@app.command()
@cli_guard('Error evolving memory')
def evolve(
    memory_id: str = typer.Argument(..., help='The SHA-256 hash or part of the L1 memory ID to promote/refine.'),
    core_type: str = typer.Option(
        'existential_alignment',
        help='The core transition category: existential_alignment, relational_discovery, or identity_transition.',
    ),
    principle: str = typer.Option(..., help='The concrete behavioral constraint/instruction (derived principle).'),
    covenant: str = typer.Option(..., help='The ethical commitment/promise to the user or self.'),
    identifier: str | None = typer.Argument(
        None, help='The name or UUID of the persona. If omitted, uses the default.'
    ),
):
    """Refine a lived experience (an existing memory or note) into a Core Memory with status pending_approval."""
    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    memory_manager = MemoryManager(base_dir=persona_dir)
    all_mems = memory_manager.load_all()

    matching_mem = None
    for m in all_mems:
        if m.id.startswith(memory_id):
            matching_mem = m
            break

    if not matching_mem:
        console.print(f"[red]Error: No memory found matching ID '{memory_id}'[/red]")
        raise typer.Exit(code=1)

    # Create a link from the new Core memory to the original L1 memory
    link = MemoryLink(uri=f'tur://memory/{matching_mem.id}', relation='refines')

    # Create the new CORE memory
    core_mem = Memory(
        type=MemoryType.CORE,
        scope=MemoryScope.UNIVERSAL,
        tags=['evolution', 'core'],
        content=matching_mem.content,  # Content is the lived context of the original experience
        links=[link],
        source_session=matching_mem.source_session,
        core_type=core_type,
        derived_principle=principle,
        ethical_covenant=covenant,
        status='pending_approval',  # Steward: Pending approval workflow
    )

    saved_path = memory_manager.save(core_mem)
    console.print(f"[green]Core Memory created and staged in 'pending_approval' status: {saved_path}[/green]")
    console.print(f'To approve and activate this axiom, run: [bold]tur approve {core_mem.id[:8]}[/bold]')


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


def main():
    app()


if __name__ == '__main__':
    main()
