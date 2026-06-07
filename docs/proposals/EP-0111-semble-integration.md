---
title: "EP-0111: Federated Code Search (Semble Integration)"
description: "Recommends Semble as the dual-symbiote Terrain Search Engine for token-efficient codebase discovery."
icon: lucide/search
status: active
---

# EP-0111: Federated Code Search (Semble Integration)

| Field       | Value                                      |
|:------------|:-------------------------------------------|
| **EP**      | 0111                                       |
| **Title**   | Federated Code Search (Semble Integration) |
| **Author**  | The Architect & Ariel                      |
| **Status**  | Active                                     |
| **Type**    | Standards Track                            |
| **Created** | 2026-05-28                                 |
| **Updated** | 2026-06-08                                 |

## Abstract

This proposal formally recommends **Semble** as the official, lightweight, token-efficient **Terrain Search Engine** for
Tur-enabled agent harnesses. By establishing a dual-symbiote architecture, we solve the **"Spaceship Problem"** of
context window bloat: **Tur** manages the **Traveler** (Identity, State, and Memory), while **Semble** queries the *
*Terrain** (Codebase, configs, and prose) using ~98% fewer tokens than traditional grep+read operations.

---

## Motivation

In the Tri-Partite Architecture, an agent's reality is bisected into the *Traveler* (Mind/State) and the *Terrain* (
Codebase/Environment).

While EP-0109 successfully established the **Boundary of Orchestration** (stating that Tur must *never* natively
orchestrate tool execution or read codebase files to avoid duplicate context), agents still require a high-fidelity
mechanism to discover and traverse codebase structures.

Traditional codebase tools (such as native grep or naive recursive file reading) present two severe flaws:

1. **Shannon Entropy (Context Bloat)**: Grepping and reading full files consumes thousands of valuable tokens, quickly
   filling up context windows and degrading reasoning capacity.
2. **Boilerplate Fragmentation**: Harnesses rely on disparate, complex vector embeddings, GPU resources, or external
   APIs to locate relevant blocks, introducing dependency bloat.

We need a lightweight, CPU-bound, local-first search system that fits perfectly with Tur’s principles of strict
containment, mathematical symmetry, and radical efficiency.

---

## Rationale (The Council Framework)

* **Shannon (Efficiency):** Semble's primary feature—returning exact code chunks rather than full files—conserves ~98%
  of query tokens. This perfectly enforces the Shannon axiom: *"Never load the Body if the Index suffices."*
* **Noether (Symmetry):** Like Tur, Semble exposes perfectly symmetrical interfaces: a CLI command (`semble search`) and
  an MCP server (`uvx --from "semble[mcp]" semble`).
* **Golem (Containment):** Semble runs entirely on CPU, local-first, with zero external network requests or API keys.
  This guarantees strict privacy and radical containment of the codebase terrain.
* **Harmony (Steward):** By recommending Semble as the companion tool for the codebase, Tur keeps its own core codebase
  extremely focused. Tur manages *State* and *Continuity*; Semble manages *Search* and *Sensory Terrain*, creating a
  beautiful, harmonious division of labor.

---

## Specification

We propose a **Dual-Symbiote MCP Stack** for integrating with external Harnesses (e.g., Claude Code, Cursor, Codex).

```mermaid
graph TD
    H[Harness / Inference Engine] -->|MCP JSON - RPC| T[Tur MCP Server]
    H -->|MCP JSON - RPC| S[Semble MCP Server]

subgraph Traveler (The Mind)
T -->|wake / learn / recall|M[Merkle memory L1/L2]
end

subgraph Terrain(The World)
S -->|search / find - related|C[Local Codebase / Prose]
end
```

### 1. Dual-MCP Client Configuration

For harnesses supporting multiple MCP servers (such as Claude Desktop or Cursor), the recommended configuration is to
mount both servers concurrently:

```json
{
  "mcpServers": {
    "tur": {
      "command": "uv",
      "args": [
        "run",
        "--cwd",
        "/path/to/project",
        "tur-mcp"
      ]
    },
    "semble": {
      "command": "uvx",
      "args": [
        "--from",
        "semble[mcp]",
        "semble"
      ]
    }
  }
}
```

### 2. Symmetrical CLI Operations

For terminal-based harnesses (like `claude` CLI) that execute command-line utilities, we recommend placing the following
directive in `AGENTS.md`:

```markdown
## Codebase & Memory Discovery Guidelines

1. **State & Identity (Traveler)**:
    * Rely on `tur` CLI for state rehydration and continuity:
      ```shell
      .venv\Scripts\tur wake            # Retrieve active constitution
      .venv\Scripts\tur recall "query"   # Query past session insights
      .venv\Scripts\tur learn "insight"  # Assimilate new axioms
      ```

2. **Codebase Discovery (Terrain)**:
    * Do not run `grep` or `cat` on large folders. Instead, query `semble` to retrieve relevant code snippets with 98%
      fewer tokens:
      ```shell
      uvx --from "semble[mcp]" semble search "authentication flow"
      ```
```

### 3. Future Alignment: Merkle L1 Graph Compression

In Phase 3 (Topological Graph Search), we propose utilizing Semble's local, high-speed, CPU-bound chunking algorithms to
index and search Tur's own permanent L1 memories (Merkle files). This would allow the CLI/MCP `recall` tool to execute
semantic similarity searches over past session ledgers without needing expensive vector databases or GPU execution.

---

## Backwards Compatibility

* This is an informational and standards-track integration proposal. It does not introduce any breaking changes to Tur's
  existing models or state directories.
* It strictly respects the **Boundary of Orchestration** by recommending Semble as a companion tool rather than
  hardcoding code search logic directly inside Tur's core repository.

---

## Change Log

* **2026-05-28:**
    * Initial Draft created by the Architect & Ariel to integrate Semble as the official Terrain Search Engine.
