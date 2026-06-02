---
title: "EP-0104: Federated Knowledge (Universal vs. Incarnational Memory)"
description: "Separates a Persona's universal knowledge from project-specific context in a federated two-tiered system."
icon: lucide/database
status: active
---

# EP-0104: Federated Knowledge (Universal vs. Incarnational Memory)

| Field       | Value                                                    |
|:------------|:---------------------------------------------------------|
| **EP**      | 0104                                                     |
| **Title**   | Federated Knowledge (Universal vs. Incarnational Memory) |
| **Author**  | The Architect                                            |
| **Status**  | Active                                                   |
| **Type**    | Standards Track                                          |
| **Created** | 2026-04-12                                               |
| **Updated** | 2026-04-18                                               |

## Abstract

Evolve the Deductive Memory architecture (EP-0103) and L1 Event Log to support a federated, two-tiered knowledge system.
This separates a
Persona's universal, first-principle knowledge (The "Soul") from its project-specific, contextual knowledge (The "
Mind"). The `tur wake` command will be updated to perform a federated compilation, merging the two memory banks to
create a complete, contextualized Persona.

## Motivation

A truly portable Persona must be able to distinguish between what it knows universally and what it knows about a
specific project. The current model stores all memories—from deep philosophical axioms to minor user preferences—in a
single, project-local directory.

This creates two problems:

1. **Redundancy:** Core knowledge (e.g., software design principles, mathematical truths) must be re-learned and
   re-stored for every new project.
2. **Portability:** When a Persona is moved to a new project, it carries with it a massive amount of irrelevant,
   project-specific baggage.

To create a reusable, efficient, and truly "wise" Persona, we must separate its essential self from its temporary
context.

## Rationale

This design aligns with the **Council Framework**:

* **Symmetry (Noether):** The architecture elegantly balances the global (universal) and the local (incarnational). The
  compilation process is a symmetrical merge operation.
* **Efficiency (Shannon):** Universal knowledge is stored once, globally. Project-specific knowledge is stored locally.
  This minimizes redundancy and reduces the size of both the global and local state files.
* **Consistency (Russell):** By separating concerns, we can ensure the Universal Memory Bank is a highly-stable,
  well-curated set of core axioms, while the Project Memory Bank can be more volatile and experimental.

## Specification

### 1. Federated Storage Locations

The MemoryManager will now read and write to two distinct locations:

* **Core Memory Bank (The "Soul" / Universal):**
    * **Location:** `~/.tur/personas/<uuid>/memories/`
    * **Content:** Universal, first-principle knowledge. Physics, mathematics, software design patterns, the Council
      Framework, core user philosophies. Written to when `scope == MemoryScope.UNIVERSAL` or `PERSONA`.

* **Project Memory Bank (The "Mind" / Incarnational):**
    * **Location:** `<project_root>/.tur/personas/<uuid>/memories/`
    * **Content:** Project-specific, incarnational knowledge. "This repo uses `uv`," "The user prefers `match/case`," "
      The database schema is X." Written to when `scope == MemoryScope.INCARNATION` or `USER`.

### 2. The `MemoryManager` Refactor

The `tur.memory.MemoryManager` will be updated:

1. **Dual Paths:** It will accept both a global and local base directory.
2. **`save(memory)` Routing:** When a memory is saved, the manager will inspect `memory.scope`. If it is `UNIVERSAL` or
   `PERSONA`, it writes to the global `~/.tur` path. If it is `INCARNATION` or `USER`, it writes to the local `./.tur`
   path.
3. **`load_all()` Merging:** When loading, it will read all `.yaml` files from *both* directories, merge the lists, and
   sort them chronologically.

### 3. Federated Compilation (`tur wake`)

Because `MemoryManager.load_all()` now handles the federation implicitly, `tur_compile` simply receives the merged
timeline of memories and injects them into the Constitution as before.

## Backwards Compatibility

* This is a non-destructive change. Existing projects that only have a local `.tur/` directory will continue to
  function, as the global path will simply fall back gracefully if missing.
* A migration script could be useful to move existing `UNIVERSAL` scoped memories from local to global, but is not
  strictly necessary for operation.

## Change Log

* **2026-04-18:**
    * Updated Status to Active.
    * Refined specification to focus on the `MemoryManager` routing based on `MemoryScope`.
* **2026-04-12:**
    * Initial Draft.