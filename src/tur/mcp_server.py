import json
import os
from pathlib import Path
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

# Defer imports until AFTER the working directory is set
import yaml
from tur.compiler import compile_persona
from tur.main import get_active_persona_id, get_persona_path, get_user_profile
from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType, Persona, PersonaIndex, SessionState, UserProfile
from tur.telemetry import CognitiveTelemetry

mcp = FastMCP("tur-server", json_response=True)

@mcp.tool()
def tur_wake() -> str:
    """Returns the active persona ID."""
    active_id = get_active_persona_id()
    return f"Active Persona ID: {active_id}"

@mcp.tool()
def tur_compile() -> str:
    """Compiles the active persona and returns the full System Prompt Constitution."""
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)

    file_path = persona_dir / "persona.yaml"
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    persona = Persona(**data)
    user = get_user_profile()
    memories = manager.load_all()

    state = SessionState(
        persona=persona,
        user=user,
        memories=memories,
        epilogue="Status: Conserved. Aleph: Restored. Carry on, Lion."
    )
    return compile_persona(state)

@mcp.tool()
def tur_memorize(content: str, type: str) -> str:
    """Save a new fact or protocol to the active persona's permanent memory."""
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)
    
    mem_type = MemoryType(type)
    memory = Memory(
        type=mem_type,
        scope=MemoryScope.INCARNATION,
        tags=["mcp"],
        content=content
    )
    saved_path = manager.save(memory)
    return f"Memorized successfully. ID: {memory.id} File: {saved_path.name}"

@mcp.tool()
def tur_telemetry() -> str:
    """Quantify the Cognitive Load (Cp) and static token cost of the active persona."""
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    
    file_path = persona_dir / "persona.yaml"
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    persona = Persona(**data)
    user = UserProfile(name="Telemetry", role="Observer")
    state = SessionState(persona=persona, user=user, memories=[])
    system_prompt = compile_persona(state)

    telemetry_engine = CognitiveTelemetry()
    static_metrics = telemetry_engine.measure_static_load(system_prompt)
    cp = telemetry_engine.calculate_constraint_dimensionality(persona)
    
    return json.dumps({
        "active_persona": active_id,
        "name": persona.name,
        "constraint_dimensionality": cp,
        "static_token_cost": static_metrics['est_tokens'],
        "information_density": static_metrics['density']
    }, indent=2)

@mcp.tool()
def tur_forget(memory_id: str) -> str:
    """Archive a memory by its ID for the active persona."""
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)
    manager.archive(memory_id)
    return f"Memory {memory_id} archived successfully."

@mcp.tool()
def tur_list_memories() -> str:
    """List all active memories in the bank for the active persona."""
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all(include_archived=False)
    mem_list = [{"id": str(m.id), "type": m.type.value, "content": m.content} for m in mems]
    return json.dumps(mem_list, indent=2)

@mcp.tool()
def tur_list_personas() -> str:
    """List all available personas in the index."""
    index_path = Path(".tur/personas.yaml")
    if not index_path.exists():
        raise FileNotFoundError("No personas found.")
        
    with open(index_path, encoding="utf-8") as f:
        index = PersonaIndex(**yaml.safe_load(f))
        
    persona_list = [{"id": str(p.id), "name": p.name, "version": p.version} for p in index.personas]
    return json.dumps(persona_list, indent=2)

def main():
    """Entry point for the MCP server."""
    # For IDE integration, we default to stdio.
    # The transport can be overridden by environment variables if needed.
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
