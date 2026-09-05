import json
import os
from datetime import UTC
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console

from tur._helpers import (
    _clean_json_response,
    _mcp_sample,
    format_delegation_prompt,
    parse_multi_json_payloads,
    require_inference,
    run_async,
)
from tur.memory.storage import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType
from tur.persona import get_persona_path

console = Console()


class ExtractedMemory(BaseModel):
    type: MemoryType = Field(description='The classification of the memory.')
    content: str = Field(description='The actual memory content...')
    scope: MemoryScope = Field(description='The context reach of this memory.')
    tags: list[str] = Field(description="A list of tags. (e.g. ['tag1', 'tag2'])")


class Dream(BaseModel):
    memories: list[ExtractedMemory]


DREAMING_EXTRACTION_PRINCIPLES = """- Scope Assignment:
  - `universal`: User preferences, persona identity, and general engineering principles.
  - `incarnation`: Architectural decisions, repository constraints, and project-specific states.
- Memory Type Taxonomy:
  - `axiom`: Permanent, immutable rules, boundary invariants, and fundamental principles.
  - `fact`: Verifiable project states, dependencies, and established technical decisions.
  - `insight`: Synthesized lessons learned, deductions, and architectural breakthroughs.
  - `preference`: User directives, coding tastes, communication style, and workflow preferences.
- Exclusion Criteria (Signal over Noise):
  - Do NOT extract transient engineering steps, ephemeral file inspections, or resolved errors.
  - Extract only high-density, durable invariants that should survive session resets.
- Exclusion & Sanitization Directives:
  - NEVER extract or store passwords, API keys, session tokens, or private credentials.
  - If a secret is observed in the transcript, extract only the architectural role
    (e.g. "Uses AWS S3 with IAM authentication") and omit the credential string entirely."""


def build_dreaming_prompt(log_content: str) -> str:
    """Builds a standardized, sanitized session dreaming extraction prompt."""
    return f"""Analyze the following session chat log and extract durable long-term memories
that should be consolidated across sessions.

Memory Extraction Principles & Scoping Rules:
{DREAMING_EXTRACTION_PRINCIPLES}

Chat Log:
{log_content}

Your Output MUST be a raw JSON object matching this schema:
{Dream.model_json_schema()}

Do not include markdown wrapper blocks (such as ```json) or any conversational text. Return only the JSON object.
"""


def perform_sleep_dreaming(
    log_content: str,
    active_id: str,
    session_id: str | None = None,
    model: str = 'gemini-3.1-pro-preview',
    ctx: Any = None,
    commit_payload: str | dict | list[str] | None = None,
) -> int:
    """
    Dehydrate a session log by parsing it to extract memories.
    Returns the number of extracted memories.
    """
    persona_dir = get_persona_path(active_id)
    memory_manager = MemoryManager(base_dir=persona_dir)

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
        prompt = build_dreaming_prompt(log_content)

        def build_delegation_instructions() -> str:
            return format_delegation_prompt(
                title='Session Epilogue & Memory Extraction Request',
                task_instructions=(
                    'Analyze the session chat log and extract durable long-term memories, '
                    'categorizing each by type, scope, and tags.'
                ),
                input_sections=[
                    ('Memory Extraction Principles & Scoping Rules', DREAMING_EXTRACTION_PRINCIPLES),
                    ('Chat Log to Process', log_content),
                ],
                schema=Dream,
                primary_commit_cmd="tur sleep --commit '<JSON_PAYLOAD>'",
                secondary_commit_cmd="tur learn --json '<JSON_PAYLOAD>'",
            )

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
    prompt = build_dreaming_prompt(log_content)

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
