"""
Execution and dispatch engine for Cognitive Skill Contracts (EP-0137).
"""

import contextlib
import json
from pathlib import Path
import subprocess
from typing import Any
import uuid

import yaml

from tur._helpers import format_delegation_prompt, yaml_safe_load
from tur.contracts.dreaming import DreamingDeltaOutput
from tur.contracts.forge import PersonaForgeOutput
from tur.contracts.registry import get_contract, validate_contract
from tur.memory.storage import MemoryManager
from tur.models import (
    Memory,
    MemoryScope,
    MemoryType,
    Persona,
    PersonaIndex,
    PersonaIndexEntry,
    Principle,
)
from tur.paths import PERSONAS_FILENAME, resolve_personas_base_dir, resolve_workspace_dir
from tur.persona import get_persona_path, save_constitution
from tur.scaffold import scaffold_workspace


def apply_forge_output(
    output: PersonaForgeOutput,
    base_dir: Path | None = None,
    workspace_dir: Path | None = None,
) -> tuple[str, str]:
    """
    Instantiates and commits a new Persona and associated scaffolding from a PersonaForgeOutput contract.

    Returns:
        tuple[str, str]: (persona_id_str, persona_name)
    """
    base_dir = base_dir or resolve_personas_base_dir()
    personas_dir = base_dir / "personas"
    index_path = base_dir / PERSONAS_FILENAME
    personas_dir.mkdir(parents=True, exist_ok=True)

    persona_id = uuid.uuid4()
    persona_folder = personas_dir / str(persona_id)
    persona_folder.mkdir(parents=True, exist_ok=True)

    # Convert initial principles to Principle models
    principles: list[Principle] = []
    for p in output.initial_principles:
        principles.append(
            Principle(
                name=p.name,
                avatar=p.avatar,
                role=p.role,
                weight=p.weight,
                constraints=p.constraints,
            )
        )

    if not principles:
        principles = [
            Principle(name="Symmetry", avatar=None, role="Guardian of Invariance", weight=1.5),
            Principle(name="Safety", avatar=None, role="Containment Protocol", weight=2.0),
        ]

    persona_obj = Persona(
        name=output.name,
        aleph=output.aleph,
        principles=principles,
        version=output.version,
        model=output.model,
        description=output.description,
    )

    # Save CONSTITUTION.md
    if output.constitution_content.strip():
        constitution_file = persona_folder / "CONSTITUTION.md"
        constitution_file.write_text(output.constitution_content.strip() + "\n", encoding="utf-8")
    else:
        save_constitution(persona_folder, persona_obj)

    # Save persona.yaml (backwards compatibility)
    persona_yaml_file = persona_folder / "persona.yaml"
    with open(persona_yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(persona_obj.model_dump(mode="json"), f, sort_keys=False)

    # Register in personas.yaml index
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            index_data: dict = yaml_safe_load(f) or {"personas": []}
            index = PersonaIndex(**index_data)
    else:
        index = PersonaIndex(personas=[])

    entry = PersonaIndexEntry(id=persona_id, name=persona_obj.name, version=persona_obj.version)
    index.personas.append(entry)

    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index.model_dump(mode="json"), f, sort_keys=False)

    # Handle AGENTS.md in workspace
    ws = workspace_dir or resolve_workspace_dir() or Path.cwd()
    if output.agents_md_content.strip():
        agents_file = ws / "AGENTS.md"
        agents_file.write_text(output.agents_md_content.strip() + "\n", encoding="utf-8")
    else:
        with contextlib.suppress(Exception):
            scaffold_workspace(force=False, workspace_dir=ws)

    # Seed initial axioms in memory ledger
    manager = MemoryManager(base_dir=persona_folder)
    for ax in output.initial_axioms:
        scope = MemoryScope(ax.scope) if isinstance(ax.scope, str) else ax.scope
        mem = Memory(
            type=MemoryType.AXIOM,
            scope=scope,
            content=ax.content,
            confidence=ax.confidence,
            tags=[*ax.tags, "forge", "axiom"],
        )
        manager.save(mem)

    return str(persona_id), persona_obj.name


