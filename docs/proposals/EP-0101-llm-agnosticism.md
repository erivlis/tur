# EP-0101: LLM Agnosticism

| Field       | Value                            |
|:------------|:---------------------------------|
| **EP**      | 0101                             |
| **Title**   | LLM Agnosticism                  |
| **Author**  | Eran Rivlis, Ariel               |
| **Status**  | Deferred                         |
| **Type**    | Architecture                     |
| **Created** | 2026-03-29                       |

## Abstract

This proposal outlines the long-term architectural goal of making the Tur framework backend-agnostic. It proposes refactoring the components that interact with Large Language Models (currently only the `sleep` command) to use a provider/adapter pattern. This will allow users to seamlessly switch between different LLM providers (e.g., Google Gemini, Anthropic Claude, OpenAI GPT, or local models) based on configuration.

## Motivation

To be a true Persona Engineering *Framework*, Tur cannot be tied to a single LLM provider. Different models have different strengths, weaknesses, and cost structures. A user might prefer:
*   **Gemini 3.1 Pro** for complex reasoning and structured data extraction (as in `sleep`).
*   **Claude 3 Opus** for long-form creative writing or philosophical debate.
*   A local, open-weights model (like Llama or Mixtral) for privacy, cost-effectiveness, or offline use.

Tying the framework to one provider violates the principle of portability and limits the user's architectural freedom.

## Rationale (The Council Framework)

1.  **The Steward (Harmony/Pragmatism):** A provider pattern allows the system to evolve and adapt as new, better models are released without requiring a full rewrite.
2.  **Noether (Symmetry):** The core logic of Tur (defining, waking, and measuring a persona) should be symmetrical and independent of the specific "brain" executing the persona's will.
3.  **The Golem (Containment):** Each provider can be contained within its own module, ensuring that the specific quirks or dependencies of one API do not bleed into the core framework.

## Specification (High-Level Vision)

1.  **Provider Interface:** Define a standard `LLMProvider` abstract base class or protocol in `tur/llms/providers.py`. This interface would have a single required method, e.g., `generate_structured_content(prompt: str, schema: BaseModel) -> dict`.

2.  **Concrete Implementations:**
    *   `tur/llms/gemini.py`: A `GeminiProvider` that implements the interface using the `google-genai` SDK.
    *   `tur/llms/anthropic.py`: A `ClaudeProvider` that implements the interface using the `anthropic` SDK.
    *   `tur/llms/openai.py`: An `OpenAIProvider` for GPT models.

3.  **Configuration in `persona.yaml`:** The `model` field in the `persona.yaml` would be updated to specify both the provider and the model name.

    ```yaml
    # Current
    model: "gemini-3.1-pro-preview"

    # Proposed
    model:
      provider: "gemini"
      name: "gemini-3.1-pro-preview"
      # Or
      # provider: "anthropic"
      # name: "claude-3-opus-20240229"
    ```

4.  **Factory Function:** A factory function, `get_llm_provider(config: dict) -> LLMProvider`, would read the persona's model configuration and return the correct provider instance. The `sleep` command would then use this provider to perform its work.

## Backwards Compatibility

This is a forward-looking architectural document. As it is `Deferred`, it breaks no current implementations. When this EP is accepted, a migration path for the `model` field in `persona.yaml` will be required.

## Change Log

*   2026-03-29: Initial Draft (Deferred for Phase 2).
