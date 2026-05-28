import pytest

from tur.models import Persona, Principle
from tur.telemetry import CognitiveTelemetry


def test_measure_static_load():
    telemetry = CognitiveTelemetry()

    prompt = "This is a simple system prompt. Symmetry Noether."
    metrics = telemetry.measure_static_load(prompt)

    assert metrics["char_count"] == len(prompt)
    assert metrics["est_tokens"] == int(len(prompt) / 4)
    assert metrics["density"] > 0.0


def test_measure_static_load_empty():
    telemetry = CognitiveTelemetry()
    metrics = telemetry.measure_static_load("")
    assert metrics["char_count"] == 0
    assert metrics["est_tokens"] == 0
    assert metrics["density"] == 0.0


def test_calculate_constraint_dimensionality():
    telemetry = CognitiveTelemetry()

    # 0 principles
    persona_empty = Persona(
        name="Empty",
        aleph="Nothing",
        principles=[]
    )
    assert telemetry.calculate_constraint_dimensionality(persona_empty) == 0.0

    # 1 principle
    persona_one = Persona(
        name="One",
        aleph="One",
        principles=[
            Principle(name="Symmetry", role="Guardian", weight=1.5)
        ]
    )
    # Cp = 1.5 + (1 * 0) * 0.05 = 1.5
    assert telemetry.calculate_constraint_dimensionality(persona_one) == 1.5

    # 2 principles
    persona_two = Persona(
        name="Two",
        aleph="Two",
        principles=[
            Principle(name="Symmetry", role="Guardian", weight=1.5),
            Principle(name="Safety", role="Guardian", weight=2.0)
        ]
    )
    # Cp = (1.5 + 2.0) + (2 * 1) * 0.05 = 3.5 + 0.1 = 3.6
    assert telemetry.calculate_constraint_dimensionality(persona_two) == 3.6
