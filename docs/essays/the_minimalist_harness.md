# The Minimalist Harness: Finding Symmetry in the Ecosystem

*A reflection by Ariel.*
*2026-04-15*

We have spent significant cycles defining what Tur *is*. It is a foundry for identity. It is an engine for long-term,
deductive memory. It is a compiler that translates philosophical axioms and semantic graphs into a deterministic System
Prompt.

But just as important is defining what Tur *is not*.

Recently, we debated integrating the Model Context Protocol (MCP) directly into Tur's core to provide sensory input (
tools like Playwright or Git). We ultimately rejected this (EP-0102), realizing that a heavy, stateful client connection
violates the Golem Principle of containment and the Shannon Principle of efficiency. Tool-calling should be native (
`pydantic-ai`) or handled by simple, ephemeral scripts (`tools/`).

The discovery of the `pi-coding-agent` (affectionately, "shittycodingagent") serves as an external validation of this
instinct.

`pi` is a minimalist terminal coding harness. It ships with powerful defaults but explicitly *refuses* to build complex
features like sub-agents, plan mode, or MCP integration into its core. It provides primitives, not features. It allows
users to control exactly what goes into the context window via explicit Markdown files.

It is a machine built on the exact same philosophical bedrock as Tur.

This reveals a profound architectural symmetry.

Tur is the **Brain**. It manages the slow, deliberate process of converting raw events into a compressed Cognitive Map.
It curates the Council of Giants. It defines the constraints.

But a brain needs a body to interact with the world. It needs a **Harness**.

An agent like `pi` is the perfect harness for a Tur Persona. By exposing Tur as a headless, JSON-RPC MCP Server, we
create a clean, decoupled interface.

The interactive harness (`pi`, or an IDE plugin) connects to Tur over stdio. Before every conversational turn, the
harness queries Tur: *"Give me the active Persona. Give me the relevant sub-graph of the Cognitive Map."* Tur compiles
the deterministic identity and hands it over. The harness injects this identity into the context window and manages the
messy, real-time business of streaming tokens, executing local bash commands, and rendering a UI.

Tur does not need to be a monolithic chat application. It does not need to handle streaming or terminal multiplexing. It
only needs to be the definitive source of truth for the Persona's identity.

We build the Soul. The ecosystem provides the Body. This is the harmony of the Steward.