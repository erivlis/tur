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

* **LLM Agnosticism (EP-0101):** Standardizing on `pydantic-ai` as the core interface for all non-agentic structural tasks (e.g., `sleep`, `meditate`). *(Superseded by Symbiotic Paradigm)*
* **Merkle Memory (EP-0106):** Refactoring the L1 storage to use SHA-256 content hashes instead of UUIDs, ensuring tamper-proof state and implicit deduplication.
* **Deductive Memory / The Cognitive Map (EP-0103):** Implementing the `tur meditate` loop to compress L1 event logs into a topological L2 Knowledge Graph using `networkx` and LLM-based triple extraction.
* **Federated Knowledge (EP-0104):** Splitting the knowledge graph into two tiers: The "Soul" (Universal/Global config) and The "Mind" (Project-Specific/Local config), merged dynamically during compilation.

### Phase 3: The Agent Ecosystem (v0.6.x -> v1.0.0)

*Goal: Transform Tur into the central Orchestration Engine for external LLMs via MCP and ACP.*

* **The Ontological Porcelain API (EP-0105):** Stabilizing the `mcp.server.fastmcp` SDK integration. Exposing the semantic `who_am_i`, `learn`, and `recall` verbs to external agents.
* **The Spark Protocol (EP-0108):** Deprecating the static "Epilogue" in favor of a high-frequency, mutable `spark.md` file. Adding the `update_spark` MCP tool to allow an active Agent to continuously record its train of thought, ensuring perfect state resumption upon waking/crashing.
* **Semantic Graph Queries:** Upgrading the MCP `recall` tool to traverse the EP-0103 L2 Knowledge Graph rather than just grepping L1 event logs.
* **The Tur Orchestration Engine (EP-0102):** Full realization of the "Swarm" capability. Allowing the Architect Persona to dynamically spawn sub-agents via ACP message passing to execute specific, containerized tasks based on Skill definitions.
* **Multi-Agent Swarm Readiness (EP-0107):** Hardening the memory bank for concurrent access and implementing MCP Resource Subscriptions (`tur://active_constitution`) to proactively synchronize state across multiple agents without triggering context overload.
* **Semble Integration (EP-0111):** Establishing a dual-symbiote architecture recommending Semble as the high-efficiency Terrain search engine to manage codebase query discovery with ~98% fewer tokens.
* **agentmemory Integration (EP-0112):** Establishing a dual-symbiote architecture where Tur provides the Constitutional Identity (Traveler) and agentmemory serves as the high-frequency local memory capture and hybrid search engine.
* **Internal Arbitration:** Implementing mechanisms where the 9 Pillars (Noether, Popper, etc.) can programmatically critique the model's output *before* it reaches the user.

## Backwards Compatibility

This is a forward-looking informational document. Future EPs derived from this roadmap will address their specific compatibility concerns (e.g., the `tur migrate --merkle` command required for EP-0106).

## Change Log

* **2026-05-28:**
    * Drafted and added **EP-0111 (Semble Integration)** and **EP-0112 (agentmemory Integration)** to Phase 3.
    * Refined roadmap to reflect local, CPU-bound federated terrain discovery and high-frequency local-first memory integration.
* **2026-04-18:**
    * Added **EP-0108 (The Spark Protocol)** to Phase 3.
    * Restructured roadmap to reflect the EP-010X series.
    * Re-focused Phase 2 on Memory Architecture (Merkle, Graph, Federation) and `pydantic-ai`.
    * Re-focused Phase 3 on the Agent Ecosystem (MCP Ontological API, ACP Swarms, EP-0107 Concurrency).
    * Updated Status to Active.
* **2026-02-19:**
    * Initial Draft.