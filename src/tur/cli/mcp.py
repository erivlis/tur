import sys
from typing import Literal

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
def serve(
        transport: Literal['stdio', 'sse'] = typer.Option(
            'stdio',
            help="The transport protocol for the MCP server ('stdio' or 'sse')."
        ),
        port: int = typer.Option(8000, help="Port to use when transport is 'sse'."),
):
    """Run the Tur MCP server."""
    try:
        from tur.mcp_server import main as mcp_main

        console.print(f'[bold green]Starting Tur MCP server with {transport} transport...[/bold green]')
        mcp_main(transport=transport, port=port)
    except Exception as e:
        console.print(f'[red]Error starting server: {e}[/red]')
        sys.exit(1)


def main():
    app()


if __name__ == '__main__':
    main()
