---
title: "EP-0000: Tur Enhancement Proposals"
description: "The process for creating, reviewing, and implementing Tur Enhancement Proposals (EPs)."
icon: lucide/file-text
status: active
---

# EP-0000: Tur Enhancement Proposals

| Field       | Value                     |
|:------------|:--------------------------|
| **EP**      | 0000                      |
| **Title**   | Tur Enhancement Proposals |
| **Author**  | Eran Rivlis               |
| **Status**  | Active                    |
| **Type**    | Process                   |
| **Created** | 2026-02-19                |
| **Updated** | 2026-08-18                |

## Abstract

This document describes the process for creating, reviewing, and implementing Tur Enhancement Proposals (EPs). EPs are
the primary mechanism for proposing major new features, collecting community input, and documenting design decisions.

## Motivation

As Tur evolves, major architectural changes, protocol additions, and process adjustments require clear documentation and
formal review to prevent architectural drift and preserve design continuity across maintainers and AI agents.

## Rationale

To maintain the architectural integrity of Tur and adhere to the **Council Framework**, major changes require careful
consideration. EPs provide a structured way to:

1. **Falsify** ideas before implementation (Popper).
2. Ensure **Clarity** in design (Feynman).
3. Maintain a history of decisions (**Harmony**).

## Specification

### 1. The EP Workflow

1. **Draft:** The author creates a new file in `docs/proposals/` using the template.
2. **Review:** The proposal is reviewed by the maintainers (The Council).
3. **Status Change:**
    * **Accepted:** The design is approved.
    * **Rejected:** The design is flawed or misaligned.
    * **Deferred:** Good idea, but not now.
    * **Superseded:** Replaced by a newer EP.
    * **Withdrawn:** The author withdrew the proposal.
4. **Implementation:** The code is written.
5. **Final:** The feature is released.

### 2. EP Types

* **Standards Track:** New features or behavioral changes.
* **Process:** Meta-EPs (like this one) describing procedures.
* **Informational:** Design issues or general guidelines.

### 3. Template

```markdown
---
title: "EP-XXXX: Title"
description: "One-sentence summary of the proposal — used in navigation and search."
icon: lucide/<icon-name>
status: draft
---

# EP-XXXX: Title

| Field        | Value                            |
|:-------------|:---------------------------------|
| **EP**       | XXXX                             |
| **Title**    | Title                            |
| **Author**   | Author Name <author@example.com> |
| **Sponsor**  | Core Maintainer Name (Optional)  |
| **Delegate** | Council Member / Delegate Name   |
| **Status**   | Draft                            |
| **Type**     | Standards Track                  |
| **Created**  | YYYY-MM-DD                       |
| **Updated**  | YYYY-MM-DD                       |

## Abstract

Short summary of the proposal.

## Motivation

Why is this change needed? What problem does it solve?

## Rationale

Why this specific design? How does it align with the Council Framework?

## Specification

Technical details of the implementation.

## Backwards Compatibility

Does this break existing code? How will the transition be handled?

## How to Teach This / Documentation Plan

Plan for user and AI agent documentation updates.

## Reference Implementation

Link to code or pseudo-code.

## Rejected Ideas

Explicit list of alternate designs considered and why they were rejected.

## Open Questions

Outstanding items pending feedback.

## Change Log

* **YYYY-MM-DD:** Initial Draft.
```

## Backwards Compatibility

This EP establishes the formal proposal process for the Tur project. Existing informal design notes or architectural
decisions are retroactively documented or superseded by formal EPs. No breaking software changes are introduced by this
process document.

## How to Teach This / Documentation Plan

The EP process is documented in `docs/proposals/EP-0000-process.md` and indexed in `zensical.toml`. AI agents interact
with EPs using the `enhancement-proposals` skill (`.agents/skills/enhancement-proposals/`).

## Reference Implementation

- **Process Definition**: `docs/proposals/EP-0000-process.md`
- **Agent Skill & Validator**: `.agents/skills/enhancement-proposals/`

## Rejected Ideas

- **Ad-hoc issue tracking only**: Rejected in favor of version-controlled markdown proposals stored directly within
  `docs/proposals/` to maintain an immutable, offline-accessible repository history.

## Open Questions

None at this time.

## Change Log

* **2026-02-19:** Initial Draft.
* **2026-04-12:** Updated workflow and status definitions.
* **2026-08-18:** Standardized sections to align with Python PEP guidelines and automated EP validator.
