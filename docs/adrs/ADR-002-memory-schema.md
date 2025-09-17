# ADR-002: Memory Schema and Naming Conventions

## Status
Proposed

## Context

AutoGen MCP uses Qdrant as a vector database for multi-scope memory. The system must support global, project, agent, thread, objectives, and artifacts scopes, with clear naming conventions for collections and payload schemas for each scope.

## Decision

- **Collections**
  - Default: `memory_default`
  - Per-project: `memory_<project_slug>` (e.g., `memory_myproject`)
  - Additional collections may be created for isolation or scaling.

- **Scopes (payload field: `scope`)**
  - `global`: System-wide events or knowledge
  - `project`: Project-specific context
  - `agent`: Agent-specific memory (role, state, preferences)
  - `thread`: Conversation or task thread
  - `objective`: High-level goals or objectives
  - `artifact`: Artifacts (PRs, summaries, files, etc.)

- **Payload Schema (per event)**
  - `scope`: One of the above
  - `thread_id`: Thread or context identifier
  - `text`: Main content or message
  - `metadata`: Arbitrary dict (optional, for extra context)
  - `ts`: Timestamp

- **Naming Conventions**
  - Collections: `memory_<project_slug>`
  - Thread IDs: `t<uuid>` or meaningful string
  - Artifacts: Use `scope: artifact` and include artifact type in `metadata`

## Consequences

- Enables efficient retrieval and isolation by project, agent, or thread.
- Supports hybrid and tiered search across scopes.
- Naming conventions simplify management and debugging.
- Schema is extensible for future needs (e.g., objectives, summaries, agent state).

## References
- `src/autogen_mcp/memory.py`
- `src/autogen_mcp/qdrant_client.py`
- `src/autogen_mcp/cli_dashboard.py`
