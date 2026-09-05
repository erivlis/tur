import os
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from tur import dreaming, persona, session
from tur.cli.agent import app as agent_app
from tur.models import HarnessDelegationError

runner = CliRunner()


def test_tur_version_flag():
    from tur import __version__

    res_long = runner.invoke(agent_app, ['--version'])
    assert res_long.exit_code == 0
    assert f'tur {__version__}' in res_long.output

    res_short = runner.invoke(agent_app, ['-V'])
    assert res_short.exit_code == 0
    assert f'tur {__version__}' in res_short.output


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
    assert 'L1 Memories' in result_active.stdout


def test_agent_status_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Status error')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['status'])
    assert result.exit_code == 1
    assert 'Error: Status error' in result.stdout


def test_agent_metrics(mock_workspace):
    result = runner.invoke(agent_app, ['metrics'])
    assert result.exit_code == 0
    assert 'System Metrics' in result.stdout
    assert 'Ariel' in result.stdout
    assert 'Constraint Dim (Cp)' in result.stdout
    assert 'Static Token Cost' in result.stdout

    # Test legacy alias
    result_alias = runner.invoke(agent_app, ['telemetry'])
    assert result_alias.exit_code == 0
    assert 'System Metrics' in result_alias.stdout


def test_agent_metrics_json(mock_workspace):
    result = runner.invoke(agent_app, ['metrics', '--json'])
    assert result.exit_code == 0
    assert '"persona_name": "Ariel"' in result.stdout
    assert '"constraint_dimensionality"' in result.stdout
    assert '"static_token_cost"' in result.stdout


def test_agent_metrics_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError('Metrics calculation failed')

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_raise)

    result = runner.invoke(agent_app, ['metrics'])
    assert result.exit_code == 1
    assert 'Error calculating metrics' in result.stdout


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

    from tur.cli.agent import main

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0


