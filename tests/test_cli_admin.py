import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from typer.testing import CliRunner

from tur import persona, session, tui, user
from tur.cli.admin import app as admin_app

runner = CliRunner()


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    # Setup directories
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    # Fake user profile
    user_data = {
        'name': 'Test Architect',
        'role': 'Architect',
        'domain_expertise': ['Software Engineering'],
        'core_values': ['Determinism'],
    }
    with open(dot_tur / 'user.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(user_data, f)

    # Fake persona index
    persona_id_1 = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    persona_id_2 = 'fab6858c-e4ad-4adf-9e2d-0c86455917cf'

    index_data = {
        'personas': [
            {'id': persona_id_1, 'name': 'Ariel', 'version': '5.4.0'},
            {'id': persona_id_2, 'name': 'Umbriel', 'version': '1.0.0'},
        ]
    }
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    # Create directories for personas
    (personas_dir / persona_id_1 / 'memories' / 'archive').mkdir(parents=True)
    (personas_dir / persona_id_2 / 'memories' / 'archive').mkdir(parents=True)

    # Fake persona yaml files
    persona_1_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [
            {
                'name': 'Symmetry',
                'avatar': 'Noether',
                'role': 'Guardian of Invariance',
                'constraints': ['Keep state timeline symmetric.'],
                'weight': 1.5,
            }
        ],
    }
    with open(personas_dir / persona_id_1 / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_1_yaml, f)

    persona_2_yaml = {
        'name': 'Umbriel',
        'version': '1.0.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To discover truth.',
        'principles': [],
    }
    with open(personas_dir / persona_id_2 / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_2_yaml, f)

    # Fake state file
    state_data = {'active_persona_id': persona_id_1}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    # Change to fake workspace root
    monkeypatch.chdir(tmp_path)
    # Mock Path.home() so global directories also route to temp folder
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    # Mock human check by forcing sys.stdout.isatty to True via a dynamic SysProxy inside the common module
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

    return tmp_path, persona_id_1, persona_id_2


def test_admin_help(mock_workspace):
    result = runner.invoke(admin_app, ['--help'])
    assert result.exit_code == 0
    assert 'Administrative Governance Suite' in result.stdout


def test_admin_golem_protocol_violation(mock_workspace, monkeypatch):
    # Force isatty to False to simulate headless execution by agent
    class FalseStdoutProxy:
        def __getattr__(self, attr):
            if attr == 'isatty':
                return lambda: False
            return getattr(sys.stdout, attr)

    class FalseSysProxy:
        def __getattr__(self, name):
            if name == 'stdout':
                return FalseStdoutProxy()
            return getattr(sys, name)

    import tur.cli.common

    monkeypatch.setattr(tur.cli.common, 'sys', FalseSysProxy())

    # Try calling persona list
    result = runner.invoke(admin_app, ['persona', 'list'])
    assert result.exit_code == 1
    assert 'GOLEM PROTOCOL VIOLATION' in result.stdout


def test_admin_persona_list(mock_workspace):
    result = runner.invoke(admin_app, ['persona', 'list'])
    assert result.exit_code == 0
    assert 'Persona Registry' in result.stdout
    assert 'Ariel' in result.stdout
    assert 'Umbriel' in result.stdout


def test_admin_persona_view(mock_workspace):
    result = runner.invoke(admin_app, ['persona', 'view', 'Ariel'])
    assert result.exit_code == 0
    assert 'Persona DNA' in result.stdout
    assert 'Ariel' in result.stdout
    assert '5.4.0' in result.stdout


def test_admin_persona_init_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock()
    monkeypatch.setattr(tui, 'init_wizard', mock_wizard)

    result = runner.invoke(admin_app, ['persona', 'init'])
    assert result.exit_code == 0
    mock_wizard.assert_called_once()


