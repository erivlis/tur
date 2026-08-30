---
title: "EP-0141: Lamport Vector Clocks and Causal Consistency in Inter-Agent Signal Protocol (IASP)"
description: "Replaces scalar integer autoincrements in IASP with Lamport Vector Clocks, establishing formal partial ordering (N^k, <=), causal delivery, and concurrent conflict detection across multi-agent swarms."
icon: lucide/clock
status: draft
---

# EP-0141: Lamport Vector Clocks and Causal Consistency in Inter-Agent Signal Protocol (IASP)

| Field        | Value                                                                              |
|:-------------|:-----------------------------------------------------------------------------------|
| **EP**       | 0141                                                                               |
| **Title**    | Lamport Vector Clocks and Causal Consistency in Inter-Agent Signal Protocol (IASP) |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                              |
| **Sponsor**  | Council of Giants                                                                  |
| **Delegate** | Noether (Causal Invariants), Popper (Falsifiable Race Detection)                   |
| **Status**   | Draft                                                                              |
| **Type**     | Standards Track                                                                    |
| **Created**  | 2026-08-28                                                                         |
| **Updated**  | 2026-08-28                                                                         |

---

## Abstract

This proposal extends the **Inter-Agent Signal Protocol (IASP)** (EP-0118, EP-0123) by introducing **Lamport Vector
Clocks** $\mathbf{V} \in \mathbb{N}^k$. In concurrent multi-agent environments (e.g. parallel Copilot, Claude Code, and
Antigravity instances operating on a shared repository), scalar database sequence numbers cannot distinguish between
**causally ordered events** ($a \prec b$) and **concurrent independent actions** ($a \parallel b$). By attaching vector
clocks to signal payloads and tracking causal history, Tur guarantees causal delivery order, detects parallel merge
conflicts before write commits, and provides formal partial-order consistency across distributed agent swarms.

---

## Motivation

