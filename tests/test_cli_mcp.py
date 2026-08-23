import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
import yaml
from typer.testing import CliRunner

from tur.cli.mcp import app as mcp_app

runner = CliRunner()


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id_1 = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    index_data = {'personas': [{'id': persona_id_1, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    (personas_dir / persona_id_1 / 'memories' / 'archive').mkdir(parents=True)

    persona_1_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
    }
    with open(personas_dir / persona_id_1 / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_1_yaml, f)

    state_data = {'active_persona_id': persona_id_1}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    return tmp_path, persona_id_1


def test_mcp_help(mock_workspace):
    result = runner.invoke(mcp_app, ['--help'])
    assert result.exit_code == 0
    assert 'Run the Tur MCP server.' in result.stdout or 'Options' in result.stdout


def test_mcp_serve_mocked(mock_workspace, monkeypatch):
    from tur import mcp_server

    mock_mcp_main = MagicMock()
    monkeypatch.setattr(mcp_server, 'main', mock_mcp_main)

    result = runner.invoke(mcp_app, [])
    assert result.exit_code == 0
    # stdout must remain completely clean for JSON-RPC transport
    assert result.stdout == ''
    mock_mcp_main.assert_called_once_with()


def test_mcp_serve_error(mock_workspace, monkeypatch):
    from tur import mcp_server

    def raise_err(*args, **kwargs):
        raise RuntimeError('Failure launching server')

    monkeypatch.setattr(mcp_server, 'main', raise_err)

    result = runner.invoke(mcp_app, [])
    assert result.exit_code == 1
    output = result.stderr if getattr(result, 'stderr', None) else result.stdout
    assert 'Error starting server: Failure launching server' in output


def test_mcp_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur-mcp', '--help'])

    from tur.cli.mcp import main

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
