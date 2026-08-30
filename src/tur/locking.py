"""
Multi-process state synchronization and advisory file locking for Tur.

Single canonical source for transactional lock acquisition across workspace
terrain (.tur/.locks) and global traveler runtime directories (resolve_runtime_dir/locks).
Implements EP-0129 with filelock, configured for low-latency fast-probing (5ms)
and singleton thread re-entrancy.
"""

import asyncio
import logging
import os
import random
import socket
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from filelock import AsyncFileLock, FileLock, Timeout

logger = logging.getLogger(__name__)

# Polling and Timeout Constants
DEFAULT_POLL_INTERVAL_SECONDS: float = 0.005  # 5ms fast probe eliminates latency quantization
MAX_POLL_INTERVAL_SECONDS: float = 0.25  # 250ms upper bound for decorrelated jitter
FAST_LOCK_TIMEOUT_SECONDS: float = 3.0  # Interactive state mutations (session notes, telemetry)
HEAVY_LOCK_TIMEOUT_SECONDS: float = 30.0  # Storage migrations and Merkle graph compaction
DEFAULT_LOCK_TIMEOUT_SECONDS: float = FAST_LOCK_TIMEOUT_SECONDS


def compute_jittered_poll_interval(
    previous_sleep: float,
    base: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_sleep: float = MAX_POLL_INTERVAL_SECONDS,
) -> float:
    """Calculates decorrelated jitter interval to eliminate lock contention.

    Follows the formula: t_{i+1} = min(t_max, Uniform(t_base, max(t_base, 3 * t_i)))
    """
    return min(max_sleep, random.uniform(base, max(base, previous_sleep * 3.0)))


def jittered_backoff_delays(
    timeout: float,
    base: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_sleep: float = MAX_POLL_INTERVAL_SECONDS,
) -> Iterator[float]:
    """Yields bounded sleep durations for decorrelated jitter retry loops until timeout."""
    deadline = time.monotonic() + timeout
    current_sleep = base
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        sleep_duration = compute_jittered_poll_interval(current_sleep, base=base, max_sleep=max_sleep)
        yield min(sleep_duration, remaining)
        current_sleep = sleep_duration


class LockTimeoutError(TimeoutError):
    """Raised when a file lock cannot be acquired within the timeout window."""

    def __init__(self, lock_path: Path, timeout: float) -> None:
        self.lock_path = lock_path
        self.timeout = timeout
        super().__init__(f'Could not acquire lock on {lock_path} after {timeout:.2f}s (held by another process)')


_CACHED_HOSTNAME = socket.gethostname()


def _stamp_lock_holder(fd: int) -> None:
    """Stamp holder PID and hostname into native lock descriptor for debugging."""
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        payload = f'pid={os.getpid()} host={_CACHED_HOSTNAME}\n'.encode()
        os.write(fd, payload)
        os.ftruncate(fd, len(payload))
    except OSError:
        pass


def get_file_lock(
    lock_path: Path,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> FileLock:
    """Instantiate a platform-aware singleton FileLock with production defaults."""
    resolved_path = lock_path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    return FileLock(
        str(resolved_path),
        timeout=timeout,
        poll_interval=poll_interval,
        is_singleton=True,
        preserve_lock_file=True,
        close_error_policy='suppress',
        on_acquired=_stamp_lock_holder,
    )


def get_async_file_lock(
    lock_path: Path,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> AsyncFileLock:
    """Instantiate a platform-aware singleton AsyncFileLock with production defaults."""
    resolved_path = lock_path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    return AsyncFileLock(
        str(resolved_path),
        timeout=timeout,
        poll_interval=poll_interval,
        is_singleton=True,
        preserve_lock_file=True,
        close_error_policy='suppress',
        on_acquired=_stamp_lock_holder,
    )


def _acquire_with_jitter(
    lock: FileLock,
    lock_path: Path,
    timeout: float,
    poll_interval: float,
    max_poll_interval: float,
) -> None:
    """Acquires synchronous FileLock using fast non-blocking probe and jittered backoff."""
    try:
        lock.acquire(blocking=False)
    except Timeout:
        logger.info(
            'Lock %s is currently held by another process; waiting up to %.1fs...',
            lock.lock_file,
            timeout,
        )
    else:
        return

    for delay in jittered_backoff_delays(timeout, base=poll_interval, max_sleep=max_poll_interval):
        time.sleep(delay)
        try:
            lock.acquire(blocking=False)
        except Timeout:
            pass
        else:
            return

    raise LockTimeoutError(lock_path=lock_path, timeout=timeout)


async def _async_acquire_with_jitter(
    lock: AsyncFileLock,
    lock_path: Path,
    timeout: float,
    poll_interval: float,
    max_poll_interval: float,
) -> None:
    """Acquires AsyncFileLock using fast non-blocking probe and async jittered backoff."""
    try:
        await lock.acquire(blocking=False)
    except Timeout:
        logger.info(
            'Lock %s is currently held by another process; waiting up to %.1fs...',
            lock.lock_file,
            timeout,
        )
    else:
        return

    for delay in jittered_backoff_delays(timeout, base=poll_interval, max_sleep=max_poll_interval):
        await asyncio.sleep(delay)
        try:
            await lock.acquire(blocking=False)
        except Timeout:
            pass
        else:
            return

    raise LockTimeoutError(lock_path=lock_path, timeout=timeout)


@contextmanager
def state_lock(
    lock_path: Path,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_poll_interval: float = MAX_POLL_INTERVAL_SECONDS,
) -> Iterator[FileLock]:
    """Synchronous lock context manager with fast probe and fallback timeout.

    1. Executes non-blocking probe (blocking=False) to acquire immediately.
    2. If contended, logs INFO and blocks up to timeout using decorrelated jitter backoff.
    3. Raises typed LockTimeoutError upon deadline expiration.
    """
    lock = get_file_lock(lock_path=lock_path, timeout=timeout, poll_interval=poll_interval)
    _acquire_with_jitter(
        lock=lock,
        lock_path=lock_path,
        timeout=timeout,
        poll_interval=poll_interval,
        max_poll_interval=max_poll_interval,
    )
    try:
        yield lock
    finally:
        lock.release()


_ASYNC_TASK_LOCKS: dict[Path, asyncio.Lock] = {}


@asynccontextmanager
async def async_state_lock(
    lock_path: Path,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_poll_interval: float = MAX_POLL_INTERVAL_SECONDS,
) -> AsyncIterator[AsyncFileLock]:
    """Asynchronous lock context manager for non-blocking MCP tool endpoints.

    Provides dual-layer synchronization:
    - In-process coroutine serialization via asyncio.Lock.
    - Cross-process mutual exclusion via AsyncFileLock (OS kernel locks) with decorrelated jitter backoff.
    """
    resolved_path = lock_path.resolve()
    if resolved_path not in _ASYNC_TASK_LOCKS:
        _ASYNC_TASK_LOCKS[resolved_path] = asyncio.Lock()
    task_lock = _ASYNC_TASK_LOCKS[resolved_path]

    lock = get_async_file_lock(lock_path=resolved_path, timeout=timeout, poll_interval=poll_interval)
    try:
        await asyncio.wait_for(task_lock.acquire(), timeout=timeout)
    except TimeoutError as exc:
        raise LockTimeoutError(lock_path=lock_path, timeout=timeout) from exc

    try:
        await _async_acquire_with_jitter(
            lock=lock,
            lock_path=lock_path,
            timeout=timeout,
            poll_interval=poll_interval,
            max_poll_interval=max_poll_interval,
        )
        try:
            yield lock
        finally:
            await lock.release()
    finally:
        task_lock.release()
