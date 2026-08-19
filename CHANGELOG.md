## v0.9.2 (2026-08-19)

### Fix

- **security**: Enables Jinja2 autoescape for HTML/XML output.
- **security**: Adds safe_extract for robust archive extraction.

### Refactor

- Adopts StrEnum and datetime.UTC for modern Python features.
- Centralizes Gemini API calls and enhances dependency error messages.

## v0.9.1 (2026-08-19)

### Fix

- Ensures state directories for robust MCP server test isolation.

### Refactor

- Adopts Pydantic v2 `ConfigDict` for model configuration.
- Implements EP-0003, refactoring introspection for policy/mechanism.
- **EP-0121**: require_inference now encapsulates local LLM generation.
- **EP-0121**: Refactors LLM inference to use EP-0121 harness delegation.

## v0.9.0 (2026-08-19)

### Feat

- **EP-0115**: Enhances persona export/import with new options, security, and memory filtering.

### Refactor

- Implements EP-0003, refactoring introspection for policy/mechanism.
- **EP-0121**: require_inference now encapsulates local LLM generation.
- **EP-0121**: Refactors LLM inference to use EP-0121 harness delegation.
- Refactors imports, guards memory loads, and fixes session state.

## v0.8.0 (2026-07-18)

### Feat

- **EP-0115**: Enhances persona export/import with new options, security, and memory filtering.
- **EP-0103**: Adds MCP introspect tool, introspection delegation, and relationship constraints.

### Refactor

- Refactors imports, guards memory loads, and fixes session state.

## v0.7.0 (2026-07-12)

### Feat

- **EP-0113**: Implements Core Memory Protocol (EP-0113) for persona axioms and CLI.

### Refactor

- **EP-0113**: Removes `devolve` command and tool, favoring forward-only evolution.

## v0.6.0 (2026-07-11)

### Feat

- Adds Tur agent skill that guides Tur persona framework interactions.
- Updates L1 memory and L2 concept storage to OKF Markdown.

### Refactor

- Centralizes YAML loading with a new `yaml_safe_load` helper.

## v0.5.0 (2026-07-11)

### Feat

- Adds pluggable compaction pipeline for introspection.
- implement EP-0103 deductive memory and EP-0119 subagent council meditation
- Adds `verify` command to check memory integrity.

### Refactor

- Updates Popper conflict, persona headless, and user memory scope.
- Uses CSafeLoader for YAML and renames meditation to introspection.

## v0.4.1 (2026-06-07)

### Refactor

- Simplify MCP server startup by removing transport options

## v0.4.0 (2026-06-02)

### Feat

- Implements EP-0118 with SQLite for multi-agent signaling and consensus sleep.

## v0.3.1 (2026-06-01)

### Refactor

- Enhances CLI dependency checks with rich error messages and graceful exits.

## v0.3.0 (2026-06-01)

### Feat

- Configures dedicated CLI entry points and optional dependencies.
- Splits CLI into agent, admin, and mcp commands.

### Refactor

- Renames `tur-admin` CLI to `tur-adm` and refactors CLI modules.

## v0.2.1 (2026-05-31)

### Refactor

- telemetry methods to static and broadens return type hints.

## v0.2.0 (2026-05-30)

### Feat

- Implements EP-0114 + EP-0115.
- Adds Tur Pi extension for simpler, external Tur integration.
- Formalizes Tur's core concepts; implements Golem Protocol and Spark.

### Refactor

- refines memory scope path resolution, CLI error handling, and adds tests.
- update enum member comments into docstrings.
- refine CLI commands, adds telemetry, and streamlines session management logic.
- Extracts CLI commands and introduces session management.
- Refactors dream consolidation return with explicit else block.
- add `recall` command, enables agent `sleep`, and renames core commands.
- Renames interaction modes to speech modulations; updates template.
- Enhance memory management and update API for learning and recalling memories

## v0.1.0 (2026-03-30)
