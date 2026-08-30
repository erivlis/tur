# Audit Report 4: Refactoring Blueprints & Concrete Python Implementations

**Document Reference:** `references/explorations/EXP-0005-mathematical-and-graph-theoretic-code-audit/04_refactoring_blueprints_and_code_diffs.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Ready-to-integrate Python implementations for Quick Wins and Medium-Term Refactors.  

---

## 1. Upgraded `src/tur/recall.py` (Full Blueprint)

```python
"""
Graph-enhanced semantic recall module for Tur.
Implements HippoRAG Personalized PageRank (PPR), cognitive effort modulation (--effort 0..10),
and conditional Mermaid visualization (--mermaid).
"""

import json
from pathlib import Path
from typing import Any

import networkx as nx

from tur._helpers import yaml_safe_load
from tur.locking import state_lock


def _l1_fallback_search(query: str, persona_dir: Path, limit: int = 5) -> str:
    """Fallback search over raw L1 memories."""
    from tur.memory import MemoryManager

    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all(include_archived=False)
    query_lower = query.lower()
    results = [
        m for m in mems 
        if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)
    ]
    if not results:
        return f"No memories found matching query: '{query}'"
    mem_list = [{'id': str(m.id), 'type': m.type.value, 'content': m.content} for m in results[:limit]]
    return json.dumps(mem_list, indent=2)


def _compute_ppr_activation(
    graph: nx.DiGraph,
    seed_scores: dict[str, float],
    top_k: int = 6,
    alpha: float = 0.15,
) -> list[str]:
    """
    Executes HippoRAG Personalized PageRank over the directed L2 Cognitive Map.
    """
    if not graph.nodes or not seed_scores:
        return []

    total_seed = sum(seed_scores.values())
    if total_seed == 0:
        return list(seed_scores.keys())[:top_k]

    personalization = {n: seed_scores.get(n, 0.0) / total_seed for n in graph.nodes}

    # Semantic edge weight matrix
    weight_map = {
        'supported_by': 1.5,
        'refines': 1.3,
        'metaphor_for': 1.2,
        'depends_on': 1.1,
        'precedes': 1.0,
        'analogy_of': 1.0,
        'related_to': 0.8,
        'contradicts': 0.01,  # Down-weight contradictions in positive spreading activation
    }

    weighted_graph = graph.copy()
    for u, v, d in weighted_graph.edges(data=True):
        rel = d.get('type', 'related_to')
        d['weight'] = weight_map.get(rel, 1.0) * float(d.get('confidence', 1.0))

    ppr_scores = nx.pagerank(
        weighted_graph, 
        alpha=1.0 - alpha, 
        personalization=personalization, 
        weight='weight'
    )

    ranked = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)
    return [node for node, score in ranked[:top_k]]


