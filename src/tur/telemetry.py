from typing import Any

from tur.models import Persona


class CognitiveTelemetry:
    """
    Measures the 'Constraint Dimensionality' and load of a Persona.
    Based on the physics defined in cognitive_load.md.
    """

    def measure_static_load(self, system_prompt: str) -> dict[str, Any]:
        """
        Measures the static weight of the persona (The DNA).
        """
        # A rough approximation of tokens (chars / 4) is standard for estimation
        # Real token counting requires tiktoken or similar, but this is sufficient for relative weight.
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
        # Sum of weighted constraints
        base_load = sum(p.weight for p in persona.principles)

        # Interaction Penalty (I_conflict)
        # Hypothesis: Load increases quadratically with the number of high-weight principles
        # because every principle must check against every other principle.
        n = len(persona.principles)
        interaction_penalty = (n * (n - 1)) * 0.05  # Arbitrary coefficient for friction

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
