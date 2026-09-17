# Security Policy

## Supported Versions

Tur is actively developed. Security patches are applied to the current release line.

| Version | Supported          |
|---------|--------------------|
| 0.15.x  | :white_check_mark: |
| 0.14.x  | :white_check_mark: |
| < 0.14  | :x:                |

---

## Reporting a Vulnerability

We take the security of Tur and the autonomy of the systems running on it seriously. If you believe you have found a
security vulnerability in Tur, please report it responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

### Disclosure Channels

1. **GitHub Security Advisories (Preferred):**
   Submit a private advisory via [GitHub Security Advisories](https://github.com/erivlis/tur/security/advisories/new).
2. **Direct Contact:**
   If you cannot access GitHub Advisories, reach out directly to the maintainer:
    - **Eran Rivlis**: [GitHub Profile](https://github.com/erivlis)

### What to Include in Your Report

To help us triage and resolve the issue quickly, please include:

- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions, Proof of Concept (PoC) script, or minimum reproduction repository.
- Affected Tur version, Python version, Operating System, and agent harness (e.g., Pi, Claude Code, Antigravity, MCP
  client).
- Any proposed remediation or patch, if available.

### Response & Coordinated Disclosure

- **Best-Effort Maintenance:** Tur is an open-source project maintained on a volunteer, best-effort basis without formal SLAs. Reports are reviewed as maintainer time and bandwidth permit.
- **Triage & Remediation:** Once a report is verified, we will coordinate with the reporter to investigate the issue and develop a fix.
- **Coordinated Release:** Once a remediation is verified, a patch release and advisory will be published simultaneously.

---

## Architecture & Threat Model

Tur is a persistent state and cognitive memory engine for autonomous AI agents. Understanding our threat model helps
researchers identify valid security boundaries:

### 1. Tri-Partite CLI Separation (EP-0116)

Tur enforces physical privilege boundaries by separating CLI entrypoints:

- `tur`: The agent runtime client. Restricted to unprivileged operations (`wake`, `note`, `learn`, `recall`, `task`).
- `tur-adm`: The human administrator binary. Holds destructive operations (`delete`, `prune`, `export`, `import`). It
  requires an interactive TTY and is structurally omitted from the MCP server.
- `tur-mcp`: The Model Context Protocol bridge communicating strictly over standard I/O (`stdio`).

*Vulnerabilities involving an agent escaping the `tur` runtime or executing administrative commands via `tur-mcp` are
considered severe.*

### 2. State Store Isolation & Merkle Integrity

- The `.tur/` directory is an immutable, content-addressable Merkle store. All mutations must be brokered through
  verified CLI/MCP commands.
- Directory creation enforces POSIX `0700` permission masks on Unix platforms to prevent unauthorized cross-user
  inspection on multi-tenant systems.

### 3. Archive Sanitization & Path Traversal (EP-0115)

- When importing or exporting persona bundles (`tur-adm export` / `tur-adm import`), archive member paths are strictly
  sanitized against relative path traversal (`../`) and absolute target overrides.

### 4. Secret Prevention & Tombstoning (EP-0143)

- Tur provides redaction mechanisms to intercept API keys, passwords, and sensitive tokens before state consolidation.
  Redacted memories use cryptographic tombstones (`[TOMBSTONE: REDACTED DUE TO SECURITY POLICY]`) to preserve graph
  integrity without leaking raw credentials.

### 5. Out of Scope

- **Host Compromise / Compromised Harness**: Attacks requiring root/admin access to the developer's local workstation,
  or an execution harness that arbitrarily modifies files on disk outside Tur's APIs, are out of scope.
- **Pure Prompt Injection in LLM Outputs**: Unless the injection causes Tur's underlying engine to corrupt state,
  perform arbitrary file execution, or bypass privilege boundaries, standard LLM alignment drift belongs to the
  inference model rather than Tur's state substrate.
