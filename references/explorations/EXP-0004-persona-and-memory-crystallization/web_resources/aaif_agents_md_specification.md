# Agentic AI Foundation (AAIF) — AGENTS.md Specification Reference

**Source:** Linux Foundation / Agentic AI Foundation (AAIF)  
**Standard:** Open AGENTS.md Standard (2025–2026)  
**Reference Document Stored For:** Tur Persona & Bootloader Decoupling  

---

## 1. Overview

`AGENTS.md` is an open, vendor-neutral Markdown specification stewarded by the **Agentic AI Foundation (AAIF)** under the **Linux Foundation**. It provides a single, predictable standard for onboarding AI coding agents (such as Claude Code, GitHub Copilot, Cursor, Antigravity, OpenHands, Aider, and Goose) to a repository.

## 2. Core Principles of the Specification

1. **Vendor Neutrality:** A single `AGENTS.md` file replaces fragmented, tool-specific dotfiles (e.g. `.cursorrules`, `CLAUDE.md`, `.copilot-instructions.md`).
2. **Predictable Discovery:** AI agents automatically discover and parse `AGENTS.md` located at the repository root upon session startup.
3. **Hierarchical Scope (Monorepos):** Nested `AGENTS.md` files in subdirectories override or augment root guidelines for specific packages.
4. **Plain Markdown:** Uses standard GitHub Flavored Markdown (GFM) without mandatory YAML frontmatter, ensuring direct readability by both humans and LLMs.
5. **Conciseness & High Signal:** Emphasizes high-impact project constraints, build/test commands, and boundary invariants rather than tutorial-style documentation.

## 3. Standard Structure & Recommended Headings

```markdown
# AI Agent Guidelines

Brief description of project purpose and architecture.

## Build & Test Commands
- Build: `uv build` / `pnpm build`
- Test all: `uv run pytest` / `cargo test`
- Lint/Format: `ruff check` / `biome check`

## Code Style & Architecture Invariants
- Functional naming conventions over anthropomorphic metaphors.
- Strict physical separation between core mechanism and user policy.

## Tool & State Boundaries
- Explanation of prohibited directories, lock files, and state management endpoints.
```

## 4. Integration with Tur

In Tur's decoupled architecture (EP-0135):
- `AGENTS.md` lives at the project root and defines the **Operational Space Suit** (teaching the LLM how to invoke `wake()`, `note()`, `learn()`, `recall()`, and enforcing the `.tur/` Golem isolation boundary).
- It remains completely decoupled from `.tur/CONSTITUTION.md` which houses the persona's internal identity and Council of Giants principles.
