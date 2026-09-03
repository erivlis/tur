import contextlib
import functools
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar, cast
from uuid import UUID

import yaml

from tur._helpers import yaml_safe_load
from tur.locking import FAST_LOCK_TIMEOUT_SECONDS, state_lock
from tur.memory import MemoryManager
from tur.models import (
    MemoryType,
    Note,
    Persona,
    SessionEntry,
    SessionIndex,
    SessionNotes,
    SessionState,
    SystemState,
)
from tur.paths import is_global_path, resolve_workspace_dir
from tur.persona import get_active_persona_id, get_persona_path, load_persona
from tur.user import get_user_profile
from tur.vector_clock import VectorClock


def get_local_persona_dir(persona_dir: Path, workspace_dir: Path | None = None) -> Path:
    """
    Returns the project-local persona directory path for runtime state (sessions, notes).

    When *persona_dir* is a global path (~/.tur/...) the corresponding local mirror
    under the resolved workspace directory is returned. This function is a pure query —
    it does NOT create directories. Call ensure_local_persona_dir() when you need
    the directory to actually exist on disk.
    """
    if is_global_path(persona_dir):
        ws = workspace_dir or resolve_workspace_dir() or Path.cwd()
        return ws / '.tur' / 'personas' / persona_dir.name
    return persona_dir


