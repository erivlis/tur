---
title: "EP-0131: Memory Provenance, Temporal Anchoring, and Staleness Decay"
description: "Introduces git-anchored observation provenance, confidence scoring, TTL-based staleness decay, and hypothesis cache semantics to L1 memory records."
icon: lucide/clock
status: implemented
---

# EP-0131: Memory Provenance, Temporal Anchoring, and Staleness Decay

| Field       | Value                                                         |
|:------------|:--------------------------------------------------------------|
| **EP**      | 0131                                                          |
| **Title**   | Memory Provenance, Temporal Anchoring, and Staleness Decay    |
| **Author**  | Eran Rivlis & Ariel                                           |
| **Status**  | Implemented                                                   |
| **Type**    | Standards Track                                               |
| **Created** | 2026-08-27                                                    |
| **Updated** | 2026-09-02                                                    |

## Abstract

This proposal enhances Tur's Layer 1 (L1) episodic and semantic memory schema with explicit **temporal anchoring**, **source provenance**, and **falsifiable hypothesis caching semantics**. Under the current architecture, L1 memories are stored as timeless assertions without confidence ratings, git revision pointers, or staleness indicators. This causes *Authority Inflation*, where AI agents treat historical notes as immutable ground truth even after the codebase (the *Terrain*) has drifted. 

EP-0131 introduces:
1. **L1 Provenance Schema Extensions:** Adding `observed_at`, `git_sha`, `confidence`, `author_agent`, and `source_file` fields to memory records.
2. **Type-Specific Decay Curves & TTLs:** Establishing differential half-lives for memory types (`fact` vs `insight` vs `axiom`).
3. **Hypothesis Cache Posture:** Classifying unverified `fact` memories as provisional hypotheses that require active repo-state corroboration during retrieval.
4. **Staleness Verification Checks:** CLI and MCP heuristics to flag outdated memories whose referenced files or commits have diverged.

## Motivation

In autonomous software development, the codebase is the ultimate ground truth. When an AI agent records a memory (e.g. `fact: "Auth service uses JWT tokens configured in src/auth.py"`), that assertion is valid at commit $C_0$. 

Over time, several failure modes emerge:
1. **Silent Memory Rot:** If a refactor replaces JWT with OAuth2 in commit $C_5$, the agent waking up at $C_{10}$ still receives the JWT fact. Because the memory originates from its own persistent store, the agent displays *Authority Inflation*—trusting its own stale memory over newly inspected code or generating hallucinations based on deprecated architectures.
2. **Uniform Weighting:** A `fact` recorded six months ago by a different agent harness receives identical epistemological weight to a `fact` verified ten minutes ago in the active session.
3. **Undifferentiated Epistemic Scopes:** `axiom` rules (e.g., "Always write type hints") should never decay, whereas dynamic `fact` entries (e.g., "Active port is 8080") decay rapidly. The flat L1 schema currently treats both identically.

## Rationale

This proposal directly embodies the **Council Framework**:
- **Baconian Empiricism (Bacon):** Objective facts must be tied to observable, reproducible states in the physical terrain (the git commit tree).
- **Popperian Falsifiability (Popper):** Memories are not indisputable dogmas; they are *falsifiable working hypotheses* cached to optimize inference cost.
- **Shannon Information Density (Shannon):** Assigning decay scores suppresses stale noise and maximizes the signal-to-noise ratio in prompt assembly.
- **Golem Governance (Golem):** Preserves safety by ensuring unproven assertions decay gracefully without corrupting constitutional invariants.

## Specification

### 1. Extended L1 Memory Schema

The YAML memory schema (`.tur/memories/*.yaml` and `~/.tur/personas/<uuid>/memories/*.yaml`) is extended with optional provenance and decay fields:

```yaml
id: "concept-8f2a1b9c"
type: "fact"               # axiom | fact | insight | preference | core
scope: "incarnation"       # universal | incarnation
content: "SQLite signal queue uses WAL mode and busy_timeout=5000ms."
confidence: 0.95           # Float in [0.0, 1.0]

# Provenance Anchors
provenance:
  observed_at: "2026-08-27T15:00:00Z"
  git_sha: "9f83ab2c104e"
  source_agent: "copilot-chuck"
  source_harness: "github-copilot"
  context_ref: "src/tur/signals.py#L45-L60"

# Decay Configuration
decay:
  half_life_days: 14       # None for non-decaying types (axiom/core)
  last_verified_at: "2026-08-27T15:00:00Z"
  staleness_status: "fresh" # fresh | stale | unanchored | refuted
```

