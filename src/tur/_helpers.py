import os
from typing import Any

import yaml
from yaml import SafeLoader

SAFE_LOADER: type[SafeLoader] = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def yaml_safe_load(stream: Any) -> Any:
    """
    Optimized YAML safe loader that uses CSafeLoader if available,
    falling back to standard SafeLoader.
    """
    return yaml.load(stream, Loader=SAFE_LOADER)


def run_async(coro: Any) -> Any:
    """
    Runs a coroutine synchronously. Supports running from worker threads
    when an event loop is already active in the main thread.
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # Running inside an active event loop from a worker thread
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        # No loop running, run it synchronously
        return asyncio.run(coro)


async def _mcp_sample(ctx: Any, prompt: str, system_prompt: str | None = None) -> str:
    """Helper to request sampling from the MCP client's LLM."""
    result = await ctx.sample(messages=prompt, system_prompt=system_prompt)
    if hasattr(result, 'text') and result.text:
        return result.text
    if hasattr(result, 'content'):
        if isinstance(result.content, str):
            return result.content
        if isinstance(result.content, list):
            texts = []
            for item in result.content:
                if hasattr(item, 'text') and item.text:
                    texts.append(item.text)
                elif hasattr(item, 'value') and item.value:
                    texts.append(item.value)
                elif isinstance(item, dict):
                    texts.append(item.get('text', item.get('value', '')))
                else:
                    texts.append(str(item))
            return ''.join(texts)
    return str(result)


def _clean_json_response(resp_text: str) -> str:
    """Strips markdown fences from LLM JSON response if present."""
    resp_text = resp_text.strip()
    if resp_text.startswith('```'):
        lines = resp_text.splitlines()
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        resp_text = '\n'.join(lines).strip()
    return resp_text


def _parse_json_or_ndjson(text: str) -> list[dict]:
    """Parses text containing full JSON or Newline-Delimited JSON (NDJSON)."""
    import json

    cleaned = _clean_json_response(text)
    if not cleaned:
        return []

    try:
        data = json.loads(cleaned)
    except Exception:
        pass
    else:
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [elem for elem in data if isinstance(elem, dict)]

    results: list[dict] = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            line_data = json.loads(line)
        except Exception:
            continue
        if isinstance(line_data, dict):
            results.append(line_data)
        elif isinstance(line_data, list):
            results.extend([elem for elem in line_data if isinstance(elem, dict)])

    if not results:
        raise ValueError(f'Failed to parse payload as JSON, NDJSON, or file path: {text[:100]}...')
    return results


def _load_file_or_glob(item_str: str) -> list[dict]:
    """Attempts to resolve item_str as a glob pattern or file path."""
    import glob
    from pathlib import Path

    results: list[dict] = []
    matched_files = glob.glob(item_str)
    if matched_files:
        for file_p in matched_files:
            try:
                p_obj = Path(file_p)
                if p_obj.is_file():
                    results.extend(_parse_json_or_ndjson(p_obj.read_text(encoding='utf-8')))
            except Exception:
                pass
        return results

    p = Path(item_str)
    if p.exists() and p.is_file():
        try:
            return _parse_json_or_ndjson(p.read_text(encoding='utf-8'))
        except Exception:
            pass

    return _parse_json_or_ndjson(item_str)


def parse_multi_json_payloads(payload: Any) -> list[dict]:
    """
    Parses single or multi-part JSON payloads into a list of dictionaries.
    Supports:
      - dict or list of dicts
      - Single JSON string (dict or list)
      - Multiple JSON strings / multiple items in a list/tuple
      - NDJSON (newline-delimited JSON)
      - File paths and glob patterns (e.g. 'chunks/*.json', 'result.json')
    """
    if payload is None:
        return []
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, (list, tuple)):
        combined: list[dict] = []
        for sub in payload:
            combined.extend(parse_multi_json_payloads(sub))
        return combined
    if isinstance(payload, str):
        item_str = payload.strip()
        if not item_str:
            return []
        return _load_file_or_glob(item_str)
    return []