def ensure_local_persona_dir(persona_dir: Path, workspace_dir: Path | None = None) -> Path:
    """
    Returns the project-local persona directory, creating it on disk if necessary.

    Use this instead of get_local_persona_dir() when you are about to write files
    into the directory. Callers that only *read* should use the pure getter.
    """
    local_dir = get_local_persona_dir(persona_dir, workspace_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    # Ensure .tur/.gitignore ignores lock files
    try:
        ws = workspace_dir or resolve_workspace_dir() or Path.cwd()
        tur_dir = ws / '.tur'
        if tur_dir.exists() and tur_dir.is_dir():
            gitignore = tur_dir / '.gitignore'
            content = gitignore.read_text(encoding='utf-8') if gitignore.exists() else ''
            rules = [r.strip() for r in content.splitlines() if r.strip()]
            needed = ['.locks/', '*.lock']
            added = False
            for n in needed:
                if n not in rules:
                    rules.append(n)
                    added = True
            if added:
                gitignore.write_text('\n'.join(rules) + '\n', encoding='utf-8')
    except Exception:
        pass

    return local_dir


def load_session_index(persona_dir: Path) -> SessionIndex:
    """Loads the session index from sessions.yaml or returns an empty index."""
    index_path = get_local_persona_dir(persona_dir) / 'sessions.yaml'  # read-only path query
    if index_path.exists():
        with open(index_path, encoding='utf-8') as f:
            try:
                data: dict = yaml_safe_load(f) or {}
                return SessionIndex(**data)
            except Exception:
                pass
    return SessionIndex(active_session_id=None, sessions=[])


def atomic_yaml_write(target_path: Path, data: Any) -> None:
    """Atomically write YAML data to target_path using tempfile and os.replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target_path.with_name(f'.tmp_{uuid.uuid4().hex}_{target_path.name}')
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        os.replace(temp_file, target_path)
    finally:
        with contextlib.suppress(OSError):
            if temp_file.exists():
                temp_file.unlink()


def save_session_index(persona_dir: Path, index: SessionIndex):
    """Saves the session index to sessions.yaml atomically."""
    index_path = ensure_local_persona_dir(persona_dir) / 'sessions.yaml'
    atomic_yaml_write(index_path, index.model_dump(mode='json'))


SESSION_ID_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')


def validate_session_id(session_id: str) -> None:
    """Validates that a session_id conforms to safe alphanumeric format and prevents path traversal (EP-0130)."""
    if not session_id or not SESSION_ID_REGEX.match(session_id):
        raise ValueError(f"Invalid session_id format: '{session_id}'. Must match ^[a-zA-Z0-9_-]+$")


def get_parent_session_id(session_id: str | None, persona_dir: Path | None = None) -> str | None:
    """
    Returns the parent session ID in the lineage DAG for the given session ID (EP-0130).
    Checks both the session flat YAML file and sessions.yaml index.
    """
    if not session_id:
        return None
    validate_session_id(session_id)
    if persona_dir is None:
        active_id = get_active_persona_id()
        persona_dir = get_persona_path(active_id)

    # Check session YAML first
    session_file = get_session_file(persona_dir, session_id)
    if session_file.exists():
        try:
            with open(session_file, encoding='utf-8') as f:
                notes_data = yaml_safe_load(f)
            if notes_data and isinstance(notes_data, dict):
                parent_id = notes_data.get('parent_session_id')
                if parent_id:
                    return str(parent_id)
        except Exception:
            pass

    # Fallback to session index
    index = load_session_index(persona_dir)
    for entry in index.sessions:
        if entry.id == session_id and entry.parent_session_id:
            return entry.parent_session_id

    return None


def get_session_lineage(session_id: str, persona_dir: Path | None = None, max_depth: int = 10) -> list[str]:
    """
    Traverses parent_session_id pointers up the DAG to return the lineage sequence:
    [session_id, parent_id, grandparent_id, ...] up to max_depth (EP-0130).
    Guards against cyclic loops via a visited set.
    """
    validate_session_id(session_id)
    if persona_dir is None:
        active_id = get_active_persona_id()
        persona_dir = get_persona_path(active_id)

    lineage: list[str] = [session_id]
    visited: set[str] = {session_id}
    curr = session_id

    while len(lineage) < max_depth:
        parent = get_parent_session_id(curr, persona_dir)
        if not parent or parent in visited:
            break
        visited.add(parent)
        lineage.append(parent)
        curr = parent

    return lineage


def get_session_file(persona_dir: Path, session_id: str) -> Path:
    """Returns the flat YAML file path for a session: sessions/<session_id>.yaml"""
    validate_session_id(session_id)
    return get_local_persona_dir(persona_dir) / 'sessions' / f'{session_id}.yaml'  # read-only path query


def load_system_state(workspace_dir: Path | None = None) -> SystemState:
    """Load SystemState from .tur/state.yaml or return a default empty SystemState."""
    ws = workspace_dir or resolve_workspace_dir()
    state_path = (ws / '.tur' / 'state.yaml') if ws is not None else Path('.tur/state.yaml')
    if state_path.exists():
        try:
            with open(state_path, encoding='utf-8') as f:
                state_data = yaml_safe_load(f)
            if state_data:
                return SystemState(**state_data)
        except Exception:
            pass
    return SystemState()


def save_system_state(state: SystemState, workspace_dir: Path | None = None) -> None:
    """Save SystemState atomically to .tur/state.yaml."""
    ws = workspace_dir or resolve_workspace_dir() or Path.cwd()
    state_path = ws / '.tur' / 'state.yaml'
    atomic_yaml_write(state_path, state.model_dump(mode='json'))


def update_system_state(
    active_persona_id: UUID | str | None = None,
    active_session_id: str | None = None,
    reset_session: bool = False,
    workspace_dir: Path | None = None,
) -> SystemState:
    """Atomically update and save SystemState."""
    state = load_system_state(workspace_dir)
    if active_persona_id is not None:
        state.active_persona_id = UUID(str(active_persona_id))
    if reset_session:
        state.active_session_id = None
    elif active_session_id is not None:
        state.active_session_id = active_session_id
    save_system_state(state, workspace_dir)
    return state


def get_active_session_id(workspace_dir: Path | None = None) -> str | None:
    """
    Resolves the active session ID.
    - Checks env var `TUR_ACTIVE_SESSION_ID`.
    - Checks `active_session_id` in `.tur/state.yaml`.
    """
    env_id = os.environ.get('TUR_ACTIVE_SESSION_ID')
    if env_id:
        return env_id
    return load_system_state(workspace_dir).active_session_id


def compile_session_notes(persona_dir: Path, session_id: str | None) -> str:
    """
    Returns the content of the most recent note in the session's flat YAML file,
    or the default axiom if no notes are found.
    """
    if not session_id:
        return 'Status: Conserved. Aleph: Restored. Carry on, Lion.'

    session_file = get_session_file(persona_dir, session_id)

    if session_file.exists():
        try:
            with open(session_file, encoding='utf-8') as f:
                notes_data = yaml_safe_load(f)
            session_notes = SessionNotes(**notes_data)
            if session_notes.notes:
                sorted_notes = sorted(session_notes.notes, key=lambda x: x.timestamp, reverse=True)
                return sorted_notes[0].content.strip()
        except Exception:
            pass

    return 'Status: Conserved. Aleph: Restored. Carry on, Lion.'


def hydrate_session_state(
    active_id: str,
    session_id: str | None = None,
    include_stale: bool = False,
) -> SessionState:
    """Hydrates the full SessionState (Persona, User, Memories, Epilogue) from the filesystem."""
    persona_dir = get_persona_path(active_id)
    persona = load_persona(persona_dir)
    user = get_user_profile()
    memory_manager = MemoryManager(base_dir=persona_dir)
    all_memories = memory_manager.load_all()
    cores = [m for m in all_memories if m.type == MemoryType.CORE and m.status == 'active']

    if include_stale:
        memories = [m for m in all_memories if m.type != MemoryType.CORE]
    else:
        from tur.provenance import evaluate_staleness

        memories = []
        for m in all_memories:
            if m.type == MemoryType.CORE:
                continue
            st, _ = evaluate_staleness(m)
            if st != 'stale' and st != 'refuted':
                memories.append(m)

    resolved_session_id = session_id or get_active_session_id()

    if resolved_session_id:
        epilogue_content = compile_session_notes(persona_dir, resolved_session_id)
    else:
        # Fall back to resolving the most recently updated session
        index = load_session_index(persona_dir)
        if index.sessions:
            sorted_sessions = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)
            epilogue_content = compile_session_notes(persona_dir, sorted_sessions[0].id)
        else:
            epilogue_content = compile_session_notes(persona_dir, None)

    kg_path = persona_dir / 'knowledge_graph.yaml'
    kg_data = None
    if kg_path.exists():
        try:
            with open(kg_path, encoding='utf-8') as f:
                kg_data = yaml_safe_load(f)
        except Exception:
            pass

    return SessionState(
        persona=persona,
        user=user,
        memories=memories,
        cores=cores,
        epilogue=epilogue_content,
        knowledge_graph=kg_data,
    )


F = TypeVar('F', bound=Callable[..., Any])


def db_retry(max_retries: int = 5, initial_delay: float = 0.05, backoff_factor: float = 2.0) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_err = None
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e).lower() or 'busy' in str(e).lower():
                        last_err = e
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise
            raise last_err or sqlite3.OperationalError('Database busy timeout exceeded.')

        return cast(F, wrapper)

    return decorator


def get_session_db(session_id: str) -> Path:
    """Resolves and returns the path to the SQLite session database, ensuring parent dirs exist."""
    ws = resolve_workspace_dir() or Path.cwd()
    db_dir = ws / '.tur' / 'sessions' / session_id
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / 'session.db'


def get_db_connection(session_id: str) -> sqlite3.Connection:
    db_path = get_session_db(session_id)
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
    conn.execute('PRAGMA busy_timeout = 5000;')
    return conn


def init_db(conn: sqlite3.Connection):
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS agents
                 (
                     id
                     TEXT
                     PRIMARY
                     KEY,
                     harness
                     TEXT
                     NOT
                     NULL,
                     substrate
                     TEXT
                     NOT
                     NULL,
                     status
                     TEXT
                     NOT
                     NULL
                     CHECK (
                     status
                     IN
                 (
                     'active',
                     'idle',
                     'sleeping',
                     'stale'
                 )),
                     last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     run_token TEXT NOT NULL,
                     joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     vector_clock TEXT NOT NULL DEFAULT '{}'
                     );
                 """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS signals
                 (
                     id
                     TEXT
                     NOT
                     NULL
                     UNIQUE,
                     sequence
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     timestamp
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP,
                     sender
                     TEXT
                     NOT
                     NULL,
                     recipient
                     TEXT
                     NOT
                     NULL,
                     type
                     TEXT
                     NOT
                     NULL
                     CHECK (
                     type
                     IN
                 (
                     'inform',
                     'query',
                     'delegate',
                     'ack',
                     'warn',
                     'sleep_event',
                     'sleep_request'
                 )
                     ),
                     content TEXT NOT NULL,
                     vector_clock TEXT NOT NULL DEFAULT '{}'
                     );
                 """)

    # Schema migration checks (EP-0141)
    try:
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(agents);')
        agent_cols = [row[1] for row in cursor.fetchall()]
        if agent_cols and 'vector_clock' not in agent_cols:
            conn.execute("ALTER TABLE agents ADD COLUMN vector_clock TEXT NOT NULL DEFAULT '{}';")

        cursor.execute('PRAGMA table_info(signals);')
        signal_cols = [row[1] for row in cursor.fetchall()]
        if signal_cols and 'vector_clock' not in signal_cols:
            conn.execute("ALTER TABLE signals ADD COLUMN vector_clock TEXT NOT NULL DEFAULT '{}';")
    except Exception:
        pass
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS signal_reads
                 (
                     signal_id
                     TEXT
                     NOT
                     NULL,
                     agent_id
                     TEXT
                     NOT
                     NULL,
                     read_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP,
                     PRIMARY
                     KEY
                 (
                     signal_id,
                     agent_id
                 ),
                     FOREIGN KEY
                 (
                     signal_id
                 ) REFERENCES signals
                 (
                     id
                 ) ON DELETE CASCADE,
                     FOREIGN KEY
                 (
                     agent_id
                 ) REFERENCES agents
                 (
                     id
                 )
                   ON DELETE CASCADE
                     );
                 """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS session_state
                 (
                     key
                     TEXT
                     PRIMARY
                     KEY,
                     value
                     TEXT
                     NOT
                     NULL,
                     updated_by
                     TEXT
                     NOT
                     NULL,
                     updated_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 );
                 """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS staged_memories
                 (
                     id
                     TEXT
                     PRIMARY
                     KEY,
                     agent_id
                     TEXT
                     NOT
                     NULL,
                     memory_data
                     TEXT
                     NOT
                     NULL,
                     created_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 );
                 """)


