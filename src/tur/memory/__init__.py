"""Authoritative public facade for the Tur memory subsystem (EP-0146).

Consolidates L1 flat persistence, Merkle trees, L2 cognitive maps, graph-theoretic recall,
session transcript dreaming, observation provenance, delta tracking, and sanitization.
"""

from tur.memory.diff import (
    compute_session_diff,
    format_diff_json,
    format_diff_summary,
    format_diff_terminal,
)
from tur.memory.dreaming import perform_sleep_dreaming, stage_sleep_dreaming
from tur.memory.introspection import (
    IntrospectionAssembly,
    format_graph_as_mermaid,
    load_cognitive_map,
    load_l2_graph_from_okf,
    run_introspection,
    save_l2_graph_to_okf,
)
from tur.memory.provenance import (
    DEFAULT_DECAY_POLICIES,
    create_provenance_and_decay,
    evaluate_staleness,
    get_git_commit_distance,
    get_git_head_sha,
)
from tur.memory.recall import (
    SEMANTIC_EDGE_WEIGHTS,
    CognitiveGraphEngine,
    pure_algebraic_connectivity,
    pure_pagerank,
    topological_recall,
)
from tur.memory.sanitizer import (
    calculate_shannon_entropy,
    detect_high_entropy_tokens,
    is_sensitive,
    sanitize_text,
)
from tur.memory.storage import MemoryManager

__all__ = [
    'DEFAULT_DECAY_POLICIES',
    'SEMANTIC_EDGE_WEIGHTS',
    'CognitiveGraphEngine',
    'IntrospectionAssembly',
    'MemoryManager',
    'calculate_shannon_entropy',
    'compute_session_diff',
    'create_provenance_and_decay',
    'detect_high_entropy_tokens',
    'evaluate_staleness',
    'format_diff_json',
    'format_diff_summary',
    'format_diff_terminal',
    'format_graph_as_mermaid',
    'get_git_commit_distance',
    'get_git_head_sha',
    'is_sensitive',
    'load_cognitive_map',
    'load_l2_graph_from_okf',
    'perform_sleep_dreaming',
    'pure_algebraic_connectivity',
    'pure_pagerank',
    'run_introspection',
    'sanitize_text',
    'save_l2_graph_to_okf',
    'stage_sleep_dreaming',
    'topological_recall',
]
