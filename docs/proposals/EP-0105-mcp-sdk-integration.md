# EP-0105: MCP SDK Integration & The Ontological Porcelain

| Field       | Value                                           |
|:------------|:------------------------------------------------|
| **EP**      | 0105                                            |
| **Title**   | MCP SDK Integration & The Ontological Porcelain |
| **Author**  | The Architect                                   |
| **Status**  | Active                                          |
| **Type**    | Standards Track                                 |
| **Created** | 2026-04-13                                      |
| **Updated** | 2026-04-18                                      |

## Abstract

This proposal mandates the refactoring of the existing `mcp_server.py` to use the official `mcp` Python SDK.
Concurrently, it redefines the MCP tool surface area to adhere to an "Ontological Porcelain vs. Structural Plumbing"
architecture. The MCP server will expose a minimal, high-level, semantic API (`who_am_i`, `learn`, `recall`) designed
for an LLM Agent's native cognition, leaving the low-level, literal CRUD operations (`tur wake`, `tur compile`,
`tur delete`) to the human-facing CLI.

## Motivation

Our current MCP server manually implements JSON-RPC over stdio and directly mirrors the CLI commands (e.g., `tur_wake`,
`tur_compile`, `tur_forget`).

This creates two fundamental problems:

1. **Fragility:** The hand-rolled JSON-RPC lacks robust error handling, transport negotiation, and capabilities
   discovery.
2. **Asymmetry of Audience:** We have traditionally viewed the CLI as the high-level "Porcelain" and the API as the
   low-level "Plumbing". However, in Persona Engineering, the consumer of the API is an LLM (an Agent), whose native
   interface *is* semantic and ontological. By exposing crude database operations (`list_memories`) to a cognitive
   entity, we break the illusion of identity.

By adopting the official `mcp` SDK and adopting an Ontological API, we gain robustness and a profound structural shift:
the MCP server becomes the semantic "Mind" (Porcelain) for the Agent, while the CLI remains the literal "Scalpel" (
Plumbing) for the Architect.

## Rationale (The Council Framework)

* **The Explorer (Structural Novelty):** We invert the standard developer paradigm. The Machine (LLM) gets the poetic,
  high-level interface; the Human (Architect) gets the literal, low-level interface.
* **The Steward (Harmony/Pragmatism):** We replace a brittle custom implementation with a standard, community-supported
  library (`mcp`).
* **Efficiency (Shannon):** The API is reduced to the absolute minimum verbs required for an agent to traverse its own
  state.
* **Containment (The Golem):** Destructive actions (`forget`) and identity shifts (`switch`) are removed from the
  machine interface, ensuring the Persona's core DNA cannot be accidentally deleted by an external LLM.

## Specification

### 1. Dependency Change

Add `mcp` to the `dependencies` in `pyproject.toml`.

### 2. The Ontological API (MCP Tool Redesign)

The `src/tur/mcp_server.py` file will be rewritten using `mcp.server.fastmcp.FastMCP` and expose *only* the following
tightly-scoped, semantic tools:

**A. `who_am_i()`**

* **Purpose:** The primary existential read operation for an agent.
* **Action:** Compiles and returns the active `PERSONA.md` string (including telemetry metadata).
* **Replaces:** `tur_wake`, `tur_compile`, `tur_telemetry`.

**B. `learn(content: str, type: str)`**

* **Purpose:** The primary cognitive write operation for an agent.
* **Action:** Assimilates an immutable L1 memory to the active persona. `type` is strictly validated against
  `MemoryType` enums (`fact`, `preference`, `axiom`, `insight`, `event`).
* **Replaces:** `tur_memorize` (tightened schema).

**C. `recall(query: str)`**

* **Purpose:** The primary cognitive exploration operation for an agent.
* **Action:** Searches the deep memory bank for relevant invariants (and eventually hooks into the EP-0103 Deductive
  Memory Graph).
* **Replaces:** `tur_list_memories`.

### 3. Structural Plumbing (The CLI)

The following tools will be removed from the MCP server entirely, remaining accessible only via the CLI (Plumbing) for
architectural intervention:

* `tur_forget` (Safety risk for an agent).
* `tur_list_personas` (Context irrelevance for a single-task agent).
* `tur_wake` / `tur_compile` / `tur_telemetry` (Merged into the semantic `who_am_i`).

## Backwards Compatibility

* **Breaking Change for MCP Clients:** Any external agent or IDE integration currently relying on the old `tur_*` tools
  must be updated to call the new ontological verbs.
* The core `.tur/` schema and the `tur` CLI commands remain completely unchanged.

## Change Log

* **2026-04-18:**
    * Revised to include the Ontological Porcelain API redesign, tightening the exposed tools to `who_am_i`, `learn`,
      and `recall` based on the Architect's paradigm inversion. Status updated to Active.
* **2026-04-13:**
    * Initial Draft (SDK Integration).