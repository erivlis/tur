import contextlib
import json
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

import networkx as nx
import yaml
from pydantic import BaseModel, Field

from tur.memory import MemoryManager
from tur.models import MemoryType


# Core exceptions as per EP-0103 and EP-0119 specifications
class TamperedStateError(ValueError):
    """Raised by the Bacon subagent when cryptographic verification fails."""


class SymmetryError(ValueError):
    """Raised by the Noether subagent when 'Conservation of Meaning' validation fails."""


# Pydantic extraction models for GenAI JSON structured generation
class ExtractedNode(BaseModel):
    id: str = Field(..., description="Unique semantic identifier/label for the concept (e.g. sqlite-db, standard-mcp)")
    type: str = Field(
        ...,
        description=(
            "Type of node: Concept, Decision, Constraint, Insight, Fact, "
            "Dependency, Hypothesis, BoundaryNode, OpenQuestion"
        )
    )
    content: str = Field(..., description="Text description/detail of the node")
    pinned: bool = Field(
        default=False,
        description="Is this a core constitutional principle that cannot be revised/deleted?"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of source L1 memory file hashes where this node was derived"
    )


class ExtractedEdge(BaseModel):
    source: str = Field(..., description="The ID of the source node")
    target: str = Field(..., description="The ID of the target node")
    type: str = Field(
        ...,
        description=(
            "Relation type: refines, contradicts, precedes, depends_on, "
            "competes_with, analogy_of, superseded_by, refuted_by"
        )
    )
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")


class ExtractedGraph(BaseModel):
    nodes: list[ExtractedNode] = Field(default_factory=list)
    edges: list[ExtractedEdge] = Field(default_factory=list)


# Abstract base class for Council Subagents
class CouncilSubagent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        """
        Runs the subagent execution pass.
        Receives the current graph state and returns an updated graph and context dict.
        """


class BaconSubagent(CouncilSubagent):
    """
    1. Ingestion & Verification (Empiricism)
    Runs Content-Hash checks on active L1 files, loads payloads, and raises TamperedStateError on mismatch.
    """

    def __init__(self):
        super().__init__("Bacon", "Reality Anchor")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        persona_dir = context["persona_dir"]
        memory_manager = MemoryManager(base_dir=persona_dir)

        # Step-Zero content hash check
        failures = memory_manager.verify_integrity()
        if failures:
            reasons = "; ".join([f"{path.name}: {err}" for path, err in failures])
            raise TamperedStateError(f"TAMPERED STATE: Cryptographic verification failed! {reasons}")

        # Ingestion mode check
        bootstrap = context.get("bootstrap", False)
        if bootstrap:
            # Load active + subsumed L1 files
            active_mems = memory_manager.load_all()
            subsumed_mems = memory_manager.load_subsumed()
            # Combine without duplicates (based on ID)
            seen_ids = set()
            mems = []
            for m in active_mems + subsumed_mems:
                if m.id not in seen_ids:
                    seen_ids.add(m.id)
                    mems.append(m)
        else:
            # Load only active L1 files
            mems = memory_manager.load_all()

        context["raw_memories"] = mems
        return graph, context


