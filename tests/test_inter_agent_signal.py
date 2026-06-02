import threading
from pathlib import Path

import pytest

from tur import session


@pytest.fixture
def mock_signal_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    p_dir = personas_dir / persona_id
    p_dir.mkdir(parents=True)
    (p_dir / 'memories' / 'archive').mkdir(parents=True)

    persona_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
    }
    import yaml

    with open(p_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_yaml, f)

    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    state_data = {'active_persona_id': persona_id}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    return tmp_path, persona_id


def test_db_setup_and_wal_mode(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_wal_test'
    db_path = session.get_session_db(session_id)
    assert not db_path.exists()

    conn = session.get_db_connection(session_id)
    session.init_db(conn)

    # Query pragma journal_mode to verify WAL is active
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode;')
    mode = cursor.fetchone()[0]
    assert mode.lower() == 'wal'
    conn.close()


def test_agent_registration_and_conflict(mock_signal_workspace, monkeypatch):
    _, _ = mock_signal_workspace
    session_id = 'sess_reg_test'

    # Start session as agent A
    res = session.start_session_logic(session_id, agent_id='agent_A', harness_conversation_id='conv_1')
    assert "started successfully for agent 'agent_A'" in res

    # Verify registration in database
    conn = session.get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute("SELECT harness, status, run_token FROM agents WHERE id = 'agent_A'")
    row = cursor.fetchone()
    assert row is not None
    assert row['status'] == 'active'
    stored_token = row['run_token']
    conn.close()

    # Attempt to register identical agent with same run_token (allowed, refresh heartbeat)
    monkeypatch.setenv('TUR_RUN_TOKEN', stored_token)
    res2 = session.start_session_logic(session_id, agent_id='agent_A', harness_conversation_id='conv_1')
    assert 'started successfully' in res2

    # Attempt to register identical agent with DIFFERENT run_token (ConflictError)
    monkeypatch.setenv('TUR_RUN_TOKEN', 'different_token')
    with pytest.raises(ValueError) as exc:
        session.start_session_logic(session_id, agent_id='agent_A', harness_conversation_id='conv_1')
    assert 'ConflictError' in str(exc.value)


def test_agent_registration_takeover_reclaim(mock_signal_workspace, monkeypatch):
    _, _ = mock_signal_workspace
    session_id = 'sess_takeover'

    # Register agent A
    session.start_session_logic(session_id, agent_id='agent_A')

    # Mock heartbeat to be stale (> 15 seconds)
    conn = session.get_db_connection(session_id)
    with conn:
        conn.execute("UPDATE agents SET last_heartbeat = datetime('now', '-20 seconds') WHERE id = 'agent_A'")
    conn.close()

    # Overwrite environment run token
    monkeypatch.setenv('TUR_RUN_TOKEN', 'token_reclaimed')
    # Should reclaim/takeover without ConflictError
    res = session.start_session_logic(session_id, agent_id='agent_A')
    assert "started successfully for agent 'agent_A'" in res


def test_directed_and_broadcast_signals(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_signal_test'

    session.start_session_logic(session_id, agent_id='agent_A')
    session.start_session_logic(session_id, agent_id='agent_B')

    # Send directed signal A -> B
    sig_id = session.signal_logic(session_id, sender='agent_A', recipient='agent_B', content='Hello B', type_='inform')

    # Agent A peeks its inbox -> should find 0 signals
    signals_a = session.read_signals_logic(session_id, agent_id='agent_A', unread_only=True)
    assert len(signals_a) == 0

    # Agent B peeks its inbox -> should find 1 signal
    signals_b = session.read_signals_logic(session_id, agent_id='agent_B', unread_only=True)
    assert len(signals_b) == 1
    assert signals_b[0]['content'] == 'Hello B'
    assert signals_b[0]['sender'] == 'agent_A'

    # Ack signal by agent B
    session.ack_signals_logic(session_id, agent_id='agent_B', signal_ids=[sig_id])

    # Agent B peeks again -> should find 0 unread
    assert len(session.read_signals_logic(session_id, agent_id='agent_B', unread_only=True)) == 0


def test_broadcast_join_table_isolation(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_broadcast'

    session.start_session_logic(session_id, agent_id='agent_A')
    session.start_session_logic(session_id, agent_id='agent_B')

    # Send broadcast note
    sig_id = session.signal_logic(session_id, sender='agent_A', recipient='*', content='Broadcast message')

    # Agent A peeks (recipient matches wildcard)
    signals_a = session.read_signals_logic(session_id, agent_id='agent_A', unread_only=True)
    assert len(signals_a) == 1

    # Agent B peeks
    signals_b = session.read_signals_logic(session_id, agent_id='agent_B', unread_only=True)
    assert len(signals_b) == 1

    # Agent A acknowledges it
    session.ack_signals_logic(session_id, agent_id='agent_A', signal_ids=[sig_id])

    # Agent A unread is now empty
    assert len(session.read_signals_logic(session_id, agent_id='agent_A', unread_only=True)) == 0

    # Agent B unread STILL HAS the broadcast (isolation via signal_reads join table!)
    assert len(session.read_signals_logic(session_id, agent_id='agent_B', unread_only=True)) == 1


def test_session_whiteboard(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_whiteboard'

    session.start_session_logic(session_id, agent_id='agent_A')

    # Write key
    session.write_whiteboard_logic(session_id, key='coord', value='X=10, Y=20', updated_by='agent_A')

    # Read key
    val = session.read_whiteboard_logic(session_id, key='coord')
    assert val == 'X=10, Y=20'

    # Read missing key
    assert session.read_whiteboard_logic(session_id, key='missing') is None


def test_staged_dreaming_consensus_sleep(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_tired'

    # Start A and B
    session.start_session_logic(session_id, agent_id='agent_A')
    session.start_session_logic(session_id, agent_id='agent_B')

    # Agent A tired: standby mode (since B is active)
    mock_transcript = 'Agent A chat log notes.'
    res_a = session.tired_logic(session_id, agent_id='agent_A', transcript=mock_transcript)
    assert 'Standby mode active' in res_a

    # Verify A status is idle and memories are staged
    conn = session.get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM agents WHERE id = 'agent_A'")
    assert cursor.fetchone()['status'] == 'idle'
    cursor.execute("SELECT COUNT(*) as count FROM staged_memories WHERE agent_id = 'agent_A'")
    assert cursor.fetchone()['count'] == 1
    conn.close()

    # Agent B tired: triggers consensus sleep since no other active agents remain
    res_b = session.tired_logic(session_id, agent_id='agent_B', transcript='Agent B log content.')
    assert 'Consensus sleep reached' in res_b

    # Verify session index status is ended

    from tur import persona

    p_dir = persona.get_persona_path('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    idx = session.load_session_index(p_dir)
    sess_entry = next((s for s in idx.sessions if s.id == session_id), None)
    assert sess_entry is not None
    assert sess_entry.status == 'ended'


def test_windows_file_locking_concurrency(mock_signal_workspace):
    _, _ = mock_signal_workspace
    session_id = 'sess_concurrency'

    # Start session for 5 distinct agents to bypass rate limits
    for t in range(5):
        session.start_session_logic(session_id, agent_id=f'agent_{t}')

    errors = []

    def writer_thread(tid):
        sender_id = f'agent_{tid}'
        try:
            for i in range(5):
                session.signal_logic(
                    session_id=session_id, sender=sender_id, recipient='*', content=f'Message {i} from thread {tid}'
                )
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer_thread, args=(t,)) for t in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(errors) == 0, f'Write concurrency errors: {errors}'
