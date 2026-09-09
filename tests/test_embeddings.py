import json
from pathlib import Path

import networkx as nx
import pytest
import yaml

from tur.memory import (
    CognitiveGraphEngine,
    MemoryManager,
    VectorEngine,
    batch_cosine_similarity,
    load_l2_graph_from_okf,
    pure_cosine_similarity,
    save_l2_graph_to_okf,
    topological_recall,
)
from tur.memory.recall import _calculate_seed_scores, _l1_fallback_search
from tur.models import Memory, MemoryScope, MemoryType


def test_pure_cosine_similarity_edge_cases():
    # Identical vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), abs=1e-5) == 1.0

    # Orthogonal vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 0.0], [0.0, 1.0]), abs=1e-5) == 0.0

    # Opposite vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 0.0], [-1.0, 0.0]), abs=1e-5) == -1.0

    # Zero norm vectors
    assert pure_cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    assert pure_cosine_similarity([1.0, 1.0], [0.0, 0.0]) == 0.0

    # Empty or mismatched vectors
    assert pure_cosine_similarity([], [1.0, 2.0]) == 0.0
    assert pure_cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_batch_cosine_similarity():
    q = [1.0, 0.0]
    candidates = [
        [1.0, 0.0],  # identical -> 1.0
        [0.0, 1.0],  # orthogonal -> 0.0
        [-1.0, 0.0],  # opposite -> -1.0
        [0.7071, 0.7071],  # 45 deg -> ~0.7071
    ]
    sims = batch_cosine_similarity(q, candidates)
    assert len(sims) == 4
    assert pytest.approx(sims[0], abs=1e-4) == 1.0
    assert pytest.approx(sims[1], abs=1e-4) == 0.0
    assert pytest.approx(sims[2], abs=1e-4) == -1.0
    assert pytest.approx(sims[3], abs=1e-3) == 0.7071

    # Empty inputs
    assert batch_cosine_similarity([], candidates) == [0.0, 0.0, 0.0, 0.0]
    assert batch_cosine_similarity(q, []) == []


def test_vector_engine_basic_and_drift():
    engine = VectorEngine(model_name='all-MiniLM-L6-v2_onnx_int8')
    assert engine.model_name == 'all-MiniLM-L6-v2_onnx_int8'

    # Graceful fallback when onnxruntime is absent or model path is missing
    assert engine.embed_text('') == []
    assert engine.embed_text('   ') == []
    assert engine.embed_text('Hello world') == []

    # Semantic drift detection
    assert engine.detect_semantic_drift(None) is False
    assert engine.detect_semantic_drift('all-MiniLM-L6-v2_onnx_int8') is False
    assert engine.detect_semantic_drift('all-MiniLM-L6-v1_legacy') is True


def test_okf_l1_frontmatter_embeddings(tmp_path: Path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Dense semantic vector retrieval uses cosine similarity',
        embedding_model='all-MiniLM-L6-v2_onnx_int8',
        embedding_vector=[0.12, -0.34, 0.56],
    )
    saved_path = mgr.save(mem)
    assert saved_path.exists()

    # Verify reload from OKF disk file
    loaded = mgr.load_all(include_archived=False)
    assert len(loaded) == 1
    assert loaded[0].embedding_model == 'all-MiniLM-L6-v2_onnx_int8'
    assert loaded[0].embedding_vector == [0.12, -0.34, 0.56]


def test_okf_l2_concept_embeddings(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-l2'
    persona_dir.mkdir(parents=True)

    g = nx.DiGraph()
    g.add_node(
        'semantic-search',
        type='Concept',
        content='Semantic search using embeddings',
        confidence=1.0,
        status='active',
        embedding_model='all-MiniLM-L6-v2_onnx_int8',
        embedding_vector=[0.5, 0.5, 0.0],
    )
    save_l2_graph_to_okf(g, persona_dir)

    loaded_g = load_l2_graph_from_okf(persona_dir)
    assert loaded_g is not None
    assert 'semantic-search' in loaded_g
    ndata = loaded_g.nodes['semantic-search']
    assert ndata.get('embedding_model') == 'all-MiniLM-L6-v2_onnx_int8'
    assert ndata.get('embedding_vector') == [0.5, 0.5, 0.0]


def test_hipporag_ppr_vector_personalization_seed():
    """Verify that vector similarity acts as HippoRAG PPR personalization seed even with vocabulary mismatch."""
    g = nx.DiGraph()
    # Node A: storage concept (no keyword match with query 'performant speed')
    g.add_node(
        'fast-cache',
        type='Concept',
        content='AST caching mechanism for compiler',
        confidence=1.0,
        status='active',
        embedding_vector=[1.0, 0.0, 0.0],
    )
    # Node B: network routing concept
    g.add_node(
        'mesh-routing',
        type='Concept',
        content='Mesh topology packet forwarding',
        confidence=1.0,
        status='active',
        embedding_vector=[0.0, 1.0, 0.0],
    )
    g.add_edge('fast-cache', 'mesh-routing', weight=1.0)

    # Query 'throughput optimization' has 0 lexical overlap with 'AST caching mechanism for compiler'
    # but query_vector is aligned with fast-cache
    query = 'throughput optimization'
    query_vec = [0.95, 0.05, 0.0]

    engine = CognitiveGraphEngine(g)
    seed_scores = engine.calculate_seed_scores(query, query_vector=query_vec)

    assert 'fast-cache' in seed_scores
    assert seed_scores['fast-cache'] > seed_scores.get('mesh-routing', 0.0)

    # Run HippoRAG associative PPR
    ranked = engine.associative_ppr_recall(seed_scores=seed_scores, alpha=0.15, top_k=2)
    assert len(ranked) >= 1
    assert ranked[0][0] == 'fast-cache'


def test_topological_recall_with_vector_seeding(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-vector-recall'
    persona_dir.mkdir(parents=True)

    g = nx.DiGraph()
    g.add_node(
        'vector-store',
        type='Concept',
        content='In-memory vector store for fast neighbor lookup',
        confidence=1.0,
        status='active',
        embedding_vector=[1.0, 0.0],
    )
    g.add_node(
        'sql-database',
        type='Concept',
        content='Relational SQLite tables',
        confidence=1.0,
        status='active',
        embedding_vector=[0.0, 1.0],
    )
    g.add_edge('vector-store', 'sql-database', type='depends_on')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    # Query with zero lexical match, but query_vector aligned with vector-store
    res = topological_recall(
        query='unmatched_lexical_token',
        persona_dir=persona_dir,
        effort=5,
        query_vector=[0.9, 0.1],
    )
    parsed = json.loads(res)
    assert len(parsed) > 0
    assert parsed[0]['id'] == 'vector-store'


def test_l1_fallback_search_with_vector(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-l1-fallback'
    persona_dir.mkdir(parents=True)

    mgr = MemoryManager(base_dir=persona_dir)
    mgr.save(
        Memory(
            type=MemoryType.FACT,
            scope=MemoryScope.INCARNATION,
            content='Persistent disk indexing with zero runtime dependencies',
            embedding_vector=[0.8, 0.2],
        )
    )

    # Query with zero lexical match but matching query_vector
    res = _l1_fallback_search('completely_foreign_token', persona_dir, query_vector=[0.8, 0.2])
    assert 'No memories found' not in res
    parsed = json.loads(res)
    assert len(parsed) == 1
    assert 'Persistent disk indexing' in parsed[0]['content']
