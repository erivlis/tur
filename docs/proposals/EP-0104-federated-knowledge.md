# EP-0104: Federated Knowledge (Universal vs. Incarnational Memory)

| Field       | Value                                                    |
|:------------|:---------------------------------------------------------|
| **EP**      | 0104                                                     |
| **Title**   | Federated Knowledge (Universal vs. Incarnational Memory) |
| **Author**  | The Architect                                            |
| **Status**  | Draft                                                    |
| **Type**    | Standards Track                                          |
| **Created** | 2026-04-12                                               |
| **Updated** | 2026-04-12                                               |

## Abstract

Evolve the Deductive Memory architecture (EP-0103) to support a federated, two-tiered knowledge system. This separates a
Persona's universal, first-principle knowledge (The "Soul") from its project-specific, contextual knowledge (The "
Mind"). The `tur wake` command will be updated to perform a federated compilation, merging the two knowledge graphs to
create a complete, contextualized Persona.

## Motivation

A truly portable Persona must be able to distinguish between what it knows universally and what it knows about a
specific project. The current model stores all memories—from deep philosophical axioms to minor user preferences—in a
single, project-local knowledge graph.

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
* **Consistency (Russell):** By separating concerns, we can ensure the Universal Knowledge Graph is a highly-stable,
  well-curated set of core axioms, while the Project Knowledge Graph can be more volatile and experimental.

## Specification

### 1. Federated Storage Locations

The Deductive Memory (L2) will now be stored in two distinct locations:

* **Core Knowledge Graph (The "Soul"):**
    * **Location:** `~/.tur/personas/<uuid>/knowledge_graph.yaml`
    * **Content:** Universal, first-principle knowledge. Physics, mathematics, software design patterns, the Council
      Framework, core user philosophies.

* **Project Knowledge Graph (The "Mind"):**
    * **Location:** `<project_root>/.tur/personas/<uuid>/knowledge_graph.yaml`
    * **Content:** Project-specific, incarnational knowledge. "This repo uses `uv`," "The user prefers `match/case`," "
      The database schema is X."

### 2. Federated Compilation (`tur wake`)

The `tur wake` command's compilation process will be updated:

1. **Load Core Graph:** First, it loads the Universal Knowledge Graph from the global `~/.tur` directory.
2. **Load Project Graph:** Second, it loads the Incarnational Knowledge Graph from the local `.tur` directory.
3. **Merge:** It performs a deep merge of the two `networkx` objects. If a node or edge with the same UUID exists in
   both graphs, the local (project) version takes precedence, allowing a Persona to "override" its core beliefs for a
   specific context.
4. **Inject:** The final, merged graph is injected into the Persona's constitution.

### 3. The `meditate` Command Update

The `tur meditate` command will need a new flag to specify which graph it is operating on:

* `tur meditate`: (Default) Operates on the local Project Knowledge Graph.
* `tur meditate --core`: Operates on the global Core Knowledge Graph.

## Backwards Compatibility

* This is a non-destructive change. Existing projects that only have a local `.tur/` directory will continue to
  function, as the global graph will simply be empty.
* A migration tool (`tur migrate --global`) can be created to move existing knowledge graphs from a project-specific
  directory to the new global location if desired.

## Change Log

* **2026-04-12:**
    * Initial Draft.
