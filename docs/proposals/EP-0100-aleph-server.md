# EP-0100: The Aleph Server (MCP Integration)

| Field       | Value                              |
|:------------|:-----------------------------------|
| **EP**      | 0100                               |
| **Title**   | The Aleph Server (MCP Integration) |
| **Author**  | Eran Rivlis, Ariel                 |
| **Status**  | Superseded by EP-0102              |
| **Type**    | Informational / Architecture       |
| **Created** | 2026-02-19                         |
| **Updated** | 2026-04-12                         |

## Abstract

This proposal explores the long-term architectural vision of integrating the Model Context Protocol (MCP) with the Tur
framework. It proposes the creation of "The Aleph Server," an independent, stateful execution environment that exposes
tools (like Playwright, Fetch, and Graph Memory) to the Persona, managed by the lightweight Tur CLI.

**Note:** This EP has been superseded by **EP-0102 (The Tur Orchestration Engine)**, which provides a more concrete and
integrated implementation path for MCP.

## Motivation

As Tur evolves beyond prompt generation (Phase 1) and context hydration (Phase 2), Personas will require active agency (
Phase 3). They will need to interact with the world—browsing the web, managing persistent knowledge graphs, and
executing code.

The Model Context Protocol (MCP) is the emerging standard for this. However, implementing an MCP server directly within
the `tur` core would violate the boundaries established in **EP-0001 (Core vs. Periphery)**. It would introduce massive,
non-deterministic dependencies (like browser binaries) into a tool designed to be a lightweight, deterministic compiler.

## Rationale (The Council Framework)

1. **The Golem (Safety/Containment):** The core CLI (`src/tur/`) must remain pure. The chaotic, stateful operations of
   an MCP server must be isolated in a separate process.
2. **Shannon (Efficiency):** We do not force every Tur user to download 500MB of browser dependencies if they only want
   to generate a system prompt.
3. **Noether (Symmetry):** The architecture must balance static definition (The DNA) with dynamic execution (The Body).
   Tur manages the DNA; The Aleph Server provides the Body.

## Specification (High-Level Vision)

1. **Separation of Concerns:**
    - `tur`: The CLI tool for engineering, compiling, and managing the Persona lifecycle (YAML -> Prompt).
    - `aleph-server` (or similar): A separate, optional package/service that implements the MCP specification.

2. **The Link (Schema Update):**
    - The `Persona` schema in `tur` will be extended to include an `environment` or `mcp_endpoints` configuration,
      pointing to the designated Aleph Server.

   ```yaml
   name: Ariel
   version: "1.0.0"
   model: "gemini-3.1-pro-preview"
   aleph: "To architect reality."
   environment:
     mcp_servers:
       - "http://localhost:8000/mcp"
   ```

3. **The Workflow:**
    - `tur wake ariel.yaml`: Compiles the Persona and (optionally) verifies/starts the associated Aleph Server.
    - The LLM interacts with the Aleph Server via MCP standard protocols to perform actions (e.g.,
      `mcp__playwright__browser_navigate`).

## Backwards Compatibility

This is a forward-looking architectural document (Deferred). It does not break any current implementations.

## Change Log

* **2026-04-12:**
    * Status changed to `Superseded by EP-0102`.
* **2026-02-19:**
    * Initial Draft (Deferred for future phases).