import os
from pathlib import Path

import typer
import yaml
from rich.console import Console

from tur.compiler import compile_persona
from tur.memory import MemoryManager
from tur.models import (
    Memory,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    Persona,
    PersonaIndex,
    PersonaIndexEntry,
    SessionState,
    UserProfile,
)
from tur.telemetry import CognitiveTelemetry
from tur.tui import init_wizard, select_persona_wizard

app = typer.Typer(
    help="Tur: Persona Lifecycle Manager (Wake/Sleep)",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
)
console = Console()


def get_user_profile() -> UserProfile:
    """
    Loads the user profile from the project's .tur/user.yaml or a global default.
    """
    local_user_path = Path(".tur/user.yaml")
    global_user_path = Path.home() / ".tur" / "user.yaml"

    config_path = None
    if local_user_path.exists():
        config_path = local_user_path
    elif global_user_path.exists():
        config_path = global_user_path

    if config_path:
        with open(config_path, encoding="utf-8") as f:
            user_data = yaml.safe_load(f)
        return UserProfile(**user_data)
    else:
        # Fallback to a default user if no config is found
        return UserProfile(
            name="Default User",
            role="Architect",
            domain_expertise=["Software Development"],
            core_values=["Clarity", "Simplicity"]
        )


def get_active_persona_id(identifier: str | None = None) -> str:
    """
    Resolves the active persona ID.
    - If an identifier is provided, it's returned.
    - If not, it checks the .tur/state.yaml file.
    - If the state file doesn't exist, it launches a TUI to select and set the default.
    """
    if identifier:
        return identifier

    state_path = Path(".tur/state.yaml")
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            state_data = yaml.safe_load(f)
        active_id = state_data.get("active_persona_id")
        if active_id:
            return active_id

    # If we're here, no default is set, so we launch the selector TUI
    index_path = Path(".tur/personas.yaml")
    if not index_path.exists():
        raise FileNotFoundError("No personas found. Please run `tur init` to create one.")

    with open(index_path, encoding="utf-8") as f:
        index = PersonaIndex(**yaml.safe_load(f))

    if not index.personas:
        raise ValueError("No personas available to select. Please run `tur init`.")

    new_active_id = select_persona_wizard(index)
    if not new_active_id:
        raise typer.Exit("No persona selected. Aborting.")

    return new_active_id


def get_persona_path(identifier: str) -> Path:
    """
    Resolves a persona identifier (UUID or name) to its directory path.
    """
    base_dir = Path(".tur")
    index_path = base_dir / "personas.yaml"

    if not index_path.exists():
        raise FileNotFoundError("No personas.yaml index found. Please run migration or init.")

    with open(index_path, encoding="utf-8") as f:
        index_data = yaml.safe_load(f)
        index = PersonaIndex(**index_data)

    for entry in index.personas:
        if str(entry.id) == identifier or entry.name.lower() == identifier.lower():
            return base_dir / "personas" / str(entry.id)

    raise ValueError(f"Persona '{identifier}' not found in index.")


