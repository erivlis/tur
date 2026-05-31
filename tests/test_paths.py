import pytest
from pathlib import Path
from tur import paths


def test_is_global_path(tmp_path, monkeypatch):
    # Mock Path.home() to point to tmp_path
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Path inside home/.tur
    global_p = tmp_path / '.tur' / 'personas'
    assert paths.is_global_path(global_p) is True

    # Path outside home/.tur
    local_p = tmp_path / 'other'
    assert paths.is_global_path(local_p) is False


def test_resolve_personas_base_dir_global(tmp_path, monkeypatch):
    # Mock Path.home() to point to tmp_path
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Create fake global personas.yaml
    global_dir = tmp_path / '.tur'
    global_dir.mkdir()
    (global_dir / 'personas.yaml').write_text('personas: []', encoding='utf-8')

    assert paths.resolve_personas_base_dir() == global_dir
