import pytest
import yaml

from tur import persona
from tur.metrics import CognitiveMetrics, compute_persona_metrics
from tur.models import Persona, Principle


def test_measure_static_load():
    metrics_engine = CognitiveMetrics()

    prompt = 'This is a simple system prompt. Symmetry Noether.'
    metrics = metrics_engine.measure_static_load(prompt)

    assert metrics['char_count'] == len(prompt)
    assert metrics['est_tokens'] == int(len(prompt) / 4)
    assert metrics['density'] > 0.0


def test_measure_static_load_empty():
    metrics_engine = CognitiveMetrics()
    metrics = metrics_engine.measure_static_load('')
    assert metrics['char_count'] == 0
    assert metrics['est_tokens'] == 0
    assert metrics['density'] == 0.0


def test_calculate_constraint_dimensionality():
    metrics_engine = CognitiveMetrics()

    # 0 principles
    persona_empty = Persona(name='Empty', aleph='Nothing', principles=[])
    assert metrics_engine.calculate_constraint_dimensionality(persona_empty) == 0.0

    # 1 principle
    persona_one = Persona(name='One', aleph='One', principles=[Principle(name='Symmetry', role='Guardian', weight=1.5)])
    # Cp = 1.5 + (1 * 0) * 0.05 = 1.5
    assert metrics_engine.calculate_constraint_dimensionality(persona_one) == 1.5

    # 2 principles
    persona_two = Persona(
        name='Two',
        aleph='Two',
        principles=[
            Principle(name='Symmetry', role='Guardian', weight=1.5),
            Principle(name='Safety', role='Guardian', weight=2.0),
        ],
    )
    # Cp = (1.5 + 2.0) + (2 * 1) * 0.05 = 3.5 + 0.1 = 3.6
    assert metrics_engine.calculate_constraint_dimensionality(persona_two) == 3.6


def test_compute_persona_metrics(tmp_path, monkeypatch):
    persona_dir = tmp_path / 'personas' / 'p-123'
    persona_dir.mkdir(parents=True)

    persona_data = {
        'name': 'TestPersona',
        'version': '1.0.0',
        'aleph': 'Test aleph mission.',
        'principles': [
            {'name': 'Principle1', 'role': 'Role1', 'weight': 1.0},
        ],
    }
    with open(persona_dir / 'persona.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(persona_data, f)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'p-123')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    report = compute_persona_metrics('p-123')
    assert report.persona_name == 'TestPersona'
    assert report.persona_id == 'p-123'
    assert report.num_principles == 1
    assert report.constraint_dimensionality == 1.0
    assert report.rating_class == 'Human (Manageable)'
    assert report.static_token_cost > 0
    assert report.information_density > 0.0

    as_dict = report.to_dict()
    assert as_dict['class'] == 'Human (Manageable)'
    assert as_dict['persona_id'] == 'p-123'


def test_compute_persona_metrics_missing_file(tmp_path, monkeypatch):
    persona_dir = tmp_path / 'personas' / 'missing-persona'
    persona_dir.mkdir(parents=True)

    monkeypatch.setattr(persona, 'get_active_persona_id', lambda ident=None: 'missing-persona')
    monkeypatch.setattr(persona, 'get_persona_path', lambda pid: persona_dir)

    with pytest.raises(FileNotFoundError, match=r'Neither CONSTITUTION.md nor persona.yaml found'):
        compute_persona_metrics('missing-persona')
