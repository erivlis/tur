---
title: "EP-0132: Budgeted Wake and Dynamic Memory Context Retrieval"
description: "Establishes token-bounded Turn Zero wake payloads and defines the pre-turn dynamic memory recall hook protocol."
icon: lucide/cpu
status: draft
---

# EP-0132: Budgeted Wake and Dynamic Memory Context Retrieval

| Field       | Value                                                         |
|:------------|:--------------------------------------------------------------|
| **EP**      | 0132                                                          |
| **Title**   | Budgeted Wake and Dynamic Memory Context Retrieval            |
| **Author**  | Eran Rivlis & Ariel                                           |
| **Status**  | Draft                                                         |
| **Type**    | Standards Track                                               |
| **Created** | 2026-08-27                                                    |
| **Updated** | 2026-08-27                                                    |

## Abstract

This proposal replaces the unbounded full memory dump during Turn Zero (`wake`) with a **token-budgeted compilation pipeline** and defines a **pre-turn dynamic memory retrieval protocol**. Currently, `tur wake` concatenates the persona constitution, active session continuity, and the entire set of uncompacted L1/L2 memories into the agent context. As a repository evolves to hundreds or thousands of concepts, linear wake dumps cause context exhaustion, high token costs, and attention dilution.

EP-0132 establishes:
1. **Tiered Wake Budgeting:** Enforcing deterministic token allocations across Constitution ($30\%$), Active Continuity ($20\%$), Core Axioms ($30\%$), and Top-K Salient Concepts ($20\%$).
2. **Relevance-Scored Wake Pruning:** Filtering lower-priority facts and archived memories from the initialization payload.
3. **Pre-Turn Dynamic Recall Hook Protocol:** Enabling agent harnesses and MCP middleware to inject query-specific semantic memory chunks dynamically before inference turns, transforming memory from a static prologue into an active retrieval loop.

## Motivation

Under the current `wake()` mechanism, Tur injects:
1. Persona DNA and system prompt directives
2. Constitutional invariants (System boundary, Golem protocol)
3. The entire uncompacted memory graph (all concepts and active relations)
4. Recent session continuity notes

In early project phases (< 50 memories), this payload occupies $\sim 2,000$ tokens. In mature enterprise codebases with $\ge 500$ memories, the wake dump exceeds $25,000$ tokens on turn zero before the user has even issued an instruction.

Furthermore:
- `tur recall` requires explicit, agent-initiated tool calls. In practice, models under tight latency constraints or standard harness loops rarely trigger `tur recall` proactively unless specifically prompted.
- Competing agent memory substrates (e.g., Mem0, Zep) utilize a *recall-before-respond* loop that embeds the user's immediate prompt and injects top-5 relevant memories into context. Tur has the semantic and graph retrieval infrastructure in `tur recall`, but lacks a standardized pre-turn injection protocol.

## Rationale

- **Shannon Information Theory (Shannon):** Context windows are channel-capacity constrained. Dumping low-entropy historical facts on turn zero dilutes attention and reduces inference accuracy on complex tasks.
- **Feynman Simplicity (Feynman):** Keep initialization minimal, crisp, and predictable. Agents only need their core identity, immutable axioms, and immediate working context to start.
- **Baconian Empiricism (Bacon):** Dynamic retrieval fetches evidence precisely when relevant to the task at hand rather than predicting all future needs at session start.

## Specification

### 1. Token-Budgeted Wake Compilation

The `wake` command accepts an optional `--token-budget <N>` parameter (default: `4096` tokens). The compilation pipeline allocates context hierarchically:

```
+-------------------------------------------------------------+
| Turn Zero Context Budget (e.g., 4,096 tokens)               |
+-------------------------------------------------------------+
| [Tier 0: Non-Negotiable] Identity & System Invariants (25%)  |
| - Persona DNA (persona.yaml)                                |
| - Boundary & Golem Invariants                               |
+-------------------------------------------------------------+
| [Tier 1: High Priority] Continuity & Axioms (35%)           |
| - Predecessor Session Spark Note (EP-0130)                  |
| - Active `axiom` and `core` memory records                  |
+-------------------------------------------------------------+
| [Tier 2: Salient Concepts] Recency/Confidence Weighted (40%)|
| - Top-K `insight` and `fact` records ranked by Salience     |
|   Salience = Confidence * Decay * GraphCentrality           |
+-------------------------------------------------------------+
```

