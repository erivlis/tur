# EXP-0005: Mathematical & Graph-Theoretic Codebase Audit

| Field | Value |
| :--- | :--- |
| **EXP** | 0005 |
| **Title** | Mathematical & Graph-Theoretic Codebase Audit |
| **Author** | Eran Rivlis, Ariel |
| **Status** | Concluded (Draft EPs Authored) |
| **Type** | Code Audit & Systems Exploration |
| **Created** | 2026-08-28 |
| **Updated** | 2026-08-30 |
| **Related EPs**| [EP-0140](../../docs/proposals/EP-0140-substrate-acceleration-and-merkle-invalidation-caching.md), [EP-0141](../../docs/proposals/EP-0141-causal-vector-clocks-in-iasp.md), [EP-0142](../../docs/proposals/EP-0142-progressive-execution-observability-and-streaming-telemetry.md) |

---

## 1. Abstract & Context

Following the conceptual breakthroughs of `EXP-0004`, this exploration executed a rigorous, 5-part line-by-line audit across `src/tur/` to identify concrete implementation bottlenecks, non-EP code paths, race conditions, and performance gaps.

---

## 2. Exploration & Audit Findings

The audit analyzed every module in the repository and identified critical engineering gaps:

1. **Part 1 (`01_codebase_inventory_and_quick_wins.md`):** Complete structural inventory of symbols, functions, and test coverage across `src/tur/`.
2. **Part 2 (`02_graph_theoretic_retrieval_and_observability_audit.md`):** Analysis of `recall.py` and `introspection.py` identifying lack of HippoRAG graph traversal and fragile Mermaid string parsing.
3. **Part 3 (`03_higher_algebra_provenance_and_tensor_readiness_audit.md`):** Integration readiness for `algebrax` 3D tensors and Betti void detection.
4. **Part 4 (`04_comprehensive_audit_blueprint_and_ep_recommendations.md`):** Master recommendations matrix.
5. **Part 5 (`05_non_ep_code_paths_and_architectural_gaps.md`):** Discovered 3 major un-EP'd substrate bottlenecks:
   - File I/O storm on `load_all()` in `src/tur/memory.py` ($150\text{ms}+$ latency per turn).
   - Linear autoincrement integer clocks in IASP SQLite table vulnerable to concurrency race conditions.
   - Synchronous, silent execution blocks during `tur sleep` and `tur introspect`.

---

## 3. Architectural Synthesis & Constraint Alignment

- Addressed the file I/O storm via an in-memory $\mathcal{O}(1)$ Merkle Invalidation Cache.
- Upgraded IASP SQLite signals to Lamport Vector Clocks ($\mathbf{V} \in \mathbb{N}^k$) to establish formal partial ordering.
- Replaced blocking CLI commands with Rich live status spinners and MCP streaming progress telemetry.

---

## 4. The Verdict / Actionable Design

The unencapsulated audit findings were formalized into **3 Standards-Track Enhancement Proposals**:
- `EP-0140` (Substrate Acceleration, Merkle Invalidation Caching, Jittered Lock Backoff)
- `EP-0141` (Lamport Vector Clocks and Causal Consistency in IASP)
- `EP-0142` (Progressive Execution Observability and Streaming Telemetry)

---

## 5. Related Enhancement Proposals & Bundled Data

* **Bundled Source Audit Reports:**
  - `01_codebase_inventory_and_quick_wins.md`
  - `02_graph_theoretic_retrieval_and_observability_audit.md`
  - `03_higher_algebra_provenance_and_tensor_readiness_audit.md`
  - `04_comprehensive_audit_blueprint_and_ep_recommendations.md`
  - `05_non_ep_code_paths_and_architectural_gaps.md`
* **Resulting Standards Proposals:**
  - [`EP-0140: Substrate Acceleration, Merkle Invalidation Caching, and Jittered Lock Backoff`](../../docs/proposals/EP-0140-substrate-acceleration-and-merkle-invalidation-caching.md)
  - [`EP-0141: Lamport Vector Clocks and Causal Consistency in Inter-Agent Signal Protocol`](../../docs/proposals/EP-0141-causal-vector-clocks-in-iasp.md)
  - [`EP-0142: Progressive Execution Observability, Live Status Spinners, and Streaming MCP Telemetry`](../../docs/proposals/EP-0142-progressive-execution-observability-and-streaming-telemetry.md)
