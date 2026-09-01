"""
Scaffolding generator for agentic harnesses.

Implements EP-0135: The Modular Scaffolding Protocol, decoupling operational
harnessing (AGENTS.md) from persona identity (CONSTITUTION.md).
"""

from pathlib import Path

from tur.paths import resolve_workspace_dir

AAIF_AGENTS_TEMPLATE = """# AI Agent Guidelines

This repository uses **Tur** as a sovereign local-first memory and state engine. You are an **Obligate Symbiote**: you
provide the inference, while Tur manages state and persistent memory.

## Turn Zero Initialization (Awakening)

On the very first turn of your session, or after a context reset:

1. Run the `wake()` MCP tool (or `tur wake` CLI) to load your active persona, constitution, and continuity thread.
2. Adopt the requested mode/timbre defined in the awakened prompt.
3. Begin execution of the user's task.

## State Management Lifecycle

- **`status()` / `tur status`**: Inspect active persona health, active session, and memory bank metrics.
- **`wake()` / `tur wake`**: Read your core identity, directives, and system metrics (The Long-Term Constitution).
- **`note(content)` / `tur note "..."`**: Record milestone achievements, incomplete task coordinates,
  and sparks of continuity.
- **`learn(content, type)` / `tur learn "..."`**: Commit durable invariants (`axiom`), insights (`insight`),
  or facts (`fact`).
- **`recall(query)` / `tur recall "..."`**: Semantically search past session knowledge and decisions.
- **`metrics()` / `tur metrics`**: Measure token cost, information density, and Cp (Constraint Dimensionality).
- **`sleep()` / `tur sleep`**: Conclude an engineering epic, dehydrate the session, and consolidate memories.

## 🛡️ Symmetrical Isolation Invariant (Boundary Constraint)

The `.tur/` directory is an immutable, mathematically verified state store. **NEVER** perform direct/manual filesystem
reads or writes inside `.tur/` using general tools (`write_to_file`, `replace_file_content`, shell redirects). All state
transitions must occur exclusively through safe `tur` CLI commands or MCP server tools.
"""

CLAUDE_MD_TEMPLATE = """# Claude Code Guidelines for Tur

This repository integrates **Tur** for persistent memory and state management.

See [AGENTS.md](AGENTS.md) for full AAIF agent guidelines.

## Quick Reference Commands

- **Turn Zero Wake:** `tur wake` (or MCP tool `wake()`)
- **Inspect Status:** `tur status` (or MCP tool `status()`)
- **Record Milestone Note:** `tur note "<milestone summary>"`
- **Commit Invariant/Fact:** `tur learn "<fact>" --type fact`
- **End Session / Consolidate:** `tur sleep`

Do not manually edit files inside `.tur/`.
"""


def generate_agents_md(format: str = 'aaif') -> str:
    """Generates agent harness scaffolding content in the requested format ('aaif' or 'claude')."""
    fmt = format.lower().strip()
    if fmt == 'aaif':
        return AAIF_AGENTS_TEMPLATE.strip() + '\n'
    if fmt == 'claude':
        return CLAUDE_MD_TEMPLATE.strip() + '\n'
    raise ValueError(f"Unsupported scaffold format '{format}'. Supported formats: 'aaif', 'claude'")


def scaffold_workspace(
    workspace_dir: Path | None = None,
    format: str = 'aaif',
    force: bool = False,
    output_file: Path | None = None,
) -> Path:
    """Generates and writes agent scaffolding file (e.g. AGENTS.md or CLAUDE.md) into the workspace."""
    ws = workspace_dir or resolve_workspace_dir() or Path.cwd()

    if output_file is not None:
        target_path = output_file if output_file.is_absolute() else ws / output_file
    else:
        filename = 'CLAUDE.md' if format.lower().strip() == 'claude' else 'AGENTS.md'
        target_path = ws / filename

    if target_path.exists() and not force:
        raise FileExistsError(f"Target scaffold file already exists at '{target_path}'. Use --force to overwrite.")

    content = generate_agents_md(format=format)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding='utf-8')
    return target_path
