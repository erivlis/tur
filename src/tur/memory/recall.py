import contextlib
import json
import math
import re
from pathlib import Path
from typing import Any

import networkx as nx

from tur.models import EdgeType, NodeType

SEMANTIC_EDGE_WEIGHTS: dict[str, float] = {
    'supported_by': 1.5,
    'depends_on': 1.4,
    'refines': 1.3,
    'metaphor_for': 1.2,
    'analogy_of': 1.1,
    'precedes': 1.0,
    'links': 1.0,
    'related_to': 0.8,
    'competes_with': 0.5,
    'contradicts': 0.01,
    'refutes': 0.01,
    'refuted_by': 0.01,
    'superseded_by': 0.01,
}


def pure_pagerank(
    graph: nx.DiGraph,
    alpha: float = 0.85,
    personalization: dict[str, float] | None = None,
    max_iter: int = 100,
    tol: float = 1e-6,
    weight_key: str = 'weight',
) -> dict[str, float]:
    """
    Pure Python implementation of Personalized PageRank (random walk with restart).
    Guarantees zero external binary dependencies.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    if n == 0:
        return {}

    if personalization is None or not personalization:
        p0 = dict.fromkeys(nodes, 1.0 / n)
    else:
        tot = sum(personalization.get(node, 0.0) for node in nodes)
        if tot <= 0:
            p0 = dict.fromkeys(nodes, 1.0 / n)
        else:
            p0 = {node: personalization.get(node, 0.0) / tot for node in nodes}

    p = dict.fromkeys(nodes, 1.0 / n)

    out_weights: dict[str, float] = {}
    for node in nodes:
        out_w = sum(float(graph[node][nbr].get(weight_key, 1.0)) for nbr in graph[node])
        out_weights[node] = out_w

    for _ in range(max_iter):
        p_next = dict.fromkeys(nodes, 0.0)
        dangling_sum = sum(p[node] for node in nodes if out_weights[node] == 0)

        for node in nodes:
            if out_weights[node] > 0:
                p_out = p[node] / out_weights[node]
                for nbr in graph[node]:
                    w = float(graph[node][nbr].get(weight_key, 1.0))
                    p_next[nbr] += alpha * p_out * w

        for node in nodes:
            p_next[node] += (1.0 - alpha) * p0[node] + alpha * dangling_sum * p0[node]

        err = sum(abs(p_next[node] - p[node]) for node in nodes)
        p = p_next
        if err < tol:
            break

    return p


def pure_algebraic_connectivity(graph: nx.Graph | nx.DiGraph, max_iter: int = 200, tol: float = 1e-7) -> float:
    """
    Calculates the Fiedler eigenvalue (algebraic connectivity lambda_2) of the graph Laplacian L = D - A.
    Pure Python power iteration on the shifted Laplacian matrix.
    """
    undirected = graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph
    n = undirected.number_of_nodes()
    if n <= 1:
        return 0.0
    if not nx.is_connected(undirected):
        return 0.0
    if n == 2:
        return 2.0 if undirected.number_of_edges() >= 1 else 0.0

    nodes = list(undirected.nodes())
    degrees = dict(undirected.degree())
    max_d = max(degrees.values())
    mu = 2.0 * max_d + 1.0

    v = [i - (n - 1) / 2.0 for i in range(n)]
    norm_v = math.sqrt(sum(x * x for x in v))
    if norm_v == 0:
        v = [1.0 if i % 2 == 0 else -1.0 for i in range(n)]
        mean_v = sum(v) / n
        v = [x - mean_v for x in v]
        norm_v = math.sqrt(sum(x * x for x in v))
    v = [x / norm_v for x in v]

    node_to_idx = {node: i for i, node in enumerate(nodes)}
    prev_rayleigh = 0.0

    for _ in range(max_iter):
        mv = [0.0] * n
        for i, u in enumerate(nodes):
            deg = degrees[u]
            adj_sum = sum(v[node_to_idx[nbr]] for nbr in undirected[u])
            mv[i] = (mu - deg) * v[i] + adj_sum

        mean = sum(mv) / n
        v_next = [x - mean for x in mv]

        norm = math.sqrt(sum(x * x for x in v_next))
        if norm < 1e-12:
            return 0.0
        v = [x / norm for x in v_next]

        l_rayleigh = sum((v[node_to_idx[u]] - v[node_to_idx[w]]) ** 2 for u, w in undirected.edges())
        if abs(l_rayleigh - prev_rayleigh) < tol:
            break
        prev_rayleigh = l_rayleigh

    return l_rayleigh


class CognitiveGraphEngine:
    """
    Graph-Theoretic Memory Engine built natively on NetworkX (EP-0136).
    Incorporates HippoRAG Personalized PageRank associative activation,
    Louvain community clustering, and spectral graph metrics.
    """

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph.copy()
        for _, _, data in self.graph.edges(data=True):
            if 'weight' not in data:
                edge_type = str(data.get('type', 'links')).lower()
                data['weight'] = SEMANTIC_EDGE_WEIGHTS.get(edge_type, 1.0)

    def compute_spectral_health(self) -> dict[str, Any]:
        """Calculates Fiedler eigenvalue lambda_2, Louvain modularity Q, and community statistics."""
        undirected = self.graph.to_undirected()
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        if node_count == 0:
            return {
                'node_count': 0,
                'edge_count': 0,
                'is_connected': True,
                'algebraic_connectivity': 0.0,
                'connectivity_status': 'No Graph',
                'community_count': 0,
                'modularity_score': 0.0,
            }

        is_connected = nx.is_connected(undirected)
        fiedler_val = pure_algebraic_connectivity(undirected) if node_count > 1 and is_connected else 0.0

        if node_count > 1:
            try:
                communities = list(nx.community.louvain_communities(undirected))
                modularity = nx.community.modularity(undirected, communities)
            except Exception:
                communities = [set(undirected.nodes())]
                modularity = 0.0
        else:
            communities = [set(undirected.nodes())] if node_count == 1 else []
            modularity = 0.0

        fiedler_rounded = round(float(fiedler_val), 4)
        modularity_rounded = round(float(modularity), 4)

        if not is_connected and node_count > 1:
            status = 'Knowledge Silos Detected'
        elif fiedler_rounded < 0.2:
            status = 'Fragmented'
        elif fiedler_rounded < 0.5:
            status = 'Well-Integrated'
        else:
            status = 'Highly Cohesive'

        return {
            'node_count': node_count,
            'edge_count': edge_count,
            'is_connected': is_connected,
            'algebraic_connectivity': fiedler_rounded,
            'connectivity_status': status,
            'community_count': len(communities),
            'modularity_score': modularity_rounded,
        }

    def detect_louvain_communities(self) -> list[set[str]]:
        """Partitions the graph into modular Louvain communities."""
        undirected = self.graph.to_undirected()
        if len(undirected) <= 1:
            return [set(undirected.nodes())] if len(undirected) == 1 else []
        try:
            return list(nx.community.louvain_communities(undirected))
        except Exception:
            return [set(undirected.nodes())]

    def associative_ppr_recall(
        self,
        seed_scores: dict[str, float],
        alpha: float = 0.15,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Executes HippoRAG Personalized PageRank (random walk with restart)
        across the directed L2 Cognitive Map.
        alpha: restart probability (0.15 -> damping factor 0.85).
        """
        if not self.graph.nodes:
            return []

        valid_seeds = {n: s for n, s in seed_scores.items() if n in self.graph}
        if not valid_seeds:
            return []

        total = sum(valid_seeds.values())
        personalization = {n: s / total for n, s in valid_seeds.items()}

        damping = 1.0 - alpha
        ppr_scores = pure_pagerank(
            self.graph,
            alpha=damping,
            personalization=personalization,
            weight_key='weight',
        )

        ranked = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def extract_bounded_ego_subgraph(
        self,
        center_nodes: list[str] | str,
        radius: int = 1,
        max_nodes: int = 8,
    ) -> nx.DiGraph:
        """Extracts a bounded k-hop neighborhood for structured context retrieval."""
        if isinstance(center_nodes, str):
            center_nodes = [center_nodes]

        nodes_to_include: set[str] = set()
        for c in center_nodes:
            if c in self.graph:
                ego = nx.ego_graph(self.graph, c, radius=radius, undirected=True)
                nodes_to_include.update(ego.nodes())

        if not nodes_to_include:
            return nx.DiGraph()

        sub = self.graph.subgraph(nodes_to_include).copy()
        if len(sub) > max_nodes:
            degrees = dict(sub.degree())
            sorted_nodes = sorted(
                degrees.keys(),
                key=lambda n: (1 if n in center_nodes else 0, degrees[n]),
                reverse=True,
            )
            sub = sub.subgraph(sorted_nodes[:max_nodes]).copy()

        return sub

    def format_subgraph_as_mermaid(self, subgraph: nx.DiGraph | None = None) -> str:
        """Formats the subgraph (or self.graph) as a clean Mermaid diagram."""
        target_graph = subgraph if subgraph is not None else self.graph
        if target_graph.number_of_nodes() == 0:
            return 'graph TD\n    empty["No nodes in retrieved subgraph"]'

        lines = ['graph TD']
        for node, data in target_graph.nodes(data=True):
            ntype = data.get('type', NodeType.CONCEPT.value)
            label_text = f'{node} [{ntype}]'
            if ntype == NodeType.DECISION.value:
                lines.append(f'    {node}["{label_text}"]')
            elif ntype == NodeType.CONSTRAINT.value:
                lines.append(f'    {node}{{"{label_text}"}}')
            elif ntype == NodeType.FACT.value:
                lines.append(f'    {node}("({label_text})")')
            elif ntype == NodeType.BOUNDARY_NODE.value:
                lines.append(f'    {node}[["{label_text}"]]')
            elif ntype == NodeType.OPEN_QUESTION.value:
                lines.append(f'    {node}{{{{"{label_text}"}}}}')
            else:
                lines.append(f'    {node}["{label_text}"]')

        for u, v in target_graph.edges:
            d = target_graph.edges[u, v]
            rel = d.get('type', 'links')
            if rel == EdgeType.METAPHOR_FOR.value:
                lines.append(f'    {u} -.->|{rel}| {v}')
            else:
                lines.append(f'    {u} -->|{rel}| {v}')

        return '\n'.join(lines)

    def check_tms_contradictions(self, nodes: list[str]) -> list[dict[str, Any]]:
        """Checks for active TMS contradiction and refutation relations among retrieved nodes."""
        conflicts = []
        node_set = set(nodes)
        for u in node_set:
            if u not in self.graph:
                continue
            for v in self.graph.successors(u):
                if v in node_set:
                    edge_type = str(self.graph.edges[u, v].get('type', '')).lower()
                    if edge_type in ['contradicts', 'refutes', 'refuted_by', 'superseded_by', 'competes_with']:
                        conflicts.append(
                            {
                                'source': u,
                                'target': v,
                                'relation': edge_type,
                                'status': 'conflict_detected',
                            }
                        )
        return conflicts

    def validate_git_anchors(self, nodes: list[str], repo_dir: Path | None = None) -> dict[str, Any]:
        """Validates Git commit anchors and source provenance for retrieved nodes (EP-0131)."""
        from tur.memory.provenance import get_git_commit_distance

        validations: dict[str, Any] = {}
        for node in nodes:
            if node not in self.graph:
                continue
            ndata = self.graph.nodes[node]
            sources = ndata.get('sources', [])
            status = 'unanchored'
            reason = None
            if sources:
                verified_count = 0
                for s in sources:
                    clean_s = str(s).strip()
                    if len(clean_s) >= 7 and all(c in '0123456789abcdefABCDEF' for c in clean_s[:7]):
                        dist = get_git_commit_distance(clean_s, repo_dir=repo_dir)
                        if dist < 999999:
                            verified_count += 1
                if verified_count > 0:
                    status = 'verified'
                else:
                    status = 'stale'
                    reason = 'Source commit hash not found in repository history'
            validations[node] = {'status': status, 'sources': sources, 'reason': reason}
        return validations