def topological_recall(
    query: str,
    persona_dir: Path,
    effort: int = 0,
    mermaid: bool = False,
    limit: int = 5,
) -> str:
    """
    Graph-enhanced semantic recall logic.
    Supports adjustable cognitive effort (0=fast keyword, 5=deep associative PPR, 10=exhaustive TMS).
    """
    from tur.introspection import load_l2_graph_from_okf

    graph = load_l2_graph_from_okf(persona_dir)

    if graph is None:
        kg_path = persona_dir / 'knowledge_graph.yaml'
        if not kg_path.exists():
            return _l1_fallback_search(query, persona_dir, limit=limit)
        try:
            with open(kg_path, encoding='utf-8') as f:
                data = yaml_safe_load(f)
            graph = nx.node_link_graph(data)
        except Exception:
            return _l1_fallback_search(query, persona_dir, limit=limit)

    query_tokens = set(query.lower().split())
    seed_scores: dict[str, float] = {}

    # 1. Candidate Seeding (Token Set Jaccard & Substring Match)
    for node, ndata in graph.nodes(data=True):
        if ndata.get('status') in ['archived', 'superseded']:
            continue
        content = ndata.get('content', '').lower()
        node_lower = node.lower()

        # Score computation
        score = 0.0
        if query.lower() in node_lower or query.lower() in content:
            score += 2.0
        
        content_tokens = set(content.split())
        matched_tokens = query_tokens.intersection(content_tokens)
        if matched_tokens:
            score += len(matched_tokens) / len(query_tokens)

        if score > 0.0:
            seed_scores[node] = score

    if not seed_scores:
        return f"No memories found matching query: '{query}'"

    # 2. Effort-Based Retrieval Modulation
    if effort == 0:
        # Fast Tier: Return top-K seeded candidates
        sorted_seeds = sorted(seed_scores.items(), key=lambda x: x[1], reverse=True)
        activated_nodes = [n for n, s in sorted_seeds[:limit]]
    elif effort < 5:
        # Light Tier: 1-hop ego expansion
        activated_set = set(seed_scores.keys())
        for n in list(seed_scores.keys()):
            activated_set.update(graph.successors(n))
            activated_set.update(graph.predecessors(n))
        activated_nodes = list(activated_set)[:limit]
    else:
        # Deep Tier (Effort >= 5): HippoRAG Personalized PageRank
        activated_nodes = _compute_ppr_activation(graph, seed_scores, top_k=limit)

    # 3. Stage access metrics safely under file lock
    log_path = persona_dir / 'recall_access_log.txt'
    try:
        with state_lock(persona_dir, timeout_seconds=2.0):
            with open(log_path, 'a', encoding='utf-8') as f:
                for node in activated_nodes:
                    f.write(f'{node}\n')
    except Exception:
        pass

    # 4. Build Structured Payload
    results: list[dict[str, Any]] = []
    for node in activated_nodes:
        ndata = graph.nodes[node]
        results.append({
            'id': node,
            'type': ndata.get('type', 'Concept'),
            'content': ndata.get('content', ''),
            'confidence': ndata.get('confidence', 1.0),
        })

    output_str = json.dumps(results, indent=2)

    # 5. Conditional Mermaid Diagram Injection
    if mermaid and activated_nodes:
        subgraph = graph.subgraph(activated_nodes)
        try:
            import networkx_mermaid as nxm
            builder = nxm.builders.DiagramBuilder(
                orientation=nxm.DiagramOrientation.TOP_BOTTOM,
                node_shape=nxm.DiagramNodeShape.ROUND_RECTANGLE,
            )
            diagram_str = str(builder.build(subgraph))
            output_str += f"\n\n```mermaid\n{diagram_str}\n```"
        except ImportError:
            pass

    return output_str
```

---

## 2. Upgraded `src/tur/metrics.py` (Full Blueprint)

```python
"""
Cognitive metrics and topological diagnostics for Tur personas.
Computes token load, Shannon entropy, Constraint Dimensionality (Cp),
graph density, algebraic connectivity (lambda_2), and Louvain modularity.
"""

import math
from collections import Counter
from typing import Any

import networkx as nx
from pydantic import BaseModel

from tur import persona, user
from tur._helpers import yaml_safe_load
from tur.compiler import compile_persona
from tur.models import Persona, SessionState


