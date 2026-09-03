import math
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal

from tur.models import Memory, MemoryDecay, MemoryProvenance, MemoryType
from tur.paths import resolve_workspace_dir

# Default half-life (in days) and commit distance sensitivity lambda (EP-0131)
DEFAULT_DECAY_POLICIES: dict[MemoryType, tuple[float | None, float]] = {
    MemoryType.AXIOM: (None, 0.0),
    MemoryType.CORE: (None, 0.0),
    MemoryType.INSIGHT: (90.0, 0.01),
    MemoryType.PREFERENCE: (180.0, 0.0),
    MemoryType.FACT: (14.0, 0.05),
    MemoryType.EVENT: (30.0, 0.02),
}

DEFAULT_STALENESS_THRESHOLD: float = 0.3
DEFAULT_COMMIT_DRIFT_THRESHOLD: int = 20


def get_git_head_sha(repo_dir: Path | None = None, short: bool = True) -> str | None:
    """
    Returns the current Git HEAD commit SHA for the repository, or None if not a Git repository.
    """
    if not shutil.which('git'):
        return None

    target_dir = repo_dir or resolve_workspace_dir() or Path.cwd()
    cmd = ['git', 'rev-parse', '--short=12' if short else 'HEAD', 'HEAD']
    try:
        res = subprocess.run(
            cmd,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            sha = res.stdout.strip()
            return sha if sha else None
    except Exception:
        pass
    return None


def get_git_commit_distance(from_sha: str, to_sha: str = 'HEAD', repo_dir: Path | None = None) -> int:
    """
    Returns the number of commits between from_sha and to_sha (exclusive of from_sha, inclusive of to_sha).
    Returns 0 if from_sha is not found or if not inside a Git repository.
    """
    if not from_sha or not shutil.which('git'):
        return 0

    target_dir = repo_dir or resolve_workspace_dir() or Path.cwd()
    cmd = ['git', 'rev-list', '--count', f'{from_sha}..{to_sha}']
    try:
        res = subprocess.run(
            cmd,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            val = res.stdout.strip()
            if val.isdigit():
                return int(val)
    except Exception:
        pass
    return 0


def is_git_file_modified_or_deleted(
    file_ref: str,
    since_sha: str | None = None,
    repo_dir: Path | None = None,
) -> bool:
    """
    Checks whether a referenced file has been modified or deleted in the working tree or since since_sha.
    file_ref may be formatted as 'path/to/file.py' or 'path/to/file.py#L10-L20'.
    """
    # Strip line range annotations if present
    clean_path_str = file_ref.split('#', 1)[0].strip()
    if not clean_path_str:
        return False

    target_dir = repo_dir or resolve_workspace_dir() or Path.cwd()
    file_path = Path(clean_path_str)
    if not file_path.is_absolute():
        file_path = target_dir / file_path

    # Check existence on disk
    if not file_path.exists():
        return True

    if not shutil.which('git'):
        return False

    try:
        # Check if modified in working directory
        res_worktree = subprocess.run(
            ['git', 'status', '--porcelain', '--', clean_path_str],
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res_worktree.returncode == 0 and res_worktree.stdout.strip():
            return True

        # If since_sha is provided, check diff since commit
        if since_sha:
            res_diff = subprocess.run(
                ['git', 'diff', '--name-only', f'{since_sha}..HEAD', '--', clean_path_str],
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if res_diff.returncode == 0 and res_diff.stdout.strip():
                return True
    except Exception:
        pass

    return False


def create_provenance_and_decay(
    memory_type: MemoryType,
    confidence: float = 1.0,
    context_ref: str | None = None,
    source_agent: str | None = None,
    source_harness: str | None = None,
    observed_at: datetime | None = None,
    repo_dir: Path | None = None,
) -> tuple[MemoryProvenance, MemoryDecay]:
    """
    Factory creating linked MemoryProvenance and MemoryDecay objects with type-appropriate defaults.
    """
    now = observed_at or datetime.now()
    git_sha = get_git_head_sha(repo_dir)

    provenance = MemoryProvenance(
        observed_at=now,
        git_sha=git_sha,
        source_agent=source_agent,
        source_harness=source_harness,
        context_ref=context_ref,
    )

    half_life, _ = DEFAULT_DECAY_POLICIES.get(memory_type, (14.0, 0.05))

    if memory_type in (MemoryType.AXIOM, MemoryType.CORE) or git_sha is not None:
        staleness_status = 'fresh'
    else:
        staleness_status = 'unanchored'

    decay = MemoryDecay(
        half_life_days=half_life,
        last_verified_at=now,
        staleness_status=staleness_status,
    )

    return provenance, decay


def compute_epistemic_weight(
    memory: Memory,
    repo_dir: Path | None = None,
    now: datetime | None = None,
) -> float:
    """
    Computes the current epistemic weight of a memory using exponential half-life decay and Git commit sensitivity:
        Weight(t, Delta_commits) = confidence * 2^(-t / t_1/2) * e^(-lambda * Delta_commits)

    Legacy memories lacking decay configuration default to infinite half-life (EP-0131 Backwards Compatibility).
    """
    if memory.status == 'falsified':
        return 0.0

    if memory.decay and memory.decay.staleness_status == 'refuted':
        return 0.0

    # Axiom and Core memories do not decay
    if memory.type in (MemoryType.AXIOM, MemoryType.CORE):
        return max(0.0, min(1.0, memory.confidence))

    current_time = now or datetime.now()
    half_life = memory.decay.half_life_days if memory.decay else None
    last_verified = memory.decay.last_verified_at if memory.decay else memory.timestamp

    # Time decay component (infinite half-life if decay is None or half_life_days is None)
    if half_life is not None and half_life > 0:
        elapsed_seconds = max(0.0, (current_time - last_verified).total_seconds())
        elapsed_days = elapsed_seconds / 86400.0
        time_decay = 2.0 ** (-elapsed_days / half_life)
    else:
        time_decay = 1.0

    # Git commit distance component
    commit_decay = 1.0
    _, lambda_default = DEFAULT_DECAY_POLICIES.get(memory.type, (14.0, 0.05))
    if memory.provenance and memory.provenance.git_sha and lambda_default > 0.0:
        delta_commits = get_git_commit_distance(memory.provenance.git_sha, repo_dir=repo_dir)
        commit_decay = math.exp(-lambda_default * delta_commits)

    total_weight = memory.confidence * time_decay * commit_decay
    return max(0.0, min(1.0, total_weight))


def evaluate_staleness(
    memory: Memory,
    repo_dir: Path | None = None,
    now: datetime | None = None,
    staleness_threshold: float = DEFAULT_STALENESS_THRESHOLD,
    commit_drift_threshold: int = DEFAULT_COMMIT_DRIFT_THRESHOLD,
) -> tuple[Literal['fresh', 'stale', 'unanchored', 'refuted'], str | None]:
    """
    Evaluates the staleness status and diagnostics for an L1 memory record.
    Returns (status, reason_diagnostic).
    """
    if memory.status == 'falsified' or (memory.decay and memory.decay.staleness_status == 'refuted'):
        return 'refuted', 'Memory is marked refuted/falsified'

    if memory.type in (MemoryType.AXIOM, MemoryType.CORE):
        return 'fresh', None

    # Check context ref file modification/deletion
    if (
        memory.provenance
        and memory.provenance.context_ref
        and is_git_file_modified_or_deleted(
            memory.provenance.context_ref,
            since_sha=memory.provenance.git_sha,
            repo_dir=repo_dir,
        )
    ):
        clean_ref = memory.provenance.context_ref.split('#', 1)[0]
        return 'stale', f"Referenced file '{clean_ref}' was modified or deleted"

    # Check Git commit drift distance
    if memory.provenance and memory.provenance.git_sha:
        commits = get_git_commit_distance(memory.provenance.git_sha, repo_dir=repo_dir)
        if commits > commit_drift_threshold:
            return 'stale', f'Commit drift: {commits} commits since observation (>{commit_drift_threshold})'

    if memory.decay and memory.decay.half_life_days is not None:
        weight = compute_epistemic_weight(memory, repo_dir=repo_dir, now=now)
        if weight < staleness_threshold:
            return 'stale', f'Epistemic weight decayed below threshold ({weight:.2f} < {staleness_threshold})'

    if memory.provenance is None or memory.provenance.git_sha is None:
        return 'unanchored', 'Memory lacks Git commit anchor'

    return 'fresh', None
