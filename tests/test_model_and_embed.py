import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from tur.cli.admin import app as admin_app
from tur.memory.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    MODEL_ALIASES,
    RECOMMENDED_MODELS,
    VectorEngine,
    is_model_compatible,
)
from tur.memory.recall import _augment_scores_with_vector_similarity, _l1_fallback_search
from tur.memory.storage import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType
from tur.paths import resolve_models_dir

runner = CliRunner()


@pytest.fixture
def mock_admin_env(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    personas_dir = dot_tur / 'personas'
    personas_dir.mkdir()

    persona_id = '7544202e-92f5-40ce-adfb-e4b0eae6c262'
    index_data = {'personas': [{'id': persona_id, 'name': 'Ariel', 'version': '5.4.0'}]}
    with open(dot_tur / 'personas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f)

    p_dir = personas_dir / persona_id
    (p_dir / 'memories' / 'archive').mkdir(parents=True)
    with open(p_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'name': 'Ariel', 'version': '5.4.0', 'model': 'test'}, f)

    state_data = {'active_persona_id': persona_id}
    with open(dot_tur / 'state.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('TUR_PROJECT_DIR', str(tmp_path))

    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    class StdoutProxy:
        def __getattr__(self, attr):
            if attr == 'isatty':
                return lambda: True
            return getattr(sys.stdout, attr)

    class SysProxy:
        def __getattr__(self, name):
            if name == 'stdout':
                return StdoutProxy()
            return getattr(sys, name)

    import tur.cli.common

    monkeypatch.setattr(tur.cli.common, 'sys', SysProxy())

    return tmp_path, persona_id, p_dir, fake_home


def test_resolve_models_dir(tmp_path, monkeypatch):
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)
    monkeypatch.delenv('TUR_DATA_DIR', raising=False)
    monkeypatch.delenv('TUR_HOME', raising=False)

    base = resolve_models_dir()
    assert base == (fake_home / '.tur' / 'models').resolve()

    specific = resolve_models_dir('all-MiniLM-L6-v2')
    assert specific == (fake_home / '.tur' / 'models' / 'all-MiniLM-L6-v2').resolve()


def test_is_model_compatible():
    # Legacy / unspecified candidate
    assert is_model_compatible(None, 'minilm') is True
    assert is_model_compatible(None, 'bge-small') is True
    assert is_model_compatible('minilm', None) is True

    # Exact match
    assert is_model_compatible('minilm', 'minilm') is True
    assert is_model_compatible('bge-small', 'bge-small') is True

    # Alias / canonical normalization
    assert is_model_compatible('minilm', 'all-MiniLM-L6-v2') is True
    assert is_model_compatible('all-minilm-l6-v2_onnx_int8', 'minilm') is True
    assert is_model_compatible('bge-small', 'bge-small-en-v1.5') is True

    # Incompatible models (Strict Homogeneity Invariant)
    assert is_model_compatible('bge-small', 'minilm') is False
    assert is_model_compatible('all-MiniLM-L6-v2', 'bge-small-en-v1.5') is False


def test_zero_poisoning_query_isolation(tmp_path):
    persona_dir = tmp_path / 'persona_iso'
    persona_dir.mkdir(parents=True)
    mgr = MemoryManager(base_dir=persona_dir)

    # Memory 1: Embedded with minilm
    mgr.save(
        Memory(
            type=MemoryType.FACT,
            content='Minilm memory content',
            embedding_model='all-MiniLM-L6-v2',
            embedding_vector=[1.0, 0.0],
        )
    )
    # Memory 2: Embedded with incompatible bge-small
    mgr.save(
        Memory(
            type=MemoryType.FACT,
            content='Bge memory content',
            embedding_model='bge-small-en-v1.5',
            embedding_vector=[0.0, 1.0],
        )
    )

    # Active engine is minilm
    engine = VectorEngine(model_name='minilm')

    # Query with vector [0.0, 1.0] (matching bge memory directionally)
    # But because bge is incompatible, it MUST be isolated and ignored
    res = _l1_fallback_search(
        'unmatched_token',
        persona_dir=persona_dir,
        query_vector=[0.0, 1.0],
        vector_engine=engine,
    )

    # Bge memory was rejected by zero-poisoning isolation; only minilm was evaluated (and cosine is 0.0)
    assert 'Bge memory content' not in res

    # Now test graph node isolation
    import networkx as nx

    g = nx.DiGraph()
    g.add_node(
        'node-bge',
        content='Bge node',
        confidence=1.0,
        status='active',
        embedding_model='bge-small-en-v1.5',
        embedding_vector=[0.0, 1.0],
    )
    g.add_node(
        'node-minilm',
        content='Minilm node',
        confidence=1.0,
        status='active',
        embedding_model='all-MiniLM-L6-v2',
        embedding_vector=[1.0, 0.0],
    )

    scores: dict[str, float] = {}
    _augment_scores_with_vector_similarity(
        graph=g,
        query='test',
        scores=scores,
        query_vector=[0.0, 1.0],
        vector_engine=engine,
    )
    assert 'node-bge' not in scores


def test_vector_engine_auto_discovery(tmp_path, monkeypatch):
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)

    models_dir = fake_home / '.tur' / 'models' / 'all-MiniLM-L6-v2'
    models_dir.mkdir(parents=True)
    fake_onnx = models_dir / 'model_quantized.onnx'
    fake_onnx.write_bytes(b'fake onnx bytes')
    fake_tok = models_dir / 'tokenizer.json'
    fake_tok.write_text('{"fake": "tokenizer"}', encoding='utf-8')

    engine = VectorEngine(model_name='minilm')
    assert engine.model_path == fake_onnx
    assert engine.tokenizer_path == fake_tok


