---
title: "EP-0136: Graph-Theoretic Semantic Subgraph Retrieval and Topological Cognitive Metrics"
description: "Integrates NetworkX graph algorithms, HippoRAG Personalized PageRank associative retrieval, Louvain community clustering, --effort <0-10> modulation, and spectral algebraic connectivity (λ2) into Tur memory."
icon: lucide/network
status: accepted
---

# EP-0136: Graph-Theoretic Semantic Subgraph Retrieval and Topological Cognitive Metrics

| Field        | Value                                                                         |
|:-------------|:------------------------------------------------------------------------------|
| **EP**       | 0136                                                                          |
| **Title**    | Graph-Theoretic Semantic Subgraph Retrieval and Topological Cognitive Metrics |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                         |
| **Sponsor**  | Council of Giants                                                             |
| **Delegate** | Shannon (Topological Entropy), Bacon (Empirical Benchmarks)                   |
| **Status**   | Accepted                                                                      |
| **Type**     | Standards Track                                                               |
| **Created**  | 2026-08-28                                                                    |
| **Updated**  | 2026-09-04                                                                    |

---

## Abstract

This proposal replaces flat, isolated vector similarity retrieval in Tur with a **Graph-Theoretic Memory Engine** built
natively on NetworkX. Incorporating principles from **HippoRAG** (Personalized PageRank associative activation) and
**LightRAG** (dual-level community clustering), Tur enables single-step multi-hop reasoning across its L2 Cognitive Map.
We introduce an adjustable **Cognitive Effort Spectrum** (`tur recall --effort <0..10>` with `--deep` alias) and
conditional Mermaid subgraph rendering (`--mermaid` via `networkx-mermaid`). Furthermore, we integrate **Spectral Graph
Theory** into `src/tur/metrics.py`, computing the **Algebraic Connectivity** (Fiedler eigenvalue $\lambda_2$) and
**Modularity** ($Q$) to detect cognitive fragmentation and reasoning bottlenecks in real time.

---

## Motivation

Traditional agent memory systems rely heavily on flat vector retrieval (Top-K Cosine Similarity). In complex software
architectures, this produces critical failure modes:

1. **The Tunnel Vision Problem:** Dense embeddings match text with superficial lexical similarity, completely missing
   multi-hop causal connections scattered across disparate documents.
2. **Context Fragmentation:** An agent retrieves isolated statements without their relational justifications (e.g.
   retrieving *"Use stdio transport"* without the parent node *"Refactored by EP-0124 to isolate parallel workspaces"*).
3. **No Compute Budget Modulation:** Agents execute the same rigid lookup regardless of whether they need a trivial
   variable name or a deep multi-module architectural synthesis.
4. **Lack of Topological Diagnostics:** Existing systems cannot quantify whether an agent's knowledge base is coherent,
   siloed, or descending into ungrounded circular logic.

---

## Rationale

### Alignment with the Council Framework

- **Information & Channel Capacity (Shannon):** Rather than flooding context with raw unlinked text, Louvain community
  partitioning and bounded ego-subgraphs inject dense, high-signal relational subgraphs into the prompt.
- **Empiricism & Verification (Bacon):** High effort levels validate supporting premises directly against Git commit
  ground truth before injecting memories.
- **Falsifiability (Popper):** Relational edges (`supported_by`, `contradicts`, `refutes`) allow spreading activation to
  down-weight or extinguish refuted belief branches automatically.

---

## Specification

### 1. The Cognitive Effort Spectrum (`tur recall --effort <0-10>`)

The `recall` CLI command and MCP tool are augmented with an integer `effort` parameter ($0 \le \text{effort} \le 10$)
and a `--deep` convenience alias:

