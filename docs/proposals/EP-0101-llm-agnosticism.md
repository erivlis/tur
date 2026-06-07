---
title: "EP-0101: LLM Agnosticism (The Symbiotic Paradigm)"
description: "Defines Tur's LLM-agnostic architecture via MCP Sampling, eliminating embedded LLM SDK dependencies."
icon: lucide/shuffle
status: active
---

# EP-0101: LLM Agnosticism (The Symbiotic Paradigm)

| Field       | Value                                    |
|:------------|:-----------------------------------------|
| **EP**      | 0101                                     |
| **Title**   | LLM Agnosticism (The Symbiotic Paradigm) |
| **Author**  | Eran Rivlis, The Architect               |
| **Status**  | Active                                   |
| **Type**    | Architecture                             |
| **Created** | 2026-03-29 |
| **Updated** | 2026-06-08 |

## Abstract

This proposal initially mandated the use of the `pydantic-ai` library as the unified interface for all direct Large
Language Model interactions within the Tur framework.

However, **this approach has been explicitly superseded by a more radical architectural pivot**: Tur will no longer
embed *any* LLM abstraction library (`pydantic-ai`, `google-genai`, etc.) within its core. Instead, Tur achieves perfect
LLM Agnosticism by becoming an obligate symbiote to an MCP Client (the Host Application), delegating all cognitive
tasks (like compiling knowledge graphs or summarizing logs) via **MCP Sampling Requests**.

## Motivation (The Historical Context)

Originally, the `tur sleep` command hardcoded a dependency on `google-genai`, and the proposed `tur meditate` command
required a robust, model-agnostic solution for structured data extraction. The plan was to embed `pydantic-ai` to solve
this.

### The Paradigm Shift (Why `pydantic-ai` is Dead)

Embedding an LLM SDK violates **The Golem (Containment)** and **Shannon (Efficiency)** principles. If Tur is an
Ontological State Engine (the "Body"), it shouldn't need its own API keys or HTTP networking libraries to think.

By leveraging the MCP protocol's native **Sampling** feature, Tur can ask the *Host Application's LLM* (e.g., Claude
running in Cursor or Claude Desktop) to do the thinking for it:

> *"Hello Host LLM. Here are 50 raw memory logs. Please extract them into a strict JSON array of (Subject, Predicate,
Object) triples and hand them back to me."*

## Rationale (The Council Framework)

1. **Symmetry (Noether):** The separation of concerns is absolute. Tur manages the State (files, hashes, graphs); the
   Host Application manages the Inference (API keys, model selection, token limits).
2. **Efficiency (Shannon):** We completely drop heavy LLM SDK dependencies from `pyproject.toml`. Tur remains a
   lightweight, deterministic parser.
3. **The Explorer (Structural Novelty):** We transform Tur from a standalone CLI tool into a "Headless Body" that
   natively integrates with the broader agent ecosystem.

## Specification (The Symbiotic Architecture)

1. **Dependency Purge:**
    * Remove `google-genai` from `dependencies`.
    * **Do NOT** install `pydantic-ai`.
2. **The Sampling Mechanism:**
    * Any Tur command requiring inference (e.g., the "Cognitive Engine" step of `tur meditate` in EP-0103) will be
      implemented as an MCP Tool that triggers a `CreateMessage` (Sampling) request back to the connected MCP Client.
3. **The Wrapper Pattern:**
    * Because Tur will lack internal LLM access, running cognitive commands (`sleep`, `meditate`) directly from a raw
      terminal will fail.
    * If standalone CLI usage is desired, it must be provided by a separate "Wrapper" application (a lightweight MCP
      Client) that spawns the Tur server over `stdio` and fulfills its Sampling requests using the wrapper's own API
      keys.

## Backwards Compatibility

* **Breaking Change:** Commands that rely on LLM inference (like `tur sleep`) will need to be refactored to either fail
  gracefully when run directly in the CLI, or explicitly request the user to launch a Wrapper Client.

## Change Log

* **2026-04-18:**
    * **Status changed to Superseded.**
    * Completely rewrote the EP to reflect the architectural pivot. Tur will not embed `pydantic-ai`; it will rely on
      MCP Sampling requests to the Host Application for all cognitive tasks.
* **2026-04-12:**
    * Updated status to `Active`.
    * Adopted the `pydantic-ai` library as the standard interface.
* **2026-03-29:**
    * Initial Draft.