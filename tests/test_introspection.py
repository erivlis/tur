import os
from datetime import datetime
from pathlib import Path

import networkx as nx
import pytest
import yaml
from typer.testing import CliRunner

from tur.cli.agent import app
from tur.memory import MemoryManager
from tur.memory.introspection import (
    BoundaryEnforcer,
    ExtractedEdge,
    ExtractedGraph,
    ExtractedNode,
    IntegrityVerifier,
    IntrospectionAssembly,
    NoveltyExplorer,
    OntologyExtractor,
    SymmetryError,
    SymmetryValidator,
    TamperedStateError,
    TruthMaintenanceEngine,
    format_graph_as_mermaid,
    load_l2_graph_from_okf,
    run_introspection,
    save_l2_graph_to_okf,
)
from tur.models import Memory, MemoryScope, MemoryType


@pytest.fixture
def temp_workspace(tmp_path, monkeypatch):
    # Setup directories
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    (personas_dir / persona_id / 'memories' / 'archive').mkdir(parents=True)
    (personas_dir / persona_id / 'memories' / 'subsumed').mkdir(parents=True)

    # Fake persona index
    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    persona_yaml = {
        'name': 'Ariel',
        'version': '5.4.0',
        'model': 'gemini-3.1-pro-preview',
        'aleph': 'To safeguard reality.',
        'principles': [],
    }
    with open(personas_dir / persona_id / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_yaml, f)

    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    # Set active persona state
    state_data = {'active_persona_id': persona_id, 'active_session_id': 'session-123'}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    return tmp_path, personas_dir / persona_id


def test_bacon_integrity_verification(temp_workspace):
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Valid memory payload.',
    )
    saved_path = memory_manager.save(mem)

    # Tamper the file manually
    os.chmod(saved_path, 0o666)
    with open(saved_path, 'w', encoding='utf-8') as f:
        f.write('tampered-content')

    # IntegrityVerifier should fail verification
    bacon = IntegrityVerifier()
    graph = nx.DiGraph()
    context = {'persona_dir': persona_dir}

    with pytest.raises(TamperedStateError):
        bacon.run(graph, context)


def test_popper_tms_propagation(temp_workspace):
    _, _persona_dir = temp_workspace

    # Build a small dependency graph
    graph = nx.DiGraph()
    # A depends on B
    graph.add_node('node-a', type='Decision', status='active', confidence=1.0)
    graph.add_node('node-b', type='Decision', status='active', confidence=1.0)
    graph.add_edge('node-a', 'node-b', type='depends_on')

    # Popper TMS pass
    popper = TruthMaintenanceEngine()

    # Mark B as superseded/invalid
    graph.nodes['node-b']['status'] = 'superseded'
    graph.nodes['node-b']['confidence'] = 0.0

    popper.run(graph, {})

    # A should also be marked superseded/decayed
    assert graph.nodes['node-a']['status'] == 'superseded'
    assert graph.nodes['node-a']['confidence'] == 0.0


def test_noether_symmetry_conservation(temp_workspace):
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Important architectural design decision.',
    )
    memory_manager.save(mem)

    noether = SymmetryValidator()
    graph = nx.DiGraph()
    context = {'persona_dir': persona_dir, 'raw_memories': [mem]}

    # Since graph does not represent the memory hash, Noether should raise SymmetryError
    with pytest.raises(SymmetryError):
        noether.run(graph, context)

    # Represent the memory hash in L2
    graph.add_node('node-1', type='Fact', content='Rep.', sources=[mem.id])
    # Now it should pass conservation check without raising an error
    noether.run(graph, context)


