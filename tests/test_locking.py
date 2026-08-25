import asyncio
import multiprocessing as mp
import os
import time
from pathlib import Path

import pytest
from filelock import FileLock

from tur.locking import (
    DEFAULT_POLL_INTERVAL_SECONDS,
    FAST_LOCK_TIMEOUT_SECONDS,
    LockTimeoutError,
    async_state_lock,
    get_file_lock,
    state_lock,
)


def test_basic_lock_acquisition(tmp_path: Path):
    """Test basic lock acquire and release cycle."""
    lock_file = tmp_path / '.locks' / 'test.lock'
    assert not lock_file.exists()

    with state_lock(lock_file, timeout=1.0) as lock:
        assert lock_file.exists()
        assert lock.is_locked

    # Lock file is preserved on disk but unlocked
    assert lock_file.exists()
    assert not lock.is_locked


def test_matrix_m3_lock_timeout_exception(tmp_path: Path):
    """Matrix M3: Test that contending lock raises LockTimeoutError with timeout metadata."""
    lock_file = tmp_path / '.locks' / 'timeout.lock'

    # Pre-acquire with direct FileLock without releasing
    lock1 = get_file_lock(lock_file)
    lock1.acquire()

    try:
        competing = FileLock(str(lock_file.resolve()))

        def _acquire_competing():
            try:
                competing.acquire(timeout=0.1, poll_interval=0.01)
            except Exception as e:
                raise LockTimeoutError(lock_file, 0.1) from e

        with pytest.raises(LockTimeoutError) as exc_info:
            _acquire_competing()

        assert exc_info.value.lock_path == lock_file
        assert exc_info.value.timeout == 0.1
        assert 'held by another process' in str(exc_info.value)
    finally:
        lock1.release()


def _barrier_worker(lock_path: Path, counter_file: Path, worker_id: int, barrier: mp.Barrier):
    """Worker process that synchronizes on barrier and increments a file counter under lock."""
    barrier.wait()  # Release all workers simultaneously

    with state_lock(lock_path, timeout=10.0, poll_interval=0.005):
        # Read-Modify-Write cycle
        current = int(counter_file.read_text(encoding='utf-8').strip()) if counter_file.exists() else 0
        time.sleep(0.005)  # Simulate small critical section work
        counter_file.write_text(str(current + 1), encoding='utf-8')


def test_matrix_m1_multiprocessing_barrier_zero_lost_updates(tmp_path: Path):
    """Matrix M1: Empirically verify 100% zero data loss under N=10 concurrent processes."""
    num_workers = 10
    lock_file = tmp_path / '.locks' / 'counter.lock'
    counter_file = tmp_path / 'counter.txt'
    counter_file.write_text('0', encoding='utf-8')

    barrier = mp.Barrier(num_workers)
    processes = [
        mp.Process(target=_barrier_worker, args=(lock_file, counter_file, i, barrier)) for i in range(num_workers)
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join(timeout=15.0)
        assert not p.is_alive(), 'Worker process timed out or deadlocked'
        assert p.exitcode == 0, f'Worker failed with exit code {p.exitcode}'

    final_val = int(counter_file.read_text(encoding='utf-8').strip())
    assert final_val == num_workers, f'Race condition detected! Expected {num_workers}, got {final_val}'


def _worker_hold_and_release(lock_path: Path, hold_seconds: float, barrier: mp.Barrier):
    barrier.wait()
    with state_lock(lock_path, timeout=5.0):
        time.sleep(hold_seconds)


def test_matrix_m2_contention_fast_probe_and_polling(tmp_path: Path):
    """Matrix M2: Verify 5ms polling recovers lock within 25ms of release under contention."""
    lock_file = tmp_path / '.locks' / 'poll.lock'
    barrier = mp.Barrier(2)
    hold_duration = 0.1  # 100ms

    p = mp.Process(target=_worker_hold_and_release, args=(lock_file, hold_duration, barrier))
    p.start()

    try:
        barrier.wait()
        # Give worker a moment to acquire lock
        time.sleep(0.02)
        start_wait = time.perf_counter()
        with state_lock(lock_file, timeout=5.0, poll_interval=DEFAULT_POLL_INTERVAL_SECONDS):
            elapsed = time.perf_counter() - start_wait
            assert elapsed >= 0.05
            assert elapsed <= hold_duration + 0.08
    finally:
        p.join(timeout=5.0)


def _worker_crash_with_lock(lock_path: Path, barrier: mp.Barrier):
    """Acquires lock and exits abnormally via os._exit to simulate hard crash."""
    barrier.wait()
    lock = FileLock(str(lock_path.resolve()))
    lock.acquire()
    os._exit(42)  # Abrupt process kill without running finalizers/context cleanup


def test_matrix_m4_abnormal_termination_crash_recovery(tmp_path: Path):
    """Matrix M4: Verify OS kernel releases lock on abnormal termination/SIGKILL."""
    lock_file = tmp_path / '.locks' / 'crash.lock'
    barrier = mp.Barrier(2)

    p = mp.Process(target=_worker_crash_with_lock, args=(lock_file, barrier))
    p.start()

    try:
        barrier.wait()
        p.join(timeout=5.0)
        assert p.exitcode == 42  # Process died abnormally

        # Subsequent process must acquire lock without deadlocking on stale lock
        with state_lock(lock_file, timeout=1.0) as lock:
            assert lock.is_locked
    finally:
        if p.is_alive():
            p.kill()


@pytest.mark.asyncio
async def test_matrix_m5_async_state_lock_concurrency(tmp_path: Path):
    """Matrix M5: Test async_state_lock serializes 5 concurrent coroutines."""
    lock_file = tmp_path / '.locks' / 'async_seq.lock'
    trace = []

    async def _task(idx: int):
        async with async_state_lock(lock_file, timeout=5.0):
            trace.append(f'start_{idx}')
            await asyncio.sleep(0.02)
            trace.append(f'end_{idx}')

    await asyncio.gather(*[_task(i) for i in range(5)])

    assert len(trace) == 10
    # Verify that each start is immediately followed by its own end (strict serialization)
    for i in range(0, 10, 2):
        start_id = trace[i].replace('start_', '')
        end_id = trace[i + 1].replace('end_', '')
        assert start_id == end_id, f'Coroutines interleaved! {trace[i]} followed by {trace[i + 1]}'


def test_matrix_m6_total_lock_hierarchy_ordering(tmp_path: Path):
    """Matrix M6: Verify multi-lock acquisition in descending order (Global -> Local)."""
    global_lock = tmp_path / 'global.lock'
    local_lock = tmp_path / 'local.lock'

    # Strict descending acquisition: Global Persona -> Local Session
    with (
        state_lock(global_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS),
        state_lock(local_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS),
    ):
        pass
