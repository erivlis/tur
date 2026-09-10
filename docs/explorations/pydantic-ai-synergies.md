# Architecture & Integration Exploration: Pydantic AI in Tur

**Author:** AI Engineering & Architecture Exploration Team
**Target Repository:** `tur` (Persistent State & Memory Management Engine for AI Agents)
**Date:** March 2025
**Document Status:** Final Architectural Report

---

## 1. Executive Summary

### High-Level Synergy Assessment: **HIGH SYNERGY** (Architectural fit for structured outputs, workflow execution, dependency management, and deterministic testing, without violating the LLM-agnostic design invariant).

`tur` is an open-source persistent state and memory management engine for AI agents. Its design is based on two fundamental pillars:
1. **L1 Ledger & L2 Cognitive Graph Integrity:** Atomic, Merkle-hashed Open Knowledge Format (OKF) markdown files (`.tur/memories/`, `.tur/concepts/`) managed deterministically.
2. **LLM-Agnostic Engine:** Operating under a dual-mode interaction model (direct API calls via `google-genai` or host harness sampling via Model Context Protocol `/sampling`).

Adopting `pydantic-ai` (https://github.com/pydantic/pydantic-ai) presents a compelling architectural opportunity for `tur`. `pydantic-ai` is built directly on Pydantic v2 (which `tur` already depends on in `pyproject.toml:34`) and provider-agnostic abstractions. Introducing `pydantic-ai` addresses several existing pain points in `tur`:

- **Structured Output Deserialization & Extraction:** Eliminates manual JSON stripping (`_clean_json_response`), ad-hoc schema stringifying, and brittle string parsing during session dreaming and Council Introspection.
- **Workflow State Machine Simplification:** Replaces custom step-by-step subagent loop execution in the 9-stage Council Assembly with `pydantic-graph`, providing typed state transitions and built-in edge validation.
- **Dependency & State Injection:** Replaces global state lookups and environment variable reads across tools with `RunContext[Deps]`, injecting `MemoryManager`, session handles, and lock guards cleanly.
- **Test Automation & Harness Mocking:** Replaces manual monkeypatching of vendor SDK clients (`google.genai.Client`) with `pydantic-ai`'s native `TestModel` and `FunctionModel` testing utilities.

Crucially, adopting `pydantic-ai` does **not** introduce heavy deep-learning dependencies (such as PyTorch or local transformer weights) and respects the zero-overhead CLI startup invariant when configured as an optional extra (e.g. `tur[pydantic-ai]`).

---

## 2. High-Impact Use Cases

### Use Case 2.1: Type-Safe Structured Outputs & Schema Extraction

#### Target Modules & Files
- `src/tur/memory/dreaming.py:18-136`
- `src/tur/memory/introspection.py:48-323`
- `src/tur/_helpers.py:170-247`

#### Current Pattern
`tur` performs structured extraction for session epilogues ("dreaming") and L2 concept graph compilation ("introspection") by manually serializing Pydantic models to JSON schemas (`Dream.model_json_schema()`, `ExtractedGraph.model_json_schema()`) and embedding them into raw prompt strings (`src/tur/memory/dreaming.py:44-63`, `src/tur/memory/introspection.py:133-176`).

Response payloads are received as raw strings, processed with regex string stripping (`_clean_json_response` in `src/tur/_helpers.py:59-69`), parsed with `json.loads`, and validated in fallible `try/except` blocks (`src/tur/memory/introspection.py:238-249`). When no API key or MCP context exists, `require_inference` raises `HarnessDelegationError` containing delegation prompt instructions (`src/tur/_helpers.py:232-238`).

```python
# Current Pattern (src/tur/memory/dreaming.py:101-118)
prompt = build_dreaming_prompt(log_content)
resp_text = require_inference(
    prompt=prompt,
    ctx=ctx,
    task_description='session dreaming extraction',
    delegation_instructions_builder=build_delegation_instructions,
    model=model,
    response_schema=Dream.model_json_schema(),
)
resp_text = _clean_json_response(resp_text)
dream_data = json.loads(resp_text)
extracted_memories = dream_data.get('memories', [])
```

#### Proposed Pydantic AI Pattern
Define a `pydantic_ai.Agent` parametrized with `Dream` or `ExtractedGraph` as its `result_type`. `pydantic-ai` natively manages response schema validation, tool retries on validation failure, and multi-provider model normalization.

```python
# Proposed Pydantic AI Pattern
from pydantic_ai import Agent
from tur.models import Dream

dreaming_agent = Agent(
    'gemini-1.5-pro', # or any configured model provider
    result_type=Dream,
    system_prompt=(
        "Analyze the session chat log and extract durable long-term memories "
        "categorized by type, scope, and tags."
    ),
)

async def perform_sleep_dreaming_pydantic(log_content: str, deps: TurSessionDeps) -> Dream:
    result = await dreaming_agent.run(log_content, deps=deps)
    return result.data  # Guaranteed instance of Dream model
```

#### Anticipated Value
1. **Elimination of Boilerplate:** Replaces string cleaning, JSON parsing, and schema generation logic across `dreaming.py` and `introspection.py` with declarative agent result definitions.
2. **Automatic Retry on Schema Mismatch:** If an LLM returns a malformed response or invalid enum string for `MemoryType` (`src/tur/models.py:34-52`), `pydantic-ai` feeds the validation error back to the model for automated self-correction before throwing an exception.
3. **Multi-Model Provider Swapping:** Allows switching seamlessly between Gemini, OpenAI, Anthropic, or Ollama without changing response schema generation or parser code.

---

### Use Case 2.2: Agent Loops, Tool Calling & Dependency Injection (`RunContext`)

#### Target Modules & Files
- `src/tur/mcp_server.py:132-520`
- `src/tur/memory/storage.py:20-120`
- `src/tur/session.py:40-200`

#### Current Pattern
In `src/tur/mcp_server.py`, MCP tools (`learn`, `wake`, `note`, `recall`, `signal`, `read_notes`, `write_whiteboard`) access global workspace configurations, process-isolated session variables (`_active_session_id` in `mcp_server.py:48`), or execute disk writes directly after acquiring process file locks (`state_lock`). State is retrieved dynamically via function calls (`get_active_persona_id()`, `get_persona_path()`), which mixes state resolution with execution logic.

```python
# Current Pattern (src/tur/mcp_server.py:183-195)
@mcp.tool()
@mcp_contention_guard()
def learn(content: str, type: str, scope: str = 'incarnation', ...) -> str:
    active_id = get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    manager = MemoryManager(base_dir=persona_dir)
    ...
    saved_path = manager.save(memory)
    return f'Learned successfully. ID: {memory.id}'
```

#### Proposed Pydantic AI Pattern
Encapsulate runtime resources (`MemoryManager`, active persona metadata, process lock handles) inside a strongly typed dependency context class (`TurDeps`). Expose Tur operations as typed agent tools using `@agent.tool` with `RunContext[TurDeps]`.

```python
from dataclasses import dataclass
from pathlib import Path
from pydantic_ai import Agent, RunContext
from tur.memory.storage import MemoryManager
from tur.models import Memory, MemoryType, MemoryScope

@dataclass
class TurDeps:
    persona_id: str
    persona_dir: Path
    memory_manager: MemoryManager
    session_id: str

tur_agent = Agent('gemini-1.5-pro', deps_type=TurDeps)

@tur_agent.tool
async def learn_memory(
    ctx: RunContext[TurDeps],
    content: str,
    type: MemoryType,
    scope: MemoryScope = MemoryScope.INCARNATION,
) -> str:
    """Store a durable invariant into the L1 Merkle memory ledger."""
    memory = Memory(
        type=type,
        scope=scope,
        content=content,
        source_session=ctx.deps.session_id,
    )
    saved_path = ctx.deps.memory_manager.save(memory)
    return f"Learned successfully (Scope: {scope.value}). ID: {memory.id}"
```

#### Anticipated Value
1. **Clean Dependency Separation:** Eliminates reliance on process-global mutables (`_active_session_id`) and environment variables (`TUR_AGENT_ID`) within memory/tool functions.
2. **Reusability across Transports:** The same `@tur_agent.tool` functions can be exposed via stdio MCP (`FastMCP`), CLI commands (`typer`), or embedded subagents without code duplication.
3. **Type-Safe Tool Signatures:** Pydantic AI generates JSON Schema for tool parameters directly from Python type annotations and docstrings, enforcing strict type coercion (e.g. `MemoryType` StrEnum) prior to tool invocation.

---

### Use Case 2.3: Workflow & Control Flow Execution with `pydantic-graph`

#### Target Modules & Files
- `src/tur/memory/introspection.py:580-618` (`IntrospectionAssembly`)
- `src/tur/memory/introspection.py:80-575` (Subagents: `IntegrityVerifier`, `OntologyExtractor`, `TruthMaintenanceEngine`, `SymmetryValidator`, `NoveltyExplorer`, `HebbianGraphDecayer`, `BoundaryEnforcer`, `ClarityDistiller`, `GraphPruner`)

#### Current Pattern
`tur` executes its 9-stage Council Assembly introspection pipeline by iterating over a list of subagent instances in an imperative `for` loop (`src/tur/memory/introspection.py:610-616`). Each subagent receives a mutable NetworkX `DiGraph` and a generic `context: dict` dictionary, returning an updated `(graph, context)` tuple. State passing relies on dict key presence (`context['raw_memories']`, `context['commit_payload']`), making branching, conditional short-circuiting, or step-level error recoveries difficult to trace or type-check statically.

```python
# Current Pattern (src/tur/memory/introspection.py:605-617)
def execute(self, graph: nx.DiGraph, context: dict, progress_callback=None):
    total = len(self.agents)
    for i, agent in enumerate(self.agents, 1):
        desc = STAGE_DESCRIPTIONS.get(agent.name, f'Executing {agent.name}...')
        if progress_callback:
            progress_callback(i, total, desc)
        graph, context = agent.run(graph, context)
    return graph, context
```

#### Proposed Pydantic AI Pattern
Model the Council Assembly as a state graph using `pydantic-graph`. Define strongly typed state nodes (`IntegrityCheckNode`, `ExtractionNode`, `TruthMaintenanceNode`, `SymmetryValidationNode`) that return the next state node or terminal end state.

```python
from dataclasses import dataclass
from typing import Annotated
import networkx as nx
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from tur.models import Memory

@dataclass
class IntrospectionState:
    graph: nx.DiGraph
    persona_dir: Path
    memories: list[Memory] = field(default_factory=list)
    tampered: bool = False

@dataclass
class IntegrityCheckNode(BaseNode[IntrospectionState]):
    async def run(self, ctx: GraphRunContext[IntrospectionState]) -> OntologyExtractionNode | End[nx.DiGraph]:
        # Step 1: Verify Merkle integrity
        failures = MemoryManager(base_dir=ctx.state.persona_dir).verify_integrity()
        if failures:
            raise TamperedStateError("Merkle state verification failed.")
        ctx.state.memories = MemoryManager(base_dir=ctx.state.persona_dir).load_all()
        return OntologyExtractionNode()

@dataclass
class OntologyExtractionNode(BaseNode[IntrospectionState]):
    async def run(self, ctx: GraphRunContext[IntrospectionState]) -> TruthMaintenanceNode:
        # Step 2: Extract concepts and add to graph
        ...
        return TruthMaintenanceNode()

# Compile graph state machine
council_assembly_graph = Graph(
    nodes=[
        IntegrityCheckNode,
        OntologyExtractionNode,
        TruthMaintenanceNode,
        SymmetryValidationNode,
        HebbianDecayNode,
    ]
)
```

#### Anticipated Value
1. **Static State Safety:** `pydantic-graph` verifies valid transition pathways at declaration time, ensuring state nodes cannot return unexpected stages.
2. **Conditional Branching & Early Exit:** Explicit support for conditional transitions (e.g. skipping LLM extraction when no new L1 memories are pending, or halting immediately on Merkle tampering).
3. **Visualization & Inspection:** Native export of graph execution topology to Mermaid diagrams for debugging and documentation.

---

### Use Case 2.4: Deterministic Testing, Mocking & Observability

#### Target Modules & Files
- `tests/test_dreaming.py:46-73`
- `tests/test_introspection.py:30-100`
- `src/tur/metrics.py:15-80`

#### Current Pattern
Currently, testing LLM-dependent code in `tur` requires mocking raw vendor SDK clients (`google.genai.Client`) with `unittest.mock.MagicMock` (`tests/test_dreaming.py:50-62`) or triggering `HarnessDelegationError` by clearing environment variables (`tests/test_dreaming.py:76-88`). This binds tests tightly to third-party SDK internals (`mock_client.models.generate_content.return_value = ...`).

```python
# Current Pattern (tests/test_dreaming.py:50-62)
mock_client = MagicMock()
mock_response = MagicMock()
mock_response.text = '{"memories": [{"type": "fact", "content": "Pytest is fast", ...}]}'
mock_client.models.generate_content.return_value = mock_response

from google import genai
monkeypatch.setattr(genai, 'Client', lambda api_key: mock_client)
```

#### Proposed Pydantic AI Pattern
Utilize `pydantic-ai`'s built-in `TestModel` or `FunctionModel` to mock agent responses deterministically without patching global modules or external SDKs.

```python
# Proposed Pydantic AI Pattern (tests/test_dreaming.py)
from pydantic_ai.models.test import TestModel
from tur.memory.dreaming import dreaming_agent
from tur.models import Dream, ExtractedMemory, MemoryType, MemoryScope

def test_perform_sleep_dreaming_pydantic():
    # Configure deterministic response model
    test_dream = Dream(memories=[
        ExtractedMemory(type=MemoryType.FACT, content="Pytest is fast", scope=MemoryScope.INCARNATION, tags=["test"])
    ])

    with dreaming_agent.override(model=TestModel(custom_result_args=test_dream)):
        result = dreaming_agent.run_sync("User: hello")
        assert len(result.data.memories) == 1
        assert result.data.memories[0].content == "Pytest is fast"
```

Additionally, `pydantic-ai` features native integration with Logfire / OpenTelemetry. Wrapping agent execution and tool calls with Logfire provides automatic tracing for signal delivery, memory recall latency, and token consumption metrics (`src/tur/metrics.py`).

#### Anticipated Value
1. **Fast, Un-mocked Unit Tests:** Eliminates monkeypatching of `google.genai.Client` or HTTP handlers.
2. **Zero Network Calls:** Tests run entirely offline and deterministically across CI environments.
3. **Built-In OpenTelemetry Tracing:** Provides fine-grained observability into tool calls, prompt token costs, and LLM latency without writing custom tracing wrappers.

---

## 3. Architecture & Dependency Fit

### Compatibility Analysis

| Compatibility Metric | `tur` Requirement | `pydantic-ai` Specification | Compatibility Status |
| :--- | :--- | :--- | :--- |
| **Python Version** | `>=3.11` (`pyproject.toml:9`) | `>=3.10` | **Fully Compatible** |
| **Pydantic Version** | `pydantic>=2.6.0` (`pyproject.toml:34`) | `pydantic>=2.10.0` | **Fully Compatible** (Minor bump in dependency constraint) |
| **Async Runtime** | `anyio` / `asyncio` (`src/tur/mcp_server.py:10-15`) | `asyncio` / `anyio` native | **Fully Compatible** |
| **MCP Integration** | `mcp>=1.27,<2` (`pyproject.toml:42`) | Native tool calling & FastMCP synergy | **Fully Compatible** |
| **Execution Engine Invariant**| Lightweight, deterministic CLI | Zero heavy DL frameworks (No PyTorch/Transformers) | **Fully Compatible** |

### Potential Friction Points & Mitigation Strategies

1. **Async vs Sync Call Inconsistencies:**
   - *Friction:* Some `tur` CLI entrypoints in `src/tur/cli/agent.py` are synchronous Typer commands that wrap async code using `run_async()` in `src/tur/_helpers.py:22-38`.
   - *Mitigation:* `pydantic-ai` provides synchronous execution helpers (`agent.run_sync()`) alongside its async core (`await agent.run()`), preventing event loop collisions when called from Typer CLI commands.

2. **Dual-Mode Agnostic Harness Interaction Protocol (Harness Delegation):**
   - *Friction:* When no LLM API key or MCP context is available, `tur` relies on raising `HarnessDelegationError` containing formatted markdown prompt instructions (`src/tur/_helpers.py:232-238`) so external harnesses (e.g. Claude Code, Antigravity) can perform inference.
   - *Mitigation:* Retain `HarnessDelegationError` as a fallback model provider inside `pydantic-ai`. Custom `pydantic_ai.models.Model` subclassing allows trapping unconfigured provider states and throwing `HarnessDelegationError` with structured delegation prompts.

3. **Dependency Footprint Management:**
   - *Friction:* Adding `pydantic-ai` as a mandatory core dependency adds sub-dependencies (e.g. `griffe`, `httpx`).
   - *Mitigation:* Package `pydantic-ai` as an optional dependency extra in `pyproject.toml` under `[project.optional-dependencies]`:
     ```toml
     [project.optional-dependencies]
     pydantic-ai = [
         "pydantic-ai>=0.0.30",
     ]
     ```

---

## 4. Feasibility & Risk Assessment

### Feasibility Score: **HIGH (8.5 / 10)**

| Consideration Category | Assessment & Trade-Offs |
| :--- | :--- |
| **Code Refactoring Risk** | **Low:** `tur`'s core storage (`MemoryManager`), data models (`models.py`), and Merkle hashing logic remain completely untouched. Integration is localized to inference & extraction boundaries (`_helpers.py`, `dreaming.py`, `introspection.py`). |
| **Runtime Performance** | **Neutral/Positive:** Pydantic v2 core validation in `pydantic-ai` is implemented in Rust, offering equal or superior deserialization performance compared to custom Python JSON/regex stripping. |
| **Maintainability** | **High Improvement:** Eliminates ~200 lines of brittle regex stripping (`_clean_json_response`), ad-hoc schema generation, and manual vendor SDK mocks across tests. |
| **Vendor Lock-In** | **Zero Lock-In:** `pydantic-ai` supports Gemini, OpenAI, Anthropic, Groq, Ollama, and custom provider endpoints out of the box. |

---

## 5. Recommended Next Steps

If the team decides to pilot `pydantic-ai` within `tur`, the following phased proof-of-concept (PoC) roadmap is recommended:

```
Phase 1: Foundation & Optional Extra Setup
  └── Add `pydantic-ai` as optional extra in `pyproject.toml` (`pydantic-ai` optional dependency group)
  └── Implement `TestModel` testing harness in `tests/test_dreaming.py`

Phase 2: Structured Output Pilot (Session Epilogue Dreaming)
  └── Refactor `src/tur/memory/dreaming.py` to use `Agent[None, Dream]`
  └── Implement `HarnessDelegationError` fallback model for unconfigured environments
  └── Verify offline test suite passing with `uv run pytest`

Phase 3: Council Introspection & Graph Compilation Pilot
  └── Replace manual graph extraction in `src/tur/memory/introspection.py` (`OntologyExtractor`) with `Agent[None, ExtractedGraph]`
  └── Pilot `pydantic-graph` for the 9-stage `IntrospectionAssembly` pipeline

Phase 4: Tool Calling & Observability Integration
  └── Wrap MCP server tool handlers in `src/tur/mcp_server.py` with `@agent.tool` & `RunContext[TurDeps]`
  └── Optional: Add Logfire/OpenTelemetry tracing integration for token cost tracking in `src/tur/metrics.py`
```

---
*Report compiled autonomously by AI Architecture Exploration Agent for the `tur` codebase.*
