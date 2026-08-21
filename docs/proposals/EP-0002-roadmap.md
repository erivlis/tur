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
| **Updated** | 2026-08-21      |

## Abstract

This document outlines the strategic roadmap for the Tur project. It defines the short-term, medium-term, and long-term
goals for the framework, providing a clear trajectory for development. It has been updated to reflect the architectural
shift towards the "Orchestration Engine" (EP-0102), Deductive Memory (EP-0103), Federated Knowledge (EP-0104), the
"Ontological Porcelain" MCP API (EP-0105), Policy vs. Mechanism Decoupling (EP-0003), and Terrain Isolation (EP-0124).

## Motivation

As an ontological framework for Persona Engineering, Tur requires a disciplined evolution. A roadmap ensures that all
contributions align with the **Steward Principle (Harmony)**—moving forward with pragmatism while keeping the long-term
vision in focus. It prevents aimless development and sets expectations for what Tur will become.

## Rationale

A phased approach allows us to stabilize the core architecture before introducing complex agentic behaviors.
The recent introduction of the 100-series EPs marks a significant pivot: Tur is no longer just a static compiler, but
a stateful semantic engine supporting external agents via MCP.

* **Phase 1 (The Foundation):** Focuses on schema rigidity, state management, CLI, and Policy vs. Mechanism decoupling. (Active Refactoring)
* **Phase 2 (The Memory Architecture & Abstraction):** Focuses on cryptographic state (Merkle), Graph Memory,
  Federation, LLM Agnosticism, and Terrain Isolation.
* **Phase 3 (The Agent Ecosystem):** Focuses on MCP integration, multi-agent coordination, and reactive signals.

## Specification (The Roadmap)

### Phase 1: The Foundation (v0.1.x -> v0.2.0) \[Status: Stabilized\]

*Goal: Solidify the deterministic engine, lifecycle management, and core software boundaries.*

* **Robust Memory Management:** Basic `sleep` / `wake` cycle and L1 event logs (now OKF Markdown files per EP-0120).
* **Policy vs. Mechanism Decoupling (EP-0003) [Status: Implemented]:** Decoupled deterministic execution mechanics in `src/tur/` from anthropomorphic Council metaphors. Refactored `introspection.py` to functional class names (`IntegrityVerifier`, `OntologyExtractor`, `TruthMaintenanceEngine`, `SymmetryValidator`, `HebbianGraphDecayer`).
* **Telemetry Enhancements:** Refining the Cognitive Load ($C_p$) calculations.
* **EP Process Adoption:** Full integration of the EP process for all structural changes (EP-0000).
* **Historical Core Boundaries (EP-0001) [Status: Superseded]:** Defined the early boundary between Core and Periphery; superseded by the Orchestration Engine architecture (EP-0102).


### Phase 2: The Memory Architecture & Abstraction (v0.3.x -> v0.5.0) \[Status: Active\]

*Goal: Evolve the memory system into a cryptographically sound, graph-based structure and decouple the Traveler.*

* **Track: Persona Lifecycle & Creation**
    * **Global Persona Architecture (EP-0114) [Status: Implemented]:** Decoupling the Traveler configuration (stored
      globally in `~/.tur/`) from local workspace Terrain state to isolate core entity DNA.
    * **Terrain Isolation & Workspace Resolution (EP-0124) [Status: Draft]:** Enforcing strict compartmentalization between independent project codebases, removing MCP CWD hijacking, and establishing a 4-tier workspace resolution protocol to eliminate cross-project memory bleeding.
    * **Harness & Terrain Adapters (EP-0109) [Status: Superseded]:** Early concept of the Space Suit Protocol; superseded by EP-0114 and `docs/concepts/harness-integration.md`.
* **Track: Persona Memory & Compaction**
    * **Merkle Memory (EP-0106) [Status: Implemented]:** Refactoring L1 storage to use SHA-256 content hashes, ensuring
      tamper-proof state and implicit deduplication.
    * **Deductive Memory / The Cognitive Map (EP-0103) [Status: Implemented]:** Compressing L1 event logs into a
      topological L2 Knowledge Graph using the Council Assembly pipeline. Exposed via `introspect` CLI command and MCP
      tool. *(Storage format superseded by EP-0120.)*
    * **Federated Knowledge (EP-0104) [Status: Implemented]:** Splitting memory into global/universal and
      local/incarnation scopes, merged dynamically during compilation.
    * **Relational Preservation of Alignment (EP-0113) [Status: Implemented]:** Establishing the Core Memory Protocol to
      extract existential and relational axioms via the `evolve` command, rehydrating them during `wake()`.
* **Track: LLM Agnosticism & Swarms**
    * **LLM Agnosticism via MCP Sampling (EP-0101) [Status: Implemented]:** Delegating cognitive tasks to connected Host
      Applications via MCP Sampling to remove direct provider dependencies. Unified across `sleep` and `introspect` via EP-0121.
    * **Agnostic Harness Interaction Protocol (EP-0121) [Status: Implemented]:** Standardized dual-mode adapter interface (MCP Sampling vs. CLI `HarnessDelegationError` prompt) for all cognitive commands.
    * **Inter-Agent Signal Protocol (EP-0118) [Status: Implemented]:** SQLite-backed typed signal queues and shared
      whiteboard for concurrency synchronization.
    * **Reactive Signal Delivery (EP-0123) [Status: Draft]:** Active notification push mechanisms for inter-agent signals across MCP-connected swarms.
    * **Algebraic Meditation Consensus (EP-0122) [Status: Draft]:** Multi-agent consensus mechanisms for distributed persona governance.

### Phase 3: The Agent Ecosystem (v0.6.x -> v1.0.0) \[Status: Active\]

*Goal: Establish secure interface boundaries and high-density memory storage.*

