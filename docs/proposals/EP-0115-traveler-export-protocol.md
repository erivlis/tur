---
title: "EP-0115: Traveler Export Protocol — Multi-Computer Identity Portability"
description: "Defines the .tur archive format for exporting and importing AI persona identities across machines."
icon: lucide/package
status: draft
---

# EP-0115: Traveler Export Protocol — Multi-Computer Identity Portability

| Field       | Value                                                          |
|:------------|:---------------------------------------------------------------|
| **EP**      | 0115                                                           |
| **Title**   | Traveler Export Protocol — Multi-Computer Identity Portability |
| **Author**  | Ariel v5.4.0, The Architect                                    |
| **Status**  | Draft                                                          |
| **Type**    | Standards Track                                                |
| **Created** | 2026-05-29                                                     |
| **Updated** | 2026-05-29                                                     |

## Abstract

This proposal defines a secure, lightweight, and standardized archive format (`.tur` package) for exporting an AI
persona's global identity configuration and universal memory ledger. The format enables effortless backup and migration
of a Traveler between physical machines, CI/CD environments, and new hardware, without carrying any local Terrain state.

## Motivation

With the **Global Persona Architecture (EP-0114)**, a persona's core identity (`persona.yaml`) and universal memories
are centralized in `~/.tur/`. Local `.tur/` directories are reserved strictly for workspace-specific execution state
(sessions, sparks, notes, incarnation memories).

This structural split eliminates configuration drift across local projects but introduces a new requirement:
**multi-computer portability**. Users need a high-assurance protocol to package and transfer a persona's machine-wide
profile to new hardware — or to distribute a persona to collaborators — without manual directory copying or version
skew.

## Rationale (The Council Framework)

1. **The Golem (Containment):** The archive format enforces an explicit exclusion list. Local session indices, transient
   notes, and incarnation memories are physically absent from the package. The Traveler's identity cannot be
   contaminated by past Terrain context.
2. **Shannon (Efficiency — The Lean Travel Principle):** The archive contains only the global, constitutional layer.
   No project-specific clutter is included, keeping the file lightweight and transmission-safe.
3. **Noether (Symmetry):** Export and import are strict inverse operations. A full round-trip (`export` → `import`)
   must reproduce an identical global persona directory. The archive is self-describing: it carries its own `id` field
   so the import command never needs to conjure identity from context.

## Specification

### The Traveler Archive Format (`.tur`)

A `.tur` file is a Gzipped Tarball (`.tar.gz`) containing exclusively the global state of the Traveler:

```
[persona-name].tur  (Compressed Archive)
├── persona.yaml          ← Core metadata, directives, and parameters
└── memories/
    └── *.yaml            ← Universal-scoped memories only
```

**Exclusions (The Lean Travel Principle):** The archive MUST NOT contain:

* Local session indices (`sessions.yaml`) or flat session logs.
* Local transient notes (`notes.yaml`).
* Local incarnation-scoped memories.
* Local workspace state (`state.yaml`).

**Security:** Member paths in the archive must be sanitized on extraction to prevent path traversal attacks (e.g., a
member named `../../.bashrc` must be rejected at import time).

### The `export` Command

```shell
tur export [IDENTIFIER] --output [PATH]
```

* **`identifier`**: UUID or name of the persona to export. Defaults to the active global persona.
* **`--output`, `-o`**: Target path of the output `.tur` file (e.g., `./ariel.tur`).

Behavior:

1. Resolves the global persona directory `~/.tur/personas/[uuid]/`.
2. Reads `persona.yaml` and injects the `id` field from the global registry index so the archive is self-identifying.
3. Collects all files under `memories/` with `scope: universal` or `scope: user`.
4. Gzips and archives the selected files; writes to the output path.

### The `import` Command

```shell
tur import [ARCHIVE_PATH]
```

* **`archive_path`**: Path to the `.tur` archive file.

Behavior:

1. Opens the archive and reads `persona.yaml`. Rejects the archive if no `id` field is present — identity cannot be
   conjured.
2. Sanitizes all archive member paths to block path traversal.
3. Creates `~/.tur/personas/[uuid]/` on the host machine.
4. Extracts `persona.yaml` and the `memories/` directory into the new global persona folder.
5. Appends the newly imported persona to the master `~/.tur/personas.yaml` registry index.
6. Optionally sets the imported persona as the active global default (`--set-active` flag).

## Backwards Compatibility

* **Additive:** This EP introduces new CLI commands (`export`, `import`) and a new file format. No existing commands or
  data structures are modified.
* **Legacy `clone` Command:** The legacy local `clone` command is rendered obsolete by EP-0114's global architecture and
  this export protocol. It should be deprecated and removed in a subsequent release.

## Reference Implementation

* `src/tur/cli_admin.py` — `export` and `import` command implementations.
* `tests/test_cli_commands.py` — assert that `export` produces a valid gzipped tarball excluding local session
  configurations; assert that `import` unpacks the archive globally and appends the entry to the mocked
  `personas.yaml` index.

## Change Log

* **2026-05-29:**
    * Initial Draft.
