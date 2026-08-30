# Deep Dive 3: Graph-Theoretic Memory & Topological Retrieval

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/03_graph_theoretic_memory_and_topological_retrieval.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Graph-theoretic knowledge structures, community detection, associative spreading activation (HippoRAG), and NetworkX integration for Tur's L2 Cognitive Map.

---

## 1. Executive Summary: Moving Beyond Flat Vector RAG

Most AI agent memory systems (MemGPT/Letta, Mem0, Zep, LangGraph) rely on **flat vector similarity (Top-K Cosine Distance)**. While vector retrieval is fast, it suffers from severe cognitive failure modes:
1. **The Tunnel Vision Dilemma:** Dense embedding vectors match text with direct lexical or superficial semantic overlap, but completely miss multi-hop causal connections scattered across disparate documents.
2. **Context Fragmentation:** An agent retrieves 5 isolated snippets without their relational justifications (e.g. retrieving *"Use stdio transport"* without the parent node *"Refactored by EP-0124 to isolate parallel workspaces"*).
3. **No Global Epistemic Topology:** Flat stores cannot answer structural questions like *"What are the core architecture clusters of this system?"* or *"What are our unresolved exploratory gaps?"*

Tur's Layer 2 (L2) Cognitive Map is fundamentally a **typed, directed Knowledge Graph** (OKF / NetworkX). This document specifies how graph-theoretic algorithms transform memory retrieval from passive keyword search into **associative cognitive traversal**.

---

## 2. Theoretical Paradigms: HippoRAG, LightRAG, and Tur

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          GRAPH-THEORETIC MEMORY MATRIX                          │
├──────────────────────┬──────────────────────┬───────────────────────────────────┤
│       Paradigm       │   Core Mechanism     │      Tur L2 Integration           │
├──────────────────────┼──────────────────────┼───────────────────────────────────┤
│ **HippoRAG**         │ Personalized PageRank│ Associative multi-hop spreading   │
│ (Hippocampal Memory) │ (PPR) random walks   │ activation along typed edges.     │
├──────────────────────┼──────────────────────┼───────────────────────────────────┤
│ **LightRAG**         │ Dual-Level Retrieval │ Local entity subgraphs + Global   │
│ (Dual-Level Graph)   │ (Local + Community)  │ Louvain community summaries.      │
├──────────────────────┼──────────────────────┼───────────────────────────────────┤
│ **Tur Cognitive Map**│ Typed TMS Graph with │ Combines PPR associative search,  │
│ (Topological Kernel) │ Provable Invariants  │ Louvain clusters, and TMS lattices│
└──────────────────────┴──────────────────────┴───────────────────────────────────┘
```

---

## 3. Core Graph-Theoretic Algorithms for Tur

```
                               ┌─────────────────────────┐
                               │   L2 COGNITIVE GRAPH    │
                               │  Nodes (Concepts/Axioms)│
                               │  Edges (Relational TMS) │
                               └────────────┬────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
  │   COMMUNITY DETECTION   │  │  SPREADING ACTIVATION   │  │  SPECTRAL CONNECTIVITY  │
  │    (Louvain / Leiden)   │  │ (Personalized PageRank) │  │  (Fiedler Eigenvalue)   │
  ├─────────────────────────┤  ├─────────────────────────┤  ├─────────────────────────┤
  │ Clusters knowledge into │  │ Multi-hop associative   │  │ Measures cognitive      │
  │ epistemic modules       │  │ traversal from query    │  │ integration vs         │
  │ (Auth, IPC, Prefs)      │  │ seed nodes.             │  │ fragmentation (metrics) │
  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

---

### 3.1. Louvain Modularity Clustering (Epistemic Subdomains)

The L2 Cognitive Map is partitioned into modular communities by maximizing graph modularity $Q$:

$$Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

Where:
- $A_{ij}$ is the edge weight between nodes $i$ and $j$.
- $k_i, k_j$ are node degrees.
- $m$ is the total number of edges.
- $\delta(c_i, c_j) = 1$ if nodes $i, j$ belong to the same community $c$.

