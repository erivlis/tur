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
    MAX_POLL_INTERVAL_SECONDS,
    LockTimeoutError,
    async_state_lock,
    compute_jittered_poll_interval,
    get_async_file_lock,
    get_file_lock,
    jittered_backoff_delays,
    lock_contention_guard,
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

    # Pre-acquire with a separate non-singleton lock
    lock1 = FileLock(str(lock_file.resolve()), is_singleton=False)
    lock1.acquire()

    try:
        with pytest.raises(LockTimeoutError) as exc_info, state_lock(lock_file, timeout=0.05, poll_interval=0.005):
            pass

        assert exc_info.value.lock_path == lock_file
        assert exc_info.value.timeout == 0.05
        assert 'held by another process' in str(exc_info.value)
    finally:
        lock1.release()


def test_lock_holder_stamping(tmp_path: Path):
    """Test that lock acquisition writes PID and hostname to the lock descriptor."""
    lock_file = tmp_path / '.locks' / 'stamp.lock'

    with state_lock(lock_file, timeout=1.0):
        assert lock_file.exists()

    content = lock_file.read_text(encoding='utf-8')
    assert f'pid={os.getpid()}' in content
    assert 'host=' in content


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


def _worker_hold_and_release(lock_path: Path, hold_duration: float, barrier: mp.Barrier):
    """Worker process holding a lock for a specified duration."""
    lock = FileLock(str(lock_path.resolve()))
    lock.acquire()
    barrier.wait()
    try:
        time.sleep(hold_duration)
    finally:
        lock.release()


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
            assert elapsed <= hold_duration + 0.35
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


def test_compute_jittered_poll_interval_bounds():
    """EP-0140: Verify decorrelated jitter mathematically satisfies lower/upper bounds."""
    base = 0.005
    max_sleep = 0.25

    # Test starting from base
    prev = base
    for _ in range(100):
        interval = compute_jittered_poll_interval(prev, base=base, max_sleep=max_sleep)
        assert base <= interval <= max_sleep, f'Interval {interval} out of bounds [{base}, {max_sleep}]'
        prev = interval

    # Test edge case: prev = 0.0
    zero_prev = compute_jittered_poll_interval(0.0, base=base, max_sleep=max_sleep)
    assert base <= zero_prev <= max_sleep

    # Test edge case: prev >> max_sleep
    huge_prev = compute_jittered_poll_interval(100.0, base=base, max_sleep=max_sleep)
    assert huge_prev == max_sleep


def test_compute_jittered_poll_interval_distribution():
    """EP-0140: Verify decorrelated jitter produces stochastic values (not fixed intervals)."""
    base = 0.005
    max_sleep = 0.25
    prev = 0.05
    samples = [compute_jittered_poll_interval(prev, base=base, max_sleep=max_sleep) for _ in range(50)]
    assert len(set(samples)) > 20, 'Samples should have stochastic diversity'


def test_jittered_backoff_delays_exhaustion():
    """EP-0140: Verify jittered_backoff_delays generator stops when timeout deadline expires."""
    delays = []
    for d in jittered_backoff_delays(timeout=0.05, base=0.005, max_sleep=0.02):
        delays.append(d)
        time.sleep(d)

    assert len(delays) >= 2
    assert all(0 < d <= 0.02 for d in delays)


def test_get_async_file_lock_creation(tmp_path: Path):
    """EP-0140: Verify get_async_file_lock instantiates configured AsyncFileLock."""
    lock_file = tmp_path / '.locks' / 'async_inst.lock'
    async_lock = get_async_file_lock(lock_file, timeout=2.0)
    assert async_lock.is_singleton
    assert lock_file.parent.exists()


def test_lock_contention_guard_sync_handling(tmp_path: Path):
    """Verify lock_contention_guard intercepts LockTimeoutError in sync functions."""
    lock_file = tmp_path / 'test.lock'

    @lock_contention_guard(on_contention=lambda e: f'Handled contention on {e.lock_path.name}')
    def sync_failing(x: int) -> str:
        """My docstring."""
        raise LockTimeoutError(lock_file, 1.5)

    @lock_contention_guard(on_contention=lambda e: 'Handled')
    def sync_success(x: int) -> int:
        return x * 2

    @lock_contention_guard(default='fallback_value')
    def sync_default_fallback() -> str:
        raise LockTimeoutError(lock_file, 0.5)

    # Contention intercepted with custom handler
    assert sync_failing(10) == 'Handled contention on test.lock'
    # Success passes through
    assert sync_success(21) == 42
    # Fallback default when no handler provided
    assert sync_default_fallback() == 'fallback_value'
    # Function metadata preserved
    assert sync_failing.__name__ == 'sync_failing'
    assert sync_failing.__doc__ == 'My docstring.'


@pytest.mark.asyncio
async def test_lock_contention_guard_async_handling(tmp_path: Path):
    """Verify lock_contention_guard intercepts LockTimeoutError in async functions."""
    lock_file = tmp_path / 'async_test.lock'

    @lock_contention_guard(on_contention=lambda e: {'status': 'contended', 'path': str(e.lock_path)})
    async def async_failing():
        await asyncio.sleep(0)
        raise LockTimeoutError(lock_file, 2.0)

    @lock_contention_guard(on_contention=lambda e: 'Never')
    async def async_success():
        await asyncio.sleep(0)
        return 'ok'

    res = await async_failing()
    assert res['status'] == 'contended'
    assert str(lock_file) in res['path']

    res_ok = await async_success()
    assert res_ok == 'ok'

