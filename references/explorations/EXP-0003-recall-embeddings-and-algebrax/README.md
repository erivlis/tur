# EXP-0003: Recall Embeddings & AlgebraX Integration

| Field | Value |
| :--- | :--- |
| **EXP** | 0003 |
| **Title** | Recall Embeddings & AlgebraX Integration |
| **Author** | Eran Rivlis, Ariel |
| **Status** | Concluded (Draft EP Authored) |
| **Type** | Architectural Exploration |
| **Created** | 2026-08-27 |
| **Updated** | 2026-08-30 |
| **Related EPs**| [EP-0136](../../docs/proposals/EP-0136-graph-theoretic-semantic-retrieval-and-topological-metrics.md), [EP-0139](../../docs/proposals/EP-0139-tensor-algebraic-provenance-and-simplicial-homology.md), [EP-0144](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md) |

---

## 1. Abstract & Context

This exploration analyzed the architectural implications of upgrading Tur's `recall` command. Currently, `recall` relies on pure substring and keyword matching combined with a 2-hop topological spreading activation via `networkx`. The goal was to explore how to integrate Dense Vector Embeddings (specifically `SentenceTransformers`) to solve the "vocabulary mismatch" problem, while adhering to Tur's strict constraints: lightweight, fast CLI startup, deterministic, and dependency-minimal (The Tur Tur Principle).

---

## 2. Exploration & Options Analysis

### 2.1 Dense Vector Search (`SentenceTransformers`)
The initial concept proposed integrating `SentenceTransformers` to enable semantic search over the L2 Knowledge Graph.

* **Pros:**
  * Resolves vocabulary mismatch (e.g., searching "fast" matches "performant").
  * Highly synergistic with **EP-0136** (Graph-Theoretic Semantic Retrieval / HippoRAG), allowing dense vectors to find initial seed nodes before topological traversal.
* **Cons (The Dependency Bloat):**
  * `SentenceTransformers` relies on PyTorch, introducing a $\sim 2\text{GB}$ dependency footprint and violating Tur's lightweight CLI goals.
  * Unacceptable cold-start latency when loading PyTorch and heavy model weights into memory on CLI invocation.

### 2.2 The ONNX Runtime Optimization
To mitigate the PyTorch footprint, the exploration investigated using the **ONNX Runtime** with the quantized `all-MiniLM-L6-v2` model.

* **Model Stats:** `all-MiniLM-L6-v2` (ONNX INT8 port) is $\sim 80\text{MB}$, requires $\sim 43-100\text{MB}$ RAM, and processes 50–200 sentences/second on a single CPU thread.
* **Architecture:** By relying on `onnxruntime` and a tokenization extra, Tur avoids PyTorch entirely.
* **Benefits:** Millisecond startup times, cross-platform compatibility (macOS, Windows, Linux, Apple Silicon), and minimal package bloat.

### 2.3 Schema Isolation & OKF Storage
A critical deployment challenge with embeddings is "Semantic Topology Drift"—if the embedding model changes, old vectors become mathematically incompatible.

* **Solution:** Leverage Tur's **Open Knowledge Format (OKF)** Markdown files.
* Embeddings and model metadata are stored directly in the YAML frontmatter of L1 memories:
  ```yaml
  embedding_model: all-MiniLM-L6-v2_onnx_int8
  embedding_vector: [0.12, -0.43, 0.91, ...]
  ```
* This isolates the source-of-truth. If the model is upgraded, Tur's `wake()` or `introspect` pipelines detect the version mismatch and trigger a background backfill, re-embedding from raw Markdown text.

---

## 3. Architectural Synthesis & Constraint Alignment

### 3.1 The AlgebraX Unification
The discussion introduced `sparse_neural_backprop.py` from the `algebrax` repository, demonstrating that exact tensor math and dot products can be performed using pure Python dictionaries.

1. **Generation:** Embeddings are generated via an external API or lightweight ONNX extra.
2. **Storage:** The dense array is converted into a sparse vector (dictionary) and stored natively in the OKF YAML.
3. **Similarity Math:** Tur uses `algebrax` natively to compute dot products and cosine similarity between query and memory vectors.
4. **Traversal:** Matches seed the topological traversal proposed in EP-0136 and EP-0139.

---

## 4. The Verdict / Actionable Design

While `algebrax` provides mathematical purity and zero dependencies, pure Python math scales linearly. For 1,000 memories, Python is fast; for 100,000 memories, it introduces noticeable CLI lag.

### The "Escape Hatch" Multi-Tier Fallback:
Tur implements a graceful degradation architecture for similarity computation:

```python
def compute_similarity(query_vec, memory_vectors):
    try:
        # Fast Path (C-backend): If numpy is available (e.g. via `tur[embeddings]`)
        import numpy as np
        return np.dot(memory_vectors, query_vec)
    except ImportError:
        # Pure Path (Python): Zero-dependency fallback for standard usage
        import algebrax as ax
        return ax.matrix.dot(memory_vectors, query_vec)
```

This preserves the zero-dependency ethos for standard users while allowing enterprise workloads to scale effortlessly.

---

## 5. Related Enhancement Proposals

* [`EP-0136: Graph-Theoretic Semantic Subgraph Retrieval and Topological Cognitive Metrics`](../../docs/proposals/EP-0136-graph-theoretic-semantic-retrieval-and-topological-metrics.md)
* [`EP-0139: Tensor-Algebraic Provenance and Simplicial Homology via AlgebraX`](../../docs/proposals/EP-0139-tensor-algebraic-provenance-and-simplicial-homology.md)
* [`EP-0144: Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval`](../../docs/proposals/EP-0144-zero-dependency-dense-semantic-embeddings.md)
