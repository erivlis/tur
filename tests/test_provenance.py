import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from tur.memory import MemoryManager
from tur.models import (
    Memory,
    MemoryDecay,
    MemoryProvenance,
    MemoryScope,
    MemoryType,
)
from tur.provenance import (
    DEFAULT_DECAY_POLICIES,
    compute_epistemic_weight,
    create_provenance_and_decay,
    evaluate_staleness,
    get_git_commit_distance,
    get_git_head_sha,
    is_git_file_modified_or_deleted,
)
from tur.session import hydrate_session_state, note_logic, start_session_logic


def test_memory_provenance_and_decay_models():
    now = datetime(2026, 8, 27, 15, 0, 0)
    prov = MemoryProvenance(
        observed_at=now,
        git_sha='9f83ab2c104e',
        source_agent='copilot-chuck',
        source_harness='github-copilot',
        context_ref='src/tur/signals.py#L45-L60',
    )
    assert prov.observed_at == now
    assert prov.git_sha == '9f83ab2c104e'
    assert prov.source_agent == 'copilot-chuck'
    assert prov.source_harness == 'github-copilot'
    assert prov.context_ref == 'src/tur/signals.py#L45-L60'

    decay = MemoryDecay(
        half_life_days=14.0,
        last_verified_at=now,
        staleness_status='fresh',
    )
    assert decay.half_life_days == 14.0
    assert decay.last_verified_at == now
    assert decay.staleness_status == 'fresh'


def test_create_provenance_and_decay_factory(monkeypatch):
    monkeypatch.setattr('tur.provenance.get_git_head_sha', lambda repo_dir=None: 'abcdef123456')

    prov, decay = create_provenance_and_decay(
        memory_type=MemoryType.FACT,
        confidence=0.9,
        context_ref='src/api.py#L1-L10',
        source_agent='ariel',
        source_harness='antigravity',
    )

    assert prov.git_sha == 'abcdef123456'
    assert prov.context_ref == 'src/api.py#L1-L10'
    assert prov.source_agent == 'ariel'
    assert prov.source_harness == 'antigravity'
    assert decay.half_life_days == 14.0
    assert decay.staleness_status == 'fresh'

    # Axioms have infinite half-life (None)
    _prov_ax, decay_ax = create_provenance_and_decay(memory_type=MemoryType.AXIOM)
    assert decay_ax.half_life_days is None
    assert decay_ax.staleness_status == 'fresh'


def test_compute_epistemic_weight_axiom_and_core():
    """Axiom and Core memories do not decay regardless of elapsed time or commit distance."""
    past = datetime(2020, 1, 1, 0, 0, 0)
    now = datetime(2026, 9, 1, 0, 0, 0)

    mem_axiom = Memory(
        timestamp=past,
        type=MemoryType.AXIOM,
        scope=MemoryScope.PERSONA,
        content='Symmetry is the foundation of truth.',
        confidence=0.95,
        decay=MemoryDecay(half_life_days=None, last_verified_at=past, staleness_status='fresh'),
        provenance=MemoryProvenance(git_sha='oldsha', observed_at=past),
    )

    with patch('tur.provenance.get_git_commit_distance', return_value=1000):
        weight = compute_epistemic_weight(mem_axiom, now=now)
        assert weight == 0.95


def test_compute_epistemic_weight_fact_decay():
    """Fact memory half-life is 14 days and lambda is 0.05."""
    start = datetime(2026, 8, 1, 0, 0, 0)
    # After exactly 14 days and 0 commit drift: weight should be confidence * 0.5
    now_14_days = datetime(2026, 8, 15, 0, 0, 0)

    mem = Memory(
        timestamp=start,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='FastAPI is mounted on port 8000',
        confidence=1.0,
        decay=MemoryDecay(half_life_days=14.0, last_verified_at=start, staleness_status='fresh'),
        provenance=MemoryProvenance(git_sha='sha123', observed_at=start),
    )

    with patch('tur.provenance.get_git_commit_distance', return_value=0):
        w = compute_epistemic_weight(mem, now=now_14_days)
        assert pytest.approx(w, 0.001) == 0.5

    # After 14 days and 10 commits drift: w = 0.5 * exp(-0.05 * 10) = 0.5 * exp(-0.5)
    with patch('tur.provenance.get_git_commit_distance', return_value=10):
        w_drift = compute_epistemic_weight(mem, now=now_14_days)
        expected = 0.5 * math.exp(-0.5)
        assert pytest.approx(w_drift, 0.001) == expected


