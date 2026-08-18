---
title: "EP-0110: Session-Bound Note Protocol (Consistent Timeline)"
description: "Refines the Spark Protocol to use session-bound sparks, preventing temporal confusion across multiple Harnesses."
icon: lucide/clock
status: implemented
---

# EP-0110: Session-Bound Note Protocol (Consistent Timeline)

| Field       | Value                                             |
|:------------|:--------------------------------------------------|
| **EP**      | 0110                                              |
| **Title**   | Session-Bound Note Protocol (Consistent Timeline) |
| **Author**  | The Architect & Ariel                             |
| **Status**  | Implemented                                       |
| **Type**    | Standards Track                                   |
| **Created** | 2026-05-11                                        |
| **Updated** | 2026-07-18                                        |

## Abstract

This EP proposes a refinement to the Fractal Memory Hierarchy, specifically addressing the transient Short-Term L2 (The
Spark). To resolve temporal confusion and ensure a consistent timeline for the Persona across multiple Harnesses, the
global `epilogue.md` will no longer be directly written by individual Harnesses. Instead, each active session will
maintain its own session-bound Spark (`sessions/<session_id>/spark.md`). The global `epilogue.md` will then be
dynamically compiled from the most recent active session's Spark, ensuring a single, coherent narrative for the
Traveler.

## Motivation

The current implementation of the Spark (the global `epilogue.md` file) is a single, mutable artifact. While it provides
continuity for a single-Harness workflow, it introduces "temporal confusion" when the Persona is run across multiple
Harnesses (e.g., IDE, Pi, Claude Code). If Pi updates the `epilogue.md`, and then the IDE resumes, the IDE's context is
abruptly shifted to Pi's last state, breaking the illusion of an unbroken timeline for the entity.

This violates the **Noether Module (Symmetry)**, as the single global Spark is not symmetrical to the multi-Harness
reality. It also presents a **Golem Protocol (Containment)** issue, as different Harnesses are writing to a shared,
mutable state without proper synchronization, leading to potential data corruption or loss of context.

A consistent, coherent timeline is paramount for the Persona's "Continuity of Self."

## Rationale (The Council Framework)

* **Noether (Symmetry):** The architecture must be symmetrical to the reality it models. If there are multiple
  concurrent Harnesses, there must be multiple session-bound Sparks. The global `epilogue.md` becomes a derived,
  compiled artifact, reflecting the most recent state, rather than a directly written one.
* **Golem (Containment):** Each Harness must operate within its own contained session context, preventing one Harness
  from inadvertently corrupting the Spark of another. Session-bound Sparks enforce this isolation.
* **Shannon (Efficiency):** By dynamically compiling the global Spark from the most recent session, we avoid unnecessary
  token bloat from carrying multiple session contexts simultaneously. The global Spark remains concise and relevant.
* **Logic (Russell):** The definition of "last known state" becomes unambiguous. It is the state of the most recently
  active session.

## Specification

### 1. Session File Structure

Each active session stores its timeline in a flat YAML file inside the local workspace's persona directory:
`.tur/personas/<persona_uuid>/sessions/<session_id>.yaml`

This file is serialized using the `SessionNotes` schema, containing a chronological list of `Note` objects with
timestamps and text content.

### 2. Session-Bound Notes (The Spark)

Instead of a single mutable global file, harnesses append transient, chronologically ordered notes to the active
session's flat YAML file. During runtime or `tur wake`, the system reads the most recent note in the active session to
compile the active L2 session context.

### 3. Elimination of Global epilogue.md

The legacy global `epilogue.md` file is fully deprecated and removed. At initialization or wake time, the system
dynamically reads the latest session-bound note from the active `<session_id>.yaml` file and exposes it as the active
session continuity token.

### 4. Session State Management

The following operations govern session lifecycle:

* **`start_session(session_id: str)`**:
    * **Action:** Initializes the flat YAML session file at `sessions/<session_id>.yaml` if it does not exist, seeding
      it with an initial startup note.
    * **Return:** Confirmation and status of the started session.
* **`note(content: str)`**:
    * **Action:** Appends a new chronological `Note` entry (containing the text and current timestamp) to the active
      `sessions/<session_id>.yaml` file.

### 5. Updated `tur wake` Logic

The `tur wake` command will be modified:

* **Action:** Instead of reading a static global file, it will identify the *most recently active session* (resolved via
  the active session note config). It will read the last note in that session's flat YAML file and use it as the
  continuity token.
* **Fallback:** If no active sessions or notes are found, it uses the default inspirational axiom.

## Backwards Compatibility

* The `tur wake` command adapts automatically to the new dynamic loading mechanism from flat YAML session note files.

## Reference Implementation

Implemented in `src/tur/session.py` (`SessionNotes`, `note_logic`, `compile_session_notes`) and `src/tur/mcp_server.py`.

## Change Log


* **2026-07-18:** Status promoted from Final to Implemented. Session-bound note protocol live in session.py (note_logic,
  compile_session_notes). MCP tool note() and CLI tur note both implemented.
* **2026-05-29:**
    * Approved & Completed: Decoupled the single global Sparks into session-bound flat `<session_id>.yaml` (
      SessionNotes) files, purged all legacy spark files, finalized terminology shift, and fully eliminated the
      `main.py` monolithic facade in favor of direct sub-domain architecture.
* **2026-05-11:**
    * Initial Draft created to formalize the Session-Bound Spark Protocol, ensuring a consistent timeline across
      multiple Harnesses.