def _l1_fallback_search(query: str, persona_dir: Path) -> str:
    """Fallback search over raw L1 memories."""
    from tur.memory.storage import MemoryManager

    manager = MemoryManager(base_dir=persona_dir)
    mems = manager.load_all(include_archived=False)
    query_lower = query.lower()
    results = [m for m in mems if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)]
    if not results:
        return f"No memories found matching query: '{query}'"
    mem_list = [{'id': str(m.id), 'type': m.type.value, 'content': m.content} for m in results]
    return json.dumps(mem_list, indent=2)


def _calculate_seed_scores(graph: nx.DiGraph, query: str) -> dict[str, float]:
    """Computes lexical seed relevance scores across active L2 graph nodes."""
    query_lower = query.lower().strip()
    query_tokens = [t for t in re.split(r'[^a-zA-Z0-9_\-]+', query_lower) if len(t) > 1]
    scores: dict[str, float] = {}

    for node, ndata in graph.nodes(data=True):
        if ndata.get('status') in ['archived', 'superseded']:
            continue
        confidence = float(ndata.get('confidence', 1.0))
        if confidence <= 0.0:
            continue

        node_lower = str(node).lower()
        content_lower = str(ndata.get('content', '')).lower()
        title_lower = str(ndata.get('title', '')).lower()
        tags = [str(t).lower() for t in ndata.get('tags', [])]

        score = 0.0

        if query_lower and query_lower in node_lower:
            score += 10.0
        if query_lower and query_lower in content_lower:
            score += 6.0
        if query_lower and query_lower in title_lower:
            score += 8.0
        if any(query_lower in t for t in tags):
            score += 5.0

        for tok in query_tokens:
            if tok in node_lower:
                score += 3.0
            if tok in content_lower:
                score += 1.5
            if tok in title_lower:
                score += 2.5
            if any(tok in t for t in tags):
                score += 2.0

        if score > 0.0:
            scores[node] = score * confidence

    return scores


