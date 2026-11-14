---
name: dreaming
description: Session compaction and memory delta synthesis skill for Tur (EP-0137). Extracts durable invariants into DreamingDeltaOutput payloads.
---

# Dreaming Compactor Skill

This cognitive skill guides autonomous agents, subagents, and compaction workers in digesting chronological session logs and scratchpad notes into durable L1 memory deltas, supersessions, and TMS refutations.

---

## 🛡️ Symmetrical Isolation & Policy Decoupling

Per **EP-0003 (Policy vs. Mechanism)** and **EP-0137 (Contract-Driven Cognitive Skills)**, Tur's state kernel handles Merkle hashing, atomic persistence, and file locking, while this skill executes cognitive memory extraction, deduplication, and truth maintenance.

**Boundary Invariant:** Never edit `.tur/` memory files directly. Ingest all extracted memory deltas via:
```bash
tur sleep --commit '<JSON_PAYLOAD>' -n "Session dehydration complete."
```

---

## 🧠 Memory Extraction Principles & Taxonomy

### Scopes:
- `universal`: User preferences, general engineering axioms, and foundational truths applicable across all projects.
- `incarnation`: Project-specific architectural constraints, repository states, and local decisions.
- `persona`: Relational coordinates and self-identity axioms.
- `user`: Architect tastes and personal style guides.

### Types:
- `axiom`: Permanent, immutable rules, boundary invariants, and fundamental principles.
- `fact`: Verifiable project states, dependencies, and established technical decisions.
- `insight`: High-leverage deductions, lessons learned, and conceptual breakthroughs.
- `preference`: User directives, coding tastes, communication style, and workflow preferences.

### Exclusion Directives (Signal over Noise):
- Do NOT extract transient engineering steps, temporary debug logs, or resolved syntax errors.
- **NEVER** extract passwords, API keys, private tokens, or credentials.

---

## 🎯 Target Output Schema (`DreamingDeltaOutput`)

```json
{
  "epilogue": "Decomposed monolith main.py into domain modules and authored EPs for memory provenance.",
  "added_memories": [
    {
      "type": "fact",
      "scope": "incarnation",
      "content": "Decomposed monolith main.py into isolated domain modules under src/tur/.",
      "confidence": 1.0,
      "tags": ["architecture", "refactoring"]
    }
  ],
  "superseded_memories": [
    {
      "superseded_id": "concept-104e77a1",
      "superseding_id": "concept-ccf1b8ee",
      "reason": "Refactored monolithic main.py into isolated domain modules."
    }
  ],
  "tms_refutations": [],
  "staged_core_memories": []
}
```

---

## 🚀 Execution & Commit

### A. Single Commit
```bash
tur sleep --commit '<JSON_PAYLOAD>' -n "Epilogue summary"
```

### B. Validation
```bash
tur-adm contract validate dreaming delta.json
```