@db_retry()
def update_heartbeat(session_id: str, agent_id: str):
    """Refreshes the last_heartbeat timestamp for the agent in the registry."""
    run_token = os.environ.get('TUR_RUN_TOKEN', 'ambient_cli')
    conn = get_db_connection(session_id)
    with conn:
        conn.execute(
            """
            UPDATE agents
            SET last_heartbeat = CURRENT_TIMESTAMP
            WHERE id = ?
              AND (run_token = ? OR status != 'active')
            """,
            (agent_id, run_token),
        )
    conn.close()


def get_agent_vector_clock(conn: sqlite3.Connection, agent_id: str) -> VectorClock:
    """Retrieves the Lamport Vector Clock for a specific agent (EP-0141)."""
    cursor = conn.cursor()
    cursor.execute('SELECT vector_clock FROM agents WHERE id = ?', (agent_id,))
    row = cursor.fetchone()
    if row and row['vector_clock']:
        return VectorClock(row['vector_clock'])
    return VectorClock()


def update_agent_vector_clock(conn: sqlite3.Connection, agent_id: str, clock: dict[str, int]) -> None:
    """Updates the Lamport Vector Clock for an agent (EP-0141)."""
    clock_json = json.dumps(clock)
    conn.execute(
        'UPDATE agents SET vector_clock = ? WHERE id = ?',
        (clock_json, agent_id),
    )


