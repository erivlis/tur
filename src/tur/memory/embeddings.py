"""src/tur/memory/embeddings.py - Zero-Dependency Dense Semantic Embeddings and ONNX Vector Retrieval.

Provides multi-tier vector generation and cosine similarity calculation:
1. Generation: ONNX Runtime (all-MiniLM-L6-v2_onnx_int8) when installed, or graceful fallback.
2. Similarity Math: NumPy vectorized dot-products -> pure-Python / AlgebraX sparse cosine fallback.
"""

from __future__ import annotations

import importlib.util
import math
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

DEFAULT_EMBEDDING_MODEL = 'all-MiniLM-L6-v2_onnx_int8'

RECOMMENDED_MODELS: dict[str, dict[str, Any]] = {
    'minilm': {
        'id': 'all-MiniLM-L6-v2',
        'repo': 'Xenova/all-MiniLM-L6-v2',
        'dim': 384,
        'size_mb': 22.8,
        'files': ['onnx/model_quantized.onnx', 'tokenizer.json'],
    },
    'bge-small': {
        'id': 'bge-small-en-v1.5',
        'repo': 'Xenova/bge-small-en-v1.5',
        'dim': 384,
        'size_mb': 32.6,
        'files': ['onnx/model_quantized.onnx', 'tokenizer.json'],
    },
    'e5-small': {
        'id': 'e5-small-v2',
        'repo': 'Xenova/e5-small-v2',
        'dim': 384,
        'size_mb': 32.6,
        'files': ['onnx/model_quantized.onnx', 'tokenizer.json'],
    },
}

MODEL_ALIASES: dict[str, str] = {
    'minilm': 'all-MiniLM-L6-v2',
    'all-minilm-l6-v2': 'all-MiniLM-L6-v2',
    'all-minilm-l6-v2_onnx_int8': 'all-MiniLM-L6-v2',
    'bge-small': 'bge-small-en-v1.5',
    'bge-small-en-v1.5': 'bge-small-en-v1.5',
    'e5-small': 'e5-small-v2',
    'e5-small-v2': 'e5-small-v2',
}


def is_model_compatible(candidate_model: str | None, active_model: str | None) -> bool:
    """Verifies whether a candidate vector's embedding model matches the active model.

    Enforces the Strict Vector Space Homogeneity Invariant.
    If candidate_model is None (legacy or test fixture), it is allowed to prevent breakage.
    If both candidate_model and active_model are specified, their canonical IDs must match.
    """
    if not candidate_model or not active_model or candidate_model == active_model:
        return True
    cand_low = candidate_model.lower()
    act_low = active_model.lower()
    if cand_low == act_low:
        return True
    return MODEL_ALIASES.get(cand_low, cand_low) == MODEL_ALIASES.get(act_low, act_low)


def pure_cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Computes cosine similarity between two dense or sparse vector sequences in pure Python.

    Zero external dependencies. Runs in O(D).
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vec_a, vec_b, strict=False):
        dot_product += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0

    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))


def batch_cosine_similarity(
    query_vec: Sequence[float],
    matrix_vecs: Sequence[Sequence[float]],
) -> list[float]:
    """Calculates cosine similarity of a query vector against a matrix of candidate vectors.

    Uses NumPy vectorized matrix math if installed; otherwise falls back to pure Python / AlgebraX.
    """
    if not query_vec or not matrix_vecs:
        return [0.0] * len(matrix_vecs)

    try:
        import numpy as np

        q = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return [0.0] * len(matrix_vecs)

        m = np.array(matrix_vecs, dtype=np.float32)
        m_norm = np.linalg.norm(m, axis=1)
        # Avoid division by zero
        m_norm[m_norm == 0] = 1e-9

        dots = m @ q
        similarities = dots / (m_norm * q_norm)
        return similarities.tolist()
    except ImportError:
        pass

    # Pure Python fallback
    return [pure_cosine_similarity(query_vec, mv) for mv in matrix_vecs]


