"""Benchmarks for topological recall: L2 graph loading, matching and spreading activation."""

import networkx as nx
import pytest

from tur.memory import (
    CognitiveGraphEngine,
    format_graph_as_mermaid,
    load_l2_graph_from_okf,
    pure_pagerank,
    topological_recall,
)


@pytest.mark.benchmark
def test_bench_load_l2_graph_from_okf(concepts_dir):
    """Parses 150 OKF concept files into a networkx DiGraph."""
    load_l2_graph_from_okf(concepts_dir)


@pytest.mark.benchmark
def test_bench_topological_recall(concepts_dir):
    """EP-0136 discrete topological recall: graph load, seed match and discrete retrieval."""
    topological_recall('topological constraints', concepts_dir)


@pytest.mark.benchmark
def test_bench_topological_recall_deep(concepts_dir):
    """EP-0136 deep associative recall: graph load, HippoRAG PPR and Louvain community subgraph."""
    topological_recall('topological constraints', concepts_dir, deep=True)


@pytest.mark.benchmark
def test_bench_topological_recall_no_match(concepts_dir):
    """Recall on a query that matches nothing — the pure scan cost."""
    topological_recall('an utterly unrelated query string', concepts_dir)


def test_bench_associative_ppr_recall(benchmark, knowledge_graph: nx.DiGraph):
    """EP-0136 HippoRAG Personalized PageRank spreading activation over 500-node graph."""
    engine = CognitiveGraphEngine(knowledge_graph)
    seed_scores = {f'concept-{index:03d}': 1.0 for index in range(0, 500, 25)}
    benchmark(engine.associative_ppr_recall, seed_scores)


def test_bench_pure_pagerank(benchmark, knowledge_graph: nx.DiGraph):
    """EP-0136 pure Python zero-dependency PageRank computation."""
    benchmark(pure_pagerank, knowledge_graph, alpha=0.85)


def test_bench_louvain_communities(benchmark, knowledge_graph: nx.DiGraph):
    """EP-0136 Louvain community detection over 500-node graph."""
    engine = CognitiveGraphEngine(knowledge_graph)
    benchmark(engine.detect_louvain_communities)


def test_bench_extract_bounded_ego_subgraph(benchmark, knowledge_graph: nx.DiGraph):
    """EP-0136 bounded k-hop ego subgraph extraction."""
    engine = CognitiveGraphEngine(knowledge_graph)
    focal_nodes = [f'concept-{index:03d}' for index in range(0, 50, 10)]
    benchmark(engine.extract_bounded_ego_subgraph, focal_nodes, radius=1, max_nodes=8)


def test_bench_format_graph_as_mermaid(benchmark, knowledge_graph: nx.DiGraph):
    """Renders the cognitive map as a Mermaid diagram (injected in the prompt)."""
    benchmark(format_graph_as_mermaid, knowledge_graph)
