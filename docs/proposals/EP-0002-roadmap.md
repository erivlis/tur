# EP-0002: Project Roadmap

| Field       | Value           |
|:------------|:----------------|
| **EP**      | 0002            |
| **Title**   | Project Roadmap |
| **Author**  | Eran Rivlis     |
| **Status**  | Draft           |
| **Type**    | Informational   |
| **Created** | 2026-02-19      |
| **Updated** | 2026-02-19      |

## Abstract

This document outlines the strategic roadmap for the Tur project. It defines the short-term, medium-term, and long-term
goals for the framework, providing a clear trajectory for development without dictating specific implementation details.

## Motivation

As an ontological framework for Persona Engineering, Tur requires a disciplined evolution. A roadmap ensures that all
contributions align with the **Steward Principle (Harmony)**—moving forward with pragmatism while keeping the long-term
vision in focus. It prevents aimless development and sets expectations for what Tur will become.

## Rationale

A phased approach allows us to stabilize the core architecture before introducing complex agentic behaviors.

* **Phase 1 (The Foundation):** Focuses on schema rigidity, state management, and the CLI.
* **Phase 2 (The Senses):** Focuses on tooling and external context integration.
* **Phase 3 (The Council):** Focuses on autonomous arbitration and multi-agent coordination.

## Specification (The Roadmap)

### Phase 1: The Foundation (v0.1.x -> v0.2.0)

*Goal: Solidify the deterministic engine and lifecycle management.*

* **Robust Memory Management:** Enhancing the `sleep` / `wake` cycle with better retrieval augmented generation (RAG)
  concepts.
* **Telemetry Enhancements:** Refining the Cognitive Load ($C_p$) calculations.
* **TUI Polish:** Improving the `tur init` textual interface for a smoother onboarding experience.
* **EP Process Adoption:** Full integration of the EP process for all structural changes.

### Phase 2: The Senses (v0.3.x -> v0.5.0)

*Goal: Safely connect the Persona to external contexts without compromising the Core.*

* **Tool Calling Integration:** Defining a standard protocol for the Persona to request and consume output from
  Periphery tools (e.g., `smart_fetch.py`).
* **Context Hydration:** Automatic injection of project-specific context (git history, AST analysis) during the `wake`
  phase.
* **LLM Agnosticism:** Abstracting the model interface to easily swap between Gemini 3.1 Pro, Claude, or local
  open-weights models.

### Phase 3: The Council (v0.6.x -> v1.0.0)

*Goal: Realize the "Council Architecture" as active, autonomous debaters.*

* **Internal Arbitration:** Implementing mechanisms where the 9 Pillars (Noether, Popper, etc.) can programmatically
  critique the model's output before it reaches the user.
* **Multi-Agent Topology:** Allowing a Persona to spawn sub-agents for specific tasks.
* **Stable API:** Freezing the `tur.schemas` and core APIs for a v1.0 release.

## Backwards Compatibility

This is a forward-looking informational document. It does not break any existing code. Future EPs derived from this
roadmap will address their specific compatibility concerns.

## Change Log

* **2026-02-19:**
    * Initial Draft.