def test_run_introspection_test_mode(temp_workspace):
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Offline facts to test.',
    )
    memory_manager.save(mem)

    # In test_mode, Russell subagent bypasses GenAI call and extracts stub nodes
    graph = run_introspection(persona_dir, bootstrap=True, test_mode=True)
    assert graph.number_of_nodes() == 1

    # Verify L2 graph was saved
    kg_path = persona_dir / 'knowledge_graph.yaml'
    assert kg_path.exists()

    # Verify L1 was moved to subsumed
    assert len(memory_manager.load_all()) == 0
    assert len(memory_manager.load_subsumed()) == 1


def test_introspect_cli_command(temp_workspace):
    _tmp_path, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        content='Testing introspection cli.',
    )
    memory_manager.save(mem)

    runner = CliRunner()
    result = runner.invoke(app, ['introspect', '--all', '--test-mode', '--visualize'])
    assert result.exit_code == 0
    assert 'Introspection Assembly completed successfully' in result.output
    assert 'Mermaid L2 Graph' in result.output


def test_topological_recall_spreading_activation(temp_workspace):
    import json

    _, persona_dir = temp_workspace

    # 1. Setup a topological graph
    graph = nx.DiGraph()
    # node-a --precedes--> node-b --depends_on--> node-c
    graph.add_node('node-a', type='Fact', content='A is first', status='active', confidence=1.0)
    graph.add_node('node-b', type='Fact', content='B is second', status='active', confidence=1.0)
    graph.add_node('node-c', type='Fact', content='C is third', status='active', confidence=1.0)
    graph.add_edge('node-a', 'node-b', type='precedes')
    graph.add_edge('node-b', 'node-c', type='depends_on')

    kg_path = persona_dir / 'knowledge_graph.yaml'
    with open(kg_path, 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(graph), f)

    from tur.memory.recall import topological_recall

    # Query for "first" with effort=5 should match node-a, and spreading activation should include node-b and node-c
    res_json = topological_recall('first', persona_dir, effort=5)
    res_data = json.loads(res_json)

    # Should contain all three nodes due to spreading activation
    node_ids = [n['id'] for n in res_data]
    assert 'node-a' in node_ids
    assert 'node-b' in node_ids
    assert 'node-c' in node_ids

    # Verify staging log was created
    log_path = persona_dir / 'recall_access_log.txt'
    assert log_path.exists()
    logged_nodes = log_path.read_text(encoding='utf-8').splitlines()
    assert 'node-a' in logged_nodes


def test_shannon_processes_and_flushes_access_log(temp_workspace):
    _, persona_dir = temp_workspace

    graph = nx.DiGraph()
    graph.add_node('node-a', type='Fact', content='A', status='active', confidence=0.8, retrieval_count=0)
    graph.add_node('node-b', type='Fact', content='B', status='active', confidence=0.8, retrieval_count=0)
    graph.add_node('node-c', type='Fact', content='C', status='active', confidence=0.8, retrieval_count=0)

    kg_path = persona_dir / 'knowledge_graph.yaml'
    with open(kg_path, 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(graph), f)

    log_path = persona_dir / 'recall_access_log.txt'
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('node-a\nnode-a\n')

    run_introspection(persona_dir, bootstrap=False, test_mode=True)

    assert not log_path.exists()

    with open(kg_path, encoding='utf-8') as f:
        updated_data = yaml.safe_load(f)
    updated_graph = nx.node_link_graph(updated_data)

    # node-a had retrievals, so its confidence should be updated to min(1.0, 0.8 + 0.1) = 0.9
    assert updated_graph.nodes['node-a']['confidence'] == pytest.approx(0.9)
    # node-c had no retrievals, so its confidence should decay to max(0.0, 0.8 - 0.1) = 0.7
    assert updated_graph.nodes['node-c']['confidence'] == pytest.approx(0.7)