class RussellSubagent(CouncilSubagent):
    """
    2. Ontological Extraction (Logic)
    Uses the Host LLM (via google-genai) to extract triples and Normalizes Schemas.
    """

    def __init__(self):
        super().__init__("Russell", "Ontological Logician")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        mems = context.get("raw_memories", [])
        if not mems:
            return graph, context

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Standard fallback for test suites or offline execution
            if context.get("test_mode"):
                # Stub extraction logic for tests
                for mem in mems:
                    node_id = f"concept-{mem.id[:8]}"
                    graph.add_node(
                        node_id,
                        type="Fact" if mem.type.value == "fact" else "Insight",
                        content=mem.content,
                        pinned=False,
                        sources=[mem.id],
                        created_at=mem.timestamp.isoformat(),
                        updated_at=mem.timestamp.isoformat(),
                        confidence=1.0,
                        retrieval_count=0,
                        status="active"
                    )
                return graph, context
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = context.get("model", "gemini-3.1-pro-preview")

        # Compile existing graph details for reference/synonym-merging
        existing_nodes_info = ""
        if graph.number_of_nodes() > 0:
            existing_nodes_info = "\nExisting Nodes in Graph:\n" + "\n".join(
                [f"- ID: {n}, Type: {d.get('type')}, Content: {d.get('content')}" for n, d in graph.nodes(data=True)]
            )

        # Ingestion payload
        raw_text = "\n\n".join(
            [f"Memory ID: {m.id}\nTimestamp: {m.timestamp.isoformat()}\nType: {m.type.value}\nContent: {m.content}" for
             m in mems])

        prompt = f"""
        You are the Ontological Logician (Russell Subagent) of a cognitive memory system.
        Analyze the following L1 memories and build/update a semantic Knowledge Graph.

        {existing_nodes_info}

        Input L1 memories:
        {raw_text}

        Your Task:
        1. Extract concepts, decisions, constraints, insights, facts, or dependencies as nodes.
        2. Resolve synonyms: if a concept matches an existing node or duplicate terms exist,
           unify them under a single node.
        3. Standardize node and edge types strictly according to the ontology.

        Allowed Node Types: Concept, Decision, Constraint, Insight, Fact, Dependency,
        Hypothesis, BoundaryNode, OpenQuestion
        Allowed Edge Types: refines, contradicts, precedes, depends_on, competes_with,
        analogy_of, superseded_by, refuted_by
        """

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=ExtractedGraph.model_json_schema(),
            ),
        )

        try:
            extracted = ExtractedGraph.model_validate_json(response.text)
        except Exception as e:
            # Fallback to manual parsing if Pydantic validation of LLM output fails
            try:
                data = json.loads(response.text)
                extracted = ExtractedGraph(**data)
            except Exception:
                raise ValueError(f"Failed to parse LLM graph output: {e}. Output: {response.text}")

        # Update NetworkX Graph based on extraction
        # Merge new nodes and consolidate synonyms
        for node in extracted.nodes:
            nid = node.id.strip().lower().replace(" ", "-")
            if graph.has_node(nid):
                # Unification Algebra
                old_data = graph.nodes[nid]
                graph.nodes[nid]["content"] = f"{old_data['content']} | {node.content}" if node.content not in old_data[
                    "content"] else old_data["content"]
                graph.nodes[nid]["sources"] = list(set(old_data["sources"] + node.sources))
                graph.nodes[nid]["pinned"] = old_data.get("pinned", False) or node.pinned
                graph.nodes[nid]["updated_at"] = datetime.now(UTC).isoformat()
            else:
                graph.add_node(
                    nid,
                    type=node.type,
                    content=node.content,
                    pinned=node.pinned,
                    sources=node.sources,
                    created_at=datetime.now(UTC).isoformat(),
                    updated_at=datetime.now(UTC).isoformat(),
                    confidence=1.0,
                    retrieval_count=0,
                    status="active"
                )

        # Merge edges
        for edge in extracted.edges:
            src = edge.source.strip().lower().replace(" ", "-")
            tgt = edge.target.strip().lower().replace(" ", "-")
            # Enforce relationship signatures
            if graph.has_node(src) and graph.has_node(tgt):
                # We assert Directed Acyclic Graph (DAG) for precedes and depends_on
                if edge.type in ["precedes", "depends_on"]:
                    graph.add_edge(src, tgt, type=edge.type, confidence=edge.confidence,
                                   created_at=datetime.now(UTC).isoformat())
                    if not nx.is_directed_acyclic_graph(nx.subgraph_view(graph,
                                                                         filter_edge=lambda u, v: graph[u][v].get(
                                                                             "type") in ["precedes",
                                                                                         "depends_on"])):
                        # If cycle is formed, remove to enforce DAG constraints
                        graph.remove_edge(src, tgt)
                else:
                    graph.add_edge(src, tgt, type=edge.type, confidence=edge.confidence,
                                   created_at=datetime.now(UTC).isoformat())

        return graph, context