#### Cognitive Application in Tur:
- **Automatic Knowledge Domain Discovery:** Nodes naturally cluster into topics such as `[Cluster: File Locking & IPC]`, `[Cluster: Split CLI Architecture]`, `[Cluster: User Coding Taste]`.
- **Community-Level Recall:** When an agent queries a concept (e.g., `tur recall "how does file locking work?"`), Tur identifies the relevant Louvain community and retrieves the **entire coherent subgraph**, preserving full context.

---

### 3.2. Personalized PageRank (PPR) Associative Retrieval (HippoRAG Model)

Rather than searching for direct text matches, Tur seeds a query vector across candidate entry nodes and performs **random walks with restart** over the directed knowledge graph:

$$\mathbf{p}_{t+1} = (1 - \alpha) \mathbf{W}^{\top} \mathbf{p}_t + \alpha \mathbf{p}_0$$

Where:
- $\mathbf{p}_0$ is the teleportation vector (initial semantic similarity to query).
- $\mathbf{W}$ is the column-normalized adjacency transition matrix.
- $\alpha \approx 0.15$ is the restart probability.
- $\mathbf{p}^* = \lim_{t \to \infty} \mathbf{p}_t$ is the stationary probability distribution representing associative cognitive relevance.

#### Why PPR Outperforms Vector Search:
1. **Multi-Hop Traversal:** If Query $\to$ Node A $\xrightarrow{\text{supported\_by}}$ Node B $\xrightarrow{\text{refutes}}$ Node C, Node C receives high activation even if it shares zero lexical tokens with the original query!
2. **Associative Resonance:** Mirrors the biological human memory retrieval mechanism (spreading activation in semantic networks).

---

### 3.3. Betweenness Centrality & Cognitive Horizons

The betweenness centrality $C_B(v)$ of a node $v$ measures the fraction of shortest paths passing through it:

$$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

- **High Betweenness Nodes:** Keystone architectural concepts that bridge two disparate subdomains (e.g., `EP-0116 Split CLI` bridging `Security Boundary` and `MCP Server`).
- **Bridge Edges ($e = (u, v)$ with high edge betweenness):** Represent **Exploratory Horizons**—connections where new insights are actively forming. If removed, the graph fractures into disconnected components.

---

### 3.4. Algebraic Connectivity & Spectral Graph Health ($\lambda_2$)

The algebraic connectivity of a graph is the second-smallest eigenvalue $\lambda_2$ (the **Fiedler value**) of the normalized graph Laplacian matrix $\mathbf{L} = \mathbf{D} - \mathbf{A}$:

$$\mathbf{L} \mathbf{v} = \lambda \mathbf{v}, \quad 0 = \lambda_1 \le \lambda_2 \le \lambda_3 \le \dots \le \lambda_N$$

#### Epistemic Diagnostic Value in `tur metrics`:
- **$\lambda_2 = 0$:** The memory graph is disconnected (contains $\ge 2$ isolated knowledge silos).
- **$\lambda_2 > 0$ (High):** The persona's knowledge base is deeply integrated, cross-referenced, and robust against context loss.
- **Spectral Gap $\Delta \lambda = \lambda_2 - \lambda_1$:** Emitted in `tur metrics` as the **Topological Coherence Index**.

---

## 4. Reference Implementation Prototype

Below is a complete, runnable NetworkX implementation prototype for `src/tur/recall.py` and `src/tur/metrics.py`:

