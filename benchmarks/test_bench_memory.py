"""Benchmarks for the federated L1 memory bank (OKF writes, reads and verification)."""

import pytest

from tur.memory import MemoryManager
from tur.models import MemoryScope


def test_bench_memory_save(benchmark, persona_dir, memory_factory):
    """Atomic OKF write of a single memory (frontmatter dump + fsync + replace)."""
    manager = MemoryManager(base_dir=persona_dir)
    memory = memory_factory(1, scope=MemoryScope.INCARNATION, content_size=3)
    benchmark(manager.save, memory)


@pytest.mark.benchmark
def test_bench_memory_load_all(populated_memory_bank: MemoryManager):
    """Reads and re-validates the whole federated bank (100 OKF files)."""
    populated_memory_bank.load_all()


@pytest.mark.benchmark
def test_bench_memory_load_all_with_archived(populated_memory_bank: MemoryManager):
    """Same as above, including the archive directories."""
    populated_memory_bank.load_all(include_archived=True)


@pytest.mark.benchmark
def test_bench_memory_verify_integrity(populated_memory_bank: MemoryManager):
    """EP-0106: recomputes every Merkle hash and checks it against the filename."""
    populated_memory_bank.verify_integrity()


@pytest.mark.benchmark
def test_bench_memory_query_by_tags(populated_memory_bank: MemoryManager):
    """Tag filtering over the merged federated timeline."""
    populated_memory_bank.query(tags=['tag-1', 'tag-4'], limit=50)