```
EFFORT LEVEL           MECHANISM                                   LATENCY / APPLICATION
────────────           ─────────                                   ─────────────────────
[0] (Default / Fast)   • Fast BM25 keyword + flat vector cosine    < 5ms
                       • Returns top-K discrete memory nodes.      Simple fact lookups ("What is the persona ID?")

[1 – 4] (Light Context)• Vector match + 1-Hop Ego Neighborhood    ~ 20ms
                       • Pulls direct justifications (supported_by)Basic architectural context

[5 – 7] (`--deep`)     • HippoRAG Personalized PageRank (PPR)      ~ 50ms
                       • Louvain Community Subgraph extraction     Multi-hop reasoning ("Why did we choose SQLite?")
                       • Bounded context block / Mermaid diagram   

[8 – 10] (Exhaustive)  • Full PPR + Louvain Community              ~ 120ms
                       • Real-time Git Commit Validation (EP-0131) Mission-critical refactors, security audits,
                       • Active TMS Contradiction Checks (EP-0134) and multi-agent consensus verification
```

### 2. Personalized PageRank (PPR) Associative Traversal

For effort levels $\ge 5$, Tur executes random walks with restart over the directed L2 Cognitive Map:

$$\mathbf{p}^* = (1 - \alpha) \mathbf{W}^{\top} \mathbf{p}^* + \alpha \mathbf{p}_0$$

Where:

- $\mathbf{p}_0$ is the initial query concept teleportation vector (derived from lexical BM25 seed relevance).
- $\mathbf{W}$ is the normalized transition matrix weighted by semantic edge types (`supported_by: 1.5`,
  `depends_on: 1.4`, `refines: 1.3`, `metaphor_for: 1.2`, `related_to: 0.8`, `contradicts: 0.01`).
- $\alpha = 0.15$ is the restart probability.

#### 2.1 Comparative Analysis of Three PageRank Engines

Tur evaluates three distinct execution backends for graph spreading activation:

| Backend Engine                                                   | Mechanism                                                              | Pros                                                                                                                                                | Cons                                                                                                              | Ideal Use Case in Tur                                                                                   |
|:-----------------------------------------------------------------|:-----------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------|
| **Inlined Pure-Python**<br>(`tur.recall.pure_pagerank`)          | Direct adjacency iteration with inlined primitive float arithmetic.    | • Zero dependencies (pure standard library).<br>• Fast convergence ($< 1\text{ms}$ on $N < 1,000$).<br>• Built-in personalization & edge weighting. | • Linear pure-Python scaling on massive graphs ($N > 10,000$).                                                    | **Default Core:** Standard cognitive maps ($N \approx 50\text{–}1,000$) in zero-install environments.   |
| **NetworkX / SciPy**<br>(`networkx.pagerank`)                    | SciPy sparse CSR matrices and compiled C/Fortran solvers.              | • Highly optimized vectorization on massive scale ($N > 10,000$).                                                                                   | • Heavy compiled binary wheels (`scipy` + `numpy`, ~150–200MB).<br>• Throws `ModuleNotFoundError` in default Tur. | **Massive Scale Extra:** Enterprise codebases with large external dependency graphs.                    |
| **AlgebraX Semiring Engine**<br>(`algebrax.algorithms.pagerank`) | Vector-matrix dot products over algebraic semirings (`ax.matrix.dot`). | • Pure Python with zero binary dependencies.<br>• Generalizes across semirings: Tropical $(\max, +)$ and Provenance Polynomials $\mathbb{N}[X]$.    | • Generic semiring dispatch overhead per scalar op compared to inlined float arithmetic.                          | **Algebraic & Provenance (EP-0139):** Tracing exact epistemic lineage and causal paths across memories. |

#### 2.2 Multi-Tier Graceful Delegation & Fallback Strategy

To balance zero-install portability with high scalability and algebraic provenance, Tur adopts a 3-tier fallback architecture:

