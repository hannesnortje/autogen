# VS Code MCP Interface Contract

This document describes the minimal interface contract for integrating VS Code (or a CLI tool) with the MCP server.

## Endpoints
- `GET /health` — Check server health
- `GET /workspace` — Get workspace folder path
- `POST /orchestrate/start` — Start agent orchestration
- `POST /orchestrate/stop` — Stop orchestration session
- `POST /memory/search` — Search memory
- `POST /objective/add` — Add an objective to a project

## Example Usage (CLI/Extension)

### Health Check
```sh
curl http://localhost:8000/health
```

### Start Orchestration
```sh
curl -X POST http://localhost:8000/orchestrate/start \
  -H 'Content-Type: application/json' \
  -d '{"project": "myproj", "agents": ["Coder", "Reviewer"], "objective": "Add login"}'
```

### Stop Orchestration
```sh
curl -X POST http://localhost:8000/orchestrate/stop \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "..."}'
```

### Memory Search
```sh
curl -X POST http://localhost:8000/memory/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "login", "scope": "project", "k": 5}'
```

### Add Objective
```sh
curl -X POST http://localhost:8000/objective/add \
  -H 'Content-Type: application/json' \
  -d '{"objective": "Add login", "project": "myproj"}'
```

## Notes
- All endpoints return JSON.
- Error responses use standard HTTP status codes and JSON error messages.
- The interface is suitable for both VS Code extensions and CLI scripts.
