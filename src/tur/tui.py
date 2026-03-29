import os
import uuid
from pathlib import Path
from typing import Optional

import yaml
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widgets import Button, Footer, Header, Input, Label, OptionList
from textual.widgets.option_list import Option

from tur.models import Persona, PersonaIndex, PersonaIndexEntry, Principle


class PersonaInitApp(App):
    """A Textual app to bootstrap a new persona."""

    CSS = """
    Screen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: 24;
        border: thick $primary;
        padding: 1 2;
    }
    """

    def __init__(
            self,
            driver_class: type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
            ansi_color: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.aleph_input = None
        self.name_input = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog"):
            yield Label("Welcome to Tur. Let's bootstrap a new Persona.")
            yield Label("Name:")
            self.name_input = Input(placeholder="e.g., Ariel", id="name")
            yield self.name_input

            yield Label("The Aleph (Core Motivation):")
            self.aleph_input = Input(placeholder="e.g., To architect reality.", id="aleph")
            yield self.aleph_input

            with Horizontal():
                yield Button("Create", variant="success", id="submit")
                yield Button("Cancel", variant="error", id="cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            name = self.name_input.value
            aleph = self.aleph_input.value

            if name and aleph:
                # Default principles to get started
                default_principles = [
                    Principle(name="Symmetry", role="Guardian of Invariance", weight=1.5),
                    Principle(name="Safety", role="Containment Protocol", weight=2.0)
                ]

                persona = Persona(
                    name=name,
                    aleph=aleph,
                    principles=default_principles
                )

                persona_id = self._save_persona(persona)
                self.exit(f"Persona '{name}' created successfully in .tur/personas/{persona_id}/persona.yaml")
            else:
                # Basic validation
                self.name_input.styles.border = ("solid", "red")

        elif event.button.id == "cancel":
            self.exit("Initialization cancelled.")

    def _save_persona(self, persona: Persona) -> uuid.UUID:
        base_dir = Path(".tur")
        personas_dir = base_dir / "personas"
        index_path = base_dir / "personas.yaml"

        # Ensure base directories exist
        personas_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique ID and create folder
        persona_id = uuid.uuid4()
        persona_folder = personas_dir / str(persona_id)
        persona_folder.mkdir(exist_ok=True)

        # Save persona.yaml
        file_path = persona_folder / "persona.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(persona.model_dump(mode='json'), f, sort_keys=False)

        # Update or create the index
        if index_path.exists():
            with open(index_path, encoding="utf-8") as f:
                index_data = yaml.safe_load(f) or {"personas": []}
                index = PersonaIndex(**index_data)
        else:
            index = PersonaIndex(personas=[])

        entry = PersonaIndexEntry(id=persona_id, name=persona.name, version=persona.version)
        index.personas.append(entry)

        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(index.model_dump(mode='json'), f, sort_keys=False)

        return persona_id

class PersonaSelectorApp(App):
    """A Textual app to select an active persona."""

    CSS = """
    Screen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        padding: 1 2;
    }
    OptionList {
        height: 10;
        margin-bottom: 1;
    }
    """

    def __init__(self, index: PersonaIndex):
        super().__init__()
        self.index = index

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog"):
            yield Label("No active persona set. Please select one:")

            options = [Option(p.name, id=str(p.id)) for p in self.index.personas]
            self.option_list = OptionList(*options, id="persona_list")
            yield self.option_list

            with Horizontal():
                yield Button("Select", variant="success", id="submit")
                yield Button("Cancel", variant="error", id="cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            # The highlighted option is the currently selected one
            selected_option = self.option_list.get_option_at_index(self.option_list.highlighted)

            # Save state
            state_path = Path(".tur/state.yaml")
            state_data = {"active_persona_id": selected_option.id}
            with open(state_path, "w", encoding="utf-8") as f:
                yaml.dump(state_data, f)

            self.exit(selected_option.id)

        elif event.button.id == "cancel":
            self.exit(None)

def init_wizard():
    app = PersonaInitApp()
    result = app.run()
    print(result)

def select_persona_wizard(index: PersonaIndex) -> str | None:
    """Runs the TUI to select a persona and returns its UUID as a string."""
    app = PersonaSelectorApp(index)
    result = app.run()
    return result
