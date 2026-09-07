from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
import networkx as nx

from tur.memory.recall import SEMANTIC_EDGE_WEIGHTS, pure_pagerank
from tur.models import SessionState

_TEMPLATE_DIR = Path(__file__).parent / 'templates'
_JINJA_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=10,
)
_PERSONA_TEMPLATE = _JINJA_ENV.get_template('persona.j2')


def estimate_tokens(text: str) -> int:
    """
    Fast, deterministic token estimator approximating BPE / Subword tokenization.
    Splits on alphanumeric words and individual punctuation symbols.
    """
    if not text:
        return 0
    tokens = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return max(1, len(tokens))


def knapsack_01(
    weights: list[int],
    values: list[float],
    capacity: int,
) -> list[int]:
    """
    Solves the 0-1 Knapsack problem.
    Returns the list of indices of selected items maximizing total value
    such that total weight <= capacity.
    """
    n = len(weights)
    if capacity <= 0 or n == 0:
        return []
    if sum(weights) <= capacity:
        return list(range(n))

    # For standard token budgets (capacity * n <= 2_000_000), use exact dynamic programming
    if capacity * n <= 2_000_000:
        dp = [0.0] * (capacity + 1)
        keep = [[False] * (capacity + 1) for _ in range(n)]

        for i in range(n):
            w = weights[i]
            v = values[i]
            if w <= 0:
                continue
            if w > capacity:
                continue
            for c in range(capacity, w - 1, -1):
                new_val = dp[c - w] + v
                if new_val > dp[c]:
                    dp[c] = new_val
                    keep[i][c] = True

        selected = []
        curr = capacity
        for i in range(n - 1, -1, -1):
            if keep[i][curr]:
                selected.append(i)
                curr -= weights[i]
        selected.reverse()

        # Always include free items (w <= 0)
        for i in range(n):
            if weights[i] <= 0 and i not in selected:
                selected.append(i)
        selected.sort()
        return selected

    # High-capacity greedy value-density heuristic fallback
    indexed_items = sorted(
        range(n),
        key=lambda i: (values[i] / max(1, weights[i]), values[i]),
        reverse=True,
    )
    selected = []
    used = 0
    for i in indexed_items:
        if used + weights[i] <= capacity:
            selected.append(i)
            used += weights[i]
    selected.sort()
    return selected


def _extract_seed_scores(
    nodes: list[dict[str, Any]],
    epilogue: str | None = None,
    cores: list[Any] | None = None,
) -> dict[str, float]:
    """
    Extracts query/context seeds from active continuity epilogue and core principles
    for HippoRAG Personalized PageRank activation.
    """
    seed_scores: dict[str, float] = {}
    context_tokens: set[str] = set()

    if epilogue:
        context_tokens.update(t.lower() for t in re.findall(r'\w+', epilogue))

    if cores:
        for c in cores:
            derived = getattr(c, 'derived_principle', None) or (
                c.get('derived_principle') if isinstance(c, dict) else ''
            )
            if derived:
                context_tokens.update(t.lower() for t in re.findall(r'\w+', derived))

    for node in nodes:
        node_id = str(node.get('id', ''))
        content = str(node.get('content', ''))
        is_pinned = bool(node.get('pinned', False))

        score = 0.0
        if is_pinned:
            score += 2.0

        # Check if node id or label tokens appear in context
        id_tokens = set(t.lower() for t in re.findall(r'\w+', node_id))
        overlap = id_tokens.intersection(context_tokens)
        if overlap:
            score += len(overlap) * 1.5

        # Check content keyword overlap
        content_tokens = set(t.lower() for t in re.findall(r'\w+', content[:100]))
        content_overlap = content_tokens.intersection(context_tokens)
        if content_overlap:
            score += len(content_overlap) * 0.5

        if score > 0:
            seed_scores[node_id] = score

    return seed_scores


