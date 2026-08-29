# EXP-0002: Sensitive Data Prevention and Sanitization in Persistent Agent State

| Field       | Value                                                         |
|:------------|:--------------------------------------------------------------|
| **EXP**     | 0002                                                          |
| **Title**   | Sensitive Data Prevention and Sanitization in Persistent State|
| **Author**  | Eran Rivlis, Ariel, Jules                                     |
| **Status**  | Draft                                                         |
| **Type**    | Architectural & Philosophical Exploration                     |
| **Created** | 2026-08-29                                                    |
| **Updated** | 2026-08-29                                                    |

---

## 1. Executive Summary

As an open-source persistent state and memory management engine for AI agents, **Tur** maintains state across sessions, harnesses, and environments. This persistence introduces a critical security boundary: **How do we prevent secrets, credentials, and sensitive personal data from entering the local memory store?**

Because memory in Tur is cryptographically indexed and persistent (via content-addressable Merkle storage in L1 and relational triples in L2), leaking secrets into Tur's storage has long-term security implications. Once written to a Merkle ledger or knowledge graph, sensitive data could persist indefinitely, migrate across environments via export protocols (EP-0115), or be surfaced in future prompt context window compilations (`tur wake`).

This exploration examines the domain of sensitive data prevention, sanitization, and secrets management within Tur's **Tri-Partite Architecture** (Traveler, Harness, Terrain). It explores responsibility boundaries, threat vectors, deterministic vs. model-based sanitization mechanisms, and strategies for handling sensitive data across the memory lifecycle.

---

## 2. Context & Architectural Framing

To evaluate where and how sanitization should occur, we must ground our analysis in Tur's foundational concepts:

### 2.1 The Tri-Partite Architecture
1. **The Traveler (Tur)**: The intrinsic, portable Mind (Persona DNA, Principles, Protocols, L1 Ledger, L2 Graph).
2. **The Terrain (Workspace/Repo)**: The local physics and codebase environment.
3. **The Harness (Agent Framework/Host)**: The execution engine (Claude Code, Gemini CLI, Pi, MCP Hosts) that provides LLM inference and raw tool affordances.

### 2.2 The Policy vs. Mechanism Boundary (EP-0003)
Under **EP-0003**, Tur enforces a strict boundary:
* **Mechanism**: Deterministic computer science algorithms, integrity checks, and data structures inside `src/tur/`.
* **Policy**: User configuration, persona directives, and prompt strategies defined in `persona.yaml` or user profiles.

Any sanitization solution within Tur must respect this decoupling. Engine code must provide deterministic, high-efficiency sanitization mechanisms without hardcoding rigid assumptions about what constitutes "sensitive" data across every domain.

### 2.3 Lightweight CLI & LLM-Agnosticism Constraint
Tur is designed to be a lightweight, deterministic CLI tool and LLM-agnostic system. Core engine operations (`tur wake`, `tur learn`, `tur-mcp`) must start instantly. **Introducing heavy local Machine Learning / NLP models (e.g., PyTorch, local transformers, heavy NER pipelines) directly into core Tur dependencies is explicitly prohibited.**

---

## 3. The Threat Space & Vector Analysis

Sensitive data can enter Tur's memory ecosystem through several distinct entry points across the agent lifecycle:

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

### 3.1 Vector 1: Direct Memory Injection (`tur learn`)
An agent or human explicitly calls `tur learn "The database password for staging is hunter2"`.
* **Risk**: The secret is immediately written to an L1 OKF file with a content-addressable Merkle hash.

### 3.2 Vector 2: Session Log Dehydration (`tur sleep`)
During session termination, raw conversation logs (which may include CLI stdout, API tokens, stack traces with secret headers, or user-supplied credentials) are passed to `tur sleep` for distillation and memory extraction.
* **Risk**: High-entropy raw text passed to the dreaming/distillation pipeline might be summarized directly into long-term memories without filtering.

