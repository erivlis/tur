import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from typer.testing import CliRunner

from tur import cli, dreaming, persona, session, tui, user
from tur.cli import app

runner = CliRunner()


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    # Setup directories
    dot_tur = tmp_path / ".tur"
    dot_tur.mkdir()
    personas_dir = dot_tur / "personas"
    personas_dir.mkdir()

    # Fake user profile
    user_data = {
        "name": "Test Architect",
        "role": "Architect",
        "domain_expertise": ["Software Engineering"],
        "core_values": ["Determinism"]
    }
    with open(dot_tur / "user.yaml", "w", encoding="utf-8") as f:
        yaml.dump(user_data, f)

    # Fake persona index
    persona_id_1 = "7544202e-92f5-40ce-adfb-e4b0eae6c262"
    persona_id_2 = "fab6858c-e4ad-4adf-9e2d-0c86455917cf"

    index_data = {
        "personas": [
            {"id": persona_id_1, "name": "Ariel", "version": "5.4.0"},
            {"id": persona_id_2, "name": "Umbriel", "version": "1.0.0"}
        ]
    }
    with open(dot_tur / "personas.yaml", "w", encoding="utf-8") as f:
        yaml.dump(index_data, f)

    # Create directories for personas
    (personas_dir / persona_id_1 / "memories" / "archive").mkdir(parents=True)
    (personas_dir / persona_id_2 / "memories" / "archive").mkdir(parents=True)

    # Fake persona yaml files
    persona_1_yaml = {
        "name": "Ariel",
        "version": "5.4.0",
        "model": "gemini-3.1-pro-preview",
        "aleph": "To safeguard reality.",
        "principles": [
            {
                "name": "Symmetry",
                "avatar": "Noether",
                "role": "Guardian of Invariance",
                "constraints": ["Keep state timeline symmetric."],
                "weight": 1.5
            }
        ]
    }
    with open(personas_dir / persona_id_1 / "persona.yaml", "w", encoding="utf-8") as f:
        yaml.dump(persona_1_yaml, f)

    persona_2_yaml = {
        "name": "Umbriel",
        "version": "1.0.0",
        "model": "gemini-3.1-pro-preview",
        "aleph": "To discover truth.",
        "principles": []
    }
    with open(personas_dir / persona_id_2 / "persona.yaml", "w", encoding="utf-8") as f:
        yaml.dump(persona_2_yaml, f)

    # Fake state file
    state_data = {
        "active_persona_id": persona_id_1
    }
    with open(dot_tur / "state.yaml", "w", encoding="utf-8") as f:
        yaml.dump(state_data, f)

    # Change to fake workspace root
    monkeypatch.chdir(tmp_path)
    # Mock Path.home() so global directories also route to temp folder
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Mock human check by forcing sys.stdout.isatty to True via a dynamic SysProxy
    class StdoutProxy:
        def __getattr__(self, attr):
            if attr == "isatty":
                return lambda: True
            return getattr(sys.stdout, attr)

    class SysProxy:
        def __getattr__(self, name):
            if name == "stdout":
                return StdoutProxy()
            return getattr(sys, name)


    monkeypatch.setattr(cli, "sys", SysProxy())

    return tmp_path, persona_id_1, persona_id_2


def test_cli_help(mock_workspace):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Persona Lifecycle Manager" in result.stdout


def test_cli_wake_default(mock_workspace):
    result = runner.invoke(app, ["wake"])
    assert result.exit_code == 0
    assert "SYSTEM WAKE: Ariel" in result.stdout
    assert "To safeguard reality." in result.stdout


def test_cli_wake_by_name(mock_workspace):
    result = runner.invoke(app, ["wake", "Umbriel"])
    assert result.exit_code == 0
    assert "SYSTEM WAKE: Umbriel" in result.stdout


def test_cli_wake_invalid(mock_workspace):
    result = runner.invoke(app, ["wake", "InvalidPersona"])
    assert result.exit_code == 1
    assert "Error waking persona" in result.stdout


def test_cli_learn_and_recall(mock_workspace):
    # Learn fact
    result_learn = runner.invoke(app, ["learn", "Memory content fact description", "--type", "fact"])
    assert result_learn.exit_code == 0
    assert "Consolidating memory" in result_learn.stdout
    assert "Memory saved" in result_learn.stdout

    # Recall fact
    result_recall = runner.invoke(app, ["recall", "description"])
    assert result_recall.exit_code == 0
    assert "Memory content fact description" in result_recall.stdout