def _recall_discrete(
    graph: nx.DiGraph, sorted_seeds: list[str], top_k: int
) -> tuple[list[str], nx.DiGraph, list[dict[str, Any]]]:
    top_nodes = sorted_seeds[:top_k]
    subgraph = graph.subgraph(top_nodes).copy()
    results = [
        {
            'id': n,
            'type': graph.nodes[n].get('type', NodeType.CONCEPT.value),
            'content': graph.nodes[n].get('content', ''),
        }
        for n in top_nodes
    ]
    return top_nodes, subgraph, results


def _recall_ego_neighborhood(
    graph: nx.DiGraph, engine: CognitiveGraphEngine, sorted_seeds: list[str], top_k: int
) -> tuple[list[str], nx.DiGraph, list[dict[str, Any]]]:
    focal_nodes = sorted_seeds[:top_k]
    subgraph = engine.extract_bounded_ego_subgraph(
        center_nodes=focal_nodes,
        radius=1,
        max_nodes=max(top_k * 2, 8),
    )
    accessed = list(subgraph.nodes())
    results: list[dict[str, Any]] = []
    for node in accessed:
        ndata = graph.nodes[node]
        direct_neighbors = [
            {'target': nbr, 'type': graph.edges[node, nbr].get('type', 'links')}
            for nbr in graph.successors(node)
            if nbr in subgraph
        ]
        record: dict[str, Any] = {
            'id': node,
            'type': ndata.get('type', NodeType.CONCEPT.value),
            'content': ndata.get('content', ''),
        }
        if direct_neighbors:
            record['relations'] = direct_neighbors
        results.append(record)
    return accessed, subgraph, results


