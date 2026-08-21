# Memory Taxonomy & Schema Reference

Tur implements a two-tiered federated memory architecture with strict type classifications.

## 1. L1 Memory Classifications

### Scopes (`MemoryScope`)

- **`universal` (Traveler)**: User preferences, persona identity, and general engineering principles applicable across
  all projects. Stored globally in ~~/.tur/personas/<uuid>/memories/.
- **` incarnation` (Terrain)**: Repository architecture, local dependencies, directory paths, and project-specific
  constraints. Stored locally in <project_root>/.tur/personas/<uuid>/memories/.

### Types (`MemoryType`)

- `axiom`: Permanent, immutable rules, boundary invariants, and non-negotiable constraints.
- `fact`: Objective, verifiable project states, tech stack invariants, and architecture decisions.
- `insight`: Synthesized deductions, lessons learned, and conceptual breakthroughs.
- `preference`: User directives, coding tastes, communication style, and workflow preferences.
- `core`: Foundational existential alignment axioms staged via evolve and activated via approve.

---

## 2. L2 Cognitive Map Taxonomy (Graph Introspection)

### Node Types

- $Concept$: Fundamental abstract ideas and core domain entities.
- $Decision$: Architectural choices and design commitments.
- $Constraint$: Boundary conditions, invariants, and negative rules (MUST NOT...).
- $Insight$: Lessons learned, deductions, and synthesized principles.
- $Fact$: Objective empirical states and verified observations.
- $Dependency$: Upstream prerequisites or structural couplings.
- $Hypothesis$: Active conjectures or experiments under test.
- $BoundaryNode$ / $OpenQuestion$: Perimeter definitions or unresolved inquiries.

### Edge Relations

- refines: Specializes another node of the same type.
- contradicts: Marks mutually exclusive claims or competing hypotheses.
- precedes: Indicates causal or temporal ordering between decisions or facts.
- depends_on: Explicit prerequisite dependency where node A requires node B.
- competes_with, analogy_of, superseded_by, refuted_by: Structural graph relations.