```python
import networkx as nx
from typing import Any
from pydantic import BaseModel

class SubgraphRecallResult(BaseModel):
    focal_nodes: list[dict[str, Any]]
    community_name: str
    subgraph_mermaid: str
    total_tokens: int

class CognitiveGraphEngine:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def compute_spectral_health(self) -> dict[str, Any]:
        """Calculates Fiedler eigenvalue and community modularity for tur metrics."""
        undirected = self.graph.to_undirected()
        
        # 1. Connectivity check
        is_connected = nx.is_connected(undirected) if len(undirected) > 0 else True
        
        # 2. Algebraic Connectivity (Fiedler value)
        if len(undirected) > 2 and is_connected:
            fiedler_val = nx.algebraic_connectivity(undirected, method="lanczos")
        else:
            fiedler_val = 0.0

        # 3. Louvain Community Detection
        if len(undirected) > 1:
            communities = list(nx.community.louvain_communities(undirected))
            modularity = nx.community.modularity(undirected, communities)
        else:
            communities = []
            modularity = 0.0

        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_connected": is_connected,
            "algebraic_connectivity": round(float(fiedler_val), 4),
            "community_count": len(communities),
            "modularity_score": round(float(modularity), 4),
        }

    def associative_ppr_recall(
        self, 
        seed_scores: dict[str, float], 
        alpha: float = 0.15, 
        top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Executes Personalized PageRank (HippoRAG model) spreading activation
        across the directed L2 Cognitive Map.
        """
        if not self.graph.nodes:
            return []

        # Filter seed scores to existing nodes and normalize
        valid_seeds = {n: s for n, s in seed_scores.items() if n in self.graph}
        if not valid_seeds:
            return []
            
        total = sum(valid_seeds.values())
        personalization = {n: s / total for n, s in valid_seeds.items()}

        # Run Personalized PageRank
        ppr_scores = nx.pagerank(
            self.graph, 
            alpha=1.0 - alpha, 
            personalization=personalization, 
            weight="weight"
        )

        ranked = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def extract_bounded_ego_subgraph(
        self, 
        center_node: str, 
        radius: int = 2, 
        max_nodes: int = 8
    ) -> nx.DiGraph:
        """Extracts a bounded k-hop neighborhood for structured context retrieval."""
        ego = nx.ego_graph(self.graph, center_node, radius=radius, undirected=True)
        if len(ego) > max_nodes:
            # Prune lowest degree nodes to respect token budget
            degrees = dict(ego.degree())
            sorted_nodes = sorted(degrees.keys(), key=lambda n: degrees[n], reverse=True)
            ego = ego.subgraph(sorted_nodes[:max_nodes]).copy()
        return ego
```

---

## 5. Source Code Mapping & Architecture Resonances

| Conceptual Feature | Source Code Target | Related Enhancement Proposals |
| :--- | :--- | :--- |
| **Topological Recall API** | [`src/tur/recall.py`](file:///C:/dev/erivlis/tur/src/tur/recall.py) | EP-0103, EP-0120, EP-0132 |
| **Spectral Health & Graph Metrics** | [`src/tur/metrics.py`](file:///C:/dev/erivlis/tur/src/tur/metrics.py) | EP-0004, EP-0117, EP-0136 |
| **L2 OKF Graph Loader & Parser** | [`src/tur/introspection/graph.py`](file:///C:/dev/erivlis/tur/src/tur/introspection/graph.py) | EP-0120, EP-0126 |
| **Contradiction / TMS Traversal** | [`src/tur/introspection/tms.py`](file:///C:/dev/erivlis/tur/src/tur/introspection/tms.py) | EP-0122, EP-0134 |
| **Mermaid Graph Visualizer** | [`src/tur/introspection/__init__.py`](file:///C:/dev/erivlis/tur/src/tur/introspection/__init__.py) | EP-0120, EP-0126 |

---

## 6. Blueprint for EP-0136 (Graph-Theoretic Semantic Retrieval & Metrics)

1. **NetworkX Substrate Adoption:** Standardize `src/tur/recall.py` and `src/tur/introspection/graph.py` on NetworkX `DiGraph` structures.
2. **Cognitive Effort Spectrum (`tur recall --effort <0-10>`):**
   - **`--effort 0` (Default / Instant):** Pure BM25 keyword + flat vector cosine similarity ($< 5\text{ms}$, zero graph overhead). Returns top-K discrete memory nodes.
   - **`--effort 1 - 4` (Light Context):** Vector seeding + 1-hop ego neighborhood retrieval (`supported_by`, `derived_from`).
   - **`--effort 5 - 7` (`--deep`):** Full HippoRAG Personalized PageRank (PPR) spreading activation + Louvain community subgraph extraction formatted as bounded context blocks.
   - **`--effort 8 - 10` (Exhaustive TMS Verification):** Full PPR + Louvain community extraction + real-time Git commit verification (EP-0131) + TMS contradiction checks (EP-0134).
3. **Graph Diagnostics in `tur metrics`:** Display `Algebraic Connectivity` ($\lambda_2$), `Modularity Score` ($Q$), and `Community Count` in both terminal panel and `--json` outputs.
4. **Subgraph Context Resource (`tur://context/subgraph?node={id}&effort={0..10}`):** Expose structured subgraphs over MCP for compatible harnesses.