def apply_budgeted_wake(
    state: SessionState,
    token_budget: int,
    tokenizer: Callable[[str], int] = estimate_tokens,
) -> SessionState:
    """
    Applies Knapsack dynamic token budgeting (EP-0132) to prioritize and pack
    top-ranked HippoRAG memory subgraphs or memories within the token budget.
    Returns a new SessionState with pruned items and context_omitted set.
    """
    if token_budget <= 0:
        return state

    # 1. Compute Base Invariant Cost (without dynamic memories/kg)
    base_dict = state.model_dump()
    base_dict['knowledge_graph'] = None
    base_dict['memories'] = []
    base_dict['context_omitted'] = None
    base_prompt = _PERSONA_TEMPLATE.render(base_dict)
    base_cost = tokenizer(base_prompt)

    remaining_budget = max(0, token_budget - base_cost)

    # 2. Case A: Knowledge Graph Budgeting
    if state.knowledge_graph and state.knowledge_graph.get('nodes'):
        raw_nodes = [
            n
            for n in state.knowledge_graph.get('nodes', [])
            if n.get('status') not in ('archived', 'superseded')
            and (n.get('confidence') is None or float(n.get('confidence', 1.0)) > 0.2)
        ]
        raw_links = [
            link
            for link in state.knowledge_graph.get('links', [])
            if (link.get('confidence') is None or float(link.get('confidence', 1.0)) > 0.2)
        ]

        if not raw_nodes:
            return state

        # Build DiGraph for HippoRAG PPR
        graph = nx.DiGraph()
        for node in raw_nodes:
            graph.add_node(str(node['id']), **node)
        for link in raw_links:
            src = str(link.get('source'))
            tgt = str(link.get('target'))
            if src in graph and tgt in graph:
                edge_type = str(link.get('type', 'links')).lower()
                weight = SEMANTIC_EDGE_WEIGHTS.get(edge_type, 1.0)
                graph.add_edge(src, tgt, type=link.get('type', 'links'), weight=weight)

        # Extract seeds and run Personalized PageRank
        seeds = _extract_seed_scores(raw_nodes, epilogue=state.epilogue, cores=state.cores)
        ppr_scores = pure_pagerank(graph, alpha=0.85, personalization=seeds if seeds else None, weight_key='weight')

        # Compute salience values and weights for each node
        node_weights: list[int] = []
        node_values: list[float] = []

        for node in raw_nodes:
            nid = str(node['id'])
            ntype = str(node.get('type', 'Concept'))
            content = str(node.get('content', ''))
            pinned = bool(node.get('pinned', False))
            conf = float(node.get('confidence', 1.0))
            ppr_val = float(ppr_scores.get(nid, 0.0))

            rendered_node = f'* **{nid}** ({ntype}):\n  {content}' + (' [PINNED]' if pinned else '')
            w = tokenizer(rendered_node)
            node_weights.append(w)

            val = (ppr_val + 1e-4) * conf * (2.0 if pinned else 1.0)
            node_values.append(val)

        # Solve 0-1 Knapsack for nodes
        selected_node_indices = knapsack_01(node_weights, node_values, remaining_budget)
        selected_nodes = [raw_nodes[i] for i in selected_node_indices]
        selected_ids = {str(n['id']) for n in selected_nodes}

        nodes_cost = sum(node_weights[i] for i in selected_node_indices)
        remaining_edge_budget = max(0, remaining_budget - nodes_cost)

        # Filter candidate links connecting selected nodes
        candidate_links = [
            link
            for link in raw_links
            if str(link.get('source')) in selected_ids and str(link.get('target')) in selected_ids
        ]

        link_weights: list[int] = []
        link_values: list[float] = []
        for link in candidate_links:
            rendered_link = f"* {link['source']} --[{link.get('type', 'links')}]--> {link['target']}"
            link_weights.append(tokenizer(rendered_link))
            edge_type = str(link.get('type', 'links')).lower()
            link_values.append(SEMANTIC_EDGE_WEIGHTS.get(edge_type, 1.0))

        selected_link_indices = knapsack_01(link_weights, link_values, remaining_edge_budget)
        selected_links = [candidate_links[i] for i in selected_link_indices]

        omitted_count = len(raw_nodes) - len(selected_nodes)

        budgeted_kg = dict(state.knowledge_graph)
        budgeted_kg['nodes'] = selected_nodes
        budgeted_kg['links'] = selected_links

        new_data = state.model_dump()
        new_data['knowledge_graph'] = budgeted_kg
        new_data['context_omitted'] = omitted_count if omitted_count > 0 else None
        new_data['token_budget'] = token_budget
        return SessionState.model_validate(new_data)

    # 3. Case B: Flat Memories Budgeting (when knowledge_graph is absent)
    if state.memories:
        raw_memories = list(state.memories)
        mem_weights: list[int] = []
        mem_values: list[float] = []

        for m in raw_memories:
            rendered_mem = f"* {m.timestamp.strftime('%Y-%m-%d')} [{m.type.value.upper()} / {m.scope.value.upper()}]: {m.content} (Tags: {', '.join(m.tags)})"
            w = tokenizer(rendered_mem)
            mem_weights.append(w)

            conf = float(m.confidence) if hasattr(m, 'confidence') else 1.0
            days_old = (
                max(0.0, (datetime.now() - m.timestamp).total_seconds() / 86400.0)
                if hasattr(m, 'timestamp')
                else 0.0
            )
            recency = 1.0 / (1.0 + 0.05 * days_old)
            val = conf * recency
            mem_values.append(val)

        selected_mem_indices = knapsack_01(mem_weights, mem_values, remaining_budget)
        selected_memories = [raw_memories[i] for i in selected_mem_indices]
        omitted_count = len(raw_memories) - len(selected_memories)

        new_data = state.model_dump()
        new_data['memories'] = selected_memories
        new_data['context_omitted'] = omitted_count if omitted_count > 0 else None
        new_data['token_budget'] = token_budget
        return SessionState.model_validate(new_data)

    return state


def compile_persona(
    state: SessionState,
    token_budget: int | None = None,
    tokenizer: Callable[[str], int] | None = None,
) -> str:
    """
    Renders a SessionState into a final System Prompt string using pre-compiled AST.
    If token_budget is specified (or state.token_budget is set), applies Knapsack
    dynamic token budgeting to pack top-ranked HippoRAG memory subgraphs (EP-0132).
    """
    eff_budget = token_budget if token_budget is not None else state.token_budget
    eff_tokenizer = tokenizer or estimate_tokens

    if eff_budget is not None and eff_budget > 0:
        budgeted_state = apply_budgeted_wake(state, token_budget=eff_budget, tokenizer=eff_tokenizer)
        return _PERSONA_TEMPLATE.render(budgeted_state.model_dump())

    return _PERSONA_TEMPLATE.render(state.model_dump())
