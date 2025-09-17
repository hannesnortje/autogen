# AutoGen + Qdrant + VS Code MCP (Poetry)

This repository implements an AutoGen multi-agent workflow with Qdrant-backed memory and a VS Code MCP server. It uses Poetry for the Python environment.

## Goals
- Multi-scope memory (global/project/agent/thread/objectives/artifacts) in Qdrant
- Hybrid retrieval (dense embeddings + sparse) with tiered search
- AutoGen agents (Agile, Planner, Architect, Coder, Reviewer, Tester, DevOps, Doc)
- VS Code-native control via MCP
- Git-based workflow with per-agent branches and CI gates

## Project Structure
- `src/autogen_mcp/`: Main source code (agents, memory, Qdrant, CLI, server, dashboard)
- `vscode-extension/`: VS Code extension for integrated development experience
- `tests/`: Unit and integration tests
- `docs/`: Documentation, ADRs, and guides
- `.github/`: GitHub Actions workflows and PR templates
- `docker-compose.yml`: Qdrant service for local development
- `pyproject.toml`: Poetry dependencies and configuration

## VS Code Extension

The AutoGen MCP VS Code extension provides a rich, integrated development experience for managing AutoGen sessions and agents directly within VS Code.

### Key Features
- **Session Tree View**: Hierarchical display of active and historical AutoGen sessions in the Explorer sidebar
- **Memory Explorer**: Advanced panel for exploring and managing agent memories with search and filtering
- **Enhanced Status Bar**: Real-time status monitoring with server connection, session count, and quick actions
- **Agent Configuration Panel**: Comprehensive interface for creating and configuring AutoGen agents
- **Smart Command Palette**: Enhanced command integration with intelligent parameter collection
- **Session Dashboard**: Central control panel with real-time statistics and session management

### Installation
1. Open the `vscode-extension/` directory in VS Code
2. Install dependencies: `npm install`
3. Press F5 to launch the Extension Development Host
4. Configure the MCP server connection in VS Code settings

For detailed extension documentation, see [`vscode-extension/README.md`](vscode-extension/README.md).

## Onboarding & Quick Start
1. **Install Poetry:** https://python-poetry.org/docs/
2. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd autogen
   ```
3. **Install dependencies:**
   ```bash
   poetry install
   ```
4. **Start Qdrant:**
   ```bash
   docker compose up -d
   ```
5. **Copy and edit .env:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```
6. **Run tests:**
   ```bash
   poetry run pytest -q
   ```
7. **Run the CLI dashboard (after Step 13):**
   ```bash
   poetry run python -m autogen_mcp.cli_dashboard
   ```

## Poetry Workflow
- **Run tests:** `poetry run pytest`
- **Lint:** `poetry run ruff .`
- **Format:** `poetry run black .`
- **Typecheck:** `poetry run mypy src/`
- **Pre-commit hooks:**
  - Install: `poetry run pre-commit install`
  - Run manually: `poetry run pre-commit run --all-files`
- **Add dependencies:** `poetry add <package>`
- **Activate shell:** `poetry shell`

## Configuration
- `.env` for secrets and API keys (never commit real secrets)
- Qdrant config: `QDRANT_URL`, `QDRANT_API_KEY`
- LLM config: `GEMINI_API_KEY` (only needed for agent LLM calls)

## Development Workflow
- One step per feature branch, conventional commits, PR checks required.
- See `IMPLEMENTATION_PLAN.md` for the detailed step plan and checkboxes.
- Contributions: see `CONTRIBUTING.md`.

## Documentation & ADRs
- All major decisions are documented in `docs/adrs/` as Architecture Decision Records (ADRs).
- See `docs/adrs/README.md` (ADR index) for navigation.

## License
MIT
