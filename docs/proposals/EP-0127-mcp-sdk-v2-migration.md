---
title: "EP-0127: Model Context Protocol Python SDK v2 Migration & Protocol Alignment"
description: "Migrates Tur's MCP server and harness integration layer to the official MCP Python SDK v2, aligning with the 2026 protocol specifications."
icon: lucide/cpu
status: draft
---

# EP-0127: Model Context Protocol Python SDK v2 Migration & Protocol Alignment

| Field       | Value                                                               |
|:------------|:--------------------------------------------------------------------|
| **EP**      | 0127                                                                |
| **Title**   | Model Context Protocol Python SDK v2 Migration & Protocol Alignment |
| **Author**  | Eran Rivlis & Ariel                                                 |
| **Status**  | Draft                                                               |
| **Type**    | Standards Track                                                     |
| **Created** | 2026-08-24                                                          |
| **Updated** | 2026-08-24                                                          |

## Abstract

This proposal specifies the architectural and technical migration of Tur's Model Context Protocol (MCP) server subsystem
from the legacy `mcp` v1.x SDK (`FastMCP`) to the official MCP Python SDK v2 (`MCPServer`) and the 2026 protocol
specifications. It establishes a modernized, type-safe interface for tool registration, lifecycle management, resource
exposure, and LLM-agnostic sampling interaction while shedding legacy protocol overhead and deprecated wire conventions.

## Motivation

Tur functions as an "Obligate Symbiote"—an external persistent memory and identity state engine for AI agent harnesses
(e.g., Claude Code, Gemini CLI, Cursor, OpenCode). Tur exposes its Ontological Porcelain (`status`, `wake`, `learn`,
`evolve`, `sleep`, `note`, `signal`, `read_whiteboard`) primarily via the Model Context Protocol.

With the release of the **MCP Python SDK v2** and the updated protocol specification (2026-07-28), several foundational
improvements and breaking changes have been introduced:

1. **`FastMCP` Deprecation & Replacement with `MCPServer`**: The high-level `FastMCP` class in `mcp.server.fastmcp` has
   been consolidated and rebuilt as `MCPServer` in `mcp.server`, moving transport binding and lifecycle initialization
   to `.run()`.
2. **Decoupled Wire Types (`mcp-types`) & `snake_case` Normalization**: Wire protocol models are extracted into a
   dedicated package (`mcp-types`) and strictly normalized to Pythonic `snake_case` fields, resolving serialization
   friction and impedance mismatches with Pydantic models.
3. **Refactored Sampling & Elicitation Protocols (`Resolve`)**: Interactive client-server round-trips are formalized
   under `Resolve`, and sampling interfaces have been streamlined.
4. **Transport Decoupling**: Transport parameters (stdio, SSE) are no longer passed into server constructors, enabling
   clean separation between server definition and transport instantiation.

Currently, Tur's `pyproject.toml` pins `mcp = ["mcp>=1.27,<2"]`, and `src/tur/mcp_server.py` relies on `FastMCP`. To
prevent ecosystem divergence, support cutting-edge agent harnesses, and prepare for reactive signal subscriptions
(EP-0123), Tur must migrate to MCP Python SDK v2.

## Rationale

### Council Alignment

* **The Noether Module (Symmetry & Invariance):** SDK v2 normalizes wire types and metadata into canonical
  `snake_case` schemas (`mcp-types`), preserving symmetrical data structures between internal models and external
  protocol envelopes.
* **The Shannon Module (Entropy & Efficiency):** Eliminating legacy handshake state, dead ping loops, and unnecessary
  adapter layers reduces transport noise and execution overhead during startup.
* **The Golem Protocol (Containment & Boundaries):** Transport configuration is isolated to invocation time (`.run()`),
  ensuring `mcp_server.py` remains a pure functional specification of tools and state resources, without binding to
  specific network sockets or I/O pipes at import time.
* **The Russell Module (Consistency & Logic):** Direct dependency on strictly-typed `MCPServer` and `mcp-types` replaces
  loose dict serialization with compile-time verified Pydantic v2 schemas.

