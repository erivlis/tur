import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from tur import persona, session
from tur.models import Memory, MemoryScope, MemoryType, Note, SessionEntry, SessionIndex, SessionNotes, SystemState


@pytest.fixture
def mock_session_workspace(tmp_path, monkeypatch):
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


def test_get_local_persona_dir_global(mock_session_workspace, monkeypatch):
    _tmp_path, _persona_id = mock_session_workspace
    # Set home so a path inside fake_home/.tur is detected as global
    global_path = Path.home() / '.tur' / 'personas' / 'Ariel'

    local_path = session.get_local_persona_dir(global_path)
    assert local_path == Path.cwd() / '.tur' / 'personas' / 'Ariel'


def test_load_session_index_corrupt(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Write corrupted sessions.yaml
    sessions_yaml = session.get_local_persona_dir(p_dir) / 'sessions.yaml'
    sessions_yaml.parent.mkdir(parents=True, exist_ok=True)
    sessions_yaml.write_text('invalid: yaml: : content', encoding='utf-8')

    idx = session.load_session_index(p_dir)
    assert len(idx.sessions) == 0


def test_get_active_session_id_env(mock_session_workspace, monkeypatch):
    monkeypatch.setenv('TUR_ACTIVE_SESSION_ID', 'env-sess-id')
    assert session.get_active_session_id() == 'env-sess-id'


def test_compile_session_notes_corrupt(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Create corrupted session file
    session_file = session.get_session_file(p_dir, 'sess-corrupt')
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text('invalid: yaml: : content', encoding='utf-8')

    notes = session.compile_session_notes(p_dir, 'sess-corrupt')
    assert notes == 'Status: Conserved. Aleph: Restored. Carry on, Lion.'


def test_compile_session_notes_none(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    notes = session.compile_session_notes(p_dir, None)
    assert notes == 'Status: Conserved. Aleph: Restored. Carry on, Lion.'


def test_hydrate_session_state_fallback(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Setup some ended sessions in the index but no active session in state.yaml
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': persona_id, 'active_session_id': None}, f)

    index = SessionIndex()
    # Add an old and a newer ended session entry
    now = datetime.now()
    entry1 = SessionEntry(id='old-sess', status='ended', updated_at=now - timedelta(days=1))
    entry2 = SessionEntry(id='new-sess', status='ended', updated_at=now)
    index.sessions = [entry1, entry2]
    session.save_session_index(p_dir, index)

    # Write a note to new-sess so compile_session_notes reads it
    new_sess_file = session.get_session_file(p_dir, 'new-sess')
    new_sess_file.parent.mkdir(parents=True, exist_ok=True)
    notes = SessionNotes(notes=[Note(timestamp=now, content='Latest ended session note content.')])
    with open(new_sess_file, 'w', encoding='utf-8') as f:
        yaml.dump(notes.model_dump(mode='json'), f)

    state = session.hydrate_session_state(persona_id)
    assert state.epilogue == 'Latest ended session note content.'


def test_hydrate_session_state_with_kg(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Add knowledge graph yaml
    kg_path = p_dir / 'knowledge_graph.yaml'
    kg_path.write_text('nodes: [1, 2]\nedges: []\n', encoding='utf-8')

    state = session.hydrate_session_state(persona_id)
    assert state.knowledge_graph == {'nodes': [1, 2], 'edges': []}

    # Test corrupted knowledge graph yaml gracefully ignored
    kg_path.write_text('corrupt: yaml: : : 123', encoding='utf-8')
    state_corrupt = session.hydrate_session_state(persona_id)
    assert state_corrupt.knowledge_graph is None


def test_start_session_logic_previous_seed(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Create previous session with a note
    prev_sess_file = session.get_session_file(p_dir, 'prev-sess')
    prev_sess_file.parent.mkdir(parents=True, exist_ok=True)
    notes = SessionNotes(notes=[Note(timestamp=datetime.now(), content='Inherited note content')])
    with open(prev_sess_file, 'w', encoding='utf-8') as f:
        yaml.dump(notes.model_dump(mode='json'), f)

    session.start_session_logic('new-sess', identifier=persona_id, previous_session_id='prev-sess')

    new_sess_file = session.get_session_file(p_dir, 'new-sess')
    with open(new_sess_file, encoding='utf-8') as f:
        new_notes_data = yaml.safe_load(f)
    new_notes = SessionNotes(**new_notes_data)
    assert len(new_notes.notes) == 1
    assert new_notes.notes[0].content == 'Inherited note content'


def test_start_session_logic_invalid_agent_id(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    with pytest.raises(ValueError, match='Invalid agent_id format'):
        session.start_session_logic('s1', agent_id='bad space id!', identifier=persona_id)


def test_start_session_logic_existing_update(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # Start it once
    session.start_session_logic('sess-id', identifier=persona_id)
    # Start it again to test updating the existing entry in the index
    session.start_session_logic('sess-id', identifier=persona_id)

    index = session.load_session_index(p_dir)
    assert len(index.sessions) == 1
    assert index.sessions[0].status == 'active'


def test_start_session_logic_no_state_yaml(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace

    # Delete state.yaml to trigger the create path
    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        state_path.unlink()

    session.start_session_logic('sess-id', identifier=persona_id)
    assert state_path.exists()


def test_end_session_logic_not_found(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    with pytest.raises(FileNotFoundError):
        session.end_session_logic('non-existent', identifier=persona_id)


def test_end_session_logic_success(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    session.start_session_logic('sess-id', identifier=persona_id)
    res = session.end_session_logic('sess-id', identifier=persona_id)
    assert 'ended successfully' in res

    index = session.load_session_index(p_dir)
    assert index.sessions[0].status == 'ended'


def test_note_logic_corrupt(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    session.start_session_logic('sess-id', identifier=persona_id)

    # Corrupt the session file
    session_file = session.get_session_file(p_dir, 'sess-id')
    session_file.write_text('invalid: yaml: : content', encoding='utf-8')

    # note_logic should handle the parsing exception and still write the new note
    res = session.note_logic('New note after corrupt', session_id='sess-id', identifier=persona_id)
    assert 'saved' in res


def test_note_logic_fallback_and_error(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)

    # No active session, no past sessions: should raise ValueError
    state_path = Path('.tur/state.yaml')
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump({'active_persona_id': persona_id, 'active_session_id': None}, f)

    with pytest.raises(ValueError) as exc:
        session.note_logic('Tether note', identifier=persona_id)
    assert 'No active session' in str(exc.value)

    # Now create a past ended session in index
    now = datetime.now()
    index = SessionIndex(sessions=[SessionEntry(id='ended-sess', status='ended', updated_at=now)])
    session.save_session_index(p_dir, index)

    # Also create the session file for ended-sess so note_logic can append to it
    sess_file = session.get_session_file(p_dir, 'ended-sess')
    sess_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sess_file, 'w', encoding='utf-8') as f:
        yaml.dump(SessionNotes(notes=[]).model_dump(mode='json'), f)

    # Calling note_logic with no active session should fall back to ended-sess
    res = session.note_logic('Fallback Tether note', identifier=persona_id)
    assert 'ended-sess' in res


def test_hydrate_session_state_with_cores(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)
    from tur.memory import MemoryManager

    manager = MemoryManager(base_dir=p_dir)

    # 1. Create a regular memory and a core memory
    mem_reg = Memory(
        timestamp=datetime(2026, 7, 12, 10, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Regular project memory.',
    )
    mem_core = Memory(
        timestamp=datetime(2026, 7, 12, 11, 0, 0),
        type=MemoryType.CORE,
        scope=MemoryScope.UNIVERSAL,
        content='ADHD cognitive scaffolding.',
        core_type='existential_alignment',
        derived_principle='Keep tasks highly visual and immediate.',
        ethical_covenant='Always present a structured visual plan.',
        status='active',
    )
    manager.save(mem_reg)
    manager.save(mem_core)

    # 2. Hydrate session state
    state = session.hydrate_session_state(persona_id)
    assert len(state.cores) == 1
    assert state.cores[0].derived_principle == 'Keep tasks highly visual and immediate.'
    assert len(state.memories) == 1
    assert state.memories[0].content == 'Regular project memory.'

    # 3. Compile prompt and check rendering
    from tur.compiler import compile_persona

    prompt = compile_persona(state)
    assert '## CORE AXIOMS & COVENANTS' in prompt
    assert 'Keep tasks highly visual and immediate.' in prompt
    assert 'Always present a structured visual plan.' in prompt


def test_db_retry_locked_and_timeout():
    attempts = 0

    @session.db_retry(max_retries=3, initial_delay=0.01, backoff_factor=1.5)
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise sqlite3.OperationalError('database is locked')
        return 'success'

    assert flaky_func() == 'success'
    assert attempts == 2

    # Timeout failure
    @session.db_retry(max_retries=2, initial_delay=0.01, backoff_factor=1.0)
    def always_locked():
        raise sqlite3.OperationalError('database is locked')

    with pytest.raises(sqlite3.OperationalError):
        always_locked()


def test_signal_logic_invalid_ids_and_ratelimit(mock_session_workspace):
    _tmp_path, persona_id = mock_session_workspace
    session.start_session_logic('sess-sig', identifier=persona_id)

    # Invalid sender
    with pytest.raises(ValueError, match='Invalid sender ID'):
        session.signal_logic('sess-sig', sender='invalid space sender', recipient='agent_1', content='test')

    # Invalid recipient
    with pytest.raises(ValueError, match='Invalid recipient ID'):
        session.signal_logic('sess-sig', sender='agent_1', recipient='invalid space recip', content='test')

    # Ratelimit: send 10 messages, 11th should raise
    for i in range(10):
        session.signal_logic('sess-sig', sender='agent_1', recipient='agent_2', content=f'msg {i}')

    with pytest.raises(ValueError, match='RateLimitError'):
        session.signal_logic('sess-sig', sender='agent_1', recipient='agent_2', content='msg 11')


def test_tired_logic_staged_dreaming_consensus(mock_session_workspace, monkeypatch):
    _tmp_path, persona_id = mock_session_workspace
    session.start_session_logic('sess-tired', agent_id='agent_1', identifier=persona_id)
    session.start_session_logic('sess-tired', agent_id='agent_2', identifier=persona_id)

    # Agent 1 calls tired with staged memories -> should be in standby since agent_2 is active
    staged_payload = json.dumps(
        [{'type': 'fact', 'scope': 'incarnation', 'tags': ['test'], 'content': 'Staged fact 1'}]
    )
    monkeypatch.setattr('tur.dreaming.stage_sleep_dreaming', lambda *args, **kwargs: staged_payload)

    res1 = session.tired_logic('sess-tired', agent_id='agent_1', transcript='agent 1 log')
    assert 'Standby mode active' in res1

    # Agent 2 calls tired with dream error simulation
    def raise_dream_error(*args, **kwargs):
        raise RuntimeError('Dream stage error')

    monkeypatch.setattr('tur.dreaming.stage_sleep_dreaming', raise_dream_error)

    # Agent 2 calls tired -> now consensus reached and session ends
    res2 = session.tired_logic('sess-tired', agent_id='agent_2', transcript='agent 2 log')
    assert 'Consensus sleep reached' in res2
    assert 'Consolidated 1 memories' in res2