def _recall_ppr_communities(
    graph: nx.DiGraph, engine: CognitiveGraphEngine, seed_scores: dict[str, float], sorted_seeds: list[str], top_k: int
) -> tuple[list[str], nx.DiGraph, list[dict[str, Any]]]:
    ppr_ranked = engine.associative_ppr_recall(seed_scores=seed_scores, alpha=0.15, top_k=max(top_k * 2, 10))
    ppr_node_dict = dict(ppr_ranked)
    communities = engine.detect_louvain_communities()

    focal_node = ppr_ranked[0][0] if ppr_ranked else sorted_seeds[0]
    focal_community: set[str] = set()
    community_id = 0
    for idx, comm in enumerate(communities):
        if focal_node in comm:
            focal_community = comm
            community_id = idx + 1
            break

    candidate_nodes = set(ppr_node_dict.keys()) | (focal_community & set(sorted_seeds))
    subgraph = graph.subgraph(candidate_nodes).copy()
    if len(subgraph) > max(top_k * 2, 10):
        degrees = dict(subgraph.degree())
        sorted_by_rank = sorted(
            subgraph.nodes(),
            key=lambda n: (ppr_node_dict.get(n, 0.0), degrees.get(n, 0)),
            reverse=True,
        )
        subgraph = subgraph.subgraph(sorted_by_rank[: max(top_k * 2, 10)]).copy()

    accessed = list(subgraph.nodes())
    results = [
        {
            'id': node,
            'type': graph.nodes[node].get('type', NodeType.CONCEPT.value),
            'content': graph.nodes[node].get('content', ''),
            'score': round(ppr_node_dict.get(node, 0.0), 4),
            'community': f'Cluster {community_id}' if community_id else 'Default',
        }
        for node in accessed
    ]
    return accessed, subgraph, results


