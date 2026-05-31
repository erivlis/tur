import os
import sys
import pytest
import yaml
import uuid
from pathlib import Path

from tur.tui import PersonaInitApp, PersonaSelectorApp, LabeledInput, init_wizard, select_persona_wizard
from tur.models import PersonaIndex, PersonaIndexEntry

@pytest.fixture
def mock_tui_workspace(tmp_path, monkeypatch):
    dot_tur = tmp_path / '.tur'
    dot_tur.mkdir()
    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / 'fake_home'
    fake_home.mkdir()
    monkeypatch.setattr(Path, 'home', lambda: fake_home)
    return tmp_path

async def test_persona_init_app_submit(mock_tui_workspace):
    app = PersonaInitApp()
    async with app.run_test() as pilot:
        # Fill name
        name_input = app.name_input.query_one("Input")
        name_input.value = "NewPersona"
        
        # Fill aleph
        aleph_input = app.aleph_input.query_one("Input")
        aleph_input.value = "To do cool stuff."
        
        # Click submit
        await pilot.click("#submit")
        
    assert app.return_value is not None
    assert "NewPersona" in app.return_value
    
    # Verify file was written inside fake home
    personas_dir = mock_tui_workspace / 'fake_home' / '.tur' / 'personas'
    assert personas_dir.exists()
    
    # There should be a subfolder containing persona.yaml
    subfolders = [x for x in personas_dir.iterdir() if x.is_dir()]
    assert len(subfolders) == 1
    assert (subfolders[0] / 'persona.yaml').exists()
    
    # Index should also exist and contain NewPersona
    index_path = mock_tui_workspace / 'fake_home' / '.tur' / 'personas.yaml'
    assert index_path.exists()
    with open(index_path, encoding='utf-8') as f:
        idx_data = yaml.safe_load(f)
    assert idx_data['personas'][0]['name'] == 'NewPersona'

async def test_persona_init_app_validation_fail(mock_tui_workspace):
    app = PersonaInitApp()
    async with app.run_test() as pilot:
        # Submit empty fields
        await pilot.click("#submit")
        
        # Styles should be solid red for both inputs due to validation failure
        assert app.name_input.query_one("Input").styles.border
        assert app.aleph_input.query_one("Input").styles.border

async def test_persona_init_app_cancel(mock_tui_workspace):
    app = PersonaInitApp()
    async with app.run_test() as pilot:
        await pilot.click("#cancel")
        
    assert app.return_value == "Initialization cancelled."

async def test_persona_selector_app_submit(mock_tui_workspace):
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    index = PersonaIndex(personas=[
        PersonaIndexEntry(id=pid1, name="ArielSelector", version="1.0"),
        PersonaIndexEntry(id=pid2, name="UmbrielSelector", version="2.0"),
    ])
    
    app = PersonaSelectorApp(index)
    async with app.run_test() as pilot:
        # Select first option (which is highlighted by default or we can click OptionList)
        await pilot.click("#submit")
        
    assert app.return_value == str(pid1)
    
    # State path in local .tur/state.yaml should be updated
    state_path = Path('.tur/state.yaml')
    assert state_path.exists()
    with open(state_path, encoding='utf-8') as f:
        state_data = yaml.safe_load(f)
    assert state_data['active_persona_id'] == str(pid1)

async def test_persona_selector_app_cancel(mock_tui_workspace):
    index = PersonaIndex(personas=[])
    app = PersonaSelectorApp(index)
    async with app.run_test() as pilot:
        await pilot.click("#cancel")
        
    assert app.return_value is None

def test_tui_labeled_input():
    widget = LabeledInput("Label", "Placeholder")
    assert widget.label == "Label"
    assert widget.placeholder == "Placeholder"

def test_init_wizard_and_select_wizard(mock_tui_workspace, monkeypatch):
    # Mock App.run to avoid running real TUI loop synchronously
    monkeypatch.setattr(PersonaInitApp, 'run', lambda self: "MockInitReturn")
    monkeypatch.setattr(PersonaSelectorApp, 'run', lambda self: "MockSelectorReturn")
    
    # Test wizard entrypoints
    init_wizard()
    res = select_persona_wizard(PersonaIndex(personas=[]))
    assert res == "MockSelectorReturn"
