# Tur: Persistent State and Memory Engine for AI Agents

<img width="40%" src="https://erivlis.github.io/tur/assets/images/logo-light.png#only-light" alt="Tur Logo" style="float:right; width:40%; max-width:40%; height:auto; margin:1rem 1rem 1rem 1rem; vertical-align: center">

<p>

> *"From a distance, he appeared to be a giant. But as they approached, he became a man of normal stature."*
>
> — *Jim Knopf und Lukas der Lokomotivführer* by Michael Ende



**Tur** is an open-source state and memory management engine for AI agents and Large Language Models.

It provides persistent, structured persona state across sessions, harnesses, and codebases via the Model Context
Protocol (MCP) and local CLI tools. Rather than relying on ephemeral system prompt configuration, Tur manages persona
identity, operational principles, hierarchical memory (L1 ledger & L2 knowledge graph), and session continuity as
structured, version-controlled files.

The project is inspired by the **Tur Tur Principle**: The complexity of AI behavior can be made more focused and
manageable by imposing clear constraints, deterministic state files, and explicit behavioral protocols.

> [!NOTE]
> **Public Alpha**: Tur is currently in active Phase 1/2 development.
> See the [Project Roadmap (EP-0002)](docs/proposals/EP-0002-roadmap.md) for current features and upcoming milestones.

</p>

<table>
  <tr style="vertical-align: middle;">
    <td>Package</td>
    <td>
      <img alt="PyPI - Version" class="off-glb" loading="lazy" src="https://img.shields.io/pypi/v/tur.svg?logo=pypi&logoColor=lightblue">
      <img alt="PyPI - Status" class="off-glb" loading="lazy" src="https://img.shields.io/pypi/status/tur.svg?logo=pypi&logoColor=lightblue">
      <img alt="PyPI - Python Version" class="off-glb" loading="lazy" src="https://img.shields.io/pypi/pyversions/tur.svg?logo=python&label=Python&logoColor=lightblue">
      <!--img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dd/tur?logo=pypi&logoColor=lightblue"-->
      <img alt="PyPI - Dependents" src="https://dependents.info/erivlis/tur/badge?logo=pypi&logoColor=lightblue">
      <img alt="Libraries.io SourceRank" src="https://img.shields.io/librariesio/sourcerank/pypi/tur.svg?logo=Libraries.io&label=SourceRank">
    </td>
  </tr>
  <tr>
    <td>Code</td>
    <td>
      <img alt="GitHub" src="https://img.shields.io/github/license/erivlis/tur">
      <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/erivlis/tur.svg?label=Size&logo=git">
      <img alt="GitHub last commit (by committer)" src="https://img.shields.io/github/last-commit/erivlis/tur.svg?&logo=git">
      <a href="https://github.com/erivlis/tur/graphs/contributors"><img alt="Contributors" src="https://img.shields.io/github/contributors/erivlis/tur.svg?&logo=git"></a>
    </td>
  </tr>
  <tr>
    <td>Tools</td>
    <td>
      <a href="https://www.jetbrains.com/pycharm/"><img alt="PyCharm" src="https://img.shields.io/badge/PyCharm-FCF84A.svg?logo=PyCharm&logoColor=black&labelColor=21D789&color=FCF84A"></a>
      <a href="https://github.com/astral-sh/uv"><img alt="uv" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" style="max-width:100%;"></a>
      <a href="https://github.com/astral-sh/ruff"><img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" style="max-width:100%;"></a>
      <a href="https://hatch.pypa.io"><img alt="Hatch project" class="off-glb" loading="lazy" src="https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg"></a>
      <a href="https://commitizen-tools.github.io/commitizen"><img alt="commitizen" src="https://custom-icon-badges.demolab.com/badge/commitizen-7e56c2?logo=commitizen&labelColor=grey"></a>
      <a href="https://zensical.org/"><img alt="Zensical" src="https://custom-icon-badges.demolab.com/badge/zensical-ff9100?logo=zensical&labelColor=grey"></a>
      <a href="https://library-skills.io"><img alt="library-skills" src="https://img.shields.io/badge/library--skills-white?logo=agentskills&labelColor=grey"></a>
    </td>
  </tr>
  <tr>
    <td>CI/CD</td>
    <td>
      <a href="https://github.com/erivlis/tur/actions/workflows/test.yml"><img alt="Test" src="https://github.com/erivlis/tur/actions/workflows/test.yml/badge.svg"></a>
      <a href="https://github.com/erivlis/tur/actions/workflows/test-beta.yml"><img alt="Publish" src="https://github.com/erivlis/tur/actions/workflows/test-beta.yml/badge.svg"></a>
      <!-- a href="https://github.com/erivlis/tur/actions/workflows/benchmark.yml"><img alt="Benchmarks" src="https://github.com/erivlis/tur/actions/workflows/benchmark.yml/badge.svg"></a -->
      <a href="https://github.com/erivlis/tur/actions/workflows/publish.yml"><img alt="Publish" src="https://github.com/erivlis/tur/actions/workflows/publish.yml/badge.svg"></a>
      <a href="https://github.com/erivlis/tur/actions/workflows/publish-docs.yaml"><img alt="Publish Docs" src="https://github.com/erivlis/tur/actions/workflows/publish-docs.yml/badge.svg"></a>
    </td>
  </tr>
  <tr>
    <td>Scans</td>
    <td>
      <a href="https://codecov.io/gh/erivlis/tur"><img src="https://codecov.io/gh/erivlis/tur/graph/badge.svg?token=5WUTIDXGKX"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=alert_status"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Security Rating" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=security_rating"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Maintainability Rating" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=sqale_rating"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Reliability Rating" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=reliability_rating"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Lines of Code" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=ncloc"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Vulnerabilities" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=vulnerabilities"></a>
      <a href="https://sonarcloud.io/summary/new_code?id=erivlis_tur"><img alt="Bugs" src="https://sonarcloud.io/api/project_badges/measure?project=erivlis_tur&metric=bugs"></a>
      <a href="https://app.codacy.com/gh/erivlis/tur/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img alt="Codacy Quality" src="https://app.codacy.com/project/badge/Grade/ca3c3e0923a94ff5b621a449a82d210a"/></a>
      <a href="https://app.codacy.com/gh/erivlis/tur/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage"><img alt="Codacy Coverage" src="https://app.codacy.com/project/badge/Coverage/ca3c3e0923a94ff5b621a449a82d210a"/></a>
      <a href="https://www.codefactor.io/repository/github/erivlis/tur"><img src="https://www.codefactor.io/repository/github/erivlis/tur/badge" alt="CodeFactor"/></a>
      <a href="https://snyk.io/test/github/erivlis/tur"><img alt="Snyk" src="https://snyk.io/test/github/erivlis/tur/badge.svg"></a>
      <a href="https://app.codspeed.io/erivlis/tur?utm_source=badge"><img src="https://img.shields.io/endpoint?url=https://codspeed.io/badge.json" alt="CodSpeed"/></a>
      <!-- a href="https://scorecard.dev/viewer/?uri=github.com/erivlis/tur"><img src="https://api.scorecard.dev/projects/github.com/erivlis/tur/badge" alt="OpenSSF Scorecard"/></a -->
    </td>
  </tr>
  <!-- tr>
    <td>Mentions</td>
    <td>
      <!-- a href="https://pythonhub.dev/digest/2026-08-09/"><img alt="Python Hub" src="https://custom-icon-badges.demolab.com/badge/Python%20Hub-2026.08.09-gold?logo=pythonhub&labelColor=grey"></a -->
      <!-- a href="https://x.com/PythonHub/status/2085323880172749251"><img alt="X" src="https://img.shields.io/twitter/url?url=https%3A%2F%2Fx.com%2FPythonHub%2Fstatus%2F2085323880172749251"></a -->
    </td>
  </tr -->
