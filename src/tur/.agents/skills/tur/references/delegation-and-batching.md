# Pure-Function Delegation & Ingestion Guide

When running cognitive commands (tur introspect, tur sleep, tur learn) in keyless, sandboxed, or enterprise agent
environments, Tur uses the Pure-Function Delegation Protocol.

## 1. The Delegation Flow

1. Trigger: An agent executes tur sleep or tur introspect in an environment without a direct API key.
2. Output: Tur prints a # TUR DELEGATION: {Title} prompt containing:
    - Task instructions and domain principles
    - Input data (chat logs or L1 memories)
    - Target JSON schema
    - Execution & commit contract
3. Synthesis: The external Harness evaluates the prompt locally using its own LLM context.
4. Ingestion: The computed JSON payload is fed back into Tur via the CLI.

---

## 2. Subagent Execution (Recommended)

When processing large inputs (such as complete conversation transcripts during tur sleep), the agent harness should
delegate the extraction to an isolated subagent (e.g. using invoke_subagent or a worker agent):

- Why: Keeps the main conversation context clean, unpolluted, and prevents reasoning degradation.
- Protocol: Spawn a subagent with the exact # TUR DELEGATION prompt and pass the resulting JSON back to the parent
  agent.

---

## 3. Ingestion Methods

### Single Commit

```bash
tur sleep --commit '{"memories": [{"content": "...", "type": "fact", "scope": "incarnation"}]}'
tur introspect --commit '{"nodes": [...], "edges": [...]}'
```

### Multi-Batch Ingestion (Chunking)

when extracting extensive memories from large logs, chunk payloads across multiple --commit flags:
``bash tur sleep --commit '<JSON_CHUNK_1>' --commit '<JSON_CHUNK_2>'

```

### File Glob Ingestion
Save extraction batches to local temporary files and pass a glob pattern:
```bash
tur sleep --commit 'scratch/chunks/*.json'
```

### Streaming NDJON

Pipe or pass newline-delimited JSON objects:

```bash
tur sleep --commit '{"type": "fact", "content": "Fact 1", "scope": "incarnation"}
{"type": "insight", "content": "Insight 2", "scope": "universal"}'
```
