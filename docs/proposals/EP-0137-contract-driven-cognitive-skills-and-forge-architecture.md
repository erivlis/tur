---
title: "EP-0137: Contract-Driven Cognitive Skills and the Pluggable Forge Architecture"
description: "Establishes typed Pydantic I/O contracts for cognitive operations (persona forging, dreaming, verification), allowing pluggable skills to execute complex workflows without bloating the core kernel."
icon: lucide/blocks
status: draft
---

# EP-0137: Contract-Driven Cognitive Skills and the Pluggable Forge Architecture

| Field        | Value                                                                 |
|:-------------|:----------------------------------------------------------------------|
| **EP**       | 0137                                                                  |
| **Title**    | Contract-Driven Cognitive Skills and the Pluggable Forge Architecture |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                 |
| **Sponsor**  | Council of Giants                                                     |
| **Delegate** | Popper (Policy vs. Mechanism), Golem (Sovereign Isolation)            |
| **Status**   | Draft                                                                 |
| **Type**     | Standards Track                                                       |
| **Created**  | 2026-08-28                                                            |
| **Updated**  | 2026-08-28                                                            |

---

## Abstract

This proposal formalizes the **Contract-Driven Cognitive Skills Architecture**, decoupling complex AI reasoning
workflows (interactive persona forging, dreaming compaction, and codebase hypothesis validation) from the deterministic
Tur state kernel. Tur defines strict, typed Pydantic schemas under `src/tur/contracts/` that govern I/O boundaries.
Cognitive operations are fulfilled by pluggable, customizable agent skills (e.g. `.agents/skills/persona-forge/`),
subagents, or local CLI plugins. This enables zero-hardcoding of prompt strings in the core kernel, native support for
air-gapped and keyless environments via pure-function delegation, and total customizability for developer teams.

---

## Motivation

In early iterations of Tur, several advanced cognitive workflows were hardcoded directly into Python source files:

1. **Interactive Persona Forging:** Hardcoded TUI wizards and static templates in `src/tur/cli/wizards.py`.
2. **Dreaming & Epilogue Extraction:** Hardcoded Gemini API client calls and prompt strings in `src/tur/dreaming.py`.
3. **Ontological Extraction Pipelines:** Rigid subagent class definitions in `src/tur/introspection/`.

This created severe architectural limitations:

- **Violation of Policy vs. Mechanism (EP-0003):** The state kernel (Body) became tangled with specific prompt
  engineering heuristics (Mind).
- **Extensibility Friction:** Developers could not easily plug in custom persona interviewers, local Ollama-based memory
  compactors, or enterprise Jira-integrated profile generators without patching Tur's internal Python code.
- **Maintenance Burden:** Prompt refinements required code refactors, version releases, and test suite updates across
  the core engine.

---

## Rationale

### Alignment with the Council Framework

- **Policy vs. Mechanism (Popper):** Tur’s core engine serves strictly as a deterministic state store and verification
  kernel. All cognitive prompt formulations are encapsulated in user-customizable skill layers.
- **Empiricism & Verification (Bacon):** Strict JSON Schema validation guarantees that external skills cannot corrupt
  state files or bypass invariant checks.
- **Containment & Sovereignty (Golem):** Pluggable skills operate through typed contracts and CLI commits
  (`--commit '<JSON>'`), preserving strict boundary isolation.

---

## Specification

### 1. The Tri-Layer Cognitive Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      1. TUR CORE STATE KERNEL (Mechanism)                       │
│  - Storage Engine (OKF Markdown, Merkle DAG, SQLite Signals)                    │
│  - Multi-Process Synchronization & File Locking (EP-0129)                       │
│  - Schema Validation & Merkle Integrity Verifier                                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │  Typed Pydantic Schemas (src/tur/contracts/)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 2. PLUGGABLE COGNITIVE SKILLS & FORGES (Policy)                 │
├──────────────────────┬──────────────────────┬───────────────────────────────────┤
│    `persona-forge`   │ `dreaming-compactor` │       `graph-analyst`             │
│  Interactive persona │  L1 transcript to L2 │  Community clustering, betweenness│
│  interview & prompt  │  graph delta synthesis│  centrality, spectral health     │
└──────────────────────┴──────────────────────┴───────────────────────────────────┘
```

### 2. Standardized Core Contracts (`src/tur/contracts/`)

#### A. `PersonaForgeContract` (`src/tur/contracts/forge.py`)

Defines the schema for interactive persona creation:

```python
class PersonaForgeOutput(BaseModel):
    agents_md_content: str
    constitution_content: str
    initial_axioms: list[AxiomPayload]
    initial_principles: list[PrinciplePayload]