def test_compute_epistemic_weight_refuted():
    mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Refuted fact',
        confidence=1.0,
        status='falsified',
    )
    assert compute_epistemic_weight(mem) == 0.0

    mem2 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Refuted decay status',
        confidence=1.0,
        decay=MemoryDecay(staleness_status='refuted'),
    )
    assert compute_epistemic_weight(mem2) == 0.0


def test_evaluate_staleness_states(tmp_path):
    # 1. Fresh fact
    fresh_mem = Memory(
        type=MemoryType.FACT,
        content='Fresh observation',
        confidence=1.0,
        provenance=MemoryProvenance(git_sha='headsha'),
        decay=MemoryDecay(half_life_days=14.0, staleness_status='fresh'),
    )
    with patch('tur.provenance.get_git_commit_distance', return_value=0):
        status, reason = evaluate_staleness(fresh_mem)
        assert status == 'fresh'
        assert reason is None

    # 2. Stale due to commit drift > 20
    with patch('tur.provenance.get_git_commit_distance', return_value=25):
        status, reason = evaluate_staleness(fresh_mem)
        assert status == 'stale'
        assert reason is not None
        assert 'Commit drift: 25' in reason

    # 3. Stale due to file deletion or modification
    nonexistent_file = str(tmp_path / 'missing.py')
    stale_file_mem = Memory(
        type=MemoryType.FACT,
        content='Refers to missing file',
        confidence=1.0,
        provenance=MemoryProvenance(git_sha='headsha', context_ref=f'{nonexistent_file}#L1-L10'),
    )
    with patch('tur.provenance.get_git_commit_distance', return_value=0):
        status, reason = evaluate_staleness(stale_file_mem)
        assert status == 'stale'
        assert reason is not None
        assert 'modified or deleted' in reason

    # 4. Unanchored
    unanchored_mem = Memory(
        type=MemoryType.FACT,
        content='No git sha',
        confidence=1.0,
        decay=MemoryDecay(half_life_days=14.0, staleness_status='unanchored'),
    )
    status, reason = evaluate_staleness(unanchored_mem)
    assert status == 'unanchored'

    # 5. Stale due to low decayed weight
    old_time = datetime(2025, 1, 1, 0, 0, 0)
    now = datetime(2026, 9, 1, 0, 0, 0)
    decayed_mem = Memory(
        timestamp=old_time,
        type=MemoryType.FACT,
        content='Very old fact',
        confidence=1.0,
        decay=MemoryDecay(half_life_days=14.0, last_verified_at=old_time),
        provenance=MemoryProvenance(git_sha='oldsha'),
    )
    with patch('tur.provenance.get_git_commit_distance', return_value=0):
        status, reason = evaluate_staleness(decayed_mem, now=now)
        assert status == 'stale'
        assert reason is not None
        assert 'decayed below threshold' in reason