def test_cli_session_lifecycle(mock_workspace):
    # 1. Start a session
    result_start = runner.invoke(app, ["session", "start", "session-foo"])
    assert result_start.exit_code == 0
    assert "Session 'session-foo' started" in result_start.stdout

    notes_yaml = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/sessions/session-foo.yaml")
    assert notes_yaml.exists()

    # 2. Add a note to the session
    result_note = runner.invoke(app, ["note", "Updated in session", "--session-id", "session-foo"])
    assert result_note.exit_code == 0
    assert "successfully" in result_note.stdout
    assert "session-foo" in result_note.stdout

    # 3. Wake with session ID — prompt should contain the note content
    result_wake = runner.invoke(app, ["wake", "--session-id", "session-foo"])
    assert result_wake.exit_code == 0
    assert "SYSTEM WAKE" in result_wake.stdout
    assert "Session ID: session-foo" in result_wake.stdout
    assert "Updated in session" in result_wake.stdout

    # 4. End the session
    result_end = runner.invoke(app, ["session", "end", "session-foo"])
    assert result_end.exit_code == 0
    assert "Session 'session-foo' ended" in result_end.stdout


def test_cli_telemetry(mock_workspace):
    result = runner.invoke(app, ["telemetry", "Ariel"])
    assert result.exit_code == 0
    assert "TELEMETRY REPORT: Ariel" in result.stdout
    assert "Constraint Dimensionality (Cp): 1.5" in result.stdout


def test_cli_memories_empty(mock_workspace):
    result = runner.invoke(app, ["memories"])
    assert result.exit_code == 0
    assert "The Memory Bank for 7544202e-92f5-40ce-adfb-e4b0eae6c262 is empty." in result.stdout


def test_cli_memories_with_items(mock_workspace):
    # Store manual memory
    runner.invoke(app, ["learn", "Pytest is running.", "--type", "insight"])

    result = runner.invoke(app, ["memories"])
    assert result.exit_code == 0
    assert "Memory Bank (7544202e-92f5-40ce-adfb-e4b0eae6c262)" in result.stdout
    assert "Pytest is running." in result.stdout


def test_cli_forget(mock_workspace):
    # Store memory
    runner.invoke(app, ["learn", "Manual memory to be forgotten.", "--type", "insight"])

    # Read active memory list to find its ID
    active_mems = session.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262").memories
    assert len(active_mems) == 1
    mem_id = active_mems[0].id

    # Forget it
    result_forget = runner.invoke(app, ["forget", mem_id])
    assert result_forget.exit_code == 0
    assert f"Memory {mem_id} has been forgotten" in result_forget.stdout

    # Verify it is no longer in active list
    active_mems_after = session.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262").memories
    assert len(active_mems_after) == 0


def test_cli_clone(mock_workspace):
    result = runner.invoke(app, ["clone", "Ariel", "ArielClone"])
    assert result.exit_code == 0
    assert "successfully cloned to 'ArielClone'" in result.stdout

    # Verify both exist in personas.yaml index now
    with open(".tur/personas.yaml", encoding="utf-8") as f:
        index_data = yaml.safe_load(f)
    assert len(index_data["personas"]) == 3
    assert any(p["name"] == "ArielClone" for p in index_data["personas"])


def test_cli_sleep(mock_workspace, monkeypatch):
    monkeypatch.setattr(dreaming, "perform_sleep_dreaming", lambda **kwargs: 2)

    log_path = Path("fake_chat.log")
    log_path.write_text("User: Hello\nAgent: Hi", encoding="utf-8")

    result = runner.invoke(app, ["sleep", str(log_path), "--note", "Test sleep note"])
    assert result.exit_code == 0
    assert "Dreams consolidated. 2 new memories formed." in result.stdout


def test_cli_sleep_exception(mock_workspace, monkeypatch):
    def raise_err(**kwargs):
        raise RuntimeError("LLM Failure")

    monkeypatch.setattr(dreaming, "perform_sleep_dreaming", raise_err)

    log_path = Path("fake_chat.log")
    log_path.write_text("User: Hello\nAgent: Hi", encoding="utf-8")

    result = runner.invoke(app, ["sleep", str(log_path), "--note", "Test sleep note"])
    assert result.exit_code == 0  # CLI prints error but exits gracefully
    assert "Error during dreaming: LLM Failure" in result.stdout