def test_popper_belief_revision_conflict_resolution():
    graph = nx.DiGraph()
    # node-a is older, node-b is newer
    graph.add_node(
        'node-a',
        type='Fact',
        content='Python is slow',
        status='active',
        confidence=1.0,
        created_at='2026-05-01T10:00:00Z',
    )
    graph.add_node(
        'node-b',
        type='Fact',
        content='Python is fast',
        status='active',
        confidence=1.0,
        created_at='2026-05-01T11:00:00Z',
    )
    graph.add_node(
        'node-c',
        type='Insight',
        content='Thus, we must avoid Python',
        status='active',
        confidence=1.0,
        created_at='2026-05-01T12:00:00Z',
    )

    # Add relationships
    graph.add_edge('node-a', 'node-b', type='contradicts')
    graph.add_edge('node-c', 'node-a', type='depends_on')

    # Run TMS
    subagent = TruthMaintenanceEngine()
    updated_graph, _ = subagent.run(graph, {})

    # node-a should be superseded because it is older than node-b
    assert updated_graph.nodes['node-a']['status'] == 'superseded'
    assert updated_graph.nodes['node-a']['confidence'] == 0.0

    # node-b should remain active
    assert updated_graph.nodes['node-b']['status'] == 'active'
    assert updated_graph.nodes['node-b']['confidence'] == 1.0

    # A superseded_by edge should have been created u -> v
    assert updated_graph.has_edge('node-a', 'node-b')
    assert updated_graph['node-a']['node-b']['type'] == 'superseded_by'

    # node-c depends on node-a, so it should be deactivated recursively
    assert updated_graph.nodes['node-c']['status'] == 'superseded'
    assert updated_graph.nodes['node-c']['confidence'] == 0.0

    # A refuted_by edge should record the trace: c refuted_by a
    assert updated_graph.has_edge('node-c', 'node-a')
    assert updated_graph['node-c']['node-a']['type'] == 'refuted_by'


def test_pluggable_compaction_pipeline_dynamic_loading():
    # 1. Test successful custom loading
    config = {'subagents': [{'name': 'CustomTMS', 'class': 'tur.memory.introspection.TruthMaintenanceEngine'}]}
    assembly = IntrospectionAssembly(config)
    assert len(assembly.agents) == 1
    assert isinstance(assembly.agents[0], TruthMaintenanceEngine)

    # 2. Test invalid import path raising ImportError
    bad_config = {'subagents': [{'name': 'BadAgent', 'class': 'nonexistent_module.NonexistentClass'}]}
    with pytest.raises(ImportError) as exc:
        IntrospectionAssembly(bad_config)
    assert 'Failed to load compaction subagent' in str(exc.value)

    # 3. Test empty configuration fallback to default assembly
    empty_assembly = IntrospectionAssembly(None)
    assert len(empty_assembly.agents) == 9
    from tur.memory.introspection import IntegrityVerifier

    assert isinstance(empty_assembly.agents[0], IntegrityVerifier)


def test_harness_delegation_error_cli(temp_workspace, monkeypatch):
    """Test that introspect command gracefully delegates when GEMINI_API_KEY is missing."""

    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Test delegation fact.',
    )
    memory_manager.save(mem)

    # Ensure GEMINI_API_KEY is not in env and test_mode is False
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)

    runner = CliRunner()
    result = runner.invoke(app, ['introspect', '--all'])

    assert result.exit_code == 0
    assert '# TUR DELEGATION: Ontological Concept Extraction Request' in result.output
    assert 'Test delegation fact.' in result.output
    assert 'tur introspect --commit' in result.output
    assert 'Boundary Invariant' in result.output
    assert 'Subagent Execution (Recommended)' in result.output


def test_relationship_signature_constraints(temp_workspace):
    """Test that OntologyExtractor rejects invalid edges that violate signature constraints."""
    from tur.memory.introspection import ExtractedEdge, ExtractedGraph, OntologyExtractor

    graph = nx.DiGraph()
    graph.add_node('decision-a', type='Decision', content='First decision', status='active', confidence=1.0)
    graph.add_node('concept-b', type='Concept', content='General concept', status='active', confidence=1.0)

    # precedes from Decision to Concept should be rejected
    # refines between Decision and Concept should be rejected
    extracted = ExtractedGraph(
        nodes=[],
        edges=[
            ExtractedEdge(source='decision-a', target='concept-b', type='precedes', confidence=1.0),
            ExtractedEdge(source='decision-a', target='concept-b', type='refines', confidence=1.0),
        ],
    )

    subagent = OntologyExtractor()
    updated_graph, _ = subagent._merge_extracted_graph(graph, extracted, {})

    # Neither of the invalid edges should be added to the graph
    assert not updated_graph.has_edge('decision-a', 'concept-b')


