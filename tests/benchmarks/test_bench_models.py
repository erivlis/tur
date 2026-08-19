"""Benchmarks for the model layer: Merkle hashing and pydantic (de)serialization."""

from datetime import datetime

import pytest

from tur.models import Memory, MemoryScope, MemoryType, Persona, SessionState


@pytest.mark.benchmark
def test_bench_memory_merkle_hash(memory_factory):
    """EP-0106: content-addressable hashing of a single small memory."""
    memory_factory(42)


@pytest.mark.benchmark
def test_bench_memory_merkle_hash_large_content():
    """Hashing a large memory body (~16 KB) — the worst case of the ledger write path."""
    Memory(
        timestamp=datetime(2026, 5, 29, 12, 0, 0),
        type=MemoryType.INSIGHT,
        scope=MemoryScope.PERSONA,
        tags=['large', 'benchmark'],
        content='The complexity of AI is an illusion of distance. ' * 350,
    )


@pytest.mark.benchmark
def test_bench_memory_batch_construction(memory_factory):
    """Constructing a full batch of memories, as done when ingesting a session."""
    for index in range(100):
        memory_factory(index, content_size=2)


def test_bench_persona_validation(benchmark, session_state: SessionState):
    """Re-validating a persona payload, the entry point of every state load."""
    payload = session_state.persona.model_dump()
    benchmark(Persona.model_validate, payload)


def test_bench_session_state_dump(benchmark, session_state: SessionState):
    """Serializing the full session state (feeds the prompt compiler)."""
    benchmark(session_state.model_dump)