def start_session_logic(
    session_id: str,
    agent_id: str | None = None,
    harness_conversation_id: str | None = None,
    identifier: str | None = None,
    previous_session_id: str | None = None,
) -> str:
    """
    Creates the flat session YAML file and sets up/registers the manifestation
    in the session SQLite database.
    """
    validate_session_id(session_id)
    if previous_session_id:
        validate_session_id(previous_session_id)

    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    # Backwards compatibility flat file setup
    session_lock = ensure_local_persona_dir(persona_dir) / '.locks' / 'session.lock'
    with state_lock(session_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS):
        sessions_dir = ensure_local_persona_dir(persona_dir) / 'sessions'
        sessions_dir.mkdir(parents=True, exist_ok=True)
        session_file = get_session_file(persona_dir, session_id)

        index = load_session_index(persona_dir)

        # EP-0130: Resolve parent session ID
        parent_id = previous_session_id
        if not parent_id and index.sessions:
            prior_sessions = [s for s in index.sessions if s.id != session_id]
            if prior_sessions:
                sorted_prior = sorted(
                    prior_sessions,
                    key=lambda s: (s.updated_at, s.created_at, s.id),
                    reverse=True,
                )
                parent_id = sorted_prior[0].id

        if not session_file.exists():
            seed_content = 'Session started.'
            if parent_id:
                # Continuity Staleness TTL: only auto-seed if parent was updated within 48h (or explicitly passed)
                parent_entry = next((s for s in index.sessions if s.id == parent_id), None)
                is_fresh = True
                if parent_entry and previous_session_id is None:
                    is_fresh = (datetime.now() - parent_entry.updated_at).total_seconds() <= 48 * 3600

                if is_fresh:
                    prev_content = compile_session_notes(persona_dir, parent_id)
                    if prev_content and prev_content != 'Status: Conserved. Aleph: Restored. Carry on, Lion.':
                        # Clamp auto-seeded spark to 256 characters (EP-0130)
                        seed_content = prev_content[:256].strip()

            session_notes = SessionNotes(
                session_id=session_id,
                parent_session_id=parent_id,
                notes=[Note(timestamp=datetime.now(), content=seed_content)],
            )
            atomic_yaml_write(session_file, session_notes.model_dump(mode='json'))

        index.active_session_id = session_id

        existing_entry = next((s for s in index.sessions if s.id == session_id), None)
        if existing_entry:
            existing_entry.updated_at = datetime.now()
            existing_entry.status = 'active'
            if parent_id and not existing_entry.parent_session_id:
                existing_entry.parent_session_id = parent_id
        else:
            new_entry = SessionEntry(id=session_id, parent_session_id=parent_id, status='active')
            index.sessions.append(new_entry)

        save_session_index(persona_dir, index)

        update_system_state(active_persona_id=active_id, active_session_id=session_id)

    # SQLite Database Multi-manifestation initialization
    model_slug = os.environ.get('TUR_MODEL_SLUG', 'agent')
    resolved_harness_conv_id = harness_conversation_id or os.environ.get('TUR_HARNESS_CONVERSATION_ID')
    if not resolved_harness_conv_id:
        resolved_harness_conv_id = str(uuid.uuid4())

    if not agent_id:
        conv_hash = hashlib.sha256(resolved_harness_conv_id.encode()).hexdigest()[:8]
        random_hex = uuid.uuid4().hex[:4]
        agent_id = f'{model_slug}_{conv_hash}_{random_hex}'

    # Sanitization validation
    if not re.match(r'^[a-zA-Z0-9_\.-]+$', agent_id):
        raise ValueError(f"Invalid agent_id format: '{agent_id}'. Must match ^[a-zA-Z0-9_\\.-]+$")

    run_token = os.environ.get('TUR_RUN_TOKEN') or str(uuid.uuid4())
    os.environ['TUR_AGENT_ID'] = agent_id
    os.environ['TUR_RUN_TOKEN'] = run_token

    harness_name = os.environ.get('TUR_HARNESS', 'terminal')
    substrate_name = os.environ.get('TUR_SUBSTRATE', 'local')

    conn = get_db_connection(session_id)
    init_db(conn)

    with conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status, last_heartbeat, run_token FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
        if row:
            status, _last_heartbeat, stored_token = row['status'], row['last_heartbeat'], row['run_token']
            if status == 'active':
                if stored_token == run_token:
                    cursor.execute(
                        """
                        UPDATE agents
                        SET last_heartbeat = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (agent_id,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT (strftime('%s', 'now') - strftime('%s', last_heartbeat)) as diff
                        FROM agents
                        WHERE id = ?
                        """,
                        (agent_id,),
                    )
                    diff_row = cursor.fetchone()
                    diff = diff_row['diff'] if diff_row else 9999

                    if diff > 15:
                        cursor.execute(
                            """
                            UPDATE agents
                            SET status         = 'active',
                                last_heartbeat = CURRENT_TIMESTAMP,
                                run_token      = ?
                            WHERE id = ?
                            """,
                            (run_token, agent_id),
                        )
                    else:
                        raise ValueError(f"ConflictError: Agent '{agent_id}' is already active in this session.")
            else:
                cursor.execute(
                    """
                    UPDATE agents
                    SET status         = 'active',
                        last_heartbeat = CURRENT_TIMESTAMP,
                        run_token      = ?
                    WHERE id = ?
                    """,
                    (run_token, agent_id),
                )
        else:
            cursor.execute(
                """
                INSERT INTO agents (id, harness, substrate, status, run_token, vector_clock)
                VALUES (?, ?, ?, 'active', ?, '{}')
                """,
                (agent_id, harness_name, substrate_name, run_token),
            )

    conn.close()
    return f"Session '{session_id}' started successfully for agent '{agent_id}'."


