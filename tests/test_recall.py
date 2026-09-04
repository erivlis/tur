import json

import networkx as nx
import pytest
import yaml

from tur.recall import (
    CognitiveGraphEngine,
    pure_algebraic_connectivity,
    pure_pagerank,
    topological_recall,
)


def test_pure_pagerank_basic():
    g = nx.DiGraph()
    g.add_edge('a', 'b', weight=1.0)
    g.add_edge('b', 'c', weight=1.0)
    g.add_edge('c', 'a', weight=1.0)

    ranks = pure_pagerank(g, alpha=0.85)
    assert len(ranks) == 3
    for n in ['a', 'b', 'c']:
        assert pytest.approx(ranks[n], abs=0.01) == 1.0 / 3.0


def test_pure_pagerank_personalization():
    g = nx.DiGraph()
    g.add_edge('a', 'b', weight=2.0)
    g.add_edge('b', 'c', weight=1.0)
    g.add_edge('x', 'y', weight=1.0)

    ranks = pure_pagerank(g, alpha=0.85, personalization={'a': 10.0})
    assert ranks['a'] > ranks['x']
    assert ranks['b'] > ranks['y']


def test_pure_algebraic_connectivity_known_graphs():
    # P4: 2 - sqrt(2) approx 0.5858
    p4 = nx.path_graph(4)
    lambda2_p4 = pure_algebraic_connectivity(p4)
    assert pytest.approx(lambda2_p4, abs=0.01) == 0.5858

    # K4: 4.0
    k4 = nx.complete_graph(4)
    assert pytest.approx(pure_algebraic_connectivity(k4), abs=0.01) == 4.0

    # Disconnected graph: 0.0
    disc = nx.Graph()
    disc.add_edge(1, 2)
    disc.add_edge(3, 4)
    assert pure_algebraic_connectivity(disc) == 0.0

    # Single node: 0.0
    single = nx.Graph()
    single.add_node(1)
    assert pure_algebraic_connectivity(single) == 0.0


def test_cognitive_graph_engine_spectral_health():
    g = nx.DiGraph()
    g.add_node('n1', type='Concept', content='One')
    g.add_node('n2', type='Concept', content='Two')
    g.add_node('n3', type='Concept', content='Three')
    g.add_edge('n1', 'n2', type='supported_by')
    g.add_edge('n2', 'n3', type='depends_on')

    engine = CognitiveGraphEngine(g)
    health = engine.compute_spectral_health()
    assert health['node_count'] == 3
    assert health['edge_count'] == 2
    assert health['is_connected'] is True
    assert health['algebraic_connectivity'] > 0.0
    assert health['community_count'] >= 1
    assert health['connectivity_status'] in ['Well-Integrated', 'Highly Cohesive']


def test_cognitive_graph_engine_ego_subgraph():
    g = nx.DiGraph()
    for i in range(6):
        g.add_node(f'node-{i}', type='Concept', content=f'Content {i}')
    g.add_edge('node-0', 'node-1')
    g.add_edge('node-0', 'node-2')
    g.add_edge('node-1', 'node-3')
    g.add_edge('node-2', 'node-4')
    g.add_edge('node-4', 'node-5')

    engine = CognitiveGraphEngine(g)
    sub = engine.extract_bounded_ego_subgraph(center_nodes=['node-0'], radius=1, max_nodes=4)
    assert 'node-0' in sub
    assert len(sub) <= 4


def test_cognitive_graph_engine_mermaid():
    g = nx.DiGraph()
    g.add_node('auth', type='Decision', content='Auth decision')
    g.add_node('db', type='Fact', content='DB fact')
    g.add_edge('auth', 'db', type='depends_on')

    engine = CognitiveGraphEngine(g)
    mermaid = engine.format_subgraph_as_mermaid()
    assert 'graph TD' in mermaid
    assert 'auth' in mermaid
    assert 'db' in mermaid
    assert 'depends_on' in mermaid


def test_topological_recall_effort_spectrum(tmp_path):
    persona_dir = tmp_path / 'personas' / 'p-test'
    persona_dir.mkdir(parents=True)

    g = nx.DiGraph()
    g.add_node(
        'sqlite-db',
        type='Decision',
        content='SQLite database engine chosen for speed',
        status='active',
        confidence=1.0,
    )
    g.add_node(
        'file-locking',
        type='Constraint',
        content='File locking ensures safe multiprocessing',
        status='active',
        confidence=1.0,
    )
    g.add_node(
        'state-store',
        type='Fact',
        content='State store persists session notes and memories',
        status='active',
        confidence=1.0,
    )
    g.add_node(
        'superseded-old',
        type='Fact',
        content='Old obsolete mechanism',
        status='superseded',
        confidence=1.0,
    )

    g.add_edge('sqlite-db', 'file-locking', type='depends_on')
    g.add_edge('file-locking', 'state-store', type='supported_by')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    # Effort 0: Fast discrete node
    res0 = json.loads(topological_recall('sqlite', persona_dir, effort=0))
    ids0 = [r['id'] for r in res0]
    assert 'sqlite-db' in ids0
    assert 'superseded-old' not in ids0

    # Effort 2: 1-hop ego neighborhood
    res2 = json.loads(topological_recall('sqlite', persona_dir, effort=2))
    ids2 = [r['id'] for r in res2]
    assert 'sqlite-db' in ids2
    assert 'file-locking' in ids2

    # Effort 5 / deep: HippoRAG PPR + Louvain communities
    res5 = json.loads(topological_recall('sqlite', persona_dir, effort=5))
    ids5 = [r['id'] for r in res5]
    assert 'sqlite-db' in ids5
    assert any('score' in r for r in res5)
    assert any('community' in r for r in res5)

    # Deep alias
    res_deep = json.loads(topological_recall('sqlite', persona_dir, deep=True))
    assert 'sqlite-db' in [r['id'] for r in res_deep]

    # Effort 8: Exhaustive TMS + Git verification
    res8 = json.loads(topological_recall('sqlite', persona_dir, effort=8))
    assert 'sqlite-db' in [r['id'] for r in res8]
    assert any('git_status' in r for r in res8)

    # Mermaid output
    mermaid_out = topological_recall('sqlite', persona_dir, effort=5, mermaid=True)
    assert '`mermaid' in mermaid_out
    assert 'graph TD' in mermaid_out


def test_topological_recall_l1_fallback(tmp_path):
    persona_dir = tmp_path / 'personas' / 'p-fallback'
    persona_dir.mkdir(parents=True)

    from tur.memory import MemoryManager
    from tur.models import Memory, MemoryScope, MemoryType

    mgr = MemoryManager(base_dir=persona_dir)
    mgr.save(Memory(type=MemoryType.FACT, scope=MemoryScope.INCARNATION, content='L1 memory about postgresql backend'))

    res = topological_recall('postgresql', persona_dir)
    assert 'postgresql' in res

    res_missing = topological_recall('nonexistent_token_xyz', persona_dir)
    assert 'No memories found' in res_missing
