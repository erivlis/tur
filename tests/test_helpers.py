import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tur._helpers import (
    _clean_json_response,
    _local_gemini_generate,
    _mcp_sample,
    require_inference,
    run_async,
    yaml_safe_load,
)
from tur.models import HarnessDelegationError


def test_yaml_safe_load():
    data = yaml_safe_load('key: value\nnumber: 42')
    assert data == {'key': 'value', 'number': 42}


def test_run_async_no_loop():
    async def sample_coro():
        return 123

    assert run_async(sample_coro()) == 123


def test_run_async_inside_thread_with_loop():
    import concurrent.futures

    async def main_loop():
        # In this thread there's an active loop
        async def inner_coro():
            return 'from_coro'

        def worker():
            return run_async(inner_coro())

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(worker)
            return future.result()

    res = asyncio.run(main_loop())
    assert res == 'from_coro'


@pytest.mark.asyncio
async def test_mcp_sample_text_attr():
    ctx = MagicMock()
    mock_res = MagicMock()
    mock_res.text = 'generated text'
    ctx.sample = AsyncMock(return_value=mock_res)

    res = await _mcp_sample(ctx, 'prompt')
    assert res == 'generated text'


@pytest.mark.asyncio
async def test_mcp_sample_content_str():
    ctx = MagicMock()
    mock_res = MagicMock(spec=['content'])
    mock_res.content = 'content text'
    ctx.sample = AsyncMock(return_value=mock_res)

    res = await _mcp_sample(ctx, 'prompt')
    assert res == 'content text'


@pytest.mark.asyncio
async def test_mcp_sample_content_list():
    ctx = MagicMock()
    mock_item1 = MagicMock(spec=['text'])
    mock_item1.text = 'Hello '
    mock_item2 = MagicMock(spec=['value'])
    mock_item2.value = 'World '
    mock_item3 = {'text': 'from '}
    mock_item4 = {'value': 'dict '}
    mock_item5 = 42

    mock_res = MagicMock(spec=['content'])
    mock_res.content = [mock_item1, mock_item2, mock_item3, mock_item4, mock_item5]
    ctx.sample = AsyncMock(return_value=mock_res)

    res = await _mcp_sample(ctx, 'prompt')
    assert res == 'Hello World from dict 42'


@pytest.mark.asyncio
async def test_mcp_sample_fallback():
    ctx = MagicMock()
    mock_res = 'plain string result'
    ctx.sample = AsyncMock(return_value=mock_res)

    res = await _mcp_sample(ctx, 'prompt')
    assert res == 'plain string result'


def test_clean_json_response():
    assert _clean_json_response('{"a": 1}') == '{"a": 1}'
    fenced_json = '```json\n{"a": 1}\n```'
    assert _clean_json_response(fenced_json) == '{"a": 1}'
    fenced_plain = '```\n{"a": 1}\n```'
    assert _clean_json_response(fenced_plain) == '{"a": 1}'


def test_local_gemini_generate_success():
    with patch('google.genai.Client') as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.text = '{"result": "ok"}'
        mock_client.models.generate_content.return_value = mock_resp

        res = _local_gemini_generate('prompt', 'fake_key', response_schema={'type': 'object'})
        assert res == '{"result": "ok"}'


def test_local_gemini_generate_empty_error():
    with patch('google.genai.Client') as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.text = ''
        mock_client.models.generate_content.return_value = mock_resp

        with pytest.raises(ValueError, match='empty response'):
            _local_gemini_generate('prompt', 'fake_key')


def test_local_gemini_generate_import_error():
    with (
        patch.dict(sys.modules, {'google': None, 'google.genai': None}),
        pytest.raises(ImportError, match='google-genai'),
    ):
        _local_gemini_generate('prompt', 'fake_key')


def test_require_inference_with_ctx():
    ctx = MagicMock()
    mock_res = MagicMock()
    mock_res.text = '```json\n{"test": true}\n```'
    ctx.sample = AsyncMock(return_value=mock_res)

    res = require_inference('prompt', ctx, 'test task')
    assert res == '{"test": true}'


def test_require_inference_no_ctx_no_key_with_builder():
    with patch.dict(os.environ, {}, clear=True):

        def builder():
            return 'Please do task'

        with pytest.raises(HarnessDelegationError) as exc_info:
            require_inference('prompt', None, 'test task', delegation_instructions_builder=builder)
        assert exc_info.value.prompt == 'Please do task'


def test_require_inference_no_ctx_no_key_no_builder():
    with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match='Inference required'):
        require_inference('prompt', None, 'test task')


def test_require_inference_with_api_key():
    with (
        patch.dict(os.environ, {'TUR_LLM_API_KEY': 'my_key'}),
        patch('tur._helpers._local_gemini_generate', return_value='```\n{"success": true}\n```') as mock_gen,
    ):
        res = require_inference('prompt', None, 'test task')
        assert res == '{"success": true}'
        mock_gen.assert_called_once()