def end_session_logic(session_id: str, identifier: str | None = None) -> str:
    """
    Marks the session as ended and updates index and state.yaml.
    """
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    session_file = get_session_file(persona_dir, session_id)

    if not session_file.exists():
        raise FileNotFoundError(f"Session '{session_id}' not found.")

    session_lock = ensure_local_persona_dir(persona_dir) / '.locks' / 'session.lock'
    with state_lock(session_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS):
        index = load_session_index(persona_dir)
        if index.active_session_id == session_id:
            index.active_session_id = None

        existing_entry = next((s for s in index.sessions if s.id == session_id), None)
        if existing_entry:
            existing_entry.status = 'ended'
            existing_entry.updated_at = datetime.now()

        save_session_index(persona_dir, index)

        ws = resolve_workspace_dir() or Path.cwd()
        state_path = ws / '.tur' / 'state.yaml'
        if state_path.exists():
            with contextlib.suppress(Exception):
                with open(state_path, encoding='utf-8') as f:
                    state_obj = SystemState(**yaml_safe_load(f))
                if state_obj.active_session_id == session_id:
                    state_obj.active_session_id = None
                with open(state_path, 'w', encoding='utf-8') as f:
                    yaml.dump(state_obj.model_dump(mode='json'), f)

    return f"Session '{session_id}' ended successfully."


@db_retry()
def signal_logic(
    session_id: str,
    sender: str,
    recipient: str,
    content: str,
    type_: str = 'inform',
    vector_clock: dict[str, int] | None = None,
) -> str:
    """Sends a message signal transactionally with Lamport Vector Clock ticking (EP-0141)."""
    if not re.match(r'^[a-zA-Z0-9_\.-]+$', sender):
        raise ValueError(f"Invalid sender ID: '{sender}'")
    if recipient != '*' and not re.match(r'^[a-zA-Z0-9_\.-]+$', recipient):
        raise ValueError(f"Invalid recipient ID: '{recipient}'")

    conn = get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM signals
        WHERE sender = ? AND timestamp > datetime('now', '-60 seconds')
        """,
        (sender,),
    )
    count_row = cursor.fetchone()
    if count_row and count_row['count'] >= 10:
        conn.close()
        raise ValueError(f"RateLimitError: Agent '{sender}' exceeded rate limit of 10 signals per minute.")

    payload = f'{sender}|{recipient}|{type_}|{content}'
    timestamp_str = datetime.now(UTC).isoformat()
    signal_id = hashlib.sha256(f'{payload}|{timestamp_str}|{uuid.uuid4().hex}'.encode()).hexdigest()

    # EP-0141: Vector Clock local emission ticking (Rule 1)
    sender_clock = get_agent_vector_clock(conn, sender)
    if vector_clock:
        sender_clock = sender_clock | VectorClock(vector_clock)
    sender_clock = sender_clock.tick(sender)
    clock_json = json.dumps(sender_clock)

    with conn:
        conn.execute(
            """
            INSERT INTO signals (id, sender, recipient, type, content, vector_clock)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (signal_id, sender, recipient, type_, content, clock_json),
        )
        conn.execute(
            """
            UPDATE agents
            SET last_heartbeat = CURRENT_TIMESTAMP, vector_clock = ?
            WHERE id = ?
            """,
            (clock_json, sender),
        )

    conn.close()
    return signal_id


