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
    if Path(".tur").exists():
        return
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".tur").exists():
            os.chdir(parent)
            return


_ensure_project_root()

# Defer imports until AFTER the working directory is set to ensure they resolve correctly,
# even if this script is launched from a different CWD.

from tur.compiler import compile_persona  # noqa: E402
from tur.main import (  # noqa: E402
    get_active_persona_id,
    get_persona_path,
    hydrate_session_state,
    perform_sleep_dreaming,
)
from tur.memory import MemoryManager  # noqa: E402
from tur.models import Memory, MemoryScope, MemoryType  # noqa: E402
from tur.telemetry import CognitiveTelemetry  # noqa: E402


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Lifecycle hook for startup and graceful shutdown."""
    print("Starting Tur MCP Server (Ontological Porcelain) on stdio...", file=sys.stderr)
    try:
        yield {}
    finally:
        print("\nShutting down Tur MCP Server gracefully...", file=sys.stderr)


mcp = FastMCP("tur-server", json_response=True, lifespan=server_lifespan)


@mcp.tool()
def wake() -> str:
    """
    Read your core identity, directives, and system metrics (formerly who_am_i).
    Call this when you need to remember your constraints or understand your current cognitive load.
    """
    active_id = get_active_persona_id()
    state = hydrate_session_state(active_id)
    system_prompt = compile_persona(state)

    # Append Telemetry Metadata
    telemetry_engine = CognitiveTelemetry()
    static_metrics = telemetry_engine.measure_static_load(system_prompt)
    cp = telemetry_engine.calculate_constraint_dimensionality(state.persona)

    telemetry_block = (
        f"\n\n--- [SYSTEM METRICS] ---\n"
        f"Active Persona ID: {active_id}\n"
        f"Constraint Dimensionality (Cp): {cp}\n"
        f"Static Token Cost: {static_metrics['est_tokens']}\n"
        f"Information Density: {static_metrics['density']:.2f}\n"
    )

    return system_prompt + telemetry_block


@mcp.tool()
def learn(
        content: str,
        type: Literal['fact', 'preference', 'insight', 'event', 'axiom'],
        scope: Literal["incarnation", "universal"] = "incarnation"
) -> str:
    """
    Assimilate a new invariant, fact, or insight into your permanent, cross-session memory.
    Call this when you deduce something that must survive a context window reset.

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
          must be one of: 'incarnation', 'universal'. Default is 'incarnation'.
         'incarnation' means it's only relevant to this specific project instance.
         'universal' means it's a general truth that should be shared across all your personas and projects.
    """
    try:
        mem_type = MemoryType(type)
    except ValueError:
        valid_types = ", ".join([t.value for t in MemoryType])
        return f"Error: Invalid memory_type '{type}'. Must be one of: {valid_types}"

    try:
        mem_scope = MemoryScope(scope)
    except ValueError:
        valid_scopes = ", ".join([s.value for s in MemoryScope])
        return f"Error: Invalid scope '{scope}'. Must be one of: {valid_scopes}"

    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)

    memory = Memory(
        type=mem_type,
        scope=mem_scope,
        tags=["mcp", "agent"],
        content=content
    )
    saved_path = manager.save(memory)
    return f"Learned successfully (Scope: {mem_scope.value}). ID: {memory.id} File: {saved_path.name}"


@mcp.tool()
def spark(content: str) -> str:
    """
    Update the transient session spark (epilogue.md) for the active persona (formerly update_spark).
    This replaces the current short-term context.
    """
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)

    spark_path = persona_dir / "epilogue.md"
    with open(spark_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

    return f"Spark successfully updated for '{active_id}'."


@mcp.tool()
def sleep(
        log_content: str,
        session_id: str | None = None,
        model: str = "gemini-3.1-pro-preview"
) -> str:
    """
    Dehydrate a session by parsing the active session's chat log to extract memories.
    Call this when the active session is ending and you want to consolidate L1 memories.

    Args:
        log_content(str): The full text/markdown chat transcript of the current session.
        session_id(str): The optional ID of the session these memories belong to.
        model(str): The model to use for dreaming (default is 'gemini-3.1-pro-preview').
    """
    try:
        active_id = get_active_persona_id()
        count = perform_sleep_dreaming(
            log_content=log_content,
            active_id=active_id,
            session_id=session_id,
            model=model
        )
    except Exception as e:
        return f"Error during dreaming: {e}"
    else:
        return f"Dreams consolidated. {count} new memories formed and persona is now sleeping."



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

    mem_list = [{"id": str(m.id), "type": m.type.value, "content": m.content} for m in results]
    return json.dumps(mem_list, indent=2)


def main(transport: Literal["stdio", "sse"] = "stdio", port: int = 8000):
    """Entry point for the MCP server."""
    try:
        match transport:
            case 'sse':
                print(f"Starting SSE server on port {port}...", file=sys.stderr)
                mcp.settings.port = port
            case 'stdio':
                print("Starting stdio server...", file=sys.stderr)
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


if __name__ == "__main__":
    main()