def test_cli_golem_protocol_violation(mock_workspace, monkeypatch):
    # Force sys.stdout.isatty to False via a FalseSysProxy
    class FalseStdoutProxy:
        def __getattr__(self, attr):
            if attr == "isatty":
                return lambda: False
            return getattr(sys.stdout, attr)

    class FalseSysProxy:
        def __getattr__(self, name):
            if name == "stdout":
                return FalseStdoutProxy()
            return getattr(sys, name)


    monkeypatch.setattr(cli, "sys", FalseSysProxy())

    # Try calling clone (decorated with require_human)
    result = runner.invoke(app, ["clone", "Ariel", "ArielClone"])
    assert result.exit_code == 1
    assert "GOLEM PROTOCOL VIOLATION" in result.stdout


def test_cli_init_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock()
    monkeypatch.setattr(tui, "init_wizard", mock_wizard)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    mock_wizard.assert_called_once()


def test_cli_switch_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value="fab6858c-e4ad-4adf-9e2d-0c86455917cf")
    monkeypatch.setattr(tui, "select_persona_wizard", mock_wizard)

    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0
    assert "Default persona switched to:" in result.stdout


def test_cli_switch_cancelled(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value=None)
    monkeypatch.setattr(tui, "select_persona_wizard", mock_wizard)

    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0
    assert "Switch cancelled." in result.stdout


def test_cli_switch_error(mock_workspace, monkeypatch):
    def raise_err(*args, **kwargs):
        raise RuntimeError("TUI error")

    monkeypatch.setattr(tui, "select_persona_wizard", raise_err)

    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "Error switching persona" in result.stdout


def test_get_user_profile_global_path(mock_workspace, monkeypatch):
    # Remove local user.yaml
    Path(".tur/user.yaml").unlink()

    # Create global user.yaml in fake home
    global_dir = Path.home() / ".tur"
    global_dir.mkdir(parents=True, exist_ok=True)

    global_user_data = {
        "name": "Global Architect",
        "role": "Consultant",
        "domain_expertise": ["Cloud Systems"],
        "core_values": ["Adaptability"]
    }
    with open(global_dir / "user.yaml", "w", encoding="utf-8") as f:
        yaml.dump(global_user_data, f)

    profile = user.get_user_profile()
    assert profile.name == "Global Architect"


def test_get_user_profile_fallback(mock_workspace):
    # Remove local user.yaml
    Path(".tur/user.yaml").unlink()
    # Path.home() has no config

    profile = user.get_user_profile()
    assert profile.name == "Default User"
    assert "Software Development" in profile.domain_expertise


def test_get_active_persona_id_env_and_selector(mock_workspace, monkeypatch):
    # 1. Resolve via env variable
    monkeypatch.setenv("TUR_ACTIVE_PERSONA_ID", "env-persona-id")
    assert persona.get_active_persona_id() == "env-persona-id"
    monkeypatch.delenv("TUR_ACTIVE_PERSONA_ID")

    # 2. Resolve via selector wizard when state.yaml is missing
    Path(".tur/state.yaml").unlink()
    mock_select = MagicMock(return_value="fab6858c-e4ad-4adf-9e2d-0c86455917cf")
    import tur.persona
    monkeypatch.setattr(tur.persona, "select_persona_wizard", mock_select)

    assert persona.get_active_persona_id() == "fab6858c-e4ad-4adf-9e2d-0c86455917cf"


def test_get_persona_path_missing_index(mock_workspace):
    Path(".tur/personas.yaml").unlink()
    with pytest.raises(FileNotFoundError):
        persona.get_persona_path("Ariel")


def test_hydrate_session_state_missing_epilogue(mock_workspace):
    state = session.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262")
    # Verify default epilogue when epilogue.md does not exist
    assert "Status: Conserved. Aleph: Restored." in state.epilogue


