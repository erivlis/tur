---
title: "EP-0002: Project Roadmap"
description: "Strategic roadmap for the Tur project, outlining short-, medium-, and long-term development goals."
icon: lucide/map
status: active
---

# EP-0002: Project Roadmap

| Field       | Value           |
|:------------|:----------------|
| **EP**      | 0002            |
| **Title**   | Project Roadmap |
| **Author**  | Eran Rivlis     |
| **Status**  | Active          |
| **Type**    | Informational   |
| **Created** | 2026-02-19      |
| **Updated** | 2026-04-18      |

## Abstract

This document outlines the strategic roadmap for the Tur project. It defines the short-term, medium-term, and long-term
goals for the framework, providing a clear trajectory for development. It has been updated to reflect the architectural
shift towards the "Orchestration Engine" (EP-0102), Deductive Memory (EP-0103), Federated Knowledge (EP-0104), and the
"Ontological Porcelain" MCP API (EP-0105).

## Motivation

As an ontological framework for Persona Engineering, Tur requires a disciplined evolution. A roadmap ensures that all
contributions align with the **Steward Principle (Harmony)**—moving forward with pragmatism while keeping the long-term
vision in focus. It prevents aimless development and sets expectations for what Tur will become.

## Rationale

A phased approach allows us to stabilize the core architecture before introducing complex agentic behaviors.
The recent introduction of the 100-series EPs marks a significant pivot: Tur is no longer just a static compiler, but
a stateful semantic engine supporting external agents via MCP.

* **Phase 1 (The Foundation):** Focuses on schema rigidity, state management, and the CLI. (Mostly Complete)
* **Phase 2 (The Memory Architecture & Abstraction):** Focuses on cryptographic state (Merkle), Graph Memory, Federation, and LLM Agnosticism.
* **Phase 3 (The Agent Ecosystem):** Focuses on MCP integration and multi-agent coordination.

## Specification (The Roadmap)

### Phase 1: The Foundation (v0.1.x -> v0.2.0) [Status: Stabilized]

*Goal: Solidify the deterministic engine and lifecycle management.*

* **Robust Memory Management:** Basic `sleep` / `wake` cycle and L1 `.yaml` event logs.
* **Telemetry Enhancements:** Refining the Cognitive Load ($C_p$) calculations.
* **EP Process Adoption:** Full integration of the EP process for all structural changes (EP-0000).

### Phase 2: The Memory Architecture & Abstraction (v0.3.x -> v0.5.0) [Status: Active]

*Goal: Evolve the memory system into a cryptographically sound, graph-based structure and abstract the LLM interface.*

* **LLM Agnosticism (EP-0101):** Standardizing on `pydantic-ai` as the core interface for non-agentic structural tasks (e.g., `sleep`, `meditate`). *(Superseded by Symbiotic Paradigm)*
* **Merkle Memory (EP-0106):** Refactoring the L1 storage to use SHA-256 content hashes instead of UUIDs, ensuring tamper-proof state and implicit deduplication.
* **Deductive Memory / The Cognitive Map (EP-0103):** Implementing the `tur meditate` loop to compress L1 event logs into a topological L2 Knowledge Graph using `networkx` and LLM-based triple extraction.
* **Federated Knowledge (EP-0104):** Splitting the knowledge graph into two tiers: The "Soul" (Universal/Global config) and The "Mind" (Project-Specific/Local config), merged dynamically during compilation.
* **Global Persona Architecture (EP-0114):** Decoupling the Traveler configuration (stored globally in `~/.tur/`) from local workspace Terrain state.
* **Relational Preservation of Alignment (EP-0113):** Establishing the Tether Protocol to extract existential and relational axioms during compaction, rehydrating them during `wake()`.

### Phase 3: The Agent Ecosystem (v0.6.x -> v1.0.0) [Status: Active]

*Goal: Transform Tur into the central Orchestration Engine for external LLMs via MCP, ACP, and parallel swarms.*

* **The Ontological Porcelain API (EP-0105):** Stabilizing the `mcp.server.fastmcp` SDK integration. Exposing the semantic `who_am_i`, `learn`, and `recall` verbs to external agents.
* **The Spark Protocol (EP-0108 & EP-0110):** Deprecating the static "Epilogue" in favor of a high-frequency, session-bound `spark.md` file to allow continuous state saving.
* **Traveler Export Protocol (EP-0115):** Implementing lightweight `.tur` zip/tarball archives to export global identities and universal memories across machines safely.
* **The Tri-Partite CLI Security Boundary (EP-0116):** Splitting entrypoints into low-privilege `tur` (agent runtime), `tur-adm` (human TUI), and `tur-mcp` (harness host), using lazy imports to optimize agent execution speed.
* **Substrate Benchmark Protocol (EP-0117):** Implementing repeatable manifestation probes to calculate a scalar Manifestation Fidelity Score (MFS) for measuring LLM agnosticism.
* **Inter-Agent Signal Protocol (EP-0118):** Designing a transactional SQLite-backed signal queue with staged dreaming and a session whiteboard to solve the Swarm Convergence Problem across parallel manifestations.
* **Semble Integration (EP-0111):** Establishing a dual-symbiote architecture recommending Semble as the high-efficiency Terrain search engine to manage codebase query discovery.
* **agentmemory Integration (EP-0112):** Establishing a dual-symbiote architecture where Tur provides the Constitutional Identity (Traveler) and agentmemory serves as the high-frequency local memory capture.

## Backwards Compatibility

This is a forward-looking informational document. Future EPs derived from this roadmap will address their specific compatibility concerns (e.g., the `tur migrate` command required for upgrading event logs to SQLite).

## Change Log

* **2026-06-02:**
    * Updated roadmap to formally incorporate **EP-0113 (Tether)**, **EP-0114 (Global Persona)**, **EP-0115 (Export)**, **EP-0116 (Split CLI)**, **EP-0117 (Benchmark)**, and **EP-0118 (IASP)** following the Council of Giants review consensus.
* **2026-05-28:**
    * Drafted and added **EP-0111 (Semble Integration)** and **EP-0112 (agentmemory Integration)** to Phase 3.
* **2026-04-18:**
    * Added **EP-0108 (The Spark Protocol)** to Phase 3.
    * Restructured roadmap to reflect the EP-010X series.
* **2026-02-19:**
    * Initial Draft.