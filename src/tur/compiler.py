from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tur.models import SessionState

_TEMPLATE_DIR = Path(__file__).parent / 'templates'
_JINJA_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=10,
)
_PERSONA_TEMPLATE = _JINJA_ENV.get_template('persona.j2')


def compile_persona(state: SessionState) -> str:
    """
    Renders a SessionState into a final System Prompt string using pre-compiled AST.
    """
    return _PERSONA_TEMPLATE.render(state.model_dump())
