# AutoGen Multi-Agent System

**🎯 Production-Ready Multi-Agent Development Platform**

AutoGen is a sophisticated multi-agent system that combines memory-augmented AI agents, collaborative scrum workflows, and comprehensive development tooling into a unified platform. The system provides intelligent memory management across multiple scopes, agent orchestration capabilities, and both desktop and VS Code integration.

## 📖 Complete Documentation

**🔗 See [`AUTOGEN_PROJECT_MASTER.md`](AUTOGEN_PROJECT_MASTER.md)** for comprehensive project documentation including:
- Complete system architecture and current capabilities
- Implementation journey and development phases
- Future roadmap with advanced analytics enhancements
- Technical reference, API documentation, and development guide

## 🚀 Quick Start Overview
- **Multi-scope memory**: 6-scope architecture with 603+ indexed entries (global/project/agent/thread/objectives/artifacts)
- **Agent collaboration**: Memory-augmented agents with scrum methodology integration
- **Desktop UI**: Complete PySide6 application with real-time memory browser and session management
- **VS Code integration**: Extension with session tree view, memory explorer, and dashboard
- **Production ready**: Sub-200ms response times, comprehensive testing, connection resilience

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

## PySide6 Desktop UI

The AutoGen Desktop UI provides a comprehensive desktop application for managing AutoGen sessions, agents, and memory directly from your desktop.

### Key Features
- **Server Management**: Real-time MCP server status monitoring and connection management
- **Session Management**: Complete session lifecycle with conversation history and working directory support
- **Memory Browser**: Advanced memory exploration with search, analytics, and file upload capabilities
- **Agent Manager**: Agent configuration with built-in presets (Code Assistant, Data Analyst, Content Writer, Research Assistant)
- **Real-time Updates**: WebSocket integration with desktop notifications
- **Professional Interface**: Modern Qt6-based interface with tabbed layout and clean design

### Auto-Launch Configuration
The UI can be configured to automatically start with the MCP server or run independently:

**Enable auto-launch (UI starts with server):**
```bash
poetry run python ui_control.py set auto
poetry run python launch.py  # Starts both server and UI
```

**Manual launch modes:**
```bash
poetry run python ui_control.py set never      # Disable auto-launch (default)
poetry run python ui_control.py set on_demand  # Manual launch only
poetry run python ui_control.py set vscode_only # VSCode extension only
```

**Launch options:**
```bash
poetry run python launch.py                    # Use configuration setting
poetry run python launch.py --server-only      # MCP server only
poetry run python launch.py --ui-only          # UI only (connect to existing server)
poetry run python launch.py --with-ui          # Force both server and UI
```

**Manual UI control:**
```bash
poetry run python ui_control.py status         # Show current configuration
poetry run python ui_control.py launch         # Launch UI manually (if server running)
```

### Architecture Benefits
- **Independent Processes**: UI and server run separately - UI can close without affecting server
- **Direct Integration**: UI uses Python imports for optimal performance (not HTTP endpoints)
- **Port 9000**: Server runs on port 9000 for both API and UI access
- **Automatic Dependencies**: Qdrant vector database auto-starts with the server
- **Flexible Deployment**: Server can run headless for production, with UI for development

### Qdrant Auto-Start
The launcher automatically manages Qdrant dependencies:
- **Smart Detection**: Checks if Qdrant is already running
- **Auto-Start**: Starts Qdrant via docker-compose if needed
- **Health Waiting**: Waits for Qdrant to be ready before starting MCP server
- **Clean Shutdown**: Stops Qdrant when launcher exits (if it started it)
- **No Manual Setup**: No need to run `docker compose up -d` manually

For detailed UI documentation, see [`docs/archive/PYSIDE6_UI_IMPLEMENTATION.md`](docs/archive/PYSIDE6_UI_IMPLEMENTATION.md).

## Onboarding & Quick Start
1. **Install Poetry:** https://python-poetry.org/docs/
2. **Install Docker:** https://docs.docker.com/get-docker/ (for Qdrant database)
3. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd autogen
   ```
4. **Install dependencies:**
   ```bash
   poetry install
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
7. **Start the application:**
   ```bash
   # Option 1: MCP server + Desktop UI + Qdrant (all auto-start)
   poetry run python launch.py

   # Option 2: MCP server only + Qdrant (auto-start)
   poetry run python launch.py --server-only

   # Option 3: CLI dashboard (legacy, requires manual Qdrant)
   docker compose up -d  # Start Qdrant manually for CLI
   poetry run python -m autogen_mcp.cli_dashboard
   ```

**Note**: Qdrant database starts automatically with the launcher - no manual `docker compose up -d` needed!

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
- `autogen.config.json` for UI launch behavior and server settings
- Qdrant config: `QDRANT_URL`, `QDRANT_API_KEY`
- LLM config: `GEMINI_API_KEY` (only needed for agent LLM calls)
- Server runs on port 9000 by default (configurable in `autogen.config.json`)

## Development Workflow
- One step per feature branch, conventional commits, PR checks required.
- See [`docs/archive/IMPLEMENTATION_PLAN.md`](docs/archive/IMPLEMENTATION_PLAN.md) for historical step plan and checkboxes.
- See [`AUTOGEN_PROJECT_MASTER.md`](AUTOGEN_PROJECT_MASTER.md) for current status and future roadmap.
- Contributions: see `CONTRIBUTING.md`.

## Documentation & ADRs
- All major decisions are documented in `docs/adrs/` as Architecture Decision Records (ADRs).
- See `docs/adrs/README.md` (ADR index) for navigation.

## License
MIT
