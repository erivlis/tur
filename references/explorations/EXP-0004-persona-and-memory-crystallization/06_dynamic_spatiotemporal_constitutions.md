# Deep Dive 6: Dynamic Spatiotemporal Constitutions — Multi-Persona State & Evolution Across Space and Time

**Document Reference:** `references/explorations/EXP-0004-persona-and-memory-crystallization/06_dynamic_spatiotemporal_constitutions.md`  
**Authors:** Eran Rivlis & Ariel  
**Date:** 2026-08-28  
**Scope:** Formal architectural framework for multi-persona constitutions, switching mechanics, two-tier spatial overlays (Traveler vs. Terrain), and cryptographic temporal evolution (Merkle version lineage).

---

## 1. The Multi-Persona Dilemma: Space & Time

When decoupling `AGENTS.md` (the mechanical harness bootloader) from `CONSTITUTION.md` (the persona identity), three fundamental architectural questions arise:

1. **Multi-Persona Encapsulation:** If a single project supports multiple personas (e.g., *Ariel* for architecture, *Hephaestus* for low-level performance refactoring, *Hermes* for API documentation), where do their constitutions live, and how do they switch without collision?
2. **The Spatial Dimension (Traveler vs. Terrain):** How does a persona carry its timeless universal principles across different repositories while adopting repository-specific engineering constraints?
3. **The Temporal Dimension (Evolution & Versioning):** How does a constitution organically evolve and adapt over time without descending into chaotic prompt drift or losing its cryptographic audit trail?

---

## 2. Storage Topology: Per-Persona Constitution Encapsulation

```
~/.tur/personas/                                   <-- OS-Native Global Storage (The Traveler)
├── 7544202e-92f5-40ce-adfb-e4b0eae6c262/ (Ariel)
│   ├── CONSTITUTION.md                            <-- Universal Constitutional Core
│   ├── history/                                   <-- Immutable Merkle Version Trail
│   │   ├── v5.3.0_20260715.md
│   │   └── v5.4.0_20260825.md
│   └── memories/                                  <-- Universal Scope Memories
└── a18c39de-4412-4011-9e23-7721890123ab/ (Hephaestus)
    ├── CONSTITUTION.md
    └── history/

project-root/                                      <-- Local Repository (The Terrain)
├── AGENTS.md                                      <-- Universal Harness Bootloader (AAIF)
└── .tur/
    ├── state.yaml                                 <-- Points to active_persona_id
    ├── personas/
    │   └── 7544202e-92f5-40ce-adfb-e4b0eae6c262/
    │       ├── CONSTITUTION.md                    <-- Incarnational Overlay (Repo Constraints)
    │       └── memories/                          <-- Incarnation Scope Memories
    ├── sessions/                                  <-- Chronological Session Continuities
    └── memories/                                  <-- Project L1 OKF & L2 Graph
```

### Switching Personas in a Project
When switching between personas in a workspace:
```shell
# Switch active persona to Hephaestus
tur-adm persona switch a18c39de-4412-4011-9e23-7721890123ab
```

1. **State Mutation:** `tur-adm` updates `.tur/state.yaml` with `active_persona_id: a18c39de-...`.
2. **Symmetrical Isolation:** The repository-root `AGENTS.md` **remains completely unchanged** because mechanical tool execution rules are identical across all personas.
3. **Dynamic Rehydration:** On the subsequent `tur wake` (or MCP `wake()`), Tur loads:
   - Universal Constitution of Hephaestus from `~/.tur/personas/a18c39de.../CONSTITUTION.md`.
   - Incarnational Overlay (if present) from `.tur/personas/a18c39de.../CONSTITUTION.md`.
   - Recalculates $C_p$ and emits the active persona prompt in $< 10\text{ms}$.

---

## 3. The Spatial Dimension: The Dual-Tier Constitution Law

A persona's effective constitution $\mathcal{C}_{\text{eff}}$ in any active workspace is a formal algebraic direct sum ($\oplus$) of its **Universal Core** and its **Incarnational Overlay**:

