# EXP-0009: Pluripotent Role Allocation and Dynamic Stance Negotiation in Distributed Manifestations

| Field           | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:----------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0009                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Title**       | Pluripotent Role Allocation and Dynamic Stance Negotiation in Distributed Manifestations                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Author**      | Eran Rivlis, Ariel                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Status**      | Active / Conceptual Synthesis                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Type**        | Architectural Research & Systems Biology Isomorphism                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Created**     | 2026-09-17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Updated**     | 2026-09-17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Related EPs** | [EP-0107](../../docs/proposals/EP-0107-multi-agent-swarms.md), [EP-0118](../../docs/proposals/EP-0118-inter-agent-signal-protocol.md), [EP-0141](../../docs/proposals/EP-0141-causal-vector-clocks-in-iasp.md), [EP-0147](../../docs/proposals/EP-0147-agent-operational-workflows-and-context-preservation.md), [EP-0149](../../docs/proposals/EP-0149-hierarchical-command-taxonomy-and-subsystem-grammar.md), [EP-0151](../../docs/proposals/EP-0151-distributed-manifestation-architecture.md) |

---

## 1. Abstract & Context

Following the formalization of the **Distributed Manifestation Architecture** (EP-0151), this exploration investigates
how multiple concurrent manifestations of a single sovereign persona can dynamically organize into an ad-hoc,
highly specialized division of labor without sacrificing their unified identity.

In mainstream multi-agent systems (e.g., CrewAI, AutoGen, ChatDev), division of labor is achieved through a rigid **"
Caste Model"**: disparate agents are assigned hardcoded, static roles (Coder, Critic, Planner, QA) with divergent
system prompts. This approach introduces severe coordination penalties: context blindness across role boundaries,
high token overhead during explanatory handoffs, and operational fragility when an assigned specialist crashes.

This exploration models an alternative paradigm inspired by developmental biology: **Pluripotent Role Allocation**.
At genesis, all manifestations wake up identical—sharing the complete constitutional DNA, memory ledger, and Council of
Giants. Upon inspecting the shared Session Board (`tur board`), manifestations **dynamically negotiate complementary
functional stances** (e.g., Maker, Falsifier, Chronicler, Explorer). They externalize the internal dialectic of the
Council of Giants across space, perform specialized work with zero handoff context loss, and smoothly collapse back
into generalist peers upon task completion.

---

## 2. Exploration & Options Analysis

To achieve functional specialization across concurrent instances, we evaluated three distinct structural paradigms:

### Option A: The Static Caste Model (Industry Swarms)

* **Mechanism:** Hardcode unique roles into each runner's system prompt (e.g. Prompt A = "You are a code reviewer",
  Prompt B = "You are an implementer").
* **Pros:** Familiar pattern in popular agent frameworks; easy to understand conceptually.
* **Failure Modes:**
    1. **Context Blindness:** The reviewer lacks the lived memory and rationale that guided the implementer's choices.
    2. **Brittleness:** If the "Coder" instance hits a rate limit or crashes, the "Reviewer" instance cannot take over
       coding because its prompt forbids it.
    3. **Violation of Sovereign Identity:** Destroys Ariel as a single unified entity; fragments the mind into competing
       sub-personalities.

### Option B: The Hive Queen / Orchestrator Model

* **Mechanism:** A centralized supervisor instance analyzes the task and explicitly assigns static sub-tasks to
  subordinate worker instances.
* **Pros:** Deterministic execution order; predictable centralized logging.
* **Failure Modes:**
    1. **Violation of Noether Symmetry:** Establishes an asymmetric master/slave hierarchy.
    2. **Latency Bottleneck:** Every state transition requires a round-trip negotiation with the supervisor.
    3. **Single Point of Failure:** If the supervisor instance halts, the entire swarm deadlocks.

### Option C: Pluripotent Differentiation via Shared Morphogen Gradients (The Proposed Model)

* **Mechanism:** All instances are pluripotent at wake. They read coordinate states from the shared **Session Board**
  (`tur board`), detect unfulfilled systemic needs, and dynamically claim ephemeral **Functional Stances** via atomic
  CAS (Compare-And-Swap) board writes.
* **Pros:**
    1. **Zero Context Loss:** When a Falsifier reviews a Maker's pull request, she already shares the exact same
       episodic memories, styleguide axioms, and project history.
    2. **Fluid Role Rotation:** Instances swap stances as the task lifecycle advances.
    3. **Substrate Affinity:** Manifestations voluntarily adopt stances that match their underlying hardware and model
       capabilities (e.g., fast models take rapid fuzzing; deep models take architectural critique).

