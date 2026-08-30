"""Benchmarks for the prompt compiler and the YAML fast path it relies on."""

import io

import pytest

from tur._helpers import yaml_safe_load
from tur.compiler import compile_persona
from tur.models import SessionState

YAML_DOCUMENT = (
    'type: L1 Memory\n'
    'title: Memory deadbeef\n'
    'description: Insight about the traveler and the terrain\n'
    'tags:\n'
    '  - benchmark\n'
    '  - tur\n'
    "timestamp: '2026-05-29T12:00:00'\n"
    'scope: PERSONA\n'
    'memory_type: INSIGHT\n'
    'hash: ' + 'a' * 64 + '\n'
    'links:\n' + ''.join(f'  - uri: tur://memory/{index}\n    relation: supports\n' for index in range(20))
)


def test_bench_compile_persona(benchmark, session_state: SessionState):
    """Renders the full system prompt from a populated session state (Jinja2)."""
    benchmark(compile_persona, session_state)


@pytest.mark.benchmark
def test_bench_yaml_safe_load():
    """The OKF frontmatter parser used on every memory and concept read."""
    yaml_safe_load(io.StringIO(YAML_DOCUMENT))
