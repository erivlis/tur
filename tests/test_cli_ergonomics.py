import importlib
import re
import sys

import pytest
from typer.testing import CliRunner


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from styled terminal output."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def test_admin_cli_loads_without_textual(monkeypatch):
    """Asserts that tur.cli.admin has zero dependency on textual and imports cleanly."""
    monkeypatch.setitem(sys.modules, 'textual', None)
    import tur.cli.admin

    assert hasattr(tur.cli.admin, 'app')


def test_mcp_cli_missing_mcp(monkeypatch):
    # Hide mcp and tur.mcp_server from sys.modules
    monkeypatch.setitem(sys.modules, 'mcp', None)
    monkeypatch.setitem(sys.modules, 'tur.mcp_server', None)

    # Import the app inside the test
    from tur.cli.mcp import app as mcp_app

    runner = CliRunner()
    result = runner.invoke(mcp_app, [])

    assert result.exit_code == 1

    plain_out = strip_ansi(result.output)
    assert "Error: The 'mcp' package is required to run the Tur MCP server." in plain_out
    assert 'pip install tur[mcp]' in plain_out


def test_dreaming_missing_google_genai(monkeypatch):
    monkeypatch.setitem(sys.modules, 'google', None)
    monkeypatch.setitem(sys.modules, 'google.genai', None)
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')

    from tur import dreaming

    with pytest.raises(ImportError) as exc_info:
        dreaming.stage_sleep_dreaming('Test log content', active_id='fake-id')

    assert "The 'google-genai' package is required for direct Gemini API calls." in str(exc_info.value)
    assert 'tur[gemini]' in str(exc_info.value)


def test_helpers_missing_google_genai(monkeypatch):
    monkeypatch.setitem(sys.modules, 'google', None)
    monkeypatch.setitem(sys.modules, 'google.genai', None)

    from tur._helpers import _local_gemini_generate

    with pytest.raises(ImportError) as exc_info:
        _local_gemini_generate('Test prompt', api_key='test-key')

    assert "The 'google-genai' package is required for direct Gemini API calls." in str(exc_info.value)
    assert 'tur[gemini]' in str(exc_info.value)
