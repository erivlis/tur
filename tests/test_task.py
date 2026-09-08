"""
tests/test_task.py - Unit tests for Task Protocol and Swarm Management (EP-0147, EP-0149).
"""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from tur import mcp_server, session, task
from tur.cli.agent import app as agent_app
from tur.compiler import compile_persona

runner = CliRunner()


@pytest.fixture
def mock_task_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    p_dir = personas_dir / persona_id
    p_dir.mkdir(parents=True)
    (p_dir / 'memories' / 'active').mkdir(parents=True)
    (p_dir / 'memories' / 'archive').mkdir(parents=True)

    persona_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
        'protocols': [],
    }

    with open(p_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_yaml, f)

    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    session_id = 'sess_task_test'
    state_data = {'active_persona_id': persona_id, 'active_session_id': session_id}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    sessions_data = {'active_session_id': session_id, 'sessions': [{'id': session_id, 'status': 'active'}]}
    with open(p_dir / 'sessions.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(sessions_data, f)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('TUR_PROJECT_DIR', str(tmp_path))
    monkeypatch.setenv('TUR_ACTIVE_SESSION', session_id)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    conn = session.get_db_connection(session_id)
    session.init_db(conn)
    conn.close()
    return tmp_path, persona_id, session_id


def test_claim_and_get_task(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    t = task.claim_task(
        session_id=sess_id,
        task_id='EP-0147',
        title='Author EP-0147',
        agent_id='agent-1',
        objective='Formalize lifecycle',
        work_items=['Draft proposal', 'Validate proposal', 'Complete task'],
        target_files=['docs/proposals/EP-0147.md'],
    )
    assert t.task_id == 'EP-0147'
    assert t.status == 'in_progress'
    assert len(t.work_items) == 3
    assert t.manifestation.agent_id == 'agent-1'

    # Retrieve by default (singleton)
    retrieved_def = task.get_task(sess_id)
    assert retrieved_def is not None
    assert retrieved_def.task_id == 'EP-0147'

    # Retrieve by specific ID
    retrieved_spec = task.get_task(sess_id, 'EP-0147')
    assert retrieved_spec is not None
    assert retrieved_spec.title == 'Author EP-0147'


def test_multi_task_namespacing_and_list(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    task.claim_task(
        session_id=sess_id,
        task_id='TASK-1',
        title='First Subsystem Task',
        agent_id='agent-1',
        objective='Task 1 objective',
    )
    task.claim_task(
        session_id=sess_id,
        task_id='TASK-2',
        title='Second Subsystem Task',
        agent_id='agent-2',
        objective='Task 2 objective',
    )

    all_tasks = task.list_tasks(sess_id)
    assert len(all_tasks) == 2
    task_ids = {t.task_id for t in all_tasks}
    assert 'TASK-1' in task_ids
    assert 'TASK-2' in task_ids


def test_check_work_items(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    task.claim_task(
        session_id=sess_id,
        task_id='EP-0147',
        title='Work Items Test',
        agent_id='agent-1',
        work_items=['First item', 'Second item', 'Third item'],
    )

    # 1-based index completion
    t = task.check_item(sess_id, item_identifier=1, task_id='EP-0147')
    assert t.work_items[0].done is True
    assert t.work_items[1].done is False

    # Substring title completion
    t = task.check_item(sess_id, item_identifier='Third', task_id='EP-0147')
    assert t.work_items[2].done is True

    # Error handling on invalid identifier
    with pytest.raises(ValueError):
        task.check_item(sess_id, item_identifier='Nonexistent', task_id='EP-0147')


def test_handover_and_complete_task(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    task.claim_task(
        session_id=sess_id,
        task_id='EP-0147',
        title='Handover Test',
        agent_id='agent-1',
        work_items=['Task 1', 'Task 2'],
    )

    # Handover task
    t_handed = task.yield_task(sess_id, task_id='EP-0147', note='Pausing for review')
    assert t_handed.status == 'handover'
    assert any('Pausing for review' in b for b in t_handed.context_breadcrumbs)

    # Complete task
    t_completed = task.seal_task(sess_id, task_id='EP-0147')
    assert t_completed.status == 'completed'
    assert t_completed.manifestation.completed_at is not None


def test_dependency_blocking_and_reactive_unblocking(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    # Task A is in progress
    task.claim_task(
        session_id=sess_id,
        task_id='TASK-A',
        title='Prerequisite Task',
        agent_id='agent-1',
    )

    # Task B depends on Task A -> should start as blocked
    t_b = task.claim_task(
        session_id=sess_id,
        task_id='TASK-B',
        title='Dependent Task',
        agent_id='agent-2',
        depends_on=['TASK-A'],
    )
    assert t_b.status == 'blocked'

    # Completing Task A unblocks Task B
    task.seal_task(sess_id, task_id='TASK-A')

    t_b_updated = task.get_task(sess_id, task_id='TASK-B')
    assert t_b_updated.status == 'in_progress'


def test_task_lease_expiry(mock_task_workspace):
    _, _, sess_id = mock_task_workspace

    t = task.claim_task(
        session_id=sess_id,
        task_id='TASK-TTL',
        title='Lease Test',
        agent_id='agent-stale',
        lease_ttl_minutes=1,
    )

    # Fast forward claimed_at in the task
    t.manifestation.claimed_at = '2020-01-01T00:00:00+00:00'
    task.save_task(sess_id, t, updated_by='test')

    expired = task.is_lease_expired(t, sess_id)
    assert expired is True

    # Another agent can claim because lease is expired
    reclaimed = task.claim_task(
        session_id=sess_id,
        task_id='TASK-TTL',
        title='Lease Test',
        agent_id='agent-fresh',
        force=False,
    )
    assert reclaimed.manifestation.agent_id == 'agent-fresh'


def test_task_cli_commands(mock_task_workspace):
    _, _, _sess_id = mock_task_workspace

    # 1. Claim via CLI
    res = runner.invoke(
        agent_app,
        [
            'task',
            'claim',
            'CLI-001',
            '--title',
            'CLI Task',
            '--objective',
            'Test CLI commands',
            '--item',
            'Step 1',
            '--item',
            'Step 2',
        ],
    )
    assert res.exit_code == 0
    assert "Claimed task 'CLI-001'" in res.stdout

    # 2. List via CLI
    res_list = runner.invoke(agent_app, ['task', 'list'])
    assert res_list.exit_code == 0
    assert 'CLI-001' in res_list.stdout

    # 3. Show via CLI
    res_show = runner.invoke(agent_app, ['task', 'show', 'CLI-001'])
    assert res_show.exit_code == 0
    assert 'Test CLI commands' in res_show.stdout
    assert '1. ✗ Step 1' in res_show.stdout

    # 4. Check item via CLI
    res_check = runner.invoke(agent_app, ['task', 'check', '1', '--task', 'CLI-001'])
    assert res_check.exit_code == 0
    assert "Updated task 'CLI-001'" in res_check.stdout

    # Verify check
    res_show2 = runner.invoke(agent_app, ['task', 'show', 'CLI-001'])
    assert '1. ✓ Step 1' in res_show2.stdout

    # 5. Handover via CLI
    res_handover = runner.invoke(agent_app, ['task', 'handover', 'CLI-001', '--note', 'Switching context'])
    assert res_handover.exit_code == 0
    assert 'handover' in res_handover.stdout

    # 6. Complete via CLI
    res_complete = runner.invoke(agent_app, ['task', 'complete', 'CLI-001'])
    assert res_complete.exit_code == 0
    assert 'completed' in res_complete.stdout


def test_wake_prompt_injection(mock_task_workspace):
    _, persona_id, sess_id = mock_task_workspace

    task.claim_task(
        session_id=sess_id,
        task_id='EP-0147',
        title='Turn Zero Wake Injection',
        agent_id='agent-pi',
        objective='Inject tactical coordinates',
        work_items=['Step A', 'Step B'],
    )

    state = session.hydrate_session_state(persona_id)
    assert state.task is not None
    assert state.task['task_id'] == 'EP-0147'

    prompt = compile_persona(state)
    assert '## ACTIVE TASK' in prompt
    assert 'EP-0147' in prompt
    assert 'Inject tactical coordinates' in prompt
    assert 'Step A' in prompt


def test_mcp_task_tools(mock_task_workspace):
    _, _, _sess_id = mock_task_workspace

    # Claim via MCP
    claim_res = mcp_server.claim_task(
        task_id='MCP-001',
        title='MCP Task',
        objective='Test MCP surface',
        work_items=['Item 1', 'Item 2'],
    )
    assert 'Claimed task' in claim_res

    # Show via MCP
    show_res = mcp_server.show_task('MCP-001')
    assert 'MCP-001' in show_res
    assert 'Test MCP surface' in show_res

    # Check item via MCP
    check_res = mcp_server.check_task_item('1', task_id='MCP-001')
    assert 'Updated task' in check_res

    # Handover via MCP
    handover_res = mcp_server.handover_task('MCP-001', note='Pausing work')
    assert 'handover' in handover_res

    # Complete via MCP
    complete_res = mcp_server.complete_task('MCP-001')
    assert 'completed' in complete_res
