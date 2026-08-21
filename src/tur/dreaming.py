import os
from datetime import UTC
from typing import Any

from rich.console import Console

from tur._helpers import _clean_json_response, _mcp_sample, run_async
from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType
from tur.persona import get_persona_path

console = Console()


def perform_sleep_dreaming(
    log_content: str,
    active_id: str,
    session_id: str | None = None,
    model: str = 'gemini-3.1-pro-preview',
    ctx: Any = None,
    commit_payload: str | dict | None = None,
) -> int:
    """
    Dehydrate a session log by parsing it to extract memories.
    Returns the number of extracted memories.
    """
    import json
    from pathlib import Path

    from pydantic import BaseModel, Field

    persona_dir = get_persona_path(active_id)
    memory_manager = MemoryManager(base_dir=persona_dir)

    class ExtractedMemory(BaseModel):
        type: MemoryType = Field(description='The classification of the memory.')
        content: str = Field(description='The actual memory content...')
        scope: MemoryScope = Field(description='The context reach of this memory.')
        tags: list[str] = Field(description="A list of tags. (e.g. ['tag1', 'tag2'])")

    class Dream(BaseModel):
        memories: list[ExtractedMemory]

    from tur._helpers import _clean_json_response, parse_multi_json_payloads

    if commit_payload:
        payloads = parse_multi_json_payloads(commit_payload)
        extracted_memories = []
        for p in payloads:
            if isinstance(p, dict):
                if 'memories' in p and isinstance(p['memories'], list):
                    extracted_memories.extend(p['memories'])
                elif 'type' in p and 'content' in p:
                    extracted_memories.append(p)
    else:
        prompt = f"""
    Analyze the following session chat log and extract durable long-term memories
    that should be consolidated across sessions.

    Memory Extraction Principles & Scoping Rules:
    - Scope Assignment:
      - `universal`: User preferences, persona identity, and general engineering principles.
      - `incarnation`: Architectural decisions, repository constraints, and project-specific states.
    - Memory Type Taxonomy:
      - `axiom`: Permanent, immutable rules, boundary invariants, and fundamental principles.
      - `fact`: Verifiable project states, dependencies, and established technical decisions.
      - `insight`: Synthesized lessons learned, deductions, and architectural breakthroughs.
      - `preference`: User directives, coding tastes, communication style, and workflow preferences.
    - Exclusion Criteria:
      - Do NOT extract transient engineering steps, ephemeral file inspections, or resolved errors.
      - Extract only high-density, durable invariants.

    Chat Log:
    {log_content}

    Your Output MUST be a raw JSON object matching this schema:
    {Dream.model_json_schema()}

    Do not include markdown wrapper blocks (such as ```json) or any conversational text. Return only the JSON object.
    """

        def build_delegation_instructions() -> str:
            from tur._helpers import format_delegation_prompt

            extraction_principles = (
                '- Scope Assignment:\n'
                '  - `universal`: User preferences, persona identity, and general engineering principles.\n'
                '  - `incarnation`: Architectural decisions, repository constraints, and project-specific states.\n'
                '- Memory Type Taxonomy:\n'
                '  - `axiom`: Permanent rules, boundary invariants, and fundamental principles.\n'
                '  - `fact`: Verifiable project states, dependencies, and established technical decisions.\n'
                '  - `insight`: Synthesized lessons learned, deductions, and conceptual breakthroughs.\n'
                '  - `preference`: User directives, coding tastes, and workflow requirements.\n'
                '- Exclusion Criteria (Signal over Noise):\n'
                '  - Do NOT extract transient steps, ephemeral file inspections, or intermediate resolved errors.\n'
                '  - Only extract high-density, durable invariants that should survive session resets.'
            )

            return format_delegation_prompt(
                title='Session Epilogue & Memory Extraction Request',
                task_instructions=(
                    'Analyze the session chat log and extract durable long-term memories, '
                    'categorizing each by type, scope, and tags.'
                ),
                input_sections=[
                    ('Memory Extraction Principles & Scoping Rules', extraction_principles),
                    ('Chat Log to Process', log_content),
                ],
                schema=Dream,
                primary_commit_cmd="tur sleep --commit '<JSON_PAYLOAD>'",
                secondary_commit_cmd="tur learn --json '<JSON_PAYLOAD>'",
            )

        from tur._helpers import require_inference

        resp_text = require_inference(
            prompt=prompt,
            ctx=ctx,
            task_description='session dreaming extraction',
            delegation_instructions_builder=build_delegation_instructions,
            model=model,
            response_schema=Dream.model_json_schema(),
        )

        resp_text = _clean_json_response(resp_text)
        dream_data = json.loads(resp_text)
        extracted_memories = dream_data.get('memories', [])

    count = 0
    for mem_data in extracted_memories:
        m_type = MemoryType(mem_data['type']) if isinstance(mem_data['type'], str) else mem_data['type']
        m_scope = MemoryScope(mem_data['scope']) if isinstance(mem_data['scope'], str) else mem_data['scope']
        memory = Memory(
            type=m_type,
            scope=m_scope,
            tags=[*mem_data.get('tags', []), 'dreaming'],
            content=mem_data['content'],
            source_session=session_id,
        )
        memory_manager.save(memory)
        count += 1
        console.print(f'  [green]+ Consolidated:[/green] {memory.content[:50]}...')

    return count


def stage_sleep_dreaming(
    log_content: str,
    active_id: str,
    session_id: str | None = None,
    model: str = 'gemini-3.1-pro-preview',
    ctx: Any = None,
) -> str:
    """
    Dehydrate a session log to extract memories and return them as a JSON list.
    Does not save to memory manager.
    """
    # Import inside function to avoid circular or early dependency issues
    from pydantic import BaseModel, Field

    from tur.models import MemoryScope, MemoryType

    class ExtractedMemory(BaseModel):
        type: MemoryType = Field(description='The classification of the memory.')
        content: str = Field(description='The actual memory content...')
        scope: MemoryScope = Field(description='The context reach of this memory.')
        tags: list[str] = Field(description="A list of tags. (e.g. ['tag1', 'tag2'])")

    class Dream(BaseModel):
        memories: list[ExtractedMemory]

    prompt = f"""
    You are the Subconscious of a Persona Engineering system.
    Analyze the following chat log and extract key insights,
    facts, or axioms that should be retained in long-term memory.

    Chat Log:
    {log_content}

    Your Output MUST be a raw JSON object matching this schema:
    {Dream.model_json_schema()}

    Do not include markdown wrapper blocks (such as ```json) or any conversational text. Return only the JSON object.
    """

    if ctx is not None:

        async def do_sampling():
            return await _mcp_sample(ctx, prompt)

        resp_text = run_async(do_sampling())
        return _clean_json_response(resp_text)

    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('TUR_LLM_API_KEY')
    if not api_key:
        return '[]'

    from tur._helpers import _local_gemini_generate

    resp_text = _local_gemini_generate(
        prompt=prompt,
        api_key=api_key,
        model=model,
        response_schema=Dream.model_json_schema(),
    )
    return _clean_json_response(resp_text)
