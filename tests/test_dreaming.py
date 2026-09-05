from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from tur import persona, session
from tur.memory import dreaming


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    # Setup directories
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    # Fake persona index
    persona_id_1 = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    index_data = {'personas': [{'id': persona_id_1, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    (personas_dir / persona_id_1 / 'memories' / 'archive').mkdir(parents=True)

    persona_1_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
    }
    with open(personas_dir / persona_id_1 / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_1_yaml, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    return tmp_path, persona_id_1


def test_perform_sleep_dreaming(mock_workspace, monkeypatch):
    # Set fake Gemini API Key
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-key')

    # Mock google-genai Client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        '{"memories": [{"type": "fact", "content": "Pytest is fast", "scope": "incarnation", "tags": ["test"]}]}'
    )
    mock_client.models.generate_content.return_value = mock_response

    # Monkeypatch the Client to return our mocked client
    from google import genai

    monkeypatch.setattr(genai, 'Client', lambda api_key: mock_client)

    count = dreaming.perform_sleep_dreaming(log_content='User: hello', active_id='7544202e-92f5-40ce-adfb-e4b0eae6c262')
    assert count == 1

    # Verify the memory was saved in the state
    state = session.hydrate_session_state('7544202e-92f5-40ce-adfb-e4b0eae6c262')
    assert len(state.memories) == 1
    assert state.memories[0].content == 'Pytest is fast'


def test_perform_sleep_dreaming_missing_api_key(mock_workspace, monkeypatch):
    from tur.models import HarnessDelegationError

    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('TUR_LLM_API_KEY', raising=False)
    with pytest.raises(HarnessDelegationError) as exc:
        dreaming.perform_sleep_dreaming(log_content='User: hello', active_id='7544202e-92f5-40ce-adfb-e4b0eae6c262')
    assert '# TUR DELEGATION: Session Epilogue & Memory Extraction Request' in exc.value.prompt
    assert 'Boundary Invariant' in exc.value.prompt
    assert 'tur sleep --commit' in exc.value.prompt
    assert 'Memory Extraction Principles & Scoping Rules' in exc.value.prompt
    assert 'Subagent Execution (Recommended)' in exc.value.prompt
