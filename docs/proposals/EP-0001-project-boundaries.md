---
title: "EP-0001: Project Boundaries (Core vs. Periphery)"
description: "Defines the architectural boundary between Tur's Core and Periphery, establishing rules against feature creep."
icon: lucide/git-branch
status: superseded
---

# EP-0001: Project Boundaries (Core vs. Periphery)

| Field       | Value                                   |
|:------------|:----------------------------------------|
| **EP**      | 0001                                    |
| **Title**   | Project Boundaries (Core vs. Periphery) |
| **Author**  | Eran Rivlis                             |
| **Status**  | Superseded                              |
| **Type**    | Process                                 |
| **Created** | 2026-02-19                              |
| **Updated** | 2026-04-12                              |

## Abstract

This proposal formally defines the architectural boundary between the Tur "Core" (`src/tur/`) and its "Periphery" (
`tools/`). It establishes strict rules against feature creep by ensuring that heavy, non-deterministic, or
highly-entropic operations (like web scraping or browser automation) are kept out of the core framework.

**Note:** This EP has been superseded by **EP-0102 (The Tur Orchestration Engine)**, which provides a more robust and
standardized mechanism (MCP) for integrating external tools without compromising the core.

## Motivation

As Tur grows, there will be a constant temptation to add utilities that make the Persona more capable (e.g., "Tur should
be able to browse the web!"). However, integrating these features directly into the core violates the **Tur Tur
Principle** by introducing "Apparent Giants" (heavy dependencies like Chromium) into the system.

The `tools/smart_fetch.py` script serves as the canonical example of this tension. It requires `playwright`, a massive
dependency. If this were added to `pyproject.toml`, every user would pay the cost of downloading browser binaries just
to use the CLI.

To maintain **The Golem** (Safety/Containment) and **Shannon** (Efficiency), we must draw a hard line.

## Rationale

This design aligns with the Council Framework:

1. **Shannon (Efficiency):** The core library (`src/tur/`) must remain lightweight. It handles low-entropy tasks (YAML
   parsing, template rendering, Pydantic validation).
2. **The Golem (Safety):** The core must be deterministic. The web is chaotic. Fetching data from the web (high-entropy)
   is an "Edge Operation."
3. **Noether (Symmetry):** The boundary must be clear. Core processes data; Tools fetch data.

## Specification

### 1. The Core (`src/tur/`)

* **Role:** The Operating System / The Engine.
* **Dependencies:** Must be minimal, pure Python, and deterministic (e.g., `typer`, `pydantic`, `jinja2`).
* **Forbidden:** No web scraping, no browser automation, no heavy ML models (unless accessed via API), no chaotic state
  manipulation.

### 2. The Periphery (`tools/`)

* **Role:** Sensors and Effectors.
* **Dependencies:** Allowed to be heavy (e.g., `playwright`, `beautifulsoup4`).
* **Execution:** These must be independent scripts. They should leverage PEP 723 inline metadata to declare their
  dependencies so they can be run ephemerally (e.g., via `uv run`).
* **Interface:** Tools communicate with the Core by outputting clean, standardized formats (like Markdown or JSON) that
  the Core or the Agent can consume.

### Canonical Example: `smart_fetch.py`

`tools/smart_fetch.py` is the reference implementation of a Periphery Tool. It is an independent script that uses
Playwright to fetch dynamic HTML and convert it to Markdown. It does not import `tur`, and `tur` does not import it.

## Backwards Compatibility

No code is broken. This is an informational EP that formalizes existing implicit rules.

## Backwards Compatibility

This document established core architectural boundaries. No software migration required.

## Reference Implementation

Superseded by [EP-0102](EP-0102-orchestration-engine.md) and module layout under `src/tur/`.

## Change Log

* **2026-04-12:**
    * Status changed to `Superseded by EP-0102`.
* **2026-02-19:**
    * Initial Draft.
