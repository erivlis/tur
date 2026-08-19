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
    Request LLM inference via the dual-mode Agnostic Harness Interaction Protocol (EP-0121).

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