def test_tur_module_main(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tur', '--help'])

    from tur.__main__ import main

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0


def test_agent_wake_state_file_corrupt(mock_workspace):
    # Corrupt state.yaml
    state_path = Path('.tur/state.yaml')
    state_path.write_text('invalid: yaml: : content', encoding='utf-8')

    result = runner.invoke(agent_app, ['wake', 'Ariel'])
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

    # 3. Agent CLI does NOT expose approve command (Physical Boundary)
    agent_approve = runner.invoke(agent_app, ['approve', core_id[:8]])
    assert agent_approve.exit_code != 0

    # 4. Approve via Admin CLI
    from tur.cli.admin import app as admin_app

    approve_res = runner.invoke(admin_app, ['memory', 'approve', core_id[:8]])
    assert approve_res.exit_code == 0
    assert 'approved and activated successfully' in approve_res.stdout

    # 5. Approving again notes that it is already active
    approve_again = runner.invoke(admin_app, ['memory', 'approve', core_id[:8]])
    assert approve_again.exit_code == 0
    assert 'already active' in approve_again.stdout


def test_agent_evolve_errors(mock_workspace):
    # Evolve nonexistent memory
    res = runner.invoke(
        agent_app,
        ['evolve', 'nonexistent_id', '--principle', 'p', '--covenant', 'c'],
    )
    assert res.exit_code == 1
    assert 'No memory found matching ID' in res.stdout


def test_agent_list_agents_and_coordination(mock_workspace):
    # Start session and wake an agent
    wake_res = runner.invoke(agent_app, ['wake', '--agent-id', 'agent_alpha'])
    assert wake_res.exit_code == 0

    # List agents (table format)
    list_res = runner.invoke(agent_app, ['list-agents'])
    assert list_res.exit_code == 0
    assert 'agent_alpha' in list_res.stdout

    # List agents (json format)
    list_json = runner.invoke(agent_app, ['list-agents', '--json'])
    assert list_json.exit_code == 0
    assert '"id": "agent_alpha"' in list_json.stdout

    # Send a signal
    sig_res = runner.invoke(
        agent_app,
        ['signal', '*', 'Broadcast sync message', '--agent-id', 'agent_alpha'],
    )
    assert sig_res.exit_code == 0
    assert 'Signal sent successfully' in sig_res.stdout

    # Read signals (standard format)
    read_res = runner.invoke(
        agent_app,
        ['read-signals', '--agent-id', 'agent_alpha', '--unread-only'],
    )
    assert read_res.exit_code == 0
    assert 'Broadcast sync message' in read_res.stdout

    # Read signals (json format)
    read_json = runner.invoke(
        agent_app,
        ['read-signals', '--agent-id', 'agent_alpha', '--json', '--all'],
    )
    assert read_json.exit_code == 0
    assert 'Broadcast sync message' in read_json.stdout

    # Extract signal id from JSON
    import json

    sigs = json.loads(read_json.stdout)
    sig_id = sigs[0]['id']

    # Ack signal
    ack_res = runner.invoke(
        agent_app,
        ['ack-signals', sig_id, '--agent-id', 'agent_alpha'],
    )
    assert ack_res.exit_code == 0

    # Whiteboard write and read
    wb_w = runner.invoke(
        agent_app,
        ['whiteboard-write', 'coord_key', 'val_123', '--agent-id', 'agent_alpha'],
    )
    assert wb_w.exit_code == 0

    wb_r = runner.invoke(agent_app, ['whiteboard-read', 'coord_key'])
    assert wb_r.exit_code == 0
    assert 'val_123' in wb_r.stdout

    # Whiteboard unset key
    wb_unset = runner.invoke(agent_app, ['whiteboard-read', 'nonexistent_key'])
    assert wb_unset.exit_code == 0
    assert "Key 'nonexistent_key' not set." in wb_unset.stdout

    # Read notes
    notes_res = runner.invoke(agent_app, ['read-notes'])
    assert notes_res.exit_code == 0

    # Tired command
    tired_res = runner.invoke(agent_app, ['tired', '--agent-id', 'agent_alpha'])
    assert tired_res.exit_code == 0


def test_agent_resolve_cli_context_namespace_violation(mock_workspace, monkeypatch):
    # Wake first to establish session
    runner.invoke(agent_app, ['wake', '--agent-id', 'alpha'])

    # Set TUR_AGENT_ID and try to use conflicting agent_id
    monkeypatch.setenv('TUR_AGENT_ID', 'alpha')
    sig_err = runner.invoke(
        agent_app,
        ['signal', '*', 'hello', '--agent-id', 'beta'],
    )
    assert sig_err.exit_code == 1
    assert 'Namespace violation' in sig_err.stdout


def test_agent_introspect(mock_workspace, monkeypatch):
    import tur.cli.agent

    def fake_run_intro(*args, **kwargs):
        import networkx as nx

        g = nx.DiGraph()
        g.add_node('concept_1', label='Root Concept')
        return g

    monkeypatch.setattr(tur.cli.agent, 'run_introspection', fake_run_intro)
    monkeypatch.setattr(tur.cli.agent, 'format_graph_as_mermaid', lambda g: 'graph TD\nconcept_1')

    intro_res = runner.invoke(agent_app, ['introspect', '--all', '--visualize'])
    assert intro_res.exit_code == 0
    assert 'Introspection Assembly completed successfully' in intro_res.stdout
    assert '--- Mermaid L2 Graph ---' in intro_res.stdout

    # Test delegation handling
    def mock_delegation(*args, **kwargs):
        raise HarnessDelegationError('Delegation required')

    monkeypatch.setattr(tur.cli.agent, 'run_introspection', mock_delegation)
    intro_del = runner.invoke(agent_app, ['introspect'])
    assert intro_del.exit_code == 0
    assert 'Delegation required' in intro_del.stdout

    # Test error handling
    def mock_err(*args, **kwargs):
        raise RuntimeError('Introspection error')

    monkeypatch.setattr(tur.cli.agent, 'run_introspection', mock_err)
    intro_err = runner.invoke(agent_app, ['introspect'])
    assert intro_err.exit_code == 1
    assert 'Error during introspection: Introspection error' in intro_err.stdout


def test_agent_resolve_cli_context_ambiguous_agents(mock_workspace, monkeypatch):
    # Wake two different agents in the same session
    runner.invoke(agent_app, ['wake', '--agent-id', 'agent_one'])
    runner.invoke(agent_app, ['wake', '--agent-id', 'agent_two'])

    # Clear env so auto-resolution triggers
    monkeypatch.delenv('TUR_AGENT_ID', raising=False)

    # Signal without --agent-id should fail due to ambiguity
    res = runner.invoke(agent_app, ['signal', '*', 'hello'])
    assert res.exit_code == 1
    assert 'AmbiguousIdentityError' in res.stdout


def test_agent_status_long_note_and_past_session(mock_workspace, monkeypatch):
    # 1. Wake and create a long note (>80 chars)
    runner.invoke(agent_app, ['wake', '--agent-id', 'agent_long'])
    long_content = (
        'This is a very detailed and long architectural note'
        ' that exceeds eighty characters in total length for testing.'
    )
    runner.invoke(agent_app, ['note', long_content])

    status_res = runner.invoke(agent_app, ['status'])
    assert status_res.exit_code == 0
    assert '…' in status_res.stdout

    # 2. Clear active session in state.yaml to verify (last) past session branch
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'active_session_id': None}, f)
    monkeypatch.delenv('TUR_ACTIVE_SESSION_ID', raising=False)

    status_ended = runner.invoke(agent_app, ['status'])
    assert status_ended.exit_code == 0
    assert '(last)' in status_ended.stdout


