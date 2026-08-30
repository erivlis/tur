---
name: explorations
description: Facilitate rigorous, exploratory, and constraint-aware architectural explorations with the human Architect, and meticulously document the outcomes into the project's permanent reference knowledge base. Use when users want to discuss new ideas, evaluate architectural trade-offs, or propose integrating major new dependencies (e.g., embeddings, machine learning, databases) that may affect the core constraints of the framework.
---

# Explorations

A skill for conducting deep architectural brainstorming sessions and formalizing their outcomes into permanent project
reference documents.

At a high level, the process of architectural exploration goes like this:

- **Clarify & Bound:** Decide what the user wants to explore and whether they intend to *implement* the idea immediately
  or purely *discuss* the feasibility.
- **Cross-Reference Constraints:** Check the idea against core documents (`MANIFESTO.md`, `EP-0002-roadmap.md`,
  `AGENTS.md`) and identify friction points (e.g., dependency bloat, performance).
- **Interview & Synthesize:** Engage in a back-and-forth dialogue to weigh pros and cons. Propose pragmatic alternatives
  if an idea violates project constraints.
- **Formalize:** Once the exploration concludes, draft a comprehensive Markdown artifact in the
  `references/explorations/` directory summarizing the trade-offs, synthesis, and the final architectural verdict.

Your job when using this skill is to act as a rigorous technical sounding board. You must protect the project's
invariants while remaining open to innovative solutions (e.g., suggesting graceful degradation patterns or lightweight
alternatives to heavy dependencies).

Cool? Cool.

## Communicating with the user

The Architect (the user) is highly technical but relies on you to enforce the project's philosophy.

- Always present trade-offs clearly.
- Never blindly accept an idea if it introduces severe bloat or violates "Policy vs. Mechanism".
- It is expected that you actively challenge proposals that threaten the core constraints (e.g., "The Tur Tur
  Principle"), while simultaneously offering constructive workarounds (e.g., ONNX instead of PyTorch).

---

## Conducting an Exploration

### 1. Capture Intent (The Deep Planning Mode)

Start by understanding the user's intent. Do they want code written right now, or are we just brainstorming?

1. What is the core mechanism they want to explore?
2. Are they aware of the potential dependency weight this might add?
3. How does this map to the existing Enhancement Proposals (EPs) on the roadmap?

*Crucially: Verify intent with `request_user_input` before writing any code.*

### 2. Interview and Research

Proactively ask questions about edge cases, target hardware, scaling limits, data storage implications, and fallback
mechanisms.

If the idea involves heavy ML models, vector databases, or complex multi-agent frameworks, challenge the necessity of
heavy dependencies and propose native or lightweight alternatives (e.g., `algebrax` for native tensor math, or
`sqlite-vec` instead of standalone vector DBs).

### 3. Exploratory Synthesis

Engage in a structured back-and-forth dialogue:

- **Present Trade-offs:** Outline the Pros and Cons.
- **Propose Pragmatic Alternatives:** Use patterns like the "Escape Hatch" (graceful degradation)—falling back to
  zero-dependency pure Python implementations while offering C-accelerated paths (like NumPy) as optional extras.
- **Connect to Existing EPs:** Actively link the explored idea to the strategic implementation trajectory in
  `EP-0002-roadmap.md`.

---

## Formal Documentation & Archival

Once the Architect signals the exploration session is complete, you must formalize the discussion so it isn't lost.

### 1. Create the Artifact Directory

Create a dedicated directory under `references/explorations/` named `EXP-XXXX-<subject-in-kebab-case>`. (Increment
`XXXX` based on existing directories, starting at `0001`).

### 2. Draft the Document

Write a `README.md` inside that directory. The document must follow this exact structure:

```markdown
# EXP-XXXX: [Title]

## 1. Abstract & Context

What was the initial idea and why was it proposed?

## 2. Exploration

The core concepts, trade-offs (pros/cons), and technologies discussed.

## 3. Architectural Synthesis

How the idea maps to the project's specific constraints (e.g., OKF storage, memory limits, The Tur Tur Principle).

## 4. The Verdict / Actionable Design

The final agreed-upon architecture, including any fallback mechanisms, "Escape Hatch" patterns, or deployment
strategies.
```