@app.command()
def clone(
        identifier: str = typer.Argument(..., help="The name or UUID of the persona to clone"),
        new_name: str = typer.Argument(..., help="The name of the new cloned persona")
):
    """Duplicate an existing persona into a new identity."""
    try:
        import shutil
        import uuid
        from datetime import datetime

        source_dir = get_persona_path(identifier)
        base_dir = Path(".tur")
        new_id = str(uuid.uuid4())
        target_dir = base_dir / "personas" / new_id

        # Copy directory
        shutil.copytree(source_dir, target_dir)

        # Update persona.yaml
        persona_path = target_dir / "persona.yaml"
        with open(persona_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        data["name"] = new_name
        data["version"] = "1.0.0-cloned"

        with open(persona_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        # Update Index
        index_path = base_dir / "personas.yaml"
        with open(index_path, encoding="utf-8") as f:
            index_data = yaml.safe_load(f)
            index = PersonaIndex(**index_data)

        new_entry = PersonaIndexEntry(id=new_id, name=new_name, version=data["version"])
        index.personas.append(new_entry)

        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(index.model_dump(mode='json'), f)

        console.print(f"[green]Persona '{identifier}' successfully cloned to '{new_name}' ({new_id})[/green]")

    except Exception as e:
        console.print(f"[red]Error cloning persona: {e}[/red]")


@app.command()
def forget(
        memory_id: str = typer.Argument(..., help="The ID of the memory to forget"),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Archive a memory by its ID for a specific persona."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        memory_manager.archive(memory_id)
        console.print(f"[green]Memory {memory_id} has been forgotten (archived).[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def init():
    """Bootstrap a new persona via an interactive TUI questionnaire."""
    init_wizard()


@app.command()
def memories(
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        include_archived: bool = typer.Option(False, help="Include forgotten memories")
):
    """Show all memories in the bank for a specific persona."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)
        mems = memory_manager.load_all(include_archived=include_archived)

        if not mems:
            console.print(f"The Memory Bank for {active_id} is empty.")
            return

        from rich.table import Table

        table = Table(title=f"Memory Bank ({active_id})", show_lines=True)
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Content")

        for m in mems:
            content_snippet = (m.content[:80] + '..') if len(m.content) > 80 else m.content

            row_style = "dim" if m.status == MemoryStatus.ARCHIVED else ""
            table.add_row(str(m.id), m.type.value, content_snippet, style=row_style)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def memorize(
        content: str = typer.Argument(..., help="The content of the memory to store."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        type: MemoryType = typer.Option(MemoryType.INSIGHT, help="The type of memory."),
        scope: MemoryScope = typer.Option(MemoryScope.INCARNATION, help="The scope of the memory."),
        session_id: str = typer.Option(None, help="The name/ID of the session this memory belongs to")
):
    """Create a new memory for a persona."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
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
def serve(
    transport: str = typer.Option("stdio", help="The transport protocol for the MCP server ('stdio' or 'streamable-http').")
):
    """Run the Tur MCP server."""
    from tur.mcp_server import main as mcp_main
    console.print(f"[bold green]Starting Tur MCP server with {transport} transport...[/bold green]")
    mcp_main(transport=transport)


@app.command()
def sleep(
        log_path: str = typer.Argument(..., help="Path to the chat log file to be parsed."),
        identifier: str | None = typer.Argument(None,
                                                help="The name or UUID of the persona. If omitted, uses the default."),
        session_id: str = typer.Option(None, help="The name/ID of the session these memories belong to"),
        model: str = typer.Option("gemini-3.1-pro-preview", help="The model to use for dreaming (insight extraction)")
):
    """Dehydrate a session by parsing a chat log to extract memories."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        memory_manager = MemoryManager(base_dir=persona_dir)

        console.print(f"Processing session log for '{active_id}' from {log_path}...")
        console.print(f"Extracting insights using {model}... (Dreaming)")

        try:
            with open(log_path, encoding="utf-8") as f:
                log_content = f.read()

            # Configure Gemini
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
                raise typer.Exit(code=1)  # noqa: TRY301

            from google import genai
            from google.genai import types
            from pydantic import BaseModel, Field

            client = genai.Client(api_key=api_key)

            class ExtractedMemory(BaseModel):
                type: MemoryType = Field(description="The classification of the memory.")
                content: str = Field(description="The actual memory content...")
                scope: MemoryScope = Field(description="The context reach of this memory.")
                tags: list[str] = Field(description="A list of tags. (e.g. ['tag1', 'tag2'])")

            class Dream(BaseModel):
                memories: list[ExtractedMemory]

            prompt = f"""
            You are the Subconscious of a Persona Engineering system.
            Analyze the following chat log and extract key insights,
            facts, or axioms that should be retained in long-term memory.

            Focus on:
            1. User preferences (what the user likes/dislikes).
            2. Important project facts (architectural decisions, tech stack).
            3. Philosophical axioms derived during the session.

            Chat Log:
            {log_content}
            """

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=Dream.model_json_schema(),
                ),
            )

            import json
            dream_data = json.loads(response.text)
            extracted_memories = dream_data.get("memories", [])

            count = 0
            for mem_data in extracted_memories:
                memory = Memory(
                    type=mem_data["type"],
                    scope=mem_data["scope"],
                    tags=[*mem_data.get("tags", []), "dreaming"],
                    content=mem_data["content"],
                    source_session=session_id
                )
                memory_manager.save(memory)
                count += 1
                console.print(f"  [green]+ Consolidated:[/green] {memory.content[:50]}...")

            console.print(f"[bold green]Dreams consolidated. {count} new memories formed.[/bold green]")

        except Exception as e:
            console.print(f"[red]Error during dreaming: {e}[/red]")

        typer.echo("State saved. Persona is now sleeping.")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def switch():
    """Set a new default persona."""

    index_path = Path(".tur/personas.yaml")
    if not index_path.exists():
        console.print("[red]No personas found. Please run `tur init` to create one.[/red]")
        raise typer.Exit(code=1)

    with open(index_path, encoding="utf-8") as f:
        index = PersonaIndex(**yaml.safe_load(f))

        if not index.personas:
            console.print("[red]No personas available to select. Please run `tur init`.[/red]")
            raise typer.Exit(code=1)

        try:
            new_active_id = select_persona_wizard(index)
            if new_active_id:
                console.print(f"[green]Default persona switched to: {new_active_id}[/green]")
            else:
                console.print("[yellow]Switch cancelled.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error switching persona: {e}[/red]")
            raise typer.Exit(code=1)


@app.command()
def telemetry(
        identifier: str | None = typer.Argument(
            None,
            help="The name or UUID of the persona. If omitted, uses the default."
        )
):
    """Quantify the Cognitive Load (Cp) of a persona."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        file_path = persona_dir / "persona.yaml"

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        persona = Persona(**data)

        # Mock state for compilation measurement
        user = UserProfile(name="Telemetry", role="Observer")
        state = SessionState(persona=persona, user=user, memories=[])
        system_prompt = compile_persona(state)

        telemetry_engine = CognitiveTelemetry()
        static_metrics = telemetry_engine.measure_static_load(system_prompt)
        cp = telemetry_engine.calculate_constraint_dimensionality(persona)

        console.print(f"[bold cyan]--- TELEMETRY REPORT: {persona.name} ---[/bold cyan]")
        console.print(f"Active Persona: {active_id} ({persona.name})")
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
def wake(identifier: str | None = typer.Argument(
    None,
    help="The name or UUID of the persona. If omitted, uses the default.")
):
    """Activate a persona by name or UUID."""
    try:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)
        file_path = persona_dir / "persona.yaml"

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 1. Load Persona (The DNA)
        persona = Persona(**data)

        # 2. Inject User Context (The Architect)
        user = get_user_profile()

        # 3. Hydrate State (The Soul)
        memory_manager = MemoryManager(base_dir=persona_dir)
        memories = memory_manager.load_all()

        state = SessionState(
            persona=persona,
            user=user,
            memories=memories,
            epilogue="Status: Conserved. Aleph: Restored. Carry on, Lion."
        )

        # 4. Compile (The Awakening)
        system_prompt = compile_persona(state)

        # Output
        console.print(f"[bold green]--- SYSTEM WAKE: {persona.name} (v{persona.version}) ---[/bold green]")
        console.print(f"[dim]Active Persona: {active_id} ({persona.name})[/dim]")

        # Use a rich panel or syntax highlighting for the prompt if desired,
        # but plain printing is often best for raw system prompts to be copied.
        console.print(system_prompt)

        console.print("[bold green]--- SYSTEM READY ---[/bold green]")

    except Exception as e:
        console.print(f"[red]Error waking persona: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
