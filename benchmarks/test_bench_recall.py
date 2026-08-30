"""Benchmarks for topological recall: L2 graph loading, matching and spreading activation."""

import networkx as nx
import pytest

from tur.introspection import format_graph_as_mermaid, load_l2_graph_from_okf
from tur.recall import _spread_activation, topological_recall


@pytest.mark.benchmark
def test_bench_load_l2_graph_from_okf(concepts_dir):
    """Parses 150 OKF concept files into a networkx DiGraph."""
    load_l2_graph_from_okf(concepts_dir)


@pytest.mark.benchmark
def test_bench_topological_recall(concepts_dir):
    """Full EP-0103 recall: graph load, substring match, 2-hop activation and JSON render."""
    topological_recall('topological constraints', concepts_dir)


@pytest.mark.benchmark
def test_bench_topological_recall_no_match(concepts_dir):
    """Recall on a query that matches nothing — the pure scan cost."""
    topological_recall('an utterly unrelated query string', concepts_dir)


def test_bench_spread_activation(benchmark, knowledge_graph: nx.DiGraph):
    """Two-hop spreading activation over a 500-node graph."""
    matched = [f'concept-{index:03d}' for index in range(0, 500, 25)]
    benchmark(_spread_activation, knowledge_graph, matched)


def test_bench_format_graph_as_mermaid(benchmark, knowledge_graph: nx.DiGraph):
    """Renders the cognitive map as a Mermaid diagram (injected in the prompt)."""
    benchmark(format_graph_as_mermaid, knowledge_graph)
