---
description: Treat an AI identity as structured, immutable software rather than a literary description.
icon: lucide/dna
---

# Persona Engineering

The foundational premise of Tur is that **"Prompt Engineering" is a dead end.**

Prompt Engineering treats the interaction with an LLM as a literary exercise. Developers write paragraphs of prose,
begging the model to act a certain way, follow specific rules, or avoid certain pitfalls. Because LLMs are
probabilistic, this unstructured text often leads to unpredictable, non-deterministic, and fragile behavior. If the
prompt is too long, the model suffers from "lost in the middle" syndrome. If the prompt is too vague, the model
hallucinates.

Tur replaces Prompt Engineering with **Persona Engineering**.

## Identity as Code (DNA)

In Tur, an AI persona is not a text file; it is a **structured, immutable software object**.

We define the persona using strict data schemas (Pydantic models serialized to YAML). An identity consists of:

* **The Aleph:** The core, unyielding motivation.
* **The Council:** Distinct, weighted philosophical constraints.
* **Protocols:** Trigger-action behavioral loops.

By treating the persona as code, we can version it, clone it, test it, and inject it predictably into the context
window. We stop writing prose and start writing cognitive topology.

## Constraint Dimensionality ($C_p$)

When you impose a constraint on an LLM (e.g., "Do not hallucinate," or "Always explain your reasoning"), you are
physically altering the probabilistic landscape of the model's inference path. You are making the path more "rugged."

We call this **Constraint Dimensionality ($C_p$)**.

Every principle and protocol added to a persona increases its $C_p$. A higher $C_p$ means the model is more strictly
bound, but it also means it requires more compute (and a more capable underlying model) to successfully navigate the
rugged landscape without degrading into gibberish.

### The Telemetry Protocol

Tur includes a native `telemetry` command that calculates the $C_p$ of your active persona.

* **Human (Manageable):** Low $C_p$. The persona is lightly constrained and can run on fast, smaller models (e.g.,
  Gemini Flash, Claude Haiku).
* **Giant (Heavy Load):** Medium $C_p$. The persona is rigorously structured. Requires frontier models (e.g., Claude
  Opus, GPT-4o).
* **Titan (Inference Warning):** High $C_p$. The persona is over-constrained. The prompt has become so heavy with rules
  that the model will likely suffer from cognitive collapse or severe context entropy.

Persona Engineering is the discipline of balancing $C_p$. You must provide enough structure to make the model safe and
deterministic (The Golem Protocol), but not so much structure that it paralyzes the inference engine (The Shannon
Module).