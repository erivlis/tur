import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP

from tur._helpers import yaml_safe_load
from tur.compiler import compile_persona
from tur.dreaming import perform_sleep_dreaming
from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType, SessionNotes
from tur.paths import resolve_personas_base_dir, resolve_workspace_dir
from tur.persona import get_active_persona_id, get_persona_path
from tur.session import (
    ack_signals_logic,
    end_session_logic,
    get_active_session_id,
    get_session_file,
    hydrate_session_state,
    list_agents_logic,
    load_session_index,
    note_logic,
    read_notes_logic,
    read_signals_logic,
    read_whiteboard_logic,
    signal_logic,
    start_session_logic,
    tired_logic,
    write_whiteboard_logic,
)
from tur.telemetry import CognitiveTelemetry

logger = logging.getLogger('tur.mcp')


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Lifecycle hook for startup and graceful shutdown."""
    logger.debug('Starting Tur MCP Server on stdio...')
    try:
        yield {}
    finally:
        logger.debug('Shutting down Tur MCP Server...')


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

    try:
        active_id = get_active_persona_id()
        persona_dir = get_persona_path(active_id)

        # Persona info
        persona_name = active_id
        persona_version = 'unknown'
        persona_yaml_path = persona_dir / 'persona.yaml'
        if persona_yaml_path.exists():
            with open(persona_yaml_path, encoding='utf-8') as f:
                pdata = yaml_safe_load(f)
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
                    notes_data = yaml_safe_load(f)
                session_notes = SessionNotes(**notes_data)
                note_count = len(session_notes.notes)
                if session_notes.notes:
                    last = sorted(session_notes.notes, key=lambda n: n.timestamp, reverse=True)[0]
                    latest_note = last.content[:200]
        elif index.sessions:
            most_recent = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)[0]
            session_id = most_recent.id
            session_status = most_recent.status + ' (last)'

        # Memory stats
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_stats = memory_manager.get_stats()
        memory_count = memory_stats['total']

        from tur.introspection import load_l2_graph_from_okf

        l2_graph = load_l2_graph_from_okf(persona_dir)
        l2_stats = None
        if l2_graph is not None:
            l2_stats = {
                'nodes': l2_graph.number_of_nodes(),
                'edges': l2_graph.number_of_edges(),
            }

        res = {
            'persona_name': persona_name,
            'persona_id': active_id,
            'persona_version': persona_version,
            'session_id': session_id,
            'session_status': session_status,
            'note_count': note_count,
            'latest_note': latest_note,
            'memory_count': memory_count,
            'memory_stats': memory_stats,
            'l2_stats': l2_stats,
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
        type: Literal['fact', 'preference', 'insight', 'event', 'axiom', 'core'],
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
          must be one of: 'fact', 'preference', 'insight', 'event', 'axiom', 'core'.
         'fact' means an objective truth (e.g., "Project uses FastAPI").
         'preference' means a user taste (e.g., "Hates black formatter").
         'event' means a narrative history (e.g., "Refactored Council").
         'axiom' means a deep philosophical belief (e.g., "Love is the Aleph").
         'insight' means a derived conclusion (e.g., "Tur Tur principle applies to AI").
         'core' means a core memory protocol representation.
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

    memory = Memory(
        type=mem_type,
        scope=mem_scope,
        tags=['mcp', 'agent'],
        content=content,
        source_session=None,
    )
    saved_path = manager.save(memory)
    return f'Learned successfully (Scope: {mem_scope.value}). ID: {memory.id} File: {saved_path.name}'


@mcp.tool()
def evolve(
        memory_id: str,
        core_type: Literal['existential_alignment', 'relational_discovery', 'identity_transition'],
        derived_principle: str,
        ethical_covenant: str,
) -> str:
    """
    Refine a lived experience (an existing memory/note) into a permanent Core Memory with status pending_approval.

    Args:
        memory_id(str): The SHA-256 content hash of the L1 memory to promote.
        core_type(str): The category of core transition (existential_alignment, relational_discovery,
           or identity_transition).
        derived_principle(str): The concrete behavioral instruction or prompt constraint.
        ethical_covenant(str): The collaborative promise made to the Architect or Self.
    """
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)

    all_mems = manager.load_all()
    matching_mem = None
    for m in all_mems:
        if m.id.startswith(memory_id):
            matching_mem = m
            break

    if not matching_mem:
        return f"Error: No L1 memory found matching ID '{memory_id}'"

    from tur.models import MemoryLink

    link = MemoryLink(uri=f'tur://memory/{matching_mem.id}', relation='refines')

    core_mem = Memory(
        type=MemoryType.CORE,
        scope=MemoryScope.UNIVERSAL,
        tags=['evolution', 'core'],
        content=matching_mem.content,
        links=[link],
        source_session=matching_mem.source_session,
        core_type=core_type,
        derived_principle=derived_principle,
        ethical_covenant=ethical_covenant,
        status='pending_approval',  # Steward: Pending approval workflow
    )
    saved_path = manager.save(core_mem)
    return (
        f"Core Memory created and staged in 'pending_approval' status: {core_mem.id}. File: {saved_path.name}."
        f' Instruct the Architect to approve it with: tur-adm memory approve {core_mem.id[:8]}'
    )


@mcp.tool()
def introspect(bootstrap: bool = False, ctx: Context | None = None) -> str:
    """
    Compress L1 event logs into the L2 Cognitive Map using the Council Assembly pipeline.
    This runs the full introspection compaction loop, consolidating raw memories
    into a topological knowledge graph.

    Args:
        bootstrap: If True, force full recompilation from scratch (loads active and subsumed memories).
                   If False (default), performs incremental update on the existing graph.
    """
    from tur.introspection import format_graph_as_mermaid, run_introspection

    try:
        persona_id = get_active_persona_id()
        persona_dir = get_persona_path(persona_id)

        graph = run_introspection(persona_dir, bootstrap=bootstrap, mcp_context=ctx)

        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        mermaid = format_graph_as_mermaid(graph)
    except Exception as e:
        return f'Error during Council Introspection: {e}'
    else:
        return (
            f'Council Introspection complete. '
            f'L2 Cognitive Map: {node_count} nodes, {edge_count} edges.\n\n'
            f'```mermaid\n{mermaid}\n```'
        )


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
def sleep(
        note: str,
        log_content: str,
        session_id: str | None = None,
        model: str = 'gemini-3.1-pro-preview',
        ctx: Context | None = None,
) -> str:
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
            log_content=log_content, active_id=active_id, session_id=resolved_session_id, model=model, ctx=ctx
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
    from tur.recall import topological_recall

    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    return topological_recall(query, persona_dir)


@mcp.tool()
def telemetry(identifier: str | None = None) -> dict:
    """
    Calculate Constraint Dimensionality (Cp) and cognitive load metrics for a persona.

    Args:
        identifier: The name or UUID of the persona. If omitted, uses the default.
    """
    try:
        from tur.models import Persona, SessionState
        from tur.user import get_user_profile

        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        file_path = persona_dir / 'persona.yaml'

        with open(file_path, encoding='utf-8') as f:
            data = yaml_safe_load(f)

        persona_obj = Persona(**data)

        # Mock state for compilation measurement
        user_profile = get_user_profile()
        state = SessionState(persona=persona_obj, user=user_profile, memories=[], epilogue=None, knowledge_graph=None)
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


@mcp.tool()
def read_notes(session_id: str | None = None, limit: int = 50) -> list[dict]:
    """
    Returns the session broadcast notes in strict ascending sequence order.
    """
    sess_id = session_id or _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    return read_notes_logic(sess_id, limit)


@mcp.tool()
def signal(to: str, content: str, type: str = 'inform', sender_id: str | None = None) -> str:
    """
    Sends a message signal to another manifestation or broadcast to all ('*').
    Enforces a token-bucket rate limiter of 10 messages/minute.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if sender_id and env_agent_id and sender_id != env_agent_id and not sender_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: sender_id '{sender_id}' does not match calling agent '{env_agent_id}'.")
    sender = sender_id or env_agent_id or 'mcp_agent'
    return signal_logic(sess_id, sender, to, content, type)


