import importlib
import re
import sys

import pytest
from typer.testing import CliRunner


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from styled terminal output."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def test_admin_cli_missing_textual(monkeypatch, capsys):
    # Hide textual from sys.modules
    monkeypatch.setitem(sys.modules, 'textual', None)

    # We must remove tur modules from sys.modules if they were already imported
    # so they execute again in this import test
    admin_module_key = 'tur.cli.admin'
    tui_module_key = 'tur.tui'

    old_admin = sys.modules.get(admin_module_key)
    old_tui = sys.modules.get(tui_module_key)

    if admin_module_key in sys.modules:
        del sys.modules[admin_module_key]
    if tui_module_key in sys.modules:
        del sys.modules[tui_module_key]

    try:
        with pytest.raises(SystemExit) as exc_info:
            importlib.import_module('tur.cli.admin')

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        plain_err = strip_ansi(captured.err)
        assert "Error: The 'textual' package is required to run 'tur-adm'." in plain_err
        assert 'pip install tur[admin]' in plain_err
    finally:
        # Restore sys.modules to avoid breaking subsequent tests
        if old_admin is not None:
            sys.modules[admin_module_key] = old_admin
        if old_tui is not None:
            sys.modules[tui_module_key] = old_tui


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
