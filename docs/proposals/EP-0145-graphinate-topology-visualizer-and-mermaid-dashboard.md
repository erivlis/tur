---
title: "EP-0145: Declarative Knowledge Graph Modeling, Interactive Dashboard, and Mermaid Visualization"
description: "Integrates networkx-mermaid for robust L2 subgraph rendering and graphinate under tur-adm for interactive browser-based persona topology inspection and GraphQL exploration."
icon: lucide/network
status: draft
---

# EP-0145: Declarative Knowledge Graph Modeling, Interactive Dashboard, and Mermaid Visualization

| Field        | Value                                                                                  |
|:-------------|:---------------------------------------------------------------------------------------|
| **EP**       | 0145                                                                                   |
| **Title**    | Declarative Knowledge Graph Modeling, Interactive Dashboard, and Mermaid Visualization |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Ariel                                                  |
| **Sponsor**  | Council of Giants                                                                      |
| **Delegate** | Shannon (Visual Information Density), Russell (Declarative Models)                     |
| **Status**   | Draft                                                                                  |
| **Type**     | Standards Track                                                                        |
| **Created**  | 2026-08-30                                                                             |
| **Updated**  | 2026-08-30                                                                             |

---

## Abstract

This proposal integrates **`networkx-mermaid`** and **`graphinate`** into the Tur framework to elevate graph modeling
and observability. In the core agent runtime (`tur`), `networkx-mermaid` replaces hand-rolled string formatting with
robust, schema-verified NetworkX-to-Mermaid compilation for L2 subgraphs and prompt injection. In the human
administrative interface (`tur-adm`), `graphinate` is integrated under the optional `tur-adm[gui]` extra to power an
interactive browser-based dashboard (`tur-adm graph serve`) and GraphQL exploration interface over the persona's
epistemic memory map.

---

## Motivation

1. **Fragile Hand-Rolled Mermaid Generation:** Currently, `src/tur/introspection/__init__.py` and `recall.py` format
   Mermaid diagrams using ad-hoc string concatenation. When memory nodes contain quotation marks, parentheses, or
   punctuation, Mermaid parsers crash.
2. **Lack of Visual Persona Observability:** While `tur status` provides tabular CLI summaries, human developers cannot
   interactively visualize community clusters (Louvain), cognitive bridges, or truth-maintenance contradiction chains in
   a graphical browser UI.
3. **Core Bloat Prevention:** Adding web GUI and visualization servers directly into `tur` would violate the **Tur Tur
   Principle** (lightweight CLI). Visualization must be cleanly quarantined to administrative extras.

---

## Rationale

### Alignment with the Council Framework

- **The Shannon Module (Visual Representation):** Graph topologies convey structural cognitive relationships at vastly
  higher bandwidth than tabular text.
- **The Golem Protocol (Boundary Containment):** Visual web servers and GUI rendering dependencies are physically
  confined to `tur-adm[gui]`, ensuring the core agent CLI (`tur`) and MCP server (`tur-mcp`) remain ultra-lightweight.
- **The Russell Module (Declarative Contracts):** `graphinate` introduces declarative graph builders, eliminating
  imperative state mutations in graph construction.

---

## Specification

### 1. Robust Subgraph Mermaid Formatting in Core (`networkx-mermaid`)

In `src/tur/recall.py` and `src/tur/introspection.py`:

```python
from networkx_mermaid import to_mermaid


def render_cognitive_subgraph(subgraph: nx.DiGraph) -> str:
    """Renders a bounded ego-subgraph or Louvain community into Mermaid syntax."""
    return to_mermaid(
        subgraph,
        direction="TD",
        node_label_attr="content",
        edge_label_attr="relation",
    )
```

### 2. Interactive Graph Dashboard in `tur-adm` (`graphinate`)

Under `src/tur/cli/admin.py`:

```bash
# Launch interactive local browser visualization
tur-adm graph serve --port 8080

# Export static visual representations
tur-adm graph export --format mermaid --output docs/knowledge-map.md
tur-adm graph export --format html --output docs/graph.html
```

```python
# In src/tur/cli/admin.py:
@graph_app.command()
def serve(
        port: int = typer.Option(8080, help="Port to bind the visual graph server."),
        identifier: str | None = typer.Argument(None, help="Persona identifier.")
):
    """Launch local Graphinate visual dashboard over the L2 Cognitive Map."""
    try:
        import graphinate
    except ImportError:
        console.print("[red]Error: Graphinate GUI requires 'tur-adm[gui]'. Run: pip install tur-adm[gui][/red]")
        raise typer.Exit(code=1)

    active_id = persona.get_active_persona_id(identifier)
    persona_dir = persona.get_persona_path(active_id)
    l2_graph = load_l2_graph_from_okf(persona_dir)

    console.print(f"[bold cyan]Serving Tur Cognitive Map for '{active_id}' at http://localhost:{port}[/bold cyan]")
    # Launch Graphinate server
    graphinate.server.run(l2_graph, port=port)
```

---

## Backwards Compatibility

- **100% Non-Breaking:** `networkx-mermaid` is an ultra-lightweight package ($8.2\text{ KB}$, pure Python, zero
  dependencies beyond NetworkX).
- **Core Isolation:** `graphinate` is packaged exclusively under the optional `[gui]` extra in `tur-adm`, adding zero
  overhead to the core `tur` runtime.

---

## How to Teach This / Documentation Plan

- Document graph export and dashboard commands in `docs/tools/visual-dashboard.md`.
- Include sample Mermaid diagrams in Zensical documentation.

---

## Reference Implementation

- Mermaid compilation: `src/tur/recall.py`
- Admin graph server: `src/tur/cli/admin.py`
- Research reference:
  `references/discussions/2026-08-28-persona-and-memory-crystallization/12_graphinate_networkx_mermaid_and_mappingtools_ecosystem.md`

---

## Rejected Ideas

- **Bundling Web Frameworks (FastAPI, Flask) in Core `tur`:** Rejected to keep the core agent runtime lean and
  dependency-minimal.
- **Client-Side Heavy Webpack Bundles:** Rejected in favor of lightweight server-rendered HTML or static Mermaid
  diagrams.

---

## Open Questions

- [ ] Should Graphinate export interactive SVG widgets directly into Zensical static documentation?

---

## Change Log

* **2026-08-30:**
    * Initial Draft authored based on the Graphinate and networkx-mermaid research monograph.