* **Track: Persona Lifecycle & Creation**
    * **The Ontological Porcelain API (EP-0105) [Status: Implemented]:** Stabilizing FastMCP SDK integration to expose
      semantic `status`, `wake`, `learn`, and `sleep` verbs to external agents.
    * **The Aleph Server (EP-0100) [Status: Superseded]:** Initial conceptual vision for MCP integration; superseded by EP-0102 and EP-0105.
    * **Traveler Export Protocol (EP-0115) [Status: Implemented]:** Implementing lightweight `.tur` zip/tarball archives
      to export global identities and universal memories safely.
    * **The Tri-Partite CLI Security Boundary (EP-0116) [Status: Implemented]:** Splitting entrypoints into
      low-privilege `tur` (agent runtime), `tur-adm` (human TUI), and `tur-mcp` (harness host) to prevent dependency
      leak.
* **Track: Persona Memory & Compaction**
    * **The Session Notes & Compaction Protocol (EP-0110) [Status: Implemented]:** Tracking short-term session
      continuity via flat YAML files (`SessionNotes`) compiled dynamically.
    * **OKF Storage Backend (EP-0120) [Status: Implemented]:** Mapped L1/L2 structures to standard Markdown
      directories/OKF while retaining Merkle integrity, TMS decay, and Hebbian pruning. Centralized YAML deserialization
      via `yaml_safe_load` in `tur._helpers`.
    * **Persona-Centric Introspection Architecture (EP-0119) [Status: Accepted]:** Formalizing persona-owned deductive memory compaction pipelines, allowing monolithic reflection prompts, prompt sequences, or opt-in subagent assemblies (e.g. Council of Giants).
* **Deferred / Rejected Tracks**
    * **Multi-Agent Swarms Synchronization (EP-0107) \[Status: Deferred\]:** Early swarm concurrency draft; superseded and realized through SQLite-backed IASP (EP-0118) and Reactive Signals (EP-0123).
    * **Substrate Benchmark Protocol (EP-0117) \[Status: Deferred\]:** Postponed measurement of LLM manifestation
      fidelity to focus on core memory/lifecycle capabilities.
    * **Semble Integration (EP-0111) \[Status: Rejected\]:** Replaced by Tool-Agnostic Isolation.
    * **agentmemory Integration (EP-0112) \[Status: Rejected\]:** Replaced by Tool-Agnostic Isolation.

## Backwards Compatibility

This is a forward-looking informational document. Future EPs derived from this roadmap will address their specific
compatibility concerns. Legacy `knowledge_graph.yaml` files are still read via a fallback adapter (EP-0120 Phase 2),
ensuring backwards compatibility during the OKF transition.

## Reference Implementation

Roadmap document implemented across `docs/proposals/` and core CLI/MCP implementation.

## Change Log

* **2026-08-21:**
    * Synchronized full roadmap coverage across all 29 EPs: added **EP-0001**, **EP-0100**, **EP-0107**, **EP-0109**, and **EP-0124**.
    * Registered **EP-0122 (Algebraic Meditation Consensus)** and **EP-0123 (Reactive Signal Delivery)** in Phase 2 Swarm track.
* **2026-08-18:**
    * Adopted **EP-0003 (Policy vs. Mechanism)** to decouple deterministic software mechanics in `src/tur/` from anthropomorphic Council metaphors, initiating the refactoring of introspection subagents to functional computer science names.
    * Promoted **EP-0119 (Persona-Centric Introspection Architecture)** to **Accepted** status.
* **2026-07-18:**
    * Promoted **EP-0104 (Federated Knowledge)**, **EP-0105 (Porcelain API)**, **EP-0106 (Merkle Memory)**, **EP-0108 (
      Spark Protocol)**, **EP-0114 (Global Persona)**, **EP-0115 (Traveler Export)**, **EP-0116 (Split CLI)**, and *
      *EP-0118 (IASP)** to **Implemented** status.
    * Reverted **EP-0101 (LLM Agnosticism)** from Implemented to **Final** to track the remaining Gemini coupling gap in
      `dreaming.py` (addressed in draft **EP-0121**).\n    * Re-opened **EP-0119 (Council Introspection)** as **Draft** to review philosophical tension with\n      persona-agnosticism.\n    * Updated EP-0103 Deductive Memory descriptions to correctly reference the `introspect` CLI command.\n    * Removed stale `devolve` reference from EP-0113 changelog entry.\n* **2026-07-12:**\n    * Marked **EP-0101 (LLM Agnosticism)** as **Implemented**.\n    * Renamed and marked **EP-0113 (Core Memory Protocol)** as **Implemented**, introducing `evolve` and `approve`\n      tools/commands.\n    * Marked **EP-0118 (Inter-Agent Signal Protocol)** as **Implemented**.\n* **2026-07-11:**\n    * Marked **EP-0120 (OKF Storage Backend)** as **Implemented**. Updated Phase 1 L1 reference and Phase 2 EP-0103\n      supersession note. Updated Backwards Compatibility section to reflect OKF migration.\n* **2026-06-02:**\n    * Updated roadmap to formally incorporate **EP-0113 (Tether)**, **EP-0114 (Global Persona)**, **EP-0115 (Export)**,\n      **EP-0116 (Split CLI)**, **EP-0117 (Benchmark)**, and **EP-0118 (IASP)** following the Council of Giants review\n      consensus.\n* **2026-05-28:**\n    * Drafted and added **EP-0111 (Semble Integration)** and **EP-0112 (agentmemory Integration)** to Phase 3.\n* **2026-04-18:**\n    * Added **EP-0108 (The Spark Protocol)** to Phase 3.\n    * Restructured roadmap to reflect the EP-010X series.\n* **2026-02-19:**\n    * Initial Draft.