def apply_dreaming_output(
    output: DreamingDeltaOutput,
    active_id: str,
    session_id: str | None = None,
) -> dict[str, int]:
    """
    Commits memory records, supersessions, refutations, and staged core memories
    from a DreamingDeltaOutput contract into persistent state.

    Returns:
        dict[str, int]: Summary counts of applied delta records.
    """
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)

    added_count = 0
    for rec in output.added_memories:
        m_type = MemoryType(rec.type) if isinstance(rec.type, str) else rec.type
        m_scope = MemoryScope(rec.scope) if isinstance(rec.scope, str) else rec.scope
        mem = Memory(
            type=m_type,
            scope=m_scope,
            content=rec.content,
            confidence=rec.confidence,
            tags=[*rec.tags, "dreaming"],
            source_session=session_id,
        )
        manager.save(mem)
        added_count += 1

    superseded_count = 0
    for link in output.superseded_memories:
        with contextlib.suppress(Exception):
            manager.subsume(link.superseded_id)
            superseded_count += 1

    refuted_count = 0
    for ref in output.tms_refutations:
        with contextlib.suppress(Exception):
            manager.archive(ref.refuted_id)
            refuted_count += 1

    staged_core_count = 0
    for stage in output.staged_core_memories:
        scope = MemoryScope(stage.scope) if isinstance(stage.scope, str) else stage.scope
        mem = Memory(
            type=MemoryType.CORE,
            scope=scope,
            content=stage.content,
            tags=["staged_core", stage.type] + ([stage.principle] if stage.principle else []),
            source_session=session_id,
        )
        manager.save(mem)
        staged_core_count += 1

    return {
        "added": added_count,
        "superseded": superseded_count,
        "refuted": refuted_count,
        "staged_core": staged_core_count,
    }


def format_contract_delegation(
    contract_name: str,
    input_payload: Any,
    primary_commit_cmd: str,
    secondary_commit_cmd: str | None = None,
    title: str | None = None,
    task_instructions: str | None = None,
) -> str:
    """
    Builds a standardized `# TUR DELEGATION: {Title}` prompt for an external harness
    conforming to the target contract's output schema.
    """
    contract = get_contract(contract_name)
    title = title or f"{contract.name.capitalize()} Cognitive Delegation"
    task_instructions = task_instructions or (
        f"Execute cognitive operation for contract '{contract.name}': {contract.description}"
    )

    if hasattr(input_payload, "model_dump_json"):
        input_json = input_payload.model_dump_json(indent=2)
    elif isinstance(input_payload, (dict, list)):
        input_json = json.dumps(input_payload, indent=2, default=str)
    else:
        input_json = str(input_payload)

    input_sections = [
        ("Input Context", input_json),
    ]

    return format_delegation_prompt(
        title=title,
        task_instructions=task_instructions,
        input_sections=input_sections,
        schema=contract.output_schema,
        primary_commit_cmd=primary_commit_cmd,
        secondary_commit_cmd=secondary_commit_cmd,
    )


def execute_external_skill_command(
    command_str: str,
    input_payload: Any,
    timeout: float = 60.0,
) -> str:
    """
    Executes a configured external shell command or CLI plugin for a cognitive skill.
    Pipes input JSON to stdin and returns stdout.
    """
    if hasattr(input_payload, "model_dump_json"):
        input_json = input_payload.model_dump_json()
    elif isinstance(input_payload, (dict, list)):
        input_json = json.dumps(input_payload, default=str)
    else:
        input_json = str(input_payload)

    proc = subprocess.run(
        command_str,
        input=input_json,
        text=True,
        capture_output=True,
        shell=True,
        timeout=timeout,
        check=True,
    )
    return proc.stdout.strip()
