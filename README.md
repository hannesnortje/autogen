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

## Configuration
1) Create a local `.env` by copying `.env.example` and filling in values. Do not commit `.env`.
   - GEMINI_API_KEY: provide only when we reach Step 7 (agents) to enable live LLM calls. Until then, we run with mocked LLMs.
   - QDRANT_URL / QDRANT_API_KEY: set based on your local or remote Qdrant instance.

2) Check Qdrant is running (after Step 3):
   - Open http://localhost:6333/ in a browser or:
   ```bash
   curl -s http://localhost:6333/collections | jq . | head -n 20
   ```
   - If it responds with JSON, Qdrant is up.

3) Confirm Poetry environment:
   ```bash
   poetry --version
   poetry run python -V
   ```

## Development workflow
- One step per feature branch, conventional commits, PR checks required.
- See `IMPLEMENTATION_PLAN.md` for the detailed step plan and checkboxes.
- Contributions: see `CONTRIBUTING.md`.

## License
MIT
