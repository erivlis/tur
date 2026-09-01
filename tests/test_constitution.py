import uuid
from pathlib import Path

import pytest
import yaml

from tur.metrics import compute_persona_metrics
from tur.models import Persona, Principle
from tur.persona import (
    dump_constitution_markdown,
    load_persona,
    parse_constitution_markdown,
    save_constitution,
)
from tur.session import hydrate_session_state


def test_parse_constitution_markdown():
    """Verify parsing CONSTITUTION.md markdown with YAML frontmatter."""
    md = """---
name: "Ariel"
version: "5.4.0"
model: "gemini-3.1-pro-preview"
aleph: "To safeguard reality"
---

# Persona Constitution: Ariel

## 1. The Aleph (Primary Directive)
To safeguard reality

## 2. Active Principles
### Symmetry — Role: Invariance
"""
    parsed = parse_constitution_markdown(md)
    assert parsed['name'] == 'Ariel'
    assert parsed['version'] == '5.4.0'
    assert parsed['model'] == 'gemini-3.1-pro-preview'
    assert parsed['aleph'] == 'To safeguard reality'


def test_dump_constitution_markdown_roundtrip():
    """Verify Persona serialization to CONSTITUTION.md and deserialization roundtrip."""
    persona = Persona(
        name='Ariel',
        version='1.0.0',
        model='gemini-3.1-pro-preview',
        aleph='To preserve topological symmetry across autonomous development.',
        principles=[
            Principle(
                name='Symmetry',
                avatar='Noether',
                role='Guardian of Invariance',
                weight=1.5,
                constraints=['Conserved quantities hold'],
            ),
            Principle(
                name='Falsifiability',
                avatar='Popper',
                role='Empirical Rigor',
                weight=1.5,
                constraints=['Hypotheses must yield'],
            ),
        ],
    )

    md = dump_constitution_markdown(persona)
    assert '---' in md
    assert 'name: Ariel' in md
    assert '# Persona Constitution: Ariel' in md
    assert '### Symmetry (Noether) — Role: Guardian of Invariance' in md
    assert '- Conserved quantities hold' in md

    parsed = parse_constitution_markdown(md)
    reconstituted = Persona(**parsed)
    assert reconstituted.name == persona.name
    assert reconstituted.version == persona.version
    assert reconstituted.aleph == persona.aleph
    assert len(reconstituted.principles) == 2
    assert reconstituted.principles[0].name == 'Symmetry'


def test_load_persona_constitution_precedence(tmp_path: Path):
    """Verify load_persona prefers CONSTITUTION.md when both CONSTITUTION.md and persona.yaml exist."""
    p_dir = tmp_path / 'personas' / 'p1'
    p_dir.mkdir(parents=True, exist_ok=True)

    # Legacy persona.yaml
    legacy = Persona(name='LegacyAriel', aleph='Legacy Aleph', version='0.1.0')
    (p_dir / 'persona.yaml').write_text(yaml.dump(legacy.model_dump(mode='json')), encoding='utf-8')

    # Modern CONSTITUTION.md
    modern = Persona(name='ModernAriel', aleph='Modern Aleph', version='2.0.0')
    save_constitution(p_dir, modern)

    loaded = load_persona(p_dir)
    assert loaded.name == 'ModernAriel'
    assert loaded.version == '2.0.0'
    assert loaded.aleph == 'Modern Aleph'


def test_load_persona_fallback_yaml(tmp_path: Path):
    """Verify load_persona falls back to persona.yaml if CONSTITUTION.md is missing."""
    p_dir = tmp_path / 'personas' / 'p2'
    p_dir.mkdir(parents=True, exist_ok=True)

    legacy = Persona(name='LegacyFallback', aleph='Legacy Fallback Aleph', version='0.2.0')
    (p_dir / 'persona.yaml').write_text(yaml.dump(legacy.model_dump(mode='json')), encoding='utf-8')

    loaded = load_persona(p_dir)
    assert loaded.name == 'LegacyFallback'
    assert loaded.version == '0.2.0'


def test_load_persona_not_found(tmp_path: Path):
    """Verify load_persona raises FileNotFoundError when no persona definitions exist."""
    empty_dir = tmp_path / 'empty'
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError, match=r'Neither CONSTITUTION.md nor persona.yaml found'):
        load_persona(empty_dir)


def test_hydrate_session_state_with_constitution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify hydrate_session_state successfully constructs SessionState from CONSTITUTION.md."""
    tur_dir = tmp_path / '.tur'
    persona_id = str(uuid.uuid4())
    p_dir = tur_dir / 'personas' / persona_id
    p_dir.mkdir(parents=True, exist_ok=True)

    persona = Persona(
        name='ArielConstitutional',
        version='3.0.0',
        model='gemini-3.1-pro-preview',
        aleph='Direct constitutional testing',
    )
    save_constitution(p_dir, persona)

    monkeypatch.setattr('tur.session.get_persona_path', lambda pid: p_dir)
    monkeypatch.setattr('tur.session.get_active_persona_id', lambda: persona_id)
    monkeypatch.chdir(tmp_path)

    state = hydrate_session_state(persona_id)
    assert state.persona.name == 'ArielConstitutional'
    assert state.persona.version == '3.0.0'
    assert state.persona.aleph == 'Direct constitutional testing'


def test_compute_persona_metrics_with_constitution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify compute_persona_metrics executes with CONSTITUTION.md."""
    tur_dir = tmp_path / '.tur'
    persona_id = str(uuid.uuid4())
    p_dir = tur_dir / 'personas' / persona_id
    p_dir.mkdir(parents=True, exist_ok=True)

    persona_obj = Persona(
        name='ArielMetrics',
        version='1.5.0',
        aleph='Metrics testing aleph',
        principles=[Principle(name='Symmetry', role='Invariance', weight=2.0)],
    )
    save_constitution(p_dir, persona_obj)

    monkeypatch.setattr('tur.metrics.persona.get_persona_path', lambda pid: p_dir)
    monkeypatch.setattr('tur.metrics.persona.get_active_persona_id', lambda ident=None: persona_id)

    report = compute_persona_metrics(persona_id)
    assert report.persona_id == persona_id
    assert report.constraint_dimensionality > 0
