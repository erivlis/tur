import json
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from tur.memory.diff import (
    DeltaStatus,
    MemoryDelta,
    compute_memory_diff,
    compute_session_diff,
    format_diff_json,
    format_diff_summary,
    format_diff_terminal,
)
from tur.models import Memory, MemoryLink, MemoryScope, MemoryType


@pytest.fixture
def sample_memories():
    now = datetime(2026, 8, 27, 10, 0, 0)
    m1 = Memory(
        id='mem-1',
        timestamp=now,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='SQLite signal queue uses WAL mode.',
        source_session='sess-1',
    )
    m2 = Memory(
        id='mem-2',
        timestamp=now,
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        content='main.py acts as monolithic router.',
        source_session='sess-1',
    )
    m3 = Memory(
        id='mem-3',
        timestamp=now,
        type=MemoryType.FACT,
        scope=MemoryScope.UNIVERSAL,
        content='Active debug port is 9229.',
        source_session='sess-1',
    )
    return m1, m2, m3


def test_compute_memory_diff_added(sample_memories):
    m1, m2, _m3 = sample_memories
    m4 = Memory(
        id='mem-4',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='New architectural fact.',
        source_session='sess-2',
    )

    base = [m1, m2]
    target = [m1, m2, m4]

    deltas = compute_memory_diff(base, target)
    assert len(deltas) == 1
    assert deltas[0].status == DeltaStatus.ADDED
    assert deltas[0].memory.id == 'mem-4'
    assert deltas[0].memory.content == 'New architectural fact.'


def test_compute_memory_diff_superseded(sample_memories):
    m1, m2, _m3 = sample_memories
    # m2_super replaces m2 with a link relation 'supersedes'
    m2_super = Memory(
        id='mem-2-new',
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        content='Monolith decomposed into isolated modules.',
        links=[MemoryLink(uri='tur://memory/mem-2', relation='supersedes')],
        source_session='sess-2',
    )

    base = [m1, m2]
    target = [m1, m2_super]

    deltas = compute_memory_diff(base, target)
    superseded_deltas = [d for d in deltas if d.status == DeltaStatus.SUPERSEDED]
    assert len(superseded_deltas) == 1
    assert superseded_deltas[0].memory.id == 'mem-2-new'
    assert superseded_deltas[0].previous_memory.id == 'mem-2'


def test_compute_memory_diff_refuted(sample_memories):
    m1, _m2, m3 = sample_memories
    # m3 is refuted via a link relation 'refutes'
    m_refuter = Memory(
        id='mem-refuter',
        type=MemoryType.FACT,
        scope=MemoryScope.UNIVERSAL,
        content='Port 9229 is deprecated.',
        links=[MemoryLink(uri='tur://memory/mem-3', relation='refutes')],
        source_session='sess-2',
    )

    base = [m1, m3]
    target = [m1, m_refuter]

    deltas = compute_memory_diff(base, target)
    refuted_deltas = [d for d in deltas if d.status == DeltaStatus.REFUTED]
    assert len(refuted_deltas) == 1
    assert refuted_deltas[0].memory.id == 'mem-3'


def test_compute_memory_diff_decayed(sample_memories):
    _m1, _m2, m3 = sample_memories
    m3_decayed = Memory(
        id='mem-3',
        timestamp=m3.timestamp,
        type=m3.type,
        scope=m3.scope,
        tags=['stale'],
        content=m3.content,
        source_session=m3.source_session,
    )

    base = [m3]
    target = [m3_decayed]

    deltas = compute_memory_diff(base, target)
    assert len(deltas) == 1
    assert deltas[0].status == DeltaStatus.DECAYED
    assert deltas[0].memory.id == 'mem-3'


def test_compute_memory_diff_modified(sample_memories):
    m1, _m2, _m3 = sample_memories
    m1_mod = Memory(
        id='mem-1',
        timestamp=m1.timestamp,
        type=m1.type,
        scope=MemoryScope.UNIVERSAL,  # changed scope
        tags=['updated'],
        content='SQLite signal queue uses WAL mode and busy_timeout=5000ms.',
        source_session=m1.source_session,
    )

    base = [m1]
    target = [m1_mod]

    deltas = compute_memory_diff(base, target)
    assert len(deltas) == 1
    assert deltas[0].status == DeltaStatus.MODIFIED
    assert deltas[0].memory.id == 'mem-1'
    assert deltas[0].previous_memory.content == m1.content


