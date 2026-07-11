import os
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from tur import dreaming, persona, session
from tur.cli.agent import app as agent_app

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

    return tmp_path, persona_id_1, persona_id_2


def test_agent_help(mock_workspace):
    result = runner.invoke(agent_app, ['--help'])
    assert result.exit_code == 0
    assert 'Persona safe agent runtime' in result.stdout


def test_agent_wake_default(mock_workspace):
    result = runner.invoke(agent_app, ['wake'])
    assert result.exit_code == 0
    assert 'SYSTEM WAKE: Ariel' in result.stdout
    assert 'To safeguard reality.' in result.stdout


def test_agent_wake_by_name(mock_workspace):
    result = runner.invoke(agent_app, ['wake', 'Umbriel'])
    assert result.exit_code == 0
    assert 'SYSTEM WAKE: Umbriel' in result.stdout


def test_agent_wake_invalid(mock_workspace):
    result = runner.invoke(agent_app, ['wake', 'InvalidPersona'])
    assert result.exit_code == 1
    assert 'Error waking persona' in result.stdout or 'Error during wake' in result.stdout


def test_agent_learn_and_recall(mock_workspace):
    # Learn fact
    result_learn = runner.invoke(agent_app, ['learn', 'Memory content fact description', '--type', 'fact'])
    assert result_learn.exit_code == 0
    assert 'Consolidating memory' in result_learn.stdout
    assert 'Memory saved' in result_learn.stdout

    # Recall fact
    result_recall = runner.invoke(agent_app, ['recall', 'description'])
    assert result_recall.exit_code == 0
    assert 'Memory content fact description' in result_recall.stdout


def test_agent_note_command(mock_workspace):
    # Ensure there is an active session
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            {
                'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262',
                'active_session_id': 'sess-note-test',
            },
            f,
        )
    # Start the session first so the folders are created
    session.start_session_logic('sess-note-test', identifier='7544202e-92f5-40ce-adfb-e4b0eae6c262')

    result = runner.invoke(agent_app, ['note', 'Appended note via agent CLI'])
    assert result.exit_code == 0
    assert 'successfully' in result.stdout


def test_agent_note_command_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Note failure')

    monkeypatch.setattr(session, 'note_logic', mock_raise)

    result = runner.invoke(agent_app, ['note', 'Note to fail'])
    assert result.exit_code == 1
    assert 'Error saving note' in result.stdout


def test_agent_sleep(mock_workspace, monkeypatch):
    monkeypatch.setattr(dreaming, 'perform_sleep_dreaming', lambda **kwargs: 2)

    # Establish an active session to test session auto-ending on sleep
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            {
                'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262',
                'active_session_id': 'session-sleep-test',
            },
            f,
        )
    session.start_session_logic('session-sleep-test', identifier='7544202e-92f5-40ce-adfb-e4b0eae6c262')

    log_path = Path('fake_chat.log')
    log_path.write_text('User: Hello\nAgent: Hi', encoding='utf-8')

    result = runner.invoke(agent_app, ['sleep', str(log_path), '--note', 'Test sleep note'])
    assert result.exit_code == 0
    assert 'Dreams consolidated. 2 new memories formed.' in result.stdout


def test_agent_sleep_exception(mock_workspace, monkeypatch):
    def raise_err(**kwargs):
        raise RuntimeError('LLM Failure')

    monkeypatch.setattr(dreaming, 'perform_sleep_dreaming', raise_err)

    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            {
                'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262',
                'active_session_id': 'session-sleep-fail',
            },
            f,
        )
    session.start_session_logic('session-sleep-fail', identifier='7544202e-92f5-40ce-adfb-e4b0eae6c262')

    log_path = Path('fake_chat.log')
    log_path.write_text('User: Hello\nAgent: Hi', encoding='utf-8')

    result = runner.invoke(agent_app, ['sleep', str(log_path), '--note', 'Test sleep note'])
    assert result.exit_code == 0  # CLI prints error but exits gracefully
    assert 'Error during dreaming: LLM Failure' in result.stdout


