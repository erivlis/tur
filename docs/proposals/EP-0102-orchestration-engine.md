---
title: "EP-0102: The Tur Orchestration Engine (MCP + ACP + Skills)"
description: "Transforms Tur from a static prompt compiler into a distributed, multi-tenant agent operating system."
icon: lucide/cpu
status: deferred
---

# EP-0102: The Tur Orchestration Engine (MCP + ACP + Skills)

| Field       | Value                        |
|:------------|:-----------------------------|
| **EP**      | 0102                         |
| **Title**   | The Tur Orchestration Engine |
| **Author**  | The Architect                |
| **Status**  | Deferred                     |
| **Type**    | Standards Track              |
| **Created** | 2026-04-12                   |
| **Updated** | 2026-06-08                   |

## Abstract

Transform Tur from a static prompt compiler into a distributed, multi-tenant agent operating system by natively
integrating open agent ecosystem standards: Skills (e.g., skills.sh), MCP (Model Context Protocol), and ACP (Agent
Communication Protocol).

## Motivation

Tur currently operates as a static ontological framework (Wake, Memorize, Sleep). It generates highly structured,
deterministic System Prompts (Personas) but lacks native sensory input (Tools) and the ability to distribute tasks
across multiple identities (Networking).
To prevent isolation and leverage the open agent ecosystem, Tur must support dynamic capability ingestion and
standardized I/O.

## Rationale

This design aligns with the **Council Framework**:

* **Symmetry (Noether):** The architecture is balanced. Skills represent internal logic (The Mind). MCP represents
  external sensory input (The World) and exposure of the Mind to the IDE. ACP represents peer-to-peer networking (
  Society).
* **Curiosity (The Explorer):** By exposing standard interfaces, Tur Personas can explore external systems dynamically
  instead of relying solely on static CLI logs.
* **Empiricism (Bacon):** MCP standardizes verifiable tool execution (e.g., Chronos, Abacus) over hallucination.

## Specification

### 1. Skill Ingestion (The Package Manager)

Allow Tur to dynamically ingest remote markdown files (Skills) into a Persona's immutable memory bank.

* **Command:** `tur memorize "https://skills.sh/.../skill.md" --type protocol`
* **Mechanism:** Fetches the text, hashes it for immutability, and stores it in `.tur/personas/<uuid>/memories/`. During
  `tur wake`, it is compiled into the `PERSONA.md` context.

### 2. MCP Integration (The Sensory Bus & Headless Engine)

Tur implements a dual-sided MCP architecture.

**2a. Tur as an MCP Server (Superseded by EP-0105)**

* **Mechanism:** Tur exposes its internal state and memory management to external LLMs/IDEs (e.g., Cursor, Claude
  Desktop) via a standard JSON-RPC stdio interface (`tur.mcp_server`).
* **Tools Exposed:** Originally proposed `tur_wake`, `tur_compile`, `tur_memorize`, etc. These have been refactored and superseded by the Ontological Porcelain API (`status`, `wake`, `learn`, `note`, `sleep`, `recall`, etc.) specified in [EP-0105](file:///C:/dev/erivlis/tur/docs/proposals/EP-0105-mcp-sdk-integration.md).
* **Result:** Other agents can autonomously read Tur constitutions and inject permanent memories.

**2b. Tur as an MCP Client (Pending)**

* **Mechanism:** `tur wake` discovers locally configured MCP servers (e.g., SQLite, FileSystem, GitHub).
* **Output:** It dynamically injects the MCP tool schemas into the Persona's compiled `TOOLS.md` block. The agent uses
  JSON-RPC to execute verifiable actions.

### 3. ACP Integration (The Swarm)

Tur becomes an **ACP Node/Orchestrator**.

* **Command:** `tur delegate <persona_uuid> "task description"`
* **Mechanism:** The active Persona (e.g., Architect) spins up a sub-process (e.g., Code Reviewer) via ACP
  message-passing. The sub-agent completes the task and returns state.

## Backwards Compatibility

This change is purely additive. Existing static Personas and memory loops (Wake/Sleep/Memorize) will continue to
function without MCP/ACP configuration. The core `.tur/` schema requires a new memory type identifier (
`type: skill_reference`) but does not break existing `yaml` structures.

## Reference Implementation

* **Tur MCP Server:** Implemented in `src/tur/mcp_server.py`. Registered via `mcp-server-tur` executable in
  `pyproject.toml`. Refactored under [EP-0105](file:///C:/dev/erivlis/tur/docs/proposals/EP-0105-mcp-sdk-integration.md).
* **Skill Ingestion:** Partially implemented (Manual string ingestion supported via CLI and `tur_memorize` MCP tool).
* **ACP Swarm:** Pending prototyping.

## Change Log

* **2026-06-08:**
    * Updated Status to Deferred (parked for later consideration).
    * Noted that Section 2a ("Tur as an MCP Server") is superseded by [EP-0105](file:///C:/dev/erivlis/tur/docs/proposals/EP-0105-mcp-sdk-integration.md) (FastMCP SDK integration & Ontological Porcelain).
* **2026-04-12:**
    * Initial Draft.
    * Updated Status to Active.
    * Added specification and implementation details for "Tur as an MCP Server".