def test_agent_coordination_no_session_errors(mock_workspace, monkeypatch):
    # Clear active session in state.yaml
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': '7544202e-92f5-40ce-adfb-e4b0eae6c262', 'active_session_id': None}, f)
    monkeypatch.delenv('TUR_ACTIVE_SESSION_ID', raising=False)

    # List agents should fail
    assert runner.invoke(agent_app, ['list-agents']).exit_code == 1
    # Read signals should fail
    assert runner.invoke(agent_app, ['read-signals']).exit_code == 1
    # Whiteboard read should fail
    assert runner.invoke(agent_app, ['whiteboard-read', 'key']).exit_code == 1
    # Whiteboard write should fail
    assert runner.invoke(agent_app, ['whiteboard-write', 'key', 'val']).exit_code == 1
    # Read notes should fail
    assert runner.invoke(agent_app, ['read-notes']).exit_code == 1


def test_agent_diff_cli(mock_workspace):
    # Wake to start session
    runner.invoke(agent_app, ['wake'])
    # Store a memory in active session
    runner.invoke(agent_app, ['learn', 'Test memory for diff', '--type', 'fact', '--scope', 'incarnation'])

    # Test diff
    diff_res = runner.invoke(agent_app, ['diff'])
    assert diff_res.exit_code == 0
    assert 'Memory Delta' in diff_res.stdout

    # Test diff JSON
    diff_json = runner.invoke(agent_app, ['diff', '--json'])
    assert diff_json.exit_code == 0
    import json

    data = json.loads(diff_json.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]['content'] == 'Test memory for diff'


def test_agent_read_notes_include_previous(mock_workspace):
    runner.invoke(agent_app, ['wake', '--session-id', 'sess-parent'])
    runner.invoke(agent_app, ['note', 'Parent note content'])

    runner.invoke(agent_app, ['wake', '--session-id', 'sess-child', '--from-session', 'sess-parent'])
    runner.invoke(agent_app, ['note', 'Child note content'])

    # Read notes with include_previous
    res = runner.invoke(agent_app, ['read-notes', '--include-previous'])
    assert res.exit_code == 0
    assert 'Parent note content' in res.stdout
    assert 'Child note content' in res.stdout

    # Read notes with session-id previous
    res_prev = runner.invoke(agent_app, ['read-notes', '--session-id', 'previous'])
    assert res_prev.exit_code == 0
    assert 'Parent note content' in res_prev.stdout


