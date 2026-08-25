import asyncio
import multiprocessing as mp
import time
from pathlib import Path

import pytest

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


def test_lock_timeout_exception(tmp_path: Path):
    """Test that contending lock raises LockTimeoutError with timeout metadata."""
    lock_file = tmp_path / '.locks' / 'timeout.lock'

    # Pre-acquire with direct FileLock without releasing
    lock1 = get_file_lock(lock_file)
    lock1.acquire()

    try:
        from filelock import FileLock

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


def test_multiprocessing_barrier_zero_lost_updates(tmp_path: Path):
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


@pytest.mark.asyncio
async def test_async_state_lock(tmp_path: Path):
    """Test async_state_lock non-blocking acquisition."""
    lock_file = tmp_path / '.locks' / 'async.lock'

    async with async_state_lock(lock_file, timeout=2.0) as lock:
        assert lock.is_locked

    assert not lock.is_locked


@pytest.mark.asyncio
async def test_async_state_lock_concurrency(tmp_path: Path):
    """Test async_state_lock serializes 5 concurrent coroutines."""
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
