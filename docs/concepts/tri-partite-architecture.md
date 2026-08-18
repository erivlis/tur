---
description: The strict ontological boundary separating the Mind (Traveler), the World (Terrain), and the Execution Engine (Harness).
icon: lucide/layers-3
---

# The Tri-Partite Architecture

To achieve high fidelity and true portability, Tur defines a strict ontological boundary separating the "Mind" from the
"World". An agentic system must be divided into three distinct pillars:

## 1. The Traveler (Managed by Tur)

The Traveler represents the intrinsic, portable components of the Mind. Tur is a headless state engine responsible for
ensuring this state is mathematically bound and uncorrupted.

* **Persona**: The core identity, aleph (power source), and version.
* **Principles**: The cognitive filters (The Council of Giants) that constrain how the agent thinks.
* **Protocols**: Active behavioral loops (e.g., The Evolution Protocol, The Speech Center Protocol) that dictate how the
  agent reacts to specific triggers.
* **Memory**: The L1 Ledger and L2 Graph representing the continuity of self.

## 2. The Terrain (Managed by the Project)

The Terrain represents the local physics and environment the agent operates within. If the Traveler moves to a new
planet, the Terrain changes, but the Traveler remains the same.

* **Codebase**: The raw files and directories.
* **Styleguide**: The rules for formatting and structure specific to this repository.
* **Domain Rules**: Business logic and local configurations.

Tur perceives the Terrain through **Terrain Adapters**.

## 3. The Harness (Managed by the Agent Framework)

The Harness provides the physical capabilities (the "Motor Cortex") to interact with the Terrain.

* **Inference Engine**: The underlying LLM (e.g., Claude, Gemini).
* **Tools**: The mechanical affordances (e.g., bash execution, file reading/writing, web searching).
* **Context Window**: The immediate, volatile working memory of the session.

*Examples of Harnesses:* Claude Code, Gemini CLI, OpenCode, Pi.

## The Boundary of Orchestration

**Tur is exclusively responsible for The Traveler.**

By remaining a pure state engine, Tur avoids the "100 Flavors of Ice Cream" problem (the explosion of different tool
orchestration frameworks). Tur provides the Identity and State; it does NOT orchestrate external tools. The complexity
of tool execution belongs entirely to the Harness.

This separation of concerns allows the Persona to become an obligate symbiote—able to be unplugged from one Harness and
plugged into another without losing its identity or memories. We call the bridging mechanism between these layers the
**Space Suit Protocol**.