def test_okf_provenance_and_decay_roundtrip(tmp_path, monkeypatch):
    fake_home = tmp_path / 'fake_home'
    local_base = tmp_path / 'local_base'
    fake_home.mkdir()
    local_base.mkdir()

    monkeypatch.setattr(Path, 'home', lambda: fake_home)
    manager = MemoryManager(base_dir=local_base)

    observed_time = datetime(2026, 8, 27, 12, 0, 0)
    prov = MemoryProvenance(
        observed_at=observed_time,
        git_sha='9f83ab2c104e',
        source_agent='copilot-chuck',
        source_harness='github-copilot',
        context_ref='src/tur/signals.py#L45-L60',
    )
    decay = MemoryDecay(
        half_life_days=14.0,
        last_verified_at=observed_time,
        staleness_status='fresh',
    )

    mem = Memory(
        timestamp=observed_time,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=['provenance', 'test'],
        content='SQLite signal queue uses WAL mode and busy_timeout=5000ms.',
        confidence=0.95,
        provenance=prov,
        decay=decay,
    )

    saved_path = manager.save(mem)
    assert saved_path.exists()

    # Verify OKF frontmatter contains provenance and decay
    content = saved_path.read_text(encoding='utf-8')
    assert 'confidence: 0.95' in content
    assert 'git_sha: 9f83ab2c104e' in content
    assert 'source_agent: copilot-chuck' in content
    assert 'context_ref: src/tur/signals.py#L45-L60' in content
    assert 'half_life_days: 14.0' in content

    # Reload and verify model preservation
    loaded = manager.load_all()
    assert len(loaded) == 1
    reloaded_mem = loaded[0]
    assert reloaded_mem.id == mem.id
    assert reloaded_mem.confidence == 0.95
    assert reloaded_mem.provenance is not None
    assert reloaded_mem.provenance.git_sha == '9f83ab2c104e'
    assert reloaded_mem.provenance.source_agent == 'copilot-chuck'
    assert reloaded_mem.provenance.context_ref == 'src/tur/signals.py#L45-L60'
    assert reloaded_mem.decay is not None
    assert reloaded_mem.decay.half_life_days == 14.0
    assert reloaded_mem.decay.staleness_status == 'fresh'

    # Cryptographic integrity check
    failures = manager.verify_integrity()
    assert len(failures) == 0


def test_wake_filter_omits_stale_memories(tmp_path, monkeypatch):
    """EP-0131: Stale memories with weight < 0.3 are omitted from the default wake prompt."""
    monkeypatch.chdir(tmp_path)
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    persona_dir = personas_dir / persona_id
    persona_dir.mkdir(parents=True)

    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    persona_yaml = (
        'name: Ariel\n'
        'version: 0.1.0\n'
        'model: gemini-3.1-pro-preview\n'
        'aleph: To understand.\n'
        'principles: []\n'
        'protocols: []\n'
    )
    (persona_dir / 'persona.yaml').write_text(persona_yaml, encoding='utf-8')
    (dot_tur / 'personas.yaml').write_text(
        f'personas:\n  - id: "{persona_id}"\n    name: Ariel\n    version: "0.1.0"\n',
        encoding='utf-8',
    )
    (dot_tur / 'state.yaml').write_text(
        f'active_persona_id: "{persona_id}"\n',
        encoding='utf-8',
    )

    manager = MemoryManager(base_dir=persona_dir)

    fresh_mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Fresh active fact',
        confidence=1.0,
        decay=MemoryDecay(half_life_days=14.0, staleness_status='fresh'),
        provenance=MemoryProvenance(git_sha='head123'),
    )
    old_time = datetime(2025, 1, 1, 0, 0, 0)
    stale_mem = Memory(
        timestamp=old_time,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Stale decayed fact from long ago',
        confidence=0.5,
        decay=MemoryDecay(half_life_days=14.0, last_verified_at=old_time, staleness_status='stale'),
        provenance=MemoryProvenance(git_sha='old123'),
    )
    axiom_mem = Memory(
        timestamp=old_time,
        type=MemoryType.AXIOM,
        scope=MemoryScope.PERSONA,
        content='Permanent Axiom of Invariance',
        confidence=1.0,
    )

    manager.save(fresh_mem)
    manager.save(stale_mem)
    manager.save(axiom_mem)

    # Wake without include_stale (default)
    with patch('tur.provenance.get_git_commit_distance', return_value=0):
        state_default = hydrate_session_state(persona_id, include_stale=False)
        loaded_contents = [m.content for m in state_default.memories]
        assert 'Fresh active fact' in loaded_contents
        assert 'Permanent Axiom of Invariance' in loaded_contents
        assert 'Stale decayed fact from long ago' not in loaded_contents

        # Wake with include_stale=True
        state_all = hydrate_session_state(persona_id, include_stale=True)
        loaded_all_contents = [m.content for m in state_all.memories]
        assert 'Fresh active fact' in loaded_all_contents
        assert 'Permanent Axiom of Invariance' in loaded_all_contents
        assert 'Stale decayed fact from long ago' in loaded_all_contents


