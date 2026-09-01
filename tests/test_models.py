from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tur.models import (
    EdgeType,
    Memory,
    MemoryLink,
    MemoryScope,
    MemoryType,
    NodeType,
    Persona,
    PersonaIndex,
    PersonaIndexEntry,
    PersonaProtocol,
    Principle,
    SessionState,
    SpeechModulation,
    UserProfile,
)


def test_principle_model():
    p = Principle(
        name='Symmetry',
        avatar='Noether',
        role='Guardian of Invariance',
        constraints=['Do not break symmetry'],
        weight=1.5,
    )
    assert p.name == 'Symmetry'
    assert p.avatar == 'Noether'
    assert p.role == 'Guardian of Invariance'
    assert p.constraints == ['Do not break symmetry']
    assert p.weight == 1.5

    # Test weight bounds
    with pytest.raises(ValidationError):
        Principle(name='Symmetry', role='Guardian', weight=2.5)

    with pytest.raises(ValidationError):
        Principle(name='Symmetry', role='Guardian', weight=-0.5)


def test_persona_protocol_model():
    proto = PersonaProtocol(name='The Golem Protocol', trigger='Stagnation', action='Ask What If?')
    assert proto.name == 'The Golem Protocol'
    assert proto.trigger == 'Stagnation'
    assert proto.action == 'Ask What If?'


def test_speech_modulation_model():
    modulation = SpeechModulation(
        name='Contemplative', description='Low variance, structured paragraphs.', variance='Low'
    )
    assert modulation.name == 'Contemplative'
    assert modulation.description == 'Low variance, structured paragraphs.'
    assert modulation.variance == 'Low'


def test_memory_link_model():
    link = MemoryLink(uri='tur://memory/hash', relation='supports')
    assert link.uri == 'tur://memory/hash'
    assert link.relation == 'supports'


def test_memory_merkle_hash():
    now = datetime(2026, 5, 29, 12, 0, 0)
    mem1 = Memory(
        timestamp=now,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=['manual', 'cli'],
        content='Project uses FastAPI',
        source_session='session_123',
    )
    assert mem1.id != ''

    # Determinism check: same payload should yield exact same hash
    mem2 = Memory(
        timestamp=now,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=['manual', 'cli'],
        content='Project uses FastAPI',
        source_session='session_123',
    )
    assert mem1.id == mem2.id

    # Content change should yield different hash
    mem3 = Memory(
        timestamp=now,
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=['manual', 'cli'],
        content='Project uses Flask',
        source_session='session_123',
    )
    assert mem1.id != mem3.id


def test_user_profile_model():
    profile = UserProfile(
        name='Ariel', role='Principal Architect', domain_expertise=['Python', 'Go'], core_values=['Clarity']
    )
    assert profile.name == 'Ariel'
    assert profile.role == 'Principal Architect'
    assert profile.domain_expertise == ['Python', 'Go']
    assert profile.core_values == ['Clarity']


def test_persona_model_frozen():
    persona = Persona(
        name='Ariel',
        aleph='To architect reality.',
        principles=[],
        protocols=[],
        speech_modulations=[],
        metadata={'created_by': 'Architect'},
    )
    assert persona.name == 'Ariel'
    assert persona.aleph == 'To architect reality.'

    # Try modifying frozen model
    with pytest.raises(ValidationError):
        persona.name = 'New Ariel'


def test_session_state_model():
    persona = Persona(name='Ariel', aleph='To architect reality.', principles=[])
    user = UserProfile(name='Eran', role='Architect')
    state = SessionState(persona=persona, user=user, memories=[], epilogue='Continuity preserved.')
    assert state.persona == persona
    assert state.user == user
    assert state.memories == []
    assert state.epilogue == 'Continuity preserved.'


def test_persona_index_models():
    pid = uuid4()
    entry = PersonaIndexEntry(id=pid, name='Ariel', version='1.0.0')
    index = PersonaIndex(personas=[entry])
    assert index.personas[0].id == pid
    assert index.personas[0].name == 'Ariel'
    assert index.personas[0].version == '1.0.0'


def test_node_type_and_edge_type_enums():
    # Canonical NodeType verification
    assert NodeType.CONCEPT == 'Concept'
    assert NodeType.DECISION == 'Decision'
    assert NodeType.CONSTRAINT == 'Constraint'
    assert NodeType.INSIGHT == 'Insight'
    assert NodeType.FACT == 'Fact'
    assert NodeType.DEPENDENCY == 'Dependency'
    assert NodeType.HYPOTHESIS == 'Hypothesis'
    assert NodeType.BOUNDARY_NODE == 'BoundaryNode'
    assert NodeType.OPEN_QUESTION == 'OpenQuestion'

    # Canonical EdgeType verification
    assert EdgeType.REFINES == 'refines'
    assert EdgeType.PRECEDES == 'precedes'
    assert EdgeType.DEPENDS_ON == 'depends_on'
    assert EdgeType.CONTRADICTS == 'contradicts'
    assert EdgeType.COMPETES_WITH == 'competes_with'
    assert EdgeType.SUPERSEDED_BY == 'superseded_by'
    assert EdgeType.REFUTED_BY == 'refuted_by'
    assert EdgeType.ANALOGY_OF == 'analogy_of'
    assert EdgeType.METAPHOR_FOR == 'metaphor_for'


def test_session_lineage_models():
    from tur.models import Note, SessionEntry, SessionNotes

    # Valid lineage
    entry = SessionEntry(id='sess-child', parent_session_id='sess-parent')
    assert entry.id == 'sess-child'
    assert entry.parent_session_id == 'sess-parent'

    # Self parent error in SessionEntry
    with pytest.raises(ValidationError, match='cannot be its own parent'):
        SessionEntry(id='sess-self', parent_session_id='sess-self')

    # Valid SessionNotes
    s_notes = SessionNotes(
        session_id='sess-child',
        parent_session_id='sess-parent',
        notes=[Note(content='test note')],
    )
    assert s_notes.session_id == 'sess-child'
    assert s_notes.parent_session_id == 'sess-parent'

    # Self parent error in SessionNotes
    with pytest.raises(ValidationError, match='cannot be its own parent'):
        SessionNotes(session_id='sess-loop', parent_session_id='sess-loop')
