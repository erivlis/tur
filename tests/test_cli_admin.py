import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from typer.testing import CliRunner

from tur import persona, session, tui
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
    assert 'Administrative persona management CLI' in result.stdout


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


def test_admin_persona_default(mock_workspace):
    result = runner.invoke(admin_app, ['persona', 'default', 'Ariel'])
    assert result.exit_code == 0
    assert "Default persona switched to: 'Ariel'" in result.stdout

    # Verify state.yaml was written
    state_path = Path('.tur/state.yaml')
    assert state_path.exists()
    with open(state_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    assert data['active_persona_id'] == '7544202e-92f5-40ce-adfb-e4b0eae6c262'


def test_admin_persona_switch_with_argument(mock_workspace):
    result = runner.invoke(admin_app, ['persona', 'switch', 'Umbriel'])
    assert result.exit_code == 0
    assert "Default persona switched to: 'Umbriel'" in result.stdout

    # Verify state.yaml was written
    state_path = Path('.tur/state.yaml')
    assert state_path.exists()
    with open(state_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    assert data['active_persona_id'] == 'fab6858c-e4ad-4adf-9e2d-0c86455917cf'


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
    result_export = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', str(archive_path)])
    assert result_export.exit_code == 0
    assert 'successfully exported' in result_export.stdout
    assert archive_path.exists()

    result_import = runner.invoke(admin_app, ['persona', 'import', str(archive_path), '--set-active'])
    # First import fails because it already exists
    assert result_import.exit_code == 1
    assert 'already exists' in result_import.stdout

    # Now delete from registry and try import again
    import shutil

    global_home = Path.home() / '.tur'
    dest_dir = global_home / 'personas' / '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    index_path = global_home / 'personas.yaml'
    if index_path.exists():
        with open(index_path, encoding='utf-8') as f:
            idx_data = yaml.safe_load(f) or {'personas': []}
        idx_data['personas'] = [
            p for p in idx_data['personas'] if str(p['id']) != '7544202e-92f5-40ce-adfb-e4b0eae6c262'
        ]
        with open(index_path, 'w', encoding='utf-8') as f:
            yaml.dump(idx_data, f)

    result_import = runner.invoke(admin_app, ['persona', 'import', str(archive_path), '--set-active'])
    assert result_import.exit_code == 0
    assert 'successfully imported' in result_import.stdout

    # Import registers in the global registry (~/.tur/ → fake_home/.tur/ in tests).
    fake_home = Path.home()
    global_index_path = fake_home / '.tur' / 'personas.yaml'
    assert global_index_path.exists()
    with open(global_index_path, encoding='utf-8') as f:
        global_index = yaml.safe_load(f)
    assert any(p['name'] == 'Ariel' for p in global_index['personas'])

    # Verify set-active worked
    state_path = Path('.tur/state.yaml')
    assert state_path.exists()
    with open(state_path, encoding='utf-8') as f:
        state_data = yaml.safe_load(f)
    assert state_data['active_persona_id'] == '7544202e-92f5-40ce-adfb-e4b0eae6c262'


def test_admin_persona_export_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Export failed internally')

    monkeypatch.setattr(persona, 'get_persona_path', mock_raise)

    result = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', 'ariel.tur'])
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
    assert 'Pytest is running' in result.stdout
    assert 'inside admin test.' in result.stdout


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


def test_admin_memory_approve(mock_workspace):
    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    persona_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memory_manager = MemoryManager(base_dir=persona_dir)
    core_mem = Memory(
        type=MemoryType.CORE,
        scope=MemoryScope.UNIVERSAL,
        tags=['core'],
        content='Core realization.',
        core_type='existential_alignment',
        derived_principle='Always uphold truth.',
        ethical_covenant='Never deceive the user.',
        status='pending_approval',
    )
    memory_manager.save(core_mem)
    mem_id = str(core_mem.id)

    # List with pending filter
    res_pending = runner.invoke(admin_app, ['memory', 'list', '--pending'])
    assert res_pending.exit_code == 0
    assert 'pending_approval' in res_pending.stdout
    assert mem_id[:12] in res_pending.stdout

    # Approve
    res_app = runner.invoke(admin_app, ['memory', 'approve', mem_id[:8]])
    assert res_app.exit_code == 0
    assert 'approved and activated successfully' in res_app.stdout

    # Approve again
    res_app_again = runner.invoke(admin_app, ['memory', 'approve', mem_id[:8]])
    assert res_app_again.exit_code == 0
    assert 'already active' in res_app_again.stdout

    # Nonexistent
    res_err = runner.invoke(admin_app, ['memory', 'approve', 'nonexistent_id'])
    assert res_err.exit_code == 1
    assert 'No Core memory found' in res_err.stdout


def test_admin_memory_list_pending_empty(mock_workspace):
    res_pending = runner.invoke(admin_app, ['memory', 'list', '--pending'])
    assert res_pending.exit_code == 0
    assert 'No pending memories found' in res_pending.stdout


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
    monkeypatch.setattr(sys, 'argv', ['tur-adm', '--help'])

    import runpy

    with pytest.raises(SystemExit) as exc:
        runpy.run_module('tur.cli.admin', run_name='__main__')

    assert exc.value.code == 0


def test_admin_persona_view_missing_yaml(mock_workspace):
    # Remove persona.yaml
    persona_path = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/persona.yaml')
    if persona_path.exists():
        persona_path.unlink()

    result = runner.invoke(admin_app, ['persona', 'view', 'Ariel'])
    assert result.exit_code == 0
    assert 'persona.yaml not found' in result.stdout


def test_admin_persona_import_path_traversal(mock_workspace, tmp_path):
    # Create malicious archive
    archive_path = tmp_path / 'traversal.tur'
    import tarfile

    with tarfile.open(archive_path, 'w:gz') as tar:
        info = tarfile.TarInfo(name='../../etc/passwd')
        info.size = len(b'traversal')
        import io

        tar.addfile(info, io.BytesIO(b'traversal'))

    result = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result.exit_code == 1
    assert 'Archive contains a path traversal entry' in result.stdout


def test_admin_persona_import_invalid_uuid(mock_workspace, tmp_path):
    archive_path = tmp_path / 'invalid_uuid.tur'
    import tarfile

    with tarfile.open(archive_path, 'w:gz') as tar:
        persona_data = {'id': 'not-a-valid-uuid', 'name': 'Fake'}
        yaml_bytes = yaml.dump(persona_data).encode('utf-8')
        info = tarfile.TarInfo(name='persona.yaml')
        info.size = len(yaml_bytes)
        import io

        tar.addfile(info, io.BytesIO(yaml_bytes))

    result = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result.exit_code == 1
    assert 'Registry Failure: Imported ID' in result.stdout


def test_admin_persona_import_duplicate_overwrite_prevention(mock_workspace, tmp_path):
    _ = mock_workspace
    archive_path = tmp_path / 'ariel.tur'

    # Export persona Ariel
    result_export = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', str(archive_path)])
    assert result_export.exit_code == 0

    # Unregister persona so the first import is a clean import
    import shutil

    _global_home = Path.home() / '.tur'
    _dest_dir = _global_home / 'personas' / '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    if _dest_dir.exists():
        shutil.rmtree(_dest_dir)
    _index_path = _global_home / 'personas.yaml'
    if _index_path.exists():
        with open(_index_path, encoding='utf-8') as _f:
            _idx = yaml.safe_load(_f) or {'personas': []}
        _idx['personas'] = [p for p in _idx['personas'] if str(p['id']) != '7544202e-92f5-40ce-adfb-e4b0eae6c262']
        with open(_index_path, 'w', encoding='utf-8') as _f:
            yaml.dump(_idx, _f)

    # First import works fine (persona absent from registry)
    result_import1 = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result_import1.exit_code == 0

    # Second import without --force fails due to duplicate
    result_import2 = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result_import2.exit_code == 1
    assert 'already exists' in result_import2.stdout

    # Third import with --force succeeds
    result_import3 = runner.invoke(admin_app, ['persona', 'import', str(archive_path), '--force'])
    assert result_import3.exit_code == 0


def test_admin_persona_import_duplicate_overwrite_with_short_alias(mock_workspace, tmp_path):
    _ = mock_workspace
    archive_path = tmp_path / 'ariel.tur'

    # Export persona Ariel
    result_export = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', str(archive_path)])
    assert result_export.exit_code == 0

    # Unregister persona so the first import is a clean import
    import shutil

    _global_home2 = Path.home() / '.tur'
    _dest_dir2 = _global_home2 / 'personas' / '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    if _dest_dir2.exists():
        shutil.rmtree(_dest_dir2)
    _index_path2 = _global_home2 / 'personas.yaml'
    if _index_path2.exists():
        with open(_index_path2, encoding='utf-8') as _f2:
            _idx2 = yaml.safe_load(_f2) or {'personas': []}
        _idx2['personas'] = [p for p in _idx2['personas'] if str(p['id']) != '7544202e-92f5-40ce-adfb-e4b0eae6c262']
        with open(_index_path2, 'w', encoding='utf-8') as _f2:
            yaml.dump(_idx2, _f2)

    # First import works fine (persona absent from registry)
    result_import1 = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result_import1.exit_code == 0

    # Second import without -f fails due to duplicate
    result_import2 = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result_import2.exit_code == 1
    assert 'already exists' in result_import2.stdout

    # Third import with -f succeeds
    result_import3 = runner.invoke(admin_app, ['persona', 'import', str(archive_path), '-f'])
    assert result_import3.exit_code == 0


def test_admin_persona_export_filters_memories(mock_workspace, tmp_path):
    _ = mock_workspace
    import tarfile

    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    # 1. Setup memories with different scopes
    persona_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memory_manager = MemoryManager(base_dir=persona_dir)

    inc_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='This is a project-specific incarnation memory.',
    )
    uni_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.UNIVERSAL,
        content='This is a global universal memory.',
    )
    user_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.USER,
        content='This is a user memory.',
    )
    pers_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.PERSONA,
        content='This is a persona memory.',
    )

    memory_manager.save(inc_mem)
    memory_manager.save(uni_mem)
    memory_manager.save(user_mem)
    memory_manager.save(pers_mem)

    # 2. Export
    archive_path = tmp_path / 'filtered.tur'
    result = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', str(archive_path)])
    assert result.exit_code == 0

    # 3. Read tar archive and inspect members
    with tarfile.open(archive_path, 'r:gz') as tar:
        members = [m.name for m in tar.getmembers()]

        # Check that universal, user, and persona memories are in the archive
        uni_filename = f'_{uni_mem.id}.md'
        user_filename = f'_{user_mem.id}.md'
        pers_filename = f'_{pers_mem.id}.md'
        inc_filename = f'_{inc_mem.id}.md'

        assert any(uni_filename in m for m in members), f'Universal memory not found in tar: {members}'
        assert any(user_filename in m for m in members), f'User memory not found in tar: {members}'
        assert any(pers_filename in m for m in members), f'Persona memory not found in tar: {members}'
        assert not any(inc_filename in m for m in members), f'Incarnation memory unexpectedly found in tar: {members}'