def test_tms_propagation_on_refines(temp_workspace):
    """Test that TruthMaintenanceEngine deactivates refiners when the refined node is superseded."""

    graph = nx.DiGraph()
    # node-a refines node-b
    graph.add_node('node-a', type='Concept', content='Specific concept', status='active', confidence=1.0)
    graph.add_node('node-b', type='Concept', content='Base concept', status='active', confidence=1.0)
    graph.add_edge('node-a', 'node-b', type='refines')

    # Deactivate the base concept
    graph.nodes['node-b']['status'] = 'superseded'
    graph.nodes['node-b']['confidence'] = 0.0

    subagent = TruthMaintenanceEngine()
    subagent._propagate_deactivations(graph)

    # Refiner node-a should also be deactivated
    assert graph.nodes['node-a']['status'] == 'superseded'
    assert graph.nodes['node-a']['confidence'] == 0.0


def test_policy_vs_mechanism_class_mappings():
    """Verify functional engine classes are correctly exported and subclass IntrospectionSubagent."""
    from tur.memory.introspection import (
        BoundaryEnforcer,
        ClarityDistiller,
        GraphPruner,
        HebbianGraphDecayer,
        IntegrityVerifier,
        IntrospectionSubagent,
        NoveltyExplorer,
        OntologyExtractor,
    )

    # Verify inheritance from IntrospectionSubagent
    assert issubclass(IntegrityVerifier, IntrospectionSubagent)
    assert issubclass(OntologyExtractor, IntrospectionSubagent)
    assert issubclass(TruthMaintenanceEngine, IntrospectionSubagent)
    assert issubclass(SymmetryValidator, IntrospectionSubagent)
    assert issubclass(NoveltyExplorer, IntrospectionSubagent)
    assert issubclass(HebbianGraphDecayer, IntrospectionSubagent)
    assert issubclass(BoundaryEnforcer, IntrospectionSubagent)
    assert issubclass(ClarityDistiller, IntrospectionSubagent)
    assert issubclass(GraphPruner, IntrospectionSubagent)


def test_okf_save_and_load_roundtrip(temp_workspace):
    _, persona_dir = temp_workspace

    graph = nx.DiGraph()
    graph.add_node(
        'active-concept',
        type='Concept',
        content='# Details\n\nActive conceptual body text.',
        status='active',
        confidence=1.0,
        pinned=True,
        sources=['src-1'],
        retrieval_count=5,
    )
    graph.add_node(
        'archived-concept',
        type='Concept',
        content='Low confidence archived node.',
        status='archived',
        confidence=0.1,
        pinned=False,
        sources=[],
    )
    graph.add_edge('active-concept', 'archived-concept', type='refines', confidence=0.9)

    save_l2_graph_to_okf(graph, persona_dir)

    # Active file should exist in concepts/active
    active_path = persona_dir / 'concepts' / 'active' / 'active-concept.md'
    assert active_path.exists()

    # Archived file should exist in concepts/archive
    archived_path = persona_dir / 'concepts' / 'archive' / 'archived-concept.md'
    assert archived_path.exists()

    # Load OKF back into graph
    loaded_graph = load_l2_graph_from_okf(persona_dir)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == 2
    assert loaded_graph.has_edge('active-concept', 'archived-concept')
    assert loaded_graph.nodes['active-concept']['pinned'] is True
    assert loaded_graph.nodes['active-concept']['confidence'] == 1.0


