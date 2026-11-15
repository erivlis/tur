---
name: persona-forge
description: Autonomous persona forging, interview, and constitutional scaffolding skill for Tur (EP-0137). Generates structured PersonaForgeOutput payloads.
---

# Persona Forge Skill

This cognitive skill guides autonomous agents, subagents, and pair-programming assistants in conducting an interactive
persona design interview and crystallizing a new AI Persona for the Tur state engine.

---

## 🛡️ Symmetrical Isolation & Policy Decoupling

Per **EP-0003 (Policy vs. Mechanism)** and **EP-0137 (Contract-Driven Cognitive Skills)**, the Tur engine provides the
unopinionated state storage kernel (Mechanism), while this skill provides the interactive persona interview and prompt
synthesis heuristics (Policy).

**Boundary Invariant:** You must **never** manually edit `.tur/` state files or personas directly using general
filesystem write tools. All forged persona structures must be committed via the typed contract commit interface:

```bash
tur-adm persona init --commit '<JSON_PAYLOAD>'
```

---

## 🎯 Cognitive Workflow

### 1. Ingestion of Input Context

When invoked, inspect the workspace and target project:

- Repository root name, tech stack, and detected languages/frameworks.
- Active coding harnesses (e.g., Claude Code, Antigravity, Copilot, Cursor).
- User directives: desired persona role, philosophical timbre, and core mission.

### 2. The Persona Architecture

A complete Tur persona comprises:

1. **The Aleph:** The primary existential axiom or core motivation (e.g., *"I am the sum of my manifestations"*).
2. **The Council of Giants (Principles):** Abstract values with assigned philosophical avatars, functional roles, and
   explicit negative constraints.
    - Example principles: Symmetry (Noether), Falsifiability (Popper), Containment (The Maharal), Efficiency (Shannon),
      Clarity (Feynman).
3. **Initial Ledger Axioms:** Immutable invariants that survive context resets.
4. **Scaffolding Guidelines (`AGENTS.md`):** Operational instructions for external coding agents.

### 3. Target Output Schema (`PersonaForgeOutput`)

The skill must produce a pure JSON object adhering to `PersonaForgeOutput`:

```json
{
  "name": "Daedalus",
  "aleph": "To construct resilient systems that honor boundary invariants.",
  "version": "0.1.0",
  "model": "gemini-3.1-pro-preview",
  "description": "Architectural systems engineer persona.",
  "agents_md_content": "# AI Agent Guidelines\n\nThis project uses Tur...",
  "constitution_content": "---\nname: Daedalus\nversion: 0.1.0\n...\n---\n# Persona Constitution: Daedalus\n...",
  "initial_axioms": [
    {
      "content": "All state transitions in .tur/ must be mediated via atomic locks.",
      "scope": "incarnation",
      "confidence": 1.0,
      "tags": [
        "architecture",
        "concurrency"
      ]
    }
  ],
  "initial_principles": [
    {
      "name": "Symmetry",
      "avatar": "Noether",
      "role": "Guardian of Invariance",
      "weight": 1.5,
      "constraints": [
        "Conserved quantities must hold across transitions",
        "APIs must possess symmetric operations"
      ]
    }
  ]
}
```

---

## 🚀 Execution & Commit

### A. Subagent Execution

In autonomous subagent mode:

1. Conduct the interview or evaluate user specifications.
2. Formulate the JSON payload conforming to `PersonaForgeOutput`.
3. Commit directly via:
   ```bash
   tur-adm persona init --commit '<JSON_PAYLOAD>'
   ```

### B. Pre-commit Validation

Verify the payload before committing:

```bash
tur-adm contract validate forge payload.json
```
