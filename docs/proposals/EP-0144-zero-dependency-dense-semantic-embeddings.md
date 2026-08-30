---
title: "EP-0144: Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval"
description: "Introduces zero-dependency dense semantic embedding retrieval via ONNX runtime and AlgebraX sparse cosine math, solving the vocabulary mismatch problem without PyTorch dependency bloat."
icon: lucide/binary
status: draft
---

# EP-0144: Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval

| Field        | Value                                                                         |
|:-------------|:------------------------------------------------------------------------------|
| **EP**       | 0144                                                                          |
| **Title**    | Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval           |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                         |
| **Sponsor**  | Council of Giants                                                             |
| **Delegate** | Shannon (Semantic Channel Encoding), Russell (Mathematical Logic & Fallbacks) |
| **Status**   | Draft                                                                         |
| **Type**     | Standards Track                                                               |
| **Created**  | 2026-08-30                                                                    |
| **Updated**  | 2026-08-30                                                                    |

---

## Abstract

This proposal integrates **Dense Semantic Vector Embeddings** into Tur's `recall` command, resolving the "vocabulary
mismatch" problem (e.g. searching for "fast" failing to match "performant") while strictly adhering to the **Tur Tur
Principle** (lightweight, minimal dependencies, fast startup). Originating from `EXP-0003`, this EP introduces an
optional `tur[embeddings]` extra powered by the **ONNX Runtime** (`all-MiniLM-L6-v2_onnx_int8`, $\sim 80\text{MB}$
memory footprint) and a pure-Python fallback using `algebrax` sparse vector math, completely avoiding
the $\sim 2\text{GB}$ PyTorch dependency overhead.

---

## Motivation

Currently, `src/tur/recall.py` relies strictly on literal substring matching across markdown bodies and tags before
executing 2-hop graph activation. While fast and deterministic, substring matching suffers from:

1. **Vocabulary Mismatch:** Synonyms and related semantic concepts are missed unless explicitly tagged.
2. **Cold Seed Failure:** If a user query shares zero literal tokens with existing memories, graph spreading activation
   (EP-0103, EP-0136) cannot find starting seed nodes.
3. **The Dependency Dilemma:** Standard embedding libraries (`sentence-transformers`, `torch`)
   add $1.5\text{GB} - 2.5\text{GB}$ of binaries, causing unacceptable CLI cold-start latency.

---

## Rationale

### Alignment with the Council Framework

- **The Shannon Module (Semantic Channel Capacity):** Embeddings map high-dimensional natural language into dense vector
  representations, maximizing semantic retrieval density per token.
- **The Golem Protocol (Substrate Isolation):** Embeddings are computed locally without third-party network calls,
  preserving sovereign isolation and offline autonomy.
- **The Russell Module (Graceful Degradation):** Provides a mathematical multi-tier fallback: `numpy`
  (accelerated) $\to$ `algebrax` (pure-Python sparse dictionary dot products) $\to$ literal BM25 token matching.

---

## Specification

### 1. The Dual-Tier Embedding Engine (`src/tur/embeddings.py`)

```python
from pathlib import Path
from typing import Sequence


class VectorEngine:
    """
    Dual-tier semantic vector similarity engine with zero-dependency fallback.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2_onnx_int8"):
        self.model_name = model_name
        self._session = None

    def embed_text(self, text: str) -> list[float]:
        """Generates embedding vector via ONNX Runtime if installed, or delegates to MCP."""
        try:
            import onnxruntime as ort
            # Run ONNX inference (< 5ms per sentence)
            return self._run_onnx_inference(text)
        except ImportError:
            # Zero-dependency graceful fallback
            return []

    def compute_similarity(self, query_vec: Sequence[float], memory_vecs: Sequence[Sequence[float]]) -> list[float]:
        """Calculates cosine similarity with accelerated numpy or pure AlgebraX fallback."""
        if not query_vec:
            return [0.0] * len(memory_vecs)

        try:
            import numpy as np
            q = np.array(query_vec)
            m = np.array(memory_vecs)
            return (m @ q / (np.linalg.norm(m, axis=1) * np.linalg.norm(q))).tolist()
        except ImportError:
            # Pure Python fallback using AlgebraX dot products
            import algebrax as ax
            return [ax.vector_cosine_similarity(query_vec, mv) for mv in memory_vecs]
```

### 2. OKF Frontmatter Storage & Semantic Drift Detection

Dense vectors are stored directly inside L1 OKF Markdown frontmatter:

```yaml
---
hash: "a1b2c3d4..."
timestamp: "2026-08-30T20:00:00Z"
type: "fact"
scope: "incarnation"
tags: [ "performance", "speed" ]
embedding_model: "all-MiniLM-L6-v2_onnx_int8"
embedding_vector: [ 0.042, -0.198, 0.771, ... ]
---
The compiler uses AST memoization to accelerate rendering.
```

If the configured embedding model version differs from `embedding_model`, Tur marks the memory for lazy background
re-embedding during `introspect` or `wake`.

### 3. Synergistic Seeding with HippoRAG (`EP-0136`)

Vector similarity scores are fed directly into the **Personalized PageRank (PPR)** personalization vector $\mathbf{p}$:

$$p_i = \frac{\text{CosineSim} (\mathbf{q}, \mathbf{v}_i)}{\sum_j \text{CosineSim} (\mathbf{q}, \mathbf{v}_j)}$$

The HippoRAG random walker diffuses from these semantic entrypoints across the L2 knowledge graph.

---

## Backwards Compatibility

- **Optional Packaging:** Embedded vectors are enabled via `pip install tur[embeddings]`, keeping base `tur`
  installation at $< 5\text{MB}$.
- **Fallback Guarantee:** If `onnxruntime` is not installed, `recall` functions transparently via exact keyword matching
  and topological graph spreading.

---

## How to Teach This / Documentation Plan

- Document vector configuration in `docs/concepts/memory-embeddings.md`.
- Explain the `all-MiniLM-L6-v2` ONNX port in release documentation.

---

## Reference Implementation

- Vector engine: `src/tur/embeddings.py`
- Recall integration: `src/tur/recall.py`
- Exploration reference: `references/explorations/EXP-0003-recall-embeddings-and-algebrax/README.md`

---

## Rejected Ideas

- **Bundling PyTorch or full SentenceTransformers:** Rejected due to 2GB+ disk overhead and cold-start latency.
- **External Cloud Embedding APIs in Core:** Rejected to maintain offline autonomy and sovereign state boundaries.

---

## Open Questions

- [ ] Should Tur provide an automated command (`tur-adm memory re-embed`) to backfill vectors when migrating models?

---

## Change Log

* **2026-08-30:**
    * Initial Draft authored based on EXP-0003.