class VectorEngine:
    """Dual-tier semantic vector similarity engine with zero-dependency fallback."""

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
            os.environ.get('TUR_EMBEDDING_ACCELERATE', '0').lower() in ('1', 'true', 'yes')
        )
        self.providers = list(providers) if providers is not None else None
        self._session: Any = None
        self._tokenizer: Any = None

        if self.model_path is None:
            self._auto_discover_model()

    def _auto_discover_model(self) -> None:
        """Auto-discovers model and tokenizer from ~/.tur/models."""
        from tur.paths import resolve_models_dir

        candidates = [self.model_name]
        canonical = MODEL_ALIASES.get(self.model_name.lower())
        if canonical and canonical not in candidates:
            candidates.append(canonical)
        for alias, rec in RECOMMENDED_MODELS.items():
            if self.model_name.lower() in (alias, rec['id'].lower()) and rec['id'] not in candidates:
                candidates.append(rec['id'])

        for cand in candidates:
            cand_dir = resolve_models_dir(cand)
            if cand_dir.exists() and cand_dir.is_dir():
                for m_file in ('model_quantized.onnx', 'model.onnx', f'{cand}.onnx'):
                    cand_file = cand_dir / m_file
                    if cand_file.exists():
                        self.model_path = cand_file
                        if self.tokenizer_path is None and (cand_dir / 'tokenizer.json').exists():
                            self.tokenizer_path = cand_dir / 'tokenizer.json'
                        return

    @property
    def is_onnx_available(self) -> bool:
        """Returns True if onnxruntime is installed and available."""
        return importlib.util.find_spec('onnxruntime') is not None

    @property
    def is_tokenizers_available(self) -> bool:
        """Returns True if tokenizers is installed and available."""
        return importlib.util.find_spec('tokenizers') is not None

    def _resolve_providers(self) -> list[str]:
        """Resolves execution providers for ONNX InferenceSession.

        Defaults strictly to ['CPUExecutionProvider'] for lean, predictable, low-latency execution.
        Hardware acceleration (CUDA, DirectML, CoreML, OpenVINO, ROCm) is engaged only when
        explicitly requested via accelerate=True, providers=[...], or $TUR_EMBEDDING_ACCELERATE=1.
        """
        if self.providers:
            return list(self.providers)

        if not self.accelerate:
            return ['CPUExecutionProvider']

        try:
            import onnxruntime as ort

            available = ort.get_available_providers()
            # Guarantee CPU fallback is always present at the end
            if 'CPUExecutionProvider' not in available:
                available.append('CPUExecutionProvider')
        except Exception:
            return ['CPUExecutionProvider']
        else:
            return available

    def _get_tokenizer(self) -> Any:
        """Resolves and caches the tokenizer instance."""
        if self._tokenizer is not None:
            return self._tokenizer

        if not self.is_tokenizers_available:
            return None

        tok_path = self.tokenizer_path
        if not tok_path and (candidate := self.model_path):
            if not candidate.is_dir():
                candidate = candidate.parent
            candidate = candidate / 'tokenizer.json'
            if candidate.exists():
                tok_path = candidate

        if tok_path and Path(tok_path).exists():
            try:
                from tokenizers import Tokenizer

                tok = Tokenizer.from_file(str(tok_path))
                tok.enable_padding(pad_id=0, pad_token='[PAD]')
                tok.enable_truncation(max_length=512)
                self._tokenizer = tok
            except Exception:
                return None
            else:
                return self._tokenizer

        return None

    def _get_session(self) -> Any:
        """Resolves and caches the ONNX InferenceSession."""
        if self._session is not None:
            return self._session

        if not self.is_onnx_available or not self.model_path:
            return None

        resolved_path = self.model_path
        if resolved_path.is_dir():
            for name in ('model.onnx', 'model_quantized.onnx', f'{self.model_name}.onnx'):
                cand = resolved_path / name
                if cand.exists():
                    resolved_path = cand
                    break

        if not resolved_path.exists() or resolved_path.is_dir():
            return None

        try:
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 1
            opts.inter_op_num_threads = 1
            providers = self._resolve_providers()
            try:
                self._session = ort.InferenceSession(
                    str(resolved_path),
                    sess_options=opts,
                    providers=providers,
                )
            except Exception:
                # If accelerator initialization failed (e.g. driver mismatch), fall back to CPU
                if providers != ['CPUExecutionProvider']:
                    self._session = ort.InferenceSession(
                        str(resolved_path),
                        sess_options=opts,
                        providers=['CPUExecutionProvider'],
                    )
                else:
                    return None
        except Exception:
            return None
        else:
            return self._session

    def embed_text(self, text: str) -> list[float]:
        """Generates embedding vector via ONNX Runtime and tokenizers if available, or returns empty list fallback."""
        if not text or not text.strip():
            return []

        tokenizer = self._get_tokenizer()
        session = self._get_session()

        if tokenizer is None or session is None:
            return []

        try:
            import numpy as np

            encoded = tokenizer.encode(text)
            input_ids = np.array([encoded.ids], dtype=np.int64)
            attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
            token_type_ids = np.array([encoded.type_ids], dtype=np.int64)

            onnx_inputs: dict[str, Any] = {}
            for input_meta in session.get_inputs():
                if input_meta.name == 'input_ids':
                    onnx_inputs['input_ids'] = input_ids
                elif input_meta.name == 'attention_mask':
                    onnx_inputs['attention_mask'] = attention_mask
                elif input_meta.name == 'token_type_ids':
                    onnx_inputs['token_type_ids'] = token_type_ids

            outputs = session.run(None, onnx_inputs)
            token_embeddings = outputs[0]

            if len(token_embeddings.shape) == 3:
                input_mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
                sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
                sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
                embedding = (sum_embeddings / sum_mask)[0]
            elif len(token_embeddings.shape) == 2:
                embedding = token_embeddings[0]
            else:
                embedding = token_embeddings.flatten()

            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return [float(x) for x in embedding]
        except Exception:
            return []

    def compute_similarity(
        self,
        query_vec: Sequence[float],
        candidate_vecs: Sequence[Sequence[float]],
    ) -> list[float]:
        """Calculates similarity scores using accelerated NumPy or pure Python fallback."""
        return batch_cosine_similarity(query_vec, candidate_vecs)

    def detect_semantic_drift(
        self,
        stored_model: str | None,
    ) -> bool:
        """Returns True if a memory's embedding vector was generated with a different model version."""
        if not stored_model:
            return False
        return stored_model != self.model_name
