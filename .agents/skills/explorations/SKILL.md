---
name: explorations
description: Facilitate rigorous, exploratory, and constraint-aware architectural explorations with the human Architect, and meticulously document the outcomes into the project's permanent reference knowledge base. Use when users want to discuss new ideas, evaluate architectural trade-offs, or propose integrating major new dependencies (e.g., embeddings, machine learning, databases) that may affect the core constraints of the framework.
---

# Explorations Skill

A skill for conducting deep architectural brainstorming sessions, evaluating research hypotheses, and formalizing their
outcomes into permanent, self-contained **Data & Research Compendiums** in the repository's permanent reference
knowledge base (`references/explorations/`).

---

## The Exploration as a Self-Contained Compendium

An Exploration in Tur is not merely a single markdown file; it is an **immutable research compendium** that preserves
complete historical and empirical provenance.

Every exploration directory (`references/explorations/EXP-XXXX-<kebab-case>/`) MUST bundle:

1. **The Synthesized Report (`README.md`)**: The canonical analysis following the standard 5-section layout and metadata
   table.
2. **The Original Data & Source Artifacts**: Exact copies of raw conversation transcripts, downloaded research papers
   (PDF/HTML), web dumps, scraped benchmark datasets, and code prototypes studied during the exploration. These must be
   preserved in the exploration directory (or subfolders like `raw/`, `papers/`, `sources/`, `data/`) so that research
   provenance is never lost.

---

## Conducting an Exploration

### 1. Capture Intent (The Deep Planning Mode)

- Understand the core architectural question or hypothesis being investigated.
- Cross-reference against core constraints (`MANIFESTO.md`, `EP-0002-roadmap.md`, `AGENTS.md`).
- Actively protect core invariants ("The Tur Tur Principle", Policy vs. Mechanism).

### 2. Research, Interview & Data Ingestion

- Collect and preserve original source materials (e.g. download papers, save full chat transcripts, extract web
  resources).
- Challenge heavy dependencies and propose native or lightweight alternatives (e.g. ONNX instead of PyTorch, `algebrax`
  sparse tensors for pure-Python fallback, `sqlite-vec` instead of standalone vector DBs).

### 3. Exploratory Synthesis

- **Present Trade-offs:** Rigorous Pros and Cons analysis.
- **The "Escape Hatch" Pattern:** Graceful degradation from zero-dependency pure Python to hardware-accelerated extras.
- **Connect to Standards Track:** Map the exploration outcomes directly to existing or new Enhancement Proposals (EPs).

---

## Formal Compendium Structure

### 1. Dedicated Directory Structure

Create `references/explorations/EXP-XXXX-<subject-in-kebab-case>/`:

```
references/explorations/EXP-XXXX-<subject-in-kebab-case>/
├── README.md                 # Canonical synthesis and verdict
├── raw/                      # (Optional) Raw transcripts and dialogue dumps
├── papers/                   # (Optional) Downloaded research papers / PDFs / HTMLs
└── [data / source files]     # Original benchmarks, code prototypes, and referenced monographs
```

### 2. Canonical `README.md` Format

```markdown
# EXP-XXXX: [Title]

| Field           | Value                                            |
|:----------------|:-------------------------------------------------|
| **EXP**         | XXXX                                             |
| **Title**       | [Full Title]                                     |
| **Author**      | [Authors]                                        |
| **Status**      | Concluded / Active / Deferred                    |
| **Type**        | Architectural & Research Exploration             |
| **Created**     | YYYY-MM-DD                                       |
| **Updated**     | YYYY-MM-DD                                       |
| **Related EPs** | [EP-0XXX](../../docs/proposals/EP-0XXX-title.md) |

---

## 1. Abstract & Context

What was the initial question, hypothesis, or engineering need?

## 2. Exploration & Options Analysis

Core concepts, comparative evaluation of options, trade-offs, and empirical findings.

## 3. Architectural Synthesis & Constraint Alignment

How the proposal maps to Tur's specific constraints (OKF storage, memory limits, The Tur Tur Principle, Policy vs.
Mechanism).

## 4. The Verdict / Actionable Design

The agreed-upon architecture, fallback mechanisms, "Escape Hatch" patterns, or phased rollout plan.

## 5. Related Enhancement Proposals & Artifacts

Cross-references to resulting Standards-Track EPs and bundled data artifacts in this compendium.
```

### 3. Master Index Registration

Every exploration MUST be registered in [
`references/explorations/README.md`](file:///C:/dev/erivlis/tur/references/explorations/README.md) with its EXP ID,
Title, Status, Date, Resulting EPs, and Directory Link.