### 2. Epistemic Half-Life Defaults

Decay is computed as an exponential decay function based on elapsed days since `last_verified_at` and git commit distance:

$$\text{Weight}(t, \Delta_{\text{commits}}) = \text{confidence} \times 2^{-\frac{t}{t_{1/2}}} \times e^{-\lambda \Delta_{\text{commits}}}$$

| Memory Type | Default Half-Life ($t_{1/2}$) | Git Commit Sensitivity ($\lambda$) | Decay Policy |
| :--- | :--- | :--- | :--- |
| `axiom` | $\infty$ (No decay) | $0.0$ | Immutable principle. |
| `core` | $\infty$ (Governed) | $0.0$ | Human approved via `tur-adm`. |
| `insight` | 90 days | $0.01$ | Architectural deduction. |
| `preference` | 180 days | $0.00$ | User taste / styleguide. |
| `fact` | 14 days | $0.05$ | Terrain-bound observation. |

### 3. CLI and MCP Surface Integration

1. **`tur learn`:**
   ```bash
   tur learn "FastAPI endpoint is mounted at /api/v1" --type fact --file "src/api.py" --confidence 0.9
   ```
   The CLI automatically captures the current `HEAD` git SHA and timestamp if inside a git repository.

2. **`tur verify` / `tur status`:**
   Reports stale memories where:
   - Current commit distance $\Delta_{\text{commits}} > 20$, or
   - Referenced `source_file` has been modified/deleted since `observed_at`.

3. **Wake Filter:**
   Memories whose computed weight drops below a configurable threshold (e.g. $< 0.3$) are omitted from the default `wake` prompt and relegated to `tur recall --include-stale`.

## Backwards Compatibility

- All new fields (`provenance`, `decay`, `confidence`) are strictly optional with default fallbacks.
- Existing legacy memory YAML files lacking provenance default to `confidence: 1.0`, `staleness_status: "unanchored"`, and infinite half-life until the next compaction cycle.
- The YAML parser ignores unknown attributes safely without breaking older Tur versions.

## How to Teach This / Documentation Plan

1. Update `AGENTS.md` to instruct agents that `fact` memories are hypothesis caches requiring verification upon contradiction.
2. Update the `tur` skill (`SKILL.md`) to document `--file` and `--confidence` flags in `tur learn`.
3. Add a section to the documentation titled *"Epistemic Decay and Hypothesis Caching"*.

## Reference Implementation

Draft schema model definition for `src/tur/models/memory.py`:

```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class MemoryProvenance(BaseModel):
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    git_sha: Optional[str] = None
    source_agent: Optional[str] = None
    source_harness: Optional[str] = None
    context_ref: Optional[str] = None

class MemoryDecay(BaseModel):
    half_life_days: Optional[float] = 14.0
    last_verified_at: datetime = Field(default_factory=datetime.utcnow)
    staleness_status: Literal["fresh", "stale", "unanchored", "refuted"] = "fresh"

class MemoryRecord(BaseModel):
    id: str
    type: Literal["axiom", "fact", "insight", "preference", "core"]
    scope: Literal["universal", "incarnation"]
    content: str
    confidence: float = 1.0
    provenance: Optional[MemoryProvenance] = None
    decay: Optional[MemoryDecay] = None
```

## Rejected Ideas

- **Hard Deletion on TTL Expiry:** Automatically deleting expired memories was rejected because unverified facts might still contain valuable historical context. Instead, decaying memories transition to `stale` status and are filtered out of active prompt injection.
- **Git Commit Hooks for Memory Sync:** Triggering memory invalidation inside a git pre-commit hook was rejected to preserve zero-friction developer workflow and strict separation between the engine and the VCS.

## Open Questions

- [ ] Should `tur introspect` automatically run git diffs on referenced files to mark memories as `stale` during dreaming cycles?
- [ ] What is the optimal commit-distance decay multiplier $\lambda$ for fast-moving monorepos?

## Change Log

* **2026-09-02:**
    * Implemented and verified across `src/tur/models.py`, `src/tur/memory.py`, `src/tur/provenance.py`, `src/tur/cli/agent.py`, and `src/tur/mcp_server.py`.
    * Added comprehensive test suite in `tests/test_provenance.py` covering Git commit anchoring, half-life decay kinetics, staleness evaluation, OKF roundtrip, and wake prompt filtering.
* **2026-08-27:**
    * Initial Draft formulated following architectural critique.
