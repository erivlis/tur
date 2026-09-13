---
title: "EP-0144: Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval"
description: "Introduces zero-dependency dense semantic embedding retrieval via ONNX runtime and AlgebraX sparse cosine math, solving the vocabulary mismatch problem without PyTorch dependency bloat."
icon: lucide/binary
status: implemented
---

# EP-0144: Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval

| Field        | Value                                                                            |
|:-------------|:---------------------------------------------------------------------------------|
| **EP**       | 0144                                                                             |
| **Title**    | Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval              |
| **Author**   | Eran Rivlis, Ariel                                                               |
| **Sponsor**  | Council of Giants                                                                |
| **Delegate** | Shannon (Semantic Channel Encoding), Russell (Mathematical Logic & Fallbacks)    |
| **Status**   | Implemented                                                                      |
| **Type**     | Standards Track                                                                  |
| **Created**  | 2026-08-30                                                                       |
| **Updated**  | 2026-09-14                                                                       |
| **Review**   | [REV-0007](../reviews/REV-0007-EP-0144-council-review.md) (Unanimously Approved) |

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

### 1. The Dual-Tier Embedding Engine (`src/tur/memory/embeddings.py`)

```python
import importlib.util
from pathlib import Path
from typing import Any, Sequence

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2_onnx_int8"


class VectorEngine:
    """
    Dual-tier semantic vector similarity engine with zero-dependency fallback.
    """

    def __init__(
            self,
            model_name: str = DEFAULT_EMBEDDING_MODEL,
            model_path: Path | None = None,
            tokenizer_path: Path | None = None,
            accelerate: bool = False,
            providers: Sequence[str] | None = None,
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        self.accelerate = accelerate or (
                os.environ.get("TUR_EMBEDDING_ACCELERATE", "0").lower() in ("1", "true", "yes")
        )
        self.providers = list(providers) if providers is not None else None
        self._session: Any = None
        self._tokenizer: Any = None

    @property
    def is_onnx_available(self) -> bool:
        """Sub-millisecond probe without eager DLL loading."""
        return importlib.util.find_spec("onnxruntime") is not None

    @property
    def is_tokenizers_available(self) -> bool:
        """Sub-millisecond probe without eager library initialization."""
        return importlib.util.find_spec("tokenizers") is not None

    def _resolve_providers(self) -> list[str]:
        """Defaults strictly to CPU for lean predictability; opt-in for CUDA, DirectML, CoreML."""
        if self.providers:
            return list(self.providers)
        if not self.accelerate:
            return ["CPUExecutionProvider"]
        try:
            import onnxruntime as ort

            available = ort.get_available_providers()
            if "CPUExecutionProvider" not in available:
                available.append("CPUExecutionProvider")
            return available
        except Exception:
            return ["CPUExecutionProvider"]

    def embed_text(self, text: str) -> list[float]:
        """4-step pipeline: WordPiece tokenization -> ONNX execution -> Masked Mean Pooling -> L2 Norm."""
        if not text or not text.strip():
            return []
        tokenizer = self._get_tokenizer()
        session = self._get_session()
        if tokenizer is None or session is None:
            return []

        import numpy as np

        encoded = tokenizer.encode(text)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)

        onnx_inputs = {
            m.name: val
            for m, val in [
                ("input_ids", input_ids),
                ("attention_mask", attention_mask),
                ("token_type_ids", token_type_ids),
            ]
            if m in [inp.name for inp in session.get_inputs()]
        }
        outputs = session.run(None, onnx_inputs)
        token_embeddings = outputs[0]

        # Masked mean pooling
        input_mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embedding = (sum_embeddings / sum_mask)[0]

        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return [float(x) for x in embedding]
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

### 4. Administrative Asset Lifecycle, Model Migration & Zero-Config Discovery

To decouple low-privilege agent runtimes (`tur`) from network I/O and heavy asset fetching while providing
zero-configuration developer ergonomics, model management is anchored in the administrative governor CLI (`tur-adm`) per
EP-0116.

#### Recommended Embedding Models Registry

| Alias                          | Full Hugging Face Repo ID             | Quantized Size | Dims | Best For                                                 |
|:-------------------------------|:--------------------------------------|:--------------:|:----:|:---------------------------------------------------------|
| `minilm` / `all-minilm-l6-v2`  | `Xenova/all-MiniLM-L6-v2` *(Default)* |     ~22 MB     | 384  | Fastest cold-start, lowest memory, ~2–4ms CPU inference. |
| `bge-small`                    | `Xenova/bge-small-en-v1.5`            |     ~33 MB     | 384  | Highest retrieval accuracy on MTEB benchmarks.           |
| `e5-small` / `multilingual-e5` | `Xenova/multilingual-e5-small`        |     ~45 MB     | 384  | Multilingual codebases (100+ languages).                 |

#### Directory Hierarchy & Zero-Config Auto-Discovery

Models are cached centrally under the global user state directory (`~/.tur/models/`, resolved via
`paths.resolve_models_dir` conforming to EP-0128):

```
~/.tur/models/
├── all-MiniLM-L6-v2/
│   ├── model_quantized.onnx
│   └── tokenizer.json
└── bge-small-en-v1.5/
    ├── model_quantized.onnx
    └── tokenizer.json
