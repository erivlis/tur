# AI Tools Protocol

This document defines standard, executable one-liners for AI Agents to verify objective facts (Time, Math) instead of
hallucinating them.

## Usage Directive

When an Agent needs to perform a calculation or state the time, it should:

1. **Not Guess.**
2. **Propose** the command from this list.
3. **Wait** for the user to run it (or run it if the environment permits).

## Tools

### 1. Chronos (Time)

**Goal:** Get a rigorous ISO-8601 timestamp.
**Command:**

```shell
python -c "import datetime; print(datetime.datetime.now().isoformat())"
```

### 2. Abacus (Simple Arithmetic)

**Goal:** Verify basic arithmetic to avoid token-prediction errors.
**Command:**

```shell
python -c "print({expression})"
```

*Example:* `python -c "print(123 * 456)"`

### 3. Calculator (Advanced Math)

**Goal:** Perform complex calculations (trig, log, exp) using the `math` module.
**Command:**

```shell
python -c "import math; print({expression})"
```

*Example:* `python -c "import math; print(math.sqrt(2) * math.pi)"`

### 4. Randomness (Entropy)

**Goal:** Generate a random seed or UUID.
**Command:**

```shell
python -c "import uuid; print(uuid.uuid4())"
```

### 5. Resource to Markdown

uses https://github.com/microsoft/markitdown

**Goal:** Convert a resource to Markdown format.
**Command:**

```shell
uvx --from 'markitdown[pdf]' markitdown {input_pdf} -o {output_md}
```
### 5. Code Search

Use `semble search` to find code by describing what it does or naming a symbol/identifier, instead of grep:

```shell
semble search "authentication flow" ./my-project
semble search "save_pretrained" ./my-project
semble search "save model to disk" ./my-project --top-k 10
```

The index is built on first run (and cached for subsequent runs) and invalidated automatically when files change.

Use `--content docs` to search documentation and prose, `--content config` for config files (yaml, toml, etc.), or `--content all` to search code, docs, and config:

```shell
semble search "deployment guide" ./my-project --content docs
semble search "database host port" ./my-project --content config
semble search "authentication" ./my-project --content all
```

Use `semble find-related` to discover code similar to a known location (pass `file_path` and `line` from a prior search result):

```shell
semble find-related src/auth.py 42 ./my-project
```

`path` defaults to the current directory when omitted; git URLs are accepted.

If `semble` is not on `$PATH`, use `uvx --from "semble[mcp]" semble` in its place.

#### Workflow

1. Start with `semble search` to find relevant chunks. The index is built and cached automatically.
2. Use `--content docs` for documentation, `--content config` for config files, or `--content all` for everything.
3. Inspect full files only when the returned chunk does not give enough context.
4. Optionally use `semble find-related` with a promising result's `file_path` and `line` to discover related implementations.
5. Use grep only when you need exhaustive literal matches or quick confirmation of an exact string.