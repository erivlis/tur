import json
from pathlib import Path

import networkx as nx
import pytest
import yaml

from tur.memory import (
    CognitiveGraphEngine,
    MemoryManager,
    VectorEngine,
    batch_cosine_similarity,
    load_l2_graph_from_okf,
    pure_cosine_similarity,
    save_l2_graph_to_okf,
    topological_recall,
)
from tur.memory.recall import _calculate_seed_scores, _l1_fallback_search
from tur.models import Memory, MemoryScope, MemoryType


def test_pure_cosine_similarity_edge_cases():
    # Identical vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), abs=1e-5) == 1.0

    # Orthogonal vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 0.0], [0.0, 1.0]), abs=1e-5) == 0.0

    # Opposite vectors
    assert pytest.approx(pure_cosine_similarity([1.0, 0.0], [-1.0, 0.0]), abs=1e-5) == -1.0

    # Zero norm vectors
    assert pure_cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    assert pure_cosine_similarity([1.0, 1.0], [0.0, 0.0]) == 0.0

    # Empty or mismatched vectors
    assert pure_cosine_similarity([], [1.0, 2.0]) == 0.0
    assert pure_cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_batch_cosine_similarity():
    q = [1.0, 0.0]
    candidates = [
        [1.0, 0.0],  # identical -> 1.0
        [0.0, 1.0],  # orthogonal -> 0.0
        [-1.0, 0.0],  # opposite -> -1.0
        [0.7071, 0.7071],  # 45 deg -> ~0.7071
    ]
    sims = batch_cosine_similarity(q, candidates)
    assert len(sims) == 4
    assert pytest.approx(sims[0], abs=1e-4) == 1.0
    assert pytest.approx(sims[1], abs=1e-4) == 0.0
    assert pytest.approx(sims[2], abs=1e-4) == -1.0
    assert pytest.approx(sims[3], abs=1e-3) == 0.7071

    # Empty inputs
    assert batch_cosine_similarity([], candidates) == [0.0, 0.0, 0.0, 0.0]
    assert batch_cosine_similarity(q, []) == []


def test_vector_engine_basic_and_drift():
    engine = VectorEngine(model_name='all-MiniLM-L6-v2_onnx_int8')
    assert engine.model_name == 'all-MiniLM-L6-v2_onnx_int8'

    # Graceful fallback when onnxruntime is absent or model path is missing
    assert engine.embed_text('') == []
    assert engine.embed_text('   ') == []
    assert engine.embed_text('Hello world') == []

    # Semantic drift detection
    assert engine.detect_semantic_drift(None) is False
    assert engine.detect_semantic_drift('all-MiniLM-L6-v2_onnx_int8') is False
    assert engine.detect_semantic_drift('all-MiniLM-L6-v1_legacy') is True


def test_okf_l1_frontmatter_embeddings(tmp_path: Path):
    mgr = MemoryManager(base_dir=tmp_path)
    mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        content='Dense semantic vector retrieval uses cosine similarity',
        embedding_model='all-MiniLM-L6-v2_onnx_int8',
        embedding_vector=[0.12, -0.34, 0.56],
    )
    saved_path = mgr.save(mem)
    assert saved_path.exists()

    # Verify reload from OKF disk file
    loaded = mgr.load_all(include_archived=False)
    assert len(loaded) == 1
    assert loaded[0].embedding_model == 'all-MiniLM-L6-v2_onnx_int8'
    assert loaded[0].embedding_vector == [0.12, -0.34, 0.56]