class CognitiveMetrics:
    """Measures cognitive load, Shannon information entropy, and topological health."""

    def measure_static_load(self, system_prompt: str) -> dict[str, Any]:
        char_count = len(system_prompt)
        est_tokens = int(char_count / 4)

        return {
            'char_count': char_count,
            'est_tokens': est_tokens,
            'density': self._calculate_density(system_prompt),
            'shannon_entropy': self.calculate_shannon_entropy(system_prompt),
        }

    @staticmethod
    def calculate_constraint_dimensionality(persona_obj: Persona) -> float:
        """Calculates Cp = Sum(W_c) + 0.05 * N * (N - 1)."""
        base_load = sum(p.weight for p in persona_obj.principles)
        n = len(persona_obj.principles)
        interaction_penalty = (n * (n - 1)) * 0.05
        return round(base_load + interaction_penalty, 2)

    @staticmethod
    def calculate_shannon_entropy(text: str) -> float:
        """Calculates Shannon Entropy H(X) in bits per word."""
        words = text.lower().split()
        if not words:
            return 0.0
        total = len(words)
        counts = Counter(words)
        return round(-sum((c / total) * math.log2(c / total) for c in counts.values()), 3)

    @staticmethod
    def _calculate_density(text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        return round(len(set(words)) / len(words), 3)

    @staticmethod
    def compute_graph_topology(graph: nx.DiGraph | None) -> dict[str, Any]:
        """Calculates density, modularity, and algebraic connectivity."""
        if graph is None or graph.number_of_nodes() < 2:
            return {
                'num_nodes': 0 if graph is None else graph.number_of_nodes(),
                'num_edges': 0 if graph is None else graph.number_of_edges(),
                'density': 0.0,
                'algebraic_connectivity': 0.0,
                'modularity': 0.0,
                'num_communities': 1,
            }

        undirected = graph.to_undirected()
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        density = round(nx.density(graph), 3)

        try:
            lambda_2 = round(float(nx.algebraic_connectivity(undirected)), 4)
        except Exception:
            lambda_2 = 0.0

        try:
            communities = list(nx.community.louvain_communities(undirected))
            modularity = round(float(nx.community.modularity(undirected, communities)), 4)
        except Exception:
            communities = [set(graph.nodes)]
            modularity = 0.0

        return {
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'density': density,
            'algebraic_connectivity': lambda_2,
            'modularity': modularity,
            'num_communities': len(communities),
        }


class MetricsReport(BaseModel):
    persona_id: str
    persona_name: str
    num_principles: int
    constraint_dimensionality: float
    rating_class: str
    static_token_cost: int
    char_count: int
    information_density: float
    shannon_entropy: float = 0.0
    graph_nodes: int = 0
    graph_edges: int = 0
    algebraic_connectivity: float = 0.0
    modularity: float = 0.0
    num_communities: int = 1


def compute_persona_metrics(identifier: str | None = None) -> MetricsReport:
    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    file_path = persona_dir / 'persona.yaml'

    if not file_path.exists():
        raise FileNotFoundError(f"persona.yaml not found for persona '{active_id}' at {file_path}")

    with open(file_path, encoding='utf-8') as f:
        data = yaml_safe_load(f)

    persona_obj = Persona(**data)
    user_profile = user.get_user_profile()
    state = SessionState(persona=persona_obj, user=user_profile, memories=[], epilogue=None, knowledge_graph=None)
    system_prompt = compile_persona(state)

    metrics_engine = CognitiveMetrics()
    static_metrics = metrics_engine.measure_static_load(system_prompt)
    cp = float(metrics_engine.calculate_constraint_dimensionality(persona_obj))

    from tur.introspection import load_l2_graph_from_okf
    graph = load_l2_graph_from_okf(persona_dir)
    graph_metrics = metrics_engine.compute_graph_topology(graph)

    if cp < 5:
        rating = 'Human (Manageable)'
    elif cp < 10:
        rating = 'Giant (Heavy Load)'
    else:
        rating = 'Titan (Inference Warning)'

    return MetricsReport(
        persona_id=active_id,
        persona_name=persona_obj.name,
        num_principles=len(persona_obj.principles),
        constraint_dimensionality=cp,
        rating_class=rating,
        static_token_cost=static_metrics['est_tokens'],
        char_count=static_metrics['char_count'],
        information_density=static_metrics['density'],
        shannon_entropy=static_metrics['shannon_entropy'],
        graph_nodes=graph_metrics['num_nodes'],
        graph_edges=graph_metrics['num_edges'],
        algebraic_connectivity=graph_metrics['algebraic_connectivity'],
        modularity=graph_metrics['modularity'],
        num_communities=graph_metrics['num_communities'],
    )
```

---

## 3. Summary of Verification

These prototypes were verified against our existing test suites and require zero breaking API changes. They can be merged into Tur's master branch incrementally under EP-0136.
