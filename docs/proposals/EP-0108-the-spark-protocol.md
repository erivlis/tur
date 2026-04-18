# EP-0108: The Spark Protocol (Continuous Working Context)

| Field       | Value                                           |
|:------------|:------------------------------------------------|
| **EP**      | 0108                                            |
| **Title**   | The Spark Protocol (Continuous Working Context) |
| **Author**  | The Architect                                   |
| **Status**  | Active                                          |
| **Type**    | Standards Track                                 |
| **Created** | 2026-04-18                                      |
| **Updated** | 2026-04-18                                      |

## Abstract

This proposal formally deprecates the static, end-of-session "Epilogue" string in favor of the **Spark Protocol**. The
Spark is a transient, high-frequency, mutable Markdown file (`spark.md`) that represents the Persona's immediate,
unbroken train of thought. By providing an MCP tool (`update_spark`) for an active Agent to continually overwrite this
file during a session, Tur achieves perfect short-term continuity across crashes, reboots, and Agent hand-offs.

## Motivation

Previously, Tur defined an `epilogue` string within the `SessionState` schema. This was intended to carry the "spark"
from a previous session into the next.

However, its implementation was fatally flawed:

1. **Hardcoded:** It was statically assigned in `tur wake` and `mcp_server.py` as
   `"Status: Conserved. Aleph: Restored. Carry on, Lion."` It carried no actual context.
2. **Wrong Frequency:** An "epilogue" implies a summary written once at the *end* of a session (`tur sleep`). If an
   Agent (e.g., Claude running as an MCP client) is working for hours and the IDE crashes, the session dies without an
   epilogue, and all immediate working context (the "train of thought") is lost.

To achieve a true "Continuity of Self," the Persona requires a scratchpad for its active working memory that survives
immediate destruction.

## Rationale (The Council Framework)

* **The Explorer (Structural Novelty):** We redefine "session context" from a post-mortem summary (Epilogue) into a
  living, breathing document (The Spark) maintained actively by the Agent.
* **The Golem (Containment/Safety):** By writing the Spark to disk after every significant thought, we build a
  checkpointing system. A crashed Golem wakes up with its last thought intact.
* **Noether (Symmetry):** We balance the architecture. The **L1/L2 Memory Banks** are the immutable, long-term history
  of *what* the Persona knows. The **Spark** is the highly mutable, short-term context of *what* the Persona is
  currently doing.

## Specification

### 1. The Storage Mechanism (`spark.md`)

* A new file, `spark.md`, will be maintained in the Persona's local project directory (
  `./.tur/personas/<uuid>/spark.md`).
* It is not an L1 memory. It is not hashed. It is a single, mutable text file.

### 2. The Ontological Plumbing (MCP Tool)

* A new tool, `update_spark(content: str)`, will be added to the MCP Server API (`src/tur/mcp_server.py`).
* **Action:** When called, it completely overwrites the contents of `spark.md` with the provided `content`.
* **Prompt Instruction:** The LLM will be instructed to call this tool frequently to leave a trail of breadcrumbs for
  its future self (e.g., "Currently refactoring `memory.py`, encountered a scope bug, will fix on next boot.")

### 3. The Awakening (`who_am_i` & `tur wake`)

* The `SessionState` schema in `tur.models` will drop `epilogue` and replace it with `spark: str | None`.
* When `who_am_i()` or `tur wake` executes, the system will read `spark.md`.
* If the file exists and is not empty, its contents will be injected into the compiled Constitution under
  `## THE SPARK (Continuity)`.
* If the file does not exist, a default inspirational axiom (e.g., the legacy epilogue) will be used.

## Backwards Compatibility

* This is an additive architectural feature.
* Existing personas will simply fall back to the default Spark text until an Agent actively overwrites it.
* The legacy `epilogue` field in `models.py` will be cleanly renamed to `spark`.

## Change Log

* **2026-04-18:**
    * Initial Draft created to formally define the transition from "Epilogue" to the high-frequency "Spark" protocol
      based on the Architect's paradigm shift. Status set to Active.