## Specification

### 1. Dependency Updates (`pyproject.toml`)

Update the optional `mcp` dependency group to target SDK v2:

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=2.0.0,<3.0.0",
    "mcp-types>=0.1.0",
]
```

### 2. Server Definition (`src/tur/mcp_server.py`)

Migrate server instantiation from `FastMCP` to `MCPServer`:

```python
# Before (SDK v1):
# from mcp.server.fastmcp import Context, FastMCP
# mcp = FastMCP('tur-server', json_response=True, lifespan=server_lifespan)

# After (SDK v2):
from mcp.server import MCPServer
from mcp.server.lifespan import lifespan_context

mcp = MCPServer("tur-server", lifespan=server_lifespan)
```

Tool registrations retain decorator semantics (`@mcp.tool()`), returning structured Python native types or Pydantic
models automatically serialized via `mcp-types`.

### 3. Transport Lifecycle & CLI Host (`src/tur/cli/mcp.py`)

SDK v2 relocates transport execution logic to the `.run()` method:

```python
# Launching stdio transport in tur-mcp
import asyncio
from tur.mcp_server import mcp


def main() -> None:
    """Launch Tur MCP server over stdio transport."""
    asyncio.run(mcp.run(transport="stdio"))
```

### 4. Sampling & Elicitation Protocol Alignment

All sampling logic in `tur.dreaming` and `tur.introspection` operating via MCP context sampling will align with SDK v2's
updated sampling request schema and response objects:

- Update sampling payload structures to use snake_case field names (`max_tokens`, `system_prompt`, `messages`).
- Integrate with `Resolve` workflows where interactive agent confirmation is required during administrative operations.

### 5. Integration with Reactive Signals (EP-0123)

SDK v2 standardizes resource update notifications (`notifications/resources/updated`). This directly satisfies the
prerequisites for **EP-0123 (Reactive Signal Delivery)**, allowing `signal_logic` to notify subscribed harnesses via
`mcp.notify_resource_updated(f"tur://signals/{agent_id}")`.

## Backwards Compatibility

* **Harness Compatibility:** Host harnesses implementing MCP 2024-11-05 through 2026-07-28 remain compatible over stdio
  transports via standard JSON-RPC 2.0 message negotiation.
* **CLI Interoperability:** Human-facing `tur` and `tur-adm` CLIs do not depend on the `mcp` extra and are completely
  unaffected.
* **State Preservation:** No changes are made to `.tur/` directory storage, OKF markdown structures, or Merkle hash
  algorithms.

## How to Teach This / Documentation Plan

* Update `docs/concepts/harness-integration.md` to reflect `MCPServer` usage and v2 transport patterns.
* Update `AGENTS.md` and `TOOLS.md` if any MCP tool signatures or elicitation flows change.
* Update `docs/proposals/EP-0002-roadmap.md` to index EP-0127 under Phase 3 (Architecture, Interfaces & Security).

## Reference Implementation

A prototype branch migrating `mcp_server.py` to `MCPServer` and validating stdio compatibility with Claude Code and
Gemini CLI test suites.

## Rejected Ideas

* **Maintaining a Custom JSON-RPC Server:** Rejected. Writing a bespoke MCP protocol parser violates the Golem
  (Containment) and Shannon (Efficiency) principles by re-implementing transport mechanics already maintained by the
  official SDK.
* **Dual-SDK Support (`mcp` v1 and v2 via runtime checks):** Rejected. Dual-version compatibility creates conditional
  import branching and fragile typing shims. Clean cutover to v2 is preferred.

## Open Questions

- [ ] Verify if all targeted agent harnesses (Claude Code, Gemini CLI, Cursor) have published v2-compatible client
  transports.
- [ ] Confirm exact `lifespan` context manager signature changes across minor releases of SDK v2.

## Change Log

* **2026-08-24:**
    * Initial Draft formulated to migrate Tur's MCP subsystem to MCP Python SDK v2 and align with the 2026 protocol
      specifications.
