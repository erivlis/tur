from typing import Any

from pydantic import BaseModel

from tur import persona, user
from tur._helpers import yaml_safe_load
from tur.compiler import compile_persona
from tur.models import Persona, SessionState


class CognitiveMetrics:
    """
    Measures the 'Constraint Dimensionality' and cognitive complexity of a Persona.
    Based on static prompt analysis and principle constraint weighting.
    """

    def measure_static_load(self, system_prompt: str) -> dict[str, Any]:
        """
        Measures the static token weight and lexical density of the compiled prompt.
        """
        char_count = len(system_prompt)
        est_tokens = char_count / 4

        return {
            'char_count': char_count,
            'est_tokens': int(est_tokens),
            'density': self._calculate_density(system_prompt),
        }

    @staticmethod
    def calculate_constraint_dimensionality(persona: Persona) -> float | int:
        """
        Calculates Cp = Sum(N_c * W_c) + I_conflict
        """
        base_load = sum(p.weight for p in persona.principles)

        n = len(persona.principles)
        interaction_penalty = (n * (n - 1)) * 0.05  # Friction coefficient across active constraints

        return round(base_load + interaction_penalty, 2)

    @staticmethod
    def _calculate_density(text: str) -> float | int:
        """
        Estimates Information Density (Unique Words / Total Words).
        """
        words = text.split()
        if not words:
            return 0.0
        unique_words = set(words)
        return round(len(unique_words) / len(words), 3)


# Backwards compatibility alias
CognitiveTelemetry = CognitiveMetrics


class MetricsReport(BaseModel):
    """Structured report containing cognitive load, token cost, and constraint dimensionality."""

    persona_id: str
    persona_name: str
    num_principles: int
    constraint_dimensionality: float
    rating_class: str
    static_token_cost: int
    char_count: int
    information_density: float

    def to_dict(self) -> dict[str, Any]:
        return {
            'persona_id': self.persona_id,
            'persona_name': self.persona_name,
            'num_principles': self.num_principles,
            'constraint_dimensionality': self.constraint_dimensionality,
            'class': self.rating_class,
            'static_token_cost': self.static_token_cost,
            'char_count': self.char_count,
            'information_density': self.information_density,
        }


# Backwards compatibility alias
TelemetryReport = MetricsReport


def compute_persona_metrics(identifier: str | None = None) -> MetricsReport:
    """
    Computes static token cost, information density, and Constraint Dimensionality (Cp)
    for the specified or active persona.
    """
    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    persona_obj = persona.load_persona(persona_dir)

    user_profile = user.get_user_profile()
    state = SessionState(persona=persona_obj, user=user_profile, memories=[], epilogue=None, knowledge_graph=None)
    system_prompt = compile_persona(state)

    metrics_engine = CognitiveMetrics()
    static_metrics = metrics_engine.measure_static_load(system_prompt)
    cp = float(metrics_engine.calculate_constraint_dimensionality(persona_obj))

    if cp < 5:
        rating = 'Human (Manageable)'
    elif cp < 10:
        rating = 'Giant (Heavy Load)'
    else:
        rating = 'Titan (Inference Warning)'

    return MetricsReport(
        persona_id=active_id,
        persona_name=persona_obj.name,
        num_principles=len(persona_obj.principles),
        constraint_dimensionality=cp,
        rating_class=rating,
        static_token_cost=static_metrics['est_tokens'],
        char_count=static_metrics['char_count'],
        information_density=static_metrics['density'],
    )


# Backwards compatibility alias
compute_persona_telemetry = compute_persona_metrics
