import json
import os
from pathlib import Path
from typing import ClassVar

import pytest
import yaml
from typer.testing import CliRunner

from tur.cli.admin import app as admin_app
from tur.cli.agent import app as agent_app
from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType, PersonaIndex
from tur.paths import get_global_tur_dir, resolve_workspace_dir

runner = CliRunner()


@pytest.fixture
def setup_two_repos(tmp_path, monkeypatch):
    """Sets up two isolated workspace repos and a global store."""
    global_tur = tmp_path / 'global_tur'
    global_tur.mkdir(parents=True, exist_ok=True)

    # Create global personas.yaml
    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    (global_tur / 'personas.yaml').write_text(yaml.dump(index_data), encoding='utf-8')

    persona_global_dir = global_tur / 'personas' / persona_id
    (persona_global_dir / 'memories' / 'active').mkdir(parents=True, exist_ok=True)
    (persona_global_dir / 'persona.yaml').write_text(
        yaml.dump({'name': 'Ariel', 'version': '5.4.0', 'principles': []}), encoding='utf-8'
    )

    repo_a = tmp_path / 'repo_a'
    (repo_a / '.tur').mkdir(parents=True, exist_ok=True)
    (repo_a / '.tur' / 'state.yaml').write_text(yaml.dump({'active_persona_id': persona_id}), encoding='utf-8')

    repo_b = tmp_path / 'repo_b'
    (repo_b / '.tur').mkdir(parents=True, exist_ok=True)
    (repo_b / '.tur' / 'state.yaml').write_text(yaml.dump({'active_persona_id': persona_id}), encoding='utf-8')

    monkeypatch.setenv('TUR_ACTIVE_PERSONA_ID', persona_id)

    return global_tur, repo_a, repo_b, persona_id


def test_isolated_multi_project_sandboxing(setup_two_repos, monkeypatch):
    """
    Isolated Multi-Project Sandboxing:
    Writes incarnation memories in repo_a, verifies repo_b reports 0 local memories.
    """
    global_tur, repo_a, repo_b, persona_id = setup_two_repos
    monkeypatch.setenv('TUR_HOME', str(global_tur))

    # In repo_a: save 1 universal memory and 3 incarnation memories
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_a))
    persona_dir = global_tur / 'personas' / persona_id
    manager_a = MemoryManager(base_dir=persona_dir)

    # Universal memory
    mem_u = Memory(
        type=MemoryType.AXIOM, scope=MemoryScope.UNIVERSAL, content='Universal truth for all realms.', tags=['core']
    )
    manager_a.save(mem_u)

    # 3 Incarnation memories in repo_a
    for i in range(3):
        mem_inc = Memory(
            type=MemoryType.FACT, scope=MemoryScope.INCARNATION, content=f'Repo A specific fact #{i}', tags=['repo_a']
        )
        manager_a.save(mem_inc)

    assert manager_a.count_all() == 4
    assert len(list((repo_a / '.tur' / 'personas' / persona_id / 'memories' / 'active').glob('*.md'))) == 3

    # Switch to repo_b
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_b))
    manager_b = MemoryManager(base_dir=persona_dir)

    # Repo B should see the 1 universal memory and 0 local memories
    all_b = manager_b.load_all()
    assert len(all_b) == 1
    assert all_b[0].content == 'Universal truth for all realms.'
    assert manager_b.count_all() == 1

    # Repo B local directory should not have repo_a files
    repo_b_active = repo_b / '.tur' / 'personas' / persona_id / 'memories' / 'active'
    if repo_b_active.exists():
        assert len(list(repo_b_active.glob('*.md'))) == 0


def test_4_tier_workspace_resolution(tmp_path, monkeypatch):
    """
    Multi-Tiered Terrain Resolution Hierarchy:
    1. TUR_PROJECT_DIR
    2. MCP Roots
    3. CWD (.tur)
    4. None (Pure Traveler)
    """
    dir1 = tmp_path / 'tier1_env'
    dir1.mkdir()
    dir2 = tmp_path / 'tier2_mcp'
    dir2.mkdir()
    dir3 = tmp_path / 'tier3_cwd'
    dir3.mkdir()
    (dir3 / '.tur').mkdir()
    dir4 = tmp_path / 'tier4_clean'
    dir4.mkdir()

    # Tier 1: Environment variable
    monkeypatch.setenv('TUR_PROJECT_DIR', str(dir1))
    assert resolve_workspace_dir() == dir1

    # Tier 2: MCP Root
    monkeypatch.delenv('TUR_PROJECT_DIR', raising=False)

    class FakeRoot:
        uri = f'file:///{dir2.as_posix()}'

    class FakeContext:
        roots: ClassVar = [FakeRoot()]

    assert resolve_workspace_dir(ctx=FakeContext()) == dir2

    # Tier 3: CWD with .tur
    monkeypatch.chdir(dir3)
    assert resolve_workspace_dir() == dir3

    # Tier 4: Pure Traveler (CWD without .tur)
    monkeypatch.chdir(dir4)
    assert resolve_workspace_dir() is None


def test_pure_function_json_delegation_sleep_commit(setup_two_repos, monkeypatch):
    """
    Pure-Function Delegation Payload Test for `tur sleep --commit`
    """
    global_tur, repo_a, _, persona_id = setup_two_repos
    monkeypatch.setenv('TUR_HOME', str(global_tur))
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_a))
    monkeypatch.chdir(repo_a)

    payload = {
        'memories': [
            {
                'type': 'insight',
                'scope': 'incarnation',
                'tags': ['delegation', 'test'],
                'content': 'A purely delegated insight.',
            }
        ]
    }
    payload_json = json.dumps(payload)

    result = runner.invoke(agent_app, ['sleep', '--commit', payload_json, '-n', 'Ending session'])
    assert result.exit_code == 0
    assert 'Dreams consolidated. 1 new memories formed.' in result.output

    # Verify memory was committed to repo_a
    manager = MemoryManager(base_dir=global_tur / 'personas' / persona_id)
    mems = manager.load_all()
    assert any('A purely delegated insight.' in m.content for m in mems)