def test_cli_telemetry_giant_and_titan_classes(mock_workspace):
    # Modify Ariel's principles to trigger Giant class (Cp >= 5 and < 10)
    persona_path = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/persona.yaml")
    with open(persona_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["principles"] = [
        {"name": f"P{i}", "role": "G", "constraints": ["C"], "weight": 1.5}
        for i in range(4)
    ]
    with open(persona_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    result_giant = runner.invoke(app, ["telemetry", "Ariel"])
    assert result_giant.exit_code == 0
    assert "Class: Giant" in result_giant.stdout or "Heavy Load" in result_giant.stdout

    # Modify Ariel's principles to trigger Titan class (Cp >= 10)
    data["principles"] = [
        {"name": f"P{i}", "role": "G", "constraints": ["C"], "weight": 2.0}
        for i in range(10)
    ]
    with open(persona_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    result_titan = runner.invoke(app, ["telemetry", "Ariel"])
    assert result_titan.exit_code == 0
    assert "Class: Titan" in result_titan.stdout or "Inference Warning" in result_titan.stdout


def test_cli_serve_call(mock_workspace, monkeypatch):
    from tur import mcp_server
    mock_mcp_main = MagicMock()
    monkeypatch.setattr(mcp_server, "main", mock_mcp_main)

    result = runner.invoke(app, ["serve", "--transport", "stdio"])
    assert result.exit_code == 0
    assert "Starting Tur MCP server" in result.stdout


def test_perform_sleep_dreaming(mock_workspace, monkeypatch):
    # Set fake Gemini API Key
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    # Mock google-genai Client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        '{"memories": [{"type": "fact", "content": "Pytest is fast", '
        '"scope": "incarnation", "tags": ["test"]}]}'
    )
    mock_client.models.generate_content.return_value = mock_response

    # Monkeypatch the Client to return our mocked client
    from google import genai
    monkeypatch.setattr(genai, "Client", lambda api_key: mock_client)

    count = dreaming.perform_sleep_dreaming(
        log_content="User: hello",
        active_id="7544202e-92f5-40ce-adfb-e4b0eae6c262"
    )
    assert count == 1

    # Verify the memory was saved in the state
    state = session.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262")
    assert len(state.memories) == 1
    assert state.memories[0].content == "Pytest is fast"


def test_perform_sleep_dreaming_missing_api_key(mock_workspace, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError) as exc:
        dreaming.perform_sleep_dreaming(
            log_content="User: hello",
            active_id="7544202e-92f5-40ce-adfb-e4b0eae6c262"
        )
    assert "GEMINI_API_KEY environment variable not set" in str(exc.value)


def test_get_active_persona_id_missing_personas_yaml(mock_workspace, monkeypatch):
    # Remove state and personas files
    Path(".tur/state.yaml").unlink()
    Path(".tur/personas.yaml").unlink()

    with pytest.raises(FileNotFoundError) as exc:
        persona.get_active_persona_id()
    assert "No personas found." in str(exc.value)


def test_get_active_persona_id_empty_personas(mock_workspace, monkeypatch):
    # Remove state file
    Path(".tur/state.yaml").unlink()

    # Empty out the personas list in index
    with open(".tur/personas.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"personas": []}, f)

    with pytest.raises(ValueError) as exc:
        persona.get_active_persona_id()
    assert "No personas available to select." in str(exc.value)


def test_get_active_persona_id_selector_returns_none(mock_workspace, monkeypatch):
    # Remove state file
    Path(".tur/state.yaml").unlink()

    # Mock select_persona_wizard in tur.persona module namespace to return None
    import tur.persona
    monkeypatch.setattr(tur.persona, "select_persona_wizard", lambda index: None)

    import typer
    with pytest.raises(typer.Exit) as exc:
        persona.get_active_persona_id()
    assert "No persona selected" in str(exc.value)


def test_hydrate_session_state_with_session_notes(mock_workspace):
    # Create a session with a note so hydrate can pick it up
    session_parent = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/sessions")
    session_parent.mkdir(parents=True, exist_ok=True)
    notes_yaml = session_parent / "test-hydrate-session.yaml"
    import yaml as _yaml
    _yaml.dump({"notes": [{"timestamp": "2026-01-01T00:00:00", "content": "Hello from notes"}]},
               notes_yaml.open("w", encoding="utf-8"))
    # Also register the session in sessions.yaml
    sessions_yaml = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/sessions.yaml")
    _yaml.dump({"active_session_id": "test-hydrate-session",
                "sessions": [{"id": "test-hydrate-session", "status": "active",
                              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}]},
               sessions_yaml.open("w", encoding="utf-8"))

    state = session.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262",
                                       session_id="test-hydrate-session")
    assert state.epilogue == "Hello from notes"


def test_get_active_persona_id_state_exists_but_no_id(mock_workspace, monkeypatch):
    # Write a state file without active_persona_id
    with open(".tur/state.yaml", "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    # Mock select_persona_wizard under tur.persona module namespace
    import tur.persona
    monkeypatch.setattr(tur.persona, "select_persona_wizard", lambda index: "7544202e-92f5-40ce-adfb-e4b0eae6c262")
    assert persona.get_active_persona_id() == "7544202e-92f5-40ce-adfb-e4b0eae6c262"


def test_cli_clone_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError("Clone failed internally")

    monkeypatch.setattr(persona, "get_persona_path", mock_raise)

    result = runner.invoke(app, ["clone", "Ariel", "ArielClone"])
    assert result.exit_code == 0
    assert "Error cloning persona: Clone failed internally" in result.stdout


def test_cli_forget_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Forget failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["forget", "some-memory-id"])
    assert result.exit_code == 0
    assert "Error: Forget failed" in result.stdout


def test_cli_memories_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Memories failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["memories"])
    assert result.exit_code == 0
    assert "Error: Memories failed" in result.stdout


def test_cli_learn_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Learn failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["learn", "Memory content fact description"])
    assert result.exit_code == 0
    assert "Error: Learn failed" in result.stdout


