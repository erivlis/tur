# Deep Dive 4: Contract-Driven Cognitive Skills & The Pluggable Forge

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/04_contract_driven_cognitive_skills_and_forge.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Specification of the Contract-Driven Cognitive Architecture, formalizing the Pure-Function Delegation Protocol into pluggable, schema-verified skills for persona forging, dreaming, and verification.

---

## 1. Executive Summary: The Ultimate Policy vs. Mechanism Decoupling

Under **EP-0003 (Policy vs. Mechanism)**, Tur established a core invariant:
> *"The deterministic execution engine (Body) must be separated from the cognitive identity and policy layer (Mind)."*

However, in practice, early versions of Tur still hardcoded several complex cognitive workflows directly into Python modules:
1. **Interactive Persona Forging:** Hardcoded Textual TUI wizards and static Jinja2 template prompts in `src/tur/cli/wizards.py`.
2. **Dreaming & Insight Extraction:** Hardcoded Gemini API prompt templates inside `src/tur/dreaming.py`.
3. **Ontological Extraction:** Rigid subagent class pipelines in `src/tur/introspection/`.

This created a major extensibility bottleneck:
- If a developer wanted to forge a persona via an interactive multi-turn interview, or extract memories using a local Ollama model or specialized DSPy pipeline, they had to modify Tur's internal Python source code.
- Running Tur in enterprise air-gapped or keyless environments required complicated monkeypatching rather than clean interface delegation.

### The Solution: Contract-Driven Cognitive Skills
Tur becomes a **sovereign, unopinionated state engine kernel**. It defines **strict, typed JSON Schema contracts** for cognitive operations, delegating their execution to **modular agent skills** (such as `.agents/skills/persona-forge/` or `playground/agent-skills/skills/subagent-prompt-generator/`).

---

## 2. The Tri-Layer Cognitive Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           1. THE HUMAN / HARNESS                                │
│                   (Developer, Claude, Copilot, Antigravity)                     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │  CLI / MCP Tool Invocation
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      2. TUR CORE STATE KERNEL (Mechanism)                       │
│  - Storage Engine (OKF Markdown, Merkle DAG, SQLite Signals)                    │
│  - Multi-Process Synchronization & File Locking (EP-0129)                       │
│  - Workspace Terrain Isolation & Canonical Paths (EP-0124, EP-0128)             │
│  - Schema Validation & Merkle Integrity Verifier                                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │  Pure-Function Delegation Protocol
                                         ▼  (Typed JSON Schemas / Markdown I/O)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 3. PLUGGABLE COGNITIVE SKILLS & FORGES (Policy)                 │
