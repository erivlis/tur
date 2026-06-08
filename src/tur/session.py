import contextlib
import functools
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from uuid import UUID

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from tur.memory import MemoryManager
from tur.models import (
    Note,
    Persona,
    SessionEntry,
    SessionIndex,
    SessionNotes,
    SessionState,
    SystemState,
)
from tur.paths import is_global_path
from tur.persona import get_active_persona_id, get_persona_path
from tur.user import get_user_profile


def get_local_persona_dir(persona_dir: Path) -> Path:
    """
    Returns the project-local persona directory path for runtime state (sessions, notes).

    When *persona_dir* is a global path (~/.tur/...) the corresponding local mirror
    under the current working directory is returned.  This function is a pure query —
    it does NOT create directories.  Call ensure_local_persona_dir() when you need
    the directory to actually exist on disk.
    """
    if is_global_path(persona_dir):
        return Path.cwd() / '.tur' / 'personas' / persona_dir.name
    return persona_dir


def ensure_local_persona_dir(persona_dir: Path) -> Path:
    """
    Returns the project-local persona directory, creating it on disk if necessary.

    Use this instead of get_local_persona_dir() when you are about to write files
    into the directory.  Callers that only *read* should use the pure getter.
    """
    local_dir = get_local_persona_dir(persona_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir


def load_session_index(persona_dir: Path) -> SessionIndex:
    """Loads the session index from sessions.yaml or returns an empty index."""
    index_path = get_local_persona_dir(persona_dir) / 'sessions.yaml'  # read-only path query
    if index_path.exists():
        with open(index_path, encoding='utf-8') as f:
            try:
                data = yaml.load(f, Loader=SafeLoader) or {}
                return SessionIndex(**data)
            except Exception:
                pass
    return SessionIndex()


def save_session_index(persona_dir: Path, index: SessionIndex):
    """Saves the session index to sessions.yaml."""
    index_path = ensure_local_persona_dir(persona_dir) / 'sessions.yaml'
    with open(index_path, 'w', encoding='utf-8') as f:
        yaml.dump(index.model_dump(mode='json'), f)


def get_session_file(persona_dir: Path, session_id: str) -> Path:
    """Returns the flat YAML file path for a session: sessions/<session_id>.yaml"""
    return get_local_persona_dir(persona_dir) / 'sessions' / f'{session_id}.yaml'  # read-only path query


def get_active_session_id() -> str | None:
    """
    Resolves the active session ID.
    - Checks env var `TUR_ACTIVE_SESSION_ID`.
    - Checks `active_session_id` in `.tur/state.yaml`.
    """
    env_id = os.environ.get('TUR_ACTIVE_SESSION_ID')
    if env_id:
        return env_id

    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        try:
            with open(state_path, encoding='utf-8') as f:
                state_data = yaml.load(f, Loader=SafeLoader)
            state_obj = SystemState(**state_data)
        except Exception:
            pass
        else:
            return state_obj.active_session_id
    return None


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
                notes_data = yaml.load(f, Loader=SafeLoader)
            session_notes = SessionNotes(**notes_data)
            if session_notes.notes:
                sorted_notes = sorted(session_notes.notes, key=lambda x: x.timestamp, reverse=True)
                return sorted_notes[0].content.strip()
        except Exception:
            pass

    return 'Status: Conserved. Aleph: Restored. Carry on, Lion.'


def hydrate_session_state(active_id: str, session_id: str | None = None) -> SessionState:
    """Hydrates the full SessionState (Persona, User, Memories, Epilogue) from the filesystem."""
    persona_dir = get_persona_path(active_id)
    file_path = persona_dir / 'persona.yaml'

    with open(file_path, encoding='utf-8') as f:
        data = yaml.load(f, Loader=SafeLoader)

    persona = Persona(**data)
    user = get_user_profile()
    memory_manager = MemoryManager(base_dir=persona_dir)
    memories = memory_manager.load_all()

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
                kg_data = yaml.load(f, Loader=SafeLoader)
        except Exception:
            pass

    return SessionState(
        persona=persona,
        user=user,
        memories=memories,
        epilogue=epilogue_content,
        knowledge_graph=kg_data,
    )


def db_retry(max_retries=5, initial_delay=0.05, backoff_factor=2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for attempt in range(max_retries):
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

        return wrapper

    return decorator


def get_session_db(session_id: str) -> Path:
    """Resolves and returns the path to the SQLite session database, ensuring parent dirs exist."""
    db_dir = Path('.tur') / 'sessions' / session_id
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
                     joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                     content TEXT NOT NULL
                     );
                 """)
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
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    # Backwards compatibility flat file setup
    sessions_dir = ensure_local_persona_dir(persona_dir) / 'sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = get_session_file(persona_dir, session_id)

    if not session_file.exists():
        seed_content = 'Session started.'
        if previous_session_id:
            prev_content = compile_session_notes(persona_dir, previous_session_id)
            if prev_content and prev_content != 'Status: Conserved. Aleph: Restored. Carry on, Lion.':
                seed_content = prev_content
        session_notes = SessionNotes(notes=[Note(timestamp=datetime.now(), content=seed_content)])
        with open(session_file, 'w', encoding='utf-8') as f:
            yaml.dump(session_notes.model_dump(mode='json'), f)

    index = load_session_index(persona_dir)
    index.active_session_id = session_id

    existing_entry = next((s for s in index.sessions if s.id == session_id), None)
    if existing_entry:
        existing_entry.updated_at = datetime.now()
        existing_entry.status = 'active'
    else:
        new_entry = SessionEntry(id=session_id, status='active')
        index.sessions.append(new_entry)

    save_session_index(persona_dir, index)

    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        try:
            with open(state_path, encoding='utf-8') as f:
                state_data = yaml.load(f, Loader=SafeLoader)
            state_obj = SystemState(**state_data)
            state_obj.active_session_id = session_id
        except Exception:
            state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=session_id)
    else:
        state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=session_id)

    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_obj.model_dump(mode='json'), f)

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
                           INSERT INTO agents (id, harness, substrate, status, run_token)
                           VALUES (?, ?, ?, 'active', ?)
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

    index = load_session_index(persona_dir)
    if index.active_session_id == session_id:
        index.active_session_id = None

    existing_entry = next((s for s in index.sessions if s.id == session_id), None)
    if existing_entry:
        existing_entry.status = 'ended'
        existing_entry.updated_at = datetime.now()

    save_session_index(persona_dir, index)

    state_path = Path('.tur/state.yaml')
    if state_path.exists():
        try:
            with open(state_path, encoding='utf-8') as f:
                state_obj = SystemState(**yaml.load(f, Loader=SafeLoader))
            if state_obj.active_session_id == session_id:
                state_obj.active_session_id = None
            with open(state_path, 'w', encoding='utf-8') as f:
                yaml.dump(state_obj.model_dump(mode='json'), f)
        except Exception:
            pass

    return f"Session '{session_id}' ended successfully."


@db_retry()
def signal_logic(
    session_id: str,
    sender: str,
    recipient: str,
    content: str,
    type_: str = 'inform',
) -> str:
    """Sends a message signal transactionally, validating boundaries and rate-limits."""
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
    timestamp_str = datetime.utcnow().isoformat()
    signal_id = hashlib.sha256(f'{payload}|{timestamp_str}|{uuid.uuid4().hex}'.encode()).hexdigest()

    with conn:
        conn.execute(
            """
                     INSERT INTO signals (id, sender, recipient, type, content)
                     VALUES (?, ?, ?, ?, ?)
                     """,
            (signal_id, sender, recipient, type_, content),
        )
        conn.execute(
            """
                     UPDATE agents
                     SET last_heartbeat = CURRENT_TIMESTAMP
                     WHERE id = ?
                     """,
            (sender,),
        )

    conn.close()
    return signal_id


@db_retry()
def read_signals_logic(
    session_id: str,
    agent_id: str,
    unread_only: bool = True,
) -> list[dict]:
    """Peeks incoming signals matching caller handle or dot subagent namespaces."""
    conn = get_db_connection(session_id)
    cursor = conn.cursor()

    query = """
            SELECT s.id, s.sequence, s.timestamp, s.sender, s.recipient, s.type, s.content
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
    results = [dict(row) for row in rows]

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
    """Acknowledges signals by registering read entries in the signal_reads table."""
    conn = get_db_connection(session_id)
    with conn:
        for sig_id in signal_ids:
            conn.execute(
                """
                         INSERT
                         OR IGNORE INTO signal_reads (signal_id, agent_id)
                VALUES (?, ?)
                         """,
                (sig_id, agent_id),
            )
        conn.execute(
            """
                     UPDATE agents
                     SET last_heartbeat = CURRENT_TIMESTAMP
                     WHERE id = ?
                     """,
            (agent_id,),
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


@db_retry()
def read_notes_logic(session_id: str, limit: int = 50) -> list[dict]:
    """Returns the broadcast signals history in strict ascending sequence order."""
    conn = get_db_connection(session_id)
    cursor = conn.cursor()
    cursor.execute(
        """
                   SELECT id, sender, recipient, type, content, timestamp, sequence
                   FROM signals
                   WHERE recipient = '*'
                   ORDER BY sequence ASC
                       LIMIT ?
                   """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


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
        sig_id = hashlib.sha256(f'{payload}|{datetime.utcnow().isoformat()}|{uuid.uuid4().hex}'.encode()).hexdigest()
        conn.execute(
            """
                     INSERT INTO signals (id, sender, recipient, type, content)
                     VALUES (?, ?, '*', 'sleep_event', 'Consensus reached. Swarm sleeping.')
                     """,
            (sig_id, agent_id),
        )
        conn.execute("UPDATE agents SET status = 'sleeping'")

        cursor.execute('SELECT agent_id, memory_data FROM staged_memories')
        staged_rows = cursor.fetchall()

        from tur.memory import MemoryManager
        from tur.models import Memory

        persona_dir = get_persona_path(active_id)
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
            content = mem.get('content', '').strip() if isinstance(mem, dict) else getattr(mem, 'content', '').strip()
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
                    content=mem_data.get('content') if isinstance(mem_data, dict) else mem_data.content,
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
        session_file = get_session_file(persona_dir, resolved_session_id)
        session_file.parent.mkdir(parents=True, exist_ok=True)

        notes_list = []
        if session_file.exists():
            try:
                with open(session_file, encoding='utf-8') as f:
                    notes_data = yaml.load(f, Loader=SafeLoader)
                session_notes = SessionNotes(**notes_data)
                notes_list = session_notes.notes
            except Exception:
                pass

        notes_list.append(Note(timestamp=datetime.now(), content=content.strip()))
        session_notes = SessionNotes(notes=notes_list)

        with open(session_file, 'w', encoding='utf-8') as f:
            yaml.dump(session_notes.model_dump(mode='json'), f)

        index = load_session_index(persona_dir)
        existing_entry = next((s for s in index.sessions if s.id == resolved_session_id), None)
        if existing_entry:
            existing_entry.updated_at = datetime.now()
        else:
            new_entry = SessionEntry(id=resolved_session_id)
            index.sessions.append(new_entry)
        save_session_index(persona_dir, index)

        # Mirror note to SQLite database
        with contextlib.suppress(Exception):
            signal_logic(
                session_id=resolved_session_id,
                sender=os.environ.get('TUR_AGENT_ID') or 'legacy_agent',
                recipient='*',
                content=content,
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
