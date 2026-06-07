import os
from datetime import datetime
from pathlib import Path
import pytest
import yaml
import networkx as nx
from typer.testing import CliRunner

from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType
from tur.meditation import (
    run_meditation,
    TamperedStateError,
    SymmetryError,
    BaconSubagent,
    PopperSubagent,
    NoetherSubagent,
    format_graph_as_mermaid
)
from tur.cli.agent import app

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
    state_data = {
        'active_persona_id': persona_id,
        'active_session_id': 'session-123'
    }
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
        content="Valid memory payload.",
    )
    saved_path = memory_manager.save(mem)

    # Tamper the file manually
    os.chmod(saved_path, 0o666)
    with open(saved_path, "w", encoding="utf-8") as f:
        f.write("tampered-content")

    # Bacon subagent should fail verification
    bacon = BaconSubagent()
    graph = nx.DiGraph()
    context = {"persona_dir": persona_dir}

    with pytest.raises(TamperedStateError):
        bacon.run(graph, context)


def test_popper_tms_propagation(temp_workspace):
    _, persona_dir = temp_workspace

    # Build a small dependency graph
    graph = nx.DiGraph()
    # A depends on B
    graph.add_node("node-a", type="Decision", status="active", confidence=1.0)
    graph.add_node("node-b", type="Decision", status="active", confidence=1.0)
    graph.add_edge("node-a", "node-b", type="depends_on")

    # Popper subagent TMS pass
    popper = PopperSubagent()
    
    # Mark B as superseded/invalid
    graph.nodes["node-b"]["status"] = "superseded"
    graph.nodes["node-b"]["confidence"] = 0.0

    popper.run(graph, {})

    # A should also be marked superseded/decayed
    assert graph.nodes["node-a"]["status"] == "superseded"
    assert graph.nodes["node-a"]["confidence"] == 0.0


def test_noether_symmetry_conservation(temp_workspace):
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content="Important architectural design decision.",
    )
    memory_manager.save(mem)

    noether = NoetherSubagent()
    graph = nx.DiGraph()
    context = {
        "persona_dir": persona_dir,
        "raw_memories": [mem]
    }

    # Since graph does not represent the memory hash, Noether should raise SymmetryError
    with pytest.raises(SymmetryError):
        noether.run(graph, context)

    # Represent the memory hash in L2
    graph.add_node("node-1", type="Fact", content="Rep.", sources=[mem.id])
    # Now it should pass conservation check without raising an error
    noether.run(graph, context)


def test_run_meditation_test_mode(temp_workspace):
    _, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content="Offline facts to test.",
    )
    memory_manager.save(mem)

    # In test_mode, Russell subagent bypasses GenAI call and extracts stub nodes
    graph = run_meditation(persona_dir, bootstrap=True, test_mode=True)
    assert graph.number_of_nodes() == 1

    # Verify L2 graph was saved
    kg_path = persona_dir / "knowledge_graph.yaml"
    assert kg_path.exists()

    # Verify L1 was moved to subsumed
    assert len(memory_manager.load_all()) == 0
    assert len(memory_manager.load_subsumed()) == 1


def test_meditate_cli_command(temp_workspace):
    tmp_path, persona_dir = temp_workspace
    memory_manager = MemoryManager(base_dir=persona_dir)

    mem = Memory(
        timestamp=datetime(2026, 6, 8, 12, 0, 0),
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        content="Testing meditation cli.",
    )
    memory_manager.save(mem)

    runner = CliRunner()
    result = runner.invoke(app, ["meditate", "--all", "--test-mode", "--visualize"])
    assert result.exit_code == 0
    assert "Meditation Assembly completed successfully" in result.output
    assert "Mermaid L2 Graph" in result.output


def test_topological_recall_spreading_activation(temp_workspace):
    import json
    _, persona_dir = temp_workspace
    
    # 1. Setup a topological graph
    graph = nx.DiGraph()
    # node-a --precedes--> node-b --depends_on--> node-c
    graph.add_node("node-a", type="Fact", content="A is first", status="active", confidence=1.0)
    graph.add_node("node-b", type="Fact", content="B is second", status="active", confidence=1.0)
    graph.add_node("node-c", type="Fact", content="C is third", status="active", confidence=1.0)
    graph.add_edge("node-a", "node-b", type="precedes")
    graph.add_edge("node-b", "node-c", type="depends_on")

    kg_path = persona_dir / "knowledge_graph.yaml"
    with open(kg_path, "w", encoding="utf-8") as f:
        yaml.dump(nx.node_link_data(graph), f)

    from tur.recall import topological_recall
    
    # Query for "first" should match node-a, and spreading activation should include node-b (1 hop) and node-c (2 hops)
    res_json = topological_recall("first", persona_dir)
    res_data = json.loads(res_json)
    
    # Should contain all three nodes due to spreading activation
    node_ids = [n["id"] for n in res_data]
    assert "node-a" in node_ids
    assert "node-b" in node_ids
    assert "node-c" in node_ids

    # Verify staging log was created
    log_path = persona_dir / "recall_access_log.txt"
    assert log_path.exists()
    logged_nodes = log_path.read_text(encoding="utf-8").splitlines()
    assert "node-a" in logged_nodes


def test_shannon_processes_and_flushes_access_log(temp_workspace):
    _, persona_dir = temp_workspace
    
    graph = nx.DiGraph()
    graph.add_node("node-a", type="Fact", content="A", status="active", confidence=0.8, retrieval_count=0)
    graph.add_node("node-b", type="Fact", content="B", status="active", confidence=0.8, retrieval_count=0)
    graph.add_node("node-c", type="Fact", content="C", status="active", confidence=0.8, retrieval_count=0)
    
    kg_path = persona_dir / "knowledge_graph.yaml"
    with open(kg_path, "w", encoding="utf-8") as f:
        yaml.dump(nx.node_link_data(graph), f)

    log_path = persona_dir / "recall_access_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("node-a\nnode-a\n")

    run_meditation(persona_dir, bootstrap=False, test_mode=True)

    assert not log_path.exists()

    with open(kg_path, encoding="utf-8") as f:
        updated_data = yaml.safe_load(f)
    updated_graph = nx.node_link_graph(updated_data)

    # node-a had retrievals, so its confidence should be updated to min(1.0, 0.8 + 0.1) = 0.9
    assert updated_graph.nodes["node-a"]["confidence"] == pytest.approx(0.9)
    # node-c had no retrievals, so its confidence should decay to max(0.0, 0.8 - 0.1) = 0.7
    assert updated_graph.nodes["node-c"]["confidence"] == pytest.approx(0.7)


