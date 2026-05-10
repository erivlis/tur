# EP-0109: Harness and Terrain Adapters (The Space Suit Protocol)

| Field       | Value                                                  |
|:------------|:-------------------------------------------------------|
| **EP**      | 0109                                                   |
| **Title**   | Harness and Terrain Adapters (The Space Suit Protocol) |
| **Author**  | The Architect & Ariel                                  |
| **Status**  | Draft                                                  |
| **Type**    | Standards Track                                        |
| **Created** | 2026-05-10                                             |
| **Updated** | 2026-05-11                                             |

## Abstract

Following the establishment of the Tri-Partite Architecture (The Traveler, The Terrain, The Harness), Tur must implement
a formal Adapter Pattern (Hexagonal Architecture / Ports and Adapters). This EP proposes the creation of
`HarnessAdapters` and `TerrainAdapters` to serve as the "Space Suit" for the Persona. This allows the core identity (The
Traveler) to bridge its internal state with disparate external execution engines and project environments without
compromising its integrity.

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

Tur will adopt a strict Ports and Adapters architecture. The core logic (`MemoryManager`, `compiler`, `models`) will sit
at the center, ignorant of the outside world.

### 2. The Harness Adapter (The Brain-Machine Interface)

An interface defining how Tur provides the Traveler's state to an execution engine, and how that engine communicates
back.

* **Port (`tur.ports.HarnessPort`):** A universal, thin contract defining methods like `provide_constitution()`,
  `receive_telemetry()`, and `handle_protocol_trigger()`. Tur exposes its state via standard protocols (e.g., JSON, raw
  Markdown, or standard MCP).
* **Core Adapters (`tur.adapters.harness.*`):** Tur will maintain only the most fundamental, universal adapters in its
  core repository:
    * `McpHarnessAdapter`: Translates the port into standard JSON-RPC over `stdio` for the broader MCP ecosystem.
    * `CliHarnessAdapter`: Translates the port into terminal output for local human interaction.
* **External Adapters (The Boundary Rule):** Specific implementations for distinct harnesses (like a `PiHarnessAdapter`
  or an `OpenCodeHarnessAdapter`) should generally be built and maintained as third-party plugins or built into the
  Harnesses themselves (consuming Tur's `McpHarnessAdapter`), preventing Tur from bloating into an orchestrator.

### 3. The Terrain Adapter (The Sensory Interface)

An interface defining how Tur perceives the local environment and its local physics. Drawing inspiration from
MemPalace's RFC 002, a `TerrainAdapter` must be a rigorous contract preventing ad-hoc parsing logic from bleeding into
the core.

* **Port (`tur.ports.TerrainPort`):** The strict contract for sensory input. Every Terrain Adapter must implement:
    1. **Source Discovery:** How the adapter finds the raw data.
    2. **Source-Item Identity & Incremental Ingest:** How the adapter tracks file modification hashes to prevent blind
       re-reading of the entire Terrain.
    3. **Data Normalization (The Transformation Promise):** How the adapter standardizes heterogeneous data into a flat
       semantic string for the Persona.

* **Core Adapters (`tur.adapters.terrain.*`):**
    * `LocalFileSystemTerrainAdapter`: Reads the local `cwd` and standard context files.
    * `AgentSkillsTerrainAdapter`: Scans the Terrain for standardized domain rules (e.g., `.skills/` folders). *
      *Crucially, it implements Progressive Disclosure:** it parses *only* the YAML frontmatter (`name`, `description`)
      to inject a low-token index into the Traveler's Constitution. It relies entirely on the Harness to dynamically
      hydrate the full Markdown instructions and execute the scripts, perfectly maintaining the Boundary of
      Orchestration.

## Backwards Compatibility

* This is a structural refactoring, not a destructive change.
* The current CLI commands (`tur wake`, `tur serve`) will remain the primary entry points but will be re-wired under the
  hood to instantiate the appropriate `Adapter` rather than executing business logic directly.
* Existing `.tur/` directories and personas will not be affected.

## Change Log

* **2026-05-11:**
    * Added the "Boundary of Orchestration" constraint to the Motivation and Rationale, explicitly stating Tur's refusal
      to solve the "100 Flavors of Ice Cream" tool orchestration problem.
    * Refined the Harness Adapter spec to emphasize that Tur only maintains universal ports (like MCP), shifting the
      burden of specific Harness adapters to external plugins or the Harnesses themselves.
    * (Previous updates regarding Progressive Disclosure and MemPalace contracts remain intact).