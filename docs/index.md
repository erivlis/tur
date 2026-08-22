---
description: Persistent state and memory management engine for AI agents.
icon: lucide/home
---

# Tur: Persistent State and Memory Engine for AI Agents

> *"From a distance, he appeared to be a giant. But as they approached, he became a man of normal stature."*
> 
> — *[Jim Knopf und Lukas der Lokomotivführer](https://en.wikipedia.org/wiki/Jim_Button_and_Luke_the_Engine_Driver)*

![Tur Logo Light](assets/images/logo-light.png#only-light){ width="300" align=right}
![Tur Logo Dark](assets/images/logo-dark.png#only-dark){ width="300" align=right}

**Tur** is an open-source state and memory management engine for AI agents and Large Language Models.

It provides persistent, structured persona state across sessions, harnesses, and codebases via the Model Context Protocol (MCP) and local CLI tools. Rather than relying on ephemeral system prompt configuration, Tur manages persona identity, operational principles, hierarchical memory (L1 ledger & L2 knowledge graph), and session continuity as structured, version-controlled files.

This documentation site provides the core concepts, architectural proposals, and usage guides for the Tur framework.

## Core Philosophy

The project is built on three foundational pillars:

1. **The Tur Tur Principle**: The complexity of AI behavior can be made more focused and manageable by imposing clear constraints, deterministic state files, and explicit behavioral protocols.
2. **The Tri-Partite Architecture**: Clean ontological separation between **The Traveler** (the sovereign Mind and Memory managed by Tur), **The Terrain** (the codebase and local physics), and **The Harness** (the compute and tools).
3. **Policy vs. Mechanism**: Strict separation between the deterministic execution engine (Body) and the philosophical Council identity (Mind).

## Getting Started

To get started, check out the **[Usage Guide](usage.md)**.

To understand the architectural roadmap and design history, explore the **[Enhancement Proposals (EPs)](proposals/index.md)**.