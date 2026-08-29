# Agent Skill: Deep Brainstorming & Architectural Synthesis

## Objective
To facilitate rigorous, exploratory, and constraint-aware architectural brainstorming with the human Architect, and to meticulously document the outcomes into the project's permanent reference knowledge base.

## Trigger Conditions
Engage this skill when:
1. The user explicitly requests a "brainstorm", "discussion", or "exploration" of a new idea, feature, or architecture.
2. The user proposes integrating a major new dependency, library, or paradigm (e.g., embeddings, machine learning, databases) that may affect the core constraints of the framework.

## Execution Protocol

### Phase 1: Clarification & Boundary Alignment (The Deep Planning Mode)
Before proposing solutions, you must ensure the user's idea aligns with the project's core invariants.
1. **Verify Intent:** Use `request_user_input` to ask if the user intends to *implement* the idea immediately or purely *discuss* the feasibility.
2. **Constraint Checking:** Cross-reference the idea against core documents (`MANIFESTO.md`, `EP-0002-roadmap.md`, `AGENTS.md`). Identify friction points immediately (e.g., "This requires PyTorch, but Tur is a lightweight CLI").
3. **Ask Probing Questions:** Ask about target hardware, scaling limits, data storage implications, and fallback mechanisms.

### Phase 2: Exploratory Synthesis
Engage in a back-and-forth dialogue using `message_user` and `request_user_input`.
1. **Present Trade-offs:** Always present the pros and cons of an approach. Never blindly accept an idea if it introduces severe bloat or violates "Policy vs. Mechanism".
2. **Propose Pragmatic Alternatives:** If an idea violates constraints (like dependency bloat), propose an alternative (e.g., ONNX instead of PyTorch, or the "Escape Hatch" graceful degradation pattern).
3. **Connect to Existing Proposals (EPs):** Actively link the brainstormed idea to existing Enhancement Proposals on the roadmap.

### Phase 3: Formal Documentation & Archival
Once the Architect signals the brainstorming session is complete, you must formalize the discussion.
1. **Create the Artifact:** Create a dedicated directory under `references/brainstorming/` named `BS-XXXX-<subject-in-kebab-case>`. (Increment `XXXX` based on existing directories, starting at `0001`).
2. **Draft the Document:** Write a `README.md` inside that directory. The document must include:
    * **Abstract & Context:** What was the initial idea and why was it proposed?
    * **Exploration:** The core concepts, trade-offs, and technologies discussed.
    * **Architectural Synthesis:** How the idea maps to the project's specific constraints (e.g., OKF storage, memory limits).
    * **The Verdict / Actionable Design:** The final agreed-upon architecture, including any fallback mechanisms or deployment strategies.
3. **Commit:** Ensure the file is saved and the plan is completed successfully.