```

#### B. `DreamingCompactionContract` (`src/tur/contracts/dreaming.py`)

Defines the schema for compacting session logs into L2 graph deltas:

```python
class DreamingDeltaOutput(BaseModel):
    epilogue: str
    added_memories: list[MemoryRecord]
    superseded_memories: list[SupersessionLink]
    tms_refutations: list[RefutationLink]
    staged_core_memories: list[CoreMemoryStaging]
```

#### C. `VerificationContract` (`src/tur/contracts/verification.py`)

Defines the schema for validating memory claims against Git repository ground truth:

```python
class VerificationOutput(BaseModel):
    memory_id: str
    status: Literal["fresh", "stale", "refuted"]
    confidence_adjustment: float
    is_contradicted: bool
    evidence: str
```

### 3. Pluggable Skill Execution Modes

Tur supports three interchangeable execution modes for all cognitive contracts:

1. **Subagent Mode (Autonomous Swarm):** Invokes an isolated background subagent (e.g.
   `invoke_subagent(TypeName="persona-forge")`) that interviews the user, validates output against the Pydantic schema,
   and commits the result via `tur-adm init --commit '<JSON>'`.
2. **Pure-Function Delegation Protocol (Keyless / Offline):** Tur prints a standardized markdown block
   (`# TUR DELEGATION: {Task}`) containing the input payload and target JSON schema. The host LLM computes the deduction
   and pipes it back into `tur sleep --commit '<JSON>'`.
3. **Local CLI Plugin Mode:** Workspaces can configure custom scripts or executables in `.tur/config.yaml`:
   ```yaml
   skills:
     persona_forge: "python -m my_custom_forge"
     dreaming: "uv run tur-skill-dreaming --model ollama/llama3.3"
   ```

---

## Backwards Compatibility

- **Zero Breaking Changes:** Existing CLI commands (`tur sleep`, `tur introspect`, `tur-adm persona init`) retain their
  exact user-facing signatures while internally routing through the new contract layer.
- **Embedded Fallback:** If no custom skill or API key is detected, Tur gracefully defaults to the Pure-Function
  Delegation Protocol prompt.

---

## How to Teach This / Documentation Plan

- Author a dedicated guide in `docs/guides/authoring-custom-skills.md` explaining how to build, test, and register
  custom Tur cognitive skills.
- Publish reference skills under `.agents/skills/persona-forge/` and `.agents/skills/dreaming/`.

---

## Reference Implementation

- Schemas: `src/tur/contracts/`
- Delegation Engine: `src/tur/delegation.py`
- Research reference:
  `references/explorations/EXP-0004-persona-and-memory-crystallization/04_contract_driven_cognitive_skills_and_forge.md`

---

## Rejected Ideas

- **Hardcoding Vendor SDKs in Core:** Rejected to preserve strict LLM agnosticism (EP-0101). Tur must never require
  proprietary cloud SDKs in its core runtime dependencies.
- **Unstructured Free-Text Skill Outputs:** Rejected because non-deterministic output breaks Merkle hashing and
  automated belief revision. All skills must adhere to strict Pydantic schemas.

---

## Open Questions

- [ ] Should Tur provide a built-in schema validation CLI utility (`tur validate-contract <schema_name> <file.json>`)?
- [ ] How should skill execution timeouts be configured in multi-agent swarm environments?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the August 28, 2026 Architectural Crystallization.
