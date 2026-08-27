---
title: "EP-0133: Session Memory Observability and Delta Tracking"
description: "Introduces the tur diff CLI command and MCP tool to inspect memory mutations, additions, supersessions, and contradictions across sessions."
icon: lucide/git-commit
status: draft
---

# EP-0133: Session Memory Observability and Delta Tracking

| Field       | Value                                                         |
|:------------|:--------------------------------------------------------------|
| **EP**      | 0133                                                          |
| **Title**   | Session Memory Observability and Delta Tracking               |
| **Author**  | Eran Rivlis & Ariel                                           |
| **Status**  | Draft                                                         |
| **Type**    | Standards Track                                               |
| **Created** | 2026-08-27                                                    |
| **Updated** | 2026-08-27                                                    |

## Abstract

This proposal establishes a first-class **memory observability and diffing interface** for Tur. Currently, the evolution of an agent's memory bank between turns, sessions, and dreaming compactions is opaque: developers and agents cannot inspect what memories were created, updated, superseded, or refuted without manually inspecting raw YAML files or running low-level file diffs.

EP-0133 introduces:
1. **The `tur diff` Command & MCP Tool:** A dedicated diffing utility that compares memory states between two session checkpoints, across git revisions, or against the active working session.
2. **Epistemic Mutation Classification:** Categorizing deltas into `ADDED`, `SUPERSEDED`, `REFUTED`, `DECAYED`, and `MERGED`.
3. **Session Delta Summaries on `sleep()`:** Automatically emitting a structured change ledger upon session conclusion, giving developers and supervising humans complete visibility into agent learning.

## Motivation

When working with Tur across long-lived epics, agents frequently call `tur learn`, `tur note`, and `tur introspect`. While these operations mutate the L1 memory ledger and L2 cognitive graph, their tangible effect is invisible in standard agent workflows.

Specifically:
- Developers using Tur cannot easily answer: *"What did the agent learn or unlearn during the last 30 minutes of coding?"*
- Multi-agent swarms lack a standard mechanism to inspect what another agent learned during its isolated execution window before adopting its findings.
- Memory regressions (e.g. an agent writing an inaccurate fact that supersedes a correct architectural insight) cannot be easily identified or audited without full database forensics.

## Rationale

- **Baconian Empiricism (Bacon):** Observability is essential to scientific verification. You cannot govern what you cannot observe.
- **Feynman Clarity (Feynman):** Surface state changes in human-readable, beautifully styled terminal diffs and structured JSON payloads.
- **Golem Safety (Golem):** Enable human supervisors to catch authority drift and hallucinated facts before they crystallize into permanent axioms.

## Specification

### 1. The `tur diff` CLI Interface

```bash
# Compare current memory state against the start of the active session
tur diff

# Compare a specific session against its predecessor (EP-0130 lineage)
tur diff 20260827_150000_841444cd

# Compare memory state across two explicit session IDs
tur diff 20260825_190758_86152dcb 20260827_150000_841444cd

# Output as structured JSON (for MCP/agent consumption)
tur diff --json
```

### 2. Delta Classification & Presentation

Output is formatted with visual status indicators:

```text
Memory Delta: Session 20260827_150000_841444cd (4 mutations)

[+] ADDED (Fact)
    id: concept-8f2a1b9c
    scope: incarnation
    content: "SQLite signal queue uses WAL mode and busy_timeout=5000ms."
    provenance: observed at 9f83ab2c (src/tur/signals.py)

[~] SUPERSEDED (Insight)
    id: concept-104e77a1 -> superseded by concept-248c704a
    old: "main.py acts as the monolithic command router."
    new: "Monolith decomposed into isolated domain modules under src/tur/."

[-] REFUTED (Fact)
    id: concept-a9dc0560
    content: "SSE transport is supported on localhost:8000."
    reason: "Refuted by EP-0124 (SSE permanently removed in favor of stdio)."

[*] DECAYED (Fact)
    id: concept-40225d13
    content: "Active debug port is 9229."
    status: fresh -> stale (last verified 32 days ago)
```

### 3. Session Consummatum (`tur sleep`) Integration

When `tur sleep` or MCP `sleep()` executes, the generated session consolidation summary automatically appends the session memory delta:

```markdown
## Session Memory Ledger Delta
- Added: 2 facts, 1 insight
- Superseded: 1 insight
- Refuted: 0
- Stale flagged: 1
```

## Backwards Compatibility

- `tur diff` is a pure read-only addition. It introduces no schema breaks and requires no migrations.
- Historical sessions lacking explicit snapshot timestamps will compute diffs based on file creation/modification times.

## How to Teach This / Documentation Plan

- Add `tur diff` to the command reference table in `SKILL.md` and `docs/commands.md`.
- Include memory diff verification in debugging and code review workflows.

## Reference Implementation

Draft diff calculation engine in `src/tur/observability/diff.py`:

```python
from dataclasses import dataclass
from typing import Literal
from tur.models.memory import MemoryRecord

@dataclass
class MemoryDelta:
    status: Literal["ADDED", "SUPERSEDED", "REFUTED", "DECAYED", "MODIFIED"]
    record: MemoryRecord
    previous_record: MemoryRecord | None = None
    reason: str | None = None

def compute_session_diff(base_memories: dict[str, MemoryRecord], target_memories: dict[str, MemoryRecord]) -> list[MemoryDelta]:
    deltas = []
    
    # Added memories
    for mid, mem in target_memories.items():
        if mid not in base_memories:
            deltas.append(MemoryDelta(status="ADDED", record=mem))
            
    # Removed / Superseded / Modified
    for mid, base_mem in base_memories.items():
        if mid not in target_memories:
            # Check if superseded in target
            superseding = [m for m in target_memories.values() if m.provenance and m.provenance.context_ref == mid]
            if superseding:
                deltas.append(MemoryDelta(status="SUPERSEDED", record=superseding[0], previous_record=base_mem))
            else:
                deltas.append(MemoryDelta(status="REFUTED", record=base_mem))
        elif base_mem != target_memories[mid]:
            deltas.append(MemoryDelta(status="MODIFIED", record=target_memories[mid], previous_record=base_mem))
            
    return deltas
```

## Rejected Ideas

- **Raw Git-Only Diffing:** Relying on `git diff .tur/memories/` was rejected because it exposes raw unformatted YAML, leaks Merkle hashes, and fails to parse semantic relationships (such as supersession and TMS refutation edges).

## Open Questions

- [ ] Should `tur diff` support filtering by memory type (e.g. `tur diff --type fact`) or scope (e.g. `tur diff --scope universal`)?

## Change Log

* **2026-08-27:**
    * Initial Draft formulated following architectural critique.