def test_cli_recall_no_match(mock_workspace):
    result = runner.invoke(app, ["recall", "completely-unmatched-query-string"])
    assert result.exit_code == 0
    assert "No memories found matching query" in result.stdout


def test_cli_recall_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Recall failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["recall", "description"])
    assert result.exit_code == 0
    assert "Error: Recall failed" in result.stdout


def test_cli_sleep_top_level_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Sleep top-level failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["sleep", "fake_chat.log", "--note", "Test sleep note"])
    assert result.exit_code == 0
    assert "Error: Sleep top-level failed" in result.stdout


def test_cli_switch_missing_personas_yaml(mock_workspace):
    Path(".tur/personas.yaml").unlink()
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "No personas found. Please run `tur init` to create one." in result.stdout


def test_cli_switch_empty_personas(mock_workspace):
    with open(".tur/personas.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"personas": []}, f)
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "No personas available to select. Please run `tur init`." in result.stdout


def test_cli_telemetry_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Telemetry failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["telemetry", "Ariel"])
    assert result.exit_code == 1
    assert "Error calculating telemetry: Telemetry failed" in result.stdout


def test_cli_wake_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Wake failed")

    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["wake"])
    assert result.exit_code == 1
    assert "Error waking persona: Wake failed" in result.stdout


def test_cli_module_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tur", "--help"])

    import runpy
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("tur.cli", run_name="__main__")

    assert exc.value.code == 0


def test_cli_status(mock_workspace):
    # No active session yet
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Tur Status" in result.stdout
    assert "Ariel" in result.stdout
    assert "Status" in result.stdout
    assert "none" in result.stdout

    # Now start one
    runner.invoke(app, ["session", "start", "session-status-test"])
    result_active = runner.invoke(app, ["status"])
    assert result_active.exit_code == 0
    assert "Status" in result_active.stdout
    assert "active" in result_active.stdout
    assert "session-status-test" in result_active.stdout

    # Add a long note (> 80 chars) to test snippet truncation
    long_content = (
        "A very long note that exceeds eighty characters in length to test "
        "the truncation snippet rendering logic inside the CLI status command table."
    )
    runner.invoke(app, ["note", long_content, "--session-id", "session-status-test"])
    result_long_note = runner.invoke(app, ["status"])
    assert result_long_note.exit_code == 0
    assert "…" in result_long_note.stdout

    # Now end it and check status to trigger "last" session branch
    runner.invoke(app, ["session", "end", "session-status-test"])
    result_ended = runner.invoke(app, ["status"])
    assert result_ended.exit_code == 0
    assert "session-status-test" in result_ended.stdout
    assert "ended" in result_ended.stdout


def test_cli_status_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError("Status error")
    monkeypatch.setattr(persona, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Error: Status error" in result.stdout


def test_cli_session_start_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError("Start failed")
    monkeypatch.setattr(session, "start_session_logic", mock_raise)

    result = runner.invoke(app, ["session", "start", "err-sess"])
    assert result.exit_code == 1
    assert "Error starting session: Start failed" in result.stdout


def test_cli_session_end_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError("End failed")
    monkeypatch.setattr(session, "end_session_logic", mock_raise)

    result = runner.invoke(app, ["session", "end", "err-sess"])
    assert result.exit_code == 1
    assert "Error ending session: End failed" in result.stdout


def test_cli_wake_auto_start(mock_workspace):
    # Ensure active_session_id is None under state.yaml
    state_path = Path(".tur/state.yaml")
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump({"active_persona_id": "7544202e-92f5-40ce-adfb-e4b0eae6c262", "active_session_id": None}, f)

    result = runner.invoke(app, ["wake"])
    assert result.exit_code == 0
    assert "Auto-started new session" in result.stdout


def test_cli_session_start_previous_seeding(mock_workspace):
    # Start session 1
    runner.invoke(app, ["session", "start", "session-prev"])
    # Append a note to session 1
    runner.invoke(app, ["note", "First session final note.", "--session-id", "session-prev"])
    # Start session 2 seeding from session 1 via main logic
    from tur import cli, session
    session.start_session_logic("session-next", previous_session_id="session-prev")

    # Verify the seed content is inherited
    persona_dir = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262")
    seed_content = session.compile_session_notes(persona_dir, "session-next")
    assert seed_content == "First session final note."
