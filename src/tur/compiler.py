import os

from jinja2 import Environment, FileSystemLoader

from tur.models import SessionState


def compile_persona(state: SessionState) -> str:
    """
    Renders a SessionState into a final System Prompt string.
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('persona.j2')

    return template.render(state.model_dump())
