import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from typer.testing import CliRunner

from tur import main
from tur.main import app

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

    monkeypatch.setattr(main, "sys", SysProxy())

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


def test_cli_spark(mock_workspace):
    result = runner.invoke(app, ["spark", "Updating epilogue spark"])
    assert result.exit_code == 0
    assert "Spark updated for" in result.stdout

    # Check epilogue.md file was updated
    epilogue_path = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/epilogue.md")
    assert epilogue_path.exists()
    assert epilogue_path.read_text(encoding="utf-8").strip() == "Updating epilogue spark"


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
    active_mems = main.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262").memories
    assert len(active_mems) == 1
    mem_id = active_mems[0].id

    # Forget it
    result_forget = runner.invoke(app, ["forget", mem_id])
    assert result_forget.exit_code == 0
    assert f"Memory {mem_id} has been forgotten" in result_forget.stdout

    # Verify it is no longer in active list
    active_mems_after = main.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262").memories
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
    monkeypatch.setattr(main, "perform_sleep_dreaming", lambda **kwargs: 2)

    log_path = Path("fake_chat.log")
    log_path.write_text("User: Hello\nAgent: Hi", encoding="utf-8")

    result = runner.invoke(app, ["sleep", str(log_path)])
    assert result.exit_code == 0
    assert "Dreams consolidated. 2 new memories formed." in result.stdout


def test_cli_sleep_exception(mock_workspace, monkeypatch):
    def raise_err(**kwargs):
        raise RuntimeError("LLM Failure")
    monkeypatch.setattr(main, "perform_sleep_dreaming", raise_err)

    log_path = Path("fake_chat.log")
    log_path.write_text("User: Hello\nAgent: Hi", encoding="utf-8")

    result = runner.invoke(app, ["sleep", str(log_path)])
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

    monkeypatch.setattr(main, "sys", FalseSysProxy())

    # Try calling clone (decorated with require_human)
    result = runner.invoke(app, ["clone", "Ariel", "ArielClone"])
    assert result.exit_code == 1
    assert "GOLEM PROTOCOL VIOLATION" in result.stdout


def test_cli_init_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock()
    monkeypatch.setattr(main, "init_wizard", mock_wizard)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    mock_wizard.assert_called_once()


def test_cli_switch_mocked(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value="fab6858c-e4ad-4adf-9e2d-0c86455917cf")
    monkeypatch.setattr(main, "select_persona_wizard", mock_wizard)

    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0
    assert "Default persona switched to:" in result.stdout


def test_cli_switch_cancelled(mock_workspace, monkeypatch):
    mock_wizard = MagicMock(return_value=None)
    monkeypatch.setattr(main, "select_persona_wizard", mock_wizard)

    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0
    assert "Switch cancelled." in result.stdout


def test_cli_switch_error(mock_workspace, monkeypatch):
    def raise_err(*args, **kwargs):
        raise RuntimeError("TUI error")
    monkeypatch.setattr(main, "select_persona_wizard", raise_err)

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

    profile = main.get_user_profile()
    assert profile.name == "Global Architect"


def test_get_user_profile_fallback(mock_workspace):
    # Remove local user.yaml
    Path(".tur/user.yaml").unlink()
    # Path.home() has no config

    profile = main.get_user_profile()
    assert profile.name == "Default User"
    assert "Software Development" in profile.domain_expertise


def test_get_active_persona_id_env_and_selector(mock_workspace, monkeypatch):
    # 1. Resolve via env variable
    monkeypatch.setenv("TUR_ACTIVE_PERSONA_ID", "env-persona-id")
    assert main.get_active_persona_id() == "env-persona-id"
    monkeypatch.delenv("TUR_ACTIVE_PERSONA_ID")

    # 2. Resolve via selector wizard when state.yaml is missing
    Path(".tur/state.yaml").unlink()
    mock_select = MagicMock(return_value="fab6858c-e4ad-4adf-9e2d-0c86455917cf")
    monkeypatch.setattr(main, "select_persona_wizard", mock_select)

    assert main.get_active_persona_id() == "fab6858c-e4ad-4adf-9e2d-0c86455917cf"


def test_get_persona_path_missing_index(mock_workspace):
    Path(".tur/personas.yaml").unlink()
    with pytest.raises(FileNotFoundError):
        main.get_persona_path("Ariel")