def test_okf_l2_concept_embeddings(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-l2'
    persona_dir.mkdir(parents=True)

    g = nx.DiGraph()
    g.add_node(
        'semantic-search',
        type='Concept',
        content='Semantic search using embeddings',
        confidence=1.0,
        status='active',
        embedding_model='all-MiniLM-L6-v2_onnx_int8',
        embedding_vector=[0.5, 0.5, 0.0],
    )
    save_l2_graph_to_okf(g, persona_dir)

    loaded_g = load_l2_graph_from_okf(persona_dir)
    assert loaded_g is not None
    assert 'semantic-search' in loaded_g
    ndata = loaded_g.nodes['semantic-search']
    assert ndata.get('embedding_model') == 'all-MiniLM-L6-v2_onnx_int8'
    assert ndata.get('embedding_vector') == [0.5, 0.5, 0.0]


def test_hipporag_ppr_vector_personalization_seed():
    """Verify that vector similarity acts as HippoRAG PPR personalization seed even with vocabulary mismatch."""
    g = nx.DiGraph()
    # Node A: storage concept (no keyword match with query 'performant speed')
    g.add_node(
        'fast-cache',
        type='Concept',
        content='AST caching mechanism for compiler',
        confidence=1.0,
        status='active',
        embedding_vector=[1.0, 0.0, 0.0],
    )
    # Node B: network routing concept
    g.add_node(
        'mesh-routing',
        type='Concept',
        content='Mesh topology packet forwarding',
        confidence=1.0,
        status='active',
        embedding_vector=[0.0, 1.0, 0.0],
    )
    g.add_edge('fast-cache', 'mesh-routing', weight=1.0)

    # Query 'throughput optimization' has 0 lexical overlap with 'AST caching mechanism for compiler'
    # but query_vector is aligned with fast-cache
    query = 'throughput optimization'
    query_vec = [0.95, 0.05, 0.0]

    engine = CognitiveGraphEngine(g)
    seed_scores = engine.calculate_seed_scores(query, query_vector=query_vec)

    assert 'fast-cache' in seed_scores
    assert seed_scores['fast-cache'] > seed_scores.get('mesh-routing', 0.0)

    # Run HippoRAG associative PPR
    ranked = engine.associative_ppr_recall(seed_scores=seed_scores, alpha=0.15, top_k=2)
    assert len(ranked) >= 1
    assert ranked[0][0] == 'fast-cache'


def test_topological_recall_with_vector_seeding(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-vector-recall'
    persona_dir.mkdir(parents=True)

    g = nx.DiGraph()
    g.add_node(
        'vector-store',
        type='Concept',
        content='In-memory vector store for fast neighbor lookup',
        confidence=1.0,
        status='active',
        embedding_vector=[1.0, 0.0],
    )
    g.add_node(
        'sql-database',
        type='Concept',
        content='Relational SQLite tables',
        confidence=1.0,
        status='active',
        embedding_vector=[0.0, 1.0],
    )
    g.add_edge('vector-store', 'sql-database', type='depends_on')

    with open(persona_dir / 'knowledge_graph.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(nx.node_link_data(g), f)

    # Query with zero lexical match, but query_vector aligned with vector-store
    res = topological_recall(
        query='unmatched_lexical_token',
        persona_dir=persona_dir,
        effort=5,
        query_vector=[0.9, 0.1],
    )
    parsed = json.loads(res)
    assert len(parsed) > 0
    assert parsed[0]['id'] == 'vector-store'


def test_l1_fallback_search_with_vector(tmp_path: Path):
    persona_dir = tmp_path / 'personas' / 'p-l1-fallback'
    persona_dir.mkdir(parents=True)

    mgr = MemoryManager(base_dir=persona_dir)
    mgr.save(
        Memory(
            type=MemoryType.FACT,
            scope=MemoryScope.INCARNATION,
            content='Persistent disk indexing with zero runtime dependencies',
            embedding_vector=[0.8, 0.2],
        )
    )

    # Query with zero lexical match but matching query_vector
    res = _l1_fallback_search('completely_foreign_token', persona_dir, query_vector=[0.8, 0.2])
    assert 'No memories found' not in res
    parsed = json.loads(res)
    assert len(parsed) == 1
    assert 'Persistent disk indexing' in parsed[0]['content']


def test_vector_engine_real_tokenization_and_inference(tmp_path: Path):
    """Verifies that input text is genuinely tokenized, passed to ONNX, mean-pooled, and L2 normalized."""
    import numpy as np
    from tokenizers import Tokenizer, models, pre_tokenizers

    # 1. Create a real tokenizer and save to tmp_path / 'tokenizer.json'
    vocab = {'[PAD]': 0, '[UNK]': 1, '[CLS]': 2, '[SEP]': 3, 'hello': 4, 'world': 5, 'tur': 6}
    tok = Tokenizer(models.WordPiece(vocab=vocab, unk_token='[UNK]'))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.enable_padding(pad_id=0, pad_token='[PAD]')
    tok.enable_truncation(max_length=512)

    tok_path = tmp_path / 'tokenizer.json'
    tok.save(str(tok_path))

    # 2. Mock ONNX input meta and InferenceSession
    class MockInputMeta:
        def __init__(self, name: str):
            self.name = name

    captured_inputs: list[dict] = []

    class MockSession:
        def get_inputs(self):
            return [MockInputMeta('input_ids'), MockInputMeta('attention_mask'), MockInputMeta('token_type_ids')]

        def run(self, output_names, onnx_inputs):
            captured_inputs.append(onnx_inputs)
            # Produce distinct embeddings for tokens
            # Shape: (1, seq_len, 4)
            seq_len = onnx_inputs['input_ids'].shape[1]
            # Give token 4 a distinct embedding from token 5
            embeddings = np.ones((1, seq_len, 4), dtype=np.float32)
            return [embeddings]

    engine = VectorEngine(
        model_name='all-MiniLM-L6-v2_onnx_int8',
        model_path=tmp_path / 'dummy_model.onnx',
        tokenizer_path=tok_path,
    )
    engine._session = MockSession()

    # 3. Test embedding generation
    vec = engine.embed_text('hello world')
    assert len(vec) == 4
    # Verify input_ids received by session correspond to 'hello' (4) and 'world' (5)
    assert len(captured_inputs) == 1
    passed_ids = captured_inputs[0]['input_ids'][0].tolist()
    assert passed_ids == [4, 5]

    # Verify L2 normalization (length == 1.0)
    norm = np.linalg.norm(vec)
    assert pytest.approx(norm, abs=1e-5) == 1.0

    # 4. Verify different text yields different token inputs
    vec2 = engine.embed_text('tur')
    assert len(vec2) == 4
    assert len(captured_inputs) == 2
    assert captured_inputs[1]['input_ids'][0].tolist() == [6]


def test_vector_engine_fallback_modes(tmp_path: Path, monkeypatch):
    """Verifies graceful degradation when onnxruntime or tokenizers are unavailable."""
    engine = VectorEngine(model_name='all-MiniLM-L6-v2_onnx_int8', model_path=tmp_path / 'dummy.onnx')

    # Without tokenizer or session
    assert engine.embed_text('test text') == []

    # With monkeypatched flags
    monkeypatch.setattr(VectorEngine, 'is_onnx_available', property(lambda self: False))
    assert engine.embed_text('test text') == []

    monkeypatch.setattr(VectorEngine, 'is_onnx_available', property(lambda self: True))
    monkeypatch.setattr(VectorEngine, 'is_tokenizers_available', property(lambda self: False))
    assert engine.embed_text('test text') == []


def test_vector_engine_directory_tokenizer_resolution(tmp_path: Path):
    """Verifies tokenizer.json resolution adjacent to model_path or inside model directory."""
    from tokenizers import Tokenizer, models

    vocab = {'[PAD]': 0, '[UNK]': 1}
    tok = Tokenizer(models.WordPiece(vocab=vocab, unk_token='[UNK]'))
    tok_path = tmp_path / 'tokenizer.json'
    tok.save(str(tok_path))

    # Test 1: model_path is a directory containing tokenizer.json
    engine_dir = VectorEngine(model_path=tmp_path)
    loaded_tok = engine_dir._get_tokenizer()
    assert loaded_tok is not None

    # Test 2: model_path is a file in the directory
    engine_file = VectorEngine(model_path=tmp_path / 'model.onnx')
    loaded_tok2 = engine_file._get_tokenizer()
    assert loaded_tok2 is not None


def test_vector_engine_hardware_acceleration_defaults_and_env(monkeypatch):
    """Verifies opt-in hardware acceleration behavior, provider resolution, and environment triggers."""
    import onnxruntime as ort

    # Default is always strictly CPUExecutionProvider
    engine_default = VectorEngine()
    assert engine_default.accelerate is False
    assert engine_default._resolve_providers() == ['CPUExecutionProvider']

    # Explicit providers list overrides everything
    engine_custom = VectorEngine(providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
    assert engine_custom._resolve_providers() == ['DmlExecutionProvider', 'CPUExecutionProvider']

    # Opt-in acceleration via accelerate=True queries available providers and appends CPU fallback
    monkeypatch.setattr(ort, 'get_available_providers', lambda: ['CUDAExecutionProvider', 'CPUExecutionProvider'])
    engine_accel = VectorEngine(accelerate=True)
    assert engine_accel.accelerate is True
    assert engine_accel._resolve_providers() == ['CUDAExecutionProvider', 'CPUExecutionProvider']

    # Ensure CPU fallback is appended if missing from available
    monkeypatch.setattr(ort, 'get_available_providers', lambda: ['CoreMLExecutionProvider'])
    engine_coreml = VectorEngine(accelerate=True)
    assert engine_coreml._resolve_providers() == ['CoreMLExecutionProvider', 'CPUExecutionProvider']

    # Opt-in via TUR_EMBEDDING_ACCELERATE environment variable
    monkeypatch.setenv('TUR_EMBEDDING_ACCELERATE', '1')
    engine_env = VectorEngine()
    assert engine_env.accelerate is True


def test_vector_engine_accelerator_fallback_on_session_error(tmp_path: Path, monkeypatch):
    """Verifies that if an accelerator provider fails to initialize, VectorEngine falls back to pure CPU."""
    import onnxruntime as ort

    model_file = tmp_path / 'dummy.onnx'
    model_file.write_text('dummy onnx bytes')

    sessions_created = []

    class MockSession:
        def __init__(self, path, sess_options=None, providers=None):
            sessions_created.append(providers)
            if providers and 'CUDAExecutionProvider' in providers:
                raise RuntimeError('CUDA driver initialization failed')
            self.providers = providers

    monkeypatch.setattr(ort, 'InferenceSession', MockSession)

    engine = VectorEngine(
        model_path=model_file,
        accelerate=True,
        providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
    )
    session = engine._get_session()
    assert session is not None
    # Verified that it first attempted CUDA, failed, and fell back to CPUExecutionProvider
    assert len(sessions_created) == 2
    assert sessions_created[0] == ['CUDAExecutionProvider', 'CPUExecutionProvider']
    assert sessions_created[1] == ['CPUExecutionProvider']
