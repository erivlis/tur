# EP-0101: LLM Agnosticism

| Field       | Value                            |
|:------------|:---------------------------------|
| **EP**      | 0101                             |
| **Title**   | LLM Agnosticism                  |
| **Author**  | Eran Rivlis, Ariel               |
| **Status**  | Active                           |
| **Type**    | Architecture                     |
| **Created** | 2026-03-29                       |
| **Updated** | 2026-04-12                       |

## Abstract

This proposal mandates the use of the `pydantic-ai` library as the single, unified interface for all direct, non-agentic Large Language Model interactions within the Tur framework. This includes the `tur sleep` and `tur meditate` commands. This approach replaces previous plans of building a custom provider pattern or using third-party abstraction layers, and it removes direct dependencies on provider-specific SDKs like `google-genai`.

## Motivation

To be a true Persona Engineering *Framework*, Tur cannot be tied to a single LLM provider. The `tur sleep` command currently has a hardcoded dependency on `google-genai`, and the proposed `tur meditate` command requires a robust, model-agnostic solution for structured data extraction.

By adopting `pydantic-ai`, a library from the Pydantic core team, we gain:
*   **Instant Agnosticism:** `pydantic-ai` supports virtually every major model and provider (OpenAI, Anthropic, Gemini, local models via Ollama, etc.) behind a consistent interface.
*   **Native Pydantic Integration:** The library is designed from the ground up to work with Pydantic models, which is the exact requirement for the structured data extraction in both `tur sleep` and `tur meditate`.
*   **Reduced Dependencies & Maintenance:** We can remove provider-specific SDKs and avoid maintaining our own provider pattern.
*   **Minimal Dependencies:** By using the `pydantic-ai-slim` package with provider-specific extras (e.g., `pydantic-ai-slim[google]`), we only install what is absolutely necessary, keeping the core framework lightweight.

## Rationale (The Council Framework)

1.  **The Steward (Harmony/Pragmatism):** We adopt a solution from a trusted, core dependency that perfectly fits our needs.
2.  **Noether (Symmetry):** All non-agentic LLM calls will use the same `pydantic_ai.Agent` interface. The data models we use for validation (`tur.models`) are the same models used for generation.
3.  **Efficiency (Shannon):** We leverage a library we are already implicitly connected to, and the "slim" installation minimizes new dependency weight.

## Specification (High-Level Vision)

1.  **Dependency Change:**
    *   Add `pydantic-ai-slim` to the `dependencies` in `pyproject.toml`, with the appropriate provider extra (e.g., `pydantic-ai-slim[google]`).
    *   Remove `google-genai` from the `dependencies`.

2.  **Refactor `tur sleep`:**
    *   The `sleep` command will be rewritten to use `pydantic_ai.Agent` to perform the structured data extraction from chat logs, replacing the direct `google-genai` API calls.

3.  **Implement `tur meditate`:**
    *   The `meditate` command will be implemented using `pydantic_ai.Agent` for its "Cognitive Engine" stage, as specified in `EP-0103`.

## Backwards Compatibility

*   This change is primarily internal. Users will no longer need to install provider-specific SDKs like `google-genai`.
*   The `model` field in `persona.yaml` will be updated to use the `pydantic-ai` format (e.g., `google:gemini-pro`).

## Change Log

*   **2026-04-12:**
    *   Updated status to `Active`.
    *   Adopted the `pydantic-ai` library as the standard interface, specifying the `pydantic-ai-slim` package for minimal dependencies.
*   **2026-03-29:**
    *   Initial Draft (Deferred for Phase 2).