1. **Tier 1 (Algebraic Provenance):** If `algebrax` is installed and the caller requests semiring provenance or causal reasoning path extraction (EP-0139), delegate to `algebrax.algorithms.pagerank`.
2. **Tier 2 (Large-Scale Acceleration):** If `scipy` and `numpy` are detected in the runtime environment and graph node count $N \ge 2,000$, delegate to `nx.pagerank` for compiled vector acceleration.
3. **Tier 3 (Universal Baseline):** Default to inlined `pure_pagerank`, guaranteeing sub-millisecond execution and zero external binary requirements in all standard installations.

### 3. Conditional Mermaid Visualization (`--mermaid`)

Using the lightweight `networkx-mermaid` package, developers and agents can request structured graphical visualization
of the retrieved subgraph:

```shell
# Returns bounded Mermaid flowchart alongside structured memory records
tur recall "file locking architecture" --deep --mermaid
```

### 4. Spectral Graph Diagnostics in `tur metrics`

`src/tur/metrics.py` is extended to calculate:

- **Algebraic Connectivity ($\lambda_2$):** The second-smallest eigenvalue of the normalized graph
  Laplacian $\mathbf{L} = \mathbf{D} - \mathbf{A}$. $\lambda_2 > 0$ guarantees that the memory graph is fully integrated
  with no isolated knowledge silos.
- **Louvain Modularity ($Q$):** Measures the density of internal cluster connections versus cross-cluster links.
- **Epistemic Entropy ($H (\mathcal{K})$):** Quantifies knowledge disorder across communities.

```
┌─────────────────────────── System Metrics: Ariel ───────────────────────────┐
│                                                                             │
│   Persona                 Ariel (7544202e-92f5-40ce-adfb-e4b0eae6c262)      │
│   Principles (N)          9                                                 │
│   Constraint Dim (Cp)     17.8 (Titan (Inference Warning))                  │
│                                                                             │
│   Static Token Cost       ~1356                                             │
│   Information Density     0.645                                             │
│                                                                             │
│   Graph Nodes / Edges     42 nodes / 78 edges                               │
│   Knowledge Communities   4 Louvain Clusters                                │
│   Algebraic Connectivity  0.412 (Well-Integrated)                           │
│   Modularity Score (Q)    0.681                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backwards Compatibility

- **Default Invocation:** Invoking `tur recall "query"` without flags runs in `--effort 0` mode, matching the legacy
  speed and output format with 100% backwards compatibility.
- **Zero Heavy Binary Dependencies:** Built entirely on NetworkX (already a core dependency) and `networkx-mermaid`
  ($8.2\text{ KB}$ pure Python).

---

## How to Teach This / Documentation Plan

- Update [`docs/usage.md`](../usage.md) with examples of `tur recall --effort <N>`,
  `tur recall --deep`, and `--mermaid`.
- Update `.agents/skills/tur/references/commands-and-mcp-tools.md` to document the effort spectrum.
- Add an informational essay on GraphRAG and HippoRAG associative retrieval in `docs/concepts/`.

---

## Reference Implementation

- Graph Engine: `src/tur/recall.py`
- Spectral Metrics: `src/tur/metrics.py`
- Research references:
  `references/explorations/EXP-0004-persona-and-memory-crystallization/03_graph_theoretic_memory_and_topological_retrieval.md`

---

## Rejected Ideas

- **Mandatory Iterative RAG (IRCoT):** Rejected because multi-step LLM search is 10–30x more expensive and 6–13x slower
  than single-step Personalized PageRank on knowledge graphs.
- **Always Forcing Mermaid in Prompt Payloads:** Rejected to preserve Shannon token efficiency. Mermaid diagrams are
  generated conditionally when `--mermaid` is explicitly requested.

---

## Open Questions

- [ ] What is the optimal restart probability $\alpha$ for deep codebase reasoning (empirically tested between 0.10 and
  0.20)?
- [ ] Should `--effort 10` automatically open a background task to verify stale Git anchors across the entire L2 graph?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the August 28, 2026 Architectural Crystallization.
