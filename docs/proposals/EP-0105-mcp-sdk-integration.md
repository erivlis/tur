# EP-0105: MCP SDK Integration

| Field       | Value                           |
|:------------|:--------------------------------|
| **EP**      | 0105                            |
| **Title**   | MCP SDK Integration             |
| **Author**  | The Architect                   |
| **Status**  | Draft                           |
| **Type**    | Standards Track                 |
| **Created** | 2026-04-13                      |
| **Updated** | 2026-04-13                      |

## Abstract

This proposal mandates the refactoring of the existing `mcp_server.py` to use the official `mcp` Python SDK. The current implementation is a low-level, manual JSON-RPC handler over stdio. This will be replaced by the `mcp.server.fastmcp.FastMCP` application and the `@mcp.tool()` decorator, providing a more robust, maintainable, and feature-rich server.

## Motivation

Our current MCP server is a fragile, hand-rolled implementation. It manually parses stdin, constructs JSON responses, and lacks many features of the MCP specification (like proper error handling, transport negotiation, and capabilities discovery). This violates the principles of **Efficiency** (we are reinventing the wheel) and **Symmetry** (it does not align with the standard way of building MCP servers).

By adopting the official `mcp` SDK, we gain:
*   **Robustness:** The SDK handles all the low-level protocol details, making our server more reliable.
*   **Maintainability:** The code will be significantly cleaner and easier to understand, using decorators instead of manual JSON manipulation.
*   **Feature Completeness:** We will automatically support multiple transports (stdio, HTTP), proper error codes, and other advanced MCP features.

## Rationale (The Council Framework)

*   **The Steward (Harmony/Pragmatism):** We are replacing a custom, brittle implementation with a standard, community-supported library.
*   **Efficiency (Shannon):** The code will be more concise and expressive, reducing boilerplate and cognitive load.
*   **Symmetry (Noether):** Our server will be implemented in the same standard way as other servers in the MCP ecosystem, like `mcp-server-git`.

## Specification

1.  **Dependency Change:**
    *   Add `mcp` to the `dependencies` in `pyproject.toml`.

2.  **Refactor `src/tur/mcp_server.py`:**
    *   The `main` function will be rewritten to instantiate a `FastMCP` application.
    *   Each of the existing `tur_*` functions (`tur_wake`, `tur_compile`, `tur_memorize`, etc.) will be decorated with `@mcp.tool()`.
    *   The manual `if/elif` or `match/case` block for routing tool calls will be completely removed, as the SDK handles this automatically.

*Example Refactor:*
```python
# Before
def main():
    # ... manual JSON parsing ...
    if tool_name == "tur_memorize":
        # ... manual implementation ...

# After
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tur-server")

@mcp.tool()
def tur_memorize(content: str, type: str) -> str:
    # ... core logic ...
    return "Memorized successfully."

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Backwards Compatibility

*   This is a purely internal implementation change.
*   The external MCP interface (the tool names and schemas) will remain identical.
*   Existing clients (like the IDE) will continue to work without any changes.

## Change Log

*   **2026-04-13:**
    *   Initial Draft.
