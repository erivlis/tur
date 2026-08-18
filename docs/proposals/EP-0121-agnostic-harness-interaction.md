---
title: "EP-0121: The Agnostic Harness Interaction Protocol"
description: "Formalizes a unified, LLM-provider-agnostic interaction pattern for all cognitive commands, covering both MCP (context/sampling) and CLI (delegation prompt) modes."
icon: lucide/cable
status: implemented
---

# EP-0121: The Agnostic Harness Interaction Protocol

| Field       | Value                                                                           |
|:------------|:--------------------------------------------------------------------------------|
| **EP**      | 0121                                                                            |
| **Title**   | The Agnostic Harness Interaction Protocol                                       |
| **Author**  | The Architect                                                                   |
| **Status**  | Implemented                                                                     |
| **Type**    | Standards Track                                                                 |
| **Created** | 2026-07-18                                                                      |
| **Updated** | 2026-07-25                                                                      |
| **Depends** | EP-0101 (LLM Agnosticism), EP-0108 (Spark Protocol), EP-0109 (Harness Adapters) |

## Abstract

This proposal formalizes a single, unified **Agnostic Harness Interaction Pattern** for all Tur commands that require
LLM inference. Rather than each cognitive module (`dreaming.py`, `introspection.py`, etc.) independently managing
the distinction between MCP vs. CLI execution contexts, this EP defines a standardized dual-mode protocol:

- **MCP Mode (Context Path):** When a `mcp_context` is available (the Harness provides the LLM), Tur requests
  inference via `ctx.sample()` (MCP Sampling). The Harness's own LLM resolves the request. Tur never holds API keys.
- **CLI Mode (Delegation Path):** When no `mcp_context` is available (standalone terminal), Tur raises a
  `HarnessDelegationError` containing a structured, self-describing prompt instructing the agent Harness to execute
  the operation on Tur's behalf. This pattern already exists in `introspection.py` but is absent in `dreaming.py`.

## Motivation

Today, the two primary cognitive surfaces diverge in their harness interaction strategy:

| Module                                | MCP path                             | CLI path                                          |
|---------------------------------------|--------------------------------------|---------------------------------------------------|
| `introspection.py` (`tur introspect`) | `ctx.sample()` via `RussellSubagent` | `HarnessDelegationError` with structured prompt ✅ |
| `dreaming.py` (`tur sleep`)           | `ctx.sample()` via `_mcp_sample`     | Hardcoded `GEMINI_API_KEY` fallback ❌             |

The `dreaming.py` CLI fallback is hardcoded to `google-genai` and `GEMINI_API_KEY`. This:

1. Violates EP-0101's goal of zero embedded LLM SDK dependencies.
2. Creates an asymmetry between the two primary cognitive commands (`sleep` vs. `introspect`).
3. Will not generalize to other LLM providers (OpenAI, Anthropic, Ollama, etc.).

The preferred long-term framing, inspired by the **Spark Protocol (EP-0108)**, uses natural language:
> *"A session epilogue is extracted during `sleep`. That epilogue **sparks** the next incarnation. The Harness ignites
the spark."*

The Harness — not Tur — is the entity holding the lighter.

## Specification

### 1. The Dual-Mode Adapter Interface

Every cognitive command that requires LLM inference must use a single shared adapter that:

1. Detects whether `mcp_context` (`ctx`) is available.
2. If yes → routes to `ctx.sample()` (MCP Sampling path).
3. If no → raises `HarnessDelegationError` with a fully self-describing delegation prompt.

This adapter should be extracted to `tur._helpers` as a utility function:

```python
def require_inference(
        prompt: str,
        ctx: Any | None,
        task_description: str,
) -> str:
    """
    Request LLM inference via the dual-mode Agnostic Harness Interaction Protocol.

    If `ctx` (MCP context) is available, issues a Sampling request to the connected Harness.
    If not, raises HarnessDelegationError with a self-describing delegation prompt.
    """
```

