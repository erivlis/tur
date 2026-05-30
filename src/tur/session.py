import os
from datetime import datetime
from pathlib import Path
from uuid import UUID

import yaml

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
        return Path.cwd() / ".tur" / "personas" / persona_dir.name
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
    index_path = get_local_persona_dir(persona_dir) / "sessions.yaml"  # read-only path query
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
                return SessionIndex(**data)
            except Exception:
                pass
    return SessionIndex()


def save_session_index(persona_dir: Path, index: SessionIndex):
    """Saves the session index to sessions.yaml."""
    index_path = ensure_local_persona_dir(persona_dir) / "sessions.yaml"
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index.model_dump(mode="json"), f)


def get_session_file(persona_dir: Path, session_id: str) -> Path:
    """Returns the flat YAML file path for a session: sessions/<session_id>.yaml"""
    return get_local_persona_dir(persona_dir) / "sessions" / f"{session_id}.yaml"  # read-only path query


def get_active_session_id() -> str | None:
    """
    Resolves the active session ID.
    - Checks env var `TUR_ACTIVE_SESSION_ID`.
    - Checks `active_session_id` in `.tur/state.yaml`.
    """
    env_id = os.environ.get("TUR_ACTIVE_SESSION_ID")
    if env_id:
        return env_id

    state_path = Path(".tur/state.yaml")
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                state_data = yaml.safe_load(f)
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
        return "Status: Conserved. Aleph: Restored. Carry on, Lion."

    session_file = get_session_file(persona_dir, session_id)

    if session_file.exists():
        try:
            with open(session_file, encoding="utf-8") as f:
                notes_data = yaml.safe_load(f)
            session_notes = SessionNotes(**notes_data)
            if session_notes.notes:
                sorted_notes = sorted(session_notes.notes, key=lambda x: x.timestamp, reverse=True)
                return sorted_notes[0].content.strip()
        except Exception:
            pass

    return "Status: Conserved. Aleph: Restored. Carry on, Lion."


def hydrate_session_state(active_id: str, session_id: str | None = None) -> SessionState:
    """Hydrates the full SessionState (Persona, User, Memories, Epilogue) from the filesystem."""
    persona_dir = get_persona_path(active_id)
    file_path = persona_dir / "persona.yaml"

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

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

    return SessionState(
        persona=persona,
        user=user,
        memories=memories,
        epilogue=epilogue_content
    )


def start_session_logic(session_id: str, identifier: str | None = None, previous_session_id: str | None = None) -> str:
    """
    Creates the flat session YAML file (sessions/<session_id>.yaml).
    If previous_session_id is provided, seeds the first note from that session's last note.
    Updates sessions.yaml and .tur/state.yaml.
    """
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    # ensure_local_persona_dir creates the dir; get_session_file reuses the same path
    sessions_dir = ensure_local_persona_dir(persona_dir) / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = get_session_file(persona_dir, session_id)

    if not session_file.exists():
        seed_content = "Session started."
        if previous_session_id:
            prev_content = compile_session_notes(persona_dir, previous_session_id)
            if prev_content and prev_content != "Status: Conserved. Aleph: Restored. Carry on, Lion.":
                seed_content = prev_content
        session_notes = SessionNotes(notes=[
            Note(timestamp=datetime.now(), content=seed_content)
        ])
        with open(session_file, "w", encoding="utf-8") as f:
            yaml.dump(session_notes.model_dump(mode="json"), f)

    # Update sessions.yaml
    index = load_session_index(persona_dir)
    index.active_session_id = session_id

    existing_entry = next((s for s in index.sessions if s.id == session_id), None)
    if existing_entry:
        existing_entry.updated_at = datetime.now()
        existing_entry.status = "active"
    else:
        new_entry = SessionEntry(id=session_id, status="active")
        index.sessions.append(new_entry)

    save_session_index(persona_dir, index)

    # Update .tur/state.yaml
    state_path = Path(".tur/state.yaml")
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                state_data = yaml.safe_load(f)
            state_obj = SystemState(**state_data)
            state_obj.active_session_id = session_id
        except Exception:
            state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=session_id)
    else:
        state_obj = SystemState(active_persona_id=UUID(active_id), active_session_id=session_id)

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_obj.model_dump(mode="json"), f)

    return f"Session '{session_id}' started successfully for persona '{active_id}'."


def end_session_logic(session_id: str, identifier: str | None = None) -> str:
    """
    Marks the session as ended and updates index and state.yaml.
    """
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    session_file = get_session_file(persona_dir, session_id)

    if not session_file.exists():
        raise FileNotFoundError(f"Session '{session_id}' not found.")

    # Update sessions.yaml
    index = load_session_index(persona_dir)
    if index.active_session_id == session_id:
        index.active_session_id = None

    existing_entry = next((s for s in index.sessions if s.id == session_id), None)
    if existing_entry:
        existing_entry.status = "ended"
        existing_entry.updated_at = datetime.now()

    save_session_index(persona_dir, index)

    # Update .tur/state.yaml
    state_path = Path(".tur/state.yaml")
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                state_obj = SystemState(**yaml.safe_load(f))
            if state_obj.active_session_id == session_id:
                state_obj.active_session_id = None
            with open(state_path, "w", encoding="utf-8") as f:
                yaml.dump(state_obj.model_dump(mode="json"), f)
        except Exception:
            pass

    return f"Session '{session_id}' ended successfully."


def note_logic(content: str, session_id: str | None = None, identifier: str | None = None) -> str:
    """
    Common business logic for appending a note to a session's notes.yaml.
    Falls back to finding the most recently updated session if no active session is found.
    """
    active_id = get_active_persona_id(identifier)
    persona_dir = get_persona_path(active_id)

    resolved_session_id = session_id or get_active_session_id()

    if resolved_session_id:
        session_file = get_session_file(persona_dir, resolved_session_id)
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing notes
        notes_list = []
        if session_file.exists():
            try:
                with open(session_file, encoding="utf-8") as f:
                    notes_data = yaml.safe_load(f)
                session_notes = SessionNotes(**notes_data)
                notes_list = session_notes.notes
            except Exception:
                pass

        # Append new note
        notes_list.append(Note(timestamp=datetime.now(), content=content.strip()))
        session_notes = SessionNotes(notes=notes_list)

        with open(session_file, "w", encoding="utf-8") as f:
            yaml.dump(session_notes.model_dump(mode="json"), f)

        # Update sessions.yaml index
        index = load_session_index(persona_dir)
        existing_entry = next((s for s in index.sessions if s.id == resolved_session_id), None)
        if existing_entry:
            existing_entry.updated_at = datetime.now()
        else:
            new_entry = SessionEntry(id=resolved_session_id)
            index.sessions.append(new_entry)
        save_session_index(persona_dir, index)

        return f"Note successfully saved for '{active_id}' in session '{resolved_session_id}'"


    else:
        # Fall back to the most recently updated session
        index = load_session_index(persona_dir)
        if index.sessions:
            sorted_sessions = sorted(index.sessions, key=lambda s: s.updated_at, reverse=True)
            return note_logic(content, session_id=sorted_sessions[0].id, identifier=identifier)
        else:
            raise ValueError(f"No active session found for persona '{active_id}'. Run 'wake' first.")