def _recall_exhaustive(
    graph: nx.DiGraph, engine: CognitiveGraphEngine, seed_scores: dict[str, float], sorted_seeds: list[str], top_k: int
) -> tuple[list[str], nx.DiGraph, list[dict[str, Any]]]:
    ppr_ranked = engine.associative_ppr_recall(seed_scores=seed_scores, alpha=0.15, top_k=max(top_k * 3, 12))
    ppr_node_dict = dict(ppr_ranked)
    communities = engine.detect_louvain_communities()

    focal_node = ppr_ranked[0][0] if ppr_ranked else sorted_seeds[0]
    focal_community: set[str] = set()
    community_id = 0
    for idx, comm in enumerate(communities):
        if focal_node in comm:
            focal_community = comm
            community_id = idx + 1
            break

    candidate_nodes = set(ppr_node_dict.keys()) | focal_community
    subgraph = graph.subgraph(candidate_nodes).copy()
    if len(subgraph) > max(top_k * 3, 12):
        degrees = dict(subgraph.degree())
        sorted_by_rank = sorted(
            subgraph.nodes(),
            key=lambda n: (ppr_node_dict.get(n, 0.0), degrees.get(n, 0)),
            reverse=True,
        )
        subgraph = subgraph.subgraph(sorted_by_rank[: max(top_k * 3, 12)]).copy()

    accessed = list(subgraph.nodes())
    tms_conflicts = engine.check_tms_contradictions(accessed)
    git_validations = engine.validate_git_anchors(accessed)

    results = []
    for node in accessed:
        ndata = graph.nodes[node]
        node_conflicts = [c for c in tms_conflicts if c['source'] == node or c['target'] == node]
        node_git = git_validations.get(node, {'status': 'unanchored'})
        results.append(
            {
                'id': node,
                'type': ndata.get('type', NodeType.CONCEPT.value),
                'content': ndata.get('content', ''),
                'score': round(ppr_node_dict.get(node, 0.0), 4),
                'community': f'Cluster {community_id}' if community_id else 'Default',
                'git_status': node_git.get('status', 'unanchored'),
                'tms_conflicts': node_conflicts if node_conflicts else None,
            }
        )
    return accessed, subgraph, results


def topological_recall(
    query: str,
    persona_dir: Path,
    effort: int = 0,
    deep: bool = False,
    mermaid: bool = False,
    top_k: int = 5,
) -> str:
    """
    Graph-enhanced semantic recall logic supporting the Cognitive Effort Spectrum (EP-0136).

    Effort Spectrum:
      - 0: Fast BM25 / keyword discrete node lookup (<5ms).
      - 1-4: Vector match + 1-Hop Ego Neighborhood context (~20ms).
      - 5-7 (--deep): HippoRAG Personalized PageRank + Louvain Community Subgraph (~50ms).
      - 8-10: Full PPR + Louvain + TMS contradiction checks + Git commit anchor verification (~120ms).
    """
    from tur.memory.introspection import load_cognitive_map

    resolved_effort = max(effort, 5) if deep else effort

    graph = load_cognitive_map(persona_dir)

    if graph is None or graph.number_of_nodes() == 0:
        return _l1_fallback_search(query, persona_dir)

    seed_scores = _calculate_seed_scores(graph, query)
    if not seed_scores:
        l1_res = _l1_fallback_search(query, persona_dir)
        if not l1_res.startswith('No memories found'):
            return l1_res
        return f"No memories found matching query: '{query}'"

    engine = CognitiveGraphEngine(graph)
    sorted_seeds = sorted(seed_scores.keys(), key=lambda n: seed_scores[n], reverse=True)

    if resolved_effort == 0:
        accessed_nodes, subgraph, results = _recall_discrete(graph, sorted_seeds, top_k)
    elif resolved_effort <= 4:
        accessed_nodes, subgraph, results = _recall_ego_neighborhood(graph, engine, sorted_seeds, top_k)
    elif resolved_effort <= 7:
        accessed_nodes, subgraph, results = _recall_ppr_communities(graph, engine, seed_scores, sorted_seeds, top_k)
    else:
        accessed_nodes, subgraph, results = _recall_exhaustive(graph, engine, seed_scores, sorted_seeds, top_k)

    log_path = persona_dir / 'recall_access_log.txt'
    with contextlib.suppress(Exception), open(log_path, 'a', encoding='utf-8') as f:
        for node in accessed_nodes:
            f.write(f'{node}\n')

    json_str = json.dumps(results, indent=2)

    if mermaid and subgraph is not None:
        mermaid_code = engine.format_subgraph_as_mermaid(subgraph)
        return f'{json_str}\n\n```mermaid\n{mermaid_code}\n```'

    return json_str
