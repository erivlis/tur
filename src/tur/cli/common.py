import functools
import sys

import typer
from rich.console import Console

console = Console()


from typing import Any, Callable, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])


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