def test_okf_load_empty_or_missing(tmp_path):
    assert load_l2_graph_from_okf(tmp_path) is None

    (tmp_path / 'concepts' / 'active').mkdir(parents=True)
    assert load_l2_graph_from_okf(tmp_path) is None


def test_novelty_explorer_disconnected_components():
    explorer = NoveltyExplorer()
    graph = nx.DiGraph()
    graph.add_node('part-a', type='Concept', content='A')
    graph.add_node('part-b', type='Concept', content='B')

    # Two disconnected nodes
    updated, _ = explorer.run(graph, {})
    assert updated.has_node('exploration-horizon-gap')
    assert updated.nodes['exploration-horizon-gap']['type'] == 'OpenQuestion'
    assert updated.has_edge('part-a', 'exploration-horizon-gap')
    assert updated.has_edge('part-b', 'exploration-horizon-gap')


def test_boundary_enforcer_path_traversal():
    enforcer = BoundaryEnforcer()
    graph = nx.DiGraph()
    graph.add_node('../bad-node', type='Concept', content='Bad')

    with pytest.raises(ValueError, match='CONTAINMENT FAILURE'):
        enforcer.run(graph, {})


def test_format_graph_as_mermaid():
    graph = nx.DiGraph()
    graph.add_node('d1', type='Decision')
    graph.add_node('c1', type='Constraint')
    graph.add_node('f1', type='Fact')
    graph.add_node('gen1', type='Concept')
    graph.add_edge('d1', 'c1', type='depends_on')

    mermaid = format_graph_as_mermaid(graph)
    assert 'graph TD' in mermaid
    assert 'd1["Decision"]' in mermaid
    assert 'c1{"Constraint"}' in mermaid
    assert 'f1("[Fact]")' in mermaid
    assert 'gen1["Concept"]' in mermaid
    assert 'd1 -->|depends_on| c1' in mermaid


def test_russell_cycle_enforcement_and_synonym_unification():
    graph = nx.DiGraph()
    graph.add_node('node-a', type='Decision', content='Base content', sources=['s1'], pinned=False)
    graph.add_node('node-b', type='Decision', content='B content', sources=['s2'], pinned=False)

    # 1. Unification: node-a already exists, merging new content into it
    extracted = ExtractedGraph(
        nodes=[
            ExtractedNode(
                id='node-a',
                type='Decision',
                content='Extended info',
                sources=['s3'],
                pinned=True,
            )
        ],
        edges=[
            ExtractedEdge(source='node-a', target='node-b', type='precedes', confidence=1.0),
            ExtractedEdge(source='node-b', target='node-a', type='precedes', confidence=1.0),
        ],
    )

    extractor = OntologyExtractor()
    merged, _ = extractor._merge_extracted_graph(graph, extracted, {})

    # Check unification
    assert 'Base content | Extended info' in merged.nodes['node-a']['content']
    assert set(merged.nodes['node-a']['sources']) == {'s1', 's3'}
    assert merged.nodes['node-a']['pinned'] is True

    # Check DAG cycle enforcement: node-a -> node-b is added, but node-b -> node-a would create a cycle and is dropped
    assert merged.has_edge('node-a', 'node-b')
    assert not merged.has_edge('node-b', 'node-a')