def test_pure_function_json_delegation_learn_commit(setup_two_repos, monkeypatch):
    """
    Pure-Function Delegation for `tur learn --json`
    """
    global_tur, repo_a, _, persona_id = setup_two_repos
    monkeypatch.setenv('TUR_HOME', str(global_tur))
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_a))
    monkeypatch.chdir(repo_a)

    payload = [
        {'type': 'fact', 'scope': 'incarnation', 'tags': ['batch'], 'content': 'Batch memory fact 1.'},
        {'type': 'preference', 'scope': 'universal', 'tags': ['batch'], 'content': 'User prefers strict boundaries.'},
    ]

    result = runner.invoke(agent_app, ['learn', '--json', json.dumps(payload)])
    assert result.exit_code == 0
    assert 'Committed 2 memories from JSON payload(s).' in result.output

    manager = MemoryManager(base_dir=global_tur / 'personas' / persona_id)
    assert manager.count_all() >= 2


def test_storage_bank_hygiene_clean(setup_two_repos, monkeypatch):
    """
    Storage Bank Hygiene (`tur-adm clean`):
    Scans for orphaned persona dirs and dangling temp files.
    """
    global_tur, repo_a, _, persona_id = setup_two_repos
    monkeypatch.setenv('TUR_HOME', str(global_tur))
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_a))

    # Create orphaned directory
    orphan_id = '00000000-0000-0000-0000-000000000000'
    orphan_dir = global_tur / 'personas' / orphan_id
    orphan_dir.mkdir(parents=True)
    (orphan_dir / 'trash.txt').write_text('orphan', encoding='utf-8')

    # Create dangling temp file
    temp_file = global_tur / 'personas' / persona_id / 'memories' / 'active' / 'test.tmp.123'
    temp_file.write_text('temp', encoding='utf-8')

    # Dry-run test
    res_dry = runner.invoke(admin_app, ['clean', '--dry-run'])
    assert res_dry.exit_code == 0
    assert 'Dry run completed.' in res_dry.output
    assert orphan_dir.exists()

    # Actual clean test
    res_clean = runner.invoke(admin_app, ['clean', '--yes'])
    assert res_clean.exit_code == 0
    assert not orphan_dir.exists()
    assert not temp_file.exists()
    assert 'Hygiene cleanup completed.' in res_clean.output
    assert '100% Merkle integrity verified.' in res_clean.output


def test_multi_payload_json_delegation(setup_two_repos, monkeypatch, tmp_path):
    """
    Multi-Payload / Multi-Chunk Ingestion for Sleep, Learn, and Introspect.
    Verifies that multiple JSON chunks, NDJSON streams, or files are combined and committed.
    """
    global_tur, repo_a, _, persona_id = setup_two_repos
    monkeypatch.setenv('TUR_HOME', str(global_tur))
    monkeypatch.setenv('TUR_PROJECT_DIR', str(repo_a))
    monkeypatch.chdir(repo_a)

    # 1. Multi-chunk sleep with multiple --commit flags
    chunk1 = json.dumps(
        {'memories': [{'type': 'insight', 'scope': 'incarnation', 'content': 'Sleep chunk 1 insight.'}]}
    )
    chunk2 = json.dumps({'memories': [{'type': 'fact', 'scope': 'incarnation', 'content': 'Sleep chunk 2 fact.'}]})

    res_sleep = runner.invoke(agent_app, ['sleep', '--commit', chunk1, '--commit', chunk2, '-n', 'Multi-chunk sleep'])
    assert res_sleep.exit_code == 0
    assert 'Dreams consolidated. 2 new memories formed.' in res_sleep.output

    # 2. NDJSON stream with tur learn --json
    ndjson_payload = (
        '{"type": "axiom", "scope": "universal", "content": "NDJSON Axiom 1."}\n'
        '{"type": "axiom", "scope": "universal", "content": "NDJSON Axiom 2."}'
    )
    res_learn = runner.invoke(agent_app, ['learn', '--json', ndjson_payload])
    assert res_learn.exit_code == 0
    assert 'Committed 2 memories from JSON payload(s).' in res_learn.output

    # 3. Multi-chunk graph with tur introspect --commit
    manager = MemoryManager(base_dir=global_tur / 'personas' / persona_id)
    all_mems = manager.load_all()
    mem_ids = [m.id for m in all_mems]

    g_chunk1 = json.dumps(
        {
            'nodes': [
                {'id': 'concept-x', 'type': 'Concept', 'content': 'Concept X from chunk 1', 'sources': mem_ids[:2]}
            ],
            'edges': [],
        }
    )
    g_chunk2 = json.dumps(
        {
            'nodes': [
                {'id': 'decision-y', 'type': 'Decision', 'content': 'Decision Y from chunk 2', 'sources': mem_ids[2:]}
            ],
            'edges': [{'source': 'decision-y', 'target': 'concept-x', 'type': 'depends_on'}],
        }
    )

    res_intro = runner.invoke(agent_app, ['introspect', '--commit', g_chunk1, '--commit', g_chunk2])
    assert res_intro.exit_code == 0
    assert 'Introspection Assembly completed successfully.' in res_intro.output
