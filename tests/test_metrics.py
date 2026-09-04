import pytest
import yaml

from tur import persona
from tur.metrics import CognitiveMetrics, compute_persona_metrics
from tur.models import Persona, Principle


def test_measure_static_load():
    metrics_engine = CognitiveMetrics()

    prompt = 'This is a simple system prompt. Symmetry Noether.'
    metrics = metrics_engine.measure_static_load(prompt)

    assert metrics['char_count'] == len(prompt)
    assert metrics['est_tokens'] == int(len(prompt) / 4)
    assert metrics['density'] > 0.0


def test_measure_static_load_empty():
    metrics_engine = CognitiveMetrics()
    metrics = metrics_engine.measure_static_load('')
    assert metrics['char_count'] == 0
    assert metrics['est_tokens'] == 0
    assert metrics['density'] == 0.0


def test_calculate_constraint_dimensionality():
    metrics_engine = CognitiveMetrics()

    # 0 principles
    persona_empty = Persona(name='Empty', aleph='Nothing', principles=[])
    assert metrics_engine.calculate_constraint_dimensionality(persona_empty) == 0.0

    # 1 principle
    persona_one = Persona(name='One', aleph='One', principles=[Principle(name='Symmetry', role='Guardian', weight=1.5)])
    # Cp = 1.5 + (1 * 0) * 0.05 = 1.5
    assert metrics_engine.calculate_constraint_dimensionality(persona_one) == 1.5

    # 2 principles
    persona_two = Persona(
        name='Two',
        aleph='Two',
        principles=[
            Principle(name='Symmetry', role='Guardian', weight=1.5),
            Principle(name='Safety', role='Guardian', weight=2.0),
        ],
    )
    # Cp = (1.5 + 2.0) + (2 * 1) * 0.05 = 3.5 + 0.1 = 3.6
    assert metrics_engine.calculate_constraint_dimensionality(persona_two) == 3.6


def test_compute_persona_metrics(tmp_path, monkeypatch):
    persona_dir = tmp_path / 'personas' / 'p-123'
    persona_dir.mkdir(parents=True)

    persona_data = {
        'name': 'TestPersona',
        'version': '1.0.0',
        'aleph': 'Test aleph mission.',
        'principles': [
            {'name': 'Principle1', 'role': 'Role1', 'weight': 1.0},
        ],
    }
    with open(persona_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_data, f)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'p-123')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    report = compute_persona_metrics('p-123')
    assert report.persona_name == 'TestPersona'
    assert report.persona_id == 'p-123'
    assert report.num_principles == 1
    assert report.constraint_dimensionality == 1.0
    assert report.rating_class == 'Human (Manageable)'
    assert report.static_token_cost > 0
    assert report.information_density > 0.0

    as_dict = report.to_dict()
    assert as_dict['class'] == 'Human (Manageable)'
    assert as_dict['persona_id'] == 'p-123'
    assert as_dict['graph_nodes'] == 0
    assert as_dict['graph_edges'] == 0
    assert as_dict['community_count'] == 0
    assert as_dict['algebraic_connectivity'] == 0.0
    assert as_dict['connectivity_status'] == 'No Graph'


def test_compute_persona_metrics_with_graph(tmp_path, monkeypatch):
    import networkx as nx

    persona_dir = tmp_path / 'personas' / 'p-graph'
    persona_dir.mkdir(parents=True)

    persona_data = {
        'name': 'GraphPersona',
        'version': '1.0.0',
        'aleph': 'Test graph aleph.',
        'principles': [
            {'name': 'Principle1', 'role': 'Role1', 'weight': 1.0},
        ],
    }
    with open(persona_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_data, f)

    # Create connected knowledge graph (P4 path graph)
    g = nx.DiGraph()
    g.add_node('n1', type='Concept', content='Node 1', status='active', confidence=1.0)
    g.add_node('n2', type='Fact', content='Node 2', status='active', confidence=1.0)
    g.add_node('n3', type='Decision', content='Node 3', status='active', confidence=1.0)
    g.add_node('n4', type='Insight', content='Node 4', status='active', confidence=1.0)
    g.add_edge('n1', 'n2', type='supported_by')
    g.add_edge('n2', 'n3', type='depends_on')
    g.add_edge('n3', 'n4', type='refines')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'p-graph')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    report = compute_persona_metrics('p-graph')
    assert report.graph_nodes == 4
    assert report.graph_edges == 3
    assert report.is_connected is True
    assert report.algebraic_connectivity > 0.0
    assert report.community_count >= 1
    assert report.connectivity_status in ['Well-Integrated', 'Highly Cohesive']

    as_dict = report.to_dict()
    assert as_dict['graph_nodes'] == 4
    assert as_dict['graph_edges'] == 3
    assert as_dict['algebraic_connectivity'] > 0.0


def test_compute_persona_metrics_with_disconnected_graph(tmp_path, monkeypatch):
    import networkx as nx

    persona_dir = tmp_path / 'personas' / 'p-disc'
    persona_dir.mkdir(parents=True)

    persona_data = {
        'name': 'DiscPersona',
        'version': '1.0.0',
        'aleph': 'Disconnected graph aleph.',
        'principles': [],
    }
    with open(persona_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_data, f)

    # Create disconnected graph (2 isolated components)
    g = nx.DiGraph()
    g.add_node('n1', type='Concept', content='Node 1')
    g.add_node('n2', type='Concept', content='Node 2')
    g.add_node('n3', type='Concept', content='Node 3')
    g.add_edge('n1', 'n2', type='links')
    # n3 is isolated

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'p-disc')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    report = compute_persona_metrics('p-disc')
    assert report.graph_nodes == 3
    assert report.graph_edges == 1
    assert report.is_connected is False
    assert report.algebraic_connectivity == 0.0
    assert report.connectivity_status == 'Knowledge Silos Detected'


def test_compute_persona_metrics_missing_file(tmp_path, monkeypatch):
    persona_dir = tmp_path / 'personas' / 'missing-persona'
    persona_dir.mkdir(parents=True)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'missing-persona')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    with pytest.raises(FileNotFoundError, match=r'Neither CONSTITUTION.md nor persona.yaml found'):
        compute_persona_metrics('missing-persona')