```

When `VectorEngine` is initialized with `model_path=None`, it automatically queries
`paths.resolve_models_dir(self.model_name)`. If the quantized ONNX graph and `tokenizer.json` exist, it binds them
seamlessly without requiring environment variables or explicit path arguments.

#### Idempotent Model Migration (`tur-adm memory embed`)

Because embeddings from differing models project into incommensurable geometric spaces, comparing vectors across
different model versions produces mathematical noise. To guarantee safe migrations:

1. **Zero-Poisoning Query Isolation (`recall.py`):**
   During vector retrieval, candidate vectors are strictly validated against `engine.model_name`. If a memory was
   embedded under an older or different model, its vector is filtered out, and the memory gracefully matches via
   literal/BM25 lexical scoring, preventing cross-model index pollution.

2. **Idempotent Batch Re-Embedding (`tur-adm memory embed`):**
   The administrative CLI provides a declarative, idempotent command to align all memories to the target model:
    - **Skip Rule:** If a memory already contains an embedding generated by the target model
      (`embedding_model == target_model`), it is **strictly ignored and skipped**, incurring zero compute cost.
    - **Update Rule:** If a memory lacks a vector or exhibits semantic drift (`embedding_model != target_model`), its
      text is embedded and its OKF frontmatter is updated in place.
    - **Forced Override:** Passing `--force` re-embeds all memories unconditionally.

#### Command Taxonomy (`tur-adm model` & `tur-adm memory`)

| Command                        | Arguments / Flags                        | Description                                                                                                     |
|:-------------------------------|:-----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
| `tur-adm model pull [MODEL]`   | `[--force]`                              | Download quantized ONNX weights and `tokenizer.json` from Hugging Face with progress tracking.                  |
| `tur-adm model list`           | `[--json]`                               | Display downloaded local models and available recommended registry models.                                      |
| `tur-adm model status`         | `[--json]`                               | Report active ONNX execution providers, tokenizer status, and current active embedding model.                   |
| `tur-adm model remove <MODEL>` | `[--all]`                                | Delete cached model assets from `~/.tur/models/` to reclaim disk space.                                         |
| `tur-adm memory embed [ID]`    | `[--model <m>] [--force] [--accelerate]` | Idempotently embed or migrate all L1/L2 memories to the target model space, skipping existing valid embeddings. |

---

## Backwards Compatibility

- **Optional Packaging:** Embedded vectors are enabled via `pip install tur[embeddings]`, which bundles `onnxruntime`,
  `tokenizers`, and `numpy`, keeping base `tur` installation at $< 5\text{MB}$.
- **Fallback Guarantee:** If `onnxruntime` or `tokenizers` is not installed, `recall` functions transparently via exact
  keyword matching
  and topological graph spreading.
- **Predictable Execution & Opt-In Acceleration:** By default, inference executes strictly on CPU
  (`CPUExecutionProvider`)
  to ensure sub-3ms cold-start latency and avoid GPU driver conflicts. Hardware acceleration (CUDA, DirectML, CoreML) is
  strictly
  opt-in via `accelerate=True`, explicit `providers=[...]`, or `$TUR_EMBEDDING_ACCELERATE=1`, with automatic fallback to
  pure CPU
  if accelerator initialization fails.

---

## How to Teach This / Documentation Plan

Documentation will be structured around two distinct operational paths in `docs/concepts/memory-embeddings.md` and user
guides:

### Path A: The Automated Administrator Workflow (`tur-adm`)

Recommended for 90% of developers and operators:

1. **Install Embeddings Extra:**
   ```bash
   pip install "tur[embeddings,admin]"
   ```
2. **Download Model Assets:**
   ```bash
   tur-adm model pull minilm
   ```
   Fetches `model_quantized.onnx` and `tokenizer.json` to `~/.tur/models/all-MiniLM-L6-v2/` with progress telemetry.
3. **Inspect Hardware & Model Status:**
   ```bash
   tur-adm model status
   ```
   Displays active execution providers (CPU, DirectML, CUDA), tokenizer health, and current model.
4. **Idempotently Embed Existing Memories:**
   ```bash
   tur-adm memory embed
   ```
   Scans the Memory Bank, skips already-embedded memories, and encodes any un-embedded or drifted memories into OKF
   frontmatter.
5. **Agent Zero-Config Autonomy:**
   Agents running `tur recall <query>` automatically utilize the local ONNX model with zero flags or configuration.

### Path B: Advanced Hardware Providers & Air-Gapped Manual Setup

For power users, air-gapped secure enclaves, and specialized GPU/NPU hardware:

1. **Selecting and Installing Hardware Acceleration Packages:**
    - **NVIDIA CUDA:** `pip install onnxruntime-gpu` (requires compatible CUDA Toolkit / cuDNN).
    - **Windows DirectX 12 (NVIDIA, AMD, Intel):** `pip install onnxruntime-directml` (zero driver setup beyond modern
      graphics drivers).
    - **Apple Silicon (M1–M4):** Standard `onnxruntime` includes built-in `CoreMLExecutionProvider`.
    - **Intel NPU/iGPU:** `pip install onnxruntime-openvino`.
2. **Air-Gapped & Custom Model Sourcing:**
    - Users in offline environments can manually copy any INT8-quantized BERT/Transformer ONNX model and
      `tokenizer.json` into:
      ```
      ~/.tur/models/<custom_model_id>/
      ├── model_quantized.onnx
      └── tokenizer.json
      ```

### Path C: Model Tiers, Evolution & The Homogeneity Invariant

To prevent cognitive confusion and architectural anti-patterns, documentation must explicitly address model selection
and migration:

1. **The Invariant: Strict Vector Space Homogeneity:**
    - Documentation must explain why **simultaneous multi-model embedding within a single memory bank is strictly
      prohibited**. Vectors from different models (even with identical dimensions) occupy incommensurable geometric
      spaces; computing cosine similarity between them produces random mathematical noise.
    - Clarify why a secondary cross-encoder reranker model is unnecessary in Tur: **the L2 Knowledge Graph itself is the
      reranker**. HippoRAG Personalized PageRank diffuses semantic energy across structural edges (`depends_on`,
      `refines`), providing topological reranking superior to flat vector search without model bloat.

2. **Tiered Selection Architecture:**
    - **Tier 1 (Agile Default):** `all-MiniLM-L6-v2` on CPU (~22 MB INT8, 384-dim, < 3ms cold start). Recommended for
      standard agent development, laptop battery efficiency, and routine engineering workflows.
    - **Tier 2 (High-Capacity Lab):** `bge-base-en-v1.5` or `nomic-embed-text-v1.5` with DirectML/CUDA GPU acceleration
      (768-dim, up to 8,192 tokens). Recommended for large monorepos, extensive architectural documentation, and
      workstation/server deployments.

3. **Graduating Between Tiers (Step-by-Step Migration Scenario):**
   Provide a concrete walkthrough for projects upgrading their embedding space:
   ```bash
   # 1. Download the higher-capacity model
   tur-adm model pull bge-base

   # 2. Idempotently migrate all existing memories in an accelerated batch
   tur-adm memory embed --model bge-base --accelerate

   # 3. Verify cryptographic integrity and alignment
   tur-adm memory verify
   ```
   Highlight that during the migration window, **Zero-Poisoning Query Isolation** ensures un-migrated memories safely
   fall back to lexical BM25 matching rather than corrupting vector similarity scores.

---

## Reference Implementation

- Vector engine: `src/tur/memory/embeddings.py`
- Recall integration: `src/tur/memory/recall.py`
- Administrative model management: `src/tur/cli/admin.py`
- Exploration reference: `references/explorations/EXP-0003-recall-embeddings-and-algebrax/README.md`

---

## Rejected Ideas

- **Bundling PyTorch or full SentenceTransformers:** Rejected due to 2GB+ disk overhead and cold-start latency.
- **External Cloud Embedding APIs in Core:** Rejected to maintain offline autonomy and sovereign state boundaries.
- **Eager Default GPU Execution:** Rejected because cold-start CUDA context initialization and VRAM allocation introduce
  unacceptable latency and instability for routine single-line CLI queries.
- **Agent-Side Model Downloading:** Rejected per EP-0116; autonomous low-privilege `tur` agents must not perform
  untracked multi-megabyte binary downloads during routine reasoning turns.
- **Simultaneous Multi-Model Embedding in a Single Store:** Rejected because incommensurable vector spaces produce
  undefined cosine similarities, double OKF frontmatter storage overhead, and distort HippoRAG graph personalization
  distributions.

---

## Open Questions

- [x] Resolved: Automated model migration and backfilling codified via declarative `tur-adm memory embed` with
  idempotent skip semantics.

---

## Change Log

* **2026-09-14:**
    * Completed full implementation and verification of the administrative model lifecycle (`tur-adm model pull`,
      `tur-adm model list`, `tur-adm model status`, `tur-adm model remove`) and idempotent memory embedding migration
      (`tur-adm memory embed`) in `src/tur/cli/admin.py`.
    * Implemented centralized model directory resolution (`resolve_models_dir`) in `src/tur/paths.py` and automatic
      model/tokenizer discovery in `VectorEngine`.
    * Enforced the Strict Vector Space Homogeneity Invariant with zero-poisoning query isolation in
      `src/tur/memory/recall.py`, guaranteeing that deprecated or alien vectors safely fall back to lexical BM25 matching.
    * Added 8 comprehensive unit tests in `tests/test_model_and_embed.py` (all passing).
    * Reviewed and unanimously ratified by the Council of Giants in [REV-0007](../reviews/REV-0007-EP-0144-council-review.md).
* **2026-09-13:**
    * Added Section 4: "Administrative Asset Lifecycle, Model Migration & Zero-Config Discovery" codifying the
      recommended models registry (`minilm`, `bge-small`, `e5-small`), central caching in `~/.tur/models/`, zero-config
      `VectorEngine` auto-discovery, zero-poisoning query isolation in `recall.py`, and the administrative commands
      `tur-adm model` and `tur-adm memory embed`.
    * Added `tokenizers>=0.19.0` to `[embeddings]` extra and implemented the complete 4-step Transformer pipeline in
      `VectorEngine` (WordPiece tokenization, dynamic ONNX graph input binding, masked mean pooling, and L2
      normalization).
    * Upgraded availability detection to `importlib.util.find_spec` for sub-millisecond capability probes without eager
      C-extension/DLL execution.
    * Codified explicit opt-in hardware acceleration (`accelerate=True`, `providers=[...]`,
      `$TUR_EMBEDDING_ACCELERATE=1`), defaulting strictly to CPU for lean predictability, with automatic CPU fallback on
      initialization error.
    * Added 5 new unit tests in `tests/test_embeddings.py` covering real tokenization, masked mean pooling, adjacent
      directory tokenizer resolution, opt-in acceleration, and accelerator fallback (13/13 passing).
* **2026-09-09:**
    * Completed full implementation and verification: integrated `VectorEngine` with ONNX runtime and pure-Python cosine
      similarity into HippoRAG Personalized PageRank (`recall.py`), added OKF frontmatter embedding fields to
      `models.py` and `storage.py`, added optional `[embeddings]` extra to `pyproject.toml`, and verified 100% test pass
      rate with 8 new unit tests in `tests/test_embeddings.py` (401/401 passing).
* **2026-08-30:**
    * Initial Draft authored based on EXP-0003.
