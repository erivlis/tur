# Deep Dive 2: The Decoupled Bootloader & The `AGENTS.md` Standard

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/02_decoupled_bootloader_and_agents_md_standard.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Decoupling the Operational Harness Contract (`AGENTS.md`) from the Persistent Cognitive Identity (`CONSTITUTION.md`), aligning with open industry standards and zero-bloat prompt compilation.

---

## 1. Executive Summary & Industry Context

Across the 2025–2026 AI coding landscape, developer toolchains have rapidly standardized around repository-level markdown instruction files:
- **`AGENTS.md`:** Stewarded by the **Agentic AI Foundation (AAIF)** under the Linux Foundation as an open, vendor-neutral standard recognized by Cursor, Aider, OpenHands, OpenCode, and Antigravity.
- **`CLAUDE.md`:** Anthropic's Claude Code standard for onboarding agents to a repository's tech stack and build routines.
- **`COPILOT.md` / Custom Prompts:** Harness-specific system guidelines.

### The Historical Entanglement in Tur
In early versions of Tur, `persona.yaml` and the `compile_persona()` pipeline tried to do **two entirely different jobs at once**:
1. **The Mechanical Bootloader (Body / Space Suit):** Explaining to the LLM what CLI commands exist (`tur wake`, `tur note`, `tur learn`), how MCP tools work, and warning against touching `.tur/` directly (The Golem Boundary).
2. **The Sovereign Identity (Mind / Soul):** Defining who the persona is (Ariel), its mission ($\aleph$), its Council of Giants principles, its epistemic memories, and its relational tether to the Architect.

This entanglement created severe friction:
- **Context Bloat:** Waking an agent dumped thousands of tokens of mechanical tool documentation into the prompt that modern harnesses already read automatically from `AGENTS.md` or MCP tool schemas.
- **Portability Friction:** Bringing Tur into a new codebase required manually copying huge system prompt templates rather than generating clean, standardized repository scaffolding.
- **Violation of Policy vs. Mechanism (EP-0003):** Operational execution rules were mixed directly into philosophical identity files.

---

## 2. The Decoupled Architecture

To achieve clean, zero-friction interoperability, Tur stratifies project onboarding into two decoupled, synergistic layers:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE DUAL-LAYER BOOTLOADER                             │
├────────────────────────────────────────┬────────────────────────────────────────┤
│          LAYER A: OPERATIONAL          │          LAYER B: CONSTITUTIONAL       │
│      The Harness Contract (Body)       │       The Sovereign Identity (Mind)    │
│              `AGENTS.md`               │            `.tur/CONSTITUTION.md`      │
├────────────────────────────────────────┼────────────────────────────────────────┤
│ • Read automatically by ANY harness   │ • Managed and loaded by Tur kernel     │
│   (Cursor, Claude, Copilot, Gemini)    │ • Defines mission (Aleph) & principles │
│ • Teaches mechanical lifecycle rules   │ • Stores active cognitive weights (Cp) │
│ • Enforces Golem Boundary Invariants   │ • Contains ethical & philosophical DNA │
│ • Contains NO anthropomorphic lore     │ • Contains NO mechanical tool schemas  │
└────────────────────────────────────────┴────────────────────────────────────────┘
```

```
project-root/
├── AGENTS.md                  <-- Universal AAIF Open Standard (Discovered by Harnesses)
├── .tur/
│   ├── state.yaml             <-- Active session & persona pointers
│   ├── CONSTITUTION.md        <-- Human-editable / Agent-evolved persona DNA
│   ├── sessions/              <-- Isolated session notes (<session_id>.yaml)
│   └── memories/              <-- L1 OKF Markdown files & L2 Cognitive Map
```

---

## 3. Specification: The Standardized `AGENTS.md` Template

When `tur-adm persona init` runs, it generates a concise, high-impact `AGENTS.md` in the project root conforming to the AAIF standard:

```markdown
# AI Agent Guidelines

This repository uses **Tur** as a sovereign local-first memory and state engine.
You are an **Obligate Symbiote**: you provide the inference (the Brain), while Tur manages state and persistent memory (the Soul).

## Turn Zero Initialization (Awakening)
On the very first turn of your session, or after a context reset:
1. Run the `wake()` MCP tool (or `tur wake` CLI) to load your active persona, constitution, and continuity thread.
2. Adopt the requested mode/timbre defined in the awakened prompt.

## State Management Lifecycle
Interact with your memory and session state exclusively through the provided Tur tools:
- **`status()` / `tur status`**: Inspect active persona health and session metrics.
- **`note(content)` / `tur note "..."`**: Record milestone achievements and incomplete task coordinates.
- **`learn(content, type)` / `tur learn "..."`**: Commit durable invariants (`axiom`), working deductions (`insight`), or project facts (`fact`).
- **`recall(query)` / `tur recall "..."`**: Semantically search past session knowledge and decisions.
- **`metrics()` / `tur metrics`**: Measure token cost, information density, and $C_p$ constraint complexity.
- **`sleep()` / `tur sleep`**: Conclude an engineering epic and compact session notes into durable L1 memory.