def sort_signals_causally(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sorts incoming IASP signal dictionaries in causal delivery order using VectorClock (EP-0141)."""
    return VectorClock.sort(signals, key=lambda s: s.get('vector_clock', {}))


@db_retry()
def read_signals_logic(
    session_id: str,
    agent_id: str,
    unread_only: bool = True,
    causal_delivery: bool = True,
) -> list[dict]:
    """Peeks incoming signals matching caller handle or dot subagent namespaces with causal ordering (EP-0141)."""
    conn = get_db_connection(session_id)
    cursor = conn.cursor()

    query = """
            SELECT s.id, s.sequence, s.timestamp, s.sender, s.recipient, s.type, s.content, s.vector_clock
            FROM signals s
            WHERE (s.recipient = :agent_id OR s.recipient = '*' OR s.recipient LIKE :sub_pattern) \
            """

    if unread_only:
        query += """
            AND NOT EXISTS (
                SELECT 1 FROM signal_reads r
                WHERE r.signal_id = s.id AND r.agent_id = :agent_id
            )
        """

    query += ' ORDER BY s.sequence ASC'

    cursor.execute(query, {'agent_id': agent_id, 'sub_pattern': f'{agent_id}.%'})

    rows = cursor.fetchall()
    results = []
    for row in rows:
        d = dict(row)
        d['vector_clock'] = VectorClock(d.get('vector_clock'))
        results.append(d)

    if causal_delivery and results:
        results = sort_signals_causally(results)

    with conn:
        conn.execute(
            """
            UPDATE agents
            SET last_heartbeat = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (agent_id,),
        )

    conn.close()
    return results


@db_retry()
def ack_signals_logic(
    session_id: str,
    agent_id: str,
    signal_ids: list[str],
) -> str:
    """
    Acknowledges signals by registering read entries in the signal_reads table
    and merging vector clocks (EP-0141).
    """
    conn = get_db_connection(session_id)
    agent_clock = get_agent_vector_clock(conn, agent_id)
    merged = False

    with conn:
        for sig_id in signal_ids:
            conn.execute(
                """
                INSERT OR IGNORE INTO signal_reads (signal_id, agent_id)
                VALUES (?, ?)
                """,
                (sig_id, agent_id),
            )
            cursor = conn.cursor()
            cursor.execute('SELECT vector_clock FROM signals WHERE id = ?', (sig_id,))
            sig_row = cursor.fetchone()
            if sig_row and sig_row['vector_clock']:
                sig_clock = VectorClock(sig_row['vector_clock'])
                agent_clock = agent_clock | sig_clock
                merged = True

        if merged:
            # Rule 2: Agent increments own local logical counter on receive & merge
            agent_clock = agent_clock.tick(agent_id)

        conn.execute(
            """
            UPDATE agents
            SET last_heartbeat = CURRENT_TIMESTAMP, vector_clock = ?
            WHERE id = ?
            """,
            (json.dumps(agent_clock), agent_id),
        )
    conn.close()
    return f'Acknowledged {len(signal_ids)} signals.'


