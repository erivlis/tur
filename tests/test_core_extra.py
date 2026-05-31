from pathlib import Path

import pytest
import typer
import yaml

from tur import persona, user


@pytest.fixture
def mock_core_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    monkeypatch.chdir(tmp_path)

    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)
    return tmp_path


def test_user_profile_global_fallback(mock_core_workspace, monkeypatch):
    # Setup global user.yaml inside fake_home/.tur/
    global_dir = mock_core_workspace / 'fake_home' / '.tur'
    global_dir.mkdir(parents=True)

    global_user = {
        'name': 'Global Architect',
        'role': 'Developer',
        'domain_expertise': ['Testing'],
        'core_values': ['Resilience'],
    }
    with open(global_dir / 'user.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(global_user, f)

    # Delete local user.yaml if it somehow exists
    local_user = Path('.tur/user.yaml')
    if local_user.exists():
        local_user.unlink()

    prof = user.get_user_profile()
    assert prof.name == 'Global Architect'

    # Also test completely default profile when no user.yaml exists anywhere
    (global_dir / 'user.yaml').unlink()
    default_prof = user.get_user_profile()
    assert default_prof.name == 'Default User'


def test_get_active_persona_id_env(mock_core_workspace, monkeypatch):
    monkeypatch.setenv('TUR_ACTIVE_PERSONA_ID', 'env-persona-uuid')
    assert persona.get_active_persona_id() == 'env-persona-uuid'


def test_get_active_persona_id_state_none(mock_core_workspace, monkeypatch):
    # If state.yaml exists but has no active_persona_id
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': None}, f)

    # We also mock select_persona_wizard to avoid actually running TUI
    monkeypatch.setattr(persona, 'select_persona_wizard', lambda index: 'selector-uuid')

    # Make index exist
    index_path = Path('.tur/personas.yaml')
    with open(index_path, 'w', encoding='utf-8') as f:
        yaml.dump({'personas': [{'id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'name': 'Ariel', 'version': '1.0'}]}, f)

    res = persona.get_active_persona_id()
    assert res == 'selector-uuid'


def test_get_active_persona_id_no_index(mock_core_workspace):
    # Delete state.yaml and personas.yaml
    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        state_path.unlink()

    with pytest.raises(FileNotFoundError) as exc:
        persona.get_active_persona_id()
    assert 'No personas found' in str(exc.value)


def test_get_active_persona_id_empty_index(mock_core_workspace):
    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        state_path.unlink()

    index_path = Path('.tur/personas.yaml')
    with open(index_path, 'w', encoding='utf-8') as f:
        yaml.dump({'personas': []}, f)

    with pytest.raises(ValueError) as exc:
        persona.get_active_persona_id()
    assert 'No personas available' in str(exc.value)


def test_get_active_persona_id_cancel_tui(mock_core_workspace, monkeypatch):
    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        state_path.unlink()

    index_path = Path('.tur/personas.yaml')
    with open(index_path, 'w', encoding='utf-8') as f:
        yaml.dump({'personas': [{'id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'name': 'Ariel', 'version': '1.0'}]}, f)

    # Mock wizard to return None (cancel)
    monkeypatch.setattr(persona, 'select_persona_wizard', lambda index: None)

    with pytest.raises(typer.Exit):
        persona.get_active_persona_id()


def test_get_persona_path_no_index(mock_core_workspace):
    index_path = Path('.tur/personas.yaml')
    if index_path.exists():
        index_path.unlink()

    with pytest.raises(FileNotFoundError):
        persona.get_persona_path('some-uuid')
