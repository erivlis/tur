import functools
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import typer
from rich.console import Console

from tur.locking import LockTimeoutError

console = Console()


F = TypeVar('F', bound=Callable[..., Any])


def handle_cli_error(e: Exception, context_msg: str = 'Error') -> None:
    """Standardized CLI exception formatting and exit code handling."""
    if isinstance(e, typer.Exit):
        raise e
    if isinstance(e, LockTimeoutError):
        console.print(f'[bold yellow]Contention Warning: State lock is held by another process: {e}[/bold yellow]')
        raise typer.Exit(code=1) from e
    console.print(f'[red]{context_msg}: {e}[/red]')
    raise typer.Exit(code=1) from e


def run_scaffold_cli(format: str, output: Path | None, force: bool) -> None:
    """Execute workspace scaffolding with standard feedback and error reporting."""
    from tur import scaffold

    try:
        path = scaffold.scaffold_workspace(format=format, force=force, output_file=output)
        console.print(f"[green]Successfully generated agent scaffolding at '[bold]{path}[/bold]'[/green]")
    except FileExistsError as e:
        console.print(f'[yellow]{e}[/yellow]')
        raise typer.Exit(code=1) from e
    except Exception as e:
        handle_cli_error(e, 'Error scaffolding workspace')


def get_memory_status_style(status: str | None) -> tuple[str, str]:
    """Returns (status_display, row_style) for memory table rendering."""
    if status == 'archived':
        return 'archived', 'dim'
    if status == 'pending_approval':
        return 'pending_approval', 'yellow'
    return 'active', ''


def get_session_status_style(status: str) -> str:
    """Returns Rich markup formatted session status string."""
    return f'[green]{status}[/green]' if status == 'active' else f'[dim]{status}[/dim]'


def require_human(func: F) -> F:
    """
    Heuristic TTY check used as a soft safety convention to discourage Harness Agents
    from executing administrative commands via headless shell execution.

    NOTE: This is a convention, not a security control.  sys.stdout.isatty() can be
    satisfied by pseudo-TTY wrappers.  Do not rely on this for hard security boundaries.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not sys.stdout.isatty():
            console.print('[red]Error: Administrative command invoked in a non-interactive shell.[/red]')
            console.print('[red]GOLEM PROTOCOL VIOLATION: Agents must use the MCP Server for state access.[/red]')
            raise typer.Exit(code=1)
        return func(*args, **kwargs)

    return cast(F, wrapper)
