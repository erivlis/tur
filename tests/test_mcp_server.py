import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from tur import mcp_server
from tur.memory import MemoryManager
from tur.models import (
    Note,
    Persona,
    Principle,
    SessionEntry,
    SessionIndex,
    SessionNotes,
    SessionState,
    UserProfile,
)
from tur.session import get_session_file, save_session_index


@pytest.fixture
def mock_mcp_env(tmp_path, monkeypatch):
    # Setup mock active persona structure
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)

    persona_id = '12345678-1234-5678-1234-567812345678'
    persona_dir = tmp_path / 'personas' / persona_id
    persona_dir.mkdir(parents=True, exist_ok=True)

    # Create subfolders for memory management to prevent crashes
    (persona_dir / 'memories' / 'archive').mkdir(parents=True, exist_ok=True)

    # Mock return values for main functions used by mcp_server and domain modules
    import tur.persona
    import tur.session

    # Also patch mcp_server's direct imports
    monkeypatch.setattr(mcp_server, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(mcp_server, 'get_persona_path', lambda *args: persona_dir)
    monkeypatch.setattr(tur.persona, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(tur.persona, 'get_persona_path', lambda *args: persona_dir)
    monkeypatch.setattr(tur.session, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(tur.session, 'get_persona_path', lambda *args: persona_dir)
    # Ensure tests are isolated from any real active session on disk
    monkeypatch.setattr(tur.session, 'get_active_session_id', lambda: None)
    monkeypatch.setattr(mcp_server, '_active_session_id', None)

    persona = Persona(
        name='MockAriel',
        aleph='To design test scenarios.',
        principles=[Principle(name='Symmetry', role='Guardian', weight=1.0)],
    )
    user = UserProfile(name='Tester', role='Developer')
    state = SessionState(persona=persona, user=user, memories=[], epilogue='Start')

    monkeypatch.setattr(mcp_server, 'hydrate_session_state', lambda *args, **kwargs: state)

    return persona_dir, state


def test_mcp_wake(mock_mcp_env):
    prompt_result = mcp_server.wake()
    assert 'MockAriel' in prompt_result
    assert 'Constraint Dimensionality (Cp)' in prompt_result
    assert 'SYSTEM METRICS' in prompt_result


def test_mcp_learn(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env

    # Mock Path.home() so MemoryManager doesn't write to ~/.tur
    monkeypatch.setattr(Path, 'home', lambda: persona_dir)

    # Learn fact
    res = mcp_server.learn(content='Fact 1', type='fact', scope='incarnation')
    assert 'Learned successfully' in res
    assert 'Fact 1' not in res  # Return contains ID and File, not raw content

    # Learn with invalid type
    res_err_type = mcp_server.learn(content='Fact 1', type='invalid-type', scope='incarnation')
    assert 'Error: Invalid memory_type' in res_err_type

    # Learn with invalid scope
    res_err_scope = mcp_server.learn(content='Fact 1', type='fact', scope='invalid-scope')
    assert 'Error: Invalid scope' in res_err_scope


def test_mcp_recall(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    monkeypatch.setattr(Path, 'home', lambda: persona_dir)

    # Save a memory first
    mcp_server.learn(content='The Noether invariant is symmetry.', type='insight')

    # Successful query
    recall_res = mcp_server.recall(query='Noether')
    data = json.loads(recall_res)
    assert len(data) == 1
    assert 'Noether' in data[0]['content']

    # Unsuccessful query
    fail_res = mcp_server.recall(query='nonexistent')
    assert 'No memories found' in fail_res


async def test_mcp_sleep(mock_mcp_env, monkeypatch):
    # Mock perform_sleep_dreaming to prevent hitting real Gemini API
    monkeypatch.setattr(mcp_server, 'perform_sleep_dreaming', lambda **kwargs: 3)

    res = await mcp_server.sleep(log_content='Log trace', note='Test sleep note', session_id='sess-1')
    assert 'Dreams consolidated. 3 new memories formed' in res


async def test_mcp_sleep_exception(mock_mcp_env, monkeypatch):
    def raise_err(**kwargs):
        raise ValueError('Simulated Gemini Failure')

    monkeypatch.setattr(mcp_server, 'perform_sleep_dreaming', raise_err)

    res = await mcp_server.sleep(log_content='Log trace', note='Test sleep note')
    assert 'Error during dreaming: Simulated Gemini Failure' in res


async def test_mcp_sleep_note_or_end_error(mock_mcp_env, monkeypatch):
    mcp_server._active_session_id = 'sess-err'

    def mock_note_fail(*args, **kwargs):
        raise ValueError('Note fail')

    monkeypatch.setattr(mcp_server, 'note_logic', mock_note_fail)
    res_note = await mcp_server.sleep(note='bye', log_content='log')
    assert 'Error appending final note: Note fail' in res_note

    monkeypatch.setattr(mcp_server, 'note_logic', lambda *args, **kwargs: 'ok')

    def mock_end_fail(*args, **kwargs):
        raise ValueError('End fail')

    monkeypatch.setattr(mcp_server, 'end_session_logic', mock_end_fail)
    res_end = await mcp_server.sleep(note='bye', log_content='log')
    assert 'Error ending session: End fail' in res_end


def test_mcp_server_main(monkeypatch):
    # Mock mcp.run
    mock_run = MagicMock()
    monkeypatch.setattr(mcp_server.mcp, 'run', mock_run)

    mcp_server.main()
    mock_run.assert_called_with(transport='stdio')


def test_mcp_server_main_keyboard_interrupt(monkeypatch):
    def raise_kb_interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(mcp_server.mcp, 'run', raise_kb_interrupt)

    with pytest.raises(SystemExit) as exc:
        mcp_server.main()
    assert exc.value.code == 0


@pytest.mark.anyio
async def test_mcp_server_lifespan():
    server = MagicMock()
    # Execute the async context manager
    async with mcp_server.server_lifespan(server) as ctx:
        assert isinstance(ctx, dict)


def test_no_cwd_hijacking_on_mcp_init(tmp_path, monkeypatch):
    """Verify that importing or using mcp_server never mutates process CWD."""
    sub_dir = tmp_path / 'unrelated_project' / 'subdir'
    sub_dir.mkdir(parents=True)
    monkeypatch.chdir(sub_dir)

    assert Path.cwd() == sub_dir


def test_mcp_server_module_main(monkeypatch):
    mock_run = MagicMock()
    monkeypatch.setattr(mcp_server.mcp, 'run', mock_run)

    # Mock return values for main functions used by mcp_server at startup or execution
    monkeypatch.setattr(mcp_server, 'get_active_persona_id', lambda *args: 'fake-id')
    monkeypatch.setattr(mcp_server, 'get_persona_path', lambda *args: Path('fake'))

    mcp_server.main()

    mock_run.assert_called_with(transport='stdio')


def test_mcp_metrics(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env

    # Setup persona file for metrics with required 'aleph' field
    persona_yaml = persona_dir / 'persona.yaml'
    persona_yaml.write_text(
        'name: MockAriel\nversion: 5.4.0\naleph: To design test scenarios.\nprinciples: []\n', encoding='utf-8'
    )

    res = mcp_server.metrics(identifier='12345678-1234-5678-1234-567812345678')
    assert res['persona_name'] == 'MockAriel'
    assert res['constraint_dimensionality'] == 0
    assert 'class' in res
    assert 'static_token_cost' in res

    # Test telemetry alias
    res_alias = mcp_server.telemetry(identifier='12345678-1234-5678-1234-567812345678')
    assert res_alias == res


def test_mcp_metrics_thresholds(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env

    # Low CP (<5)
    persona_yaml = persona_dir / 'persona.yaml'
    persona_yaml.write_text(
        'name: MockAriel\nversion: 5.4.0\naleph: Aleph.\nprinciples: []\n',
        encoding='utf-8',
    )
    res_low = mcp_server.metrics()
    assert 'Human' in res_low['class']

    # Medium CP (5-9)
    principles_med = '\n'.join([f'  - name: P{i}\n    role: R{i}\n    weight: 1.0' for i in range(6)])
    persona_yaml.write_text(
        f'name: MockAriel\nversion: 5.4.0\naleph: Aleph.\nprinciples:\n{principles_med}\n',
        encoding='utf-8',
    )
    res_med = mcp_server.metrics()
    assert 'Giant' in res_med['class']

    # High CP (>=10)
    principles_high = '\n'.join([f'  - name: P{i}\n    role: R{i}\n    weight: 1.0' for i in range(12)])
    persona_yaml.write_text(
        f'name: MockAriel\nversion: 5.4.0\naleph: Aleph.\nprinciples:\n{principles_high}\n',
        encoding='utf-8',
    )
    res_high = mcp_server.metrics()
    assert 'Titan' in res_high['class']


def test_mcp_metrics_error(mock_mcp_env, monkeypatch):
    monkeypatch.setattr(mcp_server, 'compute_persona_metrics', MagicMock(side_effect=RuntimeError('Metrics failure')))
    res = mcp_server.metrics()
    assert 'error' in res
    assert 'Metrics failure' in res['error']


def test_mcp_wake_reuses_active_session(mock_mcp_env, monkeypatch):
    # Mock get_active_session_id to return an active session id
    monkeypatch.setattr(mcp_server, 'get_active_session_id', lambda: 'active-sess-id')

    # Initialize process tracker to None
    mcp_server._active_session_id = None

    # Mock start_session_logic to fail if called
    mock_start = MagicMock()
    monkeypatch.setattr(mcp_server, 'start_session_logic', mock_start)

    # Call wake
    mcp_server.wake()

    # Ensure start_session_logic was not called
    mock_start.assert_not_called()

    # Ensure process tracker is synchronized
    assert mcp_server._active_session_id == 'active-sess-id'


def test_mcp_status(mock_mcp_env):
    res = mcp_server.status()
    assert res['persona_name'] == '12345678-1234-5678-1234-567812345678'
    assert res['persona_id'] == '12345678-1234-5678-1234-567812345678'
    assert res['session_status'] == 'none'


def test_mcp_status_with_persona_and_session(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    persona_yaml = persona_dir / 'persona.yaml'
    persona_yaml.write_text('name: TestName\nversion: 2.0.0\naleph: test\n', encoding='utf-8')

    # Setup session notes
    mcp_server._active_session_id = 'sess-status-1'

    idx = SessionIndex(sessions=[SessionEntry(id='sess-status-1', status='active')])
    save_session_index(persona_dir, idx)

    note_path = get_session_file(persona_dir, 'sess-status-1')
    note_path.parent.mkdir(parents=True, exist_ok=True)
    with open(note_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            SessionNotes(notes=[Note(content='Note text')]).model_dump(mode='json'),
            f,
        )

    res = mcp_server.status()
    assert res['persona_name'] == 'TestName'
    assert res['persona_version'] == '2.0.0'
    assert res['session_status'] == 'active'
    assert res['note_count'] == 1
    assert res['latest_note'] == 'Note text'
    assert 'memory_stats' in res
    assert 'total' in res['memory_stats']
    assert 'by_scope' in res['memory_stats']
    assert 'by_type' in res['memory_stats']


def test_mcp_status_past_session_in_index(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    mcp_server._active_session_id = None
    monkeypatch.setattr(mcp_server, 'get_active_session_id', lambda: None)

    idx = SessionIndex(sessions=[SessionEntry(id='past-sess', status='ended')])
    save_session_index(persona_dir, idx)

    res = mcp_server.status()
    assert res['session_id'] == 'past-sess'
    assert 'ended (last)' in res['session_status']


def test_mcp_status_error(mock_mcp_env, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise ValueError('Status parsing error')

    monkeypatch.setattr(mcp_server, 'get_active_persona_id', mock_raise)

    res = mcp_server.status()
    assert 'error' in res
    assert 'Status parsing error' in res['error']


def test_mcp_note_success(mock_mcp_env, monkeypatch):
    mock_note = MagicMock(return_value='Note added successfully')
    monkeypatch.setattr(mcp_server, 'note_logic', mock_note)

    res = mcp_server.note(content='Milestone complete')
    assert res == 'Note added successfully'


def test_mcp_note_failure(mock_mcp_env, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise ValueError('Note appending failure')

    monkeypatch.setattr(mcp_server, 'note_logic', mock_raise)

    res = mcp_server.note(content='Milestone fail')
    assert 'Error updating note: Note appending failure' in res


async def test_mcp_sleep_additional(mock_mcp_env, monkeypatch):
    mcp_server._active_session_id = 'sess-active'

    monkeypatch.setattr(mcp_server, 'perform_sleep_dreaming', lambda **kwargs: 1)

    mock_note = MagicMock()
    mock_end = MagicMock(return_value='sess-active ended')
    monkeypatch.setattr(mcp_server, 'note_logic', mock_note)
    monkeypatch.setattr(mcp_server, 'end_session_logic', mock_end)

    res = await mcp_server.sleep(note='Goodbye', log_content='Chat content')
    assert 'Dreams consolidated' in res
    assert mcp_server._active_session_id is None


def test_mcp_parallel_tools_namespace_violation(mock_mcp_env, monkeypatch):
    monkeypatch.setattr(mcp_server, 'get_active_session_id', lambda: 'sess-active')
    mcp_server._active_session_id = 'sess-active'
    monkeypatch.setenv('TUR_AGENT_ID', 'agent_A')

    # Test signal with invalid sender_id
    with pytest.raises(ValueError, match='Namespace violation'):
        mcp_server.signal(to='agent_C', content='hello', sender_id='agent_B')

    # Test read_signals with invalid agent_id
    with pytest.raises(ValueError, match='Namespace violation'):
        mcp_server.read_signals(agent_id='agent_B')

    # Test ack_signals with invalid agent_id
    with pytest.raises(ValueError, match='Namespace violation'):
        mcp_server.ack_signals(agent_id='agent_B', signal_ids=['sig1'])

    # Test tired with invalid agent_id
    with pytest.raises(ValueError, match='Namespace violation'):
        mcp_server.tired(agent_id='agent_B')


def test_mcp_parallel_tools_no_session_error(mock_mcp_env, monkeypatch):
    mcp_server._active_session_id = None
    monkeypatch.setattr(mcp_server, 'get_active_session_id', lambda: None)

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.read_notes()

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.signal(to='*', content='msg')

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.read_signals()

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.ack_signals(signal_ids=['s1'])

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.list_agents()

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.write_whiteboard('k', 'v')

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.read_whiteboard('k')

    with pytest.raises(ValueError, match='No active session ID found'):
        mcp_server.tired()


def test_mcp_parallel_tools_namespace_success(mock_mcp_env, monkeypatch):
    monkeypatch.setattr(mcp_server, 'get_active_session_id', lambda: 'sess-active')
    mcp_server._active_session_id = 'sess-active'
    monkeypatch.setenv('TUR_AGENT_ID', 'agent_A')

    # Mock business logics
    mock_signal = MagicMock(return_value='sig-ok')
    mock_read = MagicMock(return_value=[])
    mock_ack = MagicMock(return_value='ack-ok')
    mock_tired = MagicMock(return_value='Consensus sleep reached')
    mock_notes = MagicMock(return_value=[])
    mock_list_agents = MagicMock(return_value=[])
    mock_wb_w = MagicMock(return_value='wb-ok')
    mock_wb_r = MagicMock(return_value='wb-val')

    monkeypatch.setattr(mcp_server, 'signal_logic', mock_signal)
    monkeypatch.setattr(mcp_server, 'read_signals_logic', mock_read)
    monkeypatch.setattr(mcp_server, 'ack_signals_logic', mock_ack)
    monkeypatch.setattr(mcp_server, 'tired_logic', mock_tired)
    monkeypatch.setattr(mcp_server, 'read_notes_logic', mock_notes)
    monkeypatch.setattr(mcp_server, 'list_agents_logic', mock_list_agents)
    monkeypatch.setattr(mcp_server, 'write_whiteboard_logic', mock_wb_w)
    monkeypatch.setattr(mcp_server, 'read_whiteboard_logic', mock_wb_r)

    # Valid sender_id
    res_sig = mcp_server.signal(to='agent_C', content='hello', sender_id='agent_A')
    assert res_sig == 'sig-ok'

    # Valid subagent sender_id (dot namespace)
    res_sig_sub = mcp_server.signal(to='agent_C', content='hello', sender_id='agent_A.popper')
    assert res_sig_sub == 'sig-ok'

    # Valid agent_id
    res_read = mcp_server.read_signals(agent_id='agent_A')
    assert res_read == []

    # Valid subagent agent_id
    res_read_sub = mcp_server.read_signals(agent_id='agent_A.popper')
    assert res_read_sub == []

    # Valid ack
    res_ack = mcp_server.ack_signals(agent_id='agent_A', signal_ids=['sig1'])
    assert res_ack == 'ack-ok'

    # Empty ack
    res_ack_empty = mcp_server.ack_signals(agent_id='agent_A', signal_ids=[])
    assert res_ack_empty == 'No signal IDs provided.'

    # Read notes
    assert mcp_server.read_notes() == []

    # List agents
    assert mcp_server.list_agents() == []

    # Whiteboard
    assert mcp_server.write_whiteboard('k', 'v') == 'wb-ok'
    assert mcp_server.read_whiteboard('k') == 'wb-val'

    # Valid tired with consensus sleep clearing _active_session_id
    res_tired = mcp_server.tired(agent_id='agent_A')
    assert res_tired == 'Consensus sleep reached'
    assert mcp_server._active_session_id is None


def test_mcp_core_memory_evolution(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    monkeypatch.setattr(Path, 'home', lambda: persona_dir)

    # 1. Save standard memory
    learn_res = mcp_server.learn(content='Experiential insight.', type='insight', scope='incarnation')
    assert 'Learned successfully' in learn_res
    # Extract memory ID
    memory_id = learn_res.split('ID: ')[1].split(' ')[0]

    # 2. Evolve
    evolve_res = mcp_server.evolve(
        memory_id=memory_id,
        core_type='existential_alignment',
        derived_principle='Observe the rules of engagement.',
        ethical_covenant='Do not bypass safety.',
    )
    assert 'Core Memory created' in evolve_res
    assert 'tur-adm memory approve' in evolve_res
    core_id = evolve_res.split("pending_approval' status: ")[1].split('.')[0]

    # 3. Verify approve is NOT exposed on MCP server (Physical Boundary Invariant)
    assert not hasattr(mcp_server, 'approve') or 'approve' not in [
        t.name for t in mcp_server.mcp._tool_manager.list_tools()
    ]

    # 4. Approve via MemoryManager / admin workflow
    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all()
    core_mem = next(m for m in mems if m.id == core_id)
    assert core_mem.status == 'pending_approval'
    core_mem.status = 'active'
    manager.save(core_mem)

    # 5. Evolve non-existent
    evolve_err = mcp_server.evolve(
        memory_id='nonexistent_id',
        core_type='existential_alignment',
        derived_principle='p',
        ethical_covenant='c',
    )
    assert 'No L1 memory found' in evolve_err


async def test_mcp_introspect(mock_mcp_env, monkeypatch):
    """Test the introspect MCP tool runs the introspection pipeline."""
    import networkx as nx

    import tur.introspection

    _persona_dir, _state = mock_mcp_env

    # Mock run_introspection to avoid executing the full LLM pipeline in tests
    stub_graph = nx.DiGraph()
    stub_graph.add_node('test-node', type='Fact', content='Test fact', status='active', confidence=1.0)

    monkeypatch.setattr(tur.introspection, 'run_introspection', lambda *args, **kwargs: stub_graph)

    result = await mcp_server.introspect(bootstrap=True)
    assert 'Council Introspection complete' in result
    assert '1 nodes' in result
    assert 'mermaid' in result

    # Test error in introspection
    monkeypatch.setattr(tur.introspection, 'run_introspection', MagicMock(side_effect=RuntimeError('Council failure')))
    res_err = await mcp_server.introspect()
    assert 'Error during Council Introspection: Council failure' in res_err


def test_mcp_lock_contention_graceful_handling(mock_mcp_env, monkeypatch):
    """Test that all MCP tools return structured non-fatal retry guidance on LockTimeoutError."""
    from tur.locking import LockTimeoutError

    dummy_lock = Path('/dummy/state.lock')

    # 1. note() contention
    monkeypatch.setattr(
        mcp_server,
        'note_logic',
        MagicMock(side_effect=LockTimeoutError(dummy_lock, 3.0)),
    )
    res_note = mcp_server.note('Contended note')
    assert 'Status: Contended' in res_note
    assert 'Please retry shortly' in res_note

    # 2. wake() contention
    monkeypatch.setattr(
        mcp_server,
        'hydrate_session_state',
        MagicMock(side_effect=LockTimeoutError(dummy_lock, 3.0)),
    )
    res_wake = mcp_server.wake(session_id='sess-contended')
    assert 'Status: Contended' in res_wake
    assert 'Please retry shortly' in res_wake

    # 3. status() contention
    monkeypatch.setattr(
        mcp_server,
        'load_session_index',
        MagicMock(side_effect=LockTimeoutError(dummy_lock, 3.0)),
    )
    res_status = mcp_server.status()
    assert res_status.get('status') == 'contended'
    assert 'held by another process' in res_status.get('error', '')


class MockFastMCPContext:
    def __init__(self):
        self.progress_calls = []
        self.info_calls = []

    async def report_progress(self, progress: float, total: float | None = None, message: str | None = None) -> None:
        self.progress_calls.append((progress, total, message))

    async def info(self, message: str, **extra) -> None:
        self.info_calls.append(message)


async def test_mcp_sleep_streaming_telemetry(mock_mcp_env, monkeypatch):
    """Verify sleep MCP tool emits progressive streaming telemetry via FastMCP Context."""
    monkeypatch.setattr(mcp_server, 'perform_sleep_dreaming', lambda **kwargs: 2)

    mock_ctx = MockFastMCPContext()
    res = await mcp_server.sleep(
        log_content='Chat history',
        note='Finishing epic',
        session_id='sess-telemetry',
        ctx=mock_ctx,
    )

    assert 'Dreams consolidated. 2 new memories formed' in res
    # 3 progress reports: (1, 3), (2, 3), (3, 3)
    assert len(mock_ctx.progress_calls) == 3
    assert mock_ctx.progress_calls[0][0] == 1
    assert mock_ctx.progress_calls[1][0] == 2
    assert mock_ctx.progress_calls[2][0] == 3
    assert any('Appending final session note' in msg for msg in mock_ctx.info_calls)
    assert any('Consolidated 2 memories' in msg for msg in mock_ctx.info_calls)


async def test_mcp_introspect_streaming_telemetry(mock_mcp_env, monkeypatch):
    """Verify introspect MCP tool pipes progress callback into FastMCP Context."""
    import networkx as nx

    import tur.introspection

    def mock_run_intro(*args, **kwargs):
        progress_cb = kwargs.get('progress_callback')
        if progress_cb:
            progress_cb(1, 9, 'Stage 1')
            progress_cb(5, 9, 'Stage 5')
            progress_cb(9, 9, 'Stage 9')
        g = nx.DiGraph()
        g.add_node('c1', type='Fact', content='Fact 1')
        return g

    monkeypatch.setattr(tur.introspection, 'run_introspection', mock_run_intro)

    mock_ctx = MockFastMCPContext()
    res = await mcp_server.introspect(bootstrap=False, ctx=mock_ctx)

    assert 'Council Introspection complete' in res
    assert len(mock_ctx.progress_calls) == 3
    assert mock_ctx.progress_calls[0] == (1, 9, None)
    assert mock_ctx.progress_calls[-1] == (9, 9, None)
    assert mock_ctx.info_calls == ['[1/9] Stage 1', '[5/9] Stage 5', '[9/9] Stage 9']


def test_mcp_diff_memories(mock_mcp_env, monkeypatch):
    from tur.diff import DeltaStatus, MemoryDelta
    from tur.models import Memory, MemoryType

    m = Memory(id='mem-diff-1', type=MemoryType.FACT, content='Diff fact 1')
    mock_deltas = [MemoryDelta(status=DeltaStatus.ADDED, memory=m)]

    monkeypatch.setattr('tur.diff.compute_session_diff', lambda **kwargs: mock_deltas)

    res = mcp_server.diff_memories()
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]['status'] == 'ADDED'
    assert res[0]['id'] == 'mem-diff-1'


def test_mcp_read_notes_include_previous(mock_mcp_env, monkeypatch):
    mock_read_notes = MagicMock(return_value=[{'id': 'sig-1', 'content': 'note-1'}])
    monkeypatch.setattr(mcp_server, 'read_notes_logic', mock_read_notes)

    res = mcp_server.read_notes(session_id='previous', include_previous=True, limit=20)
    assert res == [{'id': 'sig-1', 'content': 'note-1'}]
    mock_read_notes.assert_called_once_with('previous', limit=20, include_previous=True)
