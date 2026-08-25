import os
import tempfile
from pathlib import Path

import pytest

from tur import paths


def test_is_global_path(tmp_path, monkeypatch):
    # Mock Path.home() to point to tmp_path
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Path inside home/.tur
    global_p = tmp_path / '.tur' / 'personas'
    assert paths.is_global_path(global_p) is True

    # Path inside resolved runtime/cache/log dir
    assert paths.is_global_path(paths.resolve_runtime_dir() / 'ipc.sock') is True
    assert paths.is_global_path(paths.resolve_cache_dir() / 'graph.idx') is True
    assert paths.is_global_path(paths.resolve_log_dir() / 'session.log') is True

    # Path outside global stores
    local_p = tmp_path / 'workspace' / 'my_project'
    assert paths.is_global_path(local_p) is False


def test_resolve_personas_base_dir_global(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Create fake global personas.yaml
    global_dir = tmp_path / '.tur'
    global_dir.mkdir()
    (global_dir / 'personas.yaml').write_text('personas: []', encoding='utf-8')

    assert paths.resolve_personas_base_dir() == global_dir


def test_resolve_runtime_dir_env_override(tmp_path, monkeypatch):
    custom_runtime = tmp_path / 'custom_runtime'
    monkeypatch.setenv('TUR_RUNTIME_DIR', str(custom_runtime))

    resolved = paths.resolve_runtime_dir()
    assert resolved == custom_runtime.resolve()
    assert resolved.exists()


def test_resolve_cache_dir_env_override(tmp_path, monkeypatch):
    custom_cache = tmp_path / 'custom_cache'
    monkeypatch.setenv('TUR_CACHE_DIR', str(custom_cache))

    resolved = paths.resolve_cache_dir()
    assert resolved == custom_cache.resolve()
    assert resolved.exists()


def test_resolve_log_dir_env_override(tmp_path, monkeypatch):
    custom_log = tmp_path / 'custom_log'
    monkeypatch.setenv('TUR_LOG_DIR', str(custom_log))

    resolved = paths.resolve_log_dir()
    assert resolved == custom_log.resolve()
    assert resolved.exists()


def test_resolve_data_dir_env_override(tmp_path, monkeypatch):
    custom_data = tmp_path / 'custom_data'
    monkeypatch.setenv('TUR_HOME', str(custom_data))

    resolved = paths.resolve_data_dir()
    assert resolved == custom_data.resolve()


def test_resolve_runtime_dir_container_fallback(monkeypatch):
    # Simulate an unwritable /run/user/1000 runtime directory (as in minimal Docker/CI)
    class FakePlatformDirs:
        @property
        def user_runtime_path(self):
            raise PermissionError(13, "Permission denied: '/run/user/1000'")

    monkeypatch.setattr(paths, '_PLATFORM_DIRS', FakePlatformDirs())
    monkeypatch.delenv('TUR_RUNTIME_DIR', raising=False)

    resolved = paths.resolve_runtime_dir()
    uid = os.getuid() if hasattr(os, 'getuid') else 'win'
    expected_fallback = Path(tempfile.gettempdir()) / f'tur-runtime-{uid}'
    assert resolved == expected_fallback.resolve()
    assert resolved.exists()


def test_resolve_data_dir_tur_data_dir_env(tmp_path, monkeypatch):
    custom_data = tmp_path / 'custom_data_dir'
    monkeypatch.delenv('TUR_HOME', raising=False)
    monkeypatch.setenv('TUR_DATA_DIR', str(custom_data))

    resolved = paths.resolve_data_dir()
    assert resolved == custom_data.resolve()


def test_resolve_data_dir_default_home(tmp_path, monkeypatch):
    # When TUR_HOME/TUR_DATA_DIR are unset, defaults to Path.home() / '.tur'
    monkeypatch.delenv('TUR_HOME', raising=False)
    monkeypatch.delenv('TUR_DATA_DIR', raising=False)
    monkeypatch.setattr(Path, 'home', lambda: tmp_path / 'empty_home')

    resolved = paths.resolve_data_dir()
    assert resolved == (tmp_path / 'empty_home' / '.tur').resolve()


def test_resolve_workspace_dir_env_override(tmp_path, monkeypatch):
    ws_dir = tmp_path / 'my_workspace'
    ws_dir.mkdir()
    monkeypatch.setenv('TUR_PROJECT_DIR', str(ws_dir))

    assert paths.resolve_workspace_dir() == ws_dir.resolve()


def test_resolve_workspace_dir_mcp_roots(tmp_path, monkeypatch):
    monkeypatch.delenv('TUR_PROJECT_DIR', raising=False)
    ws_dir = tmp_path / 'mcp_workspace'
    ws_dir.mkdir()

    class FakeRoot:
        def __init__(self, uri):
            self.uri = uri

    class FakeContext:
        def __init__(self, roots):
            self.roots = roots

    ctx = FakeContext(roots=[FakeRoot(uri=ws_dir.as_uri())])
    assert paths.resolve_workspace_dir(ctx) == ws_dir.resolve()


def test_resolve_workspace_dir_cwd_and_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv('TUR_PROJECT_DIR', raising=False)

    # 1. CWD with .tur directory
    tur_ws = tmp_path / 'project_with_tur'
    tur_ws.mkdir()
    (tur_ws / '.tur').mkdir()
    monkeypatch.chdir(tur_ws)
    assert paths.resolve_workspace_dir() == tur_ws.resolve()

    # 2. CWD without .tur directory -> Pure Traveler fallback (None)
    plain_dir = tmp_path / 'plain_dir'
    plain_dir.mkdir()
    monkeypatch.chdir(plain_dir)
    assert paths.resolve_workspace_dir() is None


def test_resolve_personas_base_dir_workspace(tmp_path, monkeypatch):
    monkeypatch.delenv('TUR_HOME', raising=False)
    monkeypatch.delenv('TUR_DATA_DIR', raising=False)
    monkeypatch.setattr(Path, 'home', lambda: tmp_path / 'empty_home')

    # Workspace containing .tur/personas.yaml
    ws_dir = tmp_path / 'ws_persona'
    ws_dir.mkdir()
    tur_dir = ws_dir / '.tur'
    tur_dir.mkdir()
    (tur_dir / 'personas.yaml').write_text('personas: []', encoding='utf-8')
    monkeypatch.setenv('TUR_PROJECT_DIR', str(ws_dir))

    assert paths.resolve_personas_base_dir() == tur_dir.resolve()