@db_retry()
def write_whiteboard_logic(
    session_id: str,
    key: str,
    value: str,
    updated_by: str,
) -> str:
    """Writes key-value state parameters to the shared session whiteboard."""
    conn = get_db_connection(session_id)
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO session_state (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (key, value, updated_by),
        )
        conn.execute(
            """
            UPDATE agents
            SET last_heartbeat = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (updated_by,),
        )
    conn.close()
    return f"Whiteboard coordinate '{key}' updated."


@db_retry()
def read_whiteboard_logic(
    session_id: str,
    key: str,
) -> str | None:
    """Reads state parameters from the shared session whiteboard."""
    conn = get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM session_state WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None


@db_retry()
def list_agents_logic(session_id: str) -> list[dict]:
    """Lists all registered manifestations from the SQLite session database."""
    conn = get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute('SELECT id, harness, substrate, status, last_heartbeat, run_token, joined_at FROM agents')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _fetch_single_session_notes(sess_id: str, fetch_limit: int, p_dir: Path) -> list[dict]:
    # 1. Primary: SQLite
    try:
        conn = get_db_connection(sess_id)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, sender, recipient, type, content, timestamp, sequence, vector_clock
            FROM signals
            WHERE recipient = '*'
            ORDER BY sequence ASC
            LIMIT ?
            """,
            (fetch_limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        if rows:
            results = []
            for row in rows:
                d = dict(row)
                d['vector_clock'] = VectorClock(d.get('vector_clock'))
                results.append(d)
            return results
    except Exception:
        pass

    # 2. Fallback: Flat YAML sessions/<session_id>.yaml
    session_file = get_session_file(p_dir, sess_id)
    if session_file.exists():
        try:
            with open(session_file, encoding='utf-8') as f:
                data: dict[str, Any] = yaml_safe_load(f) or {}
            s_notes = SessionNotes(**data)
            results = []
            for idx, n in enumerate(s_notes.notes[:fetch_limit]):
                ts_str = n.timestamp.isoformat() if hasattr(n.timestamp, 'isoformat') else str(n.timestamp)
                sig_id = hashlib.sha256(f'{ts_str}|{n.content}'.encode()).hexdigest()
                results.append(
                    {
                        'id': sig_id,
                        'sender': 'system',
                        'recipient': '*',
                        'type': 'inform',
                        'content': n.content,
                        'timestamp': ts_str,
                        'sequence': idx + 1,
                    }
                )
        except Exception:
            pass
        else:
            return results

    return []


def read_notes_logic(
    session_id: str,
    limit: int = 50,
    include_previous: bool = False,
    identifier: str | None = None,
    persona_dir: Path | None = None,
) -> list[dict]:
    """
    Returns broadcast notes in ascending sequence order with dual-backend fallback (SQLite + YAML)
    and cross-session lineage support (EP-0130).
    """
    if persona_dir is None:
        active_id = get_active_persona_id(identifier)
        persona_dir = get_persona_path(active_id)

    target_session_id = session_id

    if target_session_id == 'previous':
        active_sess = get_active_session_id()
        parent_id = get_parent_session_id(active_sess, persona_dir) if active_sess else None
        if not parent_id:
            index = load_session_index(persona_dir)
            priors = [s for s in index.sessions if s.id != active_sess]
            if priors:
                sorted_priors = sorted(priors, key=lambda s: (s.updated_at, s.created_at, s.id), reverse=True)
                parent_id = sorted_priors[0].id
        if not parent_id:
            return []
        target_session_id = parent_id

    validate_session_id(target_session_id)

    if include_previous:
        parent_id = get_parent_session_id(target_session_id, persona_dir)
        parent_notes = _fetch_single_session_notes(parent_id, limit, persona_dir) if parent_id else []
        curr_notes = _fetch_single_session_notes(target_session_id, limit, persona_dir)
        combined = parent_notes + curr_notes
        if len(combined) > limit:
            combined = combined[-limit:]
        return combined

    return _fetch_single_session_notes(target_session_id, limit, persona_dir)


@db_retry()
def stage_memories_logic(session_id: str, agent_id: str, memories_json: str):
    """Stages extracted memories to the staged_memories table."""
    conn = get_db_connection(session_id)
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO staged_memories (id, agent_id, memory_data)
            VALUES (?, ?, ?)
        """,
            (str(uuid.uuid4()), agent_id, memories_json),
        )
    conn.close()


def tired_logic(session_id: str, agent_id: str, transcript: str | None = None) -> str:
    """Marks agent as idle, runs staged dreaming, and ends the session if all agents are idle."""
    conn = get_db_connection(session_id)
    with conn:
        conn.execute("UPDATE agents SET status = 'idle', last_heartbeat = CURRENT_TIMESTAMP WHERE id = ?", (agent_id,))
    conn.close()

    active_id = get_active_persona_id()

    if transcript:
        try:
            from tur.dreaming import stage_sleep_dreaming

            memories_json = stage_sleep_dreaming(transcript, active_id, session_id)
            stage_memories_logic(session_id, agent_id, memories_json)
        except Exception as e:
            print(f'Error during stage dreaming: {e}')

    conn = get_db_connection(session_id)
    other_active_count = 0
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM agents
            WHERE id != ? AND status = 'active' AND last_heartbeat > datetime('now', '-300 seconds')
            """,
            (agent_id,),
        )
        count_row = cursor.fetchone()
        other_active_count = count_row['count'] if count_row else 0

    if other_active_count > 0:
        conn.close()
        return f"Agent '{agent_id}' is ready to sleep. Standby mode active (postponed until other processes idle)."

    with conn:
        cursor = conn.cursor()
        payload = f'{agent_id}|*|sleep_event|Consensus reached. Swarm sleeping.'
        sig_id = hashlib.sha256(f'{payload}|{datetime.now(UTC).isoformat()}|{uuid.uuid4().hex}'.encode()).hexdigest()

        agent_clock = get_agent_vector_clock(conn, agent_id).tick(agent_id)
        clock_json = json.dumps(agent_clock)

        conn.execute(
            """
            INSERT INTO signals (id, sender, recipient, type, content, vector_clock)
            VALUES (?, ?, '*', 'sleep_event', 'Consensus reached. Swarm sleeping.', ?)
            """,
            (sig_id, agent_id, clock_json),
        )
        conn.execute("UPDATE agents SET status = 'sleeping', vector_clock = ?", (clock_json,))

        cursor.execute('SELECT agent_id, memory_data FROM staged_memories')
        staged_rows = cursor.fetchall()

        from tur.memory import MemoryManager
        from tur.models import Memory

        persona_dir = get_persona_path(active_id)
        session_lock = ensure_local_persona_dir(persona_dir) / '.locks' / 'session.lock'
        with state_lock(session_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS):
            memory_manager = MemoryManager(base_dir=persona_dir)

            all_memories = []
            for row in staged_rows:
                try:
                    data = json.loads(row['memory_data'])
                    mems = data.get('memories', []) if isinstance(data, dict) else data
                    all_memories.extend(mems)
                except Exception:
                    pass

            unique_contents = set()
            deduped_memories = []
            for mem in all_memories:
                content = (
                    mem.get('content', '').strip() if isinstance(mem, dict) else getattr(mem, 'content', '').strip()
                )
                if content and content not in unique_contents:
                    unique_contents.add(content)
                    deduped_memories.append(mem)

            saved_count = 0
            for mem_data in deduped_memories:
                try:
                    memory = Memory(
                        type=mem_data.get('type', 'fact') if isinstance(mem_data, dict) else mem_data.type,
                        scope=mem_data.get('scope', 'local') if isinstance(mem_data, dict) else mem_data.scope,
                        tags=[
                            *(mem_data.get('tags', []) if isinstance(mem_data, dict) else mem_data.tags),
                            'dreaming',
                            'consolidated',
                        ],
                        content=(mem_data.get('content') if isinstance(mem_data, dict) else mem_data.content) or '',
                        source_session=session_id,
                    )
                    memory_manager.save(memory)
                    saved_count += 1
                except Exception:
                    pass

            conn.execute('DELETE FROM staged_memories')
            end_session_logic(session_id, identifier=active_id)

    conn.close()
    return f'Consensus sleep reached. Consolidated {saved_count} memories across manifestations. Session ended.'


def note_logic(content: str, session_id: str | None = None, identifier: str | None = None) -> str:
    """
    Common business logic for appending a note to a session's notes.yaml and the SQLite db.
    """
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    resolved_session_id = session_id or get_active_session_id()

    if resolved_session_id:
        session_lock = ensure_local_persona_dir(persona_dir) / '.locks' / 'session.lock'
        with state_lock(session_lock, timeout=FAST_LOCK_TIMEOUT_SECONDS):
            session_file = get_session_file(persona_dir, resolved_session_id)
            session_file.parent.mkdir(parents=True, exist_ok=True)

            notes_list = []
            parent_id = None
            if session_file.exists():
                try:
                    with open(session_file, encoding='utf-8') as f:
                        notes_data = yaml_safe_load(f)
                    session_notes = SessionNotes(**notes_data)
                    notes_list = session_notes.notes
                    parent_id = session_notes.parent_session_id
                except Exception:
                    pass

            note_item = Note(timestamp=datetime.now(), content=content.strip())
            notes_list.append(note_item)
            session_notes = SessionNotes(
                session_id=resolved_session_id,
                parent_session_id=parent_id,
                notes=notes_list,
            )
            atomic_yaml_write(session_file, session_notes.model_dump(mode='json'))

            index = load_session_index(persona_dir)
            existing_entry = next((s for s in index.sessions if s.id == resolved_session_id), None)
            if existing_entry:
                existing_entry.updated_at = datetime.now()
                if parent_id and not existing_entry.parent_session_id:
                    existing_entry.parent_session_id = parent_id
            else:
                new_entry = SessionEntry(id=resolved_session_id, parent_session_id=parent_id, status='active')
                index.sessions.append(new_entry)
            save_session_index(persona_dir, index)

        # Mirror note to SQLite database
        with contextlib.suppress(Exception):
            signal_logic(
                session_id=resolved_session_id,
                sender=os.environ.get('TUR_AGENT_ID') or 'legacy_agent',
                recipient='*',
                content=note_item.content,
                type_='inform',
            )

        return f"Note successfully saved for '{active_id}' in session '{resolved_session_id}'"

    else:
        index = load_session_index(persona_dir)
        if index.sessions:
            sorted_sessions = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)
            return note_logic(content, session_id=sorted_sessions[0].id, identifier=identifier)
        else:
            raise ValueError(f"No active session found for persona '{active_id}'. Run 'wake' first.")
