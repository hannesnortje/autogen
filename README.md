# AutoGen + Qdrant + VS Code MCP (Poetry)

This repository implements an AutoGen multi-agent workflow with Qdrant-backed memory and a VS Code MCP server. It uses Poetry for the Python environment.

## Goals
- Multi-scope memory (global/project/agent/thread/objectives/artifacts) in Qdrant
- Hybrid retrieval (dense embeddings + sparse) with tiered search
- AutoGen agents (Agile, Planner, Architect, Coder, Reviewer, Tester, DevOps, Doc)
- VS Code-native control via MCP
- Git-based workflow with per-agent branches and CI gates

## Requirements
- Python 3.11+
- Poetry
- Docker (for Qdrant)
- VS Code

## Quick start
1. Install Poetry: https://python-poetry.org/docs/
2. Create env and install deps (after Step 2 adds pyproject):
   ```bash
   poetry install
   ```
3. Run tests:
   ```bash
   poetry run pytest -q
   ```
4. Start Qdrant (after Step 3 adds compose):
   ```bash
   docker compose up -d
   ```

## Development workflow
- One step per feature branch, conventional commits, PR checks required.
- See `IMPLEMENTATION_PLAN.md` for the detailed step plan and checkboxes.
- Contributions: see `CONTRIBUTING.md`.

## License
MIT