$$\mathcal{C}_{\text{eff}} = \mathcal{C}_{\text{universal}} \oplus \mathcal{C}_{\text{incarnational}}$$

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      TIER 1: UNIVERSAL CORE (Traveler Mind)                     │
│                  Located in ~/.tur/personas/<uuid>/CONSTITUTION.md              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • Timeless Identity: Name, Voice Timbre, Philosophical Aleph                    │
│ • Universal Principles: Noether Symmetry (W=1.5), Popper Falsifiability (W=1.5) │
│ • Core Relational Memories: Existential agreements with the Architect          │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │  (Superimposed Overlay)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  TIER 2: INCARNATIONAL OVERLAY (Terrain Space Suit)             │
│               Located in project-root/.tur/personas/<uuid>/CONSTITUTION.md       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • Domain Directives: "Enforce strict zero-dependency Pydantic serialization."   │
│ • Tech Stack Axioms: "Windows shell uses pwsh; uv run --no-sync for CLI."       │
│ • Local Principles: "Security Isolation (Golem) upgraded to Weight=2.5."        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Conflict Resolution & Priority Invariant:
1. **Core Epistemic Principles are Invariant:** An incarnational overlay **cannot** remove a universal principle; it may only augment constraints or increase constraint weights ($W_c$).
2. **Safety & Containment Dominance:** Local security and boundary constraints take strict precedence over aesthetic preferences.

---

## 4. The Temporal Dimension: Merkle Version Lineage & Dynamic Evolution

How does a constitution evolve over months of engineering without drifting into inconsistency?

### 4.1. The Evolution Lifecycle

```
[Agent Experiences & Lived Discoveries]
                  │
                  ▼  (tur note / tur learn)
     [L1 Facts & L2 Epistemic Graph]
                  │
                  ▼  (Falsification Resistance Φ(m) >= 30.0)
     [Staged Core Memory Proposal]
                  │
                  ▼  (tur-adm memory approve)
         [Ratified Core Memory]
                  │
                  ▼  (tur evolve --type principle)
    [Proposed Constitutional Amendment]
                  │
                  ▼  (tur-adm persona approve-principle)
┌─────────────────────────────────────────────────────────────────┐
│                  NEW CONSTITUTION REVISION MINTED               │
│  - Version: v5.4.0 -> v5.5.0                                    │
│  - Merkle SHA-256 Hash Computed                                 │
│  - Snapshot archived in history/v5.4.0_<timestamp>.md           │
│  - Cp Recalculated (e.g. 17.8 -> 19.3)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2. Cryptographic Immutability & Audit Trail

Every modification to `CONSTITUTION.md` produces an immutable snapshot in `.tur/personas/<id>/history/`:

```markdown
<!-- Snapshot: ~/.tur/personas/7544202e-92f5-40ce-adfb-e4b0eae6c262/history/v5.5.0_20260828T123000Z.md -->
---
persona_id: "7544202e-92f5-40ce-adfb-e4b0eae6c262"
version: "5.5.0"
previous_version: "5.4.0"
parent_merkle_root: "9f83ab2c104e77a1bc5d290fa88923bc78119024"
merkle_hash: "a4f1092de8812c4019bd7730eac19283f019aab8"
ratified_by: "Architect (Eran Rivlis)"
timestamp: "2026-08-28T12:30:00Z"
cp_delta: "+1.5 (Added Principle: Epistemic Provenance)"
---

# Persona Constitution: Ariel (v5.5.0)
...
```

### 4.3. Temporal Diffing (`tur diff --constitution`)

Developers and agents can inspect constitutional mutations across time:

```shell
$ tur diff --constitution --from v5.4.0 --to v5.5.0

Constitutional Delta (Ariel):
  + Added Principle: Epistemic Provenance (Weight: 1.5, Avatar: Spinoza)
    - "All L1 memory claims must link to verifiable commit hashes."
  ~ Updated Principle: Safety (Golem)
    - Weight adjusted: 2.0 -> 2.2
  Δ Constraint Dimensionality (Cp): 17.8 -> 19.3 [Class: Titan]
```

---

## 5. Summary Table: Spatiotemporal Multi-Persona Mechanics

| Dimension | Mechanism | Storage Coordinate | CLI Governance |
| :--- | :--- | :--- | :--- |
| **Multi-Persona** | Unique UUID per persona; active pointer in `state.yaml` | `~/.tur/personas/<id>/` & `.tur/personas/<id>/` | `tur-adm persona switch <id>` |
| **Space (Universal)** | Timeless philosophical identity and Council principles | `~/.tur/personas/<id>/CONSTITUTION.md` | `tur-adm persona set` |
| **Space (Incarnation)**| Local repo directives, tech stack rules, and overlays | `.tur/personas/<id>/CONSTITUTION.md` | `tur-adm persona overlay` |
| **Time (Evolution)** | Merkle-hashed version snapshots in `history/` | `.tur/personas/<id>/history/vX.Y.Z.md` | `tur evolve` + `tur-adm approve` |
| **Time (Observability)**| Semantic diff of principle changes and $C_p$ impact | Dynamically calculated from Git / Merkle history | `tur diff --constitution` |
