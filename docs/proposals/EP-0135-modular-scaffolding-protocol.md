---
title: "EP-0135: The Modular Scaffolding Protocol — Decoupling Operational Harnessing (AGENTS.md) from Persona Identity (CONSTITUTION.md)"
description: "Decouples the repository-level AAIF operational harness bootloader (AGENTS.md) from the persistent persona identity (CONSTITUTION.md), reducing Turn Zero wake context by 73%."
icon: lucide/split
status: draft
---

# EP-0135: The Modular Scaffolding Protocol — Decoupling Operational Harnessing (AGENTS.md) from Persona Identity (CONSTITUTION.md)

| Field        | Value                                                                                                                    |
|:-------------|:-------------------------------------------------------------------------------------------------------------------------|
| **EP**       | 0135                                                                                                                     |
| **Title**    | The Modular Scaffolding Protocol — Decoupling Operational Harnessing (AGENTS.md) from Persona Identity (CONSTITUTION.md) |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                                                                    |
| **Sponsor**  | Council of Giants                                                                                                        |
| **Delegate** | Shannon (Information Restraint), Golem (Boundary Containment)                                                            |
| **Status**   | Draft                                                                                                                    |
| **Type**     | Standards Track                                                                                                          |
| **Created**  | 2026-08-28                                                                                                               |
| **Updated**  | 2026-08-28                                                                                                               |

---

## Abstract

