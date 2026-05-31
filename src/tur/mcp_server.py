import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP


# Force the working directory to the tur project root if possible
def _ensure_project_root():
    if Path('.tur').exists():
        return
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / '.tur').exists():
            os.chdir(parent)
            return


_ensure_project_root()

# Defer imports until AFTER the working directory is set to ensure they resolve correctly,
# even if this script is launched from a different CWD.

from tur.compiler import compile_persona  # noqa: E402
from tur.dreaming import perform_sleep_dreaming  # noqa: E402
from tur.memory import MemoryManager  # noqa: E402
from tur.models import Memory, MemoryScope, MemoryType, SessionNotes  # noqa: E402
from tur.persona import get_active_persona_id, get_persona_path  # noqa: E402
from tur.session import (  # noqa: E402
    end_session_logic,
    get_active_session_id,
    get_session_file,
    hydrate_session_state,
    load_session_index,
    note_logic,
    start_session_logic,
)
from tur.telemetry import CognitiveTelemetry  # noqa: E402


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Lifecycle hook for startup and graceful shutdown."""
    print('Starting Tur MCP Server (Ontological Porcelain) on stdio...', file=sys.stderr)
    try:
        yield {}
    finally:
        print('\nShutting down Tur MCP Server gracefully...', file=sys.stderr)


mcp = FastMCP('tur-server', json_response=True, lifespan=server_lifespan)

# Process-isolated active session tracker for this specific connection/harness
_active_session_id: str | None = None


@mcp.tool()
def status() -> dict:
    """
    Return the current persona, session, and memory status as a structured dict.
    Use this for a quick context check without loading the full system prompt.

    Returns a dict with keys: persona_name, persona_id, persona_version,
    session_id, session_status, note_count, latest_note, memory_count.
    """
    import yaml

    try:
        active_id = get_active_persona_id()
        persona_dir = get_persona_path(active_id)

        # Persona info
        persona_name = active_id
        persona_version = 'unknown'
        persona_yaml_path = persona_dir / 'persona.yaml'
        if persona_yaml_path.exists():
            with open(persona_yaml_path, encoding='utf-8') as f:
                pdata = yaml.safe_load(f)
            persona_name = pdata.get('name', active_id)
            persona_version = pdata.get('version', 'unknown')

        # Session info
        session_id = _active_session_id or get_active_session_id()
        session_status = 'none'
        note_count = 0
        latest_note = None

        index = load_session_index(persona_dir)
        if session_id:
            entry = next((s for s in index.sessions if s.id == session_id), None)
            if entry:
                session_status = entry.status
            notes_yaml_path = get_session_file(persona_dir, session_id)
            if notes_yaml_path.exists():
                with open(notes_yaml_path, encoding='utf-8') as f:
                    notes_data = yaml.safe_load(f)
                session_notes = SessionNotes(**notes_data)
                note_count = len(session_notes.notes)
                if session_notes.notes:
                    last = sorted(session_notes.notes, key=lambda n: n.timestamp, reverse=True)[0]
                    latest_note = last.content[:200]
        elif index.sessions:
            most_recent = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)[0]
            session_id = most_recent.id
            session_status = most_recent.status + ' (last)'

        # Memory count
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_count = len(memory_manager.load_all())

        res = {
            'persona_name': persona_name,
            'persona_id': active_id,
            'persona_version': persona_version,
            'session_id': session_id,
            'session_status': session_status,
            'note_count': note_count,
            'latest_note': latest_note,
            'memory_count': memory_count,
        }
    except Exception as e:
        return {'error': str(e)}
    else:
        return res


@mcp.tool()
def wake(session_id: str | None = None, previous_session_id: str | None = None) -> str:
    """
    Read your core identity, directives, and system metrics to establish context.

    Trigger Conditions:
      - Turn Zero: Execute immediately on the very first turn of a session to compile your prompt and establish
        identity.
      - Context Loss/Degradation: Invoke if you detect high perplexity, confusion, or suspect a context window reset
        occurred.
      - Task Shift: Call if the user pivots to an entirely different project epic.

    Avoid Overuse:
      - Do NOT call wake() repeatedly within an active, stable conversation.

    Args:
        session_id(str): Optional session ID. If omitted, uses active or most recent session.
        previous_session_id(str): Optional session ID to seed the opening note of a new session.
    """
    global _active_session_id
    active_id = get_active_persona_id()
    sess_id = session_id or _active_session_id or get_active_session_id()
    if not sess_id:
        import uuid
        from datetime import datetime

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_hex = uuid.uuid4().hex[:8]
        sess_id = f'{ts}_{short_hex}'
        start_session_logic(sess_id, previous_session_id=previous_session_id)
        _active_session_id = sess_id
    else:
        _active_session_id = sess_id
    state = hydrate_session_state(active_id, session_id=sess_id)
    system_prompt = compile_persona(state)

    # Append Telemetry Metadata
    telemetry_engine = CognitiveTelemetry()
    static_metrics = telemetry_engine.measure_static_load(system_prompt)
    cp = telemetry_engine.calculate_constraint_dimensionality(state.persona)

    telemetry_block = (
        f'\n\n--- [SYSTEM METRICS] ---\n'
        f'Active Persona ID: {active_id}\n'
        f'Constraint Dimensionality (Cp): {cp}\n'
        f'Static Token Cost: {static_metrics["est_tokens"]}\n'
        f'Information Density: {static_metrics["density"]:.2f}\n'
    )

    return system_prompt + telemetry_block


@mcp.tool()
def learn(
    content: str,
    type: Literal['fact', 'preference', 'insight', 'event', 'axiom'],
    scope: Literal['incarnation', 'universal', 'user', 'persona'] = 'incarnation',
) -> str:
    """
    Assimilate a new invariant, fact, or insight into your permanent, cross-session memory.

    Trigger Conditions:
      - Invariants & Preferences: Call only when you deduce or the user explicitly states an immutable ruleset,
        architectural constraint, or taste that must survive future session resets (e.g., "User prefers HSL-curated
        HSL palettes over plain RGB").
      - Structural Insights: Call when you derive a permanent project axiom (e.g., "SSE transport has a boundary leak
        on local CWD").

    Avoid Overuse:
      - Do NOT call learn() for temporary or volatile facts (like active git branch names or temporary files),
        which belong in note().

    Args:
        content(str): The knowledge or insight to be remembered.
        type(str): The classification of this memory. Determines how it should be weighted and recalled.
          must be one of: 'fact', 'preference', 'insight', 'event', 'axiom'.
         'fact' means an objective truth (e.g., "Project uses FastAPI").
         'preference' means a user taste (e.g., "Hates black formatter").
         'event' means a narrative history (e.g., "Refactored Council").
         'axiom' means a deep philosophical belief (e.g., "Love is the Aleph").
         'insight' means a derived conclusion (e.g., "Tur Tur principle applies to AI").
        scope(str): The breadth of this memory's applicability. Determines where it is stored and how it is recalled.
          must be one of: 'incarnation', 'universal', 'user', 'persona'. Default is 'incarnation'.
         'incarnation' means it's only relevant to this specific project instance (stored locally).
         'user' means it's true for the Architect across all systems (stored locally).
         'persona' means it's a value/axiom of the persona (stored globally).
         'universal' means it's a universal truth shared across all projects and personas (stored globally).
    """
    try:
        mem_type = MemoryType(type)
    except ValueError:
        valid_types = ', '.join([t.value for t in MemoryType])
        return f"Error: Invalid memory_type '{type}'. Must be one of: {valid_types}"

    try:
        mem_scope = MemoryScope(scope)
    except ValueError:
        valid_scopes = ', '.join([s.value for s in MemoryScope])
        return f"Error: Invalid scope '{scope}'. Must be one of: {valid_scopes}"

    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)

    memory = Memory(type=mem_type, scope=mem_scope, tags=['mcp', 'agent'], content=content)
    saved_path = manager.save(memory)
    return f'Learned successfully (Scope: {mem_scope.value}). ID: {memory.id} File: {saved_path.name}'


@mcp.tool()
def note(content: str) -> str:
    """
    Update the transient session notes for the active persona.
    This appends a new chronological note to the active session scratchpad.

    Trigger Conditions:
      - Milestone Achievements: Invoke when a critical engineering goal is verified and completed (e.g., refactoring
        a module, passing a test suite).
      - Progress Snapshots: Call before concluding a session to capture the exact coordinates of incomplete work for
        the next instance.

    Avoid Overuse:
      - Do NOT write notes for trivial, intermediate steps (e.g., standard file views, directory lists).
        One descriptive note per major milestone is the optimal frequency.

    Args:
        content(str): The transient content/note of the current session state.
    """
    global _active_session_id
    try:
        res = note_logic(content, session_id=_active_session_id)
    except Exception as e:
        return f'Error updating note: {e}'
    else:
        return res


@mcp.tool()
def sleep(note: str, log_content: str, session_id: str | None = None, model: str = 'gemini-3.1-pro-preview') -> str:
    """
    Dehydrate a session by parsing the active session's chat log to extract memories.
    This is a terminal operation that closes the active session.

    Trigger Conditions:
      - Epic Completion: Call strictly at the end of the entire engineering session or when concluding a major
        architectural iteration.

    Avoid Overuse:
      - Never call sleep() intermediate-turn. It ends the active session state, closes it on disk, and consolidates the
        chat log into L1 ledger memories.

    Args:
        note(str): The final utterance/note to append to the session before sleeping. Required.
        log_content(str): The full text/markdown chat transcript of the current session.
        session_id(str): The optional ID of the session these memories belong to.
        model(str): The model to use for dreaming (default is 'gemini-3.1-pro-preview').
    """
    global _active_session_id
    resolved_session_id = session_id or _active_session_id
    # Append mandatory final note and auto-end session on sleep
    if resolved_session_id:
        try:
            note_logic(note, session_id=resolved_session_id)
        except Exception as e:
            return f'Error appending final note: {e}'
        try:
            end_session_logic(resolved_session_id)
        except Exception as e:
            return f'Error ending session: {e}'
    try:
        active_id = get_active_persona_id()
        count = perform_sleep_dreaming(
            log_content=log_content, active_id=active_id, session_id=resolved_session_id, model=model
        )
    except Exception as e:
        return f'Error during dreaming: {e}'
    else:
        _active_session_id = None
        return f'Dreams consolidated. {count} new memories formed and persona is now sleeping.'


@mcp.tool()
def recall(query: str) -> str:
    """
    Search your deep memory bank for past events, decisions, or knowledge not currently in your active context.

    Args:
        query: The topic or concept to search for in past memories.
    """
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all(include_archived=False)

    # Very basic substring search for now (L1 Event Log).
    # Will be upgraded to semantic graph traversal under EP-0103.
    query_lower = query.lower()
    results = [m for m in mems if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)]

    if not results:
        return f"No memories found matching query: '{query}'"

    mem_list = [{'id': str(m.id), 'type': m.type.value, 'content': m.content} for m in results]
    return json.dumps(mem_list, indent=2)


@mcp.tool()
def telemetry(identifier: str | None = None) -> dict:
    """
    Calculate Constraint Dimensionality (Cp) and cognitive load metrics for a persona.

    Args:
        identifier: The name or UUID of the persona. If omitted, uses the default.
    """
    try:
        import yaml

        from tur.models import Persona, SessionState
        from tur.user import get_user_profile

        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        file_path = persona_dir / 'persona.yaml'

        with open(file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        persona_obj = Persona(**data)

        # Mock state for compilation measurement
        user_profile = get_user_profile()
        state = SessionState(persona=persona_obj, user=user_profile, memories=[])
        system_prompt = compile_persona(state)

        telemetry_engine = CognitiveTelemetry()
        static_metrics = telemetry_engine.measure_static_load(system_prompt)
        cp = telemetry_engine.calculate_constraint_dimensionality(persona_obj)

        if cp < 5:
            rating = 'Human (Manageable)'
        elif cp < 10:
            rating = 'Giant (Heavy Load)'
        else:
            rating = 'Titan (Inference Warning)'
    except Exception as e:
        return {'error': str(e)}
    else:
        return {
            'persona_id': active_id,
            'persona_name': persona_obj.name,
            'constraint_dimensionality': cp,
            'class': rating,
            'static_token_cost': static_metrics['est_tokens'],
            'information_density': static_metrics['density'],
        }


def main(transport: Literal['stdio', 'sse'] = 'stdio', port: int = 8000):
    """Entry point for the MCP server."""
    try:
        match transport:
            case 'sse':
                print(f'Starting SSE server on port {port}...', file=sys.stderr)
                mcp.settings.port = port
            case 'stdio':
                print('Starting stdio server...', file=sys.stderr)
            case _:
                raise ValueError(f"Transport '{transport}' is not supported. Must be 'stdio' or 'sse'.")

        mcp.run(transport=transport)
    except KeyboardInterrupt:
        # Architecture Note (The Golem Protocol):
        # We must catch KeyboardInterrupt at this synchronous top-level boundary.
        # When Ctrl-C is pressed, the OS sends SIGINT, which `anyio` (the event loop under FastMCP)
        # catches. `anyio` gracefully cancels all async tasks (triggering our @server_lifespan's
        # `finally:` block to print the shutdown message to stderr).
        # However, once the async teardown is complete, `anyio` bubbles the KeyboardInterrupt
        # back up to this synchronous caller. If we don't swallow it here, it bleeds a noisy
        # stack trace onto the terminal.
        sys.exit(0)


if __name__ == '__main__':
    main()
