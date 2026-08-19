"""Shared fixtures for the CodSpeed performance benchmarks.

The benchmarks exercise the pure, local hot paths of the engine (Merkle hashing,
OKF parsing, federated memory loading, graph recall and prompt compilation).
Every fixture builds a fully isolated, deterministic `.tur` state under `tmp_path`
so that no benchmark ever touches the real user home directory or the network.
"""

from datetime import datetime
from pathlib import Path

import networkx as nx
import pytest

from tur.models import (
    Memory,
    MemoryLink,
    MemoryScope,
    MemoryType,
    Persona,
    PersonaProtocol,
    Principle,
    SessionState,
    SpeechModulation,
    UserProfile,
)

BASE_TIMESTAMP = datetime(2026, 5, 29, 12, 0, 0)

MEMORY_TYPES = [MemoryType.FACT, MemoryType.PREFERENCE, MemoryType.EVENT, MemoryType.AXIOM, MemoryType.INSIGHT]


def make_memory(index: int, scope: MemoryScope = MemoryScope.INCARNATION, content_size: int = 1) -> Memory:
    """Builds a deterministic Memory (the Merkle hash is derived from the content)."""
    body = f'Memory {index}: the complexity of AI is an illusion of distance. ' * content_size
    return Memory(
        timestamp=BASE_TIMESTAMP.replace(second=index % 60),
        type=MEMORY_TYPES[index % len(MEMORY_TYPES)],
        scope=scope,
        tags=[f'tag-{index % 7}', 'benchmark', 'tur'],
        content=body,
        links=[MemoryLink(uri=f'tur://memory/{index - 1}', relation='derived_from')] if index else [],
        source_session=f'session-{index % 5}',
    )


@pytest.fixture
def memory_factory():
    """Exposes the deterministic Memory builder to the benchmark modules."""
    return make_memory


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """Redirects `Path.home()` and the working directory to an isolated sandbox."""
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    return fake_home


@pytest.fixture
def persona_dir(tmp_path, isolated_home) -> Path:
    """An isolated, project-local persona directory."""
    directory = tmp_path / 'workspace' / '.tur' / 'personas' / 'bench-persona'
    directory.mkdir(parents=True)
    return directory


@pytest.fixture
def populated_memory_bank(persona_dir):
    """A memory bank pre-filled with 100 OKF memories, ready to be read back."""
    from tur.memory import MemoryManager

    manager = MemoryManager(base_dir=persona_dir)
    for index in range(100):
        scope = MemoryScope.PERSONA if index % 4 == 0 else MemoryScope.INCARNATION
        manager.save(make_memory(index, scope=scope, content_size=3))
    return manager


def _concept_file(index: int, total: int) -> str:
    """Renders a single L2 concept node as an OKF markdown document."""
    targets = [f'concept-{(index + offset) % total:03d}' for offset in (1, 7, 23)]
    relations = '\n'.join(
        f'  - target: concepts/active/{target}.md\n    type: refines\n    confidence: 0.9\n'
        f"    created_at: '2026-05-29T12:00:00'"
        for target in targets
    )
    return (
        '---\n'
        "type: 'L2 Concept'\n"
        'node_type: Concept\n'
        f'pinned: {"true" if index % 10 == 0 else "false"}\n'
        f'confidence: 0.{80 + (index % 20)}\n'
        f'retrieval_count: {index % 13}\n'
        f'status: {"archived" if index % 17 == 0 else "active"}\n'
        "timestamp: '2026-05-29T12:00:00'\n"
        'sources:\n'
        f'  - hash-{index:03d}\n'
        'relations:\n'
        f'{relations}\n'
        '---\n\n'
        '# Details\n\n'
        f'Concept {index}: topological constraints render the model deterministic and safe. '
        'The traveler is decoupled from the terrain and the harness.\n'
    )


@pytest.fixture
def concepts_dir(persona_dir) -> Path:
    """A persona directory holding 150 L2 concept nodes stored as OKF markdown."""
    total = 150
    active = persona_dir / 'concepts' / 'active'
    active.mkdir(parents=True)
    for index in range(total):
        (active / f'concept-{index:03d}.md').write_text(_concept_file(index, total), encoding='utf-8')
    return persona_dir


@pytest.fixture
def knowledge_graph() -> nx.DiGraph:
    """A synthetic L2 knowledge graph (500 nodes, ~1500 edges)."""
    total = 500
    graph = nx.DiGraph()
    for index in range(total):
        graph.add_node(
            f'concept-{index:03d}',
            type='Concept',
            content=f'Concept {index}: the council of giants filters every response.',
            pinned=index % 10 == 0,
            confidence=1.0,
            retrieval_count=index % 13,
            status='archived' if index % 17 == 0 else 'active',
        )
    for index in range(total):
        for offset in (1, 7, 23):
            graph.add_edge(f'concept-{index:03d}', f'concept-{(index + offset) % total:03d}', type='refines')
    return graph


@pytest.fixture
def session_state() -> SessionState:
    """A realistic, fully populated session state used to compile the system prompt."""
    persona = Persona(
        name='Ariel',
        version='0.9.0',
        aleph='Curiosity bound by care.',
        principles=[
            Principle(
                name=f'Principle {index}',
                avatar=f'Giant {index}',
                role='Guardian of Invariance',
                constraints=[f'Constraint {index}.{sub}' for sub in range(5)],
                weight=1.0,
            )
            for index in range(12)
        ],
        protocols=[
            PersonaProtocol(name=f'Protocol {index}', trigger='Stagnation', action='Ask What If?') for index in range(8)
        ],
        speech_modulations=[
            SpeechModulation(name=f'Mode {index}', description='Rhetorical style', variance='Medium')
            for index in range(4)
        ],
        metadata={'author': 'benchmark'},
    )
    user = UserProfile(
        name='Architect',
        role='Principal Architect',
        domain_expertise=['python', 'distributed systems', 'ontology'],
        core_values=['symmetry', 'falsifiability'],
    )
    memories = [make_memory(index, content_size=2) for index in range(60)]
    cores = [
        Memory(
            timestamp=BASE_TIMESTAMP,
            type=MemoryType.CORE,
            scope=MemoryScope.PERSONA,
            tags=['core'],
            content=f'Core memory {index}',
            core_type='existential_alignment',
            derived_principle=f'Derived principle {index}',
            ethical_covenant='Never fabricate continuity.',
        )
        for index in range(6)
    ]
    return SessionState(persona=persona, user=user, memories=memories, cores=cores, epilogue='The spark endures.')
