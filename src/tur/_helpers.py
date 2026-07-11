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
