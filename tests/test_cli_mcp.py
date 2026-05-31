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

    result = runner.invoke(mcp_app, ['--transport', 'stdio'])
    assert result.exit_code == 0
    assert 'Starting Tur MCP server' in result.stdout
    mock_mcp_main.assert_called_once_with(transport='stdio', port=8000)


def test_mcp_serve_error(mock_workspace, monkeypatch):
    from tur import mcp_server

    def raise_err(*args, **kwargs):
        raise RuntimeError('Failure launching server')

    monkeypatch.setattr(mcp_server, 'main', raise_err)

    result = runner.invoke(mcp_app, ['--transport', 'stdio'])
    assert result.exit_code == 1
    assert 'Error starting server: Failure launching server' in result.stdout


def test_mcp_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur-mcp', '--help'])

    import runpy

    with pytest.raises(SystemExit) as exc:
        runpy.run_module('tur.cli.mcp', run_name='__main__')

    assert exc.value.code == 0


@pytest.fixture(scope='module')
def sse_server():
    """Fixture to start and stop the Tur MCP server for SSE transport testing."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    command = ['uv', 'run', 'python', '-m', 'tur.cli.mcp', '--transport', 'sse', '--port', str(port)]

    env = os.environ.copy()
    # Ensure any active persona state can be found if needed by the server
    try:
        from pathlib import Path

        import yaml

        state_path = Path('.tur/state.yaml')
        if state_path.exists():
            with open(state_path, encoding='utf-8') as f:
                state_data = yaml.safe_load(f)
            active_id = state_data.get('active_persona_id')
            if active_id:
                env['TUR_ACTIVE_PERSONA_ID'] = active_id
    except Exception:
        pass

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

    try:
        captured = []
        # Wait up to 10 seconds for Uvicorn's startup message
        start_time = time.time()
        ready = False
        while time.time() - start_time < 10:
            if process.poll() is not None:
                remaining, _ = process.communicate(timeout=1)
                captured.append(remaining)
                raise RuntimeError('Server process failed to start:\n' + ''.join(captured))

            # Non-blocking read (or brief block)
            try:
                line = process.stdout.readline()
                if line:
                    captured.append(line)
                    if 'Uvicorn running on' in line or 'Uvicorn running' in line:
                        ready = True
                        break
            except Exception:
                pass
            time.sleep(0.1)

        if not ready:
            raise RuntimeError('Server process exited or failed to signal readiness:\n' + ''.join(captured))

        yield f'http://127.0.0.1:{port}'

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_sse_server_responds(sse_server):
    """Tests if the SSE server starts and responds to a GET request on the /sse endpoint."""
    try:
        response = requests.get(f'{sse_server}/sse', stream=True, timeout=3)
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers.get('content-type', '')
    except requests.exceptions.ReadTimeout:
        # A successful timeout on stream proves the connection was held open
        pass
    except requests.exceptions.RequestException as e:
        pytest.fail(f'Failed to connect to the SSE server: {e}')
