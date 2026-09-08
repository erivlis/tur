"""
src/tur/task.py - Task Coordination, Preservation Protocol, and Swarm Management (EP-0147, EP-0149).

Provides structured task handover, in-flight milestone synchronization,
namespaced whiteboard storage (task:<task_id>), dependency resolution (depends_on),
and lease TTL expiration handling.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from tur.session import (
    get_db_connection,
    read_whiteboard_logic,
    write_whiteboard_logic,
)


class WorkItem(BaseModel):
    title: str
    done: bool = False


class ManifestationInfo(BaseModel):
    agent_id: str
    harness: str | None = None
    claimed_at: str | None = None
    completed_at: str | None = None
    lease_ttl_minutes: int = 60


class Task(BaseModel):
    schema_: str = Field(default='https://tur.dev/schemas/task.v1.json', alias='$schema')
    task_id: str
    title: str
    status: Literal['in_progress', 'completed', 'handover', 'blocked', 'abandoned'] = 'in_progress'
    depends_on: list[str] = Field(default_factory=list)
    manifestation: ManifestationInfo | None = None
    objective: str = ''
    work_items: list[WorkItem] = Field(default_factory=list)
    target_files: list[str] = Field(default_factory=list)
    verification_baseline: dict[str, Any] | None = None
    context_breadcrumbs: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.model_dump(by_alias=True, exclude_none=True), indent=indent)


def get_task_key(task_id: str | None) -> str:
    """Returns the whiteboard key for a given task ID."""
    if not task_id or task_id in ('task', 'task_baton', 'default'):
        return 'task'
    if task_id.startswith('task:'):
        return task_id
    if task_id.startswith('baton:'):
        return f'task:{task_id[6:]}'
    return f'task:{task_id}'


def get_task(session_id: str, task_id: str | None = None) -> Task | None:
    """Retrieves a Task from the session whiteboard."""
    key = get_task_key(task_id)
    raw_val = read_whiteboard_logic(session_id, key)

    if not raw_val and key != 'task':
        # Fallback: check legacy baton:<task_id> key if migrating
        if task_id:
            raw_val = read_whiteboard_logic(session_id, f'baton:{task_id}')

    if not raw_val and key != 'task':
        # Fallback: check if the default task or legacy task_baton matches the requested task_id
        for default_k in ('task', 'task_baton'):
            default_val = read_whiteboard_logic(session_id, default_k)
            if default_val:
                try:
                    data = json.loads(default_val)
                    if data.get('task_id') == task_id:
                        return Task.model_validate(data)
                except Exception:
                    pass
        return None

    if not raw_val and key == 'task':
        # Fallback: check legacy task_baton key
        legacy_val = read_whiteboard_logic(session_id, 'task_baton')
        if legacy_val:
            try:
                return Task.model_validate(json.loads(legacy_val))
            except Exception:
                pass
        # Fallback: check if there is an active namespaced task
        tasks = list_tasks(session_id)
        active = [t for t in tasks if t.status == 'in_progress']
        return active[0] if active else (tasks[0] if tasks else None)

    if not raw_val:
        return None

    try:
        data = json.loads(raw_val)
        return Task.model_validate(data)
    except Exception:
        return None


def list_tasks(session_id: str) -> list[Task]:
    """Discovers all tasks registered on the session whiteboard."""
    conn = get_db_connection(session_id)
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT key, value
            FROM session_state
            WHERE key = 'task' OR key = 'task_baton' OR key LIKE 'task:%' OR key LIKE 'baton:%'
            ORDER BY updated_at DESC
            """
        )
        rows = cursor.fetchall()
    conn.close()

    seen_ids: set[str] = set()
    tasks: list[Task] = []

    for row in rows:
        val = row['value']
        try:
            data = json.loads(val)
            task = Task.model_validate(data)
            if task.task_id not in seen_ids:
                seen_ids.add(task.task_id)
                tasks.append(task)
        except Exception:
            continue

    return tasks