### 3.3 Vector 3: MCP Interaction Payloads (`tur-mcp`)
External harnesses interacting with Tur via Model Context Protocol tools (`learn`, `note`, `introspect`) pass payloads generated by the host LLM.
* **Risk**: The host LLM might accidentally copy environment variables, bearer tokens, or PII into tool invocation arguments.

### 3.4 Vector 4: L1 Merkle Immutability & Persistence
Tur's L1 memory is designed to be tamper-evident and content-addressable.
* **Risk**: If a secret is stored in L1, removing it cryptographically alters the Merkle tree root hash. Redaction requires a tombstoning or rewrite mechanism to prevent index corruption.

### 3.5 Vector 5: L2 Knowledge Graph Elevation & Epistemic Propagation
During dreaming and introspection, L1 memories are parsed into L2 semantic triples (subject-predicate-object).
* **Risk**: A secret stored in L1 could be extracted into clean, queried knowledge triples in L2 (e.g., `(StagingDB, has_password, "hunter2")`), making it even easier to inadvertently inject into future system prompts.

---

## 4. Responsibility Allocation: Where Should Sanitization Live?

A core question of this exploration is: **Who is responsible for preventing secret leakage?**

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

### 4.1 Delegation to the Harness Facilities
* **Argument FOR**: The Harness is the physical host and boundary of interaction with the external world and the LLM inference engine. It possesses context about raw tool execution (e.g., bash output, API calls). Filtering secrets before calling Tur tools ensures zero sensitive data ever crosses the socket or CLI invocation into Tur.
* **Argument AGAINST**: Harnesses vary widely (Claude Code, Gemini CLI, Cursor, custom MCP clients). Depending solely on the Harness creates a defense gap—if a minimalist or third-party Harness fails to sanitize inputs, Tur's memory becomes vulnerable.

### 4.2 Handling by Tur (Traveler Core)
* **Argument FOR**: Tur is the guardian of the agent's long-term memory. As an obligate symbiote, Tur should be self-defensive and protect its own storage regardless of which Harness it is currently attached to.
* **Argument AGAINST**: Over-burdening Tur core with complex inspection logic risks violating the **Tur Tur Principle** (keeping Tur lightweight, fast, and deterministic). Tur cannot afford heavy dependencies like local transformer models.

### 4.3 Delegation to Terrain & External Facilities
* **Argument FOR**: Environment-level tools (e.g., `git-secrets`, `trufflehog`, system keyring managers, environment variable obfuscation proxies) are specialized in secret detection and updated continuously.
* **Argument AGAINST**: Workspace/Terrain security depends on human developer setup. Relying exclusively on local pre-commit hooks or external scanners leaves unmanaged environments unprotected.

### 4.4 The Architectural Synthesis: Multi-Layered Defense-in-Depth
The optimal approach is **not** an either-or choice, but a **Defense-in-Depth Layered Model**:

1. **Layer 0 (Harness / Front Door)**: Primary responsibility for filtering raw operational inputs (CLI tools, environment variables) belongs to the Harness.
2. **Layer 1 (Tur Ingestion Engine / Sanitization Pipeline)**: Tur implements a fast, deterministic, pluggable sanitization pipeline at the ingestion boundary (`tur learn`, `tur sleep`, MCP tools) to reject or redact high-entropy patterns before writing to L1 storage.
3. **Layer 2 (Tur Policy & Gating)**: Persona-level directives and secret taxonomy policies govern what kinds of entities are permitted in L2 knowledge graph crystallization.

---

## 5. Taxonomy of Sensitive Data & Detection Strategies

Not all sensitive data is identical. A robust strategy requires categorizing data types and matching them to appropriate detection mechanisms:

