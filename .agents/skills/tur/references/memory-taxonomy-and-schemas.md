# Memory Taxonomy & Schema Reference

Tur implements a two-tiered federated memory architecture with strict type classifications, provenance metadata, and typed skill contracts.

## 1. L1 Memory Classifications

### Scopes (`MemoryScope`)

- **`universal`** *(global)*: Universal truths shared across all projects and personas. Stored in `~/.tur/personas/<uuid>/memories/`.
- **`persona`** *(global)*: Entity values, identity axioms, and persona-wide principles. Stored in `~/.tur/personas/<uuid>/memories/`.
- **`user`** *(local)*: Architect preferences and coding style bound to the workspace terrain to avoid cross-project leakage. Stored in `<project_root>/.tur/personas/<uuid>/memories/`.
- **`incarnation`** *(local)*: Repository architecture, local dependencies, directory paths, and project-specific constraints. Stored in `<project_root>/.tur/personas/<uuid>/memories/`.

### Types (`MemoryType`)

- `fact`: Objective, verifiable project states, tech stack invariants, and established technical decisions.
- `preference`: User directives, coding tastes, communication style, and workflow preferences.
- `insight`: Synthesized deductions, lessons learned, and conceptual breakthroughs.
- `event`: Narrative history and milestone records.
- `axiom`: Permanent, immutable rules, boundary invariants, and fundamental principles.
- `core`: Foundational existential or relational alignment memories staged via `evolve` and activated via human review (`tur-adm memory approve`).

---

## 2. L2 Cognitive Map Taxonomy (Graph Introspection)

### Canonical Node Types (`NodeType`)

- `Concept`: Fundamental abstract ideas and core domain entities.
- `Decision`: Architectural choices and design commitments.
- `Constraint`: Boundary conditions, invariants, and negative rules (`MUST NOT...`).
- `Insight`: Lessons learned, deductions, and synthesized principles.
- `Fact`: Objective empirical states and verified observations.
- `Dependency`: Upstream prerequisites or structural couplings.
- `Hypothesis`: Active conjectures or experiments under test.
- `BoundaryNode` / `OpenQuestion`: Perimeter definitions or unresolved inquiries.

### Canonical Edge Relations (`EdgeType`)

- **Hierarchy**:
  - `refines`: Specializes another node of the same type (e.g., Concrete Decision $\to$ Base Decision).
- **Causality & Dependency (DAG-enforced)**:
  - `precedes`: Causal/temporal sequence between `Decision` and `Fact` nodes.
  - `depends_on`: Upstream prerequisite requirement where node A depends on node B.
- **Dialectic & Truth Maintenance (TMS)**:
  - `contradicts`: Mutually exclusive claims or competing hypotheses (resolved by timestamp).
  - `competes_with`: Competing alternatives addressing the same problem.
  - `superseded_by`: Direct supersession of an older node by a newer active node.
  - `refuted_by`: Falsification and decay propagation trace edge.
- **Cognitive Mapping**:
  - `analogy_of`: Structural isomorphism across distinct domains ($A:B :: C:D$, e.g., `merkle-dag` $\to$ `git-commit-history`).
  - `metaphor_for`: Figurative framing connecting a policy/narrative vehicle to a concrete technical mechanism (e.g., `traveler` $\to$ `persistent-persona-identity`).

### 3. Declarative Persona Extensibility

Domain personas can declare approved custom edge types in `persona.yaml`:

```yaml
compaction:
  ontology:
    custom_edge_types:
      - "cites_precedent"
      - "overrules"
```

---

## 4. Cognitive Skill Contracts (`EP-0137`)

Tur defines typed Pydantic contracts in `src/tur/contracts/` (`tur-adm contract list` / `show` / `validate`):

| Contract | Aliases | Input Schema | Output Schema | Purpose |
|:---|:---|:---|:---|:---|
| `forge` | `persona-forge`, `persona_init` | `PersonaForgeInput` | `PersonaForgeOutput` | Persona genesis, scaffolding, and constitutional crystallization. |
| `dreaming` | `dreaming-compactor`, `compactor`, `sleep` | `DreamingDeltaInput` | `DreamingDeltaOutput` | Dehydrates session notes and chat logs into L1 memories and L2 graph deltas. |
| `verification` | `codebase-verification`, `verify` | `VerificationInput` | `VerificationOutput` | Audits working memory claims against Git repository and filesystem ground truth. |