### 2. The Delegation Prompt Standard

A `HarnessDelegationError` delegation prompt must contain:

- **What Tur needs**: A clear description of the inference task.
- **Input data**: The raw material (memories, session notes, etc.) as structured text.
- **Output contract**: The exact format Tur expects back (JSON schema, plain text, etc.).
- **Execution steps**: How the Harness should run the task and pass the result back to Tur.

This pattern is already well-established in `introspection.py` lines 215-288 and should become the canonical template.

### 3. Provider Generalization

The protocol explicitly does not reference `GEMINI_API_KEY` or any provider-specific token. Environment variable
checks, if needed for the direct-API fallback mode, should use a generic `TUR_LLM_API_KEY` variable that can be
mapped to any provider's token by the deployment environment.

> [!NOTE]
> The direct-API fallback (local Gemini call) may optionally be retained as a *third* mode — but only if it is
> mediated through the same `require_inference` adapter and is truly provider-agnostic (e.g., via `litellm` or a
> configurable provider module). This is out of scope for this EP's initial implementation.

### 4. Scope of Changes

| File                       | Change                                                                                    |
|----------------------------|-------------------------------------------------------------------------------------------|
| `src/tur/_helpers.py`      | Add `require_inference(prompt, ctx, task_description)` utility                            |
| `src/tur/dreaming.py`      | Replace `GEMINI_API_KEY` fallback with `HarnessDelegationError` via `require_inference`   |
| `src/tur/introspection.py` | Refactor existing delegation logic to use `require_inference`                             |
| `src/tur/models.py`        | Confirm `HarnessDelegationError` is in the right module (currently in `introspection.py`) |

## Rationale (The Council Framework)

- **Noether (Symmetry):** `sleep` and `introspect` must be symmetrically agnostic — both commands follow the identical
  interaction protocol regardless of LLM provider.
- **Golem (Containment):** Tur holds no API keys. The Harness is the sovereign of inference. This boundary is absolute.
- **Shannon (Efficiency):** A single `require_inference` utility eliminates the scattered, per-module provider logic.
- **Popper (Falsifiability):** The delegation prompt output is a testable contract — the Harness knows exactly what to
  return and tests can validate the delegation path without a live LLM.

## Backwards Compatibility

- **`tur sleep` from CLI without API key**: Currently degrades to a Gemini API error. After this EP: raises
  `HarnessDelegationError` with a delegation prompt, matching the `tur introspect` behaviour.
- **`tur sleep` from MCP context**: No change — `ctx.sample()` path is already implemented.

## Open Questions

1. Should `HarnessDelegationError` be moved from `introspection.py` to `tur.models` or `tur._helpers` to be shared?
2. Should there be a third "offline" mode that uses a lightweight local summarizer (no LLM) for degraded-but-functional
   `sleep` behaviour?

## Reference Implementation

Implemented in `src/tur/_helpers.py` (`require_inference`), `src/tur/models.py` (`HarnessDelegationError`), `src/tur/dreaming.py`, and `src/tur/introspection.py`.

## Change Log


* **2026-07-25:**
    * **Status promoted to Implemented.**
    * Moved `HarnessDelegationError` into `src/tur/models.py` for shared use across the framework.
    * Added `require_inference` helper in `src/tur/_helpers.py` implementing the dual-mode adapter (MCP sampling vs. CLI delegation prompt).
    * Refactored `perform_sleep_dreaming` in `src/tur/dreaming.py` and `tur sleep` CLI command in `src/tur/cli/agent.py` to raise and catch `HarnessDelegationError` with self-describing delegation instructions when run offline without API keys.
* **2026-07-18:**
    * Initial Draft. Spawned from the EP-0101 and EP-0108 status review. Formalizes the dual-mode (MCP sampling vs.
      CLI delegation) pattern already partially implemented in `introspection.py` as the universal standard for all
      cognitive commands in Tur.