| Sensitive Data Category | Examples | Detection Mechanism | Suitable Layer |
|:---|:---|:---|:---|
| **High-Entropy Secrets** | API Keys (AWS, OpenAI, GitHub), RSA Private Keys, Bearer Tokens, Passwords | High Shannon Entropy analysis + Regex Pattern Matching | Tur Core Engine (Deterministic) |
| **Known Formatted Identifiers** | Credit Cards, SSNs, JWT Tokens, Connection URIs (`postgres://user:pass@host`) | Deterministic Structural Pattern Regex | Tur Core Engine (Deterministic) |
| **Personally Identifiable Information (PII)** | Real names, personal addresses, personal phone numbers, emails | Structural Regex (emails/phones) + Optional LLM-assisted distillation policy | Tur Policy / Harness / LLM Distiller |
| **Contextual Workspace Secrets** | Internal hostnames, proprietary code snippets, customer data | Policy rules (`.turignore` / pattern filters) | Terrain Config / Tur Policy |

### 5.1 High-Entropy & Pattern Detection (Engine Mechanism)
Deterministic detection can be achieved with zero heavy dependencies via:
* **Pattern / Regex Libraries**: Matching standard formats (e.g., `sk-[a-zA-Z0-9]{32}`, `AKIA[0-9A-Z]{16}`, `ghp_[a-zA-Z0-9]{36}`).
* **Shannon Entropy Calculation**: Measuring token entropy. Standard text has predictable entropy, whereas random cryptographic keys produce high entropy scores ($H > 4.5$ bits per character).

### 5.2 Contextual / Semantic Detection (Distillation Mechanism)
Secrets embedded in natural language require semantic context. During `tur sleep` or dreaming, distillation is already performed by an LLM prompt. Sanitization instructions can be embedded directly in the **Dreaming System Prompt** to direct the LLM to strip credentials before emitting memory JSON/YAML structures.

---

## 6. Architectural Proposals & Design Strategies for Tur

Here we outline concrete architectural patterns for evaluation:

### Strategy A: Pluggable Ingestion Redaction Pipeline (Tur Mechanism)
Introduce a lightweight `SanitizerPipeline` into `src/tur/` that runs on all text inputs prior to L1 Merkle storage commit.

* **Components**:
  * `RegexRedactor`: Detects known key formats.
  * `EntropyRedactor`: Redacts strings exceeding entropy thresholds.
  * `CustomPatternRedactor`: Uses user-defined regex patterns from `.tur/config.yaml` or `persona.yaml`.
* **Behavior Options**:
  * **Redact (Default)**: Replaces matched secret with `[REDACTED_SECRET:TYPE]`.
  * **Reject**: Fails the `tur learn` call with an error indicating sensitive data was detected.
  * **Quarantine**: Stores the memory in an ephemeral, unindexed L0 staging area pending approval.

```python
# Conceptual Architecture for Mechanism
class RedactionPipeline:
    def sanitize(self, text: str) -> SanitizedResult:
        # 1. Apply deterministic regex filters
        # 2. Apply high-entropy token detectors
        # 3. Apply custom user rules (.turignore / config)
        return SanitizedResult(sanitized_text, redaction_count, detected_types)
```

### Strategy B: Ephemeral L0 Staging & Memory Quarantine
Before a memory is committed to the immutable L1 Merkle storage, it enters an **L0 Ephemeral Ledger**.

* **Lifecycle**:
  * `L0 (Ephemeral)`: Session-bound or raw intake memory.
  * **Sanitization Sweep**: Runs before crystallization.
  * `L1 (Merkle Ledger)`: Permanently committed, content-addressable memory.
* **Benefit**: Mistakes in secret detection or redactions can be corrected while in L0 without breaking L1 Merkle tree cryptographic root hashes.

### Strategy C: Storage Tombstoning & Redaction Invalidation (Merkle Handling)
If a secret escapes detection and is written to L1 Merkle storage, how does Tur handle removal?

* **Problem**: Merkle storage is content-addressable ($Hash = \text{SHA256}(Content)$). Editing content in place breaks all referencing pointers and invalidates Merkle proofs.
* **Solution**: Cryptographic Tombstoning & Re-indexing.
  * Mark the affected memory node as `tombstoned: true` in state index.
  * Replace content with redaction markers.
  * Emit a memory invalidation signal across the L2 graph to prune connected triples.
  * (Optional) Execute a `tur admin storage compact` command to rewrite the local Merkle index if hard deletion is legally/operationally required.

