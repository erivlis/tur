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
import socket
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from filelock import AsyncFileLock, FileLock, Timeout

logger = logging.getLogger(__name__)

# Polling and Timeout Constants
DEFAULT_POLL_INTERVAL_SECONDS: float = 0.005  # 5ms fast probe eliminates latency quantization
FAST_LOCK_TIMEOUT_SECONDS: float = 3.0  # Interactive state mutations (session notes, telemetry)
HEAVY_LOCK_TIMEOUT_SECONDS: float = 30.0  # Storage migrations and Merkle graph compaction
DEFAULT_LOCK_TIMEOUT_SECONDS: float = FAST_LOCK_TIMEOUT_SECONDS


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


@contextmanager
def state_lock(
    lock_path: Path,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> Iterator[FileLock]:
    """Synchronous lock context manager with fast probe and fallback timeout.

    1. Executes non-blocking probe (blocking=False) to acquire immediately.
    2. If contended, logs INFO and blocks up to timeout with fast polling.
    3. Stretches exception to typed LockTimeoutError upon deadline expiration.
    """
    lock = get_file_lock(lock_path=lock_path, timeout=timeout, poll_interval=poll_interval)

    # 1. Fast probe: Check if immediately available without waiting
    try:
        lock.acquire(blocking=False)
    except Timeout:
        logger.info(
            'Lock %s is currently held by another process; waiting up to %.1fs...',
            lock.lock_file,
            timeout,
        )
        try:
            # 2. Block with deadline
            lock.acquire(timeout=timeout, poll_interval=poll_interval)
        except Timeout as exc:
            raise LockTimeoutError(lock_path=lock_path, timeout=timeout) from exc

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
) -> AsyncIterator[AsyncFileLock]:
    """Asynchronous lock context manager for non-blocking MCP tool endpoints.

    Provides dual-layer synchronization:
    - In-process coroutine serialization via asyncio.Lock.
    - Cross-process mutual exclusion via AsyncFileLock (OS kernel locks).
    """
    resolved_path = lock_path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    if resolved_path not in _ASYNC_TASK_LOCKS:
        _ASYNC_TASK_LOCKS[resolved_path] = asyncio.Lock()
    task_lock = _ASYNC_TASK_LOCKS[resolved_path]

    lock = AsyncFileLock(
        str(resolved_path),
        timeout=timeout,
        poll_interval=poll_interval,
        is_singleton=True,
        preserve_lock_file=True,
        close_error_policy='suppress',
        on_acquired=_stamp_lock_holder,
    )
    try:
        await asyncio.wait_for(task_lock.acquire(), timeout=timeout)
    except TimeoutError as exc:
        raise LockTimeoutError(lock_path=lock_path, timeout=timeout) from exc

    try:
        try:
            async with lock:
                yield lock
        except Timeout as exc:
            raise LockTimeoutError(lock_path=lock_path, timeout=timeout) from exc
    finally:
        task_lock.release()
