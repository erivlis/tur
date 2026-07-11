import os
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

    if ctx is not None:

        async def do_sampling():
            return await _mcp_sample(ctx, prompt)

        resp_text = run_async(do_sampling())
    else:
        # Configure Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY environment variable not set.')

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_json_schema=Dream.model_json_schema(),
            ),
        )
        resp_text = response.text
        if not resp_text:
            raise ValueError('Dream generation returned empty response')

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
    else:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return '[]'

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_json_schema=Dream.model_json_schema(),
            ),
        )
        resp_text = response.text
        if not resp_text:
            raise ValueError('Dream response was empty')

    return _clean_json_response(resp_text)