def test_admin_persona_switch_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value='fab6858c-e4ad-4adf-9e2d-0c86455917cf')
    monkeypatch.setattr(tui, 'select_persona_wizard', mock_wizard)

    result = runner.invoke(admin_app, ['persona', 'switch'])
    assert result.exit_code == 0
    assert 'Default persona switched to:' in result.stdout


def test_admin_persona_switch_cancelled(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value=None)
    monkeypatch.setattr(tui, 'select_persona_wizard', mock_wizard)

    result = runner.invoke(admin_app, ['persona', 'switch'])
    assert result.exit_code == 0
    assert 'Switch cancelled.' in result.stdout


def test_admin_persona_switch_error(mock_workspace, monkeypatch):
    def raise_err(*args, **kwargs):
        raise RuntimeError('TUI error')

    monkeypatch.setattr(tui, 'select_persona_wizard', raise_err)

    result = runner.invoke(admin_app, ['persona', 'switch'])
    assert result.exit_code == 1
    assert 'Error switching persona' in result.stdout


def test_admin_persona_switch_missing_personas_yaml(mock_workspace):
    Path('.tur/personas.yaml').unlink()
    result = runner.invoke(admin_app, ['persona', 'switch'])
    assert result.exit_code == 1
    assert 'No registered personas found.' in result.stdout or 'No personas found.' in result.stdout


def test_admin_persona_switch_empty_personas(mock_workspace):
    with open('.tur/personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'personas': []}, f)
    result = runner.invoke(admin_app, ['persona', 'switch'])
    assert result.exit_code == 1
    assert 'No personas available to select.' in result.stdout


def test_admin_persona_export_and_import(mock_workspace, tmp_path):
    _ = mock_workspace
    archive_path = Path('ariel.tur')
    result_export = runner.invoke(admin_app, ['persona', 'export', 'Ariel', str(archive_path)])
    assert result_export.exit_code == 0
    assert 'successfully exported' in result_export.stdout
    assert archive_path.exists()

    result_import = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result_import.exit_code == 0
    assert 'successfully imported' in result_import.stdout

    # Import registers in the global registry (~/.tur/ → fake_home/.tur/ in tests).
    fake_home = Path.home()
    global_index_path = fake_home / '.tur' / 'personas.yaml'
    assert global_index_path.exists()
    with open(global_index_path, encoding='utf-8') as f:
        global_index = yaml.safe_load(f)
    assert any(p['name'] == 'Ariel' for p in global_index['personas'])


def test_admin_persona_export_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Export failed internally')

    monkeypatch.setattr(persona, 'get_persona_path', mock_raise)

    result = runner.invoke(admin_app, ['persona', 'export', 'Ariel', 'ariel.tur'])
    assert result.exit_code == 1
    assert 'Error exporting persona: Export failed internally' in result.stdout


def test_admin_memory_list_empty(mock_workspace):
    result = runner.invoke(admin_app, ['memory', 'list'])
    assert result.exit_code == 0
    assert 'The Memory Bank for 7544202e-92f5-40ce-adfb-e4b0eae6c262 is empty.' in result.stdout


def test_admin_memory_list_with_items(mock_workspace):
    # We can inject a memory using standard agent API directly so it's in the bank
    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    persona_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memory_manager = MemoryManager(base_dir=persona_dir)
    memory = Memory(
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        tags=['manual', 'cli'],
        content='Pytest is running inside admin test.',
    )
    memory_manager.save(memory)

    result = runner.invoke(admin_app, ['memory', 'list'])
    assert result.exit_code == 0
    assert 'Memory Bank (7544202e-92f5-40ce-adfb-e4b0eae6c262)' in result.stdout
    assert 'Pytest is running inside admin test.' in result.stdout


def test_admin_memory_forget(mock_workspace):
    # Store memory
    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    persona_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memory_manager = MemoryManager(base_dir=persona_dir)
    memory = Memory(
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        tags=['manual'],
        content='Manual memory to be forgotten.',
    )
    memory_manager.save(memory)

    active_mems = session.hydrate_session_state('7544202e-92f5-40ce-adfb-e4b0eae6c262').memories
    assert len(active_mems) == 1
    mem_id = str(active_mems[0].id)

    # Forget it
    result_forget = runner.invoke(admin_app, ['memory', 'forget', mem_id])
    assert result_forget.exit_code == 0
    assert f'Memory {mem_id}' in result_forget.stdout
    assert 'forgotten' in result_forget.stdout

    # Verify it is no longer in active list
    active_mems_after = session.hydrate_session_state('7544202e-92f5-40ce-adfb-e4b0eae6c262').memories
    assert len(active_mems_after) == 0


def test_admin_memory_view(mock_workspace):
    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    persona_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memory_manager = MemoryManager(base_dir=persona_dir)
    memory = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=['pytest'],
        content='Test view specific memory content.',
    )
    memory_manager.save(memory)

    active_mems = session.hydrate_session_state('7544202e-92f5-40ce-adfb-e4b0eae6c262').memories
    mem_id = str(active_mems[0].id)

    result = runner.invoke(admin_app, ['memory', 'view', mem_id])
    assert result.exit_code == 0
    assert 'Memory Detail' in result.stdout
    assert 'Test view specific memory content.' in result.stdout


