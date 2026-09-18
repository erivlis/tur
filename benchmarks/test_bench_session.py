"""Benchmarks for EP-0141, EP-0147, EP-0149: Vector clocks, task coordination, and session board."""

import pytest

from tur.session import (
    get_db_connection,
    init_db,
    read_board_logic,
    sort_messages_causally,
    write_board_logic,
)
from tur.task import check_item, claim_task
from tur.vector_clock import VectorClock

# -----------------------------------------------------------------------------
# VECTOR CLOCK BENCHMARKS (EP-0141 / IASP)
# -----------------------------------------------------------------------------


def test_bench_vector_clock_tick(benchmark):
    """Microbenchmark: local emission tick on a VectorClock."""
    vc = VectorClock({"agent-alpha": 5, "agent-beta": 3, "agent-gamma": 8})
    benchmark(vc.tick, "agent-alpha")


def test_bench_vector_clock_lattice_merge(benchmark):
    """Microbenchmark: pointwise lattice maximum merge (|) across multi-agent clocks."""
    vc_a = VectorClock({"agent-1": 10, "agent-2": 5, "agent-3": 2, "agent-4": 7})
    vc_b = VectorClock({"agent-1": 8, "agent-2": 9, "agent-3": 2, "agent-5": 3})

    def run_merge():
        return vc_a | vc_b

    benchmark(run_merge)


def test_bench_vector_clock_concurrency(benchmark):
    """Microbenchmark: concurrent conflict detection (a || b) between branching clocks."""
    vc_a = VectorClock({"agent-1": 10, "agent-2": 3})
    vc_b = VectorClock({"agent-1": 8, "agent-2": 5})
    benchmark(vc_a.is_concurrent_with, vc_b)


@pytest.fixture
def synthetic_messages_50() -> list[dict]:
    """Generates 50 messages with diverse vector clock topologies (forks and dependencies)."""
    messages = []
    clock = VectorClock()
    agents = ["agent-alpha", "agent-beta", "agent-gamma"]
    for i in range(50):
        agent = agents[i % len(agents)]
        clock = clock.tick(agent)
        messages.append({
            "id": f"msg-{i:03d}",
            "sender": agent,
            "recipient": "broadcast",
            "content": f"Coordination payload {i}",
            "vector_clock": clock.to_dict(),
        })
    return list(reversed(messages))


def test_bench_sort_messages_causally(benchmark, synthetic_messages_50):
    """EP-0141 / EP-0149: Causal topological sorting over 50 multi-agent messages."""
    benchmark(sort_messages_causally, synthetic_messages_50)


# -----------------------------------------------------------------------------
# SESSION BOARD BENCHMARKS (EP-0149)
# -----------------------------------------------------------------------------


@pytest.fixture
def session_board_env(isolated_home):
    """Pre-initializes a session database with registered agent in the isolated workspace."""
    session_id = "bench-session-001"
    conn = get_db_connection(session_id)
    init_db(conn)
    conn.execute(
        "INSERT OR IGNORE INTO agents (id, harness, substrate, status, run_token) VALUES (?, ?, ?, ?, ?)",
        ("agent-bench", "bench", "local", "active", "token-bench"),
    )
    conn.commit()
    conn.close()
    return session_id


def test_bench_session_board_write(benchmark, session_board_env):
    """EP-0149: Atomic write of coordinate to the session board SQLite database."""
    session_id = session_board_env
    benchmark(
        write_board_logic,
        session_id,
        "coordination:status",
        "active_deliberation",
        "agent-bench",
    )


def test_bench_session_board_read(benchmark, session_board_env):
    """EP-0149: Read coordinate from the session board SQLite database."""
    session_id = session_board_env
    write_board_logic(session_id, "benchmark:target", "ready", "agent-bench")
    benchmark(read_board_logic, session_id, "benchmark:target")


# -----------------------------------------------------------------------------
# TASK COORDINATION BENCHMARKS (EP-0147)
# -----------------------------------------------------------------------------


def test_bench_task_claim_and_check(benchmark, session_board_env):
    """EP-0147: Task claim and checklist item synchronization on the session board."""
    session_id = session_board_env

    def run_task_cycle():
        claim_task(
            session_id=session_id,
            task_id="bench-task-100",
            title="Benchmark Task",
            objective="Evaluate performance",
            agent_id="agent-bench",
            work_items=["Compile specification", "Verify invariants", "Report results"],
            force=True,
        )
        check_item(session_id, 1, task_id="bench-task-100", done=True, updated_by="agent-bench")

    benchmark(run_task_cycle)