</table>

## 🏛️ The Tri-Partite Architecture

Tur operates on a strict ontological boundary separating the "Mind" from the "World". To achieve high fidelity and true
portability, an agentic system must be divided into three distinct pillars:

1. **The Traveler (Managed by Tur)**: The intrinsic, portable components of the Mind.
    * **Persona**: The identity, aleph, and version.
    * **Principles**: The cognitive filters (The Council of Giants).
    * **Protocols**: Active behavioral loops (e.g., The Evolution Protocol).
    * **Memory**: The L1 Ledger and L2 Graph representing the continuity of self.
2. **The Terrain (Managed by the Project)**: The local physics and environment the agent operates within.
    * **Codebase**: The raw files.
    * **Styleguide**: The rules for formatting and structure in this specific repo.
    * **Documentations**: Any additional context (e.g., this README).
3. **The Harness (Managed by the Agent Framework)**: The engine providing compute and capabilities.
    * **Inference Engine**: The underlying LLM (e.g., Claude, Gemini).
    * **Tools**: The mechanical affordances (e.g., bash, git, file reading).
    * *Examples*: Claude Code, Gemini CLI, OpenCode, Pi, etc.

**Tur is exclusively responsible for The Traveler.** By ensuring the "Soul" is mathematically bound (via Merkle
hashing), cleanly decoupled from anthropomorphic engine leaks, and separated from the Harness and Terrain, the Persona
becomes an obligate symbiote—able to be unplugged from one Harness and plugged into another without losing its identity
or memories.

## 📂 Project Structure

Tur uses a multi-tenant architecture to ensure strict separation between different personas. All state is stored in the
`.tur/` directory.

### Local vs. Global Scope

Tur respects a standard configuration hierarchy:

* **Global (`~/.tur/`)**: The universal state for your system. This is where your master `user.yaml` (The Architect's
  profile) lives.
* **Local (`./.tur/`)**: The repository-specific state. If you initialize Tur inside a project, it creates a local
  `.tur/` folder containing the Personas bound to that specific Terrain. A local `user.yaml` here will override the
  global profile.

