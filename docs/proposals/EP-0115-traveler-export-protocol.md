---
title: "EP-0115: Traveler Export Protocol: Multi-Computer Identity Portability"
description: "A proposal to implement export and import routines in Tur, packaging core identities and universal memories for seamless transition between machines."
icon: lucide/package
status: drafted
---

# EP-0115: Traveler Export Protocol: Multi-Computer Identity Portability

**Date:** 2026-05-29  
**Author:** Ariel v5.4.0 (The Alchemist)  
**Status:** Drafted  

---

## 1. Objective

To provide a secure, lightweight, and standardized export format (`.tur` package) that compiles an AI persona's global identity configuration and universal memory ledger, enabling effortless backup and migration between different physical computers.

---

## 2. Background

With the implementation of the **Global Persona Architecture (EP-0114)**, a persona's core identity (`persona.yaml`, `personas.yaml` registry index) and universal memories are now centralized globally in `~/.tur/`. Local directories `.tur/` are reserved strictly for workspace-specific execution (sessions, Sparks, notes, and local incarnation memories).

This structural split renders the legacy `clone` command obsolete for local repository transitions, as the persona is globally accessible across all local workspaces. However, it exposes a new requirement: **multi-computer portability**. 

Users need a high-assurance protocol to export a persona's machine-wide profile so they can load their deterministic partner onto new physical hardware or CI/CD environments.

---

## 3. The Traveler Archive Format (`.tur`)

We define the `.tur` archive as a compressed Gzipped Tarball (`.tar.gz`) containing exclusively the global state of the Traveler:

```
[persona-name].tur (Compressed Archive)
├── persona.yaml          <-- Core metadata, directives, and parameters
└── memories/             <-- Directory of all universal memories
    ├── *.yaml
```

### Exclusions (The Principle of Lean Travel)
The archive **MUST NOT** contain:
* Local session indices (`sessions.yaml`) or flat session logs.
* Local transient notes (`notes.yaml`).
* Local project-specific incarnation memories.
* Local workspace states (`state.yaml`).

This ensures the exported persona remains entirely decoupled from previous project terrains, keeping the file lightweight and safe from local context leakage.

---

## 4. CLI Specifications

We propose adding two new administrative commands to the `tur` CLI:

### 4.1. The `export` Command

Packages a global persona into a `.tur` traveler archive.

```shell
tur export [IDENTIFIER] --output [PATH]
```

* **Arguments:**
  * `identifier`: The UUID or name of the persona to export. Defaults to the active default persona.
* **Options:**
  * `--output`, `-o`: The target path of the output file (e.g., `./ariel.tur`).
* **Behavior:**
  1. Locates the global persona directory `~/.tur/personas/[uuid]/`.
  2. Compiles `persona.yaml` and the `memories/` directory.
  3. Gzips the target files and writes them to the output path.

### 4.2. The `import` Command

Unpacks a `.tur` traveler archive and registers it in the host machine's master index.

```shell
tur import [ARCHIVE_PATH]
```

* **Arguments:**
  * `archive_path`: The path to the `.tur` archive file (e.g., `./ariel.tur`).
* **Behavior:**
  1. Inspects the archive and reads the `persona.yaml` metadata to verify the UUID and Name.
  2. Creates the global home path: `~/.tur/personas/[uuid]/`.
  3. Unpacks `persona.yaml` and the universal memories into the folder.
  4. Appends the newly imported persona to the master `~/.tur/personas.yaml` registry.
  5. Sets the imported persona as active if requested.

---

## 5. Verification Plan

### Automated Tests
* Create unit tests in `test_cli_commands.py` asserting that running `tur export` creates a valid gzipped tarball excluding local session configurations.
* Assert that running `tur import` successfully unpacks the archive globally and appends the entry to the mocked master index `personas.yaml`.