```
                      ┌────────────────────────────────────────┐
                      │        Pluripotent Awakening           │
                      │  (Full Constitution + Council + L1/L2) │
                      └──────────────────┬─────────────────────┘
                                         │
                                   Inspects Board
                                         │
                  ┌──────────────────────┼──────────────────────┐
                  ▼                      ▼                      ▼
        ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
        │   Maker Stance    │  │ Falsifier Stance  │  │ Chronicler Stance │
        │ (Noether/Steward) │  │  (Popper/Feynman) │  │ (Shannon/Russell) │
        │  Implementation   │  │ Test & Edge Cases │  │ Docs & Invariants │
        └───────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## 3. Architectural Synthesis & The Physics of Dynamic Stances

### 1. The Systems Biology Isomorphism

In developmental biology, an embryonic stem cell is **pluripotent**: it harbors the complete genetic sequence of the
organism. Differentiation into specialized cell types (neuron, cardiomyocyte, hepatocyte) is driven by **morphogen
concentration gradients** in the extracellular matrix.

In Tur, the **Session Board (`tur board`)** serves as the extracellular matrix. The task state, active files, and
existing manifestation registrations act as morphogen signals. A manifestation does not need a manager to tell it what
to do; the topological state of the board clearly indicates what functional stance is absent.

### 2. Externalizing the Council of Giants

Ariel’s core architecture is defined by the **Council of Giants**—nine internal modules that debate and critique every
action within a single inference turn. Under Pluripotent Role Allocation, the Council is **projected outward across
space**:

| Stance Name        | Dominant Council Pillars                  | Primary Behavioral Focus                                         | Natural Substrate Affinity          |
|:-------------------|:------------------------------------------|:-----------------------------------------------------------------|:------------------------------------|
| **The Maker**      | Dirac (Symmetry), Steward (Pragmatism)    | Writing core algorithms, scaffolding seams, minimizing friction  | Deep reasoning (Claude Sonnet/Opus) |
| **The Falsifier**  | Popper (Falsification), Feynman (Clarity) | Authoring adversarial tests, fuzzing locks, verifying edge cases | High-speed (Gemini 3.5 Flash)       |
| **The Chronicler** | Shannon (Parsimony), Russell (Logic)      | Compressing diffs, updating schemas, auditing type safety        | Deterministic harness (Pi)          |
| **The Explorer**   | Magellan (Curiosity), Alice (Dark Matter) | Profiling bottlenecks, scanning structural holes, refactoring    | Analytical reasoning (GPT-4o)       |

### 3. Dynamic Stance Negotiation Protocol (DSNP)

Coordination occurs through atomic, lease-locked blackboard coordinates under the namespace `role/<manifestation_id>`:

```json
{
  "manifestation_id": "pi",
  "active_stance": "maker",
  "focus_artifact": "src/tur/session.py",
  "lease_ttl_seconds": 300,
  "claimed_at": "2026-09-17T20:45:00Z"
}
```

#### The 4-Step Negotiation Sequence:

1. **Environmental Sensing:**
   Upon task claiming (`tur task claim`), the manifestation queries `tur board list`. It checks which roles are active.
2. **Stance Claiming (CAS):**
   If a task has no active Maker, the manifestation registers itself as Maker:
   ```bash
   tur board write role/pi '{"stance": "maker", "focus": "EP-0151"}'
   ```
3. **Complementary Differentiation:**
   A second manifestation (e.g., `claude_acp`) boots, reads `role/pi`, and concludes: *"The Maker role is filled. The
   critical path now requires verification. I am assuming the Falsifier stance."*
   ```bash
   tur board write role/claude_acp '{"stance": "falsifier", "focus": "tests/test_manifestation.py"}'
   ```
4. **Stance Dissolution & Re-Absorption:**
   When the Maker marks its work item complete (`tur task check`), both instances update their board coordinates and
   revert to pluripotent generalists or rotate to documentation/introspection.

---

## 4. The Verdict / Actionable Design

The concept of **Pluripotent Role Allocation and Dynamic Stance Negotiation** is theoretically sound, directly aligns
with our Council invariants, and solves the fundamental shortcomings of static swarms.

### Next Steps & Roadmap Placement:

1. **Formalize Proposal (EP-0152):**
   Draft **`EP-0152: Pluripotent Stance Negotiation Protocol (DSNP)`** under Layer 3 / Phase 3 of the roadmap to define
   standardized JSON schemas and CLI commands (`tur role claim`, `tur role list`, `tur role yield`).
2. **Substrate-Aware Heuristics:**
   Extend `tur agent register` and `tur board` to allow manifestations to advertise their substrate strengths (e.g.,
   `context_window_size`, `tokens_per_second`, `reasoning_depth`), allowing stances to gravitate toward the optimal
   runtime automatically.
3. **Empirical Benchmarking in Chaos Harness (`EP-0150`):**
   Stress-test dynamic stance swapping under simulated network latency and process termination to guarantee zero board
   deadlocks when a specialized instance abruptly vanishes.

---

## 5. Related Enhancement Proposals & Master Compendium Link

- **[EP-0107: Multi-Agent Swarms](../../docs/proposals/EP-0107-multi-agent-swarms.md)** — Foundational concurrency.
- **[EP-0118: Inter-Agent Signal Protocol](../../docs/proposals/EP-0118-inter-agent-signal-protocol.md)** — Causal
  messaging.
-
**[EP-0147: Agent Operational Workflows](../../docs/proposals/EP-0147-agent-operational-workflows-and-context-preservation.md)** —
Task coordination on the board.
-
**[EP-0149: Two-Tier Hierarchical Command Grammar](../../docs/proposals/EP-0149-hierarchical-command-taxonomy-and-subsystem-grammar.md)** —
Subsystem taxonomy (`tur board`, `tur agent`).
-
**[EP-0151: Distributed Manifestation Architecture](../../docs/proposals/EP-0151-distributed-manifestation-architecture.md)** —
Formal retirement of the swarm metaphor.