In EP-0118 and [`src/tur/session.py`](file:///C:/dev/erivlis/tur/src/tur/session.py), IASP uses an autoincrementing
scalar integer `sequence` in the SQLite `signals` table. While sufficient for single-threaded sequential turns, scalar
sequence numbers fail in multi-agent environments:

1. **The Concurrency Illusion:** When two agents broadcast signals concurrently, SQLite assigns arbitrary scalar IDs
   (e.g. Signal 12 and Signal 13), creating the false appearance that Signal 13 was authored in response to Signal 12.
2. **Causal Inversion:** If an agent acts on incomplete local state and emits a directive based on a stale assumption,
   other agents cannot detect that the directive was causally disconnected from recent decisions.
3. **Lack of Conflict Detection:** Without vector timestamps, parallel subagents cannot mathematically determine whether
   their code refactor proposals are independent or in direct collision.

---

## Rationale

### Alignment with the Council Framework

- **Symmetry & Causal Invariance (Noether):** Conserves relativistic causal relationships across distributed timelines.
  Causal precedence ($a \prec b$) is invariant under agent relocation or SQLite replication.
- **Falsifiability & Conflict Exposure (Popper):** Concurrent operations ($a \parallel b$) are exposed explicitly rather
  than silently masked by monotonic sequence integers.
- **Boundary Containment (Golem):** Strict vector clock schemas prevent corrupted or out-of-order signals from mutating
  shared session state.

---

## Specification

### 1. Vector Clock Definition & Algebraic Partial Order

Let $N$ be the number of active agent manifestations in a session. Each agent $i \in \{1, \dots, N\}$ maintains a vector
clock:

$$\mathbf{V}_i = \langle v_{i, 1}, v_{i, 2}, \dots, v_{i, N} \rangle \in \mathbb{N}^N$$

#### The Three Operational Rules:

1. **Local Emission:** Before Agent $i$ broadcasts a signal:
   $$\mathbf{V}_i[i] \leftarrow \mathbf{V}_i[i] + 1$$
   The signal payload is stamped with $\mathbf{V}_{\text{sig}} = \mathbf{V}_i$.
2. **Message Ingestion & Merge:** When Agent $j$ receives a signal stamped with $\mathbf{V}_{\text{sig}}$:
   $$\mathbf{V}_j[k] \leftarrow \max\left (\mathbf{V}_j[k], \mathbf{V}_{\text{sig}}[k]\right) \quad \forall k \in \{1, \dots, N\}$$
   $$\mathbf{V}_j[j] \leftarrow \mathbf{V}_j[j] + 1$$
3. **Causal Comparison:**
    - **$a$ causally
      precedes $b$ ($a \prec b$):** $\forall k: \mathbf{V}_a[k] \le \mathbf{V}_b[k] \wedge \exists m: \mathbf{V}_a[m] < \mathbf{V}_b[m]$
    - **$a$ and $b$ are concurrent ($a \parallel b$):** $\neg (a \prec b) \wedge \neg (b \prec a)$

```
   Agent α (Claude Code)                           Agent β (Antigravity)
          │                                                 │
 [Local Action: V=(1, 0)]                                   │
          │                                                 │
          ├─────── Broadcast Signal (V=(2, 0)) ────────────►│
          │                                                 │ [Ingest & Merge]
          │                                                 │  V_β = max(V_β, (2, 0)) + (0, 1)
          │                                                 │  V_β = (2, 1)
```

### 2. Database Schema Extension (`signals` Table in `session.py`)

The SQLite `signals` schema in [`src/tur/session.py`](file:///C:/dev/erivlis/tur/src/tur/session.py) is extended:

```sql
ALTER TABLE signals
    ADD COLUMN vector_clock TEXT NOT NULL DEFAULT '{}';
```

Where `vector_clock` stores a JSON dictionary mapping `agent_id -> logical_counter` (e.g.
`{"agent-alpha": 2, "agent-beta": 1}`).

### 3. Causal Delivery Hook in `read_signals_logic()`

When an agent polls signals via `read_signals_logic()`, signals are sorted by **topological causal order** rather than
simple scalar sequence:

```python
def is_causally_ready(sig_clock: dict[str, int], agent_clock: dict[str, int], sender_id: str) -> bool:
    """Verifies that all prerequisite causal dependencies have been processed."""
    for agent, count in sig_clock.items():
        if agent == sender_id:
            if count != agent_clock.get(agent, 0) + 1:
                return False
        else:
            if count > agent_clock.get(agent, 0):
                return False
    return True
```

---

## Backwards Compatibility

- **Legacy Signals:** Existing signals with empty `vector_clock` default to `{}` and are processed via scalar sequence
  ordering.
- **Single-Agent Sessions:** For single-agent sessions, vector clocks reduce trivially to a single-element
  vector $\langle v_1 \rangle$, maintaining zero overhead.

---

## How to Teach This / Documentation Plan

- Add an architecture guide on multi-agent synchronization in `docs/architecture/iasp-causality.md`.
- Document vector clock inspection in `tur-adm signal inspect`.

---

## Reference Implementation

- Signal Subsystem: `src/tur/session.py`
- Clock Utilities: `src/tur/vector_clock.py`
- Research reference:
  `references/explorations/EXP-0005-mathematical-and-graph-theoretic-code-audit/05_non_ep_code_path_mathematical_optimizations.md`

---

## Rejected Ideas

- **TrueTime / Wall-Clock Synchronization:** Rejected because local system clocks across developer machines and Docker
  containers drift significantly (NTP skew), causing false ordering.
- **Single Global SQLite Sequence Lock:** Rejected because global sequence locking forces serialization across all
  agents, destroying parallelism.

---

## Open Questions

- [ ] Should dynamic agent registration automatically expand the vector clock dimension without resetting session state?

---

## Change Log

* **2026-08-28:**
    * Initial Draft authored based on the Non-EP Codebase Mathematical Audit.
