# BS-0001: Recall Embeddings & AlgebraX Integration

## 1. Abstract & Context
This brainstorming session explored the architectural implications of upgrading Tur's `recall` command. Currently, `recall` relies on pure substring/keyword matching combined with a 2-hop topological spreading activation via `networkx`. The goal was to explore how to integrate Dense Vector Embeddings (specifically `SentenceTransformers`) to solve the "vocabulary mismatch" problem, while adhering to Tur's strict constraints: lightweight, fast CLI startup, deterministic, and dependency-minimal (The Tur Tur Principle).

## 2. Dense Vector Search (`SentenceTransformers`)
The initial idea proposed integrating `SentenceTransformers` to enable semantic search over the L2 Knowledge Graph.

**Pros:**
* Resolves vocabulary mismatch (e.g., searching "fast" matches "performant").
* Highly synergistic with **EP-0136** (Graph-Theoretic Semantic Retrieval / HippoRAG), allowing dense vectors to find initial seed nodes before topological traversal.

**Cons (The Dependency Bloat):**
* `SentenceTransformers` relies on PyTorch, introducing a ~2GB dependency footprint, violating Tur's lightweight CLI goals.
* High cold-start latency when loading PyTorch and the model into memory.

## 3. The ONNX Runtime Optimization
To mitigate the PyTorch footprint, the session explored using the **ONNX Runtime** with the `all-MiniLM-L6-v2` model.

* **Model Stats:** `all-MiniLM-L6-v2` (ONNX port) is ~80MB, requires ~43-100MB RAM, and can process 50-200 sentences/second on a single-threaded CPU.
* **Architecture:** By relying on `onnxruntime` and `transformers` (tokenizer only), or the modern `sentence-transformers[onnx]` (`backend="onnx"`), Tur avoids PyTorch entirely.
* **Benefits:** Millisecond startup times, cross-platform compatibility (macOS, Windows, Linux, Apple Silicon), and minimal package bloat.

## 4. Schema Isolation & OKF Storage
A critical deployment challenge with embeddings is "Semantic Topology Drift"—if the embedding model changes, old vectors become mathematically incompatible.

* **Solution:** Leverage Tur's **Open Knowledge Format (OKF)** Markdown files.
* Embeddings and their generating model metadata can be stored directly in the YAML frontmatter of L1 memories:
  ```yaml
  embedding_model: all-MiniLM-L6-v2_onnx_int8
  embedding_vector: [0.12, -0.43, 0.91, ...]
  ```
* This isolates the source-of-truth. If the model is upgraded, Tur's `wake()` or `introspect` pipelines can detect the version mismatch and trigger a background backfill, re-embedding from the raw Markdown text.

## 5. The AlgebraX Unification
The discussion introduced `sparse_neural_backprop.py` from the `algebrax` repository, demonstrating that exact neural backpropagation and tensor math can be performed using pure Python dictionaries.

**The Grand Unified Architecture:**
1. **Generation:** Embeddings are generated via an external API or lightweight ONNX extra.
2. **Storage:** The dense array is converted into a sparse vector (dictionary) and stored natively in the OKF YAML.
3. **Similarity Math:** Tur uses `algebrax` natively to compute dot products / cosine similarity between the query and the memory vectors.
4. **Traversal:** Matches seed the topological traversal proposed in EP-0136 / EP-0139.

## 6. The Pragmatic Performance Fallback
While `algebrax` provides mathematical purity and zero dependencies, pure Python math scales poorly. For 1,000 memories, Python is fast; for 100,000 memories, it introduces noticeable CLI lag.

**The "Escape Hatch" Pattern:**
Tur will implement a graceful degradation architecture for similarity computation:
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