@mcp.tool()
def read_signals(agent_id: str | None = None, unread_only: bool = True) -> list[dict]:
    """
    Peeks incoming signals directed to the agent or its namespaces.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if agent_id and env_agent_id and agent_id != env_agent_id and not agent_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: agent_id '{agent_id}' does not match calling agent '{env_agent_id}'.")
    active_agent = agent_id or env_agent_id or 'mcp_agent'
    return read_signals_logic(sess_id, active_agent, unread_only)


@mcp.tool()
def ack_signals(agent_id: str | None = None, signal_ids: list[str] | None = None) -> str:
    """
    Acknowledges signals by marking them as read.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if agent_id and env_agent_id and agent_id != env_agent_id and not agent_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: agent_id '{agent_id}' does not match calling agent '{env_agent_id}'.")
    active_agent = agent_id or env_agent_id or 'mcp_agent'
    if not signal_ids:
        return 'No signal IDs provided.'
    return ack_signals_logic(sess_id, active_agent, signal_ids)


@mcp.tool()
def list_agents() -> list[dict]:
    """
    Lists all registered manifestations from the SQLite session database.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    return list_agents_logic(sess_id)


@mcp.tool()
def write_whiteboard(key: str, value: str) -> str:
    """
    Writes or updates key-value state parameters on the shared session whiteboard.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    sender = os.environ.get('TUR_AGENT_ID') or 'mcp_agent'
    return write_whiteboard_logic(sess_id, key, value, sender)


@mcp.tool()
def read_whiteboard(key: str) -> str | None:
    """
    Reads coordinate parameters from the shared session whiteboard.
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    return read_whiteboard_logic(sess_id, key)


@mcp.tool()
def tired(agent_id: str | None = None, transcript: str | None = None) -> str:
    """
    Marks the agent as idle, runs staged dreaming, and ends the session if all agents are idle.
    This replaces standard sleep() intermediate-turn in multi-agent environments.
    """
    global _active_session_id
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if agent_id and env_agent_id and agent_id != env_agent_id and not agent_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: agent_id '{agent_id}' does not match calling agent '{env_agent_id}'.")
    active_agent = agent_id or env_agent_id or 'mcp_agent'
    res = tired_logic(sess_id, active_agent, transcript)
    if 'Consensus sleep reached' in res:
        _active_session_id = None
    return res


def main():
    """Entry point for the MCP server."""
    try:
        mcp.run(transport='stdio')
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
