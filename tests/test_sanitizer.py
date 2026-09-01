import os
from datetime import datetime
from pathlib import Path

import yaml
from typer.testing import CliRunner

from tur.cli.admin import app as admin_app
from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType, Note, SessionNotes
from tur.sanitizer import (
    COMMON_SECRET_PATTERNS,
    REDACTED_ENTROPY_REPLACEMENT,
    REDACTED_SECRET_REPLACEMENT,
    calculate_shannon_entropy,
    detect_high_entropy_tokens,
    is_sensitive,
    sanitize_text,
)
from tur.session import get_session_file, note_logic, start_session_logic

runner = CliRunner()


def test_shannon_entropy_calculation():
    # Empty string has 0 entropy
    assert calculate_shannon_entropy('') == 0.0

    # Low entropy for repetitive strings
    assert calculate_shannon_entropy('aaaaaaaaaaaaaaaaaaaa') == 0.0

    # High entropy for random strings
    high_rand = 'dGVzdF9zZWNyZXRfdG9rZW5faGlnaF9lbnRyb3B5XzEyMzQ1'
    assert calculate_shannon_entropy(high_rand) > 4.0


def test_detect_high_entropy_tokens():
    text = 'Here is normal text with simple words.'
    assert detect_high_entropy_tokens(text) == []

    secret_token = 'K9zX7pL2vM8qW4yR1tN0bC3vF6hJ9kL2'
    text_with_secret = f'Use this token: {secret_token} for auth.'
    detected = detect_high_entropy_tokens(text_with_secret, threshold=4.2)
    assert secret_token in detected


def test_sanitize_common_secret_patterns():
    # GitHub PAT
    gh_text = 'My token is ghp_123456789012345678901234567890123456 please keep safe'
    clean_gh, detected = sanitize_text(gh_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_gh
    assert 'ghp_123456789012345678901234567890123456' not in clean_gh
    assert len(detected) == 1

    # OpenAI Key
    oa_text = 'sk-123456789012345678901234567890123456789012345678'
    clean_oa, _ = sanitize_text(oa_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_oa

    # Google API Key
    google_text = 'AIzaSyD1234567890123456789012345678901'
    clean_google, _ = sanitize_text(google_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_google

    # AWS Access Key ID
    aws_text = 'Access key AKIAIOSFODNN7EXAMPLE for S3'
    clean_aws, _ = sanitize_text(aws_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_aws

    # Assignment pattern
    assign_text = "secret_key = 'abcdef1234567890abcdef1234567890'"
    clean_assign, _ = sanitize_text(assign_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_assign

    # PEM Private Key
    pem_text = '-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----'
    clean_pem, _ = sanitize_text(pem_text)
    assert REDACTED_SECRET_REPLACEMENT in clean_pem


def test_is_sensitive():
    assert not is_sensitive('A safe sentence describing the codebase architecture.')
    assert is_sensitive("api_key = 'secret1234567890abcdef1234567890'")
    assert is_sensitive('ghp_123456789012345678901234567890123456')


def test_memory_model_pre_ingest_sanitization():
    # Initializing a Memory with sensitive content should auto-sanitize before Merkle hash
    raw_content = 'Discovered key: ghp_123456789012345678901234567890123456 in env.'
    mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content=raw_content,
    )

    assert 'ghp_123456789012345678901234567890123456' not in mem.content
    assert REDACTED_SECRET_REPLACEMENT in mem.content
    assert mem.id != ''


def test_session_note_sanitization(tmp_path, monkeypatch):
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    ws = tmp_path / 'ws'
    ws.mkdir()
    monkeypatch.chdir(ws)

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    dot_tur = ws / '.tur'
    dot_tur.mkdir(parents=True, exist_ok=True)
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir(parents=True, exist_ok=True)

    index_data = {
        'personas': [
            {'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'},
        ]
    }
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    (personas_dir / persona_id / 'memories' / 'active').mkdir(parents=True, exist_ok=True)
    with open(personas_dir / persona_id / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'name': 'Ariel', 'version': '5.4.0'}, f)

    from tur.session import update_system_state

    update_system_state(active_persona_id=persona_id, reset_session=True)

    start_session_logic('sess_sanitize_test', identifier=persona_id)

    note_text = "Staging key set to api_key = 'supersecretkey1234567890'"
    note_logic(note_text, session_id='sess_sanitize_test', identifier=persona_id)

    notes_file = get_session_file(personas_dir / persona_id, 'sess_sanitize_test')
    assert notes_file.exists()
    content = notes_file.read_text(encoding='utf-8')
    assert 'supersecretkey1234567890' not in content
    assert REDACTED_SECRET_REPLACEMENT in content


def test_merkle_tombstone_redaction(tmp_path, monkeypatch):
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    persona_dir = fake_home / '.tur' / 'personas' / 'test_redact_uuid'
    manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 8, 30, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.UNIVERSAL,
        tags=['security', 'test'],
        content='Clean content before redaction.',
    )
    saved_path = manager.save(mem)
    original_id = mem.id

    # Verify integrity passes before redaction
    assert manager.verify_integrity() == []

    # Execute redaction
    redacted_path = manager.redact(original_id, reason='Security Policy EP-0143 Test')
    assert redacted_path.exists()
    assert redacted_path == saved_path

    # Check file content on disk
    disk_content = redacted_path.read_text(encoding='utf-8')
    assert 'redacted: true' in disk_content
    assert 'redaction_reason: Security Policy EP-0143 Test' in disk_content
    assert '[TOMBSTONE: REDACTED DUE TO SECURITY POLICY - Security Policy EP-0143 Test]' in disk_content

    # Merkle Memory integrity verification MUST pass (Noether tombstone invariant)
    assert manager.verify_integrity() == []

    # Load all memories and check attributes
    mems = manager.load_all()
    assert len(mems) == 1
    loaded = mems[0]
    assert loaded.id == original_id
    assert loaded.redacted is True
    assert loaded.redaction_reason == 'Security Policy EP-0143 Test'


def test_cli_admin_memory_redact(tmp_path, monkeypatch):
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    dot_tur = fake_home / '.tur'
    dot_tur.mkdir(parents=True, exist_ok=True)
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir(parents=True, exist_ok=True)

    index_data = {
        'personas': [
            {'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'},
        ]
    }
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    persona_dir = personas_dir / persona_id
    (persona_dir / 'memories' / 'active').mkdir(parents=True, exist_ok=True)
    with open(persona_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'name': 'Ariel', 'version': '5.4.0'}, f)

    manager = MemoryManager(base_dir=persona_dir)
    mem = Memory(
        timestamp=datetime(2026, 8, 30, 12, 0, 0),
        type=MemoryType.INSIGHT,
        scope=MemoryScope.UNIVERSAL,
        tags=['admin_test'],
        content='Confidential staging cluster note.',
    )
    manager.save(mem)

    # Run CLI command
    result = runner.invoke(
        admin_app,
        ['memory', 'redact', mem.id, '--reason', 'Leaked staging credential', persona_id],
    )
    assert result.exit_code == 0
    assert 'successfully tombstoned and redacted' in result.output

    # View memory via CLI
    view_result = runner.invoke(admin_app, ['memory', 'view', mem.id, persona_id])
    assert view_result.exit_code == 0
    assert 'TRUE' in view_result.output
    assert 'Leaked staging credential' in view_result.output
