import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_tur_env(tmp_path_factory, monkeypatch):
    """
    Global Test Suite Sandboxing.
    Isolates Path.home() to a temporary sandbox home so that tests never modify
    the real user ~/.tur directory or bleed into real state.
    """
    fake_home = tmp_path_factory.mktemp('tur_home')
    monkeypatch.setattr(Path, 'home', lambda: fake_home)
    monkeypatch.delenv('TUR_HOME', raising=False)
    monkeypatch.delenv('TUR_PROJECT_DIR', raising=False)
    monkeypatch.setenv('PYTEST_CURRENT_TEST', '1')

    # Mock human check in tur.cli.common for test runner invocations
    class StdoutProxy:
        def __getattr__(self, attr):
            if attr == 'isatty':
                return lambda: True
            return getattr(sys.stdout, attr)

    class SysProxy:
        def __getattr__(self, name):
            if name == 'stdout':
                return StdoutProxy()
            return getattr(sys, name)

    import tur.cli.common

    monkeypatch.setattr(tur.cli.common, 'sys', SysProxy())

    return fake_home
