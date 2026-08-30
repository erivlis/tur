---
title: "EP-0142: Progressive Execution Observability, Live Status Spinners, and Streaming MCP Telemetry"
description: "Establishes progressive execution observability across Tur CLI commands and MCP tools, introducing Rich live spinners, multi-stage pipeline trackers, and MCP streaming progress notifications (notifications/progress)."
icon: lucide/loader-2
status: draft
---

# EP-0142: Progressive Execution Observability, Live Status Spinners, and Streaming MCP Telemetry

| Field        | Value                                                                                  |
|:-------------|:---------------------------------------------------------------------------------------|
| **EP**       | 0142                                                                                   |
| **Title**    | Progressive Execution Observability, Live Status Spinners, and Streaming MCP Telemetry |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                                  |
| **Sponsor**  | Council of Giants                                                                      |
| **Delegate** | Shannon (Telemetry & Channel Observability), Bacon (Empirical Runtime Feedback)        |
| **Status**   | Draft                                                                                  |
| **Type**     | Standards Track                                                                        |
| **Created**  | 2026-08-30                                                                             |
| **Updated**  | 2026-08-30                                                                             |

---

## Abstract

This proposal establishes comprehensive **Progressive Execution Observability** across the Tur framework. Long-running
operations such as session dehydration (`tur sleep` / MCP `sleep()`), multi-stage cognitive introspection
(`tur introspect` / MCP `introspect()`), deep associative recall (`tur recall --deep`), and schema evolution
(`tur-adm persona migrate`) can block synchronously for $10\text{s} - 45\text{s}+$. Without live feedback, human
operators and AI host harnesses cannot distinguish active computation from process deadlocks.

This EP introduces a dual-layer observability protocol:

1. **CLI Layer:** Dynamic Rich `console.status()` spinners, step-by-step pipeline progress bars
   (`rich.progress.Progress`), and elapsed-time tracking.
2. **MCP Layer:** Streaming progress notifications (`notifications/progress`) and contextual log events
   (`notifications/message`) via FastMCP `Context`, rendering native real-time progress bars inside connected IDE
   harnesses (Cursor, Claude Desktop, Antigravity).

---

## Motivation

Several fundamental operations in Tur involve multi-step pipelines and external LLM inference passes:

1. **`tur sleep` / `tired` ($5\text{s} - 25\text{s}$):** Ingests long session transcripts, delegates dreaming extraction
   to LLM providers or MCP sampling, verifies Merkle hashes, and evaluates multi-agent swarm quiescence.
2. **`tur introspect` ($15\text{s} - 45\text{s}$):** Executes a 9-stage subagent pipeline (`IntegrityVerifier`,
   `OntologyExtractor`, `TruthMaintenanceEngine`, `SymmetryValidator`, `NoveltyExplorer`, `HebbianGraphDecayer`,
   `BoundaryEnforcer`, `ClarityDistiller`, `GraphPruner`).
3. **`tur-adm persona migrate` ($5\text{s} - 30\text{s}$):** Performs pre-flight integrity validation, directory
   snapshotting, atomic staging transformation, cutover, and post-flight verification.
4. **`tur recall --deep` ($1\text{s} - 5\text{s}$):** Executes HippoRAG Personalized PageRank over large graphs, loads
   OKF markdown files, and runs live Git commit verification (EP-0131) and TMS contradiction checks (EP-0134).

### The Failure Modes of Silent Execution

- **Premature Aborts:** Developers assume the CLI has hung or deadlocked on a `.tur/.locks` file descriptor, issuing
  `Ctrl+C` and risking partial state mutations.
- **Harness Request Timeouts:** MCP client harnesses lack visibility into long-running tool execution, surfacing generic
  timeout errors or unresponsive UI spinners.
- **Zero Sub-Stage Visibility:** When an introspection failure occurs in stage 7 (`BoundaryEnforcer`), operators receive
  no prior indication of which subagents completed successfully.

---

## Rationale

### Alignment with the Council Framework

- **Information & Channel Observability (Shannon):** Eliminates entropy regarding system state. High-frequency,
  low-overhead progress signals ensure the channel remains demonstrably alive.
- **Empirical Verification (Bacon):** Provides concrete empirical milestones during lengthy cognitive transformations
  rather than treating internal pipelines as black boxes.
- **Boundary Containment (Golem):** Cleanly isolates UI rendering (Rich spinners) from the deterministic execution
  engine (`src/tur/` kernel), respecting Policy vs. Mechanism decoupling.

---

## Specification

### 1. The Core Operations Taxonomy

Every long-running operation in Tur is categorized by its execution pattern:

```
OPERATION TYPE           CLI RENDERING MECHANISM             MCP PROTOCOL NOTIFICATION
──────────────           ───────────────────────             ─────────────────────────
Atomic Async Block       Rich `console.status` Spinner       `ctx.info()` + Single Progress Step
(e.g. `tur sleep`)       (Indeterminate dots/pulse)          (0/1 -> 1/1)

Multi-Stage Pipeline     Rich `Progress` Multi-Step Bar      `ctx.report_progress(i, total)`
(e.g. `tur introspect`)  (Determinate [i/N] with timer)      + `ctx.info("[i/N] Stage Name...")`

Interactive Migration    Rich `Progress` + Step Table        `ctx.report_progress(stage, 5)`
(e.g. `persona migrate`) (Structured Stage Summary)          + Stage Validation Logs
```

---

### 2. CLI Implementation Specification

#### A. Atomic Dehydration (`tur sleep`)