├──────────────────────┬──────────────────────┬───────────────────────────────────┤
│    `persona-forge`   │ `dreaming-compactor` │       `graph-analyst`             │
│  Interactive persona │  L1 transcript to L2 │  Community clustering, betweenness│
│  interview & prompt  │  graph delta synthesis│  centrality, spectral health     │
└──────────────────────┴──────────────────────┴───────────────────────────────────┘
```

---

## 3. Formal Specification of Core Skill Contracts

### 3.1. Contract 1: `PersonaForgeContract` (Genesis & Scaffolding)

Invoked during `tur-adm persona init` or `tur scaffold`:

#### Input Payload (Context from Environment & Developer):
```json
{
  "project_name": "tur",
  "project_root": "C:/dev/erivlis/tur",
  "detected_tech_stack": ["Python 3.14", "Typer", "FastMCP", "NetworkX", "Pytest"],
  "target_harnesses": ["claude-code", "github-copilot", "antigravity", "cursor"],
  "user_directives": {
    "role": "Architect",
    "desired_timbre": "Contemplative",
    "core_mission": "Build a sovereign, local-first memory engine for AI agents."
  }
}
```

#### Target Output Schema (`PersonaForgeOutput`):
```json
{
  "agents_md_content": "# AI Agent Guidelines\n\nThis project uses Tur...",
  "constitution_content": "---\nname: Ariel\nversion: 5.4.0\n...\n---\n# Persona Constitution: Ariel\n...",
  "initial_axioms": [
    {
      "content": "All state transitions in .tur/ must be mediated via atomic locks.",
      "scope": "incarnation",
      "confidence": 1.0
    },
    {
      "content": "Core Python mechanisms must never hardcode anthropomorphic persona names.",
      "scope": "universal",
      "confidence": 1.0
    }
  ],
  "initial_principles": [
    {
      "name": "Symmetry",
      "avatar": "Noether",
      "role": "Guardian of Invariance",
      "weight": 1.5,
      "constraints": ["Conserved quantities must hold across transitions"]
    }
  ]
}
```

---

### 3.2. Contract 2: `IntrospectionDreamingContract` (Session Compaction)

Invoked during `tur sleep` or `tur introspect`:

#### Input Payload:
```json
{
  "session_id": "20260825_190758_86152dcb",
  "session_notes": [
    {"timestamp": "2026-08-27T15:00:00Z", "content": "Decomposed monolith main.py into domain modules."},
    {"timestamp": "2026-08-27T15:30:00Z", "content": "Authored draft EPs EP-0131 to EP-0134."}
  ],
  "active_l2_graph": {
    "nodes": [
      {"id": "concept-104e77a1", "content": "main.py is the monolithic router.", "type": "Fact"}
    ],
    "edges": []
  }
}
```

#### Target Output Schema (`DreamingDeltaOutput`):
```json
{
  "epilogue": "Decomposed monolithic main.py into isolated domain modules. Authored EPs for memory provenance.",
  "added_memories": [
    {
      "id": "concept-ccf1b8ee",
      "type": "fact",
      "scope": "incarnation",
      "content": "Decomposed monolith main.py into isolated domain modules under src/tur/.",
      "confidence": 1.0
    }
  ],
  "superseded_memories": [
    {
      "superseded_id": "concept-104e77a1",
      "superseding_id": "concept-ccf1b8ee",
      "reason": "Refactored monolithic architecture."
    }
  ],
  "tms_refutations": [],
  "staged_core_memories": []
}
```

---

### 3.3. Contract 3: `CodebaseVerificationContract` (Hypothesis Validation)

Invoked during `tur verify` or pre-turn recall to validate working hypotheses against repo ground truth:

#### Input Payload:
```json
{
  "memory_id": "concept-8f2a1b9c",
  "content": "SQLite signal queue uses WAL mode and busy_timeout=5000ms.",
  "provenance": {
    "observed_at": "2026-08-27T15:00:00Z",
    "git_sha": "9f83ab2c104e",
    "context_ref": "src/tur/signals.py#L45-L60"
  }
}
```

#### Target Output Schema (`VerificationOutput`):
```json
{
  "memory_id": "concept-8f2a1b9c",
  "status": "fresh",
  "confidence_adjustment": 0.0,
  "is_contradicted": false,
  "current_file_state": "WAL mode present in src/tur/session.py line 42."
}
```

---

## 4. Execution Channels for Skills

How does Tur execute these contracts across diverse developer setups?

1. **Native Subagent Execution (Autonomous Swarm Mode):**
   - Tur invokes a specialized subagent (e.g. `invoke_subagent(TypeName="persona-forge", Prompt=...)`).
   - The subagent interacts with the user, collects answers, validates against the Pydantic schema, and commits the result via `tur-adm init --commit '<JSON>'`.
2. **Pure-Function Delegation Protocol (Air-Gapped / Keyless Mode):**
   - Tur prints the standardized delegation prompt (`# TUR DELEGATION: {Title}`).
   - The external host model computes the JSON output and pipes it into `tur sleep --commit '<PAYLOAD>'`.
3. **Local CLI / Script Mode:**
   - Developers can supply a custom Python script or executable via `.tur/config.yaml`:
     ```yaml
     skills:
       persona_forge: "python -m my_enterprise_forge"
       dreaming: "uv run tur-skill-dreaming --model ollama/llama3.3"
     ```

---

## 5. Blueprint for EP-0137 (Contract-Driven Cognitive Skills)

1. **Standardized Pydantic Schemas (`src/tur/contracts/`):**
   - Create `src/tur/contracts/forge.py`, `src/tur/contracts/dreaming.py`, `src/tur/contracts/verification.py`.
2. **Zero-Hardcoding in Core Engine:**
   - Remove hardcoded Jinja2 prompt strings from `src/tur/dreaming.py`, delegating all prompt formulation to structured skill contracts.
3. **Pluggable Skill Discovery (`.tur/skills/` & `.agents/skills/`):**
   - Allow local repository skills to override default compaction and interview pipelines.