def test_metaphor_for_and_cognitive_mapping():
    """Verify metaphor_for and analogy_of relations are correctly extracted and preserved."""
    graph = nx.DiGraph()
    extracted = ExtractedGraph(
        nodes=[
            ExtractedNode(
                id='traveler-entity',
                type='Concept',
                content='Narrative persona identity vehicle.',
            ),
            ExtractedNode(
                id='persistent-identity-state',
                type='Fact',
                content='Global ~/.tur/ state directory.',
            ),
            ExtractedNode(
                id='merkle-dag',
                type='Concept',
                content='Content-addressable directed acyclic graph.',
            ),
            ExtractedNode(
                id='git-commit-history',
                type='Fact',
                content='Git commit hash history.',
            ),
        ],
        edges=[
            ExtractedEdge(
                source='traveler-entity',
                target='persistent-identity-state',
                type='metaphor_for',
                confidence=1.0,
            ),
            ExtractedEdge(
                source='merkle-dag',
                target='git-commit-history',
                type='analogy_of',
                confidence=0.95,
            ),
        ],
    )

    extractor = OntologyExtractor()
    merged, _ = extractor._merge_extracted_graph(graph, extracted, {})

    assert merged.has_edge('traveler-entity', 'persistent-identity-state')
    assert merged.edges['traveler-entity', 'persistent-identity-state']['type'] == 'metaphor_for'
    assert merged.edges['traveler-entity', 'persistent-identity-state']['confidence'] == 1.0

    assert merged.has_edge('merkle-dag', 'git-commit-history')
    assert merged.edges['merkle-dag', 'git-commit-history']['type'] == 'analogy_of'

    # Test mermaid diagram formatting for metaphor_for (dotted arrow)
    mermaid = format_graph_as_mermaid(merged)
    assert 'traveler-entity -.->|metaphor_for| persistent-identity-state' in mermaid
    assert 'merkle-dag -->|analogy_of| git-commit-history' in mermaid


def test_synonym_normalization_and_custom_persona_ontology():
    """Verify synonym drift reduction and persona declarative custom edge types."""
    graph = nx.DiGraph()
    extracted = ExtractedGraph(
        nodes=[
            ExtractedNode(id='precedent-case', type='decision', content='Court decision 123.'),
            ExtractedNode(id='current-matter', type='decision', content='Active legal matter.'),
            ExtractedNode(id='system-vehicle', type='concept', content='Poetic vehicle.'),
            ExtractedNode(id='engine-tenor', type='fact', content='Deterministic engine.'),
        ],
        edges=[
            # Synonyms to normalize
            ExtractedEdge(source='system-vehicle', target='engine-tenor', type='is_metaphor_for'),
            # Custom edge type declared in persona config
            ExtractedEdge(source='current-matter', target='precedent-case', type='cites_precedent'),
        ],
    )

    context = {
        'compaction_config': {
            'ontology': {
                'custom_edge_types': ['cites_precedent'],
            }
        }
    }

    extractor = OntologyExtractor()
    merged, _ = extractor._merge_extracted_graph(graph, extracted, context)

    # Node types normalized to canonical PascalCase
    assert merged.nodes['precedent-case']['type'] == 'Decision'
    assert merged.nodes['system-vehicle']['type'] == 'Concept'
    assert merged.nodes['engine-tenor']['type'] == 'Fact'

    # Synonym normalized to canonical metaphor_for
    assert merged.has_edge('system-vehicle', 'engine-tenor')
    assert merged.edges['system-vehicle', 'engine-tenor']['type'] == 'metaphor_for'

    # Declared custom edge type accepted
    assert merged.has_edge('current-matter', 'precedent-case')
    assert merged.edges['current-matter', 'precedent-case']['type'] == 'cites_precedent'


def test_introspection_progress_callback(temp_workspace):
    """Verify IntrospectionAssembly and run_introspection execute progress_callback across all 9 stages."""
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Progress telemetry test fact.',
    )
    memory_manager.save(mem)

    steps_recorded = []

    def callback(current: int, total: int, description: str) -> None:
        steps_recorded.append((current, total, description))

    graph = run_introspection(persona_dir, bootstrap=True, test_mode=True, progress_callback=callback)

    assert graph.number_of_nodes() == 1
    assert len(steps_recorded) == 9
    assert steps_recorded[0] == (1, 9, 'Verifying cryptographic Merkle integrity...')
    assert steps_recorded[-1] == (9, 9, 'Pruning subsumed & orphaned graph edges...')
