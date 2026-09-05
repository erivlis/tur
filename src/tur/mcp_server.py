import asyncio
import contextlib
import functools
import inspect
import logging
import os
import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, Literal, cast

import anyio
import anyio.from_thread
from mcp.server.fastmcp import Context, FastMCP

from tur import __version__
from tur.compiler import compile_persona
from tur.dreaming import perform_sleep_dreaming
from tur.locking import LockTimeoutError, lock_contention_guard
from tur.memory import MemoryManager
from tur.metrics import CognitiveMetrics, compute_persona_metrics
from tur.models import Memory, MemoryScope, MemoryType
from tur.persona import get_active_persona_id, get_persona_path
from tur.session import (
    ack_signals_logic,
    end_session_logic,
    get_active_session_id,
    get_persona_status_summary,
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

logger = logging.getLogger('tur.mcp')


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Lifecycle hook for startup and graceful shutdown."""
    logger.debug('Starting Tur MCP Server on stdio...')
    try:
        yield {}
    finally:
        logger.debug('Shutting down Tur MCP Server...')


mcp = FastMCP('tur-mcp', json_response=True, lifespan=server_lifespan)
mcp._mcp_server.version = __version__

# Process-isolated active session tracker for this specific connection/harness
_active_session_id: str | None = None


def format_contention_error(e: Exception | str, as_dict: bool = False) -> Any:
    """Formats standardized non-fatal retry guidance on LockTimeoutError."""
    if as_dict:
        return {'status': 'contended', 'error': f'State lock is currently held by another process: {e}'}
    return f'Status: Contended. The state lock is currently held by another process: {e}. Please retry shortly.'


def mcp_contention_guard(as_dict: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to catch LockTimeoutError across MCP tools and return standardized retry guidance."""
    return lock_contention_guard(on_contention=lambda e: format_contention_error(e, as_dict=as_dict))


@mcp.tool()
@mcp_contention_guard(as_dict=True)
def status() -> dict:
    """
    Return the current persona, session, and memory status as a structured dict.
    Use this for a quick context check without loading the full system prompt.

    Returns a dict with keys: tur_version, persona_name, persona_id, persona_version,
    session_id, session_status, note_count, latest_note, memory_count.
    """

    try:
        active_id = get_active_persona_id()
        persona_dir = get_persona_path(active_id)
        load_session_index(persona_dir)
        return get_persona_status_summary(
            persona_dir=persona_dir,
            session_id=_active_session_id,
            persona_id=active_id,
        )
    except LockTimeoutError:
        raise
    except Exception as e:
        return {'error': str(e)}


@mcp.tool()
@mcp_contention_guard()
def wake(
    session_id: str | None = None,
    previous_session_id: str | None = None,
    include_stale: bool = False,
) -> str:
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
        include_stale(bool): Optional flag to include decayed/stale memories in the system prompt.
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
    state = hydrate_session_state(active_id, session_id=sess_id, include_stale=include_stale)
    system_prompt = compile_persona(state)

    # Append System Metrics Metadata
    metrics_engine = CognitiveMetrics()
    static_metrics = metrics_engine.measure_static_load(system_prompt)
    cp = metrics_engine.calculate_constraint_dimensionality(state.persona)

    metrics_block = (
        f'\n\n--- [SYSTEM METRICS] ---\n'
        f'Active Persona ID: {active_id}\n'
        f'Constraint Dimensionality (Cp): {cp}\n'
        f'Static Token Cost: {static_metrics["est_tokens"]}\n'
        f'Information Density: {static_metrics["density"]:.2f}\n'
    )

    return system_prompt + metrics_block


@mcp.tool()
@mcp_contention_guard()
def learn(
    content: str,
    type: Literal['fact', 'preference', 'insight', 'event', 'axiom', 'core'],
    scope: Literal['incarnation', 'universal', 'user', 'persona'] = 'incarnation',
    confidence: float = 1.0,
    context_ref: str | None = None,
    source_agent: str | None = None,
    source_harness: str | None = None,
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
        confidence(float): Confidence score in [0.0, 1.0] (default 1.0).
        context_ref(str): Optional source file or URI reference (e.g. 'src/auth.py#L10-L20').
        source_agent(str): Optional agent identifier recording this observation.
        source_harness(str): Optional harness identifier (e.g. 'antigravity', 'pycharm').
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

    from tur.provenance import create_provenance_and_decay

    prov, dec = create_provenance_and_decay(
        memory_type=mem_type,
        confidence=confidence,
        context_ref=context_ref,
        source_agent=source_agent,
        source_harness=source_harness or os.environ.get('TUR_HARNESS'),
    )

    memory = Memory(
        type=mem_type,
        scope=mem_scope,
        tags=['mcp', 'agent'],
        content=content,
        source_session=_active_session_id or get_active_session_id(),
        confidence=confidence,
        provenance=prov,
        decay=dec,
    )
    saved_path = manager.save(memory)
    return f'Learned successfully (Scope: {mem_scope.value}). ID: {memory.id} File: {saved_path.name}'


@mcp.tool()
@mcp_contention_guard()
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


_background_tasks: set[asyncio.Task] = set()


@mcp.tool()
@mcp_contention_guard()
async def introspect(bootstrap: bool = False, ctx: Context | None = None) -> str:
    """
    Compress L1 event logs into the L2 Cognitive Map using the Council Assembly pipeline.
    This runs the full introspection compaction loop, consolidating raw memories
    into permanent concepts and relations.

    Args:
        bootstrap(bool): If True, forces a complete re-bootstrap of the graph from all memories,
                         clearing any existing graph.
    """
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)

    try:
        def on_mcp_progress(curr: int, tot: int, msg: str):
            if ctx is not None:
                with contextlib.suppress(Exception):
                    t1 = asyncio.create_task(ctx.report_progress(progress=curr, total=tot))
                    _background_tasks.add(t1)
                    t1.add_done_callback(_background_tasks.discard)
                    try:
                        loop = asyncio.get_running_loop()
                        t2 = loop.create_task(ctx.info(f'[{curr}/{tot}] {msg}'))
                        _background_tasks.add(t2)
                        t2.add_done_callback(_background_tasks.discard)
                    except Exception:
                        pass

        from tur.introspection import format_graph_as_mermaid, run_introspection

        graph = run_introspection(
            persona_dir,
            bootstrap=bootstrap,
            mcp_context=ctx,
            progress_callback=on_mcp_progress,
        )
        await asyncio.sleep(0)

        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        mermaid = format_graph_as_mermaid(graph)
    except LockTimeoutError:
        raise
    except Exception as e:
        return f'Error during Council Introspection: {e}'
    else:
        return (
            f'Council Introspection complete. '
            f'L2 Cognitive Map: {node_count} nodes, {edge_count} edges.\n\n'
            f'```mermaid\n{mermaid}\n```'
        )


@mcp.tool()
@mcp_contention_guard()
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
        return note_logic(content, session_id=_active_session_id)
    except LockTimeoutError:
        raise
    except Exception as e:
        return f'Error updating note: {e}'


@mcp.tool()
async def sleep(
    note: str,
    log_content: str,
    session_id: str | None = None,
    model: str = 'gemini-3.7-flash',
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

    if ctx is not None:
        with contextlib.suppress(Exception):
            await ctx.info(f"Appending final session note: '{note[:40]}...'")
            await ctx.report_progress(progress=1, total=3)

    # Append mandatory final note and auto-end session on sleep
    if resolved_session_id:
        try:
            note_logic(note, session_id=resolved_session_id)
        except LockTimeoutError as e:
            return format_contention_error(e)
        except Exception as e:
            return f'Error appending final note: {e}'
        try:
            end_session_logic(resolved_session_id)
        except LockTimeoutError as e:
            return format_contention_error(e)
        except Exception as e:
            return f'Error ending session: {e}'

    if ctx is not None:
        with contextlib.suppress(Exception):
            await ctx.info('Dehydrating session transcript & extracting insights (Dreaming)...')
            await ctx.report_progress(progress=2, total=3)

    try:
        active_id = get_active_persona_id()
        count = perform_sleep_dreaming(
            log_content=log_content, active_id=active_id, session_id=resolved_session_id, model=model, ctx=ctx
        )
        if ctx is not None:
            with contextlib.suppress(Exception):
                await ctx.report_progress(progress=3, total=3)
                await ctx.info(f'Consolidated {count} memories. Persona is now sleeping.')
    except LockTimeoutError as e:
        return format_contention_error(f'State lock currently held during dreaming consolidation: {e}')
    except Exception as e:
        return f'Error during dreaming: {e}'
    else:
        _active_session_id = None
        return f'Dreams consolidated. {count} new memories formed and persona is now sleeping.'


@mcp.tool()
def recall(
    query: str,
    effort: int = 0,
    deep: bool = False,
    mermaid: bool = False,
    top_k: int = 5,
) -> str:
    """
    Search your deep memory bank for past events, decisions, or knowledge with graph-theoretic retrieval (EP-0136).

    Args:
        query: The topic or concept to search for in past memories.
        effort: Cognitive effort level in [0..10].
                0: Fast BM25 keyword discrete lookup (<5ms).
                1-4: Vector match + 1-Hop Ego Neighborhood context (~20ms).
                5-7: HippoRAG Personalized PageRank + Louvain Community Subgraph (~50ms).
                8-10: Full PPR + Louvain + TMS contradiction checks + Git anchor validation (~120ms).
        deep: Convenience alias for effort=5.
        mermaid: If True, include a rendered Mermaid flowchart diagram of the retrieved subgraph.
        top_k: Maximum number of focal memory nodes to return (default 5).
    """
    from tur.recall import topological_recall

    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    return topological_recall(
        query=query,
        persona_dir=persona_dir,
        effort=effort,
        deep=deep,
        mermaid=mermaid,
        top_k=top_k,
    )


@mcp.tool()
def metrics(identifier: str | None = None) -> dict:
    """
    Calculate Constraint Dimensionality (Cp), cognitive load, and spectral graph metrics for a persona (EP-0136).

    Args:
        identifier: The name or UUID of the persona. If omitted, uses the default.
    """
    try:
        report = compute_persona_metrics(identifier)
    except Exception as e:
        return {'error': str(e)}
    else:
        return report.to_dict()


@mcp.resource('tur://context/subgraph/{node_id}')
def get_subgraph_context(node_id: str) -> str:
    """
    Exposes a bounded semantic ego-subgraph context resource for a given node (EP-0136).
    """
    import json

    from tur.introspection import load_cognitive_map
    from tur.recall import CognitiveGraphEngine

    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    graph = load_cognitive_map(persona_dir)

    if graph is None or node_id not in graph:
        return f"Node '{node_id}' not found in L2 Cognitive Map."

    engine = CognitiveGraphEngine(graph)
    sub = engine.extract_bounded_ego_subgraph(center_nodes=[node_id], radius=1, max_nodes=10)
    mermaid_code = engine.format_subgraph_as_mermaid(sub)

    nodes_data = [
        {'id': n, 'type': sub.nodes[n].get('type', 'Concept'), 'content': sub.nodes[n].get('content', '')}
        for n in sub.nodes()
    ]
    return f'{json.dumps(nodes_data, indent=2)}\n\n```mermaid\n{mermaid_code}\n```'


@mcp.tool()
def telemetry(identifier: str | None = None) -> dict:
    """
    Backwards-compatible alias for metrics().
    Calculate Constraint Dimensionality (Cp) and cognitive load metrics for a persona.
    """
    return metrics(identifier=identifier)


@mcp.tool()
def diff_memories(
    base_session_id: str | None = None,
    target_session_id: str | None = None,
    type_filter: str | None = None,
    scope_filter: str | None = None,
) -> list[dict]:
    """
    Inspect memory mutations, additions, supersessions, and contradictions across sessions (EP-0133).
    Categorizes deltas into ADDED, SUPERSEDED, REFUTED, DECAYED, and MODIFIED.

    Args:
        base_session_id: Base session ID to compare against (defaults to target session's parent in lineage DAG).
        target_session_id: Target session ID (defaults to active session).
        type_filter: Optional filter by memory type (e.g. 'fact', 'insight', 'preference', 'axiom').
        scope_filter: Optional filter by memory scope (e.g. 'incarnation', 'universal').
    """
    from tur.diff import compute_session_diff, format_diff_json

    resolved_target = target_session_id or _active_session_id or get_active_session_id()
    deltas = compute_session_diff(
        base_session_id=base_session_id,
        target_session_id=resolved_target,
        type_filter=type_filter,
        scope_filter=scope_filter,
    )
    return format_diff_json(deltas)


@mcp.tool()
def diff(
    base_session_id: str | None = None,
    target_session_id: str | None = None,
    type_filter: str | None = None,
    scope_filter: str | None = None,
) -> list[dict]:
    """
    Alias for diff_memories(). Inspect memory mutations across sessions (EP-0133).
    """
    return diff_memories(
        base_session_id=base_session_id,
        target_session_id=target_session_id,
        type_filter=type_filter,
        scope_filter=scope_filter,
    )


@mcp.tool()
def read_notes(session_id: str | None = None, include_previous: bool = False, limit: int = 50) -> list[dict]:
    """
    Returns the session broadcast notes in strict ascending sequence order.

    Args:
        session_id: Optional specific session ID, or 'previous' to resolve immediate parent.
        include_previous: If True, prepends notes from the parent session up to limit.
        limit: Maximum number of notes to retrieve.
    """
    sess_id = session_id or _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    return read_notes_logic(sess_id, limit=limit, include_previous=include_previous)


@mcp.tool()
def signal(
    to: str,
    content: str,
    type: str = 'inform',
    sender_id: str | None = None,
    vector_clock: dict[str, int] | None = None,
) -> str:
    """
    Sends a message signal to another manifestation or broadcast to all ('*').
    Enforces a token-bucket rate limiter of 10 messages/minute and attaches Lamport Vector Clocks (EP-0141).
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if sender_id and env_agent_id and sender_id != env_agent_id and not sender_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: sender_id '{sender_id}' does not match calling agent '{env_agent_id}'.")
    sender = sender_id or env_agent_id or 'mcp_agent'
    return signal_logic(sess_id, sender, to, content, type, vector_clock=vector_clock)


@mcp.tool()
def read_signals(
    agent_id: str | None = None,
    unread_only: bool = True,
    causal_delivery: bool = True,
) -> list[dict]:
    """
    Peeks incoming signals directed to the agent or its namespaces with causal partial order delivery (EP-0141).
    """
    sess_id = _active_session_id or get_active_session_id()
    if not sess_id:
        raise ValueError('No active session ID found.')
    env_agent_id = os.environ.get('TUR_AGENT_ID')
    if agent_id and env_agent_id and agent_id != env_agent_id and not agent_id.startswith(env_agent_id + '.'):
        raise ValueError(f"Namespace violation: agent_id '{agent_id}' does not match calling agent '{env_agent_id}'.")
    active_agent = agent_id or env_agent_id or 'mcp_agent'
    return read_signals_logic(sess_id, active_agent, unread_only, causal_delivery=causal_delivery)


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
@mcp_contention_guard()
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