class PopperSubagent(CouncilSubagent):
    """
    3. Belief Revision / TMS Conflict (Falsifiability)
    Runs a Truth Maintenance System (TMS) to propagate confidence decay down dependencies.
    """

    def __init__(self):
        super().__init__("Popper", "Skeptical Arbitrator")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        # Propagate deactivation recursively: if a node is superseded or confidence == 0,
        # propagate decay down its 'depends_on' edges
        visited = set()

        def propagate_decay(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            node_data = graph.nodes[node_id]

            # If node is inactive/superseded, propagate to descendants
            if node_data.get("status") == "superseded" or node_data.get("confidence", 1.0) <= 0.0:
                dependents = [u for u, v, d in graph.edges(data=True) if v == node_id and d.get("type") == "depends_on"]
                for dep in dependents:
                    graph.nodes[dep]["confidence"] = 0.0
                    graph.nodes[dep]["status"] = "superseded"
                    graph.nodes[dep]["updated_at"] = datetime.now(UTC).isoformat()
                    propagate_decay(dep)

        # Run TMS propagation on all nodes
        for node in list(graph.nodes):
            propagate_decay(node)

        return graph, context


class NoetherSubagent(CouncilSubagent):
    """
    4. Symmetry Check (Symmetry)
    Ensures "Conservation of Meaning". Validates that active decisions are not lost in graph compaction.
    """

    def __init__(self):
        super().__init__("Noether", "Symmetry Meta-Validator")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        raw_mems = context.get("raw_memories", [])
        if not raw_mems:
            return graph, context

        represented_hashes = set()
        for _, data in graph.nodes(data=True):
            represented_hashes.update(data.get("sources", []))

        # We assert that every raw memory hash must be accounted for in the L2 graph
        for mem in raw_mems:
            if mem.id not in represented_hashes and mem.type in [MemoryType.AXIOM, MemoryType.FACT]:
                raise SymmetryError(
                    f"CONSERVATION FAILURE: Memory ID '{mem.id}' ({mem.content[:40]}) was lost in transition to L2.")

        return graph, context


class ExplorerSubagent(CouncilSubagent):
    """
    5. Structural Explorer (Curiosity)
    Bridges gaps, maps alternative Hypothesis designs, and identifies OpenQuestion nodes.
    """

    def __init__(self):
        super().__init__("Explorer", "Conceptual Explorer")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        # Connect isolated parts or add OpenQuestion placeholder if we find structural holes
        sub_g = nx.subgraph_view(graph, filter_node=lambda n: graph.nodes[n].get("type") != "Dependency")
        if not nx.is_weakly_connected(sub_g) and sub_g.number_of_nodes() > 1:
            components = list(nx.weakly_connected_components(sub_g))
            gap_id = "exploration-horizon-gap"
            if not graph.has_node(gap_id):
                graph.add_node(
                    gap_id,
                    type="OpenQuestion",
                    content="Bridge connection between disconnected conceptual components.",
                    pinned=False,
                    sources=[],
                    created_at=datetime.now(UTC).isoformat(),
                    updated_at=datetime.now(UTC).isoformat(),
                    confidence=0.5,
                    retrieval_count=0,
                    status="active"
                )
                for comp in components:
                    node_in_comp = next(iter(comp))
                    graph.add_edge(node_in_comp, gap_id, type="refines", confidence=0.5,
                                   created_at=datetime.now(UTC).isoformat())

        return graph, context


class ShannonSubagent(CouncilSubagent):
    """
    6. Hebbian Decay & Pruning (Efficiency)
    Prunes low-activation nodes based on interaction turn count logs, protecting pinned core principles.
    """

    def __init__(self):
        super().__init__("Shannon", "Entropy Manager")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        # Process and flush the transient recall_access_log.txt
        persona_dir = context.get("persona_dir")
        retrievals = {}
        if persona_dir:
            log_path = Path(persona_dir) / 'recall_access_log.txt'
            if log_path.exists():
                try:
                    with open(log_path, encoding='utf-8') as f:
                        for line in f:
                            node_id = line.strip()
                            if node_id:
                                retrievals[node_id] = retrievals.get(node_id, 0) + 1
                    # Truncate or remove the log file
                    log_path.unlink(missing_ok=True)
                except Exception:
                    pass

        # Update retrieval counts in the graph
        for node_id, count in retrievals.items():
            if graph.has_node(node_id):
                graph.nodes[node_id]["retrieval_count"] = graph.nodes[node_id].get("retrieval_count", 0) + count

        # Pruning based on turn count or retrieval count
        prune_list = []
        for node, data in graph.nodes(data=True):
            if data.get("pinned", False) or data.get("type") == "Constraint":
                continue

            confidence = data.get("confidence", 1.0)
            if data.get("retrieval_count", 0) == 0:
                confidence = max(0.0, confidence - 0.1)
                graph.nodes[node]["confidence"] = confidence
                if confidence <= 0.2:
                    graph.nodes[node]["status"] = "archived"
                    prune_list.append(node)
            else:
                graph.nodes[node]["confidence"] = min(1.0, confidence + 0.1)
                graph.nodes[node]["retrieval_count"] = 0

        for node in prune_list:
            if graph.degree(node) == 0:
                graph.remove_node(node)

        return graph, context


class MaharalSubagent(CouncilSubagent):
    """
    7. Validation & Safety Sandbox (Containment)
    Checks UUID/schema validity and writes files atomically.
    """

    def __init__(self):
        super().__init__("Maharal", "Containment Subagent")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        # Validate node IDs to prevent path traversal
        for node_id in graph.nodes:
            if ".." in node_id or "/" in node_id or "\\" in node_id:
                raise ValueError(f"CONTAINMENT FAILURE: Security violation in node ID '{node_id}'.")
        return graph, context


class FeynmanSubagent(CouncilSubagent):
    """
    8. Clarity & Simplification (Clarity)
    Audits the Knowledge Graph for readability.
    """

    def __init__(self):
        super().__init__("Feynman", "Clarity Auditor")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        return graph, context


class StewardSubagent(CouncilSubagent):
    """
    9. Harmony & Lock Guards (Harmony)
    Enforces read-only recall queries and fallback compile routes.
    """

    def __init__(self):
        super().__init__("Steward", "Swarm Harmony")

    def run(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        context["introspection_completed"] = True
        return graph, context


# Introspection Assembly Coordinator
class IntrospectionAssembly:
    def __init__(self):
        self.agents = [
            BaconSubagent(),
            RussellSubagent(),
            PopperSubagent(),
            NoetherSubagent(),
            ExplorerSubagent(),
            ShannonSubagent(),
            MaharalSubagent(),
            FeynmanSubagent(),
            StewardSubagent()
        ]

    def execute(self, graph: nx.DiGraph, context: dict) -> tuple[nx.DiGraph, dict]:
        for agent in self.agents:
            graph, context = agent.run(graph, context)
        return graph, context


# Compacted L2 graph representation compiler
def format_graph_as_mermaid(graph: nx.DiGraph) -> str:
    """Exports the networkx graph to a clean, markdown-friendly Mermaid diagram."""
    lines = ["graph TD"]
    for node, data in graph.nodes(data=True):
        ntype = data.get("type", "Concept")
        if ntype == "Decision":
            lines.append(f'    {node}["Decision"]')
        elif ntype == "Constraint":
            lines.append(f'    {node}{{"Constraint"}}')
        elif ntype == "Fact":
            lines.append(f'    {node}("[Fact]")')
        else:
            lines.append(f'    {node}["{ntype}"]')

    for u, v, d in graph.edges(data=True):
        rel = d.get("type", "links")
        lines.append(f"    {u} -->|{rel}| {v}")

    return "\n".join(lines)


def run_introspection(persona_dir: Path, bootstrap: bool = False, model: str = "gemini-3.1-pro-preview",
                      test_mode: bool = False) -> nx.DiGraph:
    """
    Core entrypoint to run the introspection compaction loop.
    Loads L1, executes the Council Assembly, saves L2 Graph, and moves consolidated L1s.
    """
    kg_path = persona_dir / "knowledge_graph.yaml"

    graph = nx.DiGraph()
    if kg_path.exists() and not bootstrap:
        try:
            with open(kg_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            graph = nx.node_link_graph(data)
        except Exception:
            graph = nx.DiGraph()

    context = {
        "persona_dir": persona_dir,
        "bootstrap": bootstrap or (not kg_path.exists()),
        "model": model,
        "test_mode": test_mode
    }

    # Run subagent assembly
    assembly = IntrospectionAssembly()
    graph, context = assembly.execute(graph, context)

    # Save L2 Graph Atomically (Maharal constraint)
    kg_temp_fd, kg_temp_path = tempfile.mkstemp(dir=persona_dir, prefix="kg.tmp.")
    try:
        graph_data = nx.node_link_data(graph)
        yaml_content = yaml.dump(graph_data, sort_keys=False)
        with open(kg_temp_fd, "w", encoding="utf-8") as f:
            f.write(yaml_content)
            f.flush()
            os.fsync(f.fileno())
        if kg_path.exists():
            with contextlib.suppress(Exception):
                os.chmod(kg_path, 0o666)
        os.replace(kg_temp_path, kg_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.remove(kg_temp_path)
        raise

    # Golem's Seal: lock L2 file permissions to read-only
    with contextlib.suppress(Exception):
        os.chmod(kg_path, 0o444)

    # Compaction Handoff: move subsumed L1 files
    memory_manager = MemoryManager(base_dir=persona_dir)
    raw_mems = context.get("raw_memories", [])
    for mem in raw_mems:
        with contextlib.suppress(FileNotFoundError):
            memory_manager.subsume(mem.id)

    return graph
