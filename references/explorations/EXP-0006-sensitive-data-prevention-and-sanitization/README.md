# EXP-0006: Sensitive Data Prevention and Sanitization in Persistent Agent State

| Field | Value |
| :--- | :--- |
| **EXP** | 0006 |
| **Title** | Sensitive Data Prevention and Sanitization in Persistent State |
| **Author** | Eran Rivlis, Ariel, Jules |
| **Status** | Concluded (Draft EP Authored) |
| **Type** | Architectural & Security Exploration |
| **Created** | 2026-08-29 |
| **Updated** | 2026-08-30 |
| **Related EPs**| [EP-0003](../../docs/proposals/EP-0003-policy-vs-mechanism.md), [EP-0116](../../docs/proposals/EP-0116-split-cli.md), [EP-0143](../../docs/proposals/EP-0143-sensitive-data-prevention-and-sanitization.md) |

---

## 1. Abstract & Context

As an open-source persistent state and memory management engine for AI agents, **Tur** maintains state across sessions, harnesses, and environments. This persistence introduces a critical security boundary: **How do we prevent secrets, credentials, and sensitive personal data from entering the local memory store?**

Because memory in Tur is cryptographically indexed and persistent (via content-addressable Merkle storage in L1 and relational triples in L2), leaking secrets into Tur's storage has long-term security implications. Once written to a Merkle ledger or knowledge graph, sensitive data could persist indefinitely, migrate across environments via export protocols (`EP-0115`), or be surfaced in future prompt context window compilations (`tur wake`).

This exploration examines sensitive data prevention, sanitization, and secrets management within Tur's **Tri-Partite Architecture** (Traveler, Harness, Terrain), exploring responsibility boundaries, threat vectors, deterministic vs. model-based sanitization mechanisms, and strategies for handling sensitive data across the memory lifecycle.

---

## 2. Exploration & Threat Vector Analysis

Sensitive data can enter Tur's memory ecosystem through five distinct entry points:

```
                          ┌────────────────────────┐
                          │     External World     │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │     Harness Layer      │  ◄── Vector 1: Raw Prompt / Chat Logs
                          └───────────┬────────────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               ▼                      ▼                      ▼
    ┌────────────────────┐  ┌───────────────────┐  ┌───────────────────┐
    │     tur learn      │  │     tur sleep     │  │      tur-mcp      │
    │  (Direct Ingest)   │  │ (Session Digest)  │  │ (Tool Call / State│
    └──────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
               │                      │                      │
               │  Vector 2            │  Vector 3            │  Vector 4
               └──────────────────────┼──────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │   L1 Merkle Ledger     │
                          └───────────┬────────────┘
                                      │
                                      ▼  Vector 5: Dreaming / Epistemic Elevation
                          ┌────────────────────────┐
                          │   L2 Knowledge Graph   │
                          └────────────────────────┘
```

1. **Vector 1 (Direct Memory Injection - `tur learn`):** Explicit calls containing credentials.
2. **Vector 2 (Session Log Dehydration - `tur sleep`):** Raw conversation logs containing tool outputs, stack traces, and environment variables.
3. **Vector 3 (MCP Interaction Payloads - `tur-mcp`):** Host LLMs inadvertently passing secrets into tool arguments.
4. **Vector 4 (L1 Merkle Immutability):** Tamper-evident storage making retroactive secret removal non-trivial.
5. **Vector 5 (L2 Knowledge Graph Elevation):** Introspection crystallizing secrets into clean subject-predicate-object triples.

---

## 3. Architectural Synthesis & Defense-in-Depth

```
+-----------------------------------------------------------------------+
|                       Sanitization Responsibility                     |
+-----------------------------------+-----------------------------------+
|  Upstream / Exterior              |  Engine / Interior                |
|  - Harness (Agent Framework)      |  - Tur Core Engine                |
|  - Terrain (Workspace / Hooks)    |  - Pluggable Policy Redactors     |
|  - Proxy / Network Gateways       |  - Ephemeral L0 Quarantine        |
+-----------------------------------+-----------------------------------+
```

Tur adopts a **Self-Defensive Traveler Model**: while harnesses are encouraged to filter secrets at the edge, Tur **must not blindly trust incoming data**.

### Detection Strategy Taxonomy:
* **High-Entropy Secrets (API Keys, Private Keys):** Shannon entropy analysis ($\mathcal{H} > 4.5\text{ bits/char}$) + regex pattern matching. Zero dependencies.
* **Formatted Identifiers (JWTs, URIs, Tokens):** Deterministic structural regex matching.
* **Semantic Credentials:** Negative elicitation directives in dreaming system prompts instructing LLMs to exclude credentials.

---

## 4. The Verdict / Actionable Design

The consensus established a 3-part implementation architecture formalized in **EP-0143**:

1. **Deterministic Core Ingestion Filter (`src/tur/sanitizer.py`):** Pure-Python regex and Shannon entropy scanner executing before disk writes on `tur learn`, `tur sleep`, and `tur-mcp`.
2. **Prompt-Layer Negative Elicitation (`src/tur/dreaming.py`):** Explicit distillation constraints.
3. **Merkle Tombstone Redaction CLI (`tur-adm memory redact <hash>`):** Retroactive secret purging replacing content with deterministic tombstones (`[TOMBSTONE: REDACTED DUE TO SECURITY POLICY]`) without breaking graph backlinks.

---

## 5. Related Enhancement Proposals

* [`EP-0003: Policy vs. Mechanism Decoupling`](../../docs/proposals/EP-0003-policy-vs-mechanism.md)
* [`EP-0106: Merkle Memory Architecture`](../../docs/proposals/EP-0106-merkle-memory.md)
* [`EP-0115: Traveler Export Protocol`](../../docs/proposals/EP-0115-traveler-export-protocol.md)
* [`EP-0116: The Tri-Partite CLI Security Boundary`](../../docs/proposals/EP-0116-split-cli.md)
* [`EP-0143: Sensitive Data Prevention, Secret Redaction, and Memory Sanitization`](../../docs/proposals/EP-0143-sensitive-data-prevention-and-sanitization.md)
