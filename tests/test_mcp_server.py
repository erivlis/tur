import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tur import mcp_server
from tur.models import (
    Persona,
    Principle,
    SessionState,
    UserProfile,
)


@pytest.fixture
def mock_mcp_env(tmp_path, monkeypatch):
    # Setup mock active persona structure
    persona_id = "fake-persona-uuid"
    persona_dir = tmp_path / "personas" / persona_id
    persona_dir.mkdir(parents=True, exist_ok=True)

    # Create subfolders for memory management to prevent crashes
    (persona_dir / "memories" / "archive").mkdir(parents=True, exist_ok=True)

    # Mock return values for main functions used by mcp_server and domain modules
    import tur.persona
    import tur.session
    # Also patch mcp_server's direct imports
    monkeypatch.setattr(mcp_server, "get_active_persona_id", lambda *args: persona_id)
    monkeypatch.setattr(mcp_server, "get_persona_path", lambda *args: persona_dir)
    monkeypatch.setattr(tur.persona, "get_active_persona_id", lambda *args: persona_id)
    monkeypatch.setattr(tur.persona, "get_persona_path", lambda *args: persona_dir)
    monkeypatch.setattr(tur.session, "get_active_persona_id", lambda *args: persona_id)
    monkeypatch.setattr(tur.session, "get_persona_path", lambda *args: persona_dir)
    # Ensure tests are isolated from any real active session on disk
    monkeypatch.setattr(tur.session, "get_active_session_id", lambda: None)

    persona = Persona(
        name="MockAriel",
        aleph="To design test scenarios.",
        principles=[
            Principle(name="Symmetry", role="Guardian", weight=1.0)
        ]
    )
    user = UserProfile(name="Tester", role="Developer")
    state = SessionState(persona=persona, user=user, memories=[], epilogue="Start")

    monkeypatch.setattr(mcp_server, "hydrate_session_state", lambda *args, **kwargs: state)

    return persona_dir, state


def test_mcp_wake(mock_mcp_env):
    prompt_result = mcp_server.wake()
    assert "MockAriel" in prompt_result
    assert "Constraint Dimensionality (Cp)" in prompt_result
    assert "SYSTEM METRICS" in prompt_result


