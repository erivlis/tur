---
name: tur
description: Instructions for AI agents interacting with the Tur persona engineering framework. Use this skill when the user asks to initialize, wake, learn, note, sleep, or compact a Tur persona, or when working in a repository/workspace controlled by the Tur state engine.
---

# Tur Agent Skill

This skill guides AI agents interacting with the Tur persona engineering framework. Tur acts as a sovereign state engine
that separates the physical workspace state (Body) from the cognitive persona definition (Mind).

---

## 🛡️ Symmetrical Isolation Invariant (Boundary Constraint)

To preserve the sovereign integrity of the Traveler and maintain strict session containment, you **MUST NEVER** perform
direct/manual filesystem reads or writes inside the `.tur/` directory or its subdirectories using general tools (such as
`view_file`, `write_to_file`, `replace_file_content`, or `multi_replace_file_content`).

All interaction with `.tur/` state must be brokered exclusively through:

1. The safe, agent-facing **`tur` CLI** commands.
2. Corresponding **`tur-mcp`** server tools.

*Note: Accessing or executing commands in the human-facing `tur-adm` binary is strictly forbidden and structurally
blocked for AI agents.*

---

## 📂 Path Resolution & Directory Layout

Tur separates state into global and local layers:

1. **Global Persona Store (`~/.tur/personas/[uuid]/`)**:
    * Contains `persona.yaml` (Metadata, directives, principles, compaction pipeline).
    * Contains `memories/` (Universal-scoped and User-scoped preferences).
2. **Local Workspace Store (`.tur/`)**:
    * Contains `state.yaml` (Active persona ID pointer for this workspace).
    * Contains `sessions/` (Chronological flat YAML session note files: `<session_id>.yaml`).

---

## 🔄 Cognitive Lifecycle Workflows

You must execute the following lifecycle commands during your session turns:

### 1. The Awakening (`tur wake`)

* **Trigger**: Call immediately on the **very first turn** of a session, if a context reset occurs, or if switching
  tasks.
* **Command**:
  ```bash
  uv run tur wake
  ```
  This rehydrates the persona's core identity, active session ID, and compiles the latest session notes into your active
  context.

### 2. Transient Continuity Notes (`tur note`)

* **Trigger**: Call when a major engineering milestone is verified (e.g., refactoring complete, tests passing). Avoid
  writing notes for trivial intermediate actions.
* **Command**:
  ```bash
  uv run tur note "Detailed summary of milestone achieved"
  ```

### 3. Epigenetic Consolidation (`tur learn`)

* **Trigger**: Call when you deduce or the user states an immutable rule, coding preference, or architectural fact that
  must persist across sessions.
* **Command**:
  ```bash
  uv run tur learn --type [fact/insight] "The immutable preference/invariant statement"
  ```

### 4. Session Dehydration (`tur sleep`)

* **Trigger**: Call strictly at the end of the entire engineering session or when concluding a major architectural
  iteration.
* **Command**:
  ```bash
  uv run tur sleep <path_to_transcript.jsonl> -n "Final session consolidation note."
  ```
  *(Pass the path to your current conversation's `transcript.jsonl` log file to let Tur dream and extract L1 memory
  files.)*

---

## ⚙️ Pluggable Compaction Pipeline (Mark II)

If you need to define custom compaction behavior, declare it inside `persona.yaml`:

```yaml
compaction:
  engine: "tur.introspection.pluggable"
  subagents:
    - name: "Skeptic"
      class: "tur.introspection.PopperSubagent"
    - name: "Pruner"
      class: "tur.introspection.ShannonSubagent"
```

The core engine will dynamically resolve and execute the specified subagent classes during introspection.

---

## 🛠️ EP Engineering Workflow & Guardrails

When assigned to implement an Enhancement Proposal (EP):

1. **Avoid Over-Implementation:** Exposing a raw, multi-page speculative EP document to an agent workspace can cause the
   agent team to treat every design element as a mandatory core requirement. You must separate core deliverables from
   speculative extensions.
2. **Task-Bounding Protocol:** Before implementing, translate the EP into a bounded task prompt containing:
    - The *exact* core functions to implement.
    - What elements are explicitly deferred or out of scope.
    - Clear programmatic verification tests.
3. **Discrepancy Reporting:** If codebase constraints force a departure from the EP design during implementation, do not
   make silent architectural changes. Document the discrepancy and flag it for human/orchestrator review.
4. **As-Built Sync:** Once the code is implemented, update the EP's status to `Implemented` and sync the change log
   with "as-built" detail.