def is_lease_expired(task: Task, session_id: str) -> bool:
    """Checks if the task's manifestation lease has expired."""
    if task.status != 'in_progress' or not task.manifestation or not task.manifestation.claimed_at:
        return False

    try:
        claimed_dt = datetime.fromisoformat(task.manifestation.claimed_at.replace('Z', '+00:00'))
    except Exception:
        return False

    ttl_minutes = task.manifestation.lease_ttl_minutes or 60
    expiry_time = claimed_dt + timedelta(minutes=ttl_minutes)

    if datetime.now(UTC) <= expiry_time:
        return False

    # Check agent heartbeat in SQLite if available
    agent_id = task.manifestation.agent_id
    conn = get_db_connection(session_id)
    with conn:
        cursor = conn.cursor()
        cursor.execute('SELECT last_heartbeat FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
    conn.close()

    if row and row['last_heartbeat']:
        try:
            hb_dt = datetime.fromisoformat(str(row['last_heartbeat']).replace('Z', '+00:00'))
            if datetime.now(UTC) <= hb_dt + timedelta(minutes=ttl_minutes):
                return False
        except Exception:
            pass

    return True


def check_dependencies(depends_on: list[str], session_id: str) -> tuple[bool, list[str]]:
    """
    Checks whether all prerequisite task IDs are in 'completed' status.
    Returns (all_met, list_of_unmet_ids).
    """
    if not depends_on:
        return True, []

    tasks = list_tasks(session_id)
    completed_ids = {t.task_id for t in tasks if t.status == 'completed'}
    unmet = [dep for dep in depends_on if dep not in completed_ids]
    return len(unmet) == 0, unmet


def save_task(session_id: str, task: Task, updated_by: str) -> None:
    """Persists a Task to the session whiteboard under namespaced and default keys."""
    namespaced_key = get_task_key(task.task_id)
    payload = task.to_json()

    # Always write to the namespaced coordinate
    write_whiteboard_logic(session_id, namespaced_key, payload, updated_by)

    # Mirror to default task key if active or default
    current_default = read_whiteboard_logic(session_id, 'task') or read_whiteboard_logic(session_id, 'task_baton')
    should_mirror = True
    if current_default:
        try:
            def_data = json.loads(current_default)
            # Only mirror if default is empty, or matches this task, or this task is newly in_progress
            if (
                def_data.get('task_id')
                and def_data.get('task_id') != task.task_id
                and def_data.get('status') == 'in_progress'
                and task.status != 'in_progress'
            ):
                should_mirror = False
        except Exception:
            pass

    if should_mirror:
        write_whiteboard_logic(session_id, 'task', payload, updated_by)


def claim_task(
    session_id: str,
    task_id: str,
    title: str,
    agent_id: str,
    harness: str | None = None,
    objective: str = '',
    work_items: list[str] | None = None,
    target_files: list[str] | None = None,
    depends_on: list[str] | None = None,
    lease_ttl_minutes: int = 60,
    force: bool = False,
) -> Task:
    """Claims a task for a manifestation."""
    existing = get_task(session_id, task_id)
    if (
        existing
        and existing.status == 'in_progress'
        and not force
        and existing.manifestation
        and existing.manifestation.agent_id != agent_id
        and not is_lease_expired(existing, session_id)
    ):
        raise ValueError(
            f"TaskConflictError: Task '{task_id}' is currently claimed by "
            f"'{existing.manifestation.agent_id}' (lease active). Pass force=True to reclaim."
        )

    deps = depends_on if depends_on is not None else (existing.depends_on if existing else [])
    all_met, _ = check_dependencies(deps, session_id)
    initial_status: Literal['in_progress', 'blocked'] = 'in_progress' if all_met else 'blocked'

    items: list[WorkItem] = []
    if work_items:
        items = [WorkItem(title=w, done=False) for w in work_items]
    elif existing and existing.work_items:
        items = existing.work_items

    now_iso = datetime.now(UTC).isoformat()
    manifestation = ManifestationInfo(
        agent_id=agent_id,
        harness=harness,
        claimed_at=now_iso,
        lease_ttl_minutes=lease_ttl_minutes,
    )

    task = Task(
        task_id=task_id,
        title=title or (existing.title if existing else task_id),
        status=initial_status,
        depends_on=deps,
        manifestation=manifestation,
        objective=objective or (existing.objective if existing else ''),
        work_items=items,
        target_files=target_files if target_files is not None else (existing.target_files if existing else []),
        verification_baseline=existing.verification_baseline if existing else None,
        context_breadcrumbs=existing.context_breadcrumbs if existing else [],
        recommendations=existing.recommendations if existing else [],
    )

    save_task(session_id, task, updated_by=agent_id)
    return task


def check_item(
    session_id: str,
    item_identifier: int | str,
    task_id: str | None = None,
    done: bool = True,
    updated_by: str = 'agent',
) -> Task:
    """Marks a checklist item as completed (done=True) or undone."""
    task = get_task(session_id, task_id)
    if not task:
        raise FileNotFoundError(f"No task found matching '{task_id or 'default'}'")

    matched = False
    # If integer (1-based or 0-based)
    if isinstance(item_identifier, int) or (isinstance(item_identifier, str) and item_identifier.isdigit()):
        idx = int(item_identifier)
        # Check if 1-based index
        if 1 <= idx <= len(task.work_items):
            task.work_items[idx - 1].done = done
            matched = True
        elif 0 <= idx < len(task.work_items):
            task.work_items[idx].done = done
            matched = True
    else:
        # String match by substring / exact match
        target_lower = str(item_identifier).lower()
        for item in task.work_items:
            if target_lower in item.title.lower():
                item.done = done
                matched = True
                break

    if not matched:
        raise ValueError(f"Work item '{item_identifier}' not found in task '{task.task_id}'")

    save_task(session_id, task, updated_by=updated_by)
    return task


def yield_task(
    session_id: str,
    task_id: str | None = None,
    note: str | None = None,
    updated_by: str = 'agent',
) -> Task:
    """Hands over an active task without marking it completed."""
    task = get_task(session_id, task_id)
    if not task:
        raise FileNotFoundError(f"No task found matching '{task_id or 'default'}'")

    task.status = 'handover'
    if note:
        task.context_breadcrumbs.append(f'Handover note ({datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}): {note}')

    save_task(session_id, task, updated_by=updated_by)
    return task


# Canonical alias
handover_task = yield_task


def seal_task(
    session_id: str,
    task_id: str | None = None,
    updated_by: str = 'agent',
) -> Task:
    """Marks a task as completed and unblocks dependent tasks."""
    task = get_task(session_id, task_id)
    if not task:
        raise FileNotFoundError(f"No task found matching '{task_id or 'default'}'")

    task.status = 'completed'
    if task.manifestation:
        task.manifestation.completed_at = datetime.now(UTC).isoformat()

    save_task(session_id, task, updated_by=updated_by)

    # Check and unblock dependent tasks in the session
    all_tasks = list_tasks(session_id)
    for other in all_tasks:
        if other.status == 'blocked' and task.task_id in other.depends_on:
            all_met, _ = check_dependencies(other.depends_on, session_id)
            if all_met:
                other.status = 'in_progress'
                save_task(session_id, other, updated_by=updated_by)

    return task


# Canonical alias
complete_task = seal_task
