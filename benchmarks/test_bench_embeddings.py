"""Benchmarks for EP-0144: Dense semantic vector embeddings and cosine similarity retrieval."""

import math

import networkx as nx
import pytest

from tur.memory.embeddings import (
    VectorEngine,
    batch_cosine_similarity,
    is_model_compatible,
    pure_cosine_similarity,
)
from tur.memory.recall import _augment_scores_with_vector_similarity


def _generate_synthetic_vector(dim: int = 384, seed: int = 42) -> list[float]:
    """Generates a deterministic L2-normalized synthetic vector of dimension `dim`."""
    raw = [math.sin(seed + i * 0.1) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


@pytest.fixture
def query_vector_384() -> list[float]:
    return _generate_synthetic_vector(dim=384, seed=1)


@pytest.fixture
def candidate_matrix_100() -> list[list[float]]:
    return [_generate_synthetic_vector(dim=384, seed=100 + i) for i in range(100)]


@pytest.fixture
def candidate_matrix_1000() -> list[list[float]]:
    return [_generate_synthetic_vector(dim=384, seed=1000 + i) for i in range(1000)]


@pytest.fixture
def graph_with_embeddings(knowledge_graph: nx.DiGraph) -> nx.DiGraph:
    """Populates the 500-node synthetic knowledge graph with 384-dim embeddings."""
    g = knowledge_graph.copy()
    for index, (_node, data) in enumerate(g.nodes(data=True)):
        if data.get('status') == 'active':
            data['embedding_model'] = 'all-MiniLM-L6-v2'
            data['embedding_vector'] = _generate_synthetic_vector(dim=384, seed=index)
    return g


# -----------------------------------------------------------------------------
# PURE COSINE SIMILARITY (Pure Python O(D) baseline)
# -----------------------------------------------------------------------------


def test_bench_pure_cosine_similarity(benchmark, query_vector_384):
    """EP-0144: Pure Python single vector cosine similarity (384 dimensions)."""
    cand = _generate_synthetic_vector(dim=384, seed=2)
    benchmark(pure_cosine_similarity, query_vector_384, cand)


# -----------------------------------------------------------------------------
# BATCH COSINE SIMILARITY (NumPy vectorized matrix vs. Pure Python fallback)
# -----------------------------------------------------------------------------


def test_bench_batch_cosine_similarity_100(benchmark, query_vector_384, candidate_matrix_100):
    """EP-0144: Batch matrix cosine similarity across 100 candidate vectors (384-dim)."""
    benchmark(batch_cosine_similarity, query_vector_384, candidate_matrix_100)


def test_bench_batch_cosine_similarity_1000(benchmark, query_vector_384, candidate_matrix_1000):
    """EP-0144: Batch matrix cosine similarity across 1,000 candidate vectors (384-dim)."""
    benchmark(batch_cosine_similarity, query_vector_384, candidate_matrix_1000)


# -----------------------------------------------------------------------------
# MODEL COMPATIBILITY (Zero-Poisoning Query Isolation Check)
# -----------------------------------------------------------------------------


def test_bench_is_model_compatible(benchmark):
    """EP-0144: Fast-path model compatibility & alias resolution."""
    benchmark(is_model_compatible, 'minilm', 'all-MiniLM-L6-v2')


# -----------------------------------------------------------------------------
# GRAPH VECTOR AUGMENTATION (HippoRAG Personalization Seeding)
# -----------------------------------------------------------------------------


def test_bench_augment_scores_with_vector_similarity(benchmark, graph_with_embeddings: nx.DiGraph, query_vector_384):
    """EP-0144: Augment seed scores with dense vector similarities over 500-node graph."""
    engine = VectorEngine(model_name='all-MiniLM-L6-v2')

    def run_augment():
        scores: dict[str, float] = {}
        _augment_scores_with_vector_similarity(
            graph=graph_with_embeddings,
            query='test query',
            scores=scores,
            query_vector=query_vector_384,
            vector_engine=engine,
        )
        return scores

    benchmark(run_augment)