def test_format_diff_terminal(sample_memories):
    m1, m2, m3 = sample_memories
    deltas = [
        MemoryDelta(status=DeltaStatus.ADDED, memory=m1),
        MemoryDelta(
            status=DeltaStatus.SUPERSEDED,
            memory=Memory(
                id='mem-2-new',
                type=MemoryType.INSIGHT,
                scope=MemoryScope.INCARNATION,
                content='New insight.',
            ),
            previous_memory=m2,
        ),
        MemoryDelta(status=DeltaStatus.REFUTED, memory=m3, reason='Refuted by EP-0124'),
    ]

    out = format_diff_terminal(deltas, session_id='sess-test')
    assert 'Memory Delta: Session sess-test (3 mutations)' in out
    assert '[+] ADDED (Fact)' in out
    assert '[~] SUPERSEDED (Insight)' in out
    assert '[-] REFUTED (Fact)' in out
    assert 'Refuted by EP-0124' in out


def test_format_diff_summary(sample_memories):
    m1, m2, m3 = sample_memories
    deltas = [
        MemoryDelta(status=DeltaStatus.ADDED, memory=m1),
        MemoryDelta(status=DeltaStatus.ADDED, memory=Memory(id='mem-x', type=MemoryType.INSIGHT, content='x')),
        MemoryDelta(status=DeltaStatus.SUPERSEDED, memory=m2, previous_memory=m2),
        MemoryDelta(status=DeltaStatus.REFUTED, memory=m3),
    ]

    summary = format_diff_summary(deltas)
    assert '## Session Memory Ledger Delta' in summary
    assert '- Added: 1 fact, 1 insight' in summary
    assert '- Superseded: 1' in summary
    assert '- Refuted: 1' in summary


def test_format_diff_json(sample_memories):
    m1, m2, _m3 = sample_memories
    deltas = [
        MemoryDelta(status=DeltaStatus.ADDED, memory=m1),
        MemoryDelta(status=DeltaStatus.SUPERSEDED, memory=m2, previous_memory=m1, superseded_by=m2.id),
    ]

    json_data = format_diff_json(deltas)
    assert len(json_data) == 2
    assert json_data[0]['status'] == 'ADDED'
    assert json_data[0]['id'] == 'mem-1'
    assert json_data[1]['status'] == 'SUPERSEDED'
    assert json_data[1]['previous_id'] == 'mem-1'
    assert json_data[1]['superseded_by'] == 'mem-2'


def test_compute_session_diff_integration(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    p_dir = personas_dir / persona_id
    p_dir.mkdir(parents=True)
    (p_dir / 'memories' / 'active').mkdir(parents=True)
    (p_dir / 'memories' / 'archive').mkdir(parents=True)
    (p_dir / 'memories' / 'subsumed').mkdir(parents=True)

    persona_yaml = {'name': 'Ariel', 'version': '5.4.0', 'aleph': 'reality', 'principles': []}
    with open(p_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_yaml, f)

    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    state_data = {'active_persona_id': persona_id, 'active_session_id': 'sess-2'}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    # Sessions index linking sess-2 -> sess-1
    sessions_data = {
        'active_session_id': 'sess-2',
        'sessions': [
            {'id': 'sess-1', 'parent_session_id': None, 'status': 'ended'},
            {'id': 'sess-2', 'parent_session_id': 'sess-1', 'status': 'active'},
        ],
    }
    with open(p_dir / 'sessions.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(sessions_data, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    from tur.memory import MemoryManager

    mem_mgr = MemoryManager(base_dir=p_dir)
    m1 = Memory(
        id='mem-s1',
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Fact from session 1',
        source_session='sess-1',
    )
    m2 = Memory(
        id='mem-s2',
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        content='Insight from session 2',
        source_session='sess-2',
    )
    mem_mgr.save(m1)
    mem_mgr.save(m2)

    # Compute diff between sess-1 and sess-2
    deltas = compute_session_diff(base_session_id='sess-1', target_session_id='sess-2', persona_id=persona_id)
    assert len(deltas) >= 1
    assert any(d.status == DeltaStatus.ADDED and d.memory.content == 'Insight from session 2' for d in deltas)

    # Auto-resolve parent: target sess-2 with base=None should auto-resolve base=sess-1
    deltas_auto = compute_session_diff(base_session_id=None, target_session_id='sess-2', persona_id=persona_id)
    assert len(deltas_auto) >= 1
