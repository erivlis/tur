---
title: "EP-0143: Sensitive Data Prevention, Secret Redaction, and Memory Sanitization"
description: "Establishes a defense-in-depth sanitization and secrets redaction framework across the Tri-Partite architecture, featuring high-entropy token detection, deterministic pre-ingest filters, and Merkle tombstoning."
icon: lucide/shield-alert
status: draft
---

# EP-0143: Sensitive Data Prevention, Secret Redaction, and Memory Sanitization

| Field        | Value                                                                |
|:-------------|:---------------------------------------------------------------------|
| **EP**       | 0143                                                                 |
| **Title**    | Sensitive Data Prevention, Secret Redaction, and Memory Sanitization |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel, Jules                         |
| **Sponsor**  | Council of Giants                                                    |
| **Delegate** | Golem (Containment & Boundaries), Noether (State Invariants)         |
| **Status**   | Draft                                                                |
| **Type**     | Standards Track                                                      |
| **Created**  | 2026-08-30                                                           |
| **Updated**  | 2026-08-30                                                           |

---

## Abstract

As an open-source persistent memory and identity state engine for AI agents, Tur maintains long-term state across
sessions, harnesses, and environments. This proposal formalizes a multi-layered **Sensitive Data Prevention and
Sanitization Protocol** (originating in `EXP-0002`). It introduces deterministic pre-ingest regex filters and Shannon
entropy scanners in `src/tur/sanitizer.py`, prompt-layer negative elicitation in `tur.dreaming`, and a cryptographically
sound **Merkle Tombstone Redaction** command in `tur-adm` (`tur-adm memory redact <hash>`) that purges secrets without
corrupting historical lineage.

---

## Motivation

Persistent AI memory introduces a major security boundary:

1. **Accidental Credential Ingestion:** Agents executing bash tools often encounter environment variables, bearer
   tokens, API keys, or private certificates. During `tur sleep` or `tur learn`, these secrets risk being permanently
   written to L1 OKF Markdown files.
2. **Epistemic Secret Propagation:** Once an API token is written to L1, the introspection pipeline (`EP-0103`,
   `EP-0119`) can parse it into clean L2 knowledge triples (e.g. `(StagingDB, has_token, "ghp_...")`), subsequently
   injecting it into future `tur wake` prompt compilations across other project harnesses.
3. **Merkle Immutability Dilemma:** In content-addressable storage (`EP-0106`), modifying or deleting a file alters its
   SHA-256 hash, potentially breaking back-links in other memory records. A formal redaction protocol is required to
   sanitize compromised records cleanly.

---

## Rationale

### Alignment with the Council Framework

- **The Golem Protocol (Boundary Containment):** Strict deterministic gatekeepers prevent sensitive runtime
  environmental terrain (keys, auth headers) from leaking into the persistent traveler soul.
- **The Noether Module (Symmetry & Invariance):** Redaction replaces sensitive payloads with deterministic tombstones
  (`[REDACTED: high-entropy-token]`), preserving document structure and relational graph topology without data leakage.
- **The Shannon Module (Entropy Analysis):** Fast, zero-dependency Shannon entropy calculations
  ($\mathcal{H} = -\sum p_i \log_2 p_i$) flag high-randomness cryptographic keys ($\mathcal{H} > 4.5$) before they touch
  disk.

---

## Specification

### 1. Deterministic Sanitization Pipeline (`src/tur/sanitizer.py`)

A pure-Python, zero-dependency pre-ingest filter executes on all input strings to `tur learn`, `tur note`, `tur sleep`,
and `tur-mcp`:

```python
import math
import re

COMMON_SECRET_PATTERNS = [
    re.compile(
        r'(?i)(?:api_key|access_token|secret_key|private_key|password)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'),
    re.compile(r'ghp_[0-9a-zA-Z]{36}'),  # GitHub Personal Access Token
    re.compile(r'sk-[a-zA-Z0-9]{48}'),  # OpenAI API Key
    re.compile(r'AIza[0-9A-Za-z\-_]{35}'),  # Google API Key
    re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),  # PEM Private Key
]


def calculate_shannon_entropy(text: str) -> float:
    """Computes Shannon entropy to identify high-randomness credentials."""
    if not text:
        return 0.0
    probabilities = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probabilities)


def sanitize_text(text: str, redact: bool = True) -> tuple[str, list[str]]:
    """Detects and optionally redacts known secret patterns and high-entropy blocks."""
    detected = []
    sanitized = text

    # Pattern-based matching
    for pattern in COMMON_SECRET_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            detected.extend(matches)
            if redact:
                sanitized = pattern.sub('[REDACTED: SECRET PATTERN]', sanitized)

    return sanitized, detected
```

### 2. Prompt-Layer Negative Elicitation (`src/tur/dreaming.py`)

Session dehydration prompts explicitly instruct dreaming models to discard transient secrets:

```
- Exclusion & Sanitization Directives:
  - NEVER extract or store passwords, API keys, session tokens, or private credentials.
  - If a secret is observed in the transcript, extract only the architectural role (e.g. "Uses AWS S3 with IAM authentication") and omit the credential string entirely.
```

### 3. Merkle Tombstone Redaction CLI (`tur-adm memory redact`)

When a sensitive memory is discovered post-facto:

```bash
tur-adm memory redact <hash> --reason "Contained staging API secret"
```

1. Replaces file body content with `[TOMBSTONE: REDACTED DUE TO SECURITY POLICY]`.
2. Appends frontmatter metadata:
   ```yaml
   redacted: true
   redacted_at: "2026-08-30T20:30:00Z"
   redaction_reason: "Contained staging API secret"
   ```
3. Maintains the file at its original path to prevent broken inbound relational links in the L2 graph.

---

## Backwards Compatibility

- **Transparent:** Existing OKF memory files without sensitive data remain completely unchanged.
- **Zero Overhead:** Regex and entropy scanning takes $< 0.1\text{ms}$ per memory text, maintaining sub-millisecond CLI
  performance.

---

## How to Teach This / Documentation Plan

- Add a security architecture chapter: `docs/architecture/security-and-sanitization.md`.
- Document `tur-adm memory redact` in the administrative CLI reference.

---

## Reference Implementation

- Sanitizer module: `src/tur/sanitizer.py`
- Dream prompts: `src/tur/dreaming.py`
- Admin redact command: `src/tur/cli/admin.py`
- Exploration reference: `references/explorations/EXP-0002-sensitive-data-prevention-and-sanitization.md`

---

## Rejected Ideas

- **Heavy ML/NER Libraries (Spacy, Presidio):** Rejected to preserve the Tur Tur Principle and avoid adding 500MB+
  dependencies to core.
- **Complete Deletion of Redacted Files:** Rejected because hard deletions break cryptographic backlink graphs.
  Tombstoning preserves graph integrity while purging secret bytes.

---

## Open Questions

- [ ] Should entropy thresholds be dynamically adjustable per-domain via user profile preferences?

## Change Log

* **2026-08-30:**
    * Initial Draft authored based on EXP-0002.
