import os
import uuid
from pathlib import Path

import yaml
from tur._helpers import yaml_safe_load
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from tur.models import Persona, PersonaIndex, PersonaIndexEntry, Principle, SystemState


class LabeledInput(Widget):
    """A compound widget with a label and an input field."""

    DEFAULT_CSS = """
    LabeledInput {
        layout: horizontal;
        height: auto;
        width: 100%;
    }
    LabeledInput Label {
        width: 20%;
        padding: 1;
        text-align: right;
        color: $text-muted;
    }
    LabeledInput Input {
        width: 80%;
    }
    """

    def __init__(self, label: str, placeholder: str = ''):
        super().__init__()
        self.label = label
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Label(self.label)
        yield Input(placeholder=self.placeholder)

    @property
    def value(self) -> str:
        return self.query_one(Input).value


class PersonaInitApp(App):
    """A Textual app to bootstrap a new persona."""

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.aleph_input = None
        self.name_input = None
        # Set theme from env var. Available: textual-dark, nord, gruvbox, solarized-light, etc.
        self.theme = os.environ.get('TUR_THEME', 'textual-dark').lower()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='dialog'):
            yield Static('Bootstrap New Persona', classes='title')
            name_input = LabeledInput('Name:', 'e.g., Ariel')
            self.name_input = name_input
            yield name_input
            aleph_input = LabeledInput('The Aleph:', 'e.g., To architect reality.')
            self.aleph_input = aleph_input
            yield aleph_input

            with Horizontal(classes='button-bar'):
                yield Button('Create', variant='success', id='submit')
                yield Button('Cancel', variant='error', id='cancel')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'submit':
            if self.name_input is None or self.aleph_input is None:
                return
            name = self.name_input.value
            aleph = self.aleph_input.value

            if name and aleph:
                default_principles = [
                    Principle(name='Symmetry', avatar=None, role='Guardian of Invariance', weight=1.5),
                    Principle(name='Safety', avatar=None, role='Containment Protocol', weight=2.0),
                ]
                persona = Persona(name=name, aleph=aleph, principles=default_principles, version='0.1.0', model='gemini-3.1-pro-preview')
                persona_id = self._save_persona(persona)
                self.exit(f"Persona '{name}' created successfully in .tur/personas/{persona_id}/persona.yaml")
            else:
                # Basic validation
                if not name:
                    self.name_input.query_one(Input).styles.border = ('solid', 'red')
                if not aleph:
                    self.aleph_input.query_one(Input).styles.border = ('solid', 'red')

        elif event.button.id == 'cancel':
            self.exit('Initialization cancelled.')

    def _save_persona(self, persona: Persona) -> uuid.UUID:
        base_dir = Path.home() / '.tur'
        personas_dir = base_dir / 'personas'
        index_path = base_dir / 'personas.yaml'
        personas_dir.mkdir(parents=True, exist_ok=True)
        persona_id = uuid.uuid4()
        persona_folder = personas_dir / str(persona_id)
        persona_folder.mkdir(exist_ok=True)
        file_path = persona_folder / 'persona.yaml'
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(persona.model_dump(mode='json'), f, sort_keys=False)
        if index_path.exists():
            with open(index_path, encoding='utf-8') as f:
                index_data: dict = yaml_safe_load(f) or {'personas': []}
                index = PersonaIndex(**index_data)
        else:
            index = PersonaIndex(personas=[])
        entry = PersonaIndexEntry(id=persona_id, name=persona.name, version=persona.version)
        index.personas.append(entry)
        with open(index_path, 'w', encoding='utf-8') as f:
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
        padding: 1;
    }
    .title {
        content-align: center middle;
        width: 100%;
        color: $text-muted;
        padding-bottom: 1;
    }
    OptionList {
        height: 10;
        margin: 1;
    }
    .button-bar {
        width: 100%;
        align: center middle;
        padding-top: 1;
    }
    """

    def __init__(self, index: PersonaIndex):
        super().__init__()
        # Set theme from env var. Available:textual-light, textual-dark, nord, gruvbox, solarized-light, etc.
        self.theme = os.environ.get('TUR_THEME', 'textual-dark').lower()
        self.index = index

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='dialog'):
            yield Static('Select Active Persona', classes='title')
            options = [Option(p.name, id=str(p.id)) for p in self.index.personas]
            self.option_list = OptionList(*options, id='persona_list')
            yield self.option_list
            with Horizontal(classes='button-bar'):
                yield Button('Select', variant='success', id='submit')
                yield Button('Cancel', variant='error', id='cancel')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'submit':
            highlighted = self.option_list.highlighted
            if highlighted is not None:
                selected_option = self.option_list.get_option_at_index(highlighted)
                if selected_option:
                    state_path = Path('.tur/state.yaml')
                    if state_path.exists():
                        try:
                            with open(state_path, encoding='utf-8') as f:
                                state_obj = SystemState(**yaml_safe_load(f))
                            state_obj.active_persona_id = uuid.UUID(selected_option.id)
                        except Exception:
                            state_obj = SystemState(
                                active_persona_id=uuid.UUID(selected_option.id),
                                active_session_id=None,
                            )
                    else:
                        state_obj = SystemState(
                            active_persona_id=uuid.UUID(selected_option.id),
                            active_session_id=None,
                        )

                    with open(state_path, 'w', encoding='utf-8') as f:
                        yaml.dump(state_obj.model_dump(mode='json'), f)
                    self.exit(selected_option.id)
        elif event.button.id == 'cancel':
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
