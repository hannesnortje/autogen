# ADR-012: Docs Strategy and Dashboard Scope

## Status
Proposed

## Context

As the AutoGen MCP project grows, clear documentation and a simple dashboard are essential for onboarding, transparency, and productivity. Contributors and users need a reliable way to understand the system, track objectives, todos, and artifacts, and navigate architectural decisions.

## Decision

- **Documentation**
  - The `README.md` provides a comprehensive onboarding guide, Poetry workflow, and project structure.
  - `CONTRIBUTING.md` details the contribution process, branching, and pre-commit usage.
  - An ADR index (`docs/adrs/README.md`) lists all architectural decisions for easy reference.
- **Minimal CLI Dashboard**
  - Implemented as `src/autogen_mcp/cli_dashboard.py`.
  - Lists objectives, todos, and artifacts from Qdrant memory.
  - Usable via Poetry: `poetry run python -m autogen_mcp.cli_dashboard`
  - Designed for extensibility (future: filters, agent stats, summaries).

## Consequences

- New contributors can quickly get started and understand project structure and workflow.
- Project status (objectives, todos, artifacts) is visible from the CLI.
- ADRs provide a transparent record of key decisions.
- The dashboard can be extended as project needs evolve.

## References
- `README.md`, `CONTRIBUTING.md`
- `docs/adrs/README.md` (ADR index)
- `src/autogen_mcp/cli_dashboard.py`