def test_agent_status(mock_workspace):
    # No active session yet
    result = runner.invoke(agent_app, ['status'])
    assert result.exit_code == 0
    assert 'Tur Status' in result.stdout
    assert 'Ariel' in result.stdout
    assert 'Status' in result.stdout
    assert 'none' in result.stdout or 'none' in result.stdout.lower()

    # Now start one (using state mapping)
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            {
                'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262',
                'active_session_id': 'session-status-test',
            },
            f,
        )
    session.start_session_logic('session-status-test', identifier='7544202e-92f5-40ce-adfb-e4b0eae6c262')

    result_active = runner.invoke(agent_app, ['status'])
    assert result_active.exit_code == 0
    assert 'Status' in result_active.stdout
    assert 'active' in result_active.stdout
    assert 'session-status-test' in result_active.stdout


def test_agent_status_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Status error')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['status'])
    assert result.exit_code == 1
    assert 'Error: Status error' in result.stdout


def test_agent_wake_auto_start(mock_workspace):
    # Ensure active_session_id is None under state.yaml
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'active_session_id': None}, f)

    result = runner.invoke(agent_app, ['wake'])
    assert result.exit_code == 0
    assert 'Auto-started new session' in result.stdout


def test_agent_wake_with_args(mock_workspace):
    result = runner.invoke(agent_app, ['wake', '--agent-id', 'test_agent_cli', '--harness-conversation-id', 'conv_123'])
    assert result.exit_code == 0
    assert 'SYSTEM WAKE: Ariel' in result.stdout

    state_path = Path('.tur/state.yaml')
    with open(state_path, encoding='utf-8') as f:
        state_data = yaml.safe_load(f)
    session_id = state_data['active_session_id']

    conn = session.get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM agents WHERE id = 'test_agent_cli'")
    row = cursor.fetchone()
    assert row is not None
    assert row['status'] == 'active'
    conn.close()


def test_agent_learn_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Learn failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['learn', 'Memory content fact description'])
    assert result.exit_code == 1
    assert 'Error: Learn failed' in result.stdout


def test_agent_recall_no_match(mock_workspace):
    result = runner.invoke(agent_app, ['recall', 'completely-unmatched-query-string'])
    assert result.exit_code == 0
    assert 'No memories found matching query' in result.stdout


def test_agent_recall_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Recall failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['recall', 'description'])
    assert result.exit_code == 1
    assert 'Error: Recall failed' in result.stdout


def test_agent_sleep_top_level_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Sleep top-level failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['sleep', 'fake_chat.log', '--note', 'Test sleep note'])
    assert result.exit_code == 1
    assert 'Error: Sleep top-level failed' in result.stdout or 'Error during sleep' in result.stdout


def test_agent_wake_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError('Wake failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['wake'])
    assert result.exit_code == 1
    assert 'Error during wake: Wake failed' in result.stdout


def test_agent_no_admin_commands(mock_workspace):
    # Try calling switch
    result = runner.invoke(agent_app, ['switch'])
    assert result.exit_code == 2

    # Try calling export
    result = runner.invoke(agent_app, ['export'])
    assert result.exit_code == 2

    # Try calling memories / memory
    result = runner.invoke(agent_app, ['memories'])
    assert result.exit_code == 2

    result = runner.invoke(agent_app, ['memory'])
    assert result.exit_code == 2


def test_agent_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur', '--help'])

    import runpy

    with pytest.raises(SystemExit) as exc:
        runpy.run_module('tur.cli.agent', run_name='__main__')

    assert exc.value.code == 0


def test_tur_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur', '--help'])

    import runpy

    with pytest.raises(SystemExit) as exc:
        runpy.run_module('tur', run_name='__main__')

    assert exc.value.code == 0


def test_agent_wake_state_file_corrupt(mock_workspace, monkeypatch):
    # Corrupt state.yaml
    state_path = Path('.tur/state.yaml')
    state_path.write_text('invalid: yaml: : content', encoding='utf-8')

    # Mock select_persona_wizard to prevent blocking TUI from launching
    import tur.persona
    import tur.tui

    monkeypatch.setattr(tur.persona, 'select_persona_wizard', lambda index: '7544202e-92f5-40ce-adfb-e4b0eae6c262')
    monkeypatch.setattr(tur.tui, 'select_persona_wizard', lambda index: '7544202e-92f5-40ce-adfb-e4b0eae6c262')

    result = runner.invoke(agent_app, ['wake'])
    assert result.exit_code == 0
    assert 'SYSTEM WAKE' in result.stdout


def test_agent_status_no_persona_yaml(mock_workspace):
    # Remove persona.yaml
    persona_path = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/persona.yaml')
    if persona_path.exists():
        persona_path.unlink()

    result = runner.invoke(agent_app, ['status'])
    assert result.exit_code == 0
    assert 'Tur Status' in result.stdout
    assert 'unknown' in result.stdout.lower()


def test_agent_status_no_session(mock_workspace):
    # Ensure active session is None
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'active_session_id': None}, f)

    result = runner.invoke(agent_app, ['status'])
    assert result.exit_code == 0
    assert 'Tur Status' in result.stdout