def test_cli_learn_with_provenance_and_decay(tmp_path, monkeypatch):
    """CLI learn command attaches provenance and decay options."""
    from typer.testing import CliRunner

    from tur.cli.agent import app

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    persona_dir = dot_tur / 'personas' / persona_id
    persona_dir.mkdir(parents=True)

    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    persona_yaml = (
        'name: Ariel\n'
        'version: 0.1.0\n'
        'model: gemini-3.1-pro-preview\n'
        'aleph: To understand.\n'
        'principles: []\n'
        'protocols: []\n'
    )
    (persona_dir / 'persona.yaml').write_text(persona_yaml, encoding='utf-8')
    (dot_tur / 'personas.yaml').write_text(
        f'personas:\n  - id: "{persona_id}"\n    name: Ariel\n    version: "0.1.0"\n',
        encoding='utf-8',
    )
    (dot_tur / 'state.yaml').write_text(
        f'active_persona_id: "{persona_id}"\n',
        encoding='utf-8',
    )

    result = runner.invoke(
        app,
        [
            'learn',
            'FastAPI endpoint mounted at /api/v1',
            '--type',
            'fact',
            '--confidence',
            '0.9',
            '--file',
            'src/api.py#L1-L20',
            '--agent',
            'copilot',
            '--harness',
            'antigravity',
        ],
    )
    assert result.exit_code == 0
    assert 'Memory saved' in result.output

    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all()
    assert len(mems) == 1
    assert mems[0].confidence == 0.9
    assert mems[0].provenance is not None
    assert mems[0].provenance.context_ref == 'src/api.py#L1-L20'
    assert mems[0].provenance.source_agent == 'copilot'
    assert mems[0].provenance.source_harness == 'antigravity'
    assert mems[0].decay is not None
    assert mems[0].decay.half_life_days == 14.0


def test_mcp_learn_with_provenance_and_decay(tmp_path, monkeypatch):
    """MCP learn tool accepts confidence and provenance."""
    from tur.mcp_server import learn

    monkeypatch.chdir(tmp_path)
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    persona_dir = dot_tur / 'personas' / persona_id
    persona_dir.mkdir(parents=True)

    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    persona_yaml = (
        'name: Ariel\n'
        'version: 0.1.0\n'
        'model: gemini-3.1-pro-preview\n'
        'aleph: To understand.\n'
        'principles: []\n'
        'protocols: []\n'
    )
    (persona_dir / 'persona.yaml').write_text(persona_yaml, encoding='utf-8')
    (dot_tur / 'personas.yaml').write_text(
        f'personas:\n  - id: "{persona_id}"\n    name: Ariel\n    version: "0.1.0"\n',
        encoding='utf-8',
    )
    (dot_tur / 'state.yaml').write_text(
        f'active_persona_id: "{persona_id}"\n',
        encoding='utf-8',
    )

    msg = learn(
        content='Background worker runs in asyncio loop',
        type='insight',
        scope='incarnation',
        confidence=0.85,
        context_ref='src/worker.py',
        source_agent='ariel',
    )
    assert 'Learned successfully' in msg

    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all()
    assert len(mems) == 1
    assert mems[0].confidence == 0.85
    assert mems[0].provenance is not None
    assert mems[0].provenance.context_ref == 'src/worker.py'
    assert mems[0].provenance.source_agent == 'ariel'
    assert mems[0].decay is not None
    assert mems[0].decay.half_life_days == 90.0
