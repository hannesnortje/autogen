# ADR-000: Tech Stack and Governance

Date: 2025-09-12

## Status
Proposed

## Context
We need a clear baseline for language, environment, memory store, and workflow.

## Decision
- Language: Python 3.11+
- Environment and deps: Poetry
- Memory: Qdrant (Docker) with multi-scope payload fields
- Embeddings: FastEmbed initially (local)
- LLM: Cloud (Gemini) for testing only; secrets via env vars
- Editor and interface: VS Code with MCP server running in workspace folder
- Git policy: per-step and per-agent branches; PRs required with checks
- Observability: structured logging; consider OpenTelemetry later

## Consequences
- Reproducible env with Poetry
- Local, privacy-preserving embeddings initially
- CI will need service container for Qdrant
- Secrets management kept out of repo