def test_cli_model_list(mock_admin_env):
    res = runner.invoke(admin_app, ['model', 'list'])
    assert res.exit_code == 0
    assert 'ONNX Embedding Models' in res.stdout
    assert 'minilm' in res.stdout
    assert 'bge-small' in res.stdout


def test_cli_model_status(mock_admin_env):
    res = runner.invoke(admin_app, ['model', 'status'])
    assert res.exit_code == 0
    assert 'ONNX Embedding Subsystem Status' in res.stdout
    assert 'Hardware Providers' in res.stdout


def test_cli_model_pull_and_remove(mock_admin_env):
    _tmp_path, _persona_id, _p_dir, fake_home = mock_admin_env

    # Mock urllib.request.urlopen to simulate downloading from HuggingFace
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'dummy model or tokenizer payload'
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    with patch('urllib.request.urlopen', return_value=mock_resp):
        res = runner.invoke(admin_app, ['model', 'pull', 'minilm'])
        assert res.exit_code == 0
        assert "Model 'all-MiniLM-L6-v2' is ready" in res.stdout

    target_dir = fake_home / '.tur' / 'models' / 'all-MiniLM-L6-v2'
    assert target_dir.exists()
    assert (target_dir / 'model_quantized.onnx').exists()
    assert (target_dir / 'tokenizer.json').exists()

    # Now remove model
    res_remove = runner.invoke(admin_app, ['model', 'remove', 'minilm', '--yes'])
    assert res_remove.exit_code == 0
    assert not target_dir.exists()


def test_cli_memory_embed_idempotent_and_force(mock_admin_env):
    tmp_path, _persona_id, p_dir, _fake_home = mock_admin_env
    mgr = MemoryManager(base_dir=p_dir)

    # Create one memory without embedding
    mem1 = Memory(
        type=MemoryType.FACT,
        content='Unembedded memory one',
    )
    mgr.save(mem1)

    # Create one memory already embedded with minilm
    mem2 = Memory(
        type=MemoryType.FACT,
        content='Already embedded memory two',
        embedding_model='all-MiniLM-L6-v2',
        embedding_vector=[0.1, 0.2, 0.3],
    )
    mgr.save(mem2)

    fake_model = tmp_path / 'fake_model.onnx'
    fake_model.write_bytes(b'dummy')

    # Mock VectorEngine
    with patch('tur.cli.admin.VectorEngine') as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.is_onnx_available = True
        mock_instance.is_tokenizers_available = True
        mock_instance.model_path = fake_model
        mock_instance.model_name = 'all-MiniLM-L6-v2'
        mock_instance.embed_text.return_value = [0.4, 0.5, 0.6]
        mock_engine_cls.return_value = mock_instance

        # 1. Run without --force: m1 should be embedded, m2 should be skipped
        res = runner.invoke(admin_app, ['memory', 'embed', '--model', 'minilm'])
        assert res.exit_code == 0
        assert 'Embedding Migration Summary' in res.stdout
        # 1 processed, 1 skipped
        assert mock_instance.embed_text.call_count == 1

        # Check that m1 now has vector
        all_mems = {m.id: m for m in mgr.load_all()}
        assert mem1.id in all_mems
        loaded_m1 = all_mems[mem1.id]
        assert loaded_m1.embedding_vector == [0.4, 0.5, 0.6]
        assert loaded_m1.embedding_model == 'all-MiniLM-L6-v2'

        # 2. Run again without --force: both should be skipped!
        mock_instance.embed_text.reset_mock()
        res2 = runner.invoke(admin_app, ['memory', 'embed', '--model', 'minilm'])
        assert res2.exit_code == 0
        assert mock_instance.embed_text.call_count == 0

        # 3. Run with --force: both should be embedded
        mock_instance.embed_text.reset_mock()
        res3 = runner.invoke(admin_app, ['memory', 'embed', '--model', 'minilm', '--force'])
        assert res3.exit_code == 0
        assert mock_instance.embed_text.call_count == 2
