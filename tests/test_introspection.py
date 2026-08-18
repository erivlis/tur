import os
from datetime import datetime
from pathlib import Path

import networkx as nx
import pytest
import yaml
from typer.testing import CliRunner

from tur.cli.agent import app
from tur.introspection import (
    BaconSubagent,
    IntrospectionAssembly,
    NoetherSubagent,
    PopperSubagent,
    SymmetryError,
    TamperedStateError,
    run_introspection,
)
from tur.memory import MemoryManager
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

    # Bacon subagent should fail verification
    bacon = BaconSubagent()
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

    # Popper subagent TMS pass
    popper = PopperSubagent()

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

    noether = NoetherSubagent()
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

    from tur.recall import topological_recall

    # Query for "first" should match node-a, and spreading activation should include node-b (1 hop) and node-c (2 hops)
    res_json = topological_recall('first', persona_dir)
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

    # Run Popper Subagent
    subagent = PopperSubagent()
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
    config = {'subagents': [{'name': 'CustomPopper', 'class': 'tur.introspection.PopperSubagent'}]}
    assembly = IntrospectionAssembly(config)
    assert len(assembly.agents) == 1
    assert isinstance(assembly.agents[0], PopperSubagent)

    # 2. Test invalid import path raising ImportError
    bad_config = {'subagents': [{'name': 'BadAgent', 'class': 'nonexistent_module.NonexistentClass'}]}
    with pytest.raises(ImportError) as exc:
        IntrospectionAssembly(bad_config)
    assert 'Failed to load compaction subagent' in str(exc.value)

    # 3. Test empty configuration fallback to default assembly
    empty_assembly = IntrospectionAssembly(None)
    assert len(empty_assembly.agents) == 9
    from tur.introspection import BaconSubagent

    assert isinstance(empty_assembly.agents[0], BaconSubagent)


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
    assert '# TUR DELEGATION: Council Introspection Request' in result.output
    assert 'No local `GEMINI_API_KEY` was found in the environment' in result.output
    assert 'Test delegation fact.' in result.output
    assert 'uv run python -c' in result.output


def test_relationship_signature_constraints(temp_workspace):
    """Test that RussellSubagent rejects invalid edges that violate signature constraints."""
    from tur.introspection import ExtractedEdge, ExtractedGraph, RussellSubagent

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

    subagent = RussellSubagent()
    updated_graph, _ = subagent._merge_extracted_graph(graph, extracted, {})

    # Neither of the invalid edges should be added to the graph
    assert not updated_graph.has_edge('decision-a', 'concept-b')


def test_tms_propagation_on_refines(temp_workspace):
    """Test that PopperSubagent deactivates refiners when the refined node is superseded."""
    from tur.introspection import PopperSubagent

    graph = nx.DiGraph()
    # node-a refines node-b
    graph.add_node('node-a', type='Concept', content='Specific concept', status='active', confidence=1.0)
    graph.add_node('node-b', type='Concept', content='Base concept', status='active', confidence=1.0)
    graph.add_edge('node-a', 'node-b', type='refines')

    # Deactivate the base concept
    graph.nodes['node-b']['status'] = 'superseded'
    graph.nodes['node-b']['confidence'] = 0.0

    subagent = PopperSubagent()
    subagent._propagate_deactivations(graph)

    # Refiner node-a should also be deactivated
    assert graph.nodes['node-a']['status'] == 'superseded'
    assert graph.nodes['node-a']['confidence'] == 0.0


def test_ep0003_policy_vs_mechanism_class_mappings():
    """Verify that all functional engine classes and legacy Council aliases are correctly exported per EP-0003."""
    from tur.introspection import (
        BaconSubagent,
        BoundaryEnforcer,
        ClarityDistiller,
        CouncilSubagent,
        ExplorerSubagent,
        FeynmanSubagent,
        GraphPruner,
        HebbianGraphDecayer,
        IntegrityVerifier,
        IntrospectionSubagent,
        MaharalSubagent,
        NoetherSubagent,
        NoveltyExplorer,
        OntologyExtractor,
        PopperSubagent,
        RussellSubagent,
        ShannonSubagent,
        StewardSubagent,
        SymmetryValidator,
        TruthMaintenanceEngine,
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

    # Verify legacy alias equality
    assert CouncilSubagent is IntrospectionSubagent
    assert BaconSubagent is IntegrityVerifier
    assert RussellSubagent is OntologyExtractor
    assert PopperSubagent is TruthMaintenanceEngine
    assert NoetherSubagent is SymmetryValidator
    assert ExplorerSubagent is NoveltyExplorer
    assert ShannonSubagent is HebbianGraphDecayer
    assert MaharalSubagent is BoundaryEnforcer
    assert FeynmanSubagent is ClarityDistiller
    assert StewardSubagent is GraphPruner