In [`src/tur/cli/agent.py`](file:///C:/dev/erivlis/tur/src/tur/cli/agent.py):

```python
@app.command()
def sleep(...):
    ...
    with console.status(
            f"[bold cyan]Extracting insights & consolidating memories via {model}... (Dreaming)[/bold cyan]",
            spinner="dots",
    ):
        count = dreaming.perform_sleep_dreaming(...)

    console.print(f"[bold green]✓ Dreams consolidated. {count} new memories formed.[/bold green]")
    console.print("[bold green]✓ State saved. Persona is now sleeping.[/bold green]")
```

#### B. Multi-Stage Pipeline (`tur introspect`)

In [`src/tur/cli/agent.py`](file:///C:/dev/erivlis/tur/src/tur/cli/agent.py) and [
`src/tur/introspection.py`](file:///C:/dev/erivlis/tur/src/tur/introspection.py):

The `IntrospectionAssembly` accepts an optional `ProgressCallback` protocol:

```python
type ProgressCallback = Callable[[int, int, str], None]


class IntrospectionAssembly:
    STAGES = [
        ("IntegrityVerifier", "Verifying cryptographic Merkle integrity..."),
        ("OntologyExtractor", "Extracting ontological concepts & relationships..."),
        ("TruthMaintenanceEngine", "Resolving JTMS contradictions & deactivations..."),
        ("SymmetryValidator", "Validating semantic conservation laws..."),
        ("NoveltyExplorer", "Exploring associative semantic expansions..."),
        ("HebbianGraphDecayer", "Applying temporal decay kinetics..."),
        ("BoundaryEnforcer", "Enforcing ontological boundary constraints..."),
        ("ClarityDistiller", "Distilling and refining graph nodes..."),
        ("GraphPruner", "Pruning subsumed & orphaned graph edges..."),
    ]

    def run(self, callback: ProgressCallback | None = None) -> IntrospectionResult:
        total = len(self.STAGES)
        for i, (stage_name, desc) in enumerate(self.STAGES, 1):
            if callback:
                callback(i, total, desc)
            self._execute_stage(stage_name)
```

In the CLI wrapper:

```python
with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
) as progress:
    task = progress.add_task("Introspecting L2 Cognitive Map...", total=9)


    def on_progress(current: int, total: int, description: str) -> None:
        progress.update(task, completed=current - 1, description=f"[cyan][{current}/{total}] {description}[/cyan]")


    result = assembly.run(callback=on_progress)
    progress.update(task, completed=9, description="[bold green]✓ Introspection complete.[/bold green]")
```

---

### 3. MCP Streaming Telemetry Specification

In [`src/tur/mcp_server.py`](file:///C:/dev/erivlis/tur/src/tur/mcp_server.py), FastMCP tools inject `Context` to emit
real-time MCP notifications:

```python
@mcp.tool()
async def sleep(note: str, ctx: Context) -> str:
    """Symmetrically end the active session with live streaming progress."""
    await ctx.info(f"Appending final session note: '{note[:40]}...'")
    await ctx.report_progress(progress=1, total=3)

    await ctx.info("Dehydrating session transcript & extracting insights (Dreaming)...")
    await ctx.report_progress(progress=2, total=3)

    count = perform_sleep_dreaming(...)
    await ctx.report_progress(progress=3, total=3)
    await ctx.info(f"Consolidated {count} memories. Persona is now sleeping.")

    return f"State saved. Persona is now sleeping. {count} new memories formed."
```

```python
@mcp.tool()
async def introspect(ctx: Context) -> str:
    """Execute 9-stage ontological introspection with progressive subagent updates."""
    total_stages = 9

    async def mcp_progress(current: int, total: int, description: str):
        await ctx.report_progress(progress=current, total=total)
        await ctx.info(f"[{current}/{total}] {description}")

    result = await run_async(assembly.run, callback=mcp_progress)
    return f"Introspection complete. {result.summary}"
```

---

### 4. Non-Interactive & Machine Modes

To preserve Unix pipe composability and JSON script automation:

- When `--json` or `--quiet` is specified, all interactive spinners and progress bars are bypassed.
- When `sys.stdout.isatty()` is `False`, Rich automatically degrades to plain log lines or silent execution.

---

## Backwards Compatibility

- **100% Non-Breaking:** All CLI commands retain identical exit codes, arguments, and final stdout formats.
- **MCP Agnosticism:** MCP clients that do not support `notifications/progress` simply ignore the progress payloads
  according to the MCP specification.

---

## How to Teach This / Documentation Plan

- Document CLI spinner options and `--quiet` flags in `docs/concepts/cli.md`.
- Document MCP streaming telemetry in `docs/architecture/mcp-server.md`.

---

## Reference Implementation

- CLI spinners: `src/tur/cli/agent.py`, `src/tur/cli/admin.py`
- Introspection progress hook: `src/tur/introspection.py`
- MCP Context progress: `src/tur/mcp_server.py`

---

## Rejected Ideas

- **Terminal Raw Curses / Fullscreen TUI during CLI commands:** Rejected because it clutters terminal history and breaks
  standard shell scrolling/copy-pasting.
- **Background Async MCP Job Queue for Sleep:** Rejected because session dehydration must complete transactionally
  before the client initiates a subsequent turn.

---

## Open Questions

- [ ] Should `tur recall --deep` display a mini-spinner if graph traversal exceeds 500ms?

---

## Change Log

* **2026-08-30:**
    * Initial Draft authored to eliminate silent synchronous execution bottlenecks across CLI and MCP interfaces.
