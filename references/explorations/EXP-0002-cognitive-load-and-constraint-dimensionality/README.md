# EXP-0002: Cognitive Load Metrics & Constraint Dimensionality ($C_p$)

| Field | Value |
| :--- | :--- |
| **EXP** | 0002 |
| **Title** | Cognitive Load Metrics & Constraint Dimensionality ($C_p$) |
| **Author** | Eran Rivlis, Ariel |
| **Status** | Concluded (Implemented in Substrate) |
| **Type** | Mathematical & Epistemic Exploration |
| **Created** | 2026-01-15 |
| **Updated** | 2026-08-30 |
| **Related EPs**| [EP-0117](../../docs/proposals/EP-0117-substrate-benchmark.md), [EP-0138](../../docs/proposals/EP-0138-dynamic-epistemic-elevation-and-principle-crystallization.md) |

---

## 1. Abstract & Context

This exploration formulated the mathematical definition of **Cognitive Load ($C_p$)**, **Information Density**, and **Constraint Dimensionality** in persistent persona engineering. The goal was to establish quantitative metrics measuring how many constraints, directives, and memories an LLM can hold in its active context before experiencing reasoning degradation or instruction compliance failures.

---

## 2. Exploration & Mathematical Formulation

The exploration derived the mathematical framework for measuring the cognitive pressure on an AI persona:

### 2.1 The Cognitive Load Equation
$$C_p = \sum_{i=1}^{N} w_i \cdot \mathcal{D}_i + \alpha \cdot \log_2(1 + \mathcal{T}_{\text{active}})$$

Where:
- $w_i$: Weight of the $i$-th constitutional directive or active principle.
- $\mathcal{D}_i$: Dimensionality / operational complexity of the constraint.
- $\mathcal{T}_{\text{active}}$: Active memory token footprint.
- $\alpha$: Context scaling constant.

### 2.2 Information Density ($\rho_I$)
$$\rho_I = \frac{\mathcal{H}_{\text{semantic}}}{\mathcal{T}_{\text{tokens}}}$$

Measuring the ratio of effective semantic information (entropy) conveyed per token consumed in the system prompt.

---

## 3. Architectural Synthesis & Constraint Alignment

- **Runtime Telemetry (`tur metrics`):** Exposing quantitative $C_p$ scores directly in the CLI and MCP interfaces to alert operators when a persona is overloaded.
- **Dynamic Recalculation (`EP-0138`):** Integrating $C_p$ recalculation into the Epistemological Ladder so that elevated principles dynamically update the persona's cognitive load budget.

---

## 4. The Verdict / Actionable Design

1. Implemented in `src/tur/metrics.py` as part of the core substrate telemetry (`tur metrics`).
2. Codified into benchmark suites (`EP-0117`) to track substrate efficiency across versions.

---

## 5. Related Enhancement Proposals & Bundled Data

* **Bundled Source Artifacts:**
  - `cognitive_load.md`: Original mathematical formulation notes and draft derivations.
* **Resulting Standards Proposals:**
  - [`EP-0117: Substrate Benchmark and Performance Standards`](../../docs/proposals/EP-0117-substrate-benchmark.md)
  - [`EP-0138: Dynamic Epistemic Elevation and Principle Crystallization Lifecycle`](../../docs/proposals/EP-0138-dynamic-epistemic-elevation-and-principle-crystallization.md)