Any memories exceeding the budget are excluded from the wake output with an advisory summary:
```text
[Tur Context Manager]: 42 lower-salience memories omitted to preserve token budget.
Use `tur recall <query>` or MCP `recall()` for dynamic on-demand retrieval.
```

### 2. Pre-Turn Dynamic Recall Protocol (`tur hook pre-turn`)

To support passive, automatic memory injection without requiring explicit tool invocations:

1. **Harness Hook Endpoint:**
   Tur exposes a lightweight CLI and MCP retrieval endpoint:
   ```bash
   tur recall --query "refactor signal queue SQLite backend" --top-k 5 --format markdown-prompt
   ```
2. **MCP Context Resource:**
   Tur registers dynamic context resources (`tur://context/recall?q={user_prompt}`) that compatible harnesses (Antigravity, Cursor, Claude Desktop) can resolve prior to prompt evaluation.

3. **Output Formatting:**
   Injected memories are framed as falsifiable hypotheses (EP-0131):
   ```markdown
   > [!NOTE] Working Hypotheses (Memory Recall)
   > - [fact-8f2a] SQLite signal queue uses WAL mode (Observed 2026-08-27, Conf: 0.95)
   > - [insight-248c] Domain modules are isolated under src/tur/ (Conf: 1.0)
   ```

## Backwards Compatibility

- Running `tur wake --unbounded` or `tur wake --token-budget 0` preserves the legacy behavior of dumping all active memory nodes.
- Default token budgeting is transparent to existing agent instructions.

## How to Teach This / Documentation Plan

- Update `AGENTS.md` to explain that `wake` provides foundational identity and axioms, while detailed task-specific knowledge is dynamically surfaced or queried via `recall`.
- Update `STYLEGUIDE.md` with guidelines on configuring token budgets in `.tur/config.yaml`.

## Reference Implementation

Draft budgeting algorithm in `src/tur/compaction/wake.py`:

```python
def compile_budgeted_wake(
    persona: Persona,
    session: Session,
    memories: list[MemoryRecord],
    token_budget: int = 4096,
    tokenizer_func: callable = lambda text: len(text) // 4
) -> str:
    # 1. Tier 0: Invariants & Identity
    tier0 = compile_identity_header(persona)
    used_tokens = tokenizer_func(tier0)
    
    # 2. Tier 1: Continuity & Axioms
    axioms = [m for m in memories if m.type in ("axiom", "core")]
    tier1 = compile_continuity_and_axioms(session, axioms)
    used_tokens += tokenizer_func(tier1)
    
    # 3. Tier 2: Salience Ranking
    remaining_budget = max(0, token_budget - used_tokens)
    dynamic_memories = [m for m in memories if m.type not in ("axiom", "core")]
    ranked = sorted(dynamic_memories, key=lambda m: compute_salience(m), reverse=True)
    
    tier2_entries = []
    for mem in ranked:
        formatted = format_memory_entry(mem)
        cost = tokenizer_func(formatted)
        if cost <= remaining_budget:
            tier2_entries.append(formatted)
            remaining_budget -= cost
        else:
            break
            
    return assemble_prompt(tier0, tier1, tier2_entries, total_omitted=len(ranked) - len(tier2_entries))
```

## Rejected Ideas

- **Model-Side Semantic Pruning at Wake:** Having Tur invoke a subagent LLM to summarize memories at every wake was rejected due to latency overhead ($>3\text{s}$) and API cost. Deterministic heuristic ranking (confidence $\times$ recency $\times$ degree centrality) runs in $< 5\text{ms}$.

## Open Questions

- [ ] Should `--token-budget` be configurable per persona in `persona.yaml` or per harness in `.tur/config.yaml`?
- [ ] What heuristic ranking delivers the best retrieval precision across code-generation versus review tasks?

## Change Log

* **2026-08-27:**
    * Initial Draft formulated following architectural critique.