def format_delegation_prompt(
    title: str,
    task_instructions: str,
    input_sections: list[tuple[str, str]],
    schema: Any,
    primary_commit_cmd: str,
    secondary_commit_cmd: str | None = None,
) -> str:
    """
    Constructs a standardized, unified delegation prompt for external autonomous agent harnesses.
    Prompt design rules:
      - Strips internal metadata and API-key diagnostic messages.
      - Enforces strict boundary invariants (no manual writes inside .tur/).
      - Unifies multi-batch, NDJSON, and glob commit syntax into an integrated contract.
    """
    import json

    from pydantic import BaseModel

    if (isinstance(schema, type) and issubclass(schema, BaseModel)) or hasattr(schema, 'model_json_schema'):
        schema_dict = schema.model_json_schema()
    elif isinstance(schema, dict):
        schema_dict = schema
    else:
        schema_dict = {}

    schema_json = json.dumps(schema_dict, indent=2)

    lines = [
        f'# TUR DELEGATION: {title}',
        '',
        task_instructions.strip(),
        '',
        '## 1. Input Data',
    ]

    for sec_title, sec_content in input_sections:
        lines.append(f'### {sec_title}')
        lines.append(sec_content.strip())
        lines.append('')

    lines.extend(
        [
            '## 2. Target JSON Schema',
            '```json',
            schema_json,
            '```',
            '',
            '## 3. Execution & Commit Contract',
            '- Boundary Invariant: Under NO circumstances should you create or edit files directly inside `.tur/`. '
            'Compute and output a pure structured JSON payload conforming to the schema above.',
            '- Subagent Execution (Recommended): If your harness supports subagents, delegate this synthesis '
            'to an isolated subagent for clean, unpolluted deduction without context noise.',
            f'- Single Commit: `{primary_commit_cmd}`',
            '- Multi-Batch & Large Payload Ingestion (for large inputs):',
            '  - Multiple flags: Pass multiple `--commit <chunk>` options to the CLI command.',
            "  - File glob / path: Save chunks to a directory and pass pattern (e.g., `--commit 'chunks/*.json'`).",
            '  - Streaming: Emit Newline-Delimited JSON (NDJSON) or a JSON array of objects.',
        ]
    )

    if secondary_commit_cmd:
        lines.append(f'- Alternative Commit: `{secondary_commit_cmd}`')

    lines.append('')
    return '\n'.join(lines)


def _local_gemini_generate(
    prompt: str,
    api_key: str,
    model: str = 'gemini-3.1-pro-preview',
    response_schema: Any | None = None,
) -> str:
    """Helper to execute local Gemini SDK content generation."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError(
            "The 'google-genai' package is required for direct Gemini API calls. "
            "Install it with: pip install 'tur[gemini]' or uv add 'tur[gemini]'"
        ) from e

    client = genai.Client(api_key=api_key)
    config = None
    if response_schema is not None:
        config = types.GenerateContentConfig(
            response_mime_type='application/json',
            response_json_schema=response_schema,
        )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    resp_text = response.text
    if not resp_text:
        raise ValueError('LLM generation returned empty response')
    return resp_text


def require_inference(
    prompt: str,
    ctx: Any | None,
    task_description: str,
    delegation_instructions_builder: Any | None = None,
    model: str = 'gemini-3.1-pro-preview',
    response_schema: Any | None = None,
) -> str:
    """
    Request LLM inference via the dual-mode Agnostic Harness Interaction Protocol.

    If `ctx` (MCP context) is available, issues a Sampling request to the connected Harness.
    If `ctx` is None and no API key is present, raises HarnessDelegationError with delegation prompt.
    If an API key is present, executes local provider generation.
    """
    from tur.models import HarnessDelegationError

    if ctx is not None:
        async def do_sampling():
            return await _mcp_sample(ctx, prompt)

        resp_text = run_async(do_sampling())
        return _clean_json_response(resp_text)

    api_key = os.environ.get('TUR_LLM_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        if delegation_instructions_builder is not None:
            instructions = delegation_instructions_builder()
            raise HarnessDelegationError(instructions)
        raise ValueError(
            f"Inference required for '{task_description}' but neither MCP context "
            "nor TUR_LLM_API_KEY / GEMINI_API_KEY environment variable was provided."
        )

    raw_resp = _local_gemini_generate(
        prompt=prompt,
        api_key=api_key,
        model=model,
        response_schema=response_schema,
    )
    return _clean_json_response(raw_resp)