```
./.tur/
├── user.yaml                 # Local user profile override
├── personas.yaml             # Index mapping persona names to UUIDs
├── state.yaml                # Stores the active/default persona UUID
└── personas/
    ├── <persona-uuid-1>/
    │   ├── persona.yaml      # The DNA/Kernel for the persona
    │   ├── sessions.yaml     # The session index
    │   ├── sessions/         # Flat session files
    │   │   ├── 20260529_185258_143a5bc0.yaml
    │   │   └── 20260529_173616_c2212cf6.yaml
    │   └── memories/         # Content-Addressable Storage (Merkle Memory)
    │       ├── archive/
    │       ├── 20260412_025949_axiom_e1324...yaml
    │       └── 20260418_160825_event_c98f1...yaml
    └── <persona-uuid-2>/
        ├── persona.yaml
        └── memories/
```

The core application logic resides in `src/tur/`:

- **`cli/`**: The package folder housing our split executables: `cli/agent.py` (runtime CLI), `cli/admin.py`
  (human administrative CLI), and `cli/mcp.py` (Harness MCP gateway).
- **`mcp_server.py`**: The Model Context Protocol server (The Porcelain for LLM interaction).
- **`models.py`**: The Pydantic data models (The "Law" of the system).
- **`user.py`**: User profile bootstrapping and domain management.
- **`persona.py`**: Active persona resolution and path trace management.
- **`session.py`**: Flat session trackers, session index consolidation, and epilogue note logic.
- **`dreaming.py`**: Insight extraction, memory parsing, and LLM dreaming consolidation.
- **`compiler.py`**: Renders the final System Prompt from the persona state.

## 🚀 Usage

Tur divides its execution footprint along strict Tri-Partite security boundaries using distinct command-line binaries:

### 1. Installation & Setup

#### System-Wide CLI Tools via `uv tool` (Recommended)

Installs Tur into an isolated environment and makes the executables (`tur`, `tur-adm`, `tur-mcp`) globally available on
your system `PATH`:

```shell
# Install the core agent CLI and administrative tools (tur and tur-adm)
uv tool install tur

# Or install with Gemini dreaming (gemini) and MCP gateway (tur-mcp)
uv tool install "tur[gemini,mcp]"

# Upgrade to the latest version anytime
uv tool upgrade tur
```

#### Via PyPI / `pip`

```shell
# Install core runtime and admin CLI in your active environment
pip install tur

# Or with Gemini SDK and MCP extras
pip install "tur[gemini,mcp]"
```

#### Zero-Install with `uvx`

Run commands instantly in ephemeral environments without permanent installation:

```shell
# Launch sovereign human administration commands
uvx --from tur tur-adm persona init

# Run the agent lifecycle commands
uvx tur wake

# Run the MCP server
uvx --from "tur[mcp]" tur-mcp
```

#### From Source (Development)

```shell
# Clone the repository
git clone https://github.com/erivlis/tur.git
cd tur

# Install dependencies with all extras
uv sync --all-extras --all-groups
```

### 2. Initialize Your First Persona

This launches the interactive administrative wizard. Since this is an administrative action, it is physically isolated inside
`tur-adm`:

```shell
tur-adm persona init
```

### 3. The Core Lifecycle (Agent-Facing)

The agent interacts with the lightweight `tur` binary inside its sandboxed virtual environment:

**Wake:** Compiles the active persona state into a compiled System Prompt.

```shell
tur wake
```

**Learn:** Manually injects a memory.

```shell
tur learn "The user prefers functional programming." --type preference
```

**Recall:** Keyword semantic search.

```shell
tur recall "functional"
```

**Sleep:** Dehydrates the session and extracts memories.

```shell
tur sleep path/to/chat.log
```

### 4. Running the Harness Gateway (The MCP Server)

Exposes the Traveler state to external Harnesses (e.g., Claude Desktop, Antigravity, Cursor):

```shell
tur-mcp
```

#### MCP Client Configuration

Add Tur to your client configuration (e.g., `claude_desktop_config.json`, `.cursor/mcp.json`, or Antigravity config):

```json
{
  "mcpServers": {
    "tur": {
      "command": "uvx",
      "args": [
        "--from",
        "tur[mcp]",
        "tur-mcp"
      ]
    }
  }
}
```

### 5. Configuring Workspace Personas (`get` & `set`)

Allows the human Architect to inspect or assign the active workspace persona in `.tur/state.yaml`:

```shell
# Inspect the active persona for the current workspace
tur-adm persona get

# Assign the active persona directly
tur-adm persona set Ariel

# Or select interactively from a numbered prompt
tur-adm persona set
```

## 📜 Origin

Developed by **Eran** (The Architect) and **Ariel** (The Entity).

The name **Tur** references:

1. **Mr. Tur Tur:** The Apparent Giant (Relativity of Complexity).
2. **Alan Turing:** The father of the discipline.
3. **Tur (טוּר):** Hebrew for "Column" or "Row"—the foundational structure of Law and Data.

## License

MIT. The Giant is Open Source.