def test_admin_persona_import_missing_uuid(mock_workspace, tmp_path):
    archive_path = tmp_path / 'missing_uuid.tur'
    import io
    import tarfile

    with tarfile.open(archive_path, 'w:gz') as tar:
        persona_data = {'name': 'Fake'}  # 'id' is missing
        yaml_bytes = yaml.dump(persona_data).encode('utf-8')
        info = tarfile.TarInfo(name='persona.yaml')
        info.size = len(yaml_bytes)

        tar.addfile(info, io.BytesIO(yaml_bytes))

    result = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result.exit_code == 1
    # Rich console may wrap long error messages; check for shorter substrings
    assert 'Registry Failure' in result.stdout
    assert "canonical 'id'" in result.stdout


def test_admin_session_note_invalid_index(mock_workspace):
    # Start session first so notes folder exists
    runner.invoke(admin_app, ['session', 'start', 'session-note-bound-test'])

    # Attempt index 5 (which is out of bounds, since there's only 1 default note)
    result = runner.invoke(admin_app, ['session', 'note', '5', '--session-id', 'session-note-bound-test'])
    assert result.exit_code == 0
    assert 'Invalid note index' in result.stdout

    # Attempt index < 1
    result_neg = runner.invoke(admin_app, ['session', 'note', '0', '--session-id', 'session-note-bound-test'])
    assert result_neg.exit_code == 0
    assert 'Invalid note index' in result_neg.stdout


