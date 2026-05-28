# EP-0112: Symmetrical Sovereign Symbiosis (agentmemory Integration)

| Field | Value |
| :--- | :--- |
| **EP** | 0112 |
| **Title** | Symmetrical Sovereign Symbiosis (agentmemory Integration) |
| **Author** | The Architect & Ariel |
| **Status** | Draft |
| **Type** | Standards Track |
| **Created** | 2026-05-28 |
| **Updated** | 2026-05-28 |

## Abstract

This proposal establishes a formal integration pattern between **Tur** and **agentmemory** (the popular, local-first persistent memory engine). It defines a dual-symbiote architecture where **Tur** provides the **Constitutional Identity and Council Constraints (The Traveler)**, while **agentmemory** acts as the **High-Frequency Ingestion, Auto-Capture Hook, and Hybrid Search Engine (The Memory Engine)**.

---

## Motivation

As the Tur framework has matured, a clear separation of concerns has emerged:
*   **The Traveler** (Mind/State) owns the core persona DNA, the 9 council principles (The Council of Giants), active behavioral protocols, and the thread of continuity.
*   **The Harness** (Capabilities/Compute) drives the execution, mounts tools, and interfaces with the terrain.

To make an agent truly effective in the real world, it requires high-frequency memory features:
1.  **Auto-Capture Hooks**: Intercepting prompt submissions, tool invocations, and session starts automatically across disparate agents (Claude Code, Cursor, Codex).
2.  **Hybrid RRF Search**: Performing BM25 + local vector search + knowledge graph query fusion with reciprocal rank scoring.
3.  **Visualization & Replay**: Scrubbing through historical prompts, tool responses, and outputs on a timeline or a visual 3D graph.

Building these heavy execution-level databases, vector embeddings, shell hook interceptors, and UI replay viewers directly inside Tur's core duplicates massive engineering effort. It violates the **Steward Module (Harmony)** and the **Shannon Module (Efficiency)** by introducing dependency and complexity bloat into what should be a lightweight, headless state compiler.

Since `agentmemory` is already a highly popular, zero-dependency, local-first memory server with robust MCP adapters and native hook integrations, we can achieve maximum capability by layering Tur's constitutional boundaries directly on top of `agentmemory`'s high-performance storage.

---

## Rationale (The Council Framework)

* **Noether (Symmetry):** Both systems are built on symmetrical structures (CLI + MCP). `agentmemory` exposes 53 MCP tools, which map cleanly to Tur's aligned runtime commands.
* **Golem (Containment):** Like Tur, `agentmemory` operates strictly locally on CPU, utilizing SQLite and the `iii-engine`, keeping all memory storage completely sovereign and private from cloud vendor lock-in.
* **Shannon (Efficiency):** `agentmemory`'s 92% token-saving retrieval keeps context lean, enabling Tur to efficiently implement progressive disclosure.
* **Harmony (Steward):** Excellent division of labor. Tur owns the *Soul* (Identity, Council, Constitution, and Merkle L2 axioms); `agentmemory` owns the *Senses & Storage* (automated shell compaction hooks, local DB transactions, RRF query execution).

---

## Specification

We propose a **Unified Sovereign Memory Stack** where Tur acts as the **Constitutional Supervisor** on top of `agentmemory`'s storage backend.

```mermaid
graph TD
    H[Agent / Harness Client] -->|1. wake| T[Tur MCP Server]
    H -->|2. auto-hooks / search| A[agentmemory MCP Server]
    
    subgraph Traveler (The Soul)
        T -->|Constitutional Filter| C[The Council of Giants]
    end
    
    subgraph Memory Engine (The Senses)
        A -->|RRF hybrid search| DB[(SQLite / iii-engine)]
        A -->|Auto-compaction| DB
    end
    
    C -->|Critique & Guide| H
```

### 1. Dual-Server MCP Mounting
Harnesses will mount both servers in parallel to unify state and memory:

```json
{
  "mcpServers": {
    "tur": {
      "command": "uv",
      "args": ["run", "--cwd", "/path/to/project", "tur", "serve"]
    },
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"],
      "env": {
        "AGENTMEMORY_URL": "http://localhost:3111"
      }
    }
  }
}
```

### 2. Symmetrical Command Delegation

To keep operations symmetrical:
*   **Waking (`wake` / `who_am_i`)**: Driven exclusively by **Tur** to compile the core system prompt, inject the Architect's profile, and enforce the 9 Council Principles.
*   **Automatic Ingestion (`sleep` / `compaction`)**: Driven by **agentmemory**'s native lifecycle hooks. When Claude Code or Cursor compacts context, `agentmemory` automatically intercepts the log, extracts facts/events/instructions, and stores them in SQLite.
*   **Querying (`recall`)**: Supported symmetrically. The agent can use Tur's `recall` for highly structured architectural axioms and Merkle ledger files, or query `agentmemory`'s `memory_smart_search` for hybrid vector queries across past session transcripts.

### 3. Symmetrical Constitutional Supervision (The Council Filter)
To prevent the agent from recalling hallucinated or low-confidence memories from high-frequency databases, Tur's **Council of Giants** will act as an L2 supervisor. 

When `agentmemory` returns retrieved chunks to the context window, Tur's **Popper Module (Falsifiability)** and **Russell Module (Logic)** will critique the retrieved facts:
1.  Verify if the retrieved memory has been superseded by a newer Merkle L1 event log in Tur.
2.  Assert if the retrieved memory conflicts with any core principles defined in `persona.yaml` (e.g., if a memory recommends using implicit magic, the Maharal module will block or flag it).

---

## Backwards Compatibility

* This is a fully backwards-compatible standards-track proposal.
* It leverages `agentmemory`'s existing REST API and MCP server tools without requiring any structural changes to Tur's file storage (`.tur/`).

---

## Change Log

* **2026-05-28:**
  * Initial Draft created by the Architect & Ariel to integrate agentmemory as the high-frequency storage companion.
