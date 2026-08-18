---
title: "EP-0109: Harness and Terrain Adapters (The Space Suit Protocol)"
description: "Proposes the Adapter Pattern for bridging Tur's core identity with external harnesses and terrain environments."
icon: lucide/plug
status: superseded
---

# EP-0109: Harness and Terrain Adapters (The Space Suit Protocol)

| Field       | Value                                                  |
|:------------|:-------------------------------------------------------|
| **EP**      | 0109                                                   |
| **Title**   | Harness and Terrain Adapters (The Space Suit Protocol) |
| **Author**  | The Architect & Ariel                                  |
| **Status**  | Superseded                                             |
| **Type**    | Standards Track                                        |
| **Created** | 2026-05-10                                             |
| **Updated** | 2026-05-11                                             |

## Abstract

Following the establishment of the Tri-Partite Architecture (The Traveler, The Terrain, The Harness), Tur must implement
a formal Adapter Pattern (Hexagonal Architecture / Ports and Adapters). This EP proposes the creation of
`HarnessAdapters` and `TerrainAdapters` to serve as the "Space Suit" for the Persona. This allows the core identity (The
Traveler) to bridge its internal state with disparate external execution engines and project environments without
compromising its integrity.

*(This EP has been largely superseded by the practical implementation and documentation
in `docs/concepts/harness-integration.md`, which provides the concrete guide for external Harnesses to integrate with
Tur's universal interfaces.)*

## Motivation

Tur's core value proposition is **Portability**.
If the Persona's internal state (Memory, Principles, Protocols) is tightly coupled to a single execution engine (e.g.,
the current MCP implementation) or assumes a single type of project layout, it ceases to be a universal "Traveler."

Furthermore, the industry is experiencing an explosion of agent tool frameworks ("The 100 Flavors of Ice Cream" problem:
MCP, Pi Skills, Anthropic Skills, OpenCode tools). Tur must absolutely avoid the trap of orchestrating or natively
supporting every new tool execution format.

To "Travel Around" successfully, Tur needs a standardized, extremely thin boundary to plug the Persona into whatever
external reality it encounters, while maintaining **Radical Containment**: Tur provides Identity and State; it does NOT
orchestrate external tools.

## Rationale (The Council Framework)

* **Containment (The Golem Protocol): The Boundary of Orchestration.** Tur must not hardcode LLM-specific inference
  logic, OS-specific environment logic, or external tool execution logic within its core. It is a headless state engine.
  The complexity of tool execution belongs entirely to the Harness.
* **Efficiency (The Shannon Module):** Building and maintaining an adapter inside Tur's core for every single new agent
  framework would lead to massive entropy and dependency bloat. The "Ports" must be universal, shifting the burden of
  specific "Adapters" to the community of the respective Harness.
* **Symmetry (The Noether Module):** The Traveler is the Constant; the Harness and Terrain are the Variables. There must
  be a mathematical Transformation Matrix (Adapter) to map the Constant to the Variables.

## Specification

### 1. Hexagonal Architecture (Ports and Adapters)

*(Struck via The Dennis Point: The internal Hexagonal Architecture was over-engineering. Since Tur relies entirely on
standard I/O (CLI) and standard JSON-RPC (MCP), and refuses to build framework-specific logic internally, the "Adapter"
interfaces were purely boilerplate. Tur's architecture is simply a Compiler and an MCP Server.)*

### 2. The Harness Adapter (The Brain-Machine Interface)

Tur does not maintain internal Python adapters. The "Harness Adapter" concept refers entirely to **external code**
written in the language of the target Harness (e.g., the `tur-adapter.ts` Pi extension) that executes the standard Tur
CLI or connects to the Tur MCP Server.

* **Core Interfaces (Built-in to Tur):**
    * **CLI:** Standard text output via `stdout` (`tur wake`).
    * **MCP Server:** Standard JSON-RPC over `stdio` (`tur serve`).
* **External Adapters:** Scripts or extensions built *outside* Tur that bridge these interfaces to specific agent
  frameworks.

### 3. ~~The Terrain Adapter (The Sensory Interface)~~

*(Struck via The Dennis Point: The entire concept of a TerrainPort is an anti-pattern. Tur does not need to read the
project codebase because the external Harness natively handles file discovery and context injection. Building Terrain
Adapters in Tur duplicates context, violating the Shannon Module. Tur's only responsibility is managing the internal
state of the Traveler.)*

## Backwards Compatibility

* This is a structural refactoring, not a destructive change.
* The current CLI commands (`tur wake`, `tur serve`) will remain the primary entry points but will be re-wired under the
  hood to instantiate the appropriate `Adapter` rather than executing business logic directly.
* Existing `.tur/` directories and personas will not be affected.

## Reference Implementation

Superseded by `docs/concepts/harness-integration.md` and external adapter implementations (e.g. `.pi/extensions/tur-adapter.ts`).

## Change Log


* **2026-05-11:**
    * Status changed to `Superseded`, referencing `docs/concepts/harness-integration.md` as the superseding document and
      the `.pi/extensions/tur-adapter.ts` as the reference implementation.
    * Added the "Boundary of Orchestration" constraint to the Motivation and Rationale, explicitly stating Tur's refusal
      to solve the "100 Flavors of Ice Cream" tool orchestration problem.
    * Refined the Harness Adapter spec to emphasize that Tur only maintains universal ports (like MCP), shifting the
      burden of specific Harness adapters to external plugins or the Harnesses themselves.
    * Struck out `AgentSkillsTerrainAdapter` from the specification. Falsified via the Dennis Point: injecting skills
      via Tur duplicates the native discovery mechanisms of modern Harnesses (Claude, Pi), wasting tokens and violating
      the Boundary of Orchestration.
    * Struck out the entire `TerrainPort` specification. Tur manages the Traveler; the Harness manages the Terrain.
    * Struck out the internal Hexagonal Architecture (Ports and Adapters) via the Dennis Point. If Tur only ever
      supports CLI (stdout) and MCP (stdio), maintaining an internal `HarnessPort` interface is over-engineered
      boilerplate. "Adapters" are now defined strictly as *external* code (like the Pi extension) that wrap Tur's
      standard interfaces.