def test_agent_recall_effort_and_mermaid_cli(mock_workspace):
    import json

    import networkx as nx
    import yaml

    from tur import persona

    active_id = persona.get_active_persona_id()
    persona_dir = persona.get_persona_path(active_id)

    g = nx.DiGraph()
    g.add_node('c1', type='Concept', content='Graph retrieval architecture', status='active', confidence=1.0)
    g.add_node('c2', type='Fact', content='Personalized PageRank engine', status='active', confidence=1.0)
    g.add_edge('c1', 'c2', type='supported_by')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    # Standard recall (effort 0)
    res0 = runner.invoke(agent_app, ['recall', 'retrieval'])
    assert res0.exit_code == 0
    data0 = json.loads(res0.stdout)
    assert any(n['id'] == 'c1' for n in data0)

    # Recall with effort 5 and mermaid
    res5 = runner.invoke(agent_app, ['recall', 'retrieval', '--effort', '5', '--mermaid'])
    assert res5.exit_code == 0
    assert '```mermaid' in res5.stdout
    assert 'graph TD' in res5.stdout

    # Recall with --deep alias
    res_deep = runner.invoke(agent_app, ['recall', 'retrieval', '--deep'])
    assert res_deep.exit_code == 0
    assert 'c1' in res_deep.stdout


def test_agent_metrics_spectral_cli(mock_workspace):
    import json

    import networkx as nx
    import yaml

    from tur import persona

    active_id = persona.get_active_persona_id()
    persona_dir = persona.get_persona_path(active_id)

    g = nx.DiGraph()
    g.add_node('m1', type='Concept', content='M1', status='active', confidence=1.0)
    g.add_node('m2', type='Fact', content='M2', status='active', confidence=1.0)
    g.add_edge('m1', 'm2', type='supported_by')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    # Test rich table output
    res = runner.invoke(agent_app, ['metrics'])
    assert res.exit_code == 0
    assert 'Graph Nodes / Edges' in res.stdout
    assert 'Knowledge Communities' in res.stdout
    assert 'Algebraic Connectivity' in res.stdout
    assert 'Modularity Score (Q)' in res.stdout

    # Test JSON output
    res_json = runner.invoke(agent_app, ['metrics', '--json'])
    assert res_json.exit_code == 0
    data = json.loads(res_json.stdout)
    assert data['graph_nodes'] == 2
    assert data['graph_edges'] == 1
    assert 'algebraic_connectivity' in data
    assert 'modularity_score' in data


def test_agent_status_cli(mock_workspace):
    # Test tur status before wake
    res_initial = runner.invoke(agent_app, ['status'])
    assert res_initial.exit_code == 0
    assert 'Persona' in res_initial.stdout
    assert 'Tur Status' in res_initial.stdout

    # Wake and take a note
    runner.invoke(agent_app, ['wake'])
    runner.invoke(agent_app, ['note', 'First status test note.'])

    # Test tur status after wake and note
    res_after = runner.invoke(agent_app, ['status'])
    assert res_after.exit_code == 0
    assert 'First status test note.' in res_after.stdout
    assert 'Notes' in res_after.stdout
    assert 'active' in res_after.stdout


def test_cli_guard_lock_contention(mock_workspace, monkeypatch):
    """Verify @cli_guard catches LockTimeoutError and formats contention warning."""
    from tur.locking import LockTimeoutError

    def mock_lock_timeout(*args, **kwargs):
        raise LockTimeoutError(Path('.tur/test.lock'), timeout=2.0)

    monkeypatch.setattr(persona, 'get_active_persona_id', mock_lock_timeout)

    res = runner.invoke(agent_app, ['status'])
    assert res.exit_code == 1
    assert 'Contention Warning: State lock is held by another process' in res.stdout