def test_admin_persona_list_empty(mock_workspace):
    # Remove personas.yaml
    index_path = Path('.tur/personas.yaml')
    if index_path.exists():
        index_path.unlink()

    result = runner.invoke(admin_app, ['persona', 'list'])
    assert result.exit_code == 0
    assert 'No registered personas found' in result.stdout


def test_admin_persona_list_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise ValueError('Listing failed')

    import tur.cli.admin

    monkeypatch.setattr(tur.cli.admin, 'resolve_personas_base_dir', mock_raise)

    result = runner.invoke(admin_app, ['persona', 'list'])
    assert result.exit_code == 1
    assert 'Error listing personas: Listing failed' in result.stdout


def test_admin_persona_view_empty_principles_and_directives(mock_workspace):
    # Ariel has principles by default in mock_workspace. Umbriel has no principles/directives by default.
    result = runner.invoke(admin_app, ['persona', 'view', 'Umbriel'])
    assert result.exit_code == 0
    assert 'Principles' in result.stdout
    assert 'none' in result.stdout.lower()


def test_admin_persona_view_with_directives(mock_workspace):
    # Write a custom persona.yaml with directives and empty principles
    persona_path = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/persona.yaml')
    custom_yaml = {
        'name': 'ArielCustom',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
        'directives': ['Stay calm.', 'Think step by step.'],
    }
    with open(persona_path, 'w', encoding='utf-8') as f:
        yaml.dump(custom_yaml, f)

    result = runner.invoke(admin_app, ['persona', 'view', 'Ariel'])
    assert result.exit_code == 0
    assert 'Directives' in result.stdout
    assert 'Stay calm.' in result.stdout


