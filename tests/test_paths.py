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
