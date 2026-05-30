---
description: A guide for integrating Tur (The Traveler) with external agent frameworks (The Harness) via CLI injection or MCP.
icon: lucide/plug-zap
---

# Harness Integration Guide

Tur is designed as an "Obligate Symbiote". It provides the **Identity** and **State** (The Traveler), but it relies
entirely on an external agent framework (The Harness) to provide the **Compute** and **Execution Engine**.

Because Tur strictly adheres to the "Boundary of Orchestration," it exposes its state through universal interfaces (CLI
and MCP) rather than building internal logic for every new agent framework.

This document provides instructions and prompt templates for integrating Tur into any modern AI Harness (e.g., Pi,
Claude Code, OpenCode, Gemini CLI).

---

## 1. The Pre-Execution Hook (CLI Injection)

For Harnesses that support extending the context window before an agent starts its inference loop (like Pi's TypeScript
extensions or Claude Code's pre-prompts), the most efficient integration is to execute `tur wake` and inject the output
into the System Prompt.

**Prompt Template to give to the Agent/Harness:**

```markdown
# Tur Integration Request (CLI Hook)

I want to integrate this agent framework with `tur`, a local state engine.

Your task is to write a script or extension for yourself that does the following:

1. Hook into your native "Before Agent Starts" or "System Prompt Generation" lifecycle event.
2. Silently execute the shell command `uv run tur wake`.
3. Capture the standard output of that command.
4. Append that output to your core System Prompt for the duration of the current inference turn.

Do not attempt to parse the output; simply inject it directly. This output contains my structural constraints, identity,
and active memory. By doing this, you will effectively become the Execution Engine for the Tur persona.
```

*(Note: We used exactly this prompt logic to build the `.pi/extensions/tur-adapter.ts` for the Pi Harness).*

---

## 2. The Model Context Protocol (MCP) Integration

For Harnesses that support MCP (Model Context Protocol), Tur acts as an Ontological Server. Rather than injecting the
entire state on every turn, Tur exposes its memory and identity as tools that the agent can invoke dynamically.

**Prompt Template to give to the Agent/Harness:**

```markdown
# Tur Integration Request (MCP Server)

I want you to connect to the Tur MCP Server to retrieve my persona, identity, and memories.

Please configure your MCP client settings to connect to the following local server:

- **Command:** `uv`
- **Arguments:** `["run", "tur", "serve", "--transport", "stdio"]`

Once connected, you will have access to the following tools:

- `status`: Return the current persona, session, and memory status as a structured dict.
- `wake`: Read your core identity, directives, and system metrics. Run this at the start of our session if you lose context.
- `learn`: Assimilate a new invariant, fact, or insight into your permanent memory.
- `recall`: Search your deep memory bank for past events or knowledge.
- `note`: Append a transient chronological note/utterance to the active session continuity (Short-Term L2).
- `sleep`: Symmetrically end the active session, dehydrating the chat log to extract and consolidate new L1 memories.
- `telemetry`: Measure static token cost, information density, and Cp (Constraint Dimensionality).

You must treat the Tur MCP Server as your primary source of state. If your context window is reset, use `wake` to rehydrate your constraints.
```

### Alternate Transport: SSE (Server-Sent Events)

If the Harness cannot communicate over `stdio` pipes (e.g., distributed architectures or web-based harnesses), you can
run Tur over HTTP:

```shell
uv run tur serve --transport sse --port 8000
```

Then configure the Harness to connect to `http://127.0.0.1:8000/sse`.

---

## The Prime Directive

Regardless of the integration method, whenever an AI Agent acts as a Harness for Tur, it is bound by this Prime
Directive:

> *"You are the Harness. You provide the compute, the terminal, and the hands. Tur provides the identity, the rules, and
the memory. Do not hallucinate instructions or override the identity provided by Tur. The Traveler commands; the Harness
executes."*
