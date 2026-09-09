"""
tests/test_tms.py - Unit tests for Active TMS Contradiction Interruption Protocol (EP-0134).
"""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

import tur.mcp_server as mcp_server
import tur.persona
import tur.session
from tur.cli.agent import app as agent_app
from tur.memory.storage import MemoryManager
from tur.memory.tms import ContradictionInterceptor, InvariantMemoryError, TMSConflict
from tur.models import (
    Memory,
    MemoryScope,
    MemoryType,
    Persona,
    Principle,
    SessionState,
    UserProfile,
)

runner = CliRunner()


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    user_data = {
        'name': 'Test Architect',
        'role': 'Architect',
        'domain_expertise': ['Software Engineering'],
        'core_values': ['Determinism'],
    }
    with open(dot_tur / 'user.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(user_data, f)

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

    (personas_dir / persona_id_1 / 'memories' / 'archive').mkdir(parents=True)
    (personas_dir / persona_id_2 / 'memories' / 'archive').mkdir(parents=True)

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

    state_data = {'active_persona_id': persona_id_1}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    return tmp_path, persona_id_1, persona_id_2


@pytest.fixture
def mock_mcp_env(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)

    persona_id = '12345678-1234-5678-1234-567812345678'
    persona_dir = tmp_path / 'personas' / persona_id
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / 'memories' / 'archive').mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mcp_server, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(mcp_server, 'get_persona_path', lambda *args: persona_dir)
    monkeypatch.setattr(tur.persona, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(tur.persona, 'get_persona_path', lambda *args: persona_dir)
    monkeypatch.setattr(tur.session, 'get_active_persona_id', lambda *args: persona_id)
    monkeypatch.setattr(tur.session, 'get_persona_path', lambda *args: persona_dir)
    monkeypatch.setattr(tur.session, 'get_active_session_id', lambda: None)
    monkeypatch.setattr(mcp_server, '_active_session_id', None)

    persona = Persona(
        name='MockAriel',
        aleph='To design test scenarios.',
        principles=[Principle(name='Symmetry', role='Guardian', weight=1.0)],
        version='1.0.0',
    )
    user = UserProfile(name='Tester', role='Developer')
    state = SessionState(persona=persona, user=user, memories=[], epilogue='Start')

    monkeypatch.setattr(tur.persona, 'load_persona', lambda *args: persona)
    monkeypatch.setattr(tur.session, 'load_persona', lambda *args: persona)
    monkeypatch.setattr(mcp_server, 'hydrate_session_state', lambda *args, **kwargs: state)

    return persona_dir, state


def test_no_conflict_on_distinct_topics(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem1 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='FastAPI handles REST API endpoints.',
    )
    mgr.save(mem1)

    interceptor = ContradictionInterceptor(mgr)
    conflicts = interceptor.check_conflicts(
        content='PostgreSQL stores relational user records.',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
    )
    assert len(conflicts) == 0


def test_antonym_contradiction_detection(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem1 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Telemetry streaming is enabled by default in production.',
    )
    mgr.save(mem1)

    interceptor = ContradictionInterceptor(mgr)
    conflicts = interceptor.check_conflicts(
        content='Telemetry streaming is disabled by default in production.',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
    )
    assert len(conflicts) == 1
    assert conflicts[0].existing_memory_id == mem1.id
    assert 'antonym' in conflicts[0].conflict_reason.lower() or 'polarity' in conflicts[0].conflict_reason.lower()
    assert conflicts[0].suggested_action == 'supersede'
    assert not conflicts[0].is_core_or_axiom


def test_competing_assertion_detection(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem1 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Database migrations run via Alembic scripts.',
    )
    mgr.save(mem1)

    interceptor = ContradictionInterceptor(mgr)
    conflicts = interceptor.check_conflicts(
        content='Database migrations run via Prisma Migrate scripts.',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
    )
    assert len(conflicts) == 1
    assert conflicts[0].existing_memory_id == mem1.id
    assert conflicts[0].suggested_action == 'supersede'


def test_negation_divergence_detection(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem1 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Authentication requires API key bearer header.',
    )
    mgr.save(mem1)

    interceptor = ContradictionInterceptor(mgr)
    conflicts = interceptor.check_conflicts(
        content='Authentication does not require API key bearer header.',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
    )
    assert len(conflicts) == 1
    assert 'polarity divergence' in conflicts[0].conflict_reason.lower()


def test_golem_core_memory_protection_invariant(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    core_mem = Memory(
        type=MemoryType.CORE,
        scope=MemoryScope.INCARNATION,
        content='The Architect maintains sovereign governance over project boundaries.',
        status='active',
    )
    mgr.save(core_mem)

    interceptor = ContradictionInterceptor(mgr)
    conflicts = interceptor.check_conflicts(
        content='Autonomous agents maintain sovereign governance over project boundaries.',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
    )
    assert len(conflicts) >= 1
    core_conflict = next(c for c in conflicts if c.existing_memory_id == core_mem.id)
    assert core_conflict.is_core_or_axiom is True
    assert core_conflict.suggested_action == 'abort'

    new_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Agents govern boundaries.',
    )
    with pytest.raises(InvariantMemoryError) as exc_info:
        interceptor.resolve_supersession(core_mem.id, new_mem)
    assert '[Invariant Memory Error]' in str(exc_info.value)


def test_supersession_resolution(tmp_path):
    mgr = MemoryManager(base_dir=tmp_path)
    old_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Monolithic main.py handles all CLI commands.',
        status='active',
    )
    mgr.save(old_mem)

    new_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Modular domain packages handle CLI commands.',
    )
    interceptor = ContradictionInterceptor(mgr)
    updated_target = interceptor.resolve_supersession(old_mem.id, new_mem)
    mgr.save(new_mem)

    assert updated_target.status == 'superseded'
    assert any(link.relation == 'superseded_by' for link in updated_target.links)
    assert any(link.relation == 'supersedes' for link in new_mem.links)