def test_admin_memory_list_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Memories list failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(admin_app, ['memory', 'list'])
    assert result.exit_code == 1
    assert 'Error listing memories: Memories list failed' in result.stdout


def test_admin_memory_forget_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Forget failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(admin_app, ['memory', 'forget', 'some-memory-id'])
    assert result.exit_code == 1
    assert 'Error: Forget failed' in result.stdout


def test_admin_session_lifecycle(mock_workspace):
    # 1. Start a session
    result_start = runner.invoke(admin_app, ['session', 'start', 'session-foo'])
    assert result_start.exit_code == 0
    assert "Session 'session-foo' started" in result_start.stdout

    notes_yaml = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/sessions/session-foo.yaml')
    assert notes_yaml.exists()

    # 2. List sessions
    result_list = runner.invoke(admin_app, ['session', 'list'])
    assert result_list.exit_code == 0
    assert 'Session Index' in result_list.stdout
    assert 'session-foo' in result_list.stdout

    # 3. Add a note (simulate through standard session logic, as note command is agent-facing)
    session.note_logic(
        'Note content inside session lifecycle test',
        session_id='session-foo',
        identifier='7544202e-92f5-40ce-adfb-e4b0eae6c262',
    )

    # 4. Read note via admin note command
    result_note_view = runner.invoke(admin_app, ['session', 'note', '2', '--session-id', 'session-foo'])
    assert result_note_view.exit_code == 0
    assert 'Note #2' in result_note_view.stdout
    assert 'Note content inside session lifecycle test' in result_note_view.stdout

    # 5. End the session
    result_end = runner.invoke(admin_app, ['session', 'end', 'session-foo'])
    assert result_end.exit_code == 0
    assert "Session 'session-foo' ended" in result_end.stdout


def test_admin_session_start_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Start failed')

    monkeypatch.setattr(session, 'start_session_logic', mock_raise)

    result = runner.invoke(admin_app, ['session', 'start', 'err-sess'])
    assert result.exit_code == 1
    assert 'Error starting session: Start failed' in result.stdout


def test_admin_session_end_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('End failed')

    monkeypatch.setattr(session, 'end_session_logic', mock_raise)

    result = runner.invoke(admin_app, ['session', 'end', 'err-sess'])
    assert result.exit_code == 1
    assert 'Error ending session: End failed' in result.stdout


def test_admin_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur-admin', '--help'])

    import runpy

    with pytest.raises(SystemExit) as exc:
        runpy.run_module('tur.cli.admin', run_name='__main__')

    assert exc.value.code == 0