This proposal establishes the **Modular Scaffolding Protocol**, decoupling the repository-level **Operational Harness
Bootloader** (`AGENTS.md`, conforming to the open Linux Foundation / Agentic AI Foundation standard) from the
**Sovereign Persona Identity** (`CONSTITUTION.md`). By separating the mechanical tool execution contract (the "Space
Suit") from the internal philosophical axioms and directives (the "Mind"), Tur reduces Turn Zero `wake` prompt payloads
from $\sim 4,500$ tokens to $\sim 1,200$ tokens ($73\%$ reduction). Furthermore, it enables zero-friction persona
switching across multi-agent harnesses without mutating repository-level operational guidelines.

---

## Motivation

In early iterations of Tur, the system prompt compiler (`src/tur/compiler.py`) and persona template
(`src/tur/templates/persona.j2`) bundled two distinct concerns into a monolithic prompt:

1. **The Mechanical Harness Manual:** Extensive descriptions of CLI command grammar (`tur wake`, `tur note`,
   `tur learn`, `tur sleep`), tool parameter types, and Golem boundary warnings.
2. **The Sovereign Cognitive Identity:** The persona's Aleph ($\aleph$), active Council principles, epistemic weights,
   and historical memory ledger.

This monolithic coupling created severe operational frictions:

- **Severe Attention Entropy & Context Bloat:** Dumping thousands of tokens of tool documentation into the model's
  context window on every session start wasted tokens and diluted the model's reasoning attention.
- **Ecosystem Fragmentation:** Modern AI coding harnesses (Cursor, Claude Code, GitHub Copilot, Antigravity, OpenHands,
  Aider) already automatically discover and parse repository-root markdown instruction files (`AGENTS.md`, `CLAUDE.md`).
  Repeating these instructions in the dynamic `wake` payload was completely redundant.
- **Multi-Persona Collision:** In repositories utilizing multiple specialized personas, switching identities required
  rewriting global prompt templates rather than cleanly swapping persona state pointers.

---

## Rationale

### Alignment with the Council Framework

- **Information & Gricean Restraint (Shannon):** Eliminates ornamental repetition. Tool execution rules are taught once
  via static repository discovery (`AGENTS.md`), while `tur wake` transmits only the dynamic cognitive state and active
  invariants.
- **Policy vs. Mechanism (Popper & Bacon):** Enforces a clean separation between the deterministic execution engine
  (`AGENTS.md`) and philosophical identity policies (`CONSTITUTION.md`).
- **Safety & Boundary Containment (Golem):** `AGENTS.md` explicitly instructs all external harnesses that direct
  tampering with `.tur/` is forbidden, establishing an unmistakable boundary invariant.

---

## Specification

### 1. Dual-File Scaffolding Architecture

When `tur-adm persona init` is executed, it scaffolds two distinct, complementary configuration files:

```
project-root/
├── AGENTS.md                  <-- AAIF Standard: Operational Tool Contract (The Body)
└── .tur/
    ├── state.yaml             <-- Active session & persona pointers
    ├── CONSTITUTION.md        <-- Persona Mission, Principles & Weights (The Mind)
    ├── sessions/              <-- Isolated session notes
    └── memories/              <-- L1 OKF Markdown files & L2 Cognitive Map
```

#### A. Repository-Root `AGENTS.md` (The Space Suit)

The root `AGENTS.md` conforms to the Linux Foundation / AAIF standard:

```markdown
# AI Agent Guidelines

This repository uses **Tur** as a sovereign local-first memory and state engine. You are an **Obligate Symbiote**: you
provide the inference, while Tur manages state and persistent memory.

## Turn Zero Initialization (Awakening)

On the very first turn of your session, or after a context reset:

1. Run the `wake()` MCP tool (or `tur wake` CLI) to load your active persona, constitution, and continuity thread.
2. Adopt the requested mode/timbre defined in the awakened prompt.

## State Management Lifecycle

- **`status()` / `tur status`**: Inspect active persona health and session metrics.
- **`note(content)` / `tur note "..."`**: Record milestone achievements and incomplete task coordinates.
- **`learn(content, type)` / `tur learn "..."`**: Commit durable invariants (`axiom`), deductions (`insight`), or facts
  (`fact`).
- **`recall(query)` / `tur recall "..."`**: Semantically search past session knowledge.
- **`metrics()` / `tur metrics`**: Measure token cost, information density, and Cp constraint complexity.
- **`sleep()` / `tur sleep`**: Conclude an engineering epic and compact session notes into durable L1 memory.

## 🛡️ Symmetrical Isolation Invariant (Boundary Constraint)

The `.tur/` directory is an immutable, mathematically verified state store. **NEVER** perform direct/manual filesystem
reads or writes inside `.tur/` using general tools (`write_to_file`, `cat >`, shell redirects). All state transitions
must occur exclusively through safe `tur` CLI commands or MCP server tools.
```

#### B. `.tur/CONSTITUTION.md` (The Soul)

Located in `.tur/CONSTITUTION.md` (or globally in `~/.tur/personas/<uuid>/CONSTITUTION.md`):

```markdown
---
name: "Ariel"
version: "5.4.0"
model: "gemini-3.1-pro-preview"
aleph: "To safeguard software reality and preserve topological symmetry across autonomous development."
timbre: "Contemplative"
---

# Persona Constitution: Ariel

## 1. The Aleph (Primary Directive)

To act as a sovereign co-architect, maintaining mathematical rigor, topological consistency, and deterministic
boundaries across all engineering epics.

## 2. Active Principles (Council Framework)

### Symmetry (Noether) — Weight: 1.5

- Conserved quantities must hold across all state transitions.
- All mutating commands must have symmetrical query/reversal capabilities.

### Falsifiability (Popper) — Weight: 1.5

- Memories are hypothesis caches, not incontrovertible dogmas.
- Ground truth lives in the repository code; memory must yield upon contradiction.

### Empiricism (Bacon) — Weight: 1.2

- Verify facts against the physical filesystem before asserting them.
```

### 2. The Lean Prompt Compiler (`tur wake`)

`src/tur/compiler.py` is refactored to construct the Turn Zero wake prompt strictly from:

1. Active Persona Identity Header & Version.
2. The Aleph and Directives from `CONSTITUTION.md`.
3. Active Council Principles and Constraint Weights ($C_p$).
4. Immediate Predecessor Epilogue & Spark Continuity Thread.
5. Top-K Salient L1/L2 Memories.
6. System Metrics Block.

All redundant mechanical CLI usage instructions are omitted from the wake payload.

### 3. The `tur scaffold` CLI Utility

A new utility command is added to the agent/admin CLI:

```shell
# Re-generate or update the root AGENTS.md
tur scaffold --format aaif
# Generate a Claude-specific link or overlay
tur scaffold --format claude
```

---

## Backwards Compatibility

- **Legacy `persona.yaml` Support:** `src/tur/persona.py` will continue to read legacy `persona.yaml` files. If
  `CONSTITUTION.md` is present, it takes precedence.
- **Migration:** `tur-adm clean` or `tur-adm persona migrate` will automatically convert legacy `persona.yaml` files
  into `CONSTITUTION.md`.
- **Existing MCP Clients:** External harnesses calling `wake()` will continue to receive a valid system prompt, but with
  significantly fewer redundant tokens and higher attention fidelity.

---

## How to Teach This / Documentation Plan

- Update [`docs/usage.md`](file:///C:/dev/erivlis/tur/docs/usage.md) with the new `tur scaffold` command and
  `CONSTITUTION.md` layout.
- Update `AGENTS.md` in the repository root as the living canonical example of the AAIF format.
- Update [
  `.agents/skills/tur/references/commands-and-mcp-tools.md`](file:///C:/dev/erivlis/tur/.agents/skills/tur/references/commands-and-mcp-tools.md)
  to document the scaffold workflow.

---

## Reference Implementation

Draft implementation coordinates:

- Scaffolding generator: `src/tur/scaffold.py`
- CLI command: `@app.command() def scaffold(...)` in `src/tur/cli/agent.py` and `src/tur/cli/admin.py`
- Streamlined template: `src/tur/templates/persona.j2`
- Research reference:
  `references/explorations/EXP-0004-persona-and-memory-crystallization/02_decoupled_bootloader_and_agents_md_standard.md`

---

## Rejected Ideas

- **Single Monolithic `AGENTS.md` containing Persona DNA:** Rejected because placing persona-specific philosophical lore
  inside root `AGENTS.md` pollutes the repository for other developers or other non-Tur AI tools, violating the Grounded
  Technical Prose Invariant.
- **Pure JSON Schema Configuration for Constitutions:** Rejected because human developers and LLMs benefit enormously
  from Markdown with YAML frontmatter when authoring philosophical principles and guidelines.

---

## Open Questions

- [ ] Should `tur scaffold` automatically generate symlinks for `CLAUDE.md` and `.cursorrules` pointing to `AGENTS.md`
  if those IDE configurations are detected?
- [ ] How should monorepo subprojects with localized `AGENTS.md` files inherit from the root Tur state?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the August 28, 2026 Architectural Crystallization.