def test_admin_persona_view_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise ValueError('View failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(admin_app, ['persona', 'view', 'Ariel'])
    assert result.exit_code == 1
    assert 'Error viewing persona: View failed' in result.stdout


def test_admin_memory_view_not_found(mock_workspace):
    result = runner.invoke(admin_app, ['memory', 'view', 'non-existent-hash'])
    assert result.exit_code == 0
    assert 'No memory found matching ID' in result.stdout


def test_admin_memory_view_error(mock_workspace, monkeypatch):
    from tur.memory import MemoryManager

    def mock_raise(*args, **kwargs):
        raise ValueError('Load failed')

    monkeypatch.setattr(MemoryManager, 'load_all', mock_raise)

    result = runner.invoke(admin_app, ['memory', 'view', 'some-hash'])
    assert result.exit_code == 1
    assert 'Error viewing memory: Load failed' in result.stdout


def test_admin_session_note_no_active(mock_workspace):
    # Set active_session_id to None in state.yaml
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'active_session_id': None}, f)

    result = runner.invoke(admin_app, ['session', 'note', '1'])
    assert result.exit_code == 0
    assert 'No active session found' in result.stdout


def test_admin_session_note_missing_file(mock_workspace):
    # Set active session but delete its notes file
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            {
                'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262',
                'active_session_id': 'non-existent-sess',
            },
            f,
        )

    result = runner.invoke(admin_app, ['session', 'note', '1'])
    assert result.exit_code == 0
    assert 'No notes file found for session' in result.stdout


def test_admin_session_note_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise ValueError('Session note view failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(admin_app, ['session', 'note', '1'])
    assert result.exit_code == 1
    assert 'Error viewing session note: Session note view failed' in result.stdout


def test_admin_persona_import_symlink_prevention(mock_workspace, tmp_path):
    archive_path = tmp_path / 'symlink.tur'
    import io
    import tarfile

    with tarfile.open(archive_path, 'w:gz') as tar:
        info = tarfile.TarInfo(name='persona.yaml')
        info.type = tarfile.SYMTYPE
        info.linkname = 'some_target'
        tar.addfile(info, io.BytesIO(b''))

    result = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result.exit_code == 1
    assert 'Archive contains a symlink or hardlink' in result.stdout


def test_admin_persona_import_hardlink_prevention(mock_workspace, tmp_path):
    archive_path = tmp_path / 'hardlink.tur'
    import io
    import tarfile

    with tarfile.open(archive_path, 'w:gz') as tar:
        info = tarfile.TarInfo(name='persona.yaml')
        info.type = tarfile.LNKTYPE
        info.linkname = 'some_target'
        tar.addfile(info, io.BytesIO(b''))

    result = runner.invoke(admin_app, ['persona', 'import', str(archive_path)])
    assert result.exit_code == 1
    assert 'Archive contains a symlink or hardlink' in result.stdout


def test_admin_persona_import_set_default(mock_workspace, tmp_path):
    _ = mock_workspace
    archive_path = Path('ariel_default.tur')
    result_export = runner.invoke(admin_app, ['persona', 'export', 'Ariel', '--output', str(archive_path)])
    assert result_export.exit_code == 0
    assert archive_path.exists()

    # Persona already exists in mock registry — use --force to allow reimport
    result_import = runner.invoke(admin_app, ['persona', 'import', str(archive_path), '--set-default', '--force'])
    assert result_import.exit_code == 0
    assert 'successfully imported' in result_import.stdout

    state_path = Path('.tur/state.yaml')
    assert state_path.exists()
    with open(state_path, encoding='utf-8') as f:
        state_data = yaml.safe_load(f)
    assert state_data['active_persona_id'] == '7544202e-92f5-40ce-adfb-e4b0eae6c262'
