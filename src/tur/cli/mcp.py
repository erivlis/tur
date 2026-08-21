import sys

import typer

from tur.cli.common import console

app = typer.Typer(
    help='Tur: Harness Gateway and MCP Server.',
    context_settings={'help_option_names': ['-h', '--help']},
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode='rich',
)


@app.command()
def serve():
    """Run the Tur MCP server."""
    try:
        from tur.mcp_server import main as mcp_main
    except ImportError:
        from rich.console import Group
        from rich.panel import Panel
        from rich.syntax import Syntax

        code = 'pip install tur[mcp]\n# or\nuv pip install tur[mcp]'

        code_syntax = Syntax(code, 'shell', theme='monokai', line_numbers=True)

        code_panel = Panel(code_syntax, title='[cyan]Shell[/cyan]', border_style='cyan', expand=True)

        panel_contents = Group(
            "[bold red]Error: The 'mcp' package is required to run the Tur MCP server.[/bold red]\n\n"
            'Please install the mcp extra dependencies by running:\n',
            code_panel,
        )

        console.print(
            Panel(panel_contents, title='[bold red]Dependency Missing[/bold red]', border_style='red', expand=False)
        )
        sys.exit(1)

    try:
        mcp_main()
    except Exception as e:
        from rich.console import Console

        err_console = Console(stderr=True)
        err_console.print(f'[red]Error starting server: {e}[/red]')
        sys.exit(1)


def main():
    app()


if __name__ == '__main__':
    main()