def test_agent_verify_success(mock_workspace):
    # Save a memory first
    runner.invoke(agent_app, ['learn', 'Valid memory content.'])
    result = runner.invoke(agent_app, ['verify'])
    assert result.exit_code == 0
    assert 'verified successfully' in result.stdout


def test_agent_verify_failure(mock_workspace):
    # Save a memory
    runner.invoke(agent_app, ['learn', 'To be tampered memory.'])

    # Locate the saved memory file and tamper it
    persona_dir = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memories_dir = persona_dir / 'memories' / 'active'
    md_files = list(memories_dir.glob('*.md'))
    assert len(md_files) == 1

    # Break Golem's seal to write
    os.chmod(md_files[0], 0o666)

    # Read and tamper
    with open(md_files[0], encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    new_content = f'---{parts[1]}---\n\nTampered content.\n'

    with open(md_files[0], 'w', encoding='utf-8') as f:
        f.write(new_content)

    result = runner.invoke(agent_app, ['verify'])
    assert result.exit_code == 1
    assert 'TAMPERED STATE' in result.stdout


def test_agent_core_memory_evolution_flow(mock_workspace):
    # 1. Save standard memory first
    runner.invoke(agent_app, ['learn', 'Our collaborative workflow preference.'])

    # Find the memory ID
    persona_dir = Path('.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262')
    memories_dir = persona_dir / 'memories' / 'active'
    md_files = list(memories_dir.glob('*.md'))
    assert len(md_files) == 1
    memory_id = md_files[0].name.split('_')[-1].split('.')[0]

    # 2. Evolve the memory into a Core memory
    evolve_res = runner.invoke(
        agent_app,
        [
            'evolve',
            memory_id[:8],
            '--core-type',
            'relational_discovery',
            '--principle',
            'Always format code blocks with line counts.',
            '--covenant',
            'Ensure visual parity in plan reviews.',
        ],
    )
    assert evolve_res.exit_code == 0
    assert "Core Memory created and staged in 'pending_approval' status" in evolve_res.stdout

    # Find the new Core Memory ID
    global_memories_dir = (
        Path.home() / '.tur' / 'personas' / '7544202e-92f5-40ce-adfb-e4b0eae6c262' / 'memories' / 'active'
    )
    core_files = [f for f in global_memories_dir.glob('*.md') if 'core' in f.name]
    assert len(core_files) == 1
    core_id = core_files[0].name.split('_')[-1].split('.')[0]

    # 3. Approve the Core memory
    approve_res = runner.invoke(agent_app, ['approve', core_id[:8]])
    assert approve_res.exit_code == 0
    assert 'approved and activated successfully' in approve_res.stdout

    # 4. Devolve/Supersede the Core memory
    devolve_res = runner.invoke(agent_app, ['devolve', core_id[:8]])
    assert devolve_res.exit_code == 0
    assert 'successfully devolved (marked as superseded)' in devolve_res.stdout