def test_mcp_learn(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env

    # Mock Path.home() so MemoryManager doesn't write to ~/.tur
    monkeypatch.setattr(Path, "home", lambda: persona_dir)

    # Learn fact
    res = mcp_server.learn(content="Fact 1", type="fact", scope="incarnation")
    assert "Learned successfully" in res
    assert "Fact 1" not in res  # Return contains ID and File, not raw content

    # Learn with invalid type
    res_err_type = mcp_server.learn(content="Fact 1", type="invalid-type", scope="incarnation")
    assert "Error: Invalid memory_type" in res_err_type

    # Learn with invalid scope
    res_err_scope = mcp_server.learn(content="Fact 1", type="fact", scope="invalid-scope")
    assert "Error: Invalid scope" in res_err_scope


def test_mcp_recall(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    monkeypatch.setattr(Path, "home", lambda: persona_dir)

    # Save a memory first
    mcp_server.learn(content="The Noether invariant is symmetry.", type="insight")

    # Successful query
    recall_res = mcp_server.recall(query="Noether")
    data = json.loads(recall_res)
    assert len(data) == 1
    assert "Noether" in data[0]["content"]

    # Unsuccessful query
    fail_res = mcp_server.recall(query="nonexistent")
    assert "No memories found" in fail_res


def test_mcp_sleep(mock_mcp_env, monkeypatch):
    # Mock perform_sleep_dreaming to prevent hitting real Gemini API
    monkeypatch.setattr(mcp_server, "perform_sleep_dreaming", lambda **kwargs: 3)

    res = mcp_server.sleep(log_content="Log trace", note="Test sleep note", session_id="sess-1")
    assert "Dreams consolidated. 3 new memories formed" in res


def test_mcp_sleep_exception(mock_mcp_env, monkeypatch):
    def raise_err(**kwargs):
        raise ValueError("Simulated Gemini Failure")

    monkeypatch.setattr(mcp_server, "perform_sleep_dreaming", raise_err)

    res = mcp_server.sleep(log_content="Log trace", note="Test sleep note")
    assert "Error during dreaming: Simulated Gemini Failure" in res


def test_mcp_server_main(monkeypatch):
    # Mock mcp.run
    mock_run = MagicMock()
    monkeypatch.setattr(mcp_server.mcp, "run", mock_run)

    # Test stdio transport
    mcp_server.main(transport="stdio")
    mock_run.assert_called_with(transport="stdio")

    # Test sse transport
    mcp_server.main(transport="sse", port=9999)
    mock_run.assert_called_with(transport="sse")
    assert mcp_server.mcp.settings.port == 9999

    # Test invalid transport
    with pytest.raises(ValueError):
        mcp_server.main(transport="invalid")


def test_mcp_server_main_keyboard_interrupt(monkeypatch):
    def raise_kb_interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(mcp_server.mcp, "run", raise_kb_interrupt)

    with pytest.raises(SystemExit) as exc:
        mcp_server.main(transport="stdio")
    assert exc.value.code == 0


@pytest.mark.anyio
async def test_mcp_server_lifespan():
    server = MagicMock()
    # Execute the async context manager
    async with mcp_server.server_lifespan(server) as ctx:
        assert isinstance(ctx, dict)


def test_ensure_project_root_walk(tmp_path, monkeypatch):
    # Setup parent directories structure
    parent_dir = tmp_path / "parent_project"
    sub_dir = parent_dir / "subdir" / "deep"
    sub_dir.mkdir(parents=True)

    # Create fake .tur directory in the parent
    (parent_dir / ".tur").mkdir()

    # Change current working directory to deep sub_dir
    monkeypatch.chdir(sub_dir)
    # Mock __file__ of the module so it is resolved inside our temporary subdir
    monkeypatch.setattr(mcp_server, "__file__", str(sub_dir / "mcp_server.py"))

    # Callensure_project_root to verify it successfully traverses up and changes cwd to parent_dir
    mcp_server._ensure_project_root()
    assert Path.cwd() == parent_dir


def test_ensure_project_root_no_dot_tur(tmp_path, monkeypatch):
    # Setup parent directories structure without any .tur
    parent_dir = tmp_path / "parent_project"
    sub_dir = parent_dir / "subdir" / "deep"
    sub_dir.mkdir(parents=True)

    # Change current working directory to deep sub_dir
    monkeypatch.chdir(sub_dir)
    monkeypatch.setattr(mcp_server, "__file__", str(sub_dir / "mcp_server.py"))

    # Mock Path(".tur").exists() to be False so we traverse
    original_exists = Path.exists

    def mock_exists(self):
        if self.name == ".tur":
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", mock_exists)

    # Call _ensure_project_root
    mcp_server._ensure_project_root()
    # It should not have changed CWD since no .tur exists anywhere in parents
    assert Path.cwd() == sub_dir


def test_mcp_server_module_main(monkeypatch):
    from mcp.server.fastmcp import FastMCP
    mock_run = MagicMock()
    monkeypatch.setattr(FastMCP, "run", mock_run)

    # Mock return values for main functions used by mcp_server at startup or execution
    monkeypatch.setattr(mcp_server, "get_active_persona_id", lambda *args: "fake-id")
    monkeypatch.setattr(mcp_server, "get_persona_path", lambda *args: Path("fake"))

    import runpy
    runpy.run_module("tur.mcp_server", run_name="__main__")

    mock_run.assert_called_with(transport="stdio")


def test_mcp_telemetry(mock_mcp_env, monkeypatch):
    persona_dir, _state = mock_mcp_env
    
    # Setup persona file for telemetry with required 'aleph' field
    persona_yaml = persona_dir / "persona.yaml"
    persona_yaml.write_text("name: MockAriel\nversion: 5.4.0\naleph: To design test scenarios.\nprinciples: []\n", encoding="utf-8")
    
    res = mcp_server.telemetry(identifier="fake-persona-uuid")
    assert res["persona_name"] == "MockAriel"
    assert res["constraint_dimensionality"] == 0
    assert "class" in res
    assert "static_token_cost" in res


def test_mcp_wake_reuses_active_session(mock_mcp_env, monkeypatch):
    # Mock get_active_session_id to return an active session id
    monkeypatch.setattr(mcp_server, "get_active_session_id", lambda: "active-sess-id")
    
    # Initialize process tracker to None
    mcp_server._active_session_id = None
    
    # Mock start_session_logic to fail if called
    mock_start = MagicMock()
    monkeypatch.setattr(mcp_server, "start_session_logic", mock_start)
    
    # Call wake
    mcp_server.wake()
    
    # Ensure start_session_logic was not called
    mock_start.assert_not_called()
    
    # Ensure process tracker is synchronized
    assert mcp_server._active_session_id == "active-sess-id"
