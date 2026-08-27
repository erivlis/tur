---
title: "EP-0134: Active TMS Contradiction Interruption Protocol"
description: "Defines real-time inference and ingestion conflict checks that proactively surface contradictory assertions against the L2 Truth Maintenance System."
icon: lucide/shield-alert
status: draft
---

# EP-0134: Active TMS Contradiction Interruption Protocol

| Field       | Value                                                         |
|:------------|:--------------------------------------------------------------|
| **EP**      | 0134                                                          |
| **Title**   | Active TMS Contradiction Interruption Protocol                |
| **Author**  | Eran Rivlis & Ariel                                           |
| **Status**  | Draft                                                         |
| **Type**    | Standards Track                                               |
| **Created** | 2026-08-27                                                    |
| **Updated** | 2026-08-27                                                    |

## Abstract

This proposal introduces an **active, real-time contradiction interruption protocol** into Tur's ingestion and retrieval pipelines. While Tur's Layer 2 (L2) Truth Maintenance System (TMS) resolves contradictions post-hoc during batch dreaming and compaction cycles (`tur introspect`), conflicting statements currently pass through `tur learn` and `tur note` silently at ingestion time.

EP-0134 introduces:
1. **Real-Time TMS Ingestion Intercepts:** Proactively querying the L2 semantic graph during `tur learn` to detect opposing polarity, superseded concepts, or incompatible axioms.
2. **Interactive Conflict Resolution Protocol:** Prompting the agent/human with structured options when a collision is detected: `[supersede]`, `[refute]`, `[branch]`, or `[abort]`.
3. **Inference-Time Guardrails:** An MCP warning channel that flags when a model's proposed action or memory creation directly clashes with an active constitutional axiom or core memory.

## Motivation

In standard AI workflows, memory corruption happens incrementally:
1. An agent writes: `concept-1: "Database migrations run via Alembic."`
2. Two weeks later, another harness or developer switches the project to Prisma and the agent writes: `concept-2: "Database migrations run via Prisma Migrate."`
3. Under silent append-only ingestion, both memories exist concurrently in L1. When an agent wakes up, both concepts are injected, creating high perplexity and hallucinated hybrid instructions (e.g. attempting to run `alembic revision` on a Prisma schema).
4. Post-hoc batch compaction (`tur introspect`) eventually detects this, but only after potentially hours or days of contaminated developer turns.

If the engine intercepts the assertion at the exact moment `concept-2` is submitted, it can immediately query the agent/human:
> ⚠️ **TMS Contradiction Detected:** New assertion conflicts with existing memory `concept-1` ("Database migrations run via Alembic").
> Action required: `[s] Supersede older memory`, `[r] Refute newer memory`, `[m] Merge contexts`, `[f] Force dual existence`.

## Rationale

- **Popperian Falsifiability (Popper):** Confronting conflicting hypotheses at the moment of encounter prevents uncritical accumulation of dogma.
- **Golem Governance (Golem):** Safeguard constitutional principles and human-approved `core` memories from accidental dilution by low-privilege agents.
- **Shannon Channel Clarity (Shannon):** Eliminating cognitive interference at the input stage maintains maximal entropy efficiency in downstream reasoning.

## Specification

### 1. Ingestion Intercept Flow (`tur learn`)

When `tur learn` or MCP `learn()` is called:

```
[Agent Calls `tur learn`]
         |
         v
[L2 Embedding / Keyword Semantic Probe]
         |
         +---> High Semantic Overlap Found with Polar Opposites?
         |        |
         |        +-- YES --> [Active TMS Conflict Interruption]
         |        |              |
         |        |              +-> (Agent / CLI Prompt for Resolution)
         |        |              |      |
         |        |              |      +-> Supersede: Marks old node `superseded_by`
         |        |              |      +-> Refute: Rejects new assertion with audit trail
         |        |              |      +-> Branch: Restricts scope to specific submodules
         |        |
         +-- NO  ---> [Normal Memory Commit & Merkle Stamp]
```

### 2. Resolution Action Grammar

When a conflict is surfaced via CLI or MCP error payload:

```json
{
  "status": "conflict_detected",
  "conflicting_memory_id": "concept-104e77a1",
  "existing_content": "Monolithic main.py handles all CLI commands.",
  "new_content": "Monolith removed; domain modules handle CLI commands directly.",
  "suggested_action": "supersede",
  "resolution_options": ["supersede", "refute", "scope_branch", "abort"]
}
```

The CLI supports autonomous resolution via explicit flags for automated batch scripts:
```bash
# Explicitly indicate supersession during learn
tur learn "Domain modules handle CLI directly" --type fact --supersedes "concept-104e77a1"

# Force commit without interactive resolution
tur learn "Experimental parallel mode" --type fact --allow-conflict
```

### 3. Core Memory Protection Invariant

If an incoming memory assertion contradicts a `core` tier memory (approved by a human via `tur-adm`), the conflict **cannot** be superseded automatically by an agent. The engine structurally rejects the assertion:
```text
[Golem Invariant Error]: Assertion contradicts Core Memory 'core-0012'.
Agent cannot supersede human-governed Core memories.
To propose a change, submit via `tur-adm proposal`.
```

## Backwards Compatibility

- Scripts running in non-interactive CI environments default to `--allow-conflict` with an emitted warning log, preserving legacy non-blocking behavior.
- The MCP server returns structured conflict payloads that modern tool-calling models can interpret and respond to in a single follow-up step.

## How to Teach This / Documentation Plan

- Document the TMS conflict resolution flags in `SKILL.md` and `docs/commands.md`.
- Add an architectural explanation in the *"Truth Maintenance & Contradiction Resolution"* section of the documentation.

## Reference Implementation

Draft conflict detector in `src/tur/introspection/interceptor.py`:

```python
from tur.models.memory import MemoryRecord
from tur.storage.memory import MemoryStore

class ContradictionInterceptor:
    def __init__(self, store: MemoryStore):
        self.store = store
        
    def check_conflict(self, new_record: MemoryRecord) -> list[MemoryRecord]:
        existing_memories = self.store.list_active(scope=new_record.scope)
        conflicts = []
        for mem in existing_memories:
            if mem.id == new_record.id:
                continue
            if self._is_polar_contradiction(mem.content, new_record.content):
                conflicts.append(mem)
        return conflicts
        
    def _is_polar_contradiction(self, a: str, b: str) -> bool:
        # Heuristic / semantic check for direct entity contradiction
        # E.g. negation match or opposing framework assignment to identical entity
        return False
```

## Rejected Ideas

- **Silent Auto-Overwriting:** Blindly replacing older memories with newer ones without confirmation was rejected because nuanced architectural trade-offs often require multiple perspectives or branch-specific context.
- **Blocking All Ingestion on LLM Verification:** Requiring a remote LLM API call on every single `tur learn` call was rejected to ensure local-first zero-latency offline operation. Heuristics and fast local embeddings are used instead.

## Open Questions

- [ ] What is the optimal cosine similarity and entity-overlap threshold for triggering an interactive conflict prompt?
- [ ] Should conflict resolution history be preserved as explicit edges in the L2 graph?

## Change Log

* **2026-08-27:**
    * Initial Draft formulated following architectural critique.