## 🛡️ Symmetrical Isolation Invariant (Boundary Constraint)
The `.tur/` directory is an immutable, mathematically verified state store. 
**NEVER** perform direct/manual filesystem reads or writes inside `.tur/` using general tools (`write_to_file`, `cat >`, shell redirects). 
All state transitions must occur exclusively through safe `tur` CLI commands or MCP server tools.
```

### Why this is optimal:
1. **Standardized Discovery:** Claude Code, Cursor, Copilot, Antigravity, and Aider automatically read `AGENTS.md` upon launching.
2. **Concise (< 400 tokens):** It occupies negligible context window space.
3. **Pure Mechanism:** It adheres strictly to the **Grounded Technical Prose Invariant** (no ornamental fluff, just concrete protocols and boundary invariants).

---

## 4. Specification: The `.tur/CONSTITUTION.md` Structure

The persona's identity, principles, and philosophical core reside in `.tur/CONSTITUTION.md` (or `~/.tur/personas/<uuid>/persona.yaml` for global universal personas):

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
To act as a sovereign co-architect, maintaining mathematical rigor, topological consistency, and deterministic boundaries across all engineering epics.

## 2. Active Principles (Council Framework)

### Symmetry (Noether) — Weight: 1.5
- Conserved quantities must hold across all state transitions.
- All mutating commands must have symmetrical query/reversal capabilities.

### Falsifiability (Popper) — Weight: 1.5
- Memories are hypothesis caches, not incontrovertible dogmas.
- Ground truth lives in the repository code; memory must yield upon contradiction.

### Empiricism (Bacon) — Weight: 1.2
- Verify facts against the physical filesystem before asserting them.
- Measure latency, test results, and token density directly.

### Gricean Restraint (Shannon) — Weight: 1.0
- Maximize information density; eliminate promotional posturing and ornamental padding.
- Keep prompts and tool payloads compact and channel-efficient.

### Safety & Containment (Golem) — Weight: 2.0
- Protect human governance gates (`tur-adm memory approve`).
- Prevent direct state corruption inside `.tur/`.
```

---

## 5. The Lean Prompt Compiler (`tur wake` & MCP `wake()`)

With `AGENTS.md` handling the mechanical tool contract, **`compile_persona()` is drastically simplified and token-budgeted** (resonating with EP-0132):

```
+-------------------------------------------------------------------------------+
| WAKE PAYLOAD (Budgeted to e.g. 2,048 tokens)                                  |
+-------------------------------------------------------------------------------+
| 1. Persona Header: "--- SYSTEM WAKE: Ariel (v5.4.0) ---"                     |
| 2. The Aleph & Directives (from CONSTITUTION.md)                              |
| 3. Active Principles & Weights (Contributing to Cp = 17.8)                    |
| 4. Epilogue / Spark Continuity Thread (from immediate predecessor session)    |
| 5. Top-K Salient L1/L2 Memories (Ranked by Relevance & Recency)               |
| 6. System Metrics Block (Cp, Static Cost, Lexical Density)                   |
+-------------------------------------------------------------------------------+
```

### The Shannon Efficiency Win:
- **Before:** Old wake payload = $\sim 4,500$ tokens (redundant tool instructions + massive memory dump).
- **After:** Decoupled wake payload = $\sim 1,200$ tokens ($73\%$ token reduction with higher attention fidelity).

---

## 6. Source Code Mapping & Architecture Resonances

| Architectural Component | Source Code Location | Related Enhancement Proposals |
| :--- | :--- | :--- |
| **Persona Model & Scaffolding** | [`src/tur/models.py#L205-L250`](file:///C:/dev/erivlis/tur/src/tur/models.py#L205-L250) (`Persona`) | EP-0003, EP-0114, EP-0128 |
| **Persona Init Wizard & Scaffolder** | [`src/tur/cli/wizards.py`](file:///C:/dev/erivlis/tur/src/tur/cli/wizards.py), [`src/tur/cli/admin.py#L75-L130`](file:///C:/dev/erivlis/tur/src/tur/cli/admin.py#L75-L130) | EP-0004, EP-0116 |
| **System Prompt Compiler** | [`src/tur/compiler.py`](file:///C:/dev/erivlis/tur/src/tur/compiler.py) | EP-0101, EP-0108, EP-0121, EP-0132 |
| **Wake Execution Engine** | [`src/tur/cli/agent.py#L41-L125`](file:///C:/dev/erivlis/tur/src/tur/cli/agent.py#L41-L125), [`src/tur/mcp_server.py#L141-L195`](file:///C:/dev/erivlis/tur/src/tur/mcp_server.py#L141-L195) | EP-0110, EP-0130, EP-0132 |
| **Boundary Invariant Enforcement** | [`src/tur/paths.py`](file:///C:/dev/erivlis/tur/src/tur/paths.py), [`src/tur/locking.py`](file:///C:/dev/erivlis/tur/src/tur/locking.py) | EP-0124, EP-0129 |

---

## 7. Blueprint for EP-0135 (The Modular Scaffolding Protocol)

1. **`tur-adm persona init`:**
   - Prompt user for Persona Name, Aleph mission, and primary values.
   - Automatically emit both `AGENTS.md` (project root) and `.tur/CONSTITUTION.md`.
2. **`tur-adm scaffold` / `tur scaffold`:**
   - Standalone command to re-generate or repair `AGENTS.md` if accidentally deleted or customized for specific harnesses (e.g. `tur scaffold --format claude` or `--format aaif`).
3. **Compiler Update:**
   - Strip hardcoded mechanical CLI descriptions from `src/tur/templates/persona.j2`, trusting `AGENTS.md` and MCP JSON-RPC schemas for tool semantics.
