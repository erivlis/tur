import os
import sys
import pytest
import yaml
from pathlib import Path
from datetime import datetime, timedelta

from tur import session, persona
from tur.models import (
    SessionIndex, SessionEntry, SessionNotes, Note, SystemState,
    Memory, MemoryType, MemoryScope
)

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
        'principles': []
    }
    with open(p_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_yaml, f)

    index_data = {
        'personas': [
            {'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}
        ]
    }
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
    tmp_path, persona_id = mock_session_workspace
    # Set home so a path inside fake_home/.tur is detected as global
    global_path = Path.home() / '.tur' / 'personas' / 'Ariel'
    
    local_path = session.get_local_persona_dir(global_path)
    assert local_path == Path.cwd() / '.tur' / 'personas' / 'Ariel'

def test_load_session_index_corrupt(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
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
    tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)
    
    # Create corrupted session file
    session_file = session.get_session_file(p_dir, 'sess-corrupt')
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text('invalid: yaml: : content', encoding='utf-8')
    
    notes = session.compile_session_notes(p_dir, 'sess-corrupt')
    assert notes == 'Status: Conserved. Aleph: Restored. Carry on, Lion.'

def test_hydrate_session_state_fallback(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
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

def test_start_session_logic_previous_seed(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
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

def test_start_session_logic_existing_update(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)
    
    # Start it once
    session.start_session_logic('sess-id', identifier=persona_id)
    # Start it again to test updating the existing entry in the index
    session.start_session_logic('sess-id', identifier=persona_id)
    
    index = session.load_session_index(p_dir)
    assert len(index.sessions) == 1
    assert index.sessions[0].status == 'active'

def test_start_session_logic_no_state_yaml(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
    
    # Delete state.yaml to trigger the create path
    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        state_path.unlink()
        
    session.start_session_logic('sess-id', identifier=persona_id)
    assert state_path.exists()

def test_end_session_logic_not_found(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
    with pytest.raises(FileNotFoundError):
        session.end_session_logic('non-existent', identifier=persona_id)

def test_end_session_logic_success(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)
    
    session.start_session_logic('sess-id', identifier=persona_id)
    res = session.end_session_logic('sess-id', identifier=persona_id)
    assert 'ended successfully' in res
    
    index = session.load_session_index(p_dir)
    assert index.sessions[0].status == 'ended'

def test_note_logic_corrupt(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
    p_dir = persona.get_persona_path(persona_id)
    
    session.start_session_logic('sess-id', identifier=persona_id)
    
    # Corrupt the session file
    session_file = session.get_session_file(p_dir, 'sess-id')
    session_file.write_text('invalid: yaml: : content', encoding='utf-8')
    
    # note_logic should handle the parsing exception and still write the new note
    res = session.note_logic('New note after corrupt', session_id='sess-id', identifier=persona_id)
    assert 'saved' in res

def test_note_logic_fallback_and_error(mock_session_workspace):
    tmp_path, persona_id = mock_session_workspace
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
