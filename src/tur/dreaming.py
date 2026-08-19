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
) -> int:
    """
    Dehydrate a session log by parsing it to extract memories.
    Returns the number of extracted memories.
    """
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

    Your Output MUST be a raw JSON object matching this schema:
    {Dream.model_json_schema()}

    Do not include markdown wrapper blocks (such as ```json) or any conversational text. Return only the JSON object.
    """

    def build_delegation_instructions() -> str:
        from datetime import datetime, timezone
        current_time = datetime.now(UTC).isoformat()
        persona_uuid = persona_dir.name

        return f"""# TUR DELEGATION: Session Epilogue & Memory Extraction Request (EP-0121)

No local `GEMINI_API_KEY` or `TUR_LLM_API_KEY` was found in the environment.
Since you (the Harness) are an autonomous agent with file-writing tools,
you must execute the memory extraction yourself.

Please parse the chat log below and extract key insights, facts, or axioms into individual OKF memory files.

## 1. Chat Log to Process:
{log_content}

## 2. Allowed Memory Types & Scopes:
- Memory Types: fact, preference, insight, axiom, event
- Memory Scopes: universal, user, persona, incarnation

## 3. OKF Memory File Schema:
For each extracted memory, write a file named:
`.tur/personas/{persona_uuid}/memories/active/<timestamp>_<type>_<short_hash>.md`

The file MUST use this exact format (YAML frontmatter + body):
---
type: L1 Memory
timestamp: {current_time}
memory_type: <One of the Allowed Memory Types>
scope: <One of the Allowed Memory Scopes>
tags:
  - dreaming
source_session: {session_id or 'unknown'}
---

<Content of the memory>

Please perform these file modifications directly. Once done, print a completion message.
"""

    from tur._helpers import require_inference
    resp_text = require_inference(
        prompt=prompt,
        ctx=ctx,
        task_description="session dreaming extraction",
        delegation_instructions_builder=build_delegation_instructions,
        model=model,
        response_schema=Dream.model_json_schema(),
    )

    import json

    resp_text = _clean_json_response(resp_text)
    dream_data = json.loads(resp_text)
    extracted_memories = dream_data.get('memories', [])

    count = 0
    for mem_data in extracted_memories:
        memory = Memory(
            type=mem_data['type'],
            scope=mem_data['scope'],
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