def test_hydrate_session_state_missing_epilogue(mock_workspace):
    state = main.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262")
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

    count = main.perform_sleep_dreaming(
        log_content="User: hello",
        active_id="7544202e-92f5-40ce-adfb-e4b0eae6c262"
    )
    assert count == 1

    # Verify the memory was saved in the state
    state = main.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262")
    assert len(state.memories) == 1
    assert state.memories[0].content == "Pytest is fast"


def test_perform_sleep_dreaming_missing_api_key(mock_workspace, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError) as exc:
        main.perform_sleep_dreaming(
            log_content="User: hello",
            active_id="7544202e-92f5-40ce-adfb-e4b0eae6c262"
        )
    assert "GEMINI_API_KEY environment variable not set" in str(exc.value)


def test_get_active_persona_id_missing_personas_yaml(mock_workspace, monkeypatch):
    # Remove state and personas files
    Path(".tur/state.yaml").unlink()
    Path(".tur/personas.yaml").unlink()

    with pytest.raises(FileNotFoundError) as exc:
        main.get_active_persona_id()
    assert "No personas found." in str(exc.value)


def test_get_active_persona_id_empty_personas(mock_workspace, monkeypatch):
    # Remove state file
    Path(".tur/state.yaml").unlink()

    # Empty out the personas list in index
    with open(".tur/personas.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"personas": []}, f)

    with pytest.raises(ValueError) as exc:
        main.get_active_persona_id()
    assert "No personas available to select." in str(exc.value)


def test_get_active_persona_id_selector_returns_none(mock_workspace, monkeypatch):
    # Remove state file
    Path(".tur/state.yaml").unlink()

    # Mock select_persona_wizard to return None
    monkeypatch.setattr(main, "select_persona_wizard", lambda index: None)

    import typer
    with pytest.raises(typer.Exit) as exc:
        main.get_active_persona_id()
    assert "No persona selected" in str(exc.value)


def test_hydrate_session_state_with_epilogue(mock_workspace):
    # Write a fake epilogue file
    epilogue_path = Path(".tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/epilogue.md")
    epilogue_path.write_text("Hello Epilogue", encoding="utf-8")

    state = main.hydrate_session_state("7544202e-92f5-40ce-adfb-e4b0eae6c262")
    assert state.epilogue == "Hello Epilogue"


def test_get_active_persona_id_state_exists_but_no_id(mock_workspace, monkeypatch):
    # Write a state file without active_persona_id
    with open(".tur/state.yaml", "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    # Mock select_persona_wizard to return a mock persona ID so it resolves it
    monkeypatch.setattr(main, "select_persona_wizard", lambda index: "7544202e-92f5-40ce-adfb-e4b0eae6c262")
    assert main.get_active_persona_id() == "7544202e-92f5-40ce-adfb-e4b0eae6c262"


def test_cli_clone_error(mock_workspace, monkeypatch):
    def mock_raise(*args, **kwargs):
        raise RuntimeError("Clone failed internally")
    monkeypatch.setattr(main, "get_persona_path", mock_raise)

    result = runner.invoke(app, ["clone", "Ariel", "ArielClone"])
    assert result.exit_code == 0
    assert "Error cloning persona: Clone failed internally" in result.stdout


def test_cli_forget_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Forget failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["forget", "some-memory-id"])
    assert result.exit_code == 0
    assert "Error: Forget failed" in result.stdout


def test_cli_memories_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Memories failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["memories"])
    assert result.exit_code == 0
    assert "Error: Memories failed" in result.stdout


def test_cli_learn_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Learn failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

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
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["recall", "description"])
    assert result.exit_code == 0
    assert "Error: Recall failed" in result.stdout


def test_cli_spark_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Spark failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["spark", "new content"])
    assert result.exit_code == 1
    assert "Error saving spark: Spark failed" in result.stdout


def test_cli_sleep_top_level_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Sleep top-level failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["sleep", "fake_chat.log"])
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
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["telemetry", "Ariel"])
    assert result.exit_code == 1
    assert "Error calculating telemetry: Telemetry failed" in result.stdout


def test_cli_wake_error(mock_workspace, monkeypatch):
    def mock_raise(*args):
        raise RuntimeError("Wake failed")
    monkeypatch.setattr(main, "get_active_persona_id", mock_raise)

    result = runner.invoke(app, ["wake"])
    assert result.exit_code == 1
    assert "Error waking persona: Wake failed" in result.stdout


def test_cli_module_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tur", "--help"])

    import runpy
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("tur.main", run_name="__main__")

    assert exc.value.code == 0