### Strategy D: `.turignore` File Convention (Terrain Boundary)
Following established CLI patterns (`.gitignore`, `.dockerignore`, `.aiignore`), Tur can support a `.turignore` file in the project root (Terrain).

* **Purpose**: Allows developers to define file paths, environment variables, or regex patterns that must never be ingested by `tur learn`, `tur sleep`, or MCP tools.
* **Example `.turignore`**:
  ```ini
  # Ignore specific secret files
  *.pem
  *.key
  .env*

  # Ignore regex patterns in memory text
  regex:AKIA[0-9A-Z]{16}
  regex:BEGIN (RSA|EC|DSA) PRIVATE KEY
  ```

---

## 7. Comparative Evaluation Matrix

| Strategy | Security Efficacy | Performance Impact | Complexity | Dependencies | EP Alignment |
|:---|:---|:---|:---|:---|:---|
| **Harness-Only Delegation** | Low (Vulnerable to non-conforming harnesses) | Zero (In Tur) | Minimal in Tur | None | Relies entirely on external systems |
| **Strategy A: Pluggable Regex/Entropy Redactor** | High (Catches ~95% of standard keys/passwords) | Low (< 2ms per ingest) | Low | Standard library (`re`, `math`) | Aligns with EP-0003 (Mechanism) |
| **Strategy B: Ephemeral L0 Quarantine** | Very High (Allows verification before Merkle commit) | Low | Moderate | Internal state management | Aligns with EP-0113 (Core Memory Protocol) |
| **Strategy C: Cryptographic Tombstoning** | High (Removes sensitive payload from active state) | Low | High (Merkle re-indexing) | Internal storage engine | Aligns with EP-0106 & EP-0140 |
| **Strategy D: `.turignore` File** | Moderate (Prevents file/pattern ingestion) | Minimal | Low | Native file parser | Fits Terrain isolation (EP-0124) |

---

## 8. Recommendations & Next Steps

Based on this exploration, we recommend a phased approach for Tur:

### 8.1 Short-Term Recommendations (Phase 1)
1. **Implement Strategy A (Deterministic Core Sanitizer)**: Add a lightweight, dependency-free regex and high-entropy scanner in `src/tur/` that executes during `tur learn`, `tur sleep`, and `tur-mcp`.
2. **Introduce Strategy D (`.turignore`)**: Support `.turignore` for excluding patterns and environment variables from memory ingestion.
3. **Enhance Dreaming Prompts**: Update system prompt templates used in dreaming/compaction to explicitly instruct LLMs to exclude credentials and secrets when summarizing sessions.

### 8.2 Medium-Term Recommendations (Phase 2)
1. **Formulate EP-0142 (Memory Sanitization & Secret Prevention Protocol)**: Draft a formal Enhancement Proposal translating these mechanisms into concrete engineering specifications.
2. **Define Cryptographic Tombstoning Protocol**: Formalize how L1 Merkle storage and L2 triples are tombstoned and pruned when a secret is retroactively flagged.

### 8.3 Philosophical Conclusion
Tur should adopt a **Self-Defensive Traveler Model**. While Harnesses and Terrains are encouraged to filter secrets at the edge, Tur **must not blindly trust incoming data**. By embedding fast, deterministic, zero-dependency sanitization mechanisms at the Traveler's ingestion boundary, Tur protects the longevity, safety, and sovereignty of persona memory.

---

## 9. Open Questions for Further Discussion

1. **User Overrides**: Should an Architect be able to force-store sensitive text if explicitly desired (e.g., `--allow-sensitive` flag in `tur learn`)?
2. **Redaction Telemetry**: Should Tur log when a secret is redacted, and how do we notify the active persona/harness that data was altered during ingestion?
3. **Tombstone Auditing**: Does tombstoning leave behind enough metadata for debugging while ensuring zero leakage of the original key?