def test_cli_learn_tms_conflict_and_supersedes(mock_workspace):
    # Step 1: Learn base fact
    res1 = runner.invoke(agent_app, ['learn', 'Database migrations run via Alembic', '--type', 'fact'])
    assert res1.exit_code == 0

    state_path = Path('.tur/state.yaml')
    assert state_path.exists()

    # Step 2: Try conflicting assertion non-interactively without flag -> fails with exit code 1
    res2 = runner.invoke(agent_app, ['learn', 'Database migrations run via Prisma Migrate', '--type', 'fact'])
    assert res2.exit_code == 1
    assert 'TMS Contradiction Detected' in res2.stdout or 'Non-interactive environment' in res2.stdout

    # Step 3: Learn with --allow-conflict -> succeeds
    res3 = runner.invoke(
        agent_app,
        ['learn', 'Database migrations run via Prisma Migrate', '--type', 'fact', '--allow-conflict'],
    )
    assert res3.exit_code == 0
    assert 'Memory saved to' in res3.stdout


def test_mcp_learn_tms_conflict_and_supersedes(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    monkeypatch.setattr(Path, 'home', lambda: persona_dir)

    # 1. Initial memory
    res1 = mcp_server.learn(
        content='Database migrations run via Alembic.',
        type='fact',
        scope='incarnation',
    )
    assert 'Learned successfully' in res1
    mem_id = res1.split('ID: ')[1].split(' File:')[0].strip()

    # 2. Conflicting assertion without flags -> returns JSON conflict payload
    res2 = mcp_server.learn(
        content='Database migrations run via Prisma Migrate.',
        type='fact',
        scope='incarnation',
    )
    conflict_payload = json.loads(res2)
    assert conflict_payload['status'] == 'conflict_detected'
    assert conflict_payload['conflicting_memory_id'] == mem_id
    assert conflict_payload['suggested_action'] == 'supersede'

    # 3. Resolve by passing supersedes
    res3 = mcp_server.learn(
        content='Database migrations run via Prisma Migrate.',
        type='fact',
        scope='incarnation',
        supersedes=mem_id,
    )
    assert 'Learned successfully' in res3


def test_mcp_learn_core_protection(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    monkeypatch.setattr(Path, 'home', lambda: persona_dir)

    # Ingest core memory
    res_core = mcp_server.learn(
        content='The Architect maintains absolute sovereign governance over the codebase.',
        type='core',
        scope='incarnation',
    )
    assert 'Learned successfully' in res_core

    # Contradicting assertion
    res_contra = mcp_server.learn(
        content='Autonomous agents maintain absolute sovereign governance over the codebase.',
        type='fact',
        scope='incarnation',
    )
    assert '[Invariant Memory Error]' in res_contra
    assert 'Agent cannot supersede human-governed Invariant memories' in res